"""Testes unitários de TransformData."""

from datetime import datetime

from photos_etl.entities.photo_dto import PhotoDTO
from photos_etl.entities.photo_record import PhotoRecord
from photos_etl.transform.transform_data import TransformData

FIXED_NOW = datetime(2026, 6, 19, 12, 0, 0)


def fixed_clock() -> datetime:
    return FIXED_NOW


class TestTransformData:
    def test_maps_single_photo_dto_to_photo_record(self) -> None:
        photo_dto = PhotoDTO.model_validate(
            {
                "albumId": 1,
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                "thumbnailUrl": "https://via.placeholder.com/150/92c952",
            }
        )

        sut = TransformData(clock=fixed_clock)
        result = sut.execute([photo_dto])

        assert len(result) == 1
        assert isinstance(result[0], PhotoRecord)
        assert result[0].album_id == 1
        assert result[0].photo_id == 1
        assert result[0].title == "titulo qualquer"
        assert result[0].image_url == "https://via.placeholder.com/600/92c952"
        assert result[0].thumbnail_url == "https://via.placeholder.com/150/92c952"
        assert result[0].processed_at == FIXED_NOW

    def test_maps_multiple_photo_dtos_preserving_order(self) -> None:
        photo_dtos = [
            PhotoDTO.model_validate(
                {
                    "albumId": 1,
                    "id": 1,
                    "title": "primeira foto",
                    "url": "https://via.placeholder.com/600/92c952",
                    "thumbnailUrl": "https://via.placeholder.com/150/92c952",
                }
            ),
            PhotoDTO.model_validate(
                {
                    "albumId": 2,
                    "id": 2,
                    "title": "segunda foto",
                    "url": "https://via.placeholder.com/600/771796",
                    "thumbnailUrl": "https://via.placeholder.com/150/771796",
                }
            ),
        ]

        sut = TransformData(clock=fixed_clock)
        result = sut.execute(photo_dtos)

        assert len(result) == 2
        assert result[0].photo_id == 1
        assert result[1].photo_id == 2
        assert result[0].album_id == 1
        assert result[1].album_id == 2

    def test_returns_empty_list_when_input_is_empty(self) -> None:
        sut = TransformData(clock=fixed_clock)
        result = sut.execute([])

        assert result == []

    def test_applies_same_processed_at_to_all_records_in_same_execution(self) -> None:
        photo_dtos = [
            PhotoDTO.model_validate(
                {
                    "albumId": 1,
                    "id": 1,
                    "title": "primeira foto",
                    "url": "https://via.placeholder.com/600/92c952",
                    "thumbnailUrl": "https://via.placeholder.com/150/92c952",
                }
            ),
            PhotoDTO.model_validate(
                {
                    "albumId": 1,
                    "id": 2,
                    "title": "segunda foto",
                    "url": "https://via.placeholder.com/600/771796",
                    "thumbnailUrl": "https://via.placeholder.com/150/771796",
                }
            ),
        ]

        sut = TransformData(clock=fixed_clock)
        result = sut.execute(photo_dtos)

        assert result[0].processed_at == result[1].processed_at == FIXED_NOW

    def test_uses_default_clock_when_not_injected(self) -> None:
        photo_dto = PhotoDTO.model_validate(
            {
                "albumId": 1,
                "id": 1,
                "title": "titulo qualquer",
                "url": "https://via.placeholder.com/600/92c952",
                "thumbnailUrl": "https://via.placeholder.com/150/92c952",
            }
        )

        before = datetime.now()
        sut = TransformData()
        result = sut.execute([photo_dto])
        after = datetime.now()

        assert before <= result[0].processed_at <= after
