"""Classe responsável por persistir PhotoRecord em arquivos CSV, agrupados por álbum."""

import csv
from collections import defaultdict
from pathlib import Path

from photos_etl.entities.photo_record import PhotoRecord

CSV_FIELDNAMES = [
    "album_id",
    "photo_id",
    "title",
    "image_url",
    "thumbnail_url",
    "processed_at",
]


class SendToDestiny:
    """Persiste PhotoRecord em arquivos CSV, um por albumId.

    Segue o padrão Command/Service Object: expõe um único método público
    `execute()`. O diretório de destino é injetado via construtor (DIP),
    permitindo testes apontarem para um diretório temporário.

    Registros com photo_id já presente no arquivo de destino não são
    duplicados em execuções repetidas.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def execute(self, records: list[PhotoRecord]) -> list[Path]:
        """Agrupa os registros por album_id e persiste cada grupo em seu CSV.

        Returns:
            Lista de caminhos dos arquivos CSV que tiveram registros novos
            de fato escritos. Álbuns sem nenhum registro novo não aparecem
            na lista, mesmo que o arquivo já exista.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        records_by_album = self._group_by_album_id(records)
        written_files: list[Path] = []

        for album_id, album_records in records_by_album.items():
            file_path = self._output_dir / f"photos_album_{album_id}.csv"
            was_written = self._write_album_csv(file_path, album_records)
            if was_written:
                written_files.append(file_path)

        return written_files

    @staticmethod
    def _group_by_album_id(
        records: list[PhotoRecord],
    ) -> dict[int, list[PhotoRecord]]:
        grouped: dict[int, list[PhotoRecord]] = defaultdict(list)
        for record in records:
            grouped[record.album_id].append(record)
        return dict(grouped)

    def _write_album_csv(self, file_path: Path, records: list[PhotoRecord]) -> bool:
        existing_photo_ids = self._read_existing_photo_ids(file_path)
        new_records = [r for r in records if r.photo_id not in existing_photo_ids]

        if not new_records:
            return False

        file_already_exists = file_path.exists()
        with file_path.open(mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)

            if not file_already_exists:
                writer.writeheader()

            for record in new_records:
                writer.writerow(
                    {
                        "album_id": record.album_id,
                        "photo_id": record.photo_id,
                        "title": record.title,
                        "image_url": record.image_url,
                        "thumbnail_url": record.thumbnail_url,
                        "processed_at": record.processed_at.isoformat(),
                    }
                )

        return True

    @staticmethod
    def _read_existing_photo_ids(file_path: Path) -> set[int]:
        if not file_path.exists():
            return set()

        with file_path.open(mode="r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            return {int(row["photo_id"]) for row in reader}
