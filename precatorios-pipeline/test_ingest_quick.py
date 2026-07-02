"""Quick test: ingere apenas 2026 (mais recente) para validar pipeline."""
import sys
sys.path.insert(0, ".")
from ingest.sof import ingest_execucao_orcamentaria, ingest_expedidos, ingest_ipca

print("=== Quick Test: SOF Ingest ===")
print("1. Execução orçamentária (consolidada)...")
n1 = ingest_execucao_orcamentaria()
print(f"   → {n1} registros ✓")

print("2. Expedidos 2026 apenas (74MB, ~1min)...")
n2 = ingest_expedidos(years=[2026])
print(f"   → {n2} registros ✓")

print("3. IPCA...")
n3 = ingest_ipca()
print(f"   → {n3} registros ✓")

print(f"\nTotal: {n1 + n2 + n3} registros ingeridos.")
