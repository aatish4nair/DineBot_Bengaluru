from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import re
import threading
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


def _add_phase_src_to_syspath() -> None:
    # Project root: .../Project1-1
    root = Path(__file__).resolve().parents[2]
    for phase in ["Phase1", "Phase2", "Phase3", "Phase4", "Phase5", "Phase6"]:
        src = root / phase / "src"
        if src.exists():
            sys.path.insert(0, str(src))


def _load_env() -> None:
    root = Path(__file__).resolve().parents[2]
    # Load Phase4/.env first (has GROQ_API_KEY); override=True so file values take precedence
    phase4_env = root / "Phase4" / ".env"
    if phase4_env.exists():
        load_dotenv(dotenv_path=phase4_env, override=True)
    root_env = root / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env, override=False)


_add_phase_src_to_syspath()
_load_env()

from ai_restaurant_phase2.data_loader import DatasetLoader, validate_dataset  # noqa: E402
from ai_restaurant_phase3.filtering import filter_restaurants, rank_restaurants  # noqa: E402
from ai_restaurant_phase3.models import Restaurant, UserPreferences  # noqa: E402
from ai_restaurant_phase4.prompting import CandidateContext, build_prompt  # noqa: E402
from ai_restaurant_phase5.formatter import format_recommendation  # noqa: E402
from ai_restaurant_phase6.logging_config import get_logger  # noqa: E402
from ai_restaurant_phase6.metrics import get_metrics  # noqa: E402
from ai_restaurant_phase6.tracing import with_request_id  # noqa: E402

LOG = get_logger("app.backend")


class RecommendRequest(BaseModel):
    place: str = Field(min_length=1)
    price_range: int = Field(ge=1, le=4)
    rating_min: float = Field(ge=0, le=5)
    rating_max: float = Field(ge=0, le=6)
    cuisines: list[str] = Field(default_factory=list)

    @field_validator("place")
    @classmethod
    def strip_place(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("place cannot be empty")
        return s

    @field_validator("cuisines")
    @classmethod
    def normalize_cuisines(cls, v: list) -> list:
        return [str(x).strip() for x in (v or []) if str(x).strip()]


def _clean_text(value: Any) -> str:
    """
    Normalize text from the dataset and fix common mojibake (e.g. CafÃ© -> Café).
    This helps remove extra characters in names like the cafe examples.
    """
    s = str(value or "").strip()
    if not s:
        return s
    # Try to repair typical UTF-8/latin1 mojibake only when suspicious characters appear
    if any(ch in s for ch in ("Ã", "Â")):
        try:
            repaired = s.encode("latin1", "ignore").decode("utf-8", "ignore").strip()
            if repaired:
                s = repaired
        except Exception:
            # If anything goes wrong, keep original string
            pass
    # Remove leftover mojibake control characters if any remain
    if any(ch in s for ch in ("Ã", "Â")):
        s = re.sub(r"[ÃÂ]+", "", s)
    # Specific tidy-up for common patterns in cafe names
    # e.g. "Caf Secret Alley" -> "Cafe Secret Alley"
    s = re.sub(r"\bCaf\b", "Cafe", s)
    # Collapse repeated whitespace
    s = " ".join(s.split())
    # Canonicalize known problematic names with extra junk/spacing
    low = s.lower()
    if "urban solace" in low and "soul" in low:
        # Normalize to a single clean display name
        return "Urban Solace - Cafe for the Soul"
    if "secret" in low and "alley" in low:
        return "Cafe Secret Alley"
    return s


def _normalize_dataset_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize HF dataset columns to expected format (City, Price range, etc).
    Handles ManikaSaini/zomato-restaurant-recommendation: listed_in(city), name,
    approx_cost(for two people), rate (e.g. "4.1/5").
    """
    column_aliases = {
        "city": "City",
        "listed_in(city)": "City",
        "restaurant name": "Restaurant Name",
        "restaurant_name": "Restaurant Name",
        "name": "Restaurant Name",
        "price range": "Price range",
        "price_range": "Price range",
        "approx_cost(for two people)": "Price range",
        "aggregate rating": "Aggregate rating",
        "aggregate_rating": "Aggregate rating",
        "rate": "Aggregate rating",
        "cuisines": "Cuisines",
        "address": "Address",
        "rating": "Aggregate rating",
    }
    out = dict(record)
    for k, v in record.items():
        k_lower = k.lower().strip()
        for variant, canonical in column_aliases.items():
            if k_lower == variant and canonical not in out:
                out[canonical] = v
                break
    # ManikaSaini dataset: convert approx cost string (e.g. "800") to Price range 1-4
    if "Price range" not in out or not isinstance(out.get("Price range"), int):
        cost_raw = out.get("Price range") or record.get("approx_cost(for two people)", "300")
        try:
            cost_val = int(str(cost_raw).replace(",", "").strip() or 300)
            if cost_val <= 300:
                out["Price range"] = 1
            elif cost_val <= 600:
                out["Price range"] = 2
            elif cost_val <= 1000:
                out["Price range"] = 3
            else:
                out["Price range"] = 4
        except (ValueError, TypeError):
            out["Price range"] = 1
    # ManikaSaini dataset: parse rate "4.1/5" to float
    if "Aggregate rating" not in out or not isinstance(out.get("Aggregate rating"), (int, float)):
        rate_raw = out.get("Aggregate rating") or record.get("rate", "0")
        try:
            s = str(rate_raw).strip()
            if "/" in s:
                out["Aggregate rating"] = float(s.split("/")[0].strip())
            else:
                out["Aggregate rating"] = float(s or 0)
        except (ValueError, TypeError):
            out["Aggregate rating"] = 0.0
    # Ensure Address exists for Phase2 validation
    if not out.get("Address") and not out.get("address"):
        out["Address"] = out.get("City", out.get("place", record.get("location", "—")))
    return out


def _dataset_provider_from_hf() -> list[dict[str, Any]]:
    """
    Fetch Zomato dataset from Hugging Face via `datasets`.
    MAX_DATASET_RECORDS=0 or unset loads full dataset; set to a positive number to limit.
    """
    from datasets import load_dataset  # local import: only used at runtime

    ds = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    size = len(ds)
    max_records = int(os.getenv("MAX_DATASET_RECORDS", "0"))
    if max_records <= 0:
        max_records = size
    n = min(size, max_records)
    raw = [ds[i] for i in range(n)]
    LOG.info("Loading %d records from ManikaSaini/zomato-restaurant-recommendation (dataset size=%d)", n, size)
    # Normalize column names for compatibility
    return [_normalize_dataset_record(r) for r in raw]


def _record_to_restaurant(record: dict[str, Any]) -> Restaurant:
    cuisines_raw = record.get("Cuisines") or record.get("cuisines") or ""
    cuisines = [s.strip() for s in str(cuisines_raw).split(",") if s.strip()]
    if not cuisines:
        cuisines = ["—"]

    return Restaurant(
        restaurant_name=_clean_text(record.get("Restaurant Name", record.get("restaurant_name", "—"))),
        place=_clean_text(record.get("City", record.get("place", record.get("location", "—")))),
        price_range=int(record.get("Price range", record.get("price_range", 1))),
        rating=float(record.get("Aggregate rating", record.get("rating", 0.0))),
        cuisines=[_clean_text(c) for c in cuisines],
    )


def _restaurant_to_record(r: Restaurant) -> dict[str, Any]:
    """Serialize Restaurant for JSON cache."""
    return {
        "Restaurant Name": r.restaurant_name,
        "City": r.place,
        "Price range": r.price_range,
        "Aggregate rating": r.rating,
        "Cuisines": ", ".join(r.cuisines) if r.cuisines else "—",
    }


def _cache_file_path() -> Path:
    """Path to persistent restaurant cache (JSON)."""
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "restaurants.json"


def _load_restaurants_from_cache_file() -> list[Restaurant] | None:
    """Load restaurant list from JSON cache if present and valid."""
    path = _cache_file_path()
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
        if not isinstance(records, list) or not records:
            return None
        return [_record_to_restaurant(r) for r in records]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        LOG.warning("Cache file invalid, ignoring: %s", e)
        return None


def _save_restaurants_to_cache_file(restaurants: list[Restaurant]) -> None:
    """Persist restaurant list to JSON cache."""
    path = _cache_file_path()
    records = [_restaurant_to_record(r) for r in restaurants]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        LOG.info("Saved %d restaurants to cache file: %s", len(records), path)
    except OSError as e:
        LOG.warning("Could not write cache file: %s", e)


def _restaurant_to_candidate(r: Restaurant) -> CandidateContext:
    return CandidateContext(
        restaurant_name=r.restaurant_name,
        location=r.place,
        price_range=r.price_range,
        rating=r.rating,
        cuisines=r.cuisines,
    )


def _rest_attr(rest, attr: str, default: Any = "—"):
    """Safely get attribute from Restaurant or dict."""
    if hasattr(rest, attr):
        return getattr(rest, attr, default)
    if isinstance(rest, dict):
        return rest.get(attr, default)
    return default


def _fallback_rationale(prefs: RecommendRequest, rest, index: int) -> str:
    """Generate a unique, creative fallback rationale per restaurant (used when LLM unavailable)."""
    name = _rest_attr(rest, "restaurant_name", "—")
    rating = _rest_attr(rest, "rating", 0)
    cuisines = _rest_attr(rest, "cuisines", [])
    if isinstance(cuisines, str):
        cuisines = [c.strip() for c in cuisines.split(",") if c.strip()]
    rest_cuisine = cuisines[0] if cuisines else "diverse"
    user_cuisine = ", ".join(prefs.cuisines) or "your choice"
    templates = [
        f"{name} brings authentic {rest_cuisine} to {prefs.place}—rated {rating}!",
        f"Craving {user_cuisine}? {name} delivers with a {rating} rating in your budget.",
        f"Discover {name}: top-rated {rest_cuisine} in {prefs.place} at great value.",
        f"{name}—where {rest_cuisine} meets quality and your price range.",
        f"Love {user_cuisine}? {name} in {prefs.place} won't disappoint (rated {rating}).",
        f"{name} stands out for {rest_cuisine} in {prefs.place}—try it today!",
        f"Your next favourite spot: {name} for {rest_cuisine} in {prefs.place}.",
        f"{name} offers standout {rest_cuisine} in your area—rated {rating}.",
    ]
    return templates[index % len(templates)]


def _generate_one_line_rationales(
    prefs: RecommendRequest, restaurants: list
) -> list[str]:
    """
    Generate a unique one-line recommendation message for each restaurant using LLM (Groq).
    One LLM call per restaurant. Guarantees different messages via deduplication.
    """
    price_labels = {1: "₹0-300", 2: "₹300-600", 3: "₹600-1000", 4: "₹1000+"}
    price_str = price_labels.get(prefs.price_range, str(prefs.price_range))
    cuisine_str = ", ".join(prefs.cuisines) or "any"
    results: list[str] = []
    fallbacks: list[str] = []

    for i, r in enumerate(restaurants):
        rest = r.restaurant if hasattr(r, "restaurant") else r
        fb = _fallback_rationale(prefs, rest, i)
        fallbacks.append(fb)
        name = _rest_attr(rest, "restaurant_name", "—")
        loc = _rest_attr(rest, "place", "—")
        rating = _rest_attr(rest, "rating", 0)
        cuisines = _rest_attr(rest, "cuisines", [])
        if isinstance(cuisines, str):
            cuisines = [c.strip() for c in cuisines.split(",") if c.strip()]
        cuis_str = ", ".join(cuisines[:3]) if cuisines else "—"

        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if not groq_key:
            results.append(fb)
            continue

        try:
            from groq import Groq

            prompt = (
                f"User wants: Place {prefs.place}, Price {price_str}, Rating {prefs.rating_min}-{prefs.rating_max}, Cuisine: {cuisine_str}.\n\n"
                f"Restaurant: {name} | {loc} | rating {rating} | cuisines: {cuis_str}\n\n"
                "Write ONE creative, catchy line (max 15 words) to attract customers. "
                "Be specific to THIS restaurant. No generic phrases like 'matches your preference' or 'within budget'. "
                "Reply with ONLY the one line, nothing else."
            )
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                messages=[
                    {"role": "system", "content": "You write catchy one-liners for restaurants. Each must be unique. Output only the line."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.95,
                max_tokens=60,
            )
            text = (resp.choices[0].message.content or "").strip()
            results.append(text if text else fb)
        except Exception as e:
            LOG.warning("Groq rationale for %s failed: %s", name, e)
            results.append(fb)

    # Deduplicate: if any rationale repeats, replace with fallback to guarantee uniqueness
    seen: set[str] = set()
    for i in range(len(results)):
        r = results[i]
        r_normalized = r.strip().lower()[:80]
        if r_normalized in seen or not r.strip():
            results[i] = fallbacks[i]
        else:
            seen.add(r_normalized)

    return results


def _choose_and_rationale(prefs: RecommendRequest, ranked: list) -> tuple[Restaurant, str]:
    """
    Deterministic choice (top-ranked) + short rationale.
    Optionally enhances rationale via Groq if available and reachable.
    """
    chosen: Restaurant = ranked[0].restaurant
    base_rationale = (
        f"Top match in {prefs.place} for cuisines {', '.join(prefs.cuisines) or 'any'} "
        f"within price range {prefs.price_range}, rated {chosen.rating}."
    )

    if not os.getenv("GROQ_API_KEY"):
        return chosen, base_rationale

    try:
        from groq import Groq

        prompt = build_prompt(
            {
                "place": prefs.place,
                "price_range": prefs.price_range,
                "rating_min": prefs.rating_min,
                "rating_max": prefs.rating_max,
                "cuisines": prefs.cuisines,
            },
            [_restaurant_to_candidate(chosen)],
        )
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            messages=[
                {
                    "role": "system",
                    "content": "Return a short, user-friendly rationale only (1-2 sentences).",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        text = (resp.choices[0].message.content or "").strip()
        return chosen, (text or base_rationale)
    except Exception as e:
        LOG.warning("Groq rationale unavailable, using fallback: %s", type(e).__name__)
        return chosen, base_rationale


app = FastAPI(title="AI Restaurant Recommender", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_loader = DatasetLoader(provider=_dataset_provider_from_hf, cache_enabled=True)
_restaurants_cache: list[Restaurant] | None = None


@app.on_event("startup")
def _startup() -> None:
    global _restaurants_cache
    groq_ok = bool(os.getenv("GROQ_API_KEY", "").strip())
    LOG.info("GROQ_API_KEY loaded: %s (AI rationales %s)", groq_ok, "enabled" if groq_ok else "using fallbacks")
    app.state.dataset_status = "initializing"
    app.state.dataset_error = None
    use_sample_only = os.getenv("USE_SAMPLE_DATASET_ONLY", "").lower() in ("1", "true", "yes")

    if not use_sample_only:
        # Load from Hugging Face (ManikaSaini/zomato-restaurant-recommendation)
        if os.getenv("RESTAURANT_LOAD_FROM_CACHE", "").lower() in ("1", "true", "yes"):
            cached = _load_restaurants_from_cache_file()
            if cached:
                _restaurants_cache = cached
                app.state.dataset_status = "cache"
                LOG.info("Loaded %d restaurants from cache file", len(_restaurants_cache))
                return
        try:
            LOG.info("Loading ManikaSaini/zomato-restaurant-recommendation dataset...")
            records = _loader.load()
            validate_dataset(records)
            _restaurants_cache = [_record_to_restaurant(r) for r in records]
            _save_restaurants_to_cache_file(_restaurants_cache)
            app.state.dataset_status = "ready"
            LOG.info("Hugging Face dataset ready: %d restaurants loaded (saved to cache)", len(_restaurants_cache))
            return
        except Exception as e:
            app.state.dataset_status = "degraded"
            app.state.dataset_error = f"{type(e).__name__}: {e}"
            LOG.warning("Hugging Face dataset load failed, falling back to sample dataset: %s", app.state.dataset_error)

    # Optionally load from persistent cache (JSON file) when using sample mode
    if os.getenv("RESTAURANT_LOAD_FROM_CACHE", "").lower() in ("1", "true", "yes"):
        cached = _load_restaurants_from_cache_file()
        if cached:
            _restaurants_cache = cached
            app.state.dataset_status = "cache"
            LOG.info("Loaded %d restaurants from cache file", len(_restaurants_cache))
            return

    # Built-in sample dataset (when USE_SAMPLE_DATASET_ONLY=1 or HF load failed)
    sample_records = [
        {
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.4,
            "Cuisines": "Italian, Cafe",
            "Restaurant Name": "Cafe Roma",
            "Address": "Pune",
        },
        {
            "City": "Pune",
            "Price range": 2,
            "Aggregate rating": 4.2,
            "Cuisines": "Italian",
            "Restaurant Name": "Bistro One",
            "Address": "Pune",
        },
        {
            "City": "Mumbai",
            "Price range": 3,
            "Aggregate rating": 4.1,
            "Cuisines": "Indian",
            "Restaurant Name": "Spice Hub",
            "Address": "Mumbai",
        },
        {
            "City": "Bangalore",
            "Price range": 2,
            "Aggregate rating": 4.3,
            "Cuisines": "South Indian, Indian",
            "Restaurant Name": "MTR",
            "Address": "Bangalore",
        },
        {
            "City": "Delhi",
            "Price range": 2,
            "Aggregate rating": 4.0,
            "Cuisines": "North Indian, Indian",
            "Restaurant Name": "Saravana Bhavan",
            "Address": "Delhi",
        },
        {
            "City": "Chennai",
            "Price range": 1,
            "Aggregate rating": 4.2,
            "Cuisines": "South Indian, Cafe",
            "Restaurant Name": "Murugan Idli",
            "Address": "Chennai",
        },
        {
            "City": "Hyderabad",
            "Price range": 2,
            "Aggregate rating": 4.5,
            "Cuisines": "Indian, Biryani",
            "Restaurant Name": "Paradise",
            "Address": "Hyderabad",
        },
        {
            "City": "Kolkata",
            "Price range": 2,
            "Aggregate rating": 4.1,
            "Cuisines": "Indian, Bengali",
            "Restaurant Name": "Oh! Calcutta",
            "Address": "Kolkata",
        },
        # Extra restaurants so each place has multiple options and variety in cuisine/price/rating
        {"City": "Pune", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Indian", "Restaurant Name": "Pune Spice", "Address": "Pune"},
        {"City": "Pune", "Price range": 3, "Aggregate rating": 4.5, "Cuisines": "Italian, Continental", "Restaurant Name": "La Vista", "Address": "Pune"},
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Indian, North Indian", "Restaurant Name": "Taj Chaat", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 4, "Aggregate rating": 4.6, "Cuisines": "Indian, Fine Dining", "Restaurant Name": "Trishna", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "South Indian", "Restaurant Name": "Vidyarthi Bhavan", "Address": "Bangalore"},
        {"City": "Bangalore", "Price range": 3, "Aggregate rating": 4.4, "Cuisines": "North Indian, Indian", "Restaurant Name": "Toit", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 1, "Aggregate rating": 3.7, "Cuisines": "North Indian, Indian", "Restaurant Name": "Chandni Chowk", "Address": "Delhi"},
        {"City": "Delhi", "Price range": 3, "Aggregate rating": 4.3, "Cuisines": "Indian, Mughlai", "Restaurant Name": "Karim's", "Address": "Delhi"},
        {"City": "Chennai", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "South Indian, Indian", "Restaurant Name": "Sangeetha", "Address": "Chennai"},
        {"City": "Hyderabad", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Indian, Biryani", "Restaurant Name": "Bawarchi", "Address": "Hyderabad"},
        {"City": "Kolkata", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Indian, Bengali", "Restaurant Name": "Kewpie's", "Address": "Kolkata"},
        # Japanese restaurants for cuisine filter testing (Mumbai, Bangalore, etc.)
        {"City": "Mumbai", "Price range": 1, "Aggregate rating": 4.0, "Cuisines": "Japanese", "Restaurant Name": "Sakura Sushi", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Japanese, Sushi", "Restaurant Name": "Tokyo Express", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.2, "Cuisines": "Japanese", "Restaurant Name": "Wasabi", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Japanese", "Restaurant Name": "Sushi House", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 1, "Aggregate rating": 4.1, "Cuisines": "Japanese, Ramen", "Restaurant Name": "Ramen Bar", "Address": "Delhi"},
        {"City": "Pune", "Price range": 1, "Aggregate rating": 3.7, "Cuisines": "Japanese", "Restaurant Name": "Sakura Pune", "Address": "Pune"},
        # Chinese - all places, varied price/rating
        {"City": "Mumbai", "Price range": 1, "Aggregate rating": 4.0, "Cuisines": "Chinese", "Restaurant Name": "China Town", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.2, "Cuisines": "Chinese", "Restaurant Name": "Mainland China", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Chinese", "Restaurant Name": "Beijing Bites", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 2, "Aggregate rating": 4.1, "Cuisines": "Chinese", "Restaurant Name": "Dragon Palace", "Address": "Delhi"},
        {"City": "Pune", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Chinese", "Restaurant Name": "Wok Express", "Address": "Pune"},
        {"City": "Chennai", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Chinese", "Restaurant Name": "Golden Dragon", "Address": "Chennai"},
        {"City": "Hyderabad", "Price range": 1, "Aggregate rating": 3.7, "Cuisines": "Chinese", "Restaurant Name": "Chopsticks", "Address": "Hyderabad"},
        {"City": "Kolkata", "Price range": 2, "Aggregate rating": 4.3, "Cuisines": "Chinese", "Restaurant Name": "Beijing", "Address": "Kolkata"},
        # Mexican - all places
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.1, "Cuisines": "Mexican", "Restaurant Name": "Sabor", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Mexican", "Restaurant Name": "Taco Bell", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 3, "Aggregate rating": 4.4, "Cuisines": "Mexican", "Restaurant Name": "El Mexicano", "Address": "Delhi"},
        {"City": "Pune", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Mexican", "Restaurant Name": "Chimichanga", "Address": "Pune"},
        # Thai - all places
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.2, "Cuisines": "Thai", "Restaurant Name": "Lemongrass", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Thai", "Restaurant Name": "Bangkok Express", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Thai", "Restaurant Name": "Thai High", "Address": "Delhi"},
        {"City": "Pune", "Price range": 1, "Aggregate rating": 3.7, "Cuisines": "Thai", "Restaurant Name": "Pad Thai", "Address": "Pune"},
        # Fast Food - all places
        {"City": "Mumbai", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Fast Food", "Restaurant Name": "McDonald's", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 1, "Aggregate rating": 4.0, "Cuisines": "Fast Food", "Restaurant Name": "KFC", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 1, "Aggregate rating": 3.8, "Cuisines": "Fast Food", "Restaurant Name": "Burger King", "Address": "Delhi"},
        {"City": "Pune", "Price range": 1, "Aggregate rating": 3.6, "Cuisines": "Fast Food", "Restaurant Name": "Domino's", "Address": "Pune"},
        {"City": "Chennai", "Price range": 1, "Aggregate rating": 4.1, "Cuisines": "Fast Food", "Restaurant Name": "Subway", "Address": "Chennai"},
        {"City": "Hyderabad", "Price range": 1, "Aggregate rating": 3.7, "Cuisines": "Fast Food", "Restaurant Name": "Pizza Hut", "Address": "Hyderabad"},
        {"City": "Kolkata", "Price range": 1, "Aggregate rating": 3.9, "Cuisines": "Fast Food", "Restaurant Name": "Wendy's", "Address": "Kolkata"},
        # Fast Food - price 2 and 3 for coverage (Delhi Upscale, etc.)
        {"City": "Delhi", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Fast Food", "Restaurant Name": "Jumbo King", "Address": "Delhi"},
        {"City": "Delhi", "Price range": 3, "Aggregate rating": 4.2, "Cuisines": "Fast Food", "Restaurant Name": "Social", "Address": "Delhi"},
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.1, "Cuisines": "Fast Food", "Restaurant Name": "Smoke House Deli", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 3, "Aggregate rating": 4.0, "Cuisines": "Fast Food", "Restaurant Name": "The Beer Cafe", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 2, "Aggregate rating": 4.0, "Cuisines": "Fast Food", "Restaurant Name": "Truffles", "Address": "Bangalore"},
        {"City": "Pune", "Price range": 2, "Aggregate rating": 3.9, "Cuisines": "Fast Food", "Restaurant Name": "German Bakery", "Address": "Pune"},
        # Seafood - all places
        {"City": "Mumbai", "Price range": 2, "Aggregate rating": 4.3, "Cuisines": "Seafood", "Restaurant Name": "Trishna Seafood", "Address": "Mumbai"},
        {"City": "Mumbai", "Price range": 4, "Aggregate rating": 4.6, "Cuisines": "Seafood", "Restaurant Name": "Sea Lounge", "Address": "Mumbai"},
        {"City": "Bangalore", "Price range": 2, "Aggregate rating": 4.1, "Cuisines": "Seafood", "Restaurant Name": "Coastal Kitchen", "Address": "Bangalore"},
        {"City": "Delhi", "Price range": 3, "Aggregate rating": 4.2, "Cuisines": "Seafood", "Restaurant Name": "Ocean's Catch", "Address": "Delhi"},
        {"City": "Chennai", "Price range": 1, "Aggregate rating": 4.0, "Cuisines": "Seafood", "Restaurant Name": "Fish Market", "Address": "Chennai"},
        {"City": "Kolkata", "Price range": 2, "Aggregate rating": 4.4, "Cuisines": "Seafood", "Restaurant Name": "Oh! Calcutta Seafood", "Address": "Kolkata"},
        # Premium (price 4) for Japanese, Indian - for price range filter testing
        {"City": "Mumbai", "Price range": 4, "Aggregate rating": 4.5, "Cuisines": "Japanese", "Restaurant Name": "Nobu Mumbai", "Address": "Mumbai"},
        {"City": "Delhi", "Price range": 4, "Aggregate rating": 4.6, "Cuisines": "Indian", "Restaurant Name": "Indian Accent", "Address": "Delhi"},
        {"City": "Bangalore", "Price range": 4, "Aggregate rating": 4.4, "Cuisines": "Italian", "Restaurant Name": "Olive Beach", "Address": "Bangalore"},
    ]
    _restaurants_cache = [_record_to_restaurant(r) for r in sample_records]
    _save_restaurants_to_cache_file(_restaurants_cache)
    LOG.info("Sample dataset ready: %d restaurants loaded (saved to cache)", len(_restaurants_cache))

    def _load_hf_in_background() -> None:
        global _restaurants_cache
        if os.getenv("USE_SAMPLE_DATASET_ONLY", "").lower() in ("1", "true", "yes"):
            LOG.info("USE_SAMPLE_DATASET_ONLY set; keeping sample dataset")
            app.state.dataset_status = "sample_only"
            return
        try:
            LOG.info("Loading Hugging Face dataset in background...")
            records = _loader.load()
            validate_dataset(records)
            _restaurants_cache = [_record_to_restaurant(r) for r in records]
            _save_restaurants_to_cache_file(_restaurants_cache)
            app.state.dataset_status = "ready"
            LOG.info("Hugging Face dataset ready: %d restaurants loaded (saved to cache)", len(_restaurants_cache))
        except Exception as e:
            app.state.dataset_status = "degraded"
            app.state.dataset_error = f"{type(e).__name__}: {e}"
            LOG.warning("Hugging Face dataset load failed, staying on sample dataset: %s", app.state.dataset_error)

    threading.Thread(target=_load_hf_in_background, daemon=True).start()


@app.get("/health")
def health() -> dict[str, str]:
    status = getattr(app.state, "dataset_status", "unknown")
    out = {"status": "ok", "dataset": status}
    if getattr(app.state, "dataset_error", None):
        out["dataset_error"] = str(app.state.dataset_error)
    return out


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return get_metrics().snapshot()


@app.get("/places")
def places() -> dict[str, Any]:
    """Return sorted list of distinct places (cities/towns) with first letter capitalised for dropdown."""
    if _restaurants_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")
    distinct = sorted({r.place for r in _restaurants_cache if r.place and r.place != "—"})
    # Capitalise first letter of each word (e.g. "new delhi" -> "New Delhi")
    capitalised = [p.strip().title() for p in distinct]
    return {"places": capitalised, "count": len(capitalised)}


@app.get("/data-coverage")
def data_coverage() -> dict[str, Any]:
    """Return summary of restaurant data: per place, count and available cuisines/price ranges."""
    if _restaurants_cache is None:
        raise HTTPException(status_code=503, detail="Dataset not loaded")
    by_place: dict[str, Any] = {}
    for r in _restaurants_cache:
        place = r.place
        if place not in by_place:
            by_place[place] = {"count": 0, "cuisines": set(), "price_ranges": set()}
        by_place[place]["count"] += 1
        by_place[place]["cuisines"].update(r.cuisines)
        by_place[place]["price_ranges"].add(r.price_range)
    # Convert sets to sorted lists for JSON
    out = {}
    for place, data in sorted(by_place.items()):
        out[place] = {
            "restaurant_count": data["count"],
            "cuisines": sorted(data["cuisines"]),
            "price_ranges": sorted(data["price_ranges"]),
        }
    return {"by_place": out, "total_restaurants": len(_restaurants_cache)}


_PRICE_LABELS = {
    1: "₹0 - ₹300",
    2: "₹300 - ₹600",
    3: "₹600 - ₹1000",
    4: "₹1000+",
}


def _no_match_rationale(req: RecommendRequest) -> str:
    """Build a specific message when no restaurants match the exact criteria."""
    if req.rating_min >= 5.0:
        rating_str = "(5.0+)"
    elif req.rating_min == 0 and req.rating_max < 3.0:
        rating_str = "(below 3.0)"
    else:
        rating_str = f"({req.rating_min}-{req.rating_max})"
    cuisine_str = ", ".join(req.cuisines) if req.cuisines else "any"
    price_str = _PRICE_LABELS.get(req.price_range, f"₹{req.price_range}")
    return (
        f"We're unable to find any restaurants in {req.place} offering {cuisine_str} cuisine "
        f"that fall within the hotel ratings range of {rating_str} and your selected price range of ({price_str})."
    )


def _filter_strict(restaurants: list, req: RecommendRequest) -> list:
    """
    Strict filter only: no fallbacks. Returns restaurants that match place, price,
    rating range, and cuisine exactly. When no match, caller shows specific message.
    """
    prefs = UserPreferences(
        place=req.place,
        price_range=req.price_range,
        rating_min=req.rating_min,
        rating_max=req.rating_max,
        cuisines=req.cuisines,
    )
    return filter_restaurants(restaurants, prefs)


@app.post("/recommend")
async def recommend(req: RecommendRequest, request: Request) -> dict[str, Any]:
    rid = request.headers.get("X-Request-ID")
    with with_request_id(rid):
        if _restaurants_cache is None:
            raise HTTPException(status_code=503, detail="Dataset not initialized yet")

        metrics_store = get_metrics()
        metrics_store.increment_requests()

        LOG.info(
            "Recommend request: place=%r price_range=%d rating=%s-%s cuisines=%r; dataset size=%d",
            req.place, req.price_range, req.rating_min, req.rating_max, req.cuisines, len(_restaurants_cache),
        )

        try:
            filtered = _filter_strict(_restaurants_cache, req)
            if not filtered:
                rationale = _no_match_rationale(req)
                LOG.info("No restaurants matched exact criteria: %s", rationale)
                return {
                    "recommended_restaurant": {
                        "name": "—",
                        "location": req.place,
                        "price_range": req.price_range,
                        "rating": 0.0,
                        "cuisines": req.cuisines,
                    },
                    "rationale": rationale,
                    "alternatives": [],
                }

            ranked = rank_restaurants(filtered, req, limit=int(os.getenv("TOP_N", "10")))
            # Deduplicate by (name, place) so the same restaurant is not returned multiple times
            seen: set[tuple[str, str]] = set()
            unique_ranked: list = []
            for sr in ranked:
                key = (sr.restaurant.restaurant_name.strip(), sr.restaurant.place.strip())
                if key not in seen:
                    seen.add(key)
                    unique_ranked.append(sr)
            ranked = unique_ranked

            chosen, rationale = _choose_and_rationale(req, ranked)

            # Generate one-line rationale for each restaurant via LLM (fallback to templates on any error)
            try:
                rationales = _generate_one_line_rationales(req, ranked)
            except Exception as e:
                LOG.exception("Rationale generation failed, using fallbacks: %s", e)
                rationales = [_fallback_rationale(req, sr.restaurant, i) for i, sr in enumerate(ranked)]

            recommended_dict = {
                "restaurant_name": chosen.restaurant_name,
                "place": chosen.place,
                "price_range": chosen.price_range,
                "rating": chosen.rating,
                "cuisines": chosen.cuisines,
            }
            alternatives_dicts = [
                {
                    "restaurant_name": sr.restaurant.restaurant_name,
                    "place": sr.restaurant.place,
                    "price_range": sr.restaurant.price_range,
                    "rating": sr.restaurant.rating,
                    "cuisines": sr.restaurant.cuisines,
                }
                for sr in ranked[1:]
            ]

            formatted = format_recommendation(
                recommended=recommended_dict,
                rationale=rationale,
                alternatives=alternatives_dicts,
            )
            metrics_store.increment_recommendations()

            # Build response with rationale per restaurant
            rec_rationale = rationales[0] if rationales else rationale
            alt_with_rationales = [
                {
                    "name": a.name,
                    "location": a.location,
                    "price": a.price,
                    "rating": a.rating,
                    "cuisine": a.cuisine,
                    "rationale": rationales[i + 1] if i + 1 < len(rationales) else "",
                }
                for i, a in enumerate(formatted.alternatives)
            ]

            return {
                "recommended_restaurant": {
                    "name": formatted.recommended_restaurant.name,
                    "location": formatted.recommended_restaurant.location,
                    "price": formatted.recommended_restaurant.price,
                    "rating": formatted.recommended_restaurant.rating,
                    "cuisine": formatted.recommended_restaurant.cuisine,
                    "rationale": rec_rationale,
                },
                "rationale": formatted.rationale,
                "alternatives": alt_with_rationales,
            }
        except HTTPException:
            raise
        except Exception as e:
            metrics_store.increment_errors()
            LOG.exception("Recommendation failed: %s", e)
            raise HTTPException(status_code=500, detail="Internal error") from e

