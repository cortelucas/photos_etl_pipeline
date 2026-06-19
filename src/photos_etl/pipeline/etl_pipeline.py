"""Classe orquestradora (esteira final) do pipeline de ETL de fotos."""

from pathlib import Path

from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem
from photos_etl.load.send_to_destiny import SendToDestiny
from photos_etl.transform.transform_data import TransformData


class EtlPipeline:
    """Coordena a execução completa do pipeline: extract -> transform -> load.

    Segue o padrão Command/Service Object: expõe um único método público
    `execute()`. Cada etapa é injetada via construtor (DIP), permitindo
    substituir qualquer uma delas por um mock/fake em testes.
    """

    def __init__(
        self,
        extract_step: ExtractDataFromOrigem,
        transform_step: TransformData,
        load_step: SendToDestiny,
    ) -> None:
        self._extract_step = extract_step
        self._transform_step = transform_step
        self._load_step = load_step

    def execute(self) -> list[Path]:
        """Executa a esteira completa e retorna os arquivos CSV gerados/atualizados."""
        raw_photos = self._extract_step.execute()
        photo_records = self._transform_step.execute(raw_photos)
        written_files: list[Path] = self._load_step.execute(photo_records)
        return written_files
