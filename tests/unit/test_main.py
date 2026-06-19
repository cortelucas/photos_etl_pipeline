"""Testes unitários do entrypoint main.py."""

import csv
from pathlib import Path
from typing import Any

import httpx
import pytest
from pytest_mock import MockerFixture

from photos_etl.main import main, run_pipeline


def build_fake_api_payload() -> list[dict[str, Any]]:
    return [
        {
            "albumId": 1,
            "id": 1,
            "title": "foto de teste",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }
    ]


class TestRunPipeline:
    def test_run_pipeline_returns_written_csv_files(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = build_fake_api_payload()
        mock_response.raise_for_status.return_value = None

        mock_http_client = mocker.Mock(spec=httpx.Client)
        mock_http_client.get.return_value = mock_response

        written_files = run_pipeline(http_client=mock_http_client, output_dir=tmp_path)

        assert written_files == [tmp_path / "photos_album_1.csv"]

        with (tmp_path / "photos_album_1.csv").open(newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))

        assert len(rows) == 1
        assert rows[0]["title"] == "foto de teste"


class TestMain:
    def test_main_creates_real_http_client_and_prints_summary(
        self, mocker: MockerFixture, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = build_fake_api_payload()
        mock_response.raise_for_status.return_value = None

        mock_http_client_instance = mocker.Mock(spec=httpx.Client)
        mock_http_client_instance.get.return_value = mock_response
        mock_http_client_instance.__enter__ = mocker.Mock(return_value=mock_http_client_instance)
        mock_http_client_instance.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("photos_etl.main.httpx.Client", return_value=mock_http_client_instance)
        mocker.patch("photos_etl.main.OUTPUT_DIR", tmp_path)

        main()

        captured = capsys.readouterr()
        assert "Pipeline concluído." in captured.out
        assert "1 arquivo(s)" in captured.out
        assert (tmp_path / "photos_album_1.csv").exists()
