"""Ponto de entrada do pipeline de ETL de fotos."""

from pathlib import Path

import httpx

from photos_etl.config import Settings, get_settings
from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem
from photos_etl.load.send_to_destiny import SendToDestiny
from photos_etl.pipeline.etl_pipeline import EtlPipeline
from photos_etl.transform.transform_data import TransformData


def run_pipeline(http_client: httpx.Client, settings: Settings) -> list[Path]:
    """Monta e executa o EtlPipeline com as dependências concretas de produção.

    O http_client é recebido por parâmetro (não instanciado aqui) para que
    main() controle seu ciclo de vida via context manager, e para que testes
    possam injetar um client mockado sem precisar interceptar a criação dele.
    """
    extract_step = ExtractDataFromOrigem(http_client=http_client, source_url=settings.source_url)
    transform_step = TransformData()
    load_step = SendToDestiny(output_dir=settings.output_dir)

    pipeline = EtlPipeline(
        extract_step=extract_step,
        transform_step=transform_step,
        load_step=load_step,
        batch_size=settings.batch_size,
    )

    written_files: list[Path] = pipeline.execute()
    return written_files


def main() -> None:
    settings = get_settings()

    with httpx.Client(timeout=30.0) as http_client:
        written_files = run_pipeline(http_client=http_client, settings=settings)

    print(f"Pipeline concluído. {len(written_files)} arquivo(s) CSV gerado(s)/atualizado(s):")
    for file_path in written_files:
        print(f"  - {file_path}")


if __name__ == "__main__":
    main()
