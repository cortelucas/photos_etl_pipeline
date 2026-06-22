"""Aplicação FastAPI expondo o pipeline de ETL via HTTP."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, FastAPI

from photos_etl.config import get_settings
from photos_etl.main import run_pipeline
from photos_etl.scheduler import build_scheduler


def _execute_pipeline_in_background() -> None:
    """Executa o pipeline completo, criando seu próprio httpx.Client.

    Função isolada para ser usada tanto pelo endpoint /start (via
    BackgroundTasks) quanto pelo scheduler, garantindo que ambos os
    gatilhos disparem exatamente a mesma execução.
    """
    settings = get_settings()
    with httpx.Client(timeout=30.0) as http_client:
        written_files = run_pipeline(http_client=http_client, settings=settings)

    print(f"[pipeline] Concluído. {len(written_files)} arquivo(s) gerado(s)/atualizado(s).")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicia o scheduler quando a aplicação sobe, e o encerra ao desligar."""
    settings = get_settings()
    scheduler = build_scheduler(settings=settings, job_func=_execute_pipeline_in_background)
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Photos ETL Pipeline", version="1.0.0", lifespan=lifespan)


@app.get("/start")
def start_pipeline(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Dispara a execução do pipeline em background e responde imediatamente."""
    background_tasks.add_task(_execute_pipeline_in_background)
    return {"status": "accepted", "message": "Pipeline disparado em background."}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint simples de verificação de saúde da aplicação."""
    return {"status": "ok"}
