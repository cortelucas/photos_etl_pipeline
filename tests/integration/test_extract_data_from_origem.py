"""Testes de integração de ExtractDataFromOrigem, validando comportamento
contra falhas de rede, timeout e payloads corrompidos, usando mocks do httpx.Client.
"""

import httpx
import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from photos_etl.entities.photo_dto import PhotoDTO
from photos_etl.extract.extract_data_from_origem import ExtractDataFromOrigem

SOURCE_URL = "https://jsonplaceholder.typicode.com/photos"


class TestExtractDataFromOrigem:
    def test_returns_list_of_photo_dto_on_successful_response(self, mocker: MockerFixture) -> None:
        valid_payload = [
            {
                "albumId": 1,
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                "thumbnailUrl": "https://via.placeholder.com/150/92c952",
            },
            {
                "albumId": 1,
                "id": 2,
                "title": "outro titulo",
                "url": "https://via.placeholder.com/600/771796",
                "thumbnailUrl": "https://via.placeholder.com/150/771796",
            },
        ]

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = valid_payload
        mock_response.raise_for_status.return_value = None

        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)
        result = sut.execute()

        assert len(result) == 2
        assert all(isinstance(item, PhotoDTO) for item in result)
        assert result[0].album_id == 1
        mock_client.get.assert_called_once_with(SOURCE_URL)

    def test_raises_http_status_error_when_api_returns_error_status(
        self, mocker: MockerFixture
    ) -> None:
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=mocker.Mock(spec=httpx.Request),
            response=mocker.Mock(spec=httpx.Response, status_code=500),
        )

        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises(httpx.HTTPStatusError):
            sut.execute()

    def test_raises_timeout_exception_when_request_times_out(self, mocker: MockerFixture) -> None:
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises(httpx.TimeoutException):
            sut.execute()

    def test_raises_connect_error_when_network_is_unreachable(self, mocker: MockerFixture) -> None:
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises(httpx.ConnectError):
            sut.execute()

    def test_raises_validation_error_when_payload_has_missing_field(
        self, mocker: MockerFixture
    ) -> None:
        corrupted_payload = [
            {
                "albumId": 1,
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                # thumbnailUrl ausente de propósito
            }
        ]

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = corrupted_payload
        mock_response.raise_for_status.return_value = None

        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises(ValidationError):
            sut.execute()

    def test_raises_validation_error_when_payload_has_wrong_type(
        self, mocker: MockerFixture
    ) -> None:
        corrupted_payload = [
            {
                "albumId": "deveria-ser-int",
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                "thumbnailUrl": "https://via.placeholder.com/150/92c952",
            }
        ]

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = corrupted_payload
        mock_response.raise_for_status.return_value = None

        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises(ValidationError):
            sut.execute()

    def test_raises_value_error_when_payload_is_not_a_list(self, mocker: MockerFixture) -> None:
        malformed_payload = {"error": "unexpected single object instead of list"}

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.json.return_value = malformed_payload
        mock_response.raise_for_status.return_value = None

        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        sut = ExtractDataFromOrigem(http_client=mock_client, source_url=SOURCE_URL)

        with pytest.raises((ValidationError, TypeError)):
            sut.execute()
