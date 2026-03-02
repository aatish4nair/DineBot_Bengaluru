#!/usr/bin/env python3
"""
Seed the restaurant cache from ManikaSaini/zomato-restaurant-recommendation.
Run once to populate App/backend/data/restaurants.json so the backend can load
from cache (RESTAURANT_LOAD_FROM_CACHE=1) without loading HF at startup.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datasets import load_dataset


def main() -> None:
    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    records = []
    for i in range(len(ds)):
        row = ds[i]
        # Map to backend format
        place = str(row.get("listed_in(city)", "") or "").strip() or "—"
        name = str(row.get("name", "") or "—").strip()
        cuisines_raw = row.get("cuisines", "") or ""
        cuisines = [s.strip() for s in str(cuisines_raw).split(",") if s.strip()] or ["—"]
        # Price range from approx_cost
        try:
            cost = int(str(row.get("approx_cost(for two people)", "300") or "300").replace(",", "").strip() or 300)
            if cost <= 300:
                price_range = 1
            elif cost <= 600:
                price_range = 2
            elif cost <= 1000:
                price_range = 3
            else:
                price_range = 4
        except (ValueError, TypeError):
            price_range = 1
        # Rating from rate "4.1/5"
        try:
            rate = str(row.get("rate", "0") or "0").strip()
            rating = float(rate.split("/")[0].strip()) if "/" in rate else float(rate or 0)
        except (ValueError, TypeError):
            rating = 0.0
        rec = {
            "Restaurant Name": name,
            "City": place,
            "Price range": price_range,
            "Aggregate rating": rating,
            "Cuisines": ", ".join(cuisines) if cuisines else "—",
        }
        records.append(rec)
    out_path = ROOT / "App" / "data" / "restaurants.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    places = sorted({r["City"] for r in records if r["City"] and r["City"] != "—"})
    print(f"Saved {len(records)} restaurants to {out_path}")
    print(f"Distinct places: {len(places)}")
    print("Places:", places)


if __name__ == "__main__":
    main()
