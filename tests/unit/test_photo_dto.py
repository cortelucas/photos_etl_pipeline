"""Testes unitários do PhotoDTO."""

import pytest
from pydantic import ValidationError

from photos_etl.entities.photo_dto import PhotoDTO


class TestPhotoDTO:
    def test_creates_instance_from_api_camel_case_payload(self) -> None:
        payload = {
            "albumId": 1,
            "id": 1,
            "title": "accusamus beatae ad facilis cum similique qui sunt",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }

        dto = PhotoDTO.model_validate(payload)

        assert dto.album_id == 1
        assert dto.id == 1
        assert dto.title == payload["title"]
        assert str(dto.url) == payload["url"]
        assert str(dto.thumbnail_url) == payload["thumbnailUrl"]

    def test_creates_instance_from_snake_case_payload(self) -> None:
        dto = PhotoDTO.model_validate(
            {
                "album_id": 2,
                "id": 51,
                "title": "non sunt voluptatem placeat consequuntur rem incidunt",
                "url": "https://via.placeholder.com/600/8e973b",
                "thumbnail_url": "https://via.placeholder.com/150/8e973b",
            }
        )

        assert dto.album_id == 2
        assert dto.id == 51

    def test_raises_validation_error_when_album_id_is_not_an_integer(self) -> None:
        payload = {
            "albumId": "not-an-integer",
            "id": 1,
            "title": "titulo qualquer",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }

        with pytest.raises(ValidationError):
            PhotoDTO.model_validate(payload)

    def test_raises_validation_error_when_url_is_malformed(self) -> None:
        payload = {
            "albumId": 1,
            "id": 1,
            "title": "titulo qualquer",
            "url": "isso-nao-e-uma-url",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }

        with pytest.raises(ValidationError):
            PhotoDTO.model_validate(payload)

    def test_raises_validation_error_when_required_field_is_missing(self) -> None:
        payload = {
            "albumId": 1,
            "id": 1,
            "title": "titulo qualquer",
            "url": "https://via.placeholder.com/600/92c952",
            # thumbnailUrl ausente de propósito
        }

        with pytest.raises(ValidationError):
            PhotoDTO.model_validate(payload)

    def test_instance_is_immutable(self) -> None:
        dto = PhotoDTO.model_validate(
            {
                "albumId": 1,
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                "thumbnailUrl": "https://via.placeholder.com/150/92c952",
            }
        )

        with pytest.raises(ValidationError):
            dto.album_id = 999
