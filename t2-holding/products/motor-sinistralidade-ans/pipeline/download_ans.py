"""
Pipeline de Atualização — Módulo 1: Download de Dados ANS
==========================================================
Baixa automaticamente os dados mais recentes do DIOPS e SIB
do portal de dados abertos da ANS.

Fontes:
- DIOPS: https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/{ano}/{trimestre}.zip
- SIB:   https://dadosabertos.ans.gov.br/FTP/PDA/dados_de_beneficiarios_por_operadora/sib_ativo_{uf}.zip

Calendário ANS:
- DIOPS: Publicado trimestralmente (~3 meses após o fim do trimestre)
  - 1T: disponível em ~Jun | 2T: ~Set | 3T: ~Dez | 4T: ~Mar do ano seguinte
- SIB: Atualizado mensalmente (competência ~2 meses de atraso)

Sprint 10 — Mai/2026
Autor: Ricardo Squillaci — Tallent Two Financial Holding
"""

import os
import sys
import json
import zipfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# ─── Configuração ────────────────────────────────────────────────────────────

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
DATA_DIR = BASE_DIR / "data"
DIOPS_DIR = DATA_DIR / "diops"
DIOPS_HIST_DIR = DATA_DIR / "diops_historico"
SIB_DIR = DATA_DIR / "sib"
LOGS_DIR = BASE_DIR / "pipeline" / "logs"
STATE_FILE = BASE_DIR / "pipeline" / "pipeline_state.json"

# URLs base
DIOPS_BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis"
SIB_BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/dados_de_beneficiarios_por_operadora"

# UFs para download do SIB (todas as 27)
UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]

# UFs prioritárias (Top 10 por volume — cobertura >90% do mercado)
UFS_PRIORITARIAS = ["SP", "RJ", "MG", "PR", "RS", "BA", "SC", "GO", "PE", "DF"]

# Logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ─── Estado do Pipeline ──────────────────────────────────────────────────────

def load_state() -> dict:
    """Carrega o estado do pipeline (último download, versões, etc.)."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "ultimo_diops": None,
        "ultimo_sib": None,
        "diops_trimestres_baixados": [],
        "sib_ufs_baixadas": [],
        "ultima_execucao": None,
        "historico_execucoes": []
    }


def save_state(state: dict):
    """Salva o estado do pipeline."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)


# ─── Funções de Download ─────────────────────────────────────────────────────

def download_file(url: str, dest_path: Path, timeout: int = 300) -> bool:
    """Baixa um arquivo com retry e verificação de integridade."""
    for attempt in range(3):
        try:
            logger.info(f"  Baixando: {url}")
            response = requests.get(url, timeout=timeout, stream=True)
            
            if response.status_code == 404:
                logger.warning(f"  Arquivo não encontrado (404): {url}")
                return False
            
            response.raise_for_status()
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
            
            if total_size > 0 and downloaded != total_size:
                logger.warning(f"  Download incompleto: {downloaded}/{total_size} bytes")
                continue
            
            logger.info(f"  ✅ Salvo: {dest_path} ({downloaded / 1e6:.1f} MB)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"  Tentativa {attempt + 1}/3 falhou: {e}")
            if attempt < 2:
                import time
                time.sleep(5 * (attempt + 1))
    
    logger.error(f"  ❌ Falha após 3 tentativas: {url}")
    return False


def extract_zip(zip_path: Path, dest_dir: Path) -> list:
    """Extrai ZIP e retorna lista de arquivos extraídos."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_dir)
            extracted = zf.namelist()
            logger.info(f"  Extraído: {len(extracted)} arquivo(s) de {zip_path.name}")
            return extracted
    except zipfile.BadZipFile:
        logger.error(f"  ❌ ZIP corrompido: {zip_path}")
        return []


# ─── Download DIOPS ──────────────────────────────────────────────────────────

def detectar_trimestre_mais_recente() -> tuple:
    """Detecta qual é o trimestre DIOPS mais recente disponível na ANS.
    
    Calendário de publicação:
    - 1T: publicado em Jun (~3 meses após)
    - 2T: publicado em Set
    - 3T: publicado em Dez
    - 4T: publicado em Mar do ano seguinte
    """
    hoje = datetime.now()
    
    # Tenta do mais recente para o mais antigo
    candidatos = []
    for delta_meses in range(0, 12):
        data_ref = hoje - timedelta(days=delta_meses * 30)
        ano = data_ref.year
        
        # Mapeamento: mês de publicação → trimestre
        # Mar → 4T do ano anterior | Jun → 1T | Set → 2T | Dez → 3T
        if data_ref.month >= 1 and data_ref.month <= 3:
            candidatos.append((ano - 1, 4))
        elif data_ref.month >= 4 and data_ref.month <= 6:
            candidatos.append((ano, 1))
        elif data_ref.month >= 7 and data_ref.month <= 9:
            candidatos.append((ano, 2))
        else:
            candidatos.append((ano, 3))
    
    # Remove duplicatas mantendo ordem
    seen = set()
    candidatos_unicos = []
    for c in candidatos:
        if c not in seen:
            seen.add(c)
            candidatos_unicos.append(c)
    
    return candidatos_unicos


def download_diops(force: bool = False, trimestres_extras: int = 0) -> dict:
    """Baixa o DIOPS mais recente e opcionalmente trimestres anteriores.
    
    Args:
        force: Se True, baixa mesmo se já foi baixado
        trimestres_extras: Quantos trimestres anteriores baixar além do mais recente
    
    Returns:
        Dict com status do download
    """
    state = load_state()
    result = {"success": False, "trimestres_baixados": [], "erros": []}
    
    candidatos = detectar_trimestre_mais_recente()
    trimestres_alvo = candidatos[:1 + trimestres_extras]
    
    logger.info(f"═══ DOWNLOAD DIOPS ═══")
    logger.info(f"Trimestres alvo: {trimestres_alvo}")
    
    for ano, tri in trimestres_alvo:
        trimestre_id = f"{tri}T{ano}"
        
        # Verifica se já foi baixado
        if not force and trimestre_id in state.get("diops_trimestres_baixados", []):
            logger.info(f"  ⏭️  {trimestre_id} já baixado, pulando...")
            continue
        
        # URL do ZIP
        url = f"{DIOPS_BASE_URL}/{ano}/{trimestre_id}.zip"
        zip_path = DIOPS_DIR / f"{trimestre_id}.zip"
        
        if download_file(url, zip_path):
            # Extrair
            extracted = extract_zip(zip_path, DIOPS_DIR)
            if extracted:
                # Copiar CSV para diops_historico
                for fname in extracted:
                    if fname.endswith('.csv'):
                        src = DIOPS_DIR / fname
                        dst = DIOPS_HIST_DIR / f"{trimestre_id}.csv"
                        if src.exists():
                            import shutil
                            shutil.copy2(src, dst)
                            logger.info(f"  Copiado para histórico: {dst.name}")
                
                result["trimestres_baixados"].append(trimestre_id)
                if trimestre_id not in state.get("diops_trimestres_baixados", []):
                    state.setdefault("diops_trimestres_baixados", []).append(trimestre_id)
            else:
                result["erros"].append(f"Falha ao extrair {trimestre_id}")
        else:
            result["erros"].append(f"Falha ao baixar {trimestre_id}")
    
    state["ultimo_diops"] = datetime.now().isoformat()
    save_state(state)
    
    result["success"] = len(result["erros"]) == 0
    logger.info(f"DIOPS concluído: {len(result['trimestres_baixados'])} novos trimestres")
    return result


# ─── Download SIB ────────────────────────────────────────────────────────────

def download_sib(ufs: Optional[list] = None, force: bool = False) -> dict:
    """Baixa o SIB consolidado por UF.
    
    Args:
        ufs: Lista de UFs para baixar (None = prioritárias)
        force: Se True, baixa mesmo se já foi baixado
    
    Returns:
        Dict com status do download
    """
    state = load_state()
    result = {"success": False, "ufs_baixadas": [], "erros": [], "tamanho_total_mb": 0}
    
    if ufs is None:
        ufs = UFS_PRIORITARIAS
    
    logger.info(f"═══ DOWNLOAD SIB ═══")
    logger.info(f"UFs alvo: {ufs}")
    
    for uf in ufs:
        uf_upper = uf.upper()
        
        # Verifica se já foi baixado (e se não é forçado)
        if not force and uf_upper in state.get("sib_ufs_baixadas", []):
            logger.info(f"  ⏭️  SIB {uf_upper} já baixado, pulando...")
            continue
        
        url = f"{SIB_BASE_URL}/sib_ativo_{uf_upper}.zip"
        zip_path = SIB_DIR / f"sib_ativo_{uf_upper}.zip"
        
        if download_file(url, zip_path, timeout=600):
            # Extrair
            extracted = extract_zip(zip_path, SIB_DIR)
            if extracted:
                result["ufs_baixadas"].append(uf_upper)
                result["tamanho_total_mb"] += zip_path.stat().st_size / 1e6
                if uf_upper not in state.get("sib_ufs_baixadas", []):
                    state.setdefault("sib_ufs_baixadas", []).append(uf_upper)
            else:
                result["erros"].append(f"Falha ao extrair SIB {uf_upper}")
        else:
            result["erros"].append(f"Falha ao baixar SIB {uf_upper}")
    
    state["ultimo_sib"] = datetime.now().isoformat()
    save_state(state)
    
    result["success"] = len(result["erros"]) == 0
    logger.info(f"SIB concluído: {len(result['ufs_baixadas'])} UFs ({result['tamanho_total_mb']:.0f} MB)")
    return result


# ─── Entry Point ─────────────────────────────────────────────────────────────

def run_downloads(diops: bool = True, sib: bool = True, 
                  sib_ufs: Optional[list] = None, force: bool = False) -> dict:
    """Executa downloads completos.
    
    Args:
        diops: Se True, baixa DIOPS
        sib: Se True, baixa SIB
        sib_ufs: Lista de UFs (None = prioritárias)
        force: Se True, redownload mesmo se já existe
    """
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  PIPELINE ANS — MÓDULO 1: DOWNLOAD          ║")
    logger.info(f"║  Execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}       ║")
    logger.info("╚══════════════════════════════════════════════╝")
    
    results = {"diops": None, "sib": None, "timestamp": datetime.now().isoformat()}
    
    if diops:
        results["diops"] = download_diops(force=force)
    
    if sib:
        results["sib"] = download_sib(ufs=sib_ufs, force=force)
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download de dados ANS")
    parser.add_argument("--diops", action="store_true", default=True, help="Baixar DIOPS")
    parser.add_argument("--sib", action="store_true", default=True, help="Baixar SIB")
    parser.add_argument("--sib-ufs", nargs="+", help="UFs específicas para SIB")
    parser.add_argument("--sib-todas", action="store_true", help="Baixar SIB de todas as 27 UFs")
    parser.add_argument("--force", action="store_true", help="Forçar redownload")
    
    args = parser.parse_args()
    
    sib_ufs = UFS if args.sib_todas else args.sib_ufs
    results = run_downloads(diops=args.diops, sib=args.sib, sib_ufs=sib_ufs, force=args.force)
    
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
