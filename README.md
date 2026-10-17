# Volver a Casa: bilingual travel guide + fare tracker (US → San Salvador, SAL)

Plain static site, no framework, no dependencies.

- `build.py` generates `public/` (EN at `/`, ES at `/es/`). Run `python3 build.py`.
- `public/data/fares.json` holds fares, written only by `scripts/refresh_fares.py` from the Travelpayouts Data API (cheapest cached round trip per airport, market us, USD). Affiliate links are `https://www.aviasales.com{link}&marker=791370`. **Never hand-edit numbers into it.**
- `scripts/refresh_fares.py` pulls cached fares from the Travelpayouts/Aviasales Data API when `TRAVELPAYOUTS_TOKEN` is set.
- `ci/refresh-fares.yml` (move to `.github/workflows/` to enable; pushing workflow files needs a token with `workflow` scope) runs it every 6 hours on GitHub Actions and commits the JSON, which triggers a Render redeploy.
- Email signup and paid alerts are disabled placeholders (see ../launch_plan.md).

Preview locally: `cd public && python3 -m http.server 8000`
Deploy: Render static site, build `python3 build.py`, publish dir `public` (see `render.yaml`).
