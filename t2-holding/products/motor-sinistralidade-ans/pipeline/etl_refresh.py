"""
Pipeline de Atualização — Módulo 2: ETL + Benchmarks + Retreino ML
===================================================================
Processa os dados baixados, recalcula sinistralidade, benchmarks e
retreina o modelo XGBoost com a base atualizada.

Sprint 10 — Mai/2026
Autor: Ricardo Squillaci — Tallent Two Financial Holding
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import numpy as np

# ─── Configuração ────────────────────────────────────────────────────────────

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ans_analytics.duckdb"
DIOPS_DIR = DATA_DIR / "diops"
DIOPS_HIST_DIR = DATA_DIR / "diops_historico"
SIB_DIR = DATA_DIR / "sib"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR = BASE_DIR / "pipeline" / "logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ─── ETL DIOPS ───────────────────────────────────────────────────────────────

def etl_diops(con: duckdb.DuckDBPyConnection) -> dict:
    """Processa todos os CSVs DIOPS e recalcula sinistralidade."""
    logger.info("═══ ETL DIOPS ═══")
    
    # Identificar CSVs disponíveis no histórico
    csv_files = sorted(DIOPS_HIST_DIR.glob("*.csv"))
    logger.info(f"  CSVs encontrados: {len(csv_files)}")
    
    if not csv_files:
        return {"success": False, "error": "Nenhum CSV DIOPS encontrado"}
    
    # Verificar CSV mais recente (para sinistralidade_operadora)
    latest_csv = csv_files[-1]
    logger.info(f"  Mais recente: {latest_csv.name}")
    
    # ─── 1. Sinistralidade por operadora (trimestre mais recente) ─────────
    logger.info("  Processando sinistralidade_operadora...")
    
    con.execute("DROP TABLE IF EXISTS sinistralidade_operadora")
    con.execute(f"""
        CREATE TABLE sinistralidade_operadora AS
        WITH raw AS (
            SELECT 
                CAST(REG_ANS AS INTEGER) as registro_ans,
                CAST(REPLACE(REPLACE(VL_SALDO_FINAL, '.', ''), ',', '.') AS DOUBLE) as valor,
                CD_CONTA_CONTABIL as conta,
                DESCRICAO as descricao
            FROM read_csv_auto('{latest_csv}', header=true, sep=';', 
                              all_varchar=true, ignore_errors=true)
            WHERE REG_ANS IS NOT NULL
        ),
        receitas AS (
            SELECT registro_ans, SUM(valor) as receita_contraprestacoes
            FROM raw
            WHERE conta LIKE '31%' AND conta NOT LIKE '311%'
            GROUP BY registro_ans
        ),
        despesas AS (
            SELECT registro_ans, SUM(valor) as despesa_assistencial
            FROM raw
            WHERE conta LIKE '41%' OR conta LIKE '42%'
            GROUP BY registro_ans
        )
        SELECT 
            r.registro_ans,
            r.receita_contraprestacoes,
            COALESCE(d.despesa_assistencial, 0) as despesa_assistencial,
            CASE 
                WHEN r.receita_contraprestacoes > 0 
                THEN COALESCE(d.despesa_assistencial, 0) / r.receita_contraprestacoes
                ELSE NULL 
            END as sinistralidade_total
        FROM receitas r
        LEFT JOIN despesas d ON r.registro_ans = d.registro_ans
        WHERE r.receita_contraprestacoes > 1000000
    """)
    
    count = con.execute("SELECT COUNT(*) FROM sinistralidade_operadora").fetchone()[0]
    logger.info(f"  ✅ sinistralidade_operadora: {count} operadoras")
    
    # ─── 2. Série temporal (todos os trimestres) ─────────────────────────
    logger.info("  Processando sinistralidade_historica...")
    
    con.execute("DROP TABLE IF EXISTS sinistralidade_historica")
    
    # Criar tabela vazia
    con.execute("""
        CREATE TABLE sinistralidade_historica (
            registro_ans INTEGER,
            trimestre VARCHAR,
            receita_contraprestacoes DOUBLE,
            despesa_assistencial DOUBLE,
            sinistralidade DOUBLE
        )
    """)
    
    for csv_file in csv_files:
        trimestre = csv_file.stem  # ex: "4T2025"
        try:
            con.execute(f"""
                INSERT INTO sinistralidade_historica
                WITH raw AS (
                    SELECT 
                        CAST(REG_ANS AS INTEGER) as registro_ans,
                        CAST(REPLACE(REPLACE(VL_SALDO_FINAL, '.', ''), ',', '.') AS DOUBLE) as valor,
                        CD_CONTA_CONTABIL as conta
                    FROM read_csv_auto('{csv_file}', header=true, sep=';', 
                                      all_varchar=true, ignore_errors=true)
                    WHERE REG_ANS IS NOT NULL
                ),
                receitas AS (
                    SELECT registro_ans, SUM(valor) as receita
                    FROM raw WHERE conta LIKE '31%' AND conta NOT LIKE '311%'
                    GROUP BY registro_ans
                ),
                despesas AS (
                    SELECT registro_ans, SUM(valor) as despesa
                    FROM raw WHERE conta LIKE '41%' OR conta LIKE '42%'
                    GROUP BY registro_ans
                )
                SELECT 
                    r.registro_ans,
                    '{trimestre}' as trimestre,
                    r.receita,
                    COALESCE(d.despesa, 0),
                    CASE WHEN r.receita > 0 THEN COALESCE(d.despesa, 0) / r.receita ELSE NULL END
                FROM receitas r
                LEFT JOIN despesas d ON r.registro_ans = d.registro_ans
                WHERE r.receita > 1000000
            """)
        except Exception as e:
            logger.warning(f"  ⚠️ Erro ao processar {trimestre}: {e}")
    
    hist_count = con.execute("SELECT COUNT(*) FROM sinistralidade_historica").fetchone()[0]
    logger.info(f"  ✅ sinistralidade_historica: {hist_count} registros")
    
    return {"success": True, "operadoras": count, "historico_registros": hist_count}


# ─── ETL SIB ─────────────────────────────────────────────────────────────────

def etl_sib(con: duckdb.DuckDBPyConnection) -> dict:
    """Processa SIB consolidado e gera evolução temporal com forward-fill."""
    logger.info("═══ ETL SIB ═══")
    
    # Verificar CSVs do SIB disponíveis
    sib_csvs = list(SIB_DIR.glob("*.csv"))
    if not sib_csvs:
        # Tentar extrair de ZIPs
        sib_zips = list(SIB_DIR.glob("sib_ativo_*.zip"))
        if sib_zips:
            import zipfile
            for zp in sib_zips:
                try:
                    with zipfile.ZipFile(zp, 'r') as zf:
                        zf.extractall(SIB_DIR)
                except Exception as e:
                    logger.warning(f"  ⚠️ Erro ao extrair {zp.name}: {e}")
            sib_csvs = list(SIB_DIR.glob("*.csv"))
    
    if not sib_csvs:
        logger.warning("  Nenhum CSV SIB encontrado")
        return {"success": False, "error": "Nenhum CSV SIB disponível"}
    
    logger.info(f"  CSVs SIB encontrados: {len(sib_csvs)}")
    
    # Carregar e consolidar
    con.execute("DROP TABLE IF EXISTS sib_operadoras")
    
    # Usar o CSV consolidado se existir
    consolidado = SIB_DIR / "beneficiarios_operadora_carteira.csv"
    if consolidado.exists():
        logger.info(f"  Usando consolidado: {consolidado.name}")
        con.execute(f"""
            CREATE TABLE sib_operadoras AS
            SELECT * FROM read_csv_auto('{consolidado}', header=true, sep=';',
                                        all_varchar=false, ignore_errors=true)
        """)
    else:
        # Consolidar de múltiplos CSVs por UF
        logger.info("  Consolidando CSVs por UF...")
        first = True
        for csv_file in sib_csvs:
            try:
                if first:
                    con.execute(f"""
                        CREATE TABLE sib_operadoras AS
                        SELECT * FROM read_csv_auto('{csv_file}', header=true, sep=';',
                                                    all_varchar=false, ignore_errors=true)
                    """)
                    first = False
                else:
                    con.execute(f"""
                        INSERT INTO sib_operadoras
                        SELECT * FROM read_csv_auto('{csv_file}', header=true, sep=';',
                                                    all_varchar=false, ignore_errors=true)
                    """)
            except Exception as e:
                logger.warning(f"  ⚠️ Erro ao processar {csv_file.name}: {e}")
    
    sib_count = con.execute("SELECT COUNT(*) FROM sib_operadoras").fetchone()[0]
    logger.info(f"  ✅ sib_operadoras: {sib_count} registros")
    
    # ─── Evolução temporal com forward-fill ──────────────────────────────
    logger.info("  Calculando evolução temporal (forward-fill)...")
    
    try:
        # Extrair dados para pandas para forward-fill
        df = con.execute("""
            SELECT 
                CD_OPERADORA as registro_ans,
                ID_CMPT as mes,
                TP_SEXO,
                DE_TIPO_CONTRATACAO as tipo_contratacao,
                DE_CONTRATACAO_COLETIVO as tipo_financiamento,
                SG_UF as uf,
                DE_FAIXA_ETARIA as faixa_etaria,
                QT_BENEFICIARIO_ATIVO as beneficiarios
            FROM sib_operadoras
            WHERE QT_BENEFICIARIO_ATIVO > 0
        """).fetchdf()
        
        if len(df) > 0:
            # Agregar por (operadora, mes, tipo_contratacao, tipo_financiamento)
            df_agg = df.groupby(
                ['registro_ans', 'mes', 'tipo_contratacao', 'tipo_financiamento'],
                dropna=False
            )['beneficiarios'].sum().reset_index()
            
            # Forward-fill por grupo
            all_meses = sorted(df_agg['mes'].unique())
            groups = df_agg.groupby(['registro_ans', 'tipo_contratacao', 'tipo_financiamento'], dropna=False)
            
            filled_records = []
            for name, group in groups:
                group_sorted = group.sort_values('mes').set_index('mes')
                group_reindexed = group_sorted.reindex(all_meses)
                group_reindexed['beneficiarios'] = group_reindexed['beneficiarios'].ffill()
                group_reindexed['registro_ans'] = name[0]
                group_reindexed['tipo_contratacao'] = name[1]
                group_reindexed['tipo_financiamento'] = name[2]
                group_reindexed = group_reindexed.dropna(subset=['beneficiarios'])
                filled_records.append(group_reindexed.reset_index().rename(columns={'index': 'mes'}))
            
            if filled_records:
                df_filled = pd.concat(filled_records, ignore_index=True)
                
                # Agregar por (operadora, mes) para total
                df_evolucao = df_filled.groupby(['registro_ans', 'mes'])['beneficiarios'].sum().reset_index()
                df_evolucao.columns = ['registro_ans', 'mes', 'total_beneficiarios']
                
                con.execute("DROP TABLE IF EXISTS sib_evolucao_temporal")
                con.execute("CREATE TABLE sib_evolucao_temporal AS SELECT * FROM df_evolucao")
                
                evol_count = con.execute("SELECT COUNT(*) FROM sib_evolucao_temporal").fetchone()[0]
                logger.info(f"  ✅ sib_evolucao_temporal: {evol_count} registros")
            else:
                evol_count = 0
        else:
            evol_count = 0
            
    except Exception as e:
        logger.error(f"  ❌ Erro no forward-fill: {e}")
        evol_count = 0
    
    return {"success": True, "sib_registros": sib_count, "evolucao_registros": evol_count}


# ─── Benchmarks ──────────────────────────────────────────────────────────────

def recalcular_benchmarks(con: duckdb.DuckDBPyConnection) -> dict:
    """Recalcula benchmarks por modalidade usando operadoras_classificacao."""
    logger.info("═══ RECÁLCULO DE BENCHMARKS ═══")
    
    con.execute("DROP TABLE IF EXISTS resultado_benchmark")
    con.execute("""
        CREATE TABLE resultado_benchmark AS
        WITH classified AS (
            SELECT 
                s.registro_ans,
                s.sinistralidade_total,
                s.receita_contraprestacoes,
                COALESCE(c.modalidade, 'Não classificada') as modalidade
            FROM sinistralidade_operadora s
            LEFT JOIN operadoras_classificacao c ON s.registro_ans = c.registro_ans
            WHERE s.sinistralidade_total IS NOT NULL
              AND s.sinistralidade_total > 0
              AND s.sinistralidade_total < 3.0
        ),
        benchmarks AS (
            SELECT 
                modalidade,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sinistralidade_total) as mediana,
                AVG(sinistralidade_total) as media,
                COUNT(*) as n_operadoras
            FROM classified
            GROUP BY modalidade
            HAVING COUNT(*) >= 3
        )
        SELECT 
            c.registro_ans,
            c.modalidade,
            c.sinistralidade_total as sinistralidade_real,
            b.mediana as benchmark_referencia,
            c.sinistralidade_total - b.mediana as delta_vs_benchmark,
            CASE 
                WHEN c.sinistralidade_total <= b.mediana * 0.9 THEN 'Eficiente'
                WHEN c.sinistralidade_total <= b.mediana * 1.1 THEN 'Na Média'
                WHEN c.sinistralidade_total <= b.mediana * 1.3 THEN 'Sob Pressão'
                ELSE 'Crítico'
            END as classificacao
        FROM classified c
        JOIN benchmarks b ON c.modalidade = b.modalidade
    """)
    
    bench_count = con.execute("SELECT COUNT(*) FROM resultado_benchmark").fetchone()[0]
    modals = con.execute("SELECT COUNT(DISTINCT modalidade) FROM resultado_benchmark").fetchone()[0]
    logger.info(f"  ✅ resultado_benchmark: {bench_count} operadoras em {modals} modalidades")
    
    return {"success": True, "operadoras": bench_count, "modalidades": modals}


# ─── Retreino ML ─────────────────────────────────────────────────────────────

def retreinar_modelo(con: duckdb.DuckDBPyConnection) -> dict:
    """Retreina o modelo XGBoost com a base atualizada."""
    logger.info("═══ RETREINO ML (XGBoost) ═══")
    
    try:
        from xgboost import XGBRegressor
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.metrics import mean_absolute_error, r2_score
        import joblib
    except ImportError:
        logger.error("  ❌ xgboost ou sklearn não instalados")
        return {"success": False, "error": "Dependências ML não instaladas"}
    
    # Preparar dados de treino
    df = con.execute("""
        SELECT 
            h.registro_ans,
            h.trimestre,
            h.sinistralidade as sinistralidade_atual,
            COALESCE(c.modalidade, 'Outro') as modalidade,
            h.receita_contraprestacoes as receita
        FROM sinistralidade_historica h
        LEFT JOIN operadoras_classificacao c ON h.registro_ans = c.registro_ans
        WHERE h.sinistralidade IS NOT NULL
          AND h.sinistralidade > 0
          AND h.sinistralidade < 3.0
        ORDER BY h.registro_ans, h.trimestre
    """).fetchdf()
    
    if len(df) < 100:
        logger.warning(f"  ⚠️ Dados insuficientes para treino: {len(df)} registros")
        return {"success": False, "error": f"Apenas {len(df)} registros disponíveis"}
    
    logger.info(f"  Dados de treino: {len(df)} registros, {df['registro_ans'].nunique()} operadoras")
    
    # Feature engineering
    # Encode modalidade
    modalidade_map = {m: i for i, m in enumerate(df['modalidade'].unique())}
    df['modalidade_enc'] = df['modalidade'].map(modalidade_map)
    
    # Trimestre como features numéricas
    df['ano'] = df['trimestre'].str.extract(r'(\d{4})').astype(float)
    df['tri'] = df['trimestre'].str.extract(r'(\d)T').astype(float)
    df['periodo'] = df['ano'] + (df['tri'] - 1) / 4
    
    # Lag features (sinistralidade do trimestre anterior)
    df = df.sort_values(['registro_ans', 'periodo'])
    df['sinist_lag1'] = df.groupby('registro_ans')['sinistralidade_atual'].shift(1)
    df['sinist_lag2'] = df.groupby('registro_ans')['sinistralidade_atual'].shift(2)
    df['tendencia'] = df['sinist_lag1'] - df['sinist_lag2']
    
    # Remover NaN dos lags
    df_train = df.dropna(subset=['sinist_lag1', 'sinist_lag2']).copy()
    
    if len(df_train) < 50:
        logger.warning(f"  ⚠️ Dados insuficientes após lags: {len(df_train)}")
        return {"success": False, "error": "Dados insuficientes após feature engineering"}
    
    # Features e target
    features = ['sinist_lag1', 'sinist_lag2', 'tendencia', 'modalidade_enc', 'periodo']
    X = df_train[features].values
    y = df_train['sinistralidade_atual'].values
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Treinar
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)
    
    # Métricas
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    logger.info(f"  R² (test): {r2:.4f}")
    logger.info(f"  MAE (test): {mae:.4f} ({mae*100:.2f} pp)")
    logger.info(f"  CV 5-fold: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # Salvar modelo
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "xgboost_sinistralidade.joblib"
    metadata = {
        "version": f"sprint10_{datetime.now().strftime('%Y%m%d')}",
        "r2_test": round(r2, 4),
        "mae_test": round(mae, 4),
        "cv_mean": round(cv_scores.mean(), 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_operadoras": df_train['registro_ans'].nunique(),
        "features": features,
        "modalidade_map": modalidade_map,
        "trained_at": datetime.now().isoformat()
    }
    
    joblib.dump({"model": model, "metadata": metadata}, model_path)
    logger.info(f"  ✅ Modelo salvo: {model_path}")
    
    # Gerar predições para todas as operadoras
    logger.info("  Gerando predições...")
    
    # Pegar último trimestre de cada operadora
    df_latest = df.sort_values('periodo').groupby('registro_ans').last().reset_index()
    df_latest = df_latest.dropna(subset=['sinist_lag1', 'sinist_lag2'])
    
    if len(df_latest) > 0:
        X_pred = df_latest[features].values
        df_latest['predicao'] = model.predict(X_pred)
        df_latest['variacao_predita'] = df_latest['predicao'] - df_latest['sinistralidade_atual']
        
        # Salvar predições no banco
        df_pred = df_latest[['registro_ans', 'sinistralidade_atual', 'predicao', 'variacao_predita']].copy()
        df_pred.columns = ['registro_ans', 'sinistralidade_atual', 'sinistralidade_predita', 'variacao_predita']
        
        con.execute("DROP TABLE IF EXISTS predicoes_xgboost")
        con.execute("CREATE TABLE predicoes_xgboost AS SELECT * FROM df_pred")
        
        pred_count = con.execute("SELECT COUNT(*) FROM predicoes_xgboost").fetchone()[0]
        logger.info(f"  ✅ predicoes_xgboost: {pred_count} predições")
    else:
        pred_count = 0
    
    return {
        "success": True,
        "r2": round(r2, 4),
        "mae_pp": round(mae * 100, 2),
        "cv_mean": round(cv_scores.mean(), 4),
        "n_operadoras": df_train['registro_ans'].nunique(),
        "predicoes": pred_count
    }


# ─── Orquestrador ETL ────────────────────────────────────────────────────────

def run_etl(skip_sib: bool = False, skip_ml: bool = False) -> dict:
    """Executa o pipeline ETL completo."""
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  PIPELINE ANS — MÓDULO 2: ETL + ML          ║")
    logger.info(f"║  Execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}       ║")
    logger.info("╚══════════════════════════════════════════════╝")
    
    results = {"timestamp": datetime.now().isoformat()}
    
    con = duckdb.connect(str(DB_PATH))
    
    try:
        # 1. ETL DIOPS
        results["diops"] = etl_diops(con)
        
        # 2. ETL SIB
        if not skip_sib:
            results["sib"] = etl_sib(con)
        
        # 3. Benchmarks
        results["benchmarks"] = recalcular_benchmarks(con)
        
        # 4. ML
        if not skip_ml:
            results["ml"] = retreinar_modelo(con)
        
    finally:
        con.close()
    
    logger.info("═══ ETL CONCLUÍDO ═══")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ETL + Benchmarks + ML")
    parser.add_argument("--skip-sib", action="store_true", help="Pular processamento SIB")
    parser.add_argument("--skip-ml", action="store_true", help="Pular retreino ML")
    
    args = parser.parse_args()
    results = run_etl(skip_sib=args.skip_sib, skip_ml=args.skip_ml)
    
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
