"""Classe responsável por transformar PhotoDTO em PhotoRecord."""

from collections.abc import Callable
from datetime import datetime

from photos_etl.entities.photo_dto import PhotoDTO
from photos_etl.entities.photo_record import PhotoRecord


class TransformData:
    """Converte uma lista de PhotoDTO (origem) em PhotoRecord (domínio).

    Segue o padrão Command/Service Object: expõe um único método público
    `execute()`. A função de relógio (`clock`) é injetada via construtor (DIP),
    permitindo testes determinísticos sem depender do horário real do sistema.
    """

    def __init__(self, clock: Callable[[], datetime] = datetime.now) -> None:
        self._clock = clock

    def execute(self, photos: list[PhotoDTO]) -> list[PhotoRecord]:
        """Mapeia cada PhotoDTO para um PhotoRecord, adicionando processed_at."""
        processed_at = self._clock()

        return [
            PhotoRecord(
                album_id=photo.album_id,
                photo_id=photo.id,
                title=photo.title,
                image_url=str(photo.url),
                thumbnail_url=str(photo.thumbnail_url),
                processed_at=processed_at,
            )
            for photo in photos
        ]
