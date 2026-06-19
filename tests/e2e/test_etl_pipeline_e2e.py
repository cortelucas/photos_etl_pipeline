"""Teste E2E: dispara EtlPipeline.execute() real, mockando apenas a API externa.

TransformData e SendToDestiny rodam com sua lógica real e completa;
apenas a chamada HTTP é simulada, e o output_dir aponta para tmp_path
(diretório temporário do Pytest), mantendo data/output/ real intocado.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pytest_mock import MockerFixture

from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem
from photos_etl.load.send_to_destiny import SendToDestiny
from photos_etl.pipeline.etl_pipeline import EtlPipeline
from photos_etl.transform.transform_data import TransformData

SOURCE_URL = "https://jsonplaceholder.typicode.com/photos"
FIXED_NOW = datetime(2026, 6, 19, 12, 0, 0)


def fixed_clock() -> datetime:
    return FIXED_NOW


def build_fake_api_payload() -> list[dict[str, Any]]:
    return [
        {
            "albumId": 1,
            "id": 1,
            "title": "primeira foto do album 1",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        },
        {
            "albumId": 1,
            "id": 2,
            "title": "segunda foto do album 1",
            "url": "https://via.placeholder.com/600/771796",
            "thumbnailUrl": "https://via.placeholder.com/150/771796",
        },
        {
            "albumId": 2,
            "id": 3,
            "title": "primeira foto do album 2",
            "url": "https://via.placeholder.com/600/24f355",
            "thumbnailUrl": "https://via.placeholder.com/150/24f355",
        },
    ]


class TestEtlPipelineE2E:
    def test_executes_full_pipeline_and_generates_csv_files_per_album(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        fake_payload = build_fake_api_payload()

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = fake_payload
        mock_response.raise_for_status.return_value = None

        mock_http_client = mocker.Mock(spec=httpx.Client)
        mock_http_client.get.return_value = mock_response

        extract_step = ExtractDataFromOrigem(http_client=mock_http_client, source_url=SOURCE_URL)
        transform_step = TransformData(clock=fixed_clock)
        load_step = SendToDestiny(output_dir=tmp_path)

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
        )

        written_files = pipeline.execute()

        album_1_csv = tmp_path / "photos_album_1.csv"
        album_2_csv = tmp_path / "photos_album_2.csv"

        assert album_1_csv.exists()
        assert album_2_csv.exists()
        assert set(written_files) == {album_1_csv, album_2_csv}

        with album_1_csv.open(newline="", encoding="utf-8") as csv_file:
            album_1_rows = list(csv.DictReader(csv_file))

        with album_2_csv.open(newline="", encoding="utf-8") as csv_file:
            album_2_rows = list(csv.DictReader(csv_file))

        assert len(album_1_rows) == 2
        assert len(album_2_rows) == 1

        assert album_1_rows[0]["photo_id"] == "1"
        assert album_1_rows[0]["title"] == "primeira foto do album 1"
        assert album_1_rows[0]["image_url"] == "https://via.placeholder.com/600/92c952"
        assert album_1_rows[0]["processed_at"] == FIXED_NOW.isoformat()

        assert album_2_rows[0]["photo_id"] == "3"
        assert album_2_rows[0]["album_id"] == "2"

        mock_http_client.get.assert_called_once_with(SOURCE_URL)

    def test_running_pipeline_twice_does_not_duplicate_records(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        fake_payload = build_fake_api_payload()

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = fake_payload
        mock_response.raise_for_status.return_value = None

        mock_http_client = mocker.Mock(spec=httpx.Client)
        mock_http_client.get.return_value = mock_response

        def build_pipeline() -> EtlPipeline:
            extract_step = ExtractDataFromOrigem(
                http_client=mock_http_client, source_url=SOURCE_URL
            )
            transform_step = TransformData(clock=fixed_clock)
            load_step = SendToDestiny(output_dir=tmp_path)
            return EtlPipeline(
                extract_step=extract_step,
                transform_step=transform_step,
                load_step=load_step,
            )

        first_run_written = build_pipeline().execute()
        second_run_written = build_pipeline().execute()

        assert len(first_run_written) == 2
        assert second_run_written == []

        album_1_csv = tmp_path / "photos_album_1.csv"
        with album_1_csv.open(newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))

        assert len(rows) == 2
