#!/usr/bin/env python3
"""Month view data: cheapest round-trip fares to SAL seen in recent Aviasales searches, by departure
date, for the active airports (config/airports.json), next 12 months. Writes public/data/calendar.json
and appends one daily snapshot line to data/history.jsonl (append-only, used for "when is it cheapest").
Standard library only. Never prints or stores the token. Does nothing without TRAVELPAYOUTS_TOKEN.

Source: Travelpayouts Data API v3 grouped_prices (group_by=departure_at, one_way=false), per airport.
  * "seen" date = the search_date in the fare's own Aviasales link (date of the search that found it).
  * The API keeps cached data for 7 days (Travelpayouts docs), so anything seen >7 days ago is dropped.
  * Departure must be >= 48 h away; return must be on a later calendar day than departure.
  * Refreshed at most every REFRESH_HOURS so the hourly workflow does not rebuild the site every hour.
Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from refresh_fares import ORIGINS, DEST, DEFAULT_MARKER, get, affiliate_link  # same config + link format

OUT = os.path.join(ROOT, "public", "data", "calendar.json")
HIST = os.path.join(ROOT, "data", "history.jsonl")
MONTHS = 12
MAX_SEEN_DAYS = 7
MIN_LEAD_HOURS = 48
REFRESH_HOURS = 6

def seen_date(link):
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(link).query)
    s = (q.get("search_date") or [""])[0]
    try:
        return datetime.strptime(s, "%d%m%Y").date()
    except ValueError:
        return None

def month_list(today):
    y, m = today.year, today.month
    for _ in range(MONTHS):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13: y, m = y + 1, 1

def append_history(data, now):
    today = now.date().isoformat()
    last = None
    if os.path.exists(HIST):
        with open(HIST) as f:
            for line in f:
                if line.strip(): last = json.loads(line)
    if last and last.get("date") == today:
        return False
    days = {}
    for d in data["days"]:
        days.setdefault(d["depart_date"], {})[d["origin"]] = d["price"]
    snap = {"date": today, "captured_at": now.isoformat(timespec="seconds"), "source": data["source"],
            "currency": "usd", "basis": "1 adult, round trip, economy; cheapest seen per departure date",
            "by_month": {m["month"]: {"min": m["min"], "days_with_data": m["days_with_data"]} for m in data["months"] if m["min"] is not None},
            "days": days}
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "a") as f:
        f.write(json.dumps(snap, separators=(",", ":")) + "\n")
    return True

def main():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    marker = os.environ.get("TRAVELPAYOUTS_MARKER", "").strip() or DEFAULT_MARKER
    if not token:
        print("TRAVELPAYOUTS_TOKEN not set; leaving calendar.json unchanged."); return 0
    now = datetime.now(timezone.utc)
    force = "--force" in sys.argv
    try:
        with open(OUT) as f: prev = json.load(f)
    except (OSError, ValueError):
        prev = None
    if prev and not force and prev.get("generated_at"):
        age = now - datetime.fromisoformat(prev["generated_at"])
        if age < timedelta(hours=REFRESH_HOURS):
            print(f"calendar.json is {age.total_seconds()/3600:.1f} h old (< {REFRESH_HOURS} h); skipping")
            return 0
    today = now.date()
    days, failed = [], []
    for o in ORIGINS:
        for m in month_list(today):
            try:
                d = get(token, "/aviasales/v3/grouped_prices", origin=o, destination=DEST, currency="usd", market="us",
                        group_by="departure_at", departure_at=m, one_way="false")
            except Exception as e:
                print(f"{o} {m}: request failed ({type(e).__name__})", file=sys.stderr); failed.append(f"{o} {m}"); continue
            for key, t in ((d.get("data") or {}) if d.get("success") else {}).items():
                if t.get("origin_airport") != o or not t.get("return_at") or not t.get("link"):
                    continue
                dep = datetime.fromisoformat(t["departure_at"])
                if dep < now + timedelta(hours=MIN_LEAD_HOURS) or t["return_at"][:10] <= t["departure_at"][:10]:
                    continue
                sd = seen_date(t["link"])
                if not sd or not (0 <= (today - sd).days <= MAX_SEEN_DAYS):
                    continue
                days.append({"origin": o, "depart_date": t["departure_at"][:10], "return_date": t["return_at"][:10],
                             "price": t["price"], "airline": t.get("airline"), "transfers": t.get("transfers"),
                             "return_transfers": t.get("return_transfers"), "seen_date": sd.isoformat(),
                             "link": affiliate_link(t["link"], marker)})
            time.sleep(0.25)
    days.sort(key=lambda x: (x["depart_date"], x["price"]))
    months = []
    for m in month_list(today):
        md = [d for d in days if d["depart_date"].startswith(m)]
        best = min(md, key=lambda x: x["price"]) if md else None
        months.append({"month": m, "min": best["price"] if best else None, "min_origin": best["origin"] if best else None,
                       "min_depart_date": best["depart_date"] if best else None, "min_seen_date": best["seen_date"] if best else None,
                       "days_with_data": len({d["depart_date"] for d in md})})
    data = {"source": "Aviasales (Travelpayouts Data API, v3 grouped_prices)", "generated_at": now.isoformat(timespec="seconds"),
            "currency": "usd", "market": "us", "origins": ORIGINS, "destination": DEST, "max_seen_days": MAX_SEEN_DAYS,
            "basis": {"passengers": 1, "round_trip": True, "trip_class": "economy"}, "failed": failed,
            "months": months, "days": days}
    if failed and not days and prev:
        print("all requests failed; keeping previous calendar.json"); return 0
    hist = append_history(data, now)
    same = prev and {k: v for k, v in prev.items() if k != "generated_at"} == {k: v for k, v in data.items() if k != "generated_at"}
    if same:
        # keep the file byte-identical (no commit, no rebuild); the 6 h throttle then re-checks next hour
        print(f"calendar unchanged ({len(days)} day-fares); history appended: {hist}"); return 0
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1); f.write("\n")
    print(f"wrote calendar.json: {len(days)} day-fares across {sum(1 for m in months if m['min'])} months; history appended: {hist}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
