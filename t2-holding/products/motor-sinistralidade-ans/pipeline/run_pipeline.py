"""
Pipeline de Atualização — Orquestrador Principal
=================================================
Coordena download, ETL, benchmarks e retreino ML.
Pode ser executado manualmente ou via cron/scheduler.

Uso:
    # Execução completa (download + ETL + ML)
    python3 pipeline/run_pipeline.py --full
    
    # Apenas ETL (sem download, usa dados já existentes)
    python3 pipeline/run_pipeline.py --etl-only
    
    # Apenas download (sem processar)
    python3 pipeline/run_pipeline.py --download-only
    
    # Dry-run (mostra o que faria sem executar)
    python3 pipeline/run_pipeline.py --dry-run

Agendamento recomendado (cron):
    # Trimestral — 1º dia de Jan, Abr, Jul, Out às 03:00
    0 3 1 1,4,7,10 * cd /home/ubuntu/mvp_sinistralidade && python3 pipeline/run_pipeline.py --full >> pipeline/logs/cron.log 2>&1

Sprint 10 — Mai/2026
Autor: Ricardo Squillaci — Tallent Two Financial Holding
"""

import os
import sys
import json
import logging
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText

# Adicionar diretório pai ao path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(BASE_DIR / "pipeline"))

from download_ans import run_downloads, load_state, save_state
from etl_refresh import run_etl

# ─── Configuração ────────────────────────────────────────────────────────────

LOGS_DIR = BASE_DIR / "pipeline" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuração de notificação (opcional)
NOTIFICATION_CONFIG = {
    "enabled": False,
    "email_to": "",
    "email_from": "",
    "smtp_server": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_pass": ""
}


# ─── Notificação ─────────────────────────────────────────────────────────────

def send_notification(subject: str, body: str):
    """Envia notificação por email (se configurado)."""
    if not NOTIFICATION_CONFIG["enabled"]:
        return
    
    try:
        msg = MIMEText(body)
        msg["Subject"] = f"[Motor Sinistralidade] {subject}"
        msg["From"] = NOTIFICATION_CONFIG["email_from"]
        msg["To"] = NOTIFICATION_CONFIG["email_to"]
        
        with smtplib.SMTP(NOTIFICATION_CONFIG["smtp_server"], NOTIFICATION_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(NOTIFICATION_CONFIG["smtp_user"], NOTIFICATION_CONFIG["smtp_pass"])
            server.send_message(msg)
        
        logger.info("  📧 Notificação enviada")
    except Exception as e:
        logger.warning(f"  ⚠️ Falha ao enviar notificação: {e}")


# ─── Pipeline Principal ──────────────────────────────────────────────────────

def run_full_pipeline(download: bool = True, etl: bool = True, 
                      sib_ufs: list = None, force_download: bool = False,
                      skip_ml: bool = False) -> dict:
    """Executa o pipeline completo de atualização.
    
    Args:
        download: Se True, baixa dados novos da ANS
        etl: Se True, processa dados e retreina modelo
        sib_ufs: UFs específicas para SIB (None = prioritárias)
        force_download: Se True, redownload mesmo se já existe
        skip_ml: Se True, pula retreino do modelo
    
    Returns:
        Dict com resultados de cada etapa
    """
    start_time = datetime.now()
    
    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  MOTOR DE SINISTRALIDADE ANS — PIPELINE AUTOMÁTICO  ║")
    logger.info(f"║  Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}                       ║")
    logger.info("╚══════════════════════════════════════════════════════╝")
    
    results = {
        "inicio": start_time.isoformat(),
        "etapas": {},
        "sucesso": True,
        "erros": []
    }
    
    # ─── Etapa 1: Download ────────────────────────────────────────────────
    if download:
        logger.info("\n▶ ETAPA 1/3: DOWNLOAD DE DADOS ANS")
        try:
            dl_results = run_downloads(
                diops=True, sib=True, 
                sib_ufs=sib_ufs, force=force_download
            )
            results["etapas"]["download"] = dl_results
            
            # Verificar se houve novos dados
            diops_novos = len(dl_results.get("diops", {}).get("trimestres_baixados", []))
            sib_novos = len(dl_results.get("sib", {}).get("ufs_baixadas", []))
            
            if diops_novos == 0 and sib_novos == 0 and not force_download:
                logger.info("  ℹ️ Nenhum dado novo disponível. Pipeline encerrado.")
                results["nota"] = "Sem dados novos — pipeline encerrado sem alterações"
                results["fim"] = datetime.now().isoformat()
                return results
                
        except Exception as e:
            logger.error(f"  ❌ Erro no download: {e}")
            results["erros"].append(f"Download: {str(e)}")
            results["sucesso"] = False
    
    # ─── Etapa 2: ETL + Benchmarks ───────────────────────────────────────
    if etl:
        logger.info("\n▶ ETAPA 2/3: ETL + BENCHMARKS")
        try:
            etl_results = run_etl(skip_ml=True)  # ML separado
            results["etapas"]["etl"] = etl_results
        except Exception as e:
            logger.error(f"  ❌ Erro no ETL: {e}")
            results["erros"].append(f"ETL: {str(e)}")
            results["sucesso"] = False
    
    # ─── Etapa 3: Retreino ML ────────────────────────────────────────────
    if etl and not skip_ml:
        logger.info("\n▶ ETAPA 3/3: RETREINO ML")
        try:
            import duckdb
            DB_PATH = BASE_DIR / "data" / "ans_analytics.duckdb"
            con = duckdb.connect(str(DB_PATH))
            try:
                from etl_refresh import retreinar_modelo
                ml_results = retreinar_modelo(con)
                results["etapas"]["ml"] = ml_results
            finally:
                con.close()
        except Exception as e:
            logger.error(f"  ❌ Erro no retreino ML: {e}")
            results["erros"].append(f"ML: {str(e)}")
            results["sucesso"] = False
    
    # ─── Finalização ─────────────────────────────────────────────────────
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results["fim"] = end_time.isoformat()
    results["duracao_segundos"] = round(duration)
    results["duracao_humano"] = f"{int(duration // 60)}min {int(duration % 60)}s"
    
    # Atualizar estado
    state = load_state()
    state["ultima_execucao"] = end_time.isoformat()
    state.setdefault("historico_execucoes", []).append({
        "timestamp": end_time.isoformat(),
        "sucesso": results["sucesso"],
        "duracao_s": round(duration),
        "erros": results["erros"]
    })
    # Manter apenas últimas 50 execuções
    state["historico_execucoes"] = state["historico_execucoes"][-50:]
    save_state(state)
    
    # Log final
    status = "✅ SUCESSO" if results["sucesso"] else "❌ COM ERROS"
    logger.info(f"\n{'═' * 50}")
    logger.info(f"  Pipeline {status} em {results['duracao_humano']}")
    if results["erros"]:
        for err in results["erros"]:
            logger.error(f"  Erro: {err}")
    logger.info(f"{'═' * 50}")
    
    # Notificação
    if results["sucesso"]:
        send_notification(
            "Pipeline executado com sucesso",
            f"Pipeline concluído em {results['duracao_humano']}.\n\n"
            f"Resultados: {json.dumps(results['etapas'], indent=2, default=str)}"
        )
    else:
        send_notification(
            "⚠️ Pipeline com erros",
            f"Pipeline falhou após {results['duracao_humano']}.\n\n"
            f"Erros: {json.dumps(results['erros'], indent=2)}"
        )
    
    return results


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Motor de Sinistralidade ANS — Pipeline de Atualização Automática",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 pipeline/run_pipeline.py --full              # Execução completa
  python3 pipeline/run_pipeline.py --etl-only          # Apenas ETL (sem download)
  python3 pipeline/run_pipeline.py --download-only     # Apenas download
  python3 pipeline/run_pipeline.py --full --force      # Forçar redownload
  python3 pipeline/run_pipeline.py --full --sib-todas  # SIB de todas as 27 UFs
        """
    )
    
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true", help="Execução completa (download + ETL + ML)")
    mode.add_argument("--etl-only", action="store_true", help="Apenas ETL (sem download)")
    mode.add_argument("--download-only", action="store_true", help="Apenas download (sem ETL)")
    mode.add_argument("--dry-run", action="store_true", help="Mostra o que faria sem executar")
    mode.add_argument("--status", action="store_true", help="Mostra status do pipeline")
    
    parser.add_argument("--force", action="store_true", help="Forçar redownload")
    parser.add_argument("--sib-todas", action="store_true", help="Baixar SIB de todas as 27 UFs")
    parser.add_argument("--sib-ufs", nargs="+", help="UFs específicas para SIB")
    parser.add_argument("--skip-ml", action="store_true", help="Pular retreino ML")
    
    args = parser.parse_args()
    
    if args.status:
        state = load_state()
        print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
        sys.exit(0)
    
    if args.dry_run:
        state = load_state()
        print("═══ DRY RUN — O pipeline faria: ═══")
        print(f"  Último DIOPS: {state.get('ultimo_diops', 'Nunca')}")
        print(f"  Último SIB: {state.get('ultimo_sib', 'Nunca')}")
        print(f"  Última execução: {state.get('ultima_execucao', 'Nunca')}")
        print(f"  DIOPS baixados: {state.get('diops_trimestres_baixados', [])}")
        print(f"  SIB UFs baixadas: {state.get('sib_ufs_baixadas', [])}")
        print(f"\n  Ação: {'Download + ETL + ML' if args.full else 'ETL only' if args.etl_only else 'Download only'}")
        sys.exit(0)
    
    # Determinar UFs do SIB
    from download_ans import UFS
    sib_ufs = UFS if args.sib_todas else args.sib_ufs
    
    # Executar
    results = run_full_pipeline(
        download=not args.etl_only,
        etl=not args.download_only,
        sib_ufs=sib_ufs,
        force_download=args.force,
        skip_ml=args.skip_ml
    )
    
    print("\n" + json.dumps(results, indent=2, ensure_ascii=False, default=str))
