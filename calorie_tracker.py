import streamlit as st
import os
import requests
from dotenv import load_dotenv
import math

load_dotenv()
API_KEY = os.getenv("USDA_API_KEY")

# ------------------ helpers ------------------

def cycle_fill(key):
    # increment 0..4 then wrap to 0
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

def _polar(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)

def render_circle(fill_level, label):
    # Render a pie-sector fill: 0, 90, 180, 270, 360 degrees starting at -90 (top).
    fraction = fill_to_fraction.get(fill_level, 0)
    cx, cy = 60, 60
    r = 50
    start_angle = -90
    sweep = 360 * fraction
    end_angle = start_angle + sweep

    # When fully filled, draw a full red circle to avoid arc seam issues.
    if fraction >= 1.0:
        sector_svg = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ef4444"/>'
    elif fraction <= 0.0:
        sector_svg = ""  # nothing red
    else:
        # compute start and end points on circumference
        x1, y1 = _polar(cx, cy, r, start_angle)
        x2, y2 = _polar(cx, cy, r, end_angle)
        large_arc = 1 if sweep > 180 else 0
        # path: move to center, line to start point, arc to end point, close
        path = (
            f"M {cx} {cy} L {x1:.3f} {y1:.3f} "
            f"A {r} {r} 0 {large_arc} 1 {x2:.3f} {y2:.3f} Z"
        )
        sector_svg = f'<path d="{path}" fill="#ef4444"/>'

    svg = f"""
    <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <!-- grey background circle -->
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="#e5e7eb"/>
        {sector_svg}
        <!-- thin outline -->
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#9ca3af" stroke-width="2"/>
    </svg>
    <div style="text-align:center;font-weight:600">{label}</div>
    """
    st.markdown(svg, unsafe_allow_html=True)

def render_glass(fill_level):
    # Draw the cup (trapezium) and compute a trapezoid polygon for the filled area
    # instead of using clipPath; this avoids clip-path rendering issues in some contexts.
    fraction = fill_to_fraction.get(fill_level, 0)

    # cup corners
    top_left = (30.0, 10.0)
    top_right = (90.0, 10.0)
    bottom_right = (75.0, 140.0)
    bottom_left = (45.0, 140.0)

    max_inner_top = top_left[1]
    max_inner_bottom = bottom_left[1]
    max_fill_height = max_inner_bottom - max_inner_top  # 130

    fill_px = fraction * max_fill_height
    fill_px = max(0.0, min(fill_px, max_fill_height))
    y_fill_top = max_inner_bottom - fill_px

    # If fraction is 0, skip drawing the red fill polygon; cup background should still show.
    fill_polygon_svg = ""
    if fraction > 0:
        # Compute intersection points on the left and right edges where the horizontal fill line at y_fill_top meets them.
        # left edge runs from top_left -> bottom_left
        left_t = 0.0
        left_dy = bottom_left[1] - top_left[1]
        if left_dy != 0:
            left_t = (y_fill_top - top_left[1]) / left_dy
        x_left = top_left[0] + left_t * (bottom_left[0] - top_left[0])

        # right edge runs from top_right -> bottom_right
        right_t = 0.0
        right_dy = bottom_right[1] - top_right[1]
        if right_dy != 0:
            right_t = (y_fill_top - top_right[1]) / right_dy
        x_right = top_right[0] + right_t * (bottom_right[0] - top_right[0])

        # If fully filled, draw the full cup area (top->top->bottom->bottom)
        if fraction >= 1.0:
            filled_points = f"{top_left[0]},{top_left[1]} {top_right[0]},{top_right[1]} {bottom_right[0]},{bottom_right[1]} {bottom_left[0]},{bottom_left[1]}"
        else:
            # polygon from the horizontal fill top line down to bottom corners
            filled_points = f"{x_left:.3f},{y_fill_top:.3f} {x_right:.3f},{y_fill_top:.3f} {bottom_right[0]},{bottom_right[1]} {bottom_left[0]},{bottom_left[1]}"

        fill_polygon_svg = f'<polygon points="{filled_points}" fill="#ef4444" />'

    svg = f"""
    <svg width="120" height="160" viewBox="0 0 120 160" xmlns="http://www.w3.org/2000/svg">
        <!-- cup background -->
        <polygon points="{top_left[0]},{top_left[1]} {top_right[0]},{top_right[1]} {bottom_right[0]},{bottom_right[1]} {bottom_left[0]},{bottom_left[1]}"
            fill="#e5e7eb" stroke="#9ca3af" stroke-width="2"/>
        {fill_polygon_svg}
        <!-- thin outline -->
        <polygon points="{top_left[0]},{top_left[1]} {top_right[0]},{top_right[1]} {bottom_right[0]},{bottom_right[1]} {bottom_left[0]},{bottom_left[1]}"
            fill="none" stroke="#9ca3af" stroke-width="2"/>
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

# ensure our session keys exist
for k in ("plate_fill", "bowl_fill", "glass_fill"):
    if k not in st.session_state:
        st.session_state[k] = 0

food_name = st.text_input("Enter food name:")

portion_type = st.selectbox(
    "Select portion type:",
    ["Plate", "Bowl", "Glass", "Piece / Slice"]
)

if portion_type in ["Plate", "Bowl"]:
    key = f"{portion_type.lower()}_fill"
    # unique button key so Streamlit sees it as different control than other buttons
    if st.button(f"Click to fill {portion_type.lower()}", key=key + "_btn"):
        cycle_fill(key)
    render_circle(st.session_state.get(key, 0), portion_type)
    fraction = fill_to_fraction[st.session_state.get(key, 0)]

elif portion_type == "Glass":
    key = "glass_fill"
    if st.button("Click to fill glass", key=key + "_btn"):
        cycle_fill(key)
    render_glass(st.session_state.get(key, 0))
    fraction = fill_to_fraction[st.session_state.get(key, 0)]

else:
    pieces = st.number_input("Number of pieces / slices:", min_value=1, step=1)

# ------------------ calculate ------------------

if st.button("Search", key="search_btn"):
    if not food_name.strip():
        st.write("Please enter a food name.")
    else:
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
