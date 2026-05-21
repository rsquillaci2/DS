#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Motor de Sinistralidade ANS — Configuração de Agendamento
# ═══════════════════════════════════════════════════════════════
#
# Este script configura o cron para execução automática do pipeline.
#
# Calendário de publicação da ANS:
#   - DIOPS: Trimestral (~3 meses após o fim do trimestre)
#     - 1T: publicado em Jun | 2T: Set | 3T: Dez | 4T: Mar
#   - SIB: Mensal (competência ~2 meses de atraso)
#
# Agendamento recomendado:
#   - Pipeline completo: Trimestral (Jan, Abr, Jul, Out)
#   - Verificação de novos dados: Mensal (dia 15)
#
# Uso:
#   chmod +x pipeline/crontab_config.sh
#   ./pipeline/crontab_config.sh install   # Instala o cron
#   ./pipeline/crontab_config.sh remove    # Remove o cron
#   ./pipeline/crontab_config.sh status    # Mostra status
# ═══════════════════════════════════════════════════════════════

PIPELINE_DIR="/home/ubuntu/mvp_sinistralidade"
PYTHON="/usr/bin/python3"
LOG_DIR="${PIPELINE_DIR}/pipeline/logs"

# Criar diretório de logs se não existir
mkdir -p "$LOG_DIR"

CRON_COMMENT="# Motor Sinistralidade ANS - Pipeline Automático"
CRON_TRIMESTRAL="0 3 1 1,4,7,10 * cd ${PIPELINE_DIR} && ${PYTHON} pipeline/run_pipeline.py --full >> ${LOG_DIR}/cron_\$(date +\\%Y\\%m\\%d).log 2>&1"
CRON_MENSAL="0 6 15 * * cd ${PIPELINE_DIR} && ${PYTHON} pipeline/run_pipeline.py --download-only >> ${LOG_DIR}/cron_check_\$(date +\\%Y\\%m\\%d).log 2>&1"

case "$1" in
    install)
        echo "Instalando cron jobs..."
        # Remove entradas anteriores
        crontab -l 2>/dev/null | grep -v "Motor Sinistralidade" | grep -v "run_pipeline.py" > /tmp/crontab_temp
        # Adiciona novas
        echo "" >> /tmp/crontab_temp
        echo "$CRON_COMMENT" >> /tmp/crontab_temp
        echo "$CRON_TRIMESTRAL" >> /tmp/crontab_temp
        echo "$CRON_MENSAL" >> /tmp/crontab_temp
        crontab /tmp/crontab_temp
        rm /tmp/crontab_temp
        echo "✅ Cron instalado:"
        echo "   - Pipeline completo: 1º dia de Jan/Abr/Jul/Out às 03:00"
        echo "   - Verificação mensal: Dia 15 de cada mês às 06:00"
        crontab -l | grep -A2 "Motor Sinistralidade"
        ;;
    remove)
        echo "Removendo cron jobs..."
        crontab -l 2>/dev/null | grep -v "Motor Sinistralidade" | grep -v "run_pipeline.py" | crontab -
        echo "✅ Cron removido"
        ;;
    status)
        echo "═══ Status do Pipeline ═══"
        echo ""
        echo "Cron jobs ativos:"
        crontab -l 2>/dev/null | grep "run_pipeline" || echo "  (nenhum)"
        echo ""
        echo "Últimos logs:"
        ls -lt ${LOG_DIR}/*.log 2>/dev/null | head -5 || echo "  (nenhum)"
        echo ""
        echo "Estado do pipeline:"
        cd ${PIPELINE_DIR} && ${PYTHON} pipeline/run_pipeline.py --status 2>/dev/null || echo "  (erro ao ler estado)"
        ;;
    *)
        echo "Uso: $0 {install|remove|status}"
        exit 1
        ;;
esac
