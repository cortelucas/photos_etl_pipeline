"""Scheduler em background que dispara o pipeline periodicamente via cron."""

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from photos_etl.config import Settings


def build_scheduler(settings: Settings, job_func: Callable[[], None]) -> BackgroundScheduler:
    """Monta (mas não inicia) um BackgroundScheduler com o job do pipeline.

    A função do job é injetada via parâmetro (DIP), permitindo testes
    substituírem a execução real do pipeline por um mock/spy, sem
    precisar mockar internals do APScheduler.
    """
    scheduler = BackgroundScheduler(timezone="UTC")
    trigger = CronTrigger.from_crontab(settings.cron_expression, timezone="UTC")

    scheduler.add_job(
        func=job_func,
        trigger=trigger,
        id="etl_pipeline_job",
        replace_existing=True,
    )

    return scheduler
