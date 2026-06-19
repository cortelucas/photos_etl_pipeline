# photos_etl_pipeline

Pipeline de ETL (Extract, Transform, Load) em Python, construído de forma orientada a objetos e seguindo os princípios SOLID. Consome dados de fotos da API pública [JSONPlaceholder](https://jsonplaceholder.typicode.com/photos), valida e transforma os registros, e persiste o resultado em arquivos `.csv` organizados por `albumId`.

## Arquitetura

O pipeline segue o padrão **Command/Service Object**: cada etapa é uma classe isolada, com um único método público `execute()`. A composição entre as etapas é feita via **injeção de dependência** (Dependency Inversion Principle), o que torna cada peça testável de forma independente.

```
ExtractDataFromOrigem.execute()  →  TransformData.execute()  →  SendToDestiny.execute()
        (busca da API)                 (regras de negócio)         (persistência em CSV)
                            ↑
                    EtlPipeline.execute()
                  (orquestrador / esteira final)
```

### Camadas

| Camada | Classe | Responsabilidade |
|---|---|---|
| `entities/` | `PhotoDTO` | Espelha o contrato bruto da API (Pydantic, com aliases `camelCase`) |
| `entities/` | `PhotoRecord` | Entidade de domínio/saída, pronta para persistência (inclui `processed_at`) |
| `extract/` | `ExtractDataFromOrigem` | Busca os dados na API e retorna `list[PhotoDTO]` validados |
| `transform/` | `TransformData` | Mapeia `PhotoDTO` → `PhotoRecord`, adicionando o timestamp de processamento |
| `load/` | `SendToDestiny` | Persiste os `PhotoRecord` em CSV, agrupados por `album_id`, evitando duplicatas |
| `pipeline/` | `EtlPipeline` | Orquestra as três etapas na ordem correta |
| `main.py` | `run_pipeline`, `main` | Ponto de entrada: monta as dependências reais e executa o pipeline |

Todas as dependências externas (cliente HTTP, relógio, diretório de destino) são injetadas via construtor, nunca instanciadas internamente nas classes de serviço — isso é o que permite testar cada camada isoladamente, sem rede ou disco reais.

## Requisitos

- Python `>=3.13`
- [Poetry](https://python-poetry.org/) para gerenciamento de dependências

## Instalação

```bash
git clone https://github.com/cortelucas/photos_etl_pipeline.git
cd photos_etl_pipeline
poetry install
```

## Uso

Executar o pipeline completo (extrai da API real, transforma e grava os CSVs):

```bash
poetry run run-pipeline
```

Os arquivos serão gerados em `data/output/`, no formato `photos_album_{albumId}.csv`, um por álbum. Execuções repetidas não duplicam registros: o `SendToDestiny` verifica o `photo_id` já presente no arquivo antes de anexar novas linhas.

### Formato do CSV gerado

| Coluna | Descrição |
|---|---|
| `album_id` | ID do álbum (inteiro) |
| `photo_id` | ID da foto (inteiro) |
| `title` | Título da foto |
| `image_url` | URL da imagem em tamanho completo |
| `thumbnail_url` | URL da miniatura |
| `processed_at` | Timestamp (ISO 8601) de quando o lote foi processado |

## Testes

O projeto segue uma estratégia de testes em três camadas, usando [Pytest](https://docs.pytest.org/):

```bash
# Todos os testes, com relatório de cobertura
poetry run pytest --cov=photos_etl --cov-report=term-missing

# Apenas testes unitários (entities, transform, load — sem infraestrutura real)
poetry run pytest tests/unit -v

# Apenas testes de integração (extract, com mocks de rede/timeout/payload corrompido)
poetry run pytest tests/integration -v

# Apenas teste end-to-end (esteira completa, mockando só a API externa)
poetry run pytest tests/e2e -v
```

A cobertura mínima exigida é de **90%** (`--cov-fail-under=90`, configurado em `pyproject.toml`); a suíte atual mantém a cobertura acima de 99%.

## Qualidade de código

```bash
# Lint e formatação (Ruff)
poetry run ruff check .
poetry run ruff format .

# Checagem de tipos estáticos (mypy --strict)
poetry run mypy src tests
```

Os hooks de [pre-commit](https://pre-commit.com/) (Ruff + mypy) rodam automaticamente a cada commit:

```bash
poetry run pre-commit install
```

## Padrão de commits

O histórico do projeto segue estritamente a especificação [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (`feat`, `fix`, `test`, `refactor`, `chore`, entre outros).

## Stack

- [httpx](https://www.python-httpx.org/) — cliente HTTP
- [Pydantic](https://docs.pydantic.dev/) — validação de schemas e DTOs
- [Pytest](https://docs.pytest.org/) + [pytest-mock](https://pytest-mock.readthedocs.io/) + [pytest-cov](https://pytest-cov.readthedocs.io/) — testes e cobertura
- [Ruff](https://docs.astral.sh/ruff/) — lint e formatação
- [mypy](https://mypy-lang.org/) — checagem estática de tipos (modo `strict`)
- [Poetry](https://python-poetry.org/) — gerenciamento de dependências e empacotamento
