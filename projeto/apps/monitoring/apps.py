import threading
import time
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 30 * 60  # 30 minutos


def _run_check_risks():
    from django.core.management import call_command
    while True:
        try:
            logger.info("[monitoring] Executando check_risks...")
            call_command('check_risks')
        except Exception as e:
            logger.error(f"[monitoring] Erro no check_risks: {e}")
        time.sleep(INTERVAL_SECONDS)


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'

    def ready(self):
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return

        thread = threading.Thread(target=_run_check_risks, daemon=True)
        thread.start()
        logger.info("[monitoring] Scheduler iniciado (intervalo: 30min)")
