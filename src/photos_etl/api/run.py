"""Wrapper para rodar o servidor FastAPI via script do Poetry."""

import uvicorn


def run_server() -> None:
    uvicorn.run("photos_etl.api.app:app", host="0.0.0.0", port=8000, reload=False)  # noqa: S104
