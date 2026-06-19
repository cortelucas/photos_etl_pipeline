"""Configurações do pipeline, centralizadas via variáveis de ambiente."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente (ou arquivo .env).

    Centraliza todos os parâmetros que antes eram constantes fixas no
    código, permitindo ajustar comportamento do pipeline sem alterar
    código-fonte (ex: tamanho de lote, agenda do scheduler, destino).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    source_url: str = Field(
        default="https://jsonplaceholder.typicode.com/photos",
        description="URL da API de origem dos dados de fotos.",
    )
    output_dir: Path = Field(
        default=Path("data/output"),
        description="Diretório de destino dos arquivos CSV gerados.",
    )
    batch_size: int = Field(
        default=500,
        gt=0,
        description="Tamanho do lote para processamento de transform/load.",
    )
    cron_expression: str = Field(
        default="0 * * * *",
        description="Expressão cron (5 campos) para o scheduler do pipeline.",
    )


def get_settings() -> Settings:
    """Factory simples para Settings, facilitando override/mock em testes."""
    return Settings()
