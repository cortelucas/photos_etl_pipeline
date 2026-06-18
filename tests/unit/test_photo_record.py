"""Testes unitários do PhotoRecord."""

import pytest
from pydantic import ValidationError

from photos_etl.entities.photo_record import PhotoRecord


class TestPhotoRecord:
    def test_creates_instance_with_valid_data(self) -> None:
        record = PhotoRecord(
            album_id=1,
            photo_id=1,
            title="accusamus beatae ad facilis cum similique qui sunt",
            image_url="https://via.placeholder.com/600/92c952",
            thumbnail_url="https://via.placeholder.com/150/92c952",
        )

        assert record.album_id == 1
        assert record.photo_id == 1
        assert record.title == "accusamus beatae ad facilis cum similique qui sunt"

    def test_raises_validation_error_when_photo_id_is_not_an_integer(self) -> None:
        with pytest.raises(ValidationError):
            PhotoRecord(
                album_id=1,
                photo_id="not-an-integer",
                title="titulo qualquer",
                image_url="https://via.placeholder.com/600/92c952",
                thumbnail_url="https://via.placeholder.com/150/92c952",
            )

    def test_instance_is_immutable(self) -> None:
        record = PhotoRecord(
            album_id=1,
            photo_id=1,
            title="titulo qualquer",
            image_url="https://via.placeholder.com/600/92c952",
            thumbnail_url="https://via.placeholder.com/150/92c952",
        )

        with pytest.raises(ValidationError):
            record.title = "outro titulo"
