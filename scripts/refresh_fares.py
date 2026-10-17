#!/usr/bin/env python3
"""Fetch cached round-trip fares US -> SAL from the Travelpayouts / Aviasales Data API and
write public/data/fares.json. If TRAVELPAYOUTS_TOKEN is not set it does nothing, so the
'coming soon' state stays. Standard library only. Never prints or stores the token.

Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
Affiliate link: Aviasales page URL + marker=<partner ID>
  (https://support.travelpayouts.com/hc/ru/articles/5711895629714 , manual link templates)
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ORIGINS = ["LAX", "ONT", "IAD", "JFK", "EWR", "IAH", "HOU", "DFW", "SFO", "OAK", "BOS", "MIA", "ATL"]
DEST = "SAL"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "data", "fares.json")
API = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
DEFAULT_MARKER = "791370"  # public affiliate ID

def found_on(link):
    """Aviasales links carry search_date=DDMMYYYY: the day the price was found."""
    m = re.search(r"[?&]search_date=(\d{2})(\d{2})(\d{4})", link or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None

def affiliate_link(link, marker):
    if not link:
        return None
    url = "https://www.aviasales.com" + link
    return url + ("&" if "?" in url else "?") + "marker=" + urllib.parse.quote(marker)

def fetch(origin, token):
    q = urllib.parse.urlencode({"origin": origin, "destination": DEST, "currency": "usd", "market": "us",
                                "one_way": "false", "sorting": "price", "limit": 30, "page": 1})
    req = urllib.request.Request(f"{API}?{q}", headers={"X-Access-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

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
            d = fetch(o, token)
        except Exception as e:
            print(f"{o}: request failed ({type(e).__name__})", file=sys.stderr); empty.append(o); continue
        rows = (d.get("data") or []) if d.get("success") else []
        good = []
        for t in rows:
            try:
                dep = datetime.fromisoformat(t["departure_at"])
            except Exception:
                continue
            # sanity: exact airports, future departure, real positive price, has link
            if (t.get("origin_airport") == o and t.get("destination_airport") == DEST and dep > now
                    and isinstance(t.get("price"), (int, float)) and t["price"] > 0 and t.get("link")):
                good.append(t)
        if not good:
            print(f"{o}: no recent fares"); empty.append(o); continue
        t = min(good, key=lambda x: x["price"])
        fares.append({
            "origin": o, "destination": DEST, "price": t["price"], "currency": "usd",
            "round_trip": bool(t.get("return_at")), "airline": t.get("airline"),
            "transfers": t.get("transfers"), "return_transfers": t.get("return_transfers"),
            "departure_at": t["departure_at"], "return_at": t.get("return_at"),
            "departure_month": t["departure_at"][:7], "found_on": found_on(t["link"]),
            "link": affiliate_link(t["link"], marker),
        })
        print(f"{o}: ${t['price']} depart {t['departure_at'][:10]} found {found_on(t['link'])}")
        time.sleep(0.5)
    data = {"status": "live" if fares else "pending", "source": "Aviasales (Travelpayouts Data API)",
            "updated_at": now.isoformat(timespec="seconds"), "currency": "usd", "market": "us",
            "no_data": empty, "fares": fares}
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"wrote {len(fares)} fares; no data: {empty}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
