# AVGJØRELSER

## Språk og rammeverk
Python 3.13 med **FastAPI** og **Pydantic**. Oppgaven ser ut til å være I/O-tung, ikke CPU-bundet. Derfor gir asynckron tilnærming mening.
FastAPI gir gratis utfylte forespørsels/responskontrakter og OpenAPI-dokumentasjon. Pydantic håndteres forespørsels/respons validering.

## Arkitektur
En heksagonal arkitektur (ports-and-adapters) ble vurdert, men ikke fullt
implementert gitt tidsrammen. Det finnes derfor verken tjenestelag, Unit of Work eller eget
ports-modul. Abstrakte repositorier er likevel beholdt for å vise litt fleksibilitet — samme
grensesnitt har både en in-memory- og en Postgres-implementasjon.

Domenemodellene er utledet med inspirasjon fra domenedrevet design (DDD) og holdt adskilt fra API-kontrakter.
Domenemodeller og Pydantic-klasser holdes adskilt slik at domenelogikken ikke bindes til HTTP-/serialiseringslaget,
og API-kontrakten kan endres uavhengig av domenet.

Konfigurasjonshåndtering er ikke implementert. Ingen ORM er brukt; PostgreSQL aksesseres med rå SQL.

## Feilhåndtering mot eksterne API-er
Henting i `POST /fetch` skjer samtidig for alle lokasjoner, og feil isoleres per lokasjon: en
feil for én lokasjon stopper ikke de andre. Responsen returnerer antall oppdaterte,
antall feilede og en `failures`-liste med detaljer per lokasjon.

## PostgreSQL
`ON DELETE CASCADE` på fremmednøkkelen ville gitt mening for å fjerne varsler sammen med
lokasjonen, men er ikke lagt til. Sletting skjer derfor i to separate kall uten felles
transaksjon — det kunne vært løst med en Unit of Work, men det er ikke implementert.

## Oppdaterte lokasjoner
Det er uklart hva «oppdatert» betyr — antall lokasjoner som ble hentet på nytt, eller antall av
verdier som endret seg (f.eks. temperaturen). Implementasjonen teller lokasjoner som ble
hentet på nytt.

## Utdaterte varsler
Utdatert-status (eldre enn 60 minutter) beregnes i applikasjonen ved lesing, ikke i databasen —
også `?fresh=true` filtreres i appen. I stor skala kan det løses med filtrering på databasenivå
(f.eks. en `WHERE` på `fetched_at`).

## Kjente problemer og begrensninger
- Duplikate lokasjoner tillates.
- Ingen rate-limiting.
- Ingen skjemamigrasjoner (f.eks. Alembic eller Liquibase).
