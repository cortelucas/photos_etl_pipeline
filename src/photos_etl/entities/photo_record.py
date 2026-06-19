"""Entidade de saída representando um registro pronto para persistência em CSV."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PhotoRecord(BaseModel):
    """Representa a estrutura final de negócio que será escrita no CSV.

    Desacoplada do contrato da API: usa apenas os tipos e nomes de campo
    que fazem sentido para o domínio deste pipeline.
    """

    model_config = ConfigDict(frozen=True)

    album_id: int
    photo_id: int
    title: str
    image_url: str
    thumbnail_url: str
    processed_at: datetime
