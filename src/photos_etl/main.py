"""Ponto de entrada do pipeline de ETL de fotos."""

from pathlib import Path

import httpx

from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem
from photos_etl.load.send_to_destiny import SendToDestiny
from photos_etl.pipeline.etl_pipeline import EtlPipeline
from photos_etl.transform.transform_data import TransformData

SOURCE_URL = "https://jsonplaceholder.typicode.com/photos"
OUTPUT_DIR = Path("data/output")


def main() -> None:
    with httpx.Client(timeout=30.0) as http_client:
        extract_step = ExtractDataFromOrigem(http_client=http_client, source_url=SOURCE_URL)
        transform_step = TransformData()
        load_step = SendToDestiny(output_dir=OUTPUT_DIR)

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
        )

        written_files = pipeline.execute()

    print(f"Pipeline concluído. {len(written_files)} arquivo(s) CSV gerado(s)/atualizado(s):")
    for file_path in written_files:
        print(f"  - {file_path}")


if __name__ == "__main__":
    main()
