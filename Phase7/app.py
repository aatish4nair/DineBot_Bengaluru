from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import streamlit as st

from phase7_ui.client import ApiClient, ApiError
from phase7_ui.config import UIConfig
from phase7_ui.models import PreferenceInput


st.set_page_config(page_title="DineBot Bengaluru 🍜📍🤖", layout="centered", initial_sidebar_state="collapsed")

# Price range labels for display (₹ in both parts)
PRICE_RANGE_LABELS = {
    1: "₹0 - ₹300",
    2: "₹300 - ₹600",
    3: "₹600 - ₹1000",
    4: "₹1000+",
}

# Match ui.webp: light bg #F8F8F8, white form box #FFFFFF, dark text, orange button #E67C3F
st.markdown("""
<style>
    .stApp { max-width: 560px; margin: 0 auto; background: #F8F8F8 !important; }
    .main .block-container { padding: 1.5rem 1rem; background: #F8F8F8 !important; }
    .title-wrapper { text-align: center; margin-bottom: 0.75rem; margin-top: 4.5em; }
    .title-line1 { font-size: 2rem; font-weight: 700; color: #0F0F0F !important; margin: 0; line-height: 1.2; text-align: center; }
    h2, h3 { text-align: center; color: #0F0F0F !important; font-weight: 600; }
    p, label, span, .stMarkdown { color: #0F0F0F !important; font-size: 14px; }
    [data-testid="stCaptionContainer"] { color: #0F0F0F !important; text-align: center; }
    div[data-testid="stForm"] { 
        border: 1px solid #e0e0e0; border-radius: 12px; padding: 1.5rem; 
        background: #FFFFFF !important; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    div[data-testid="stForm"]:focus-within { border-color: #d4a574; box-shadow: 0 0 0 1px #d4a574; }
    .result-block { 
        margin: 0.75rem auto; padding: 0.6rem 0.9rem; border: 2px solid #d96b2f; border-radius: 10px; 
        background: #FFDBBB !important; color: #0F0F0F; text-align: left; max-width: 420px; font-size: 13px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .result-block p { font-size: 13px !important; color: #0F0F0F !important; margin: 0.25rem 0 !important; }
    .result-block .restaurant-name { font-size: 1.05rem !important; font-weight: 600 !important; color: #0F0F0F !important; margin-bottom: 0.2rem !important; }
    .result-block .rating-stars { color: #d4a017; font-size: 0.9rem; letter-spacing: 1px; margin-bottom: 0.35rem; }
    .result-block .loc-price-row { display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 0.2rem 0; }
    .top-recommendations-heading { text-align: center; font-size: 2rem; font-weight: 600; color: #0F0F0F; margin: 0.5rem 0 1rem 0; }
    .no-match-message { font-size: 1.1rem !important; font-weight: 600 !important; color: #0F0F0F !important; text-align: center; padding: 1rem; line-height: 1.5; }
    [data-testid="stSelectbox"] label { color: #0F0F0F !important; }
    [data-testid="stSidebar"] { background: #F8F8F8 !important; }
    [data-testid="stSidebar"] .stMarkdown { color: #0F0F0F !important; }
    section[data-testid="stSidebar"] { background: #F8F8F8 !important; }
    div[data-baseweb="select"] > div { 
        background: #FFFFFF !important; 
        border: 1px solid #e0e0e0 !important; 
        border-radius: 8px; color: #0F0F0F !important;
    }
    div[data-baseweb="select"] > div:focus-within { border-color: #d4a574 !important; box-shadow: 0 0 0 1px #d4a574 !important; }
    div[data-baseweb="select"] input { background: #FFFFFF !important; color: #0F0F0F !important; }
    [data-testid="stSelectbox"] > div > div { background: #FFFFFF !important; border: 1px solid #e0e0e0 !important; color: #0F0F0F !important; }
    [data-testid="stSelectbox"] > div > div:focus-within { border-color: #d4a574 !important; }
    [data-testid="stSelectbox"] svg, div[data-baseweb="select"] svg { fill: #0F0F0F !important; color: #0F0F0F !important; }
    [data-testid="stWidgetLabel"] { color: #0F0F0F !important; }
    div[data-testid="stFormSubmitButton"] { text-align: center; margin-top: 1rem; }
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%; max-width: 100%; margin: 0 auto; display: block;
        padding: 0.75rem 1.5rem !important; font-size: 1.25rem !important; font-weight: 600 !important;
        border-radius: 8px; border: none !important; background: #E67C3F !important; color: #0F0F0F !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover { background: #d96b2f !important; box-shadow: 0 2px 4px rgba(230,124,63,0.3); }
    div[data-testid="stFormSubmitButton"] > button:focus, div[data-testid="stFormSubmitButton"] > button:active {
        outline: none !important; border: none !important; box-shadow: 0 0 0 2px rgba(230,124,63,0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="title-wrapper">'
    '<div class="title-line1">DineBot Bengaluru 🍜📍🤖</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.caption("Choose your preferences and get your recommendations.")

config = UIConfig.from_env()
client = ApiClient(config=config)

# Fetch places from backend (dynamic from dataset); fallback = 30 Bengaluru regions (ManikaSaini/zomato-restaurant-recommendation)
DEFAULT_PLACES = [
    "BTM", "Banashankari", "Bannerghatta Road", "Basavanagudi", "Bellandur",
    "Brigade Road", "Brookefield", "Church Street", "Electronic City", "Frazer Town",
    "HSR", "Indiranagar", "JP Nagar", "Jayanagar", "Kalyan Nagar", "Kammanahalli",
    "Koramangala 4th Block", "Koramangala 5th Block", "Koramangala 6th Block", "Koramangala 7th Block",
    "Lavelle Road", "MG Road", "Malleshwaram", "Marathahalli", "New BEL Road",
    "Old Airport Road", "Rajajinagar", "Residency Road", "Sarjapur Road", "Whitefield",
]
if "places" not in st.session_state:
    try:
        import requests
        r = requests.get(config.api_base_url.rstrip("/") + "/places", timeout=5)
        if r.status_code == 200:
            data = r.json()
            st.session_state["places"] = data.get("places", DEFAULT_PLACES) or DEFAULT_PLACES
        else:
            st.session_state["places"] = DEFAULT_PLACES
    except Exception:
        st.session_state["places"] = DEFAULT_PLACES
PLACES = st.session_state["places"]

with st.sidebar:
    with st.expander("API configuration", expanded=False):
        st.write("Backend:", f"`{config.api_base_url}`")

# Placeholder for "empty" - no pre-entered values
PLACEHOLDER_PLACE = "-- Select location --"
PLACEHOLDER_PRICE = 0
PLACEHOLDER_RATING = ""
PLACEHOLDER_CUISINE = "-- Select cuisine --"
PRICE_OPTIONS = [
    (0, "-- Select price range --"),
    (1, "₹0 - ₹300"),
    (2, "₹300 - ₹600"),
    (3, "₹600 - ₹1000"),
    (4, "₹1000+"),
]
# Rating ranges: key -> (min, max), label
RATING_OPTIONS = [
    ("", "-- Select Hotel Ratings --"),
    ("0_3", "Below 3.0 ratings"),
    ("3_4", "3.0 - 4.0"),
    ("4_5", "4.0 - 5.0"),
    ("5_5.5", "Above 5.0+ ratings"),
]
RATING_RANGE_MAP = {
    "0_3": (0.0, 3.0),
    "3_4": (3.0, 4.0),
    "4_5": (4.0, 5.0),
    "5_5.5": (5.0, 5.5),
}
CUISINES = ["Italian", "Indian", "Chinese", "Japanese", "Mexican", "Thai", "Cafe", "Fast Food", "Seafood"]

with st.form("prefs_form"):
    col1, col2 = st.columns(2)
    with col1:
        place = st.selectbox(
            "Location",
            options=[PLACEHOLDER_PLACE] + PLACES,
            format_func=lambda x: ("BTM Layout" if str(x).strip().lower() == "btm" else ("HSR Layout" if str(x).strip().lower() == "hsr" else x)),
            index=0,
        )
        rating_range_key = st.selectbox(
            "Hotel Ratings",
            options=[r[0] for r in RATING_OPTIONS],
            format_func=lambda x: next((l for v, l in RATING_OPTIONS if v == x), str(x)),
            index=0,
        )
    with col2:
        price_range = st.selectbox(
            "Price range",
            options=[r[0] for r in PRICE_OPTIONS],
            format_func=lambda x: next(l for v, l in PRICE_OPTIONS if v == x),
            index=0,
        )
        cuisine = st.selectbox(
            "Cuisine",
            options=[PLACEHOLDER_CUISINE] + CUISINES,
            index=0,
        )
    submitted = st.form_submit_button("Get recommendation")

def price_label(price: int) -> str:
    return PRICE_RANGE_LABELS.get(price, f"₹{price}")

def rating_to_stars(rating: float) -> str:
    """Convert numeric rating (0-5.5) to golden star display."""
    r = max(0, min(5.5, float(rating)))
    full = min(5, round(r))
    empty = 5 - full
    return "★" * full + "☆" * empty

def render_card(index: int, name: str, location: str, price: int, rating: float, cuisine: str, rationale: str = "") -> str:
    pl = price_label(price)
    stars = rating_to_stars(rating)
    rationale_html = f'<p class="rationale" style="margin-top: 0.35rem; font-style: italic; color: #0F0F0F; font-size: 12px !important;">{rationale}</p>' if rationale else ""
    return (
        f'<div class="result-block">'
        f'<p class="restaurant-name">#{index} {name}</p>'
        f'<p class="rating-stars" title="{rating}">{stars} ({rating})</p>'
        f'<div class="loc-price-row"><span><strong>Location:</strong> {location}</span><span><strong>Price range:</strong> {pl}</span></div>'
        f'<p><strong>Cuisine:</strong> {cuisine}</p>'
        f'{rationale_html}'
        f'</div>'
    )

if submitted:
    if place == PLACEHOLDER_PLACE or price_range == PLACEHOLDER_PRICE or rating_range_key == PLACEHOLDER_RATING or cuisine == PLACEHOLDER_CUISINE:
        st.error("Please select all options: Location, Price range, Hotel Ratings, and Cuisine.")
    else:
        rating_min, rating_max = RATING_RANGE_MAP[rating_range_key]
        prefs = PreferenceInput(
            place=place.strip(),
            price_range=int(price_range),
            rating_min=float(rating_min),
            rating_max=float(rating_max),
            cuisines=[cuisine],
        )
        try:
            with st.spinner("Finding recommendations..."):
                rec = client.recommend(prefs)
        except ApiError as e:
            st.error(str(e))
            st.info("Ensure the backend is running: `USE_SAMPLE_DATASET_ONLY=1 uvicorn App.backend.main:app --port 8000`")
        else:
            all_restaurants = [rec.recommended_restaurant]
            if rec.alternatives:
                all_restaurants.extend(rec.alternatives)

            if all_restaurants and all_restaurants[0].name and all_restaurants[0].name != "—":
                st.markdown('<p class="top-recommendations-heading">Top-Recommendations</p>', unsafe_allow_html=True)
                for i, r in enumerate(all_restaurants, start=1):
                    if r.name and r.name != "—":
                        st.markdown(
                            render_card(i, r.name, r.location, r.price, r.rating, r.cuisine, getattr(r, "rationale", "") or ""),
                            unsafe_allow_html=True,
                        )
            else:
                msg = rec.rationale or "No restaurants matched your filters. Try relaxing price, rating, or cuisine."
                st.markdown(f'<p class="no-match-message">{msg}</p>', unsafe_allow_html=True)
