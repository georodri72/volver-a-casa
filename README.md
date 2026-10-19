# Volver a Casa: bilingual travel guide + fare tracker (US → San Salvador, SAL)

Plain static site, no framework, no dependencies.

- `build.py` generates `public/` (EN at `/`, ES at `/es/`). Run `python3 build.py`.
- `public/data/fares.json` holds fares, written only by `scripts/refresh_fares.py` from the Travelpayouts Data API (cheapest cached round trip per airport, market us, USD). Affiliate links are `https://www.aviasales.com{link}&marker=791370`. **Never hand-edit numbers into it.**
- `scripts/refresh_fares.py` pulls cached fares from the Travelpayouts/Aviasales Data API when `TRAVELPAYOUTS_TOKEN` is set.
- `.github/workflows/refresh-fares.yml` runs it every hour on GitHub Actions and commits the JSON only when fares change, which triggers a Render redeploy.
- Email signup and paid alerts are disabled placeholders (see ../launch_plan.md).

Preview locally: `cd public && python3 -m http.server 8000`
Deploy: Render static site, build `python3 build.py`, publish dir `public` (see `render.yaml`).

## Month view and price history
- `scripts/refresh_calendar.py` writes `public/data/calendar.json`: cheapest round-trip fare seen per departure date
  (next 12 months, active airports only) from Travelpayouts v3 `grouped_prices`. Each entry carries the date it was seen
  (from the fare link's `search_date`); entries seen more than 7 days ago are dropped. Runs from the hourly workflow but
  only refreshes every 6 h, and only rewrites the file when the data changed.
- It also appends one line per UTC day to `data/history.jsonl` (append-only). The "When is it cheapest to fly" section on
  `calendar.html` stays a placeholder until there are 28 daily snapshots, then shows medians of the daily cheapest by month.
- `build.py` renders `calendar.html` statically from these files at build time (Render rebuilds on each data commit).
