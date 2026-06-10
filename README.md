# ssb-yr — Værdata-innhenter

HTTP-tjeneste som registrerer geografiske steder, hentes værvarsler fra YT ved åpne API, lagrer dem og eksponener dem via sitt eget REST-API.
Se DECISIONS.md for nøkkelavgjørelser og valg.

## Kjøre

Krever Docker. Starter applikasjonen + PostgreSQL med persistent volum

```bash
docker compose up --build
```

APIet er tilgjengelig på http://localhost:8000 (interktiv dokumentasjon finnes på `/docs`)

### Miljøvariabler

| Variabel          | Standardverdi                                        |
|------------------|-------------------------------------------------------|
| `DATABASE_URL`   | Ikke satt → in-memory; docker compose setter Postgres |
| `YR_USER_AGENT`  | `ssb-yr/1.0 nikita.s.fomin@gmail.com`                 |


## Utvikling

Kreves Python 3.13 og [uv](https://docs.astral.sh/uv/)

```bash
uv sync --extra dev                               # Opprett virtuelt miljø og instalere avhengigheter
source .venv/bin/activate                         # Aktiver virtuelt miljø
uv run pytest                                     # kjøre enhetstester
uv run ruff check .                               # kjøre linter
uv run mypy src                                   # kjøre typesjekker
uv run uvicorn main:app --reload --app-dir src    # Kjøre applikasjonen lokalt
```
