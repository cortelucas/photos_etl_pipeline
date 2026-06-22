"""Testes de integração da API FastAPI, validando o endpoint /start."""

from pathlib import Path

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from photos_etl.api.app import app
from photos_etl.config import Settings

client = TestClient(app)


def build_fake_api_payload() -> list[dict[str, str | int]]:
    return [
        {
            "albumId": 1,
            "id": 1,
            "title": "foto de teste",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }
    ]


class TestHealthCheck:
    def test_returns_ok_status(self) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestStartEndpoint:
    def test_returns_accepted_status_immediately(self, mocker: MockerFixture) -> None:
        # Mocka a execução real para não bater na API/disco verdadeiros neste teste.
        mocker.patch("photos_etl.api.app._execute_pipeline_in_background")

        response = client.get("/start")

        assert response.status_code == 200
        assert response.json() == {
            "status": "accepted",
            "message": "Pipeline disparado em background.",
        }

    def test_triggers_pipeline_execution_as_background_task(self, mocker: MockerFixture) -> None:
        mock_execute = mocker.patch("photos_etl.api.app._execute_pipeline_in_background")

        client.get("/start")

        # TestClient executa BackgroundTasks de forma síncrona ao final da resposta,
        # então neste ponto a tarefa já deve ter sido chamada.
        mock_execute.assert_called_once()

    def test_runs_real_pipeline_end_to_end_with_mocked_http_and_settings(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Valida a integração real entre /start e o pipeline, mockando apenas
        a chamada HTTP externa e o diretório de output (via Settings)."""
        import httpx

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = build_fake_api_payload()
        mock_response.raise_for_status.return_value = None

        mock_http_client_instance = mocker.Mock(spec=httpx.Client)
        mock_http_client_instance.get.return_value = mock_response
        mock_http_client_instance.__enter__ = mocker.Mock(return_value=mock_http_client_instance)
        mock_http_client_instance.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("photos_etl.api.app.httpx.Client", return_value=mock_http_client_instance)
        mocker.patch(
            "photos_etl.api.app.get_settings",
            return_value=Settings(output_dir=tmp_path, batch_size=500),
        )

        response = client.get("/start")

        assert response.status_code == 200
        assert (tmp_path / "photos_album_1.csv").exists()
