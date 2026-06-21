"""Testes unitários de EtlPipeline, focando no processamento em lotes."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from photos_etl.entities.photo_dto import PhotoDTO
from photos_etl.pipeline.etl_pipeline import EtlPipeline


def build_photo_dto(album_id: int, photo_id: int) -> PhotoDTO:
    return PhotoDTO.model_validate(
        {
            "albumId": album_id,
            "id": photo_id,
            "title": f"foto {photo_id}",
            "url": "https://via.placeholder.com/600/92c952",
            "thumbnailUrl": "https://via.placeholder.com/150/92c952",
        }
    )


class TestEtlPipelineBatching:
    def test_raises_value_error_when_batch_size_is_zero(self, mocker: MockerFixture) -> None:
        with pytest.raises(ValueError, match="batch_size deve ser maior que zero"):
            EtlPipeline(
                extract_step=mocker.Mock(),
                transform_step=mocker.Mock(),
                load_step=mocker.Mock(),
                batch_size=0,
            )

    def test_calls_transform_and_load_once_per_batch(self, mocker: MockerFixture) -> None:
        photos = [build_photo_dto(album_id=1, photo_id=i) for i in range(1, 6)]  # 5 fotos

        extract_step = mocker.Mock()
        extract_step.execute.return_value = photos

        transform_step = mocker.Mock()
        transform_step.execute.side_effect = lambda batch: [
            mocker.Mock(album_id=p.album_id, photo_id=p.id) for p in batch
        ]

        load_step = mocker.Mock()
        load_step.execute.return_value = [Path("data/output/photos_album_1.csv")]

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
            batch_size=2,
        )

        pipeline.execute()

        # 5 fotos, batch_size=2 -> lotes de [2, 2, 1] -> 3 chamadas
        assert transform_step.execute.call_count == 3
        assert load_step.execute.call_count == 3

    def test_first_batch_has_exactly_batch_size_items(self, mocker: MockerFixture) -> None:
        photos = [build_photo_dto(album_id=1, photo_id=i) for i in range(1, 6)]  # 5 fotos

        extract_step = mocker.Mock()
        extract_step.execute.return_value = photos

        transform_step = mocker.Mock()
        transform_step.execute.return_value = []

        load_step = mocker.Mock()
        load_step.execute.return_value = []

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
            batch_size=2,
        )

        pipeline.execute()

        first_batch_passed_to_transform = transform_step.execute.call_args_list[0].args[0]
        assert len(first_batch_passed_to_transform) == 2

    def test_deduplicates_written_files_across_multiple_batches(
        self, mocker: MockerFixture
    ) -> None:
        photos = [build_photo_dto(album_id=1, photo_id=i) for i in range(1, 6)]
        album_1_csv = Path("data/output/photos_album_1.csv")

        extract_step = mocker.Mock()
        extract_step.execute.return_value = photos

        transform_step = mocker.Mock()
        transform_step.execute.return_value = []

        load_step = mocker.Mock()
        # mesmo arquivo retornado em todos os lotes (álbum 1 espalhado por 3 lotes)
        load_step.execute.return_value = [album_1_csv]

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
            batch_size=2,
        )

        written_files = pipeline.execute()

        assert written_files == [album_1_csv]

    def test_returns_sorted_written_files(self, mocker: MockerFixture) -> None:
        photos = [build_photo_dto(album_id=1, photo_id=1)]

        extract_step = mocker.Mock()
        extract_step.execute.return_value = photos

        transform_step = mocker.Mock()
        transform_step.execute.return_value = []

        load_step = mocker.Mock()
        load_step.execute.return_value = [
            Path("data/output/photos_album_9.csv"),
            Path("data/output/photos_album_1.csv"),
        ]

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
            batch_size=1,
        )

        written_files = pipeline.execute()

        assert written_files == sorted(written_files)

    def test_returns_empty_list_when_no_photos_are_extracted(self, mocker: MockerFixture) -> None:
        extract_step = mocker.Mock()
        extract_step.execute.return_value = []

        transform_step = mocker.Mock()
        load_step = mocker.Mock()

        pipeline = EtlPipeline(
            extract_step=extract_step,
            transform_step=transform_step,
            load_step=load_step,
            batch_size=500,
        )

        written_files = pipeline.execute()

        assert written_files == []
        transform_step.execute.assert_not_called()
        load_step.execute.assert_not_called()
