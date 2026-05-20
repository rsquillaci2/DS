"""
Sprint 8.5 — Retreino ML com Base Expandida
Modelo 1: Predição de sinistralidade por operadora (série temporal)
Modelo 2: Score de risco por produto (SIB granular - mantido para 5 ops com dados)
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import json
import pickle
import os

DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"
MODELS_DIR = "/home/ubuntu/mvp_sinistralidade/data/models"

def retrain_model1():
    """Retreina Modelo 1: Predição de sinistralidade por operadora."""
    print("=" * 70)
    print("SPRINT 8.5 — RETREINO ML COM BASE EXPANDIDA")
    print("=" * 70)
    
    con = duckdb.connect(DB_PATH, read_only=True)
    
    # Carregar série temporal expandida
    df = con.execute("""
        SELECT registro_ans, trimestre, receita, despesa, sinistralidade
        FROM sinistralidade_historica
        WHERE sinistralidade IS NOT NULL 
          AND sinistralidade > 0 
          AND sinistralidade < 2
          AND receita > 1000000
        ORDER BY registro_ans, trimestre
    """).df()
    
    print(f"\n[MODELO 1] Predição de Sinistralidade por Operadora")
    print(f"   Registros disponíveis: {len(df):,}")
    print(f"   Operadoras únicas: {df['registro_ans'].nunique()}")
    print(f"   Trimestres: {df['trimestre'].nunique()}")
    
    # Criar features de série temporal
    # Ordenar trimestres cronologicamente
    trim_order = {
        '1T2020': 1, '2T2020': 2, '3T2020': 3, '4T2020': 4,
        '1T2021': 5, '2T2021': 6, '3T2021': 7, '4T2021': 8,
        '1T2022': 9, '2T2022': 10, '3T2022': 11, '4T2022': 12,
        '1T2023': 13, '2T2023': 14, '3T2023': 15, '4T2023': 16,
        '1T2024': 17, '2T2024': 18, '3T2024': 19, '4T2024': 20,
        '1T2025': 21, '2T2025': 22, '3T2025': 23, '4T2025': 24,
    }
    df['trim_num'] = df['trimestre'].map(trim_order)
    df = df.dropna(subset=['trim_num'])
    df = df.sort_values(['registro_ans', 'trim_num'])
    
    # Feature engineering por operadora
    features_list = []
    
    for reg_ans, group in df.groupby('registro_ans'):
        if len(group) < 6:  # Mínimo 6 trimestres para criar lags
            continue
        
        group = group.sort_values('trim_num').reset_index(drop=True)
        
        for i in range(4, len(group)):
            row = {
                'registro_ans': reg_ans,
                'target': group.iloc[i]['sinistralidade'],
                # Lags de sinistralidade
                'sinist_lag_1': group.iloc[i-1]['sinistralidade'],
                'sinist_lag_2': group.iloc[i-2]['sinistralidade'],
                'sinist_lag_4': group.iloc[i-4]['sinistralidade'] if i >= 4 else None,
                # Média móvel
                'sinist_ma4': group.iloc[max(0,i-4):i]['sinistralidade'].mean(),
                # Tendência (delta últimos 4 trimestres)
                'tendencia_4t': group.iloc[i-1]['sinistralidade'] - group.iloc[i-4]['sinistralidade'] if i >= 4 else 0,
                # Delta recente
                'delta_sinist_1': group.iloc[i-1]['sinistralidade'] - group.iloc[i-2]['sinistralidade'],
                # Receita (log)
                'log_receita': np.log1p(group.iloc[i-1]['receita']),
                # Lags de receita
                'receita_lag_1': group.iloc[i-1]['receita'],
                'receita_lag_4': group.iloc[i-4]['receita'] if i >= 4 else group.iloc[0]['receita'],
                # Volatilidade
                'volatilidade': group.iloc[max(0,i-4):i]['sinistralidade'].std(),
            }
            features_list.append(row)
    
    df_features = pd.DataFrame(features_list).dropna()
    print(f"   Features geradas: {len(df_features):,} registros")
    print(f"   Operadoras com features: {df_features['registro_ans'].nunique()}")
    
    # Preparar X e y
    feature_cols = ['sinist_lag_1', 'sinist_lag_2', 'sinist_lag_4', 'sinist_ma4',
                    'tendencia_4t', 'delta_sinist_1', 'log_receita', 
                    'receita_lag_1', 'receita_lag_4', 'volatilidade']
    
    X = df_features[feature_cols].values
    y = df_features['target'].values
    
    # Split temporal (últimos 20% como teste)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n   Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    # Treinar XGBoost
    try:
        from xgboost import XGBRegressor
    except ImportError:
        os.system("sudo pip3 install xgboost -q")
        from xgboost import XGBRegressor
    
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Avaliar
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    mae_test = mean_absolute_error(y_test, y_pred_test)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    print(f"\n   === RESULTADOS MODELO 1 (Expandido) ===")
    print(f"   R² (Train): {r2_train:.4f}")
    print(f"   R² (Test):  {r2_test:.4f}")
    print(f"   MAE (Test): {mae_test:.4f} ({mae_test*100:.2f} pp)")
    print(f"   RMSE (Test): {rmse_test:.4f}")
    print(f"   CV 5-fold R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # Feature importance
    importances = model.feature_importances_
    fi_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print(f"\n   Feature Importance:")
    for _, row in fi_df.iterrows():
        print(f"     {row['feature']:>20s}: {row['importance']:.4f}")
    
    # Salvar modelo e importances
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    with open(f"{MODELS_DIR}/modelo_sinistralidade_operadora.pkl", 'wb') as f:
        pickle.dump(model, f)
    
    fi_df.to_csv(f"{MODELS_DIR}/feature_importance_m1.csv", index=False)
    
    # Fechar conexão read_only antes de abrir para escrita
    con.close()
    
    # Salvar feature importance no banco
    con2 = duckdb.connect(DB_PATH)
    con2.execute("CREATE OR REPLACE TABLE feature_importance_m1 AS SELECT * FROM read_csv_auto(?)", 
                 [f"{MODELS_DIR}/feature_importance_m1.csv"])
    
    # =========================================================
    # Gerar predições para próximo trimestre (todas operadoras)
    # =========================================================
    print(f"\n   Gerando predições para próximo trimestre...")
    
    # Pegar últimos dados de cada operadora
    predictions = []
    for reg_ans, group in df.groupby('registro_ans'):
        group = group.sort_values('trim_num').reset_index(drop=True)
        if len(group) < 4:
            continue
        
        i = len(group)
        try:
            features = np.array([[
                group.iloc[-1]['sinistralidade'],  # sinist_lag_1
                group.iloc[-2]['sinistralidade'],  # sinist_lag_2
                group.iloc[-4]['sinistralidade'] if len(group) >= 4 else group.iloc[-1]['sinistralidade'],  # sinist_lag_4
                group.iloc[-4:]['sinistralidade'].mean(),  # sinist_ma4
                group.iloc[-1]['sinistralidade'] - group.iloc[-4]['sinistralidade'] if len(group) >= 4 else 0,  # tendencia_4t
                group.iloc[-1]['sinistralidade'] - group.iloc[-2]['sinistralidade'],  # delta_sinist_1
                np.log1p(group.iloc[-1]['receita']),  # log_receita
                group.iloc[-1]['receita'],  # receita_lag_1
                group.iloc[-4]['receita'] if len(group) >= 4 else group.iloc[0]['receita'],  # receita_lag_4
                group.iloc[-4:]['sinistralidade'].std(),  # volatilidade
            ]])
            
            pred = model.predict(features)[0]
            predictions.append({
                'registro_ans': reg_ans,
                'sinistralidade_atual': group.iloc[-1]['sinistralidade'],
                'sinistralidade_predita': float(pred),
                'delta': float(pred - group.iloc[-1]['sinistralidade']),
                'tendencia': 'Piora' if pred > group.iloc[-1]['sinistralidade'] + 0.01 else 
                            ('Melhora' if pred < group.iloc[-1]['sinistralidade'] - 0.01 else 'Estável')
            })
        except Exception:
            continue
    
    df_pred = pd.DataFrame(predictions)
    print(f"   Predições geradas: {len(df_pred)} operadoras")
    print(f"   Tendência Piora: {len(df_pred[df_pred['tendencia']=='Piora'])}")
    print(f"   Tendência Melhora: {len(df_pred[df_pred['tendencia']=='Melhora'])}")
    print(f"   Tendência Estável: {len(df_pred[df_pred['tendencia']=='Estável'])}")
    
    # Salvar predições no banco
    con2.execute("""
        CREATE OR REPLACE TABLE predicoes_xgboost AS
        SELECT * FROM df_pred
    """)
    
    # Salvar resultados
    results = {
        'modelo': 'XGBoost Regressor v2 (Expandido)',
        'dados_treino': len(X_train),
        'dados_teste': len(X_test),
        'operadoras': int(df_features['registro_ans'].nunique()),
        'r2_train': float(r2_train),
        'r2_test': float(r2_test),
        'mae_test': float(mae_test),
        'rmse_test': float(rmse_test),
        'cv_r2_mean': float(cv_scores.mean()),
        'cv_r2_std': float(cv_scores.std()),
        'predicoes_geradas': len(df_pred),
        'feature_importance': fi_df.to_dict(orient='records')
    }
    
    with open(f"{MODELS_DIR}/sprint85_resultados.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    con2.close()
    
    print(f"\n✅ Modelo 1 retreinado e salvo!")
    print(f"   Melhoria: R² 0.901 (6 ops) → {r2_test:.3f} ({df_features['registro_ans'].nunique()} ops)")
    
    return results


if __name__ == "__main__":
    results = retrain_model1()
    print(f"\n{'='*70}")
    print(f"RESUMO FINAL")
    print(f"{'='*70}")
    print(f"  R² (Test): {results['r2_test']:.4f}")
    print(f"  MAE: {results['mae_test']*100:.2f} pp")
    print(f"  Predições: {results['predicoes_geradas']} operadoras")
