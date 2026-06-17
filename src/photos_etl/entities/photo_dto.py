"""DTO representando o payload bruto retornado pela API de fotos."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PhotoDTO(BaseModel):
    """Espelha exatamente o contrato JSON da API jsonplaceholder

    Qualquer mudança no formato retornado pela origem deve ser refletida
    apenas aqui, sem impactar a entidade de saída (PhotoRecord).
    """

    model_config = ConfigDict(frozen=True)

    album_id: int = Field(alias="albumId")
    id: int = Field(alias="id")
    title: str = Field(alias="title")
    url: HttpUrl = Field(alias="url")
    thumbnail_url: HttpUrl = Field(alias="thumbnailUrl")
