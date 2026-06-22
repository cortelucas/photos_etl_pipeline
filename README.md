# photos_etl_pipeline

Pipeline de ETL (Extract, Transform, Load) em Python, construído de forma orientada a objetos e seguindo os princípios SOLID. Consome dados de fotos da API pública [JSONPlaceholder](https://jsonplaceholder.typicode.com/photos), valida e transforma os registros em lotes, e persiste o resultado em arquivos `.csv` organizados por `albumId`.

O pipeline pode ser disparado de três formas: via linha de comando, via endpoint HTTP (`GET /start`), ou automaticamente em intervalos definidos por uma expressão cron.

## Arquitetura

O pipeline segue o padrão **Command/Service Object**: cada etapa é uma classe isolada, com um único método público `execute()`. A composição entre as etapas é feita via **injeção de dependência** (Dependency Inversion Principle), o que torna cada peça testável de forma independente.

```
ExtractDataFromOrigem.execute()  →  TransformData.execute()  →  SendToDestiny.execute()
        (busca da API)              (regras de negócio, por lote)   (persistência em CSV)
                            ↑
                    EtlPipeline.execute()
            (orquestrador / esteira final, processa em lotes de batch_size)
                            ↑
        ┌───────────────────┴───────────────────┐
   GET /start (FastAPI)              Scheduler (APScheduler + CronTrigger)
   disparo manual, em background      disparo automático, via CRON_EXPRESSION
```

### Camadas

| Camada | Classe | Responsabilidade |
|---|---|---|
| `config/` | `Settings` | Configuração centralizada via variáveis de ambiente (pydantic-settings) |
| `entities/` | `PhotoDTO` | Espelha o contrato bruto da API (Pydantic, com aliases `camelCase`) |
| `entities/` | `PhotoRecord` | Entidade de domínio/saída, pronta para persistência (inclui `processed_at`) |
| `extract/` | `ExtractDataFromOrigem` | Busca os dados na API e retorna `list[PhotoDTO]` validados |
| `transform/` | `TransformData` | Mapeia `PhotoDTO` → `PhotoRecord`, adicionando o timestamp de processamento |
| `load/` | `SendToDestiny` | Persiste os `PhotoRecord` em CSV, agrupados por `album_id`, evitando duplicatas |
| `pipeline/` | `chunk_list` | Utilitário de fatiamento de listas em lotes |
| `pipeline/` | `EtlPipeline` | Orquestra as três etapas, processando em lotes de `batch_size` |
| `api/` | `app` (FastAPI) | Expõe `GET /start` e `GET /health`; inicia o scheduler no lifespan |
| `scheduler/` | `build_scheduler` | Monta um `BackgroundScheduler` com `CronTrigger` a partir de `CRON_EXPRESSION` |
| `main.py` | `run_pipeline`, `main` | Ponto de entrada de linha de comando |

Todas as dependências externas (cliente HTTP, relógio, diretório de destino, configuração) são injetadas via construtor, nunca instanciadas internamente nas classes de serviço — isso é o que permite testar cada camada isoladamente, sem rede, disco ou agendador reais.

### Paginação em lotes

A API de origem (JSONPlaceholder) não suporta paginação real via query params — sempre retorna o dataset completo em uma única resposta. Por isso, a extração (`ExtractDataFromOrigem`) sempre busca tudo de uma vez, mas o **processamento** (transform + load) é feito em lotes de `BATCH_SIZE` registros, controlados pelo `EtlPipeline`. Isso protege o uso de memória caso a fonte de dados cresça significativamente no futuro, sem exigir paginação real da API.

## Requisitos

- Python `>=3.13`
- [Poetry](https://python-poetry.org/) para gerenciamento de dependências

## Instalação

```bash
git clone https://github.com/cortelucas/photos_etl_pipeline.git
cd photos_etl_pipeline
poetry install
cp .env.example .env
```

## Configuração

Todas as configurações são feitas via variáveis de ambiente (arquivo `.env`, ver `.env.example`):

| Variável | Default | Descrição |
|---|---|---|
| `SOURCE_URL` | `https://jsonplaceholder.typicode.com/photos` | URL da API de origem |
| `OUTPUT_DIR` | `data/output` | Diretório de destino dos arquivos CSV |
| `BATCH_SIZE` | `500` | Tamanho do lote para processamento de transform/load |
| `CRON_EXPRESSION` | `0 * * * *` | Expressão cron (5 campos) para disparo automático |

## Uso

### Linha de comando (execução única)

```bash
poetry run run-pipeline
```

### Servidor HTTP (FastAPI)

```bash
poetry run run-api
```

Sobe um servidor em `http://localhost:8000` com:

- `GET /health` — health check simples
- `GET /start` — dispara o pipeline em background e responde imediatamente, sem esperar a execução terminar
- Scheduler automático rodando em paralelo, disparando o pipeline conforme `CRON_EXPRESSION` (timezone UTC)

```bash
curl http://localhost:8000/health
curl http://localhost:8000/start
```

Os arquivos serão gerados em `OUTPUT_DIR`, no formato `photos_album_{albumId}.csv`, um por álbum. Execuções repetidas (manuais ou agendadas) não duplicam registros: o `SendToDestiny` verifica o `photo_id` já presente no arquivo antes de anexar novas linhas.

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

# Apenas testes unitários (entities, transform, load, pipeline, scheduler — sem infraestrutura real)
poetry run pytest tests/unit -v

# Apenas testes de integração (extract com mocks de rede; API FastAPI com TestClient)
poetry run pytest tests/integration -v

# Apenas teste end-to-end (esteira completa, mockando só a API externa)
poetry run pytest tests/e2e -v
```

A cobertura mínima exigida é de **90%** (`--cov-fail-under=90`, configurado em `pyproject.toml`); a suíte atual mantém a cobertura acima de 97%.

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
- [Pydantic](https://docs.pydantic.dev/) / [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — validação de schemas, DTOs e configuração via env vars
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — servidor HTTP e endpoint `/start`
- [APScheduler](https://apscheduler.readthedocs.io/) — agendamento periódico via expressão cron
- [Pytest](https://docs.pytest.org/) + [pytest-mock](https://pytest-mock.readthedocs.io/) + [pytest-cov](https://pytest-cov.readthedocs.io/) — testes e cobertura
- [Ruff](https://docs.astral.sh/ruff/) — lint e formatação
- [mypy](https://mypy-lang.org/) — checagem estática de tipos (modo `strict`)
- [Poetry](https://python-poetry.org/) — gerenciamento de dependências e empacotamento