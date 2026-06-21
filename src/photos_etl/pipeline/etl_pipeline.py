"""Classe orquestradora (esteira final) do pipeline de ETL de fotos."""

from pathlib import Path

from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem
from photos_etl.load.send_to_destiny import SendToDestiny
from photos_etl.pipeline.chunking import chunk_list
from photos_etl.transform.transform_data import TransformData


class EtlPipeline:
    """Coordena a execução completa do pipeline: extract -> transform -> load.

    Segue o padrão Command/Service Object: expõe um único método público
    `execute()`. Cada etapa é injetada via construtor (DIP), permitindo
    substituir qualquer uma delas por um mock/fake em testes.

    O transform e o load são executados em lotes (batch_size), para que
    o uso de memória permaneça controlado mesmo se a quantidade de
    registros extraídos crescer significativamente.
    """

    def __init__(
        self,
        extract_step: ExtractDataFromOrigem,
        transform_step: TransformData,
        load_step: SendToDestiny,
        batch_size: int = 500,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size deve ser maior que zero.")

        self._extract_step = extract_step
        self._transform_step = transform_step
        self._load_step = load_step
        self._batch_size = batch_size

    def execute(self) -> list[Path]:
        """Executa a esteira completa e retorna os arquivos CSV gerados/atualizados.

        Cada caminho aparece no máximo uma vez, mesmo que o arquivo tenha
        recebido registros novos em mais de um lote durante esta execução.
        """
        raw_photos = self._extract_step.execute()

        written_files: set[Path] = set()
        for photo_batch in chunk_list(raw_photos, self._batch_size):
            photo_records = self._transform_step.execute(photo_batch)
            batch_written_files = self._load_step.execute(photo_records)
            written_files.update(batch_written_files)

        return sorted(written_files)
