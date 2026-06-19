"""Classe responsável por extrair dados brutos da API de fotos."""

import httpx

from photos_etl.entities.photo_dto import PhotoDTO


class ExtractDataFromOrigem:
    """Busca os dados de fotos na API de origem e os encapsula em PhotoDTO.

    Segue o padrão Command/Service Object: expõe um único método público
    `execute()`. O cliente HTTP é injetado via construtor (DIP), permitindo
    substituí-lo por um mock em testes, sem depender de rede real.
    """

    def __init__(self, http_client: httpx.Client, source_url: str) -> None:
        self._http_client = http_client
        self._source_url = source_url

    def execute(self) -> list[PhotoDTO]:
        """Busca o payload da API e retorna a lista de PhotoDTO validados.

        Raises:
            httpx.HTTPStatusError: se a API responder com status de erro (4xx/5xx).
            httpx.TimeoutException: se a requisição exceder o timeout configurado.
            pydantic.ValidationError: se o payload retornado não corresponder
                ao schema esperado de PhotoDTO.
        """
        response = self._http_client.get(self._source_url)
        response.raise_for_status()

        raw_payload = response.json()

        return [PhotoDTO.model_validate(item) for item in raw_payload]
