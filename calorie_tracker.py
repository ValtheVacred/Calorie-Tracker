import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("USDA_API_KEY")

# ------------------ helpers ------------------

def cycle_fill(key):
    st.session_state[key] = (st.session_state.get(key, 0) + 1) % 5

fill_to_fraction = {
    0: 0.0,
    1: 0.25,
    2: 0.5,
    3: 0.75,
    4: 1.0
}

portion_servings = {
    "Plate": 2.5,
    "Bowl": 1.75,
    "Glass": 1.0
}

def render_circle(fill_level, label):
    percent = fill_level * 25
    svg = f"""
    <svg width="120" height="120">
        <circle cx="60" cy="60" r="50" fill="#e5e7eb"/>
        <circle cx="60" cy="60" r="50"
            stroke="#ef4444"
            stroke-width="100"
            stroke-dasharray="{percent} 100"
            transform="rotate(-90 60 60)"
            fill="none"/>
        <circle cx="60" cy="60" r="50" fill="none" stroke="#9ca3af" stroke-width="2"/>
    </svg>
    <div style="text-align:center;font-weight:600">{label}</div>
    """
    st.markdown(svg, unsafe_allow_html=True)

def render_glass(fill_level):
    height = fill_level * 20
    svg = f"""
    <svg width="120" height="160">
        <polygon points="30,10 90,10 75,140 45,140"
            fill="#e5e7eb" stroke="#9ca3af" stroke-width="2"/>
        <rect x="45" y="{140-height}" width="30" height="{height}" fill="#ef4444"/>
    </svg>
    <div style="text-align:center;font-weight:600">Glass</div>
    """
    st.markdown(svg, unsafe_allow_html=True)

def search_food(food_name):
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={API_KEY}&query={food_name}"
    r = requests.get(url)
    return r.json().get("foods", []) if r.status_code == 200 else []

def get_calories(food):
    for n in food.get("foodNutrients", []):
        if n.get("nutrientName") == "Energy" and n.get("unitName") == "KCAL":
            return n.get("value")
    return None

# ------------------ UI ------------------

st.title("Calorie Tracker")

food_name = st.text_input("Enter food name:")

portion_type = st.selectbox(
    "Select portion type:",
    ["Plate", "Bowl", "Glass", "Piece / Slice"]
)

if portion_type in ["Plate", "Bowl"]:
    key = f"{portion_type.lower()}_fill"
    if st.button(f"Click to fill {portion_type.lower()}"):
        cycle_fill(key)
    render_circle(st.session_state.get(key, 0), portion_type)
    fraction = fill_to_fraction[st.session_state.get(key, 0)]

elif portion_type == "Glass":
    key = "glass_fill"
    if st.button("Click to fill glass"):
        cycle_fill(key)
    render_glass(st.session_state.get(key, 0))
    fraction = fill_to_fraction[st.session_state.get(key, 0)]

else:
    pieces = st.number_input("Number of pieces / slices:", min_value=1, step=1)

# ------------------ calculate ------------------

if st.button("Search"):
    results = search_food(food_name)

    if not results:
        st.write("No results found")
    else:
        base_calories = get_calories(results[0])

        if base_calories is None:
            st.write("Calorie data not available")
        else:
            if portion_type == "Piece / Slice":
                total = base_calories * pieces
                st.write(f"{results[0]['description']}: {total:.0f} kcal")
            else:
                servings = portion_servings[portion_type] * fraction
                total = base_calories * servings
                st.write(f"{results[0]['description']}: {total:.0f} kcal")
