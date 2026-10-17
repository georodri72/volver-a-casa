#!/usr/bin/env python3
"""Fetch recently seen round-trip fares US airport -> SAL from the Travelpayouts / Aviasales
Data API and write public/data/fares.json. If TRAVELPAYOUTS_TOKEN is not set it does nothing.
Standard library only. Never prints or stores the token.

Freshness rule (see launch_plan.md section 11):
  * Candidates come from v3 prices_for_dates (airport-level, includes a booking link).
  * Each candidate must match an entry in v3 get_latest_prices with the SAME departure
    datetime, return datetime and price, which gives a precise found_at timestamp.
  * Keep it only if found_at is within MAX_AGE_HOURS (48 h; the docs describe
    prices_for_dates as "found by Aviasales users in the last 48 hours", but the cache
    actually returned entries up to ~7 days old, so we enforce it ourselves).
  * Departure must be at least MIN_LEAD_HOURS in the future.
  * Fares without a verifiable timestamp are dropped. Routes with nothing left show
    "no recent fares". The browser also hides fares older than 48 h at view time.
Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
Affiliate link: Aviasales page URL + marker=<partner ID> (Travelpayouts manual link template)
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

ORIGINS = ["LAX", "ONT", "IAD", "JFK", "EWR", "IAH", "HOU", "DFW", "SFO", "OAK", "BOS", "MIA", "ATL"]
DEST = "SAL"
MAX_AGE_HOURS = 48
MIN_LEAD_HOURS = 48
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "data", "fares.json")
BASE = "https://api.travelpayouts.com"
DEFAULT_MARKER = "791370"  # public affiliate ID

def get(token, path, **params):
    req = urllib.request.Request(f"{BASE}{path}?{urllib.parse.urlencode(params)}", headers={"X-Access-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc) if s else None

def affiliate_link(link, marker):
    url = "https://www.aviasales.com" + link
    return url + ("&" if "?" in url else "?") + "marker=" + urllib.parse.quote(marker)

def candidates(token, o):
    d = get(token, "/aviasales/v3/prices_for_dates", origin=o, destination=DEST, currency="usd", market="us",
            one_way="false", sorting="price", limit=100, page=1)
    rows = (d.get("data") or []) if d.get("success") else []
    return [t for t in rows if t.get("origin_airport") == o and t.get("destination_airport") == DEST
            and isinstance(t.get("price"), (int, float)) and t["price"] > 0 and t.get("link") and t.get("return_at")]

def found_index(token, o, now):
    idx = {}
    for year in sorted({now.year, now.year + 1}):
        for page in (1, 2):
            d = get(token, "/aviasales/v3/get_latest_prices", origin=o, destination=DEST, currency="usd", market="us",
                    period_type="year", beginning_of_period=str(year), one_way="false", trip_class=0,
                    sorting="price", limit=1000, page=page)
            rows = (d.get("data") or []) if d.get("success") else []
            for x in rows:
                k = (x.get("depart_date"), x.get("return_date"), x.get("value"))
                fa = parse_ts(x.get("found_at"))
                if fa and (k not in idx or fa > idx[k]):
                    idx[k] = fa
            if len(rows) < 1000:
                break
            time.sleep(0.3)
    return idx

def main():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    marker = os.environ.get("TRAVELPAYOUTS_MARKER", "").strip() or DEFAULT_MARKER
    if not token:
        print("TRAVELPAYOUTS_TOKEN not set; leaving fares.json unchanged.")
        return 0
    now = datetime.now(timezone.utc)
    fares, empty = [], []
    for o in ORIGINS:
        try:
            cands = candidates(token, o)
            idx = found_index(token, o, now) if cands else {}
        except Exception as e:
            print(f"{o}: request failed ({type(e).__name__})", file=sys.stderr); empty.append(o); continue
        fresh = []
        for t in cands:
            dep = parse_ts(t["departure_at"])
            fa = idx.get((t["departure_at"], t["return_at"], t["price"]))
            if not dep or dep < now + timedelta(hours=MIN_LEAD_HOURS) or not fa:
                continue
            if timedelta(0) <= now - fa <= timedelta(hours=MAX_AGE_HOURS):
                fresh.append((t, fa))
        if not fresh:
            print(f"{o}: no recent fares ({len(cands)} cached candidates, none verifiably <{MAX_AGE_HOURS}h old)")
            empty.append(o); continue
        t, fa = min(fresh, key=lambda x: x[0]["price"])
        fares.append({
            "origin": o, "destination": DEST, "price": t["price"], "currency": "usd",
            "round_trip": True, "passengers": 1, "trip_class": "economy",
            "airline": t.get("airline"), "transfers": t.get("transfers"), "return_transfers": t.get("return_transfers"),
            "departure_at": t["departure_at"], "return_at": t["return_at"],
            "found_at": fa.isoformat(timespec="seconds"), "link": affiliate_link(t["link"], marker),
        })
        print(f"{o}: ${t['price']} depart {t['departure_at'][:10]} found {round((now-fa).total_seconds()/3600,1)}h ago")
        time.sleep(0.3)
    data = {"status": "live" if fares else "pending", "source": "Aviasales (Travelpayouts Data API)",
            "updated_at": now.isoformat(timespec="seconds"), "max_age_hours": MAX_AGE_HOURS,
            "currency": "usd", "market": "us", "no_data": empty, "fares": fares}
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"wrote {len(fares)} fares; no recent data: {empty}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
