#!/usr/bin/env python3
"""Fetch cached fares US -> SAL from the Travelpayouts / Aviasales Data API and
write public/data/fares.json. Does nothing (and leaves the 'coming soon' state)
if TRAVELPAYOUTS_TOKEN is not set. Uses only the standard library.

Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
Endpoint: /aviasales/v3/prices_for_dates (cheapest tickets found by Aviasales users, last 48h)
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ORIGINS = ["LAX", "ONT", "IAD", "JFK", "EWR", "IAH", "HOU", "DFW", "SFO", "OAK", "BOS", "MIA", "ATL"]
DEST = "SAL"
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "data", "fares.json")
API = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

def main():
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
    marker = os.environ.get("TRAVELPAYOUTS_MARKER", "").strip()
    if not token:
        print("TRAVELPAYOUTS_TOKEN not set; leaving fares.json unchanged (coming-soon state).")
        return 0
    fares = []
    for o in ORIGINS:
        q = urllib.parse.urlencode({"origin": o, "destination": DEST, "currency": "usd", "market": "us",
                                    "one_way": "false", "sorting": "price", "limit": 1, "page": 1})
        req = urllib.request.Request(f"{API}?{q}", headers={"X-Access-Token": token, "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
        except Exception as e:  # keep going; a missing route just shows "no recent data"
            print(f"{o}: error {e}", file=sys.stderr); continue
        rows = (d.get("data") or []) if d.get("success") else []
        if not rows:
            print(f"{o}: no cached data"); continue
        t = rows[0]
        link = None
        # Affiliate deep link: only when a marker is configured. VERIFY the exact deep-link
        # format in the Travelpayouts dashboard ("deep link creation form") before enabling.
        if marker and t.get("link"):
            link = "https://www.aviasales.com" + t["link"] + "&marker=" + urllib.parse.quote(marker)
        fares.append({"origin": o, "destination": DEST, "price": t.get("price"), "currency": "usd",
                      "airline": t.get("airline"), "transfers": t.get("transfers"),
                      "departure_month": (t.get("departure_at") or "")[:7], "round_trip": bool(t.get("return_at")),
                      "found_at": datetime.now(timezone.utc).isoformat(), "link": link})
        time.sleep(1)  # be gentle; documented rate limits not verified (see launch_plan.md)
    data = {"status": "live" if fares else "pending", "source": "Aviasales via Travelpayouts",
            "updated_at": datetime.now(timezone.utc).isoformat(), "fares": fares}
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {len(fares)} fares")
    return 0

if __name__ == "__main__":
    sys.exit(main())
