"""Camada de carga (load) do pipeline de ETL de fotos."""

from photos_etl.load.send_to_destiny import SendToDestiny

__all__ = ["SendToDestiny"]
