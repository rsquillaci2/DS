"""
Sprint 8 — Modelo Preditivo XGBoost
Motor de Sinistralidade ANS — Tallent Two Financial Holding

Implementa:
- Modelo 1: Regressão de sinistralidade por operadora (série temporal)
- Modelo 2: Classificação de risco por produto (cross-section)
- SHAP values para explicabilidade
- Serialização dos modelos para uso no dashboard
"""

import duckdb
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, classification_report
)
import xgboost as xgb
import shap
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

DB_PATH = "data/ans_analytics.duckdb"
OUTPUT_DIR = "data/models/"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("SPRINT 8 — MODELO PREDITIVO XGBOOST")
print("=" * 60)

# ============================================================
# PARTE 1: MODELO 1 — REGRESSÃO POR OPERADORA (SÉRIE TEMPORAL)
# ============================================================

print("\n[1/6] Feature Engineering — Modelo 1 (Operadora)")

con = duckdb.connect(DB_PATH, read_only=True)

# Carregar série temporal
df_hist = con.execute("""
    SELECT registro_ans, trimestre, receita, despesa, sinistralidade
    FROM sinistralidade_historica
    WHERE tipo_despesa = 'assistencial'
    ORDER BY registro_ans, trimestre
""").fetchdf()

# Criar features temporais
def parse_trimestre(t):
    """Converte '1T2020' para (ano, trimestre_num)"""
    parts = t.split('T')
    return int(parts[1]), int(parts[0])

df_hist['ano'] = df_hist['trimestre'].apply(lambda x: parse_trimestre(x)[0])
df_hist['trim_num'] = df_hist['trimestre'].apply(lambda x: parse_trimestre(x)[1])
df_hist['periodo_seq'] = df_hist['ano'] * 4 + df_hist['trim_num']

# Ordenar para cálculo de lags
df_hist = df_hist.sort_values(['registro_ans', 'periodo_seq']).reset_index(drop=True)

# Calcular features por operadora
features_list = []
for reg_ans, group in df_hist.groupby('registro_ans'):
    group = group.sort_values('periodo_seq').reset_index(drop=True)
    
    for i in range(len(group)):
        row = group.iloc[i]
        feat = {
            'registro_ans': reg_ans,
            'trimestre': row['trimestre'],
            'periodo_seq': row['periodo_seq'],
            'trim_num': row['trim_num'],
            'receita': row['receita'],
            'despesa': row['despesa'],
            'sinistralidade': row['sinistralidade'],
        }
        
        # Lag features
        if i >= 1:
            feat['sinist_lag_1'] = group.iloc[i-1]['sinistralidade']
            feat['receita_lag_1'] = group.iloc[i-1]['receita']
        else:
            feat['sinist_lag_1'] = np.nan
            feat['receita_lag_1'] = np.nan
            
        if i >= 2:
            feat['sinist_lag_2'] = group.iloc[i-2]['sinistralidade']
        else:
            feat['sinist_lag_2'] = np.nan
            
        # Lag sazonal (mesmo trimestre ano anterior)
        if i >= 4:
            feat['sinist_lag_4'] = group.iloc[i-4]['sinistralidade']
            feat['receita_lag_4'] = group.iloc[i-4]['receita']
        else:
            feat['sinist_lag_4'] = np.nan
            feat['receita_lag_4'] = np.nan
        
        # Média móvel 4 trimestres
        if i >= 4:
            feat['sinist_ma4'] = group.iloc[i-4:i]['sinistralidade'].mean()
            feat['receita_growth_4t'] = (row['receita'] / group.iloc[i-4]['receita'] - 1) if group.iloc[i-4]['receita'] > 0 else 0
        else:
            feat['sinist_ma4'] = np.nan
            feat['receita_growth_4t'] = np.nan
        
        # Delta de sinistralidade
        if i >= 1:
            feat['delta_sinist_1'] = row['sinistralidade'] - group.iloc[i-1]['sinistralidade']
        else:
            feat['delta_sinist_1'] = np.nan
            
        # Tendência (slope dos últimos 4 trimestres)
        if i >= 4:
            recent = group.iloc[i-3:i+1]['sinistralidade'].values
            feat['tendencia_4t'] = np.polyfit(range(4), recent, 1)[0]
        else:
            feat['tendencia_4t'] = np.nan
        
        # Receita per capita (proxy de porte)
        feat['log_receita'] = np.log1p(row['receita'])
        
        features_list.append(feat)

df_features = pd.DataFrame(features_list)

# Adicionar info de operadora (tipo)
tipo_operadora = {
    '310239': 'pequena',
    '355097': 'media',
    '359017': 'grande_verticalizada',
    '417491': 'seguradora',
    '421197': 'filantropia',
    '422371': 'media_verticalizada'
}
df_features['tipo_operadora'] = df_features['registro_ans'].map(tipo_operadora)

# Encode tipo_operadora
le_tipo = LabelEncoder()
df_features['tipo_operadora_enc'] = le_tipo.fit_transform(df_features['tipo_operadora'])

# Remover linhas com NaN (primeiros trimestres sem lags)
feature_cols_m1 = [
    'trim_num', 'sinist_lag_1', 'sinist_lag_2', 'sinist_lag_4',
    'receita_lag_1', 'receita_lag_4', 'sinist_ma4', 'receita_growth_4t',
    'delta_sinist_1', 'tendencia_4t', 'log_receita', 'tipo_operadora_enc'
]

df_train_m1 = df_features.dropna(subset=feature_cols_m1).copy()
print(f"   Registros para treinamento: {len(df_train_m1)} (de {len(df_features)} total)")
print(f"   Features: {len(feature_cols_m1)}")

# Split temporal (últimos 4 trimestres = test)
df_train_m1 = df_train_m1.sort_values('periodo_seq')
cutoff = df_train_m1['periodo_seq'].quantile(0.8)
train_mask = df_train_m1['periodo_seq'] <= cutoff

X_train = df_train_m1[train_mask][feature_cols_m1]
y_train = df_train_m1[train_mask]['sinistralidade']
X_test = df_train_m1[~train_mask][feature_cols_m1]
y_test = df_train_m1[~train_mask]['sinistralidade']

print(f"   Train: {len(X_train)} | Test: {len(X_test)}")

# Treinar Modelo 1
print("\n[2/6] Treinamento — Modelo 1 (XGBoost Regressor)")

model_1 = xgb.XGBRegressor(
    max_depth=4,
    learning_rate=0.05,
    n_estimators=200,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    verbosity=0
)

model_1.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)

# Métricas
y_pred_train = model_1.predict(X_train)
y_pred_test = model_1.predict(X_test)

metrics_m1 = {
    'mae_train': mean_absolute_error(y_train, y_pred_train),
    'mae_test': mean_absolute_error(y_test, y_pred_test),
    'rmse_train': np.sqrt(mean_squared_error(y_train, y_pred_train)),
    'rmse_test': np.sqrt(mean_squared_error(y_test, y_pred_test)),
    'r2_train': r2_score(y_train, y_pred_train),
    'r2_test': r2_score(y_test, y_pred_test),
}

print(f"   MAE (train): {metrics_m1['mae_train']:.4f}")
print(f"   MAE (test):  {metrics_m1['mae_test']:.4f}")
print(f"   RMSE (test): {metrics_m1['rmse_test']:.4f}")
print(f"   R² (train):  {metrics_m1['r2_train']:.4f}")
print(f"   R² (test):   {metrics_m1['r2_test']:.4f}")

# Cross-validation temporal
tscv = TimeSeriesSplit(n_splits=3)
cv_scores = cross_val_score(model_1, 
    df_train_m1[feature_cols_m1], 
    df_train_m1['sinistralidade'], 
    cv=tscv, scoring='neg_mean_absolute_error')
metrics_m1['cv_mae_mean'] = -cv_scores.mean()
metrics_m1['cv_mae_std'] = cv_scores.std()
print(f"   CV MAE: {metrics_m1['cv_mae_mean']:.4f} ± {metrics_m1['cv_mae_std']:.4f}")

# ============================================================
# PARTE 2: MODELO 2 — CLASSIFICAÇÃO POR PRODUTO (CROSS-SECTION)
# ============================================================

print("\n[3/6] Feature Engineering — Modelo 2 (Produto)")

df_produtos = con.execute("""
    SELECT 
        registro_ans, cd_plano, segmentacao, tipo_contratacao, abrangencia,
        vidas_total, score_total, despesa_estimada, receita_estimada,
        sinistralidade_estimada, custo_per_capita_medio, 
        fator_etario_medio, municipios, ufs, sinist_total_operadora
    FROM score_risco_produto_agg
    WHERE vidas_total > 0
""").fetchdf()

con.close()

# Criar target: classificação de risco
def classificar_risco(sinist):
    if sinist < 0.70:
        return 'Baixo'
    elif sinist < 0.80:
        return 'Medio'
    elif sinist < 0.90:
        return 'Alto'
    else:
        return 'Critico'

df_produtos['classe_risco'] = df_produtos['sinistralidade_estimada'].apply(classificar_risco)

# Encode categóricas
le_seg = LabelEncoder()
le_cont = LabelEncoder()
le_abr = LabelEncoder()
le_reg = LabelEncoder()

df_produtos['segmentacao_enc'] = le_seg.fit_transform(df_produtos['segmentacao'].fillna('Desconhecido'))
df_produtos['tipo_contratacao_enc'] = le_cont.fit_transform(df_produtos['tipo_contratacao'].fillna('Desconhecido'))
df_produtos['abrangencia_enc'] = le_abr.fit_transform(df_produtos['abrangencia'].fillna('Desconhecido'))
df_produtos['registro_ans_enc'] = le_reg.fit_transform(df_produtos['registro_ans'])

# Features derivadas
df_produtos['log_vidas'] = np.log1p(df_produtos['vidas_total'])
df_produtos['log_despesa'] = np.log1p(df_produtos['despesa_estimada'])
df_produtos['concentracao_geo'] = 1.0 / df_produtos['municipios'].clip(lower=1)
df_produtos['proporcao_score_vidas'] = df_produtos['score_total'] / df_produtos['vidas_total'].clip(lower=1)

feature_cols_m2 = [
    'segmentacao_enc', 'tipo_contratacao_enc', 'abrangencia_enc',
    'registro_ans_enc', 'log_vidas', 'fator_etario_medio',
    'municipios', 'ufs', 'concentracao_geo', 'proporcao_score_vidas',
    'custo_per_capita_medio', 'sinist_total_operadora'
]

# Encode target
le_risco = LabelEncoder()
df_produtos['classe_risco_enc'] = le_risco.fit_transform(df_produtos['classe_risco'])

# Remover NaN
df_train_m2 = df_produtos.dropna(subset=feature_cols_m2).copy()
print(f"   Registros para treinamento: {len(df_train_m2)}")
print(f"   Features: {len(feature_cols_m2)}")
print(f"   Distribuição de classes:")
print(f"   {df_train_m2['classe_risco'].value_counts().to_dict()}")

# Split stratificado
from sklearn.model_selection import train_test_split
X_train2, X_test2, y_train2, y_test2 = train_test_split(
    df_train_m2[feature_cols_m2],
    df_train_m2['classe_risco_enc'],
    test_size=0.2,
    random_state=42,
    stratify=df_train_m2['classe_risco_enc']
)

print(f"   Train: {len(X_train2)} | Test: {len(X_test2)}")

# Treinar Modelo 2
print("\n[4/6] Treinamento — Modelo 2 (XGBoost Classifier)")

model_2 = xgb.XGBClassifier(
    max_depth=5,
    learning_rate=0.08,
    n_estimators=150,
    min_child_weight=5,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    verbosity=0,
    use_label_encoder=False,
    eval_metric='mlogloss'
)

model_2.fit(
    X_train2, y_train2,
    eval_set=[(X_test2, y_test2)],
    verbose=False
)

# Métricas
y_pred2_train = model_2.predict(X_train2)
y_pred2_test = model_2.predict(X_test2)

metrics_m2 = {
    'accuracy_train': accuracy_score(y_train2, y_pred2_train),
    'accuracy_test': accuracy_score(y_test2, y_pred2_test),
    'f1_macro_test': f1_score(y_test2, y_pred2_test, average='macro'),
    'f1_weighted_test': f1_score(y_test2, y_pred2_test, average='weighted'),
}

print(f"   Accuracy (train): {metrics_m2['accuracy_train']:.4f}")
print(f"   Accuracy (test):  {metrics_m2['accuracy_test']:.4f}")
print(f"   F1 Macro (test):  {metrics_m2['f1_macro_test']:.4f}")
print(f"   F1 Weighted:      {metrics_m2['f1_weighted_test']:.4f}")

# Classification report
print("\n   Classification Report:")
report = classification_report(y_test2, y_pred2_test, 
    target_names=le_risco.classes_, output_dict=True)
for cls in le_risco.classes_:
    print(f"     {cls}: precision={report[cls]['precision']:.2f}, recall={report[cls]['recall']:.2f}, f1={report[cls]['f1-score']:.2f}")

# Cross-validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores2 = cross_val_score(model_2, 
    df_train_m2[feature_cols_m2], 
    df_train_m2['classe_risco_enc'], 
    cv=skf, scoring='f1_weighted')
metrics_m2['cv_f1_mean'] = cv_scores2.mean()
metrics_m2['cv_f1_std'] = cv_scores2.std()
print(f"\n   CV F1 Weighted: {metrics_m2['cv_f1_mean']:.4f} ± {metrics_m2['cv_f1_std']:.4f}")

# ============================================================
# PARTE 3: SHAP VALUES
# ============================================================

print("\n[5/6] SHAP Values — Explicabilidade")

# SHAP Modelo 1
explainer_1 = shap.TreeExplainer(model_1)
shap_values_1 = explainer_1.shap_values(df_train_m1[feature_cols_m1])

# Feature importance Modelo 1
fi_m1 = pd.DataFrame({
    'feature': feature_cols_m1,
    'importance': model_1.feature_importances_,
    'shap_mean_abs': np.abs(shap_values_1).mean(axis=0)
}).sort_values('shap_mean_abs', ascending=False)

print("   Modelo 1 — Top Features (SHAP):")
for _, row in fi_m1.head(6).iterrows():
    print(f"     {row['feature']}: {row['shap_mean_abs']:.4f}")

# SHAP Modelo 2
explainer_2 = shap.TreeExplainer(model_2)
shap_values_2 = explainer_2.shap_values(df_train_m2[feature_cols_m2])

# Feature importance Modelo 2
if isinstance(shap_values_2, list):
    # Multiclass: shap_values_2 is a list of arrays (one per class)
    shap_abs_m2 = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values_2], axis=0)
else:
    # Binary or single array
    if shap_values_2.ndim == 3:
        shap_abs_m2 = np.abs(shap_values_2).mean(axis=(0, 2))
    else:
        shap_abs_m2 = np.abs(shap_values_2).mean(axis=0)

fi_m2 = pd.DataFrame({
    'feature': feature_cols_m2,
    'importance': model_2.feature_importances_,
    'shap_mean_abs': shap_abs_m2
}).sort_values('shap_mean_abs', ascending=False)

print("\n   Modelo 2 — Top Features (SHAP):")
for _, row in fi_m2.head(6).iterrows():
    print(f"     {row['feature']}: {row['shap_mean_abs']:.4f}")

# ============================================================
# PARTE 4: PREDIÇÕES E SERIALIZAÇÃO
# ============================================================

print("\n[6/6] Serialização e Predições Futuras")

# Gerar predições para o próximo trimestre (1T2026)
predictions = []
for reg_ans in df_features['registro_ans'].unique():
    op_data = df_train_m1[df_train_m1['registro_ans'] == reg_ans].sort_values('periodo_seq')
    if len(op_data) < 1:
        continue
    last = op_data.iloc[-1]
    
    # Usar último registro como base para predição
    pred_features = last[feature_cols_m1].values.reshape(1, -1)
    pred_sinist = model_1.predict(pred_features)[0]
    
    # Intervalo de confiança (usando erro do modelo)
    ci_lower = pred_sinist - metrics_m1['mae_test']
    ci_upper = pred_sinist + metrics_m1['mae_test']
    
    predictions.append({
        'registro_ans': reg_ans,
        'ultimo_trimestre': last['trimestre'],
        'sinistralidade_atual': last['sinistralidade'],
        'predicao_proximo_trim': float(pred_sinist),
        'ic_inferior': float(max(0, ci_lower)),
        'ic_superior': float(min(1.5, ci_upper)),
        'tendencia': 'Piora' if pred_sinist > last['sinistralidade'] else 'Melhora',
        'delta_previsto': float(pred_sinist - last['sinistralidade'])
    })

df_predictions = pd.DataFrame(predictions)
print("   Predições para próximo trimestre:")
print(df_predictions[['registro_ans', 'sinistralidade_atual', 'predicao_proximo_trim', 'tendencia']].to_string(index=False))

# Serializar modelos
joblib.dump(model_1, f"{OUTPUT_DIR}modelo_sinistralidade_operadora.pkl")
joblib.dump(model_2, f"{OUTPUT_DIR}modelo_risco_produto.pkl")
joblib.dump(le_tipo, f"{OUTPUT_DIR}encoder_tipo_operadora.pkl")
joblib.dump(le_seg, f"{OUTPUT_DIR}encoder_segmentacao.pkl")
joblib.dump(le_cont, f"{OUTPUT_DIR}encoder_contratacao.pkl")
joblib.dump(le_abr, f"{OUTPUT_DIR}encoder_abrangencia.pkl")
joblib.dump(le_reg, f"{OUTPUT_DIR}encoder_registro.pkl")
joblib.dump(le_risco, f"{OUTPUT_DIR}encoder_risco.pkl")

# Salvar SHAP values e feature importance
fi_m1.to_csv(f"{OUTPUT_DIR}feature_importance_m1.csv", index=False)
fi_m2.to_csv(f"{OUTPUT_DIR}feature_importance_m2.csv", index=False)

# Salvar predições
df_predictions.to_json(f"{OUTPUT_DIR}predicoes_proximo_trimestre.json", orient='records', indent=2)

# Salvar métricas consolidadas
all_metrics = {
    'modelo_1_operadora': metrics_m1,
    'modelo_2_produto': metrics_m2,
    'feature_importance_m1': fi_m1.to_dict('records'),
    'feature_importance_m2': fi_m2.to_dict('records'),
    'predicoes': predictions,
    'metadata': {
        'data_treinamento': '2026-05-20',
        'n_operadoras': len(df_features['registro_ans'].unique()),
        'n_produtos': len(df_train_m2),
        'n_features_m1': len(feature_cols_m1),
        'n_features_m2': len(feature_cols_m2),
        'classes_risco': list(le_risco.classes_),
        'feature_names_m1': feature_cols_m1,
        'feature_names_m2': feature_cols_m2,
    }
}

with open(f"{OUTPUT_DIR}sprint8_resultados.json", 'w') as f:
    json.dump(all_metrics, f, indent=2, default=str)

# Salvar no DuckDB
con = duckdb.connect(DB_PATH, read_only=False)
con.execute("DROP TABLE IF EXISTS predicoes_xgboost")
con.execute("""
    CREATE TABLE predicoes_xgboost AS 
    SELECT * FROM df_predictions
""")
con.execute("DROP TABLE IF EXISTS feature_importance_m1")
con.execute("""
    CREATE TABLE feature_importance_m1 AS 
    SELECT * FROM fi_m1
""")
con.execute("DROP TABLE IF EXISTS feature_importance_m2")
con.execute("""
    CREATE TABLE feature_importance_m2 AS 
    SELECT * FROM fi_m2
""")
con.close()

print("\n" + "=" * 60)
print("SPRINT 8 CONCLUÍDO")
print("=" * 60)
print(f"\nArquivos gerados em {OUTPUT_DIR}:")
for f in os.listdir(OUTPUT_DIR):
    size = os.path.getsize(f"{OUTPUT_DIR}{f}")
    print(f"  {f} ({size/1024:.1f} KB)")
print(f"\nModelo 1 (Operadora): R²={metrics_m1['r2_test']:.3f}, MAE={metrics_m1['mae_test']:.4f}")
print(f"Modelo 2 (Produto):   Acc={metrics_m2['accuracy_test']:.3f}, F1={metrics_m2['f1_weighted_test']:.4f}")
