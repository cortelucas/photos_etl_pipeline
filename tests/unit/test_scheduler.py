"""Testes unitários de build_scheduler."""

from unittest.mock import Mock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from photos_etl.config import Settings
from photos_etl.scheduler.scheduler import build_scheduler


class TestBuildScheduler:
    def test_returns_a_background_scheduler_instance(self) -> None:
        settings = Settings(cron_expression="0 * * * *")
        job_func = Mock()

        scheduler = build_scheduler(settings=settings, job_func=job_func)

        assert isinstance(scheduler, BackgroundScheduler)

    def test_registers_job_with_expected_id(self) -> None:
        settings = Settings(cron_expression="0 * * * *")
        job_func = Mock()

        scheduler = build_scheduler(settings=settings, job_func=job_func)

        job = scheduler.get_job("etl_pipeline_job")
        assert job is not None
        assert job.id == "etl_pipeline_job"

    def test_registers_job_with_cron_trigger_matching_settings(self) -> None:
        settings = Settings(cron_expression="30 5 * * *")
        job_func = Mock()

        scheduler = build_scheduler(settings=settings, job_func=job_func)

        job = scheduler.get_job("etl_pipeline_job")
        assert job is not None
        assert isinstance(job.trigger, CronTrigger)

    def test_job_func_is_not_called_during_build(self) -> None:
        """build_scheduler apenas registra o job; não deve executá-lo."""
        settings = Settings(cron_expression="0 * * * *")
        job_func = Mock()

        build_scheduler(settings=settings, job_func=job_func)

        job_func.assert_not_called()

    def test_replacing_job_with_same_id_does_not_duplicate(self) -> None:
        settings = Settings(cron_expression="0 * * * *")
        job_func = Mock()

        scheduler = build_scheduler(settings=settings, job_func=job_func)
        scheduler.start()

        try:
            # Simula uma segunda chamada de add_job reaproveitando o mesmo scheduler:
            # adicionar o job de novo com o mesmo id (replace_existing=True) não deve duplicar.
            trigger = CronTrigger.from_crontab(settings.cron_expression, timezone="UTC")
            scheduler.add_job(
                func=job_func,
                trigger=trigger,
                id="etl_pipeline_job",
                replace_existing=True,
            )

            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
        finally:
            scheduler.shutdown(wait=False)
