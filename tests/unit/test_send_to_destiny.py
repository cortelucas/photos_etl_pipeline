"""Testes unitários de SendToDestiny."""

import csv
from datetime import datetime
from pathlib import Path

from photos_etl.entities.photo_record import PhotoRecord
from photos_etl.load.send_to_destiny import SendToDestiny

FIXED_NOW = datetime(2026, 6, 19, 12, 0, 0)


def build_record(album_id: int, photo_id: int, title: str = "titulo qualquer") -> PhotoRecord:
    return PhotoRecord(
        album_id=album_id,
        photo_id=photo_id,
        title=title,
        image_url="https://via.placeholder.com/600/92c952",
        thumbnail_url="https://via.placeholder.com/150/92c952",
        processed_at=FIXED_NOW,
    )


class TestSendToDestiny:
    def test_creates_one_csv_file_per_album_id(self, tmp_path: Path) -> None:
        records = [
            build_record(album_id=1, photo_id=1),
            build_record(album_id=2, photo_id=2),
        ]

        sut = SendToDestiny(output_dir=tmp_path)
        written_files = sut.execute(records)

        assert (tmp_path / "photos_album_1.csv").exists()
        assert (tmp_path / "photos_album_2.csv").exists()
        assert len(written_files) == 2

    def test_writes_correct_header_and_rows(self, tmp_path: Path) -> None:
        records = [build_record(album_id=1, photo_id=1, title="primeira foto")]

        sut = SendToDestiny(output_dir=tmp_path)
        sut.execute(records)

        csv_path = tmp_path / "photos_album_1.csv"
        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)

        assert reader.fieldnames == [
            "album_id",
            "photo_id",
            "title",
            "image_url",
            "thumbnail_url",
            "processed_at",
        ]
        assert len(rows) == 1
        assert rows[0]["title"] == "primeira foto"
        assert rows[0]["photo_id"] == "1"

    def test_groups_multiple_photos_of_same_album_into_single_file(self, tmp_path: Path) -> None:
        records = [
            build_record(album_id=1, photo_id=1),
            build_record(album_id=1, photo_id=2),
            build_record(album_id=1, photo_id=3),
        ]

        sut = SendToDestiny(output_dir=tmp_path)
        sut.execute(records)

        csv_path = tmp_path / "photos_album_1.csv"
        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))

        assert len(rows) == 3

    def test_appends_new_records_without_duplicating_existing_photo_ids(
        self, tmp_path: Path
    ) -> None:
        sut = SendToDestiny(output_dir=tmp_path)

        first_batch = [build_record(album_id=1, photo_id=1)]
        sut.execute(first_batch)

        second_batch = [
            build_record(album_id=1, photo_id=1),  # já existe, não deve duplicar
            build_record(album_id=1, photo_id=2),  # novo, deve ser adicionado
        ]
        sut.execute(second_batch)

        csv_path = tmp_path / "photos_album_1.csv"
        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))

        photo_ids = sorted(int(row["photo_id"]) for row in rows)
        assert photo_ids == [1, 2]

    def test_writes_header_only_once_across_multiple_executions(self, tmp_path: Path) -> None:
        sut = SendToDestiny(output_dir=tmp_path)
        sut.execute([build_record(album_id=1, photo_id=1)])
        sut.execute([build_record(album_id=1, photo_id=2)])

        csv_path = tmp_path / "photos_album_1.csv"
        content = csv_path.read_text(encoding="utf-8")

        assert content.count("album_id,photo_id,title,image_url,thumbnail_url,processed_at") == 1

    def test_returns_empty_list_when_no_records_are_new(self, tmp_path: Path) -> None:
        sut = SendToDestiny(output_dir=tmp_path)
        record = build_record(album_id=1, photo_id=1)

        sut.execute([record])
        written_files = sut.execute([record])

        assert written_files == []

    def test_returns_empty_list_when_input_is_empty(self, tmp_path: Path) -> None:
        sut = SendToDestiny(output_dir=tmp_path)
        result = sut.execute([])

        assert result == []

    def test_creates_output_directory_if_it_does_not_exist(self, tmp_path: Path) -> None:
        nested_dir = tmp_path / "nested" / "output"
        sut = SendToDestiny(output_dir=nested_dir)

        sut.execute([build_record(album_id=1, photo_id=1)])

        assert nested_dir.exists()
        assert (nested_dir / "photos_album_1.csv").exists()
