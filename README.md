# navy_database

Active combatant warships of CN, RU, US, JP, GB, FR, KR, IN, TR, scraped from English Wikipedia (MediaWiki API).

Pipeline (run from repo root, `pip install -r requirements.txt`):

1. `navydb/classes.py` – curated list of classes (page titles). 
2. `python -c "from navydb.fetch import main; main()"` -> `data/classes_raw.json` (merged infobox fields)
3. `python -c "from navydb.fetch_ships import main; main()"` -> `data/ships_raw.json` (per-ship wikitable rows)
4. `python -c "from navydb.build_db import main; main()"` -> `data/navy.db` (SQLite)

Tables: `ship_class`, `ship` (per hull: name, pennant, commissioned, status), `radar`, `vls`, `weapon`.
Every parsed value keeps its raw text (`*_raw`) and the source page + revision id.

## Known limitations
- Specs are heuristically parsed from free text; sub-batch/flight variants are mixed (use `*_raw` to audit).
- `ship.status` is `unknown` where the source table has no status column.
- Some classes have no per-ship table on their page (see `ship_class` rows with no `ship`).
- Pages shared by several countries (e.g. Kilo, Sovremenny) describe the main variant only.
