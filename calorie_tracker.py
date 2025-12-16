import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # to access environment variables

API_KEY = os.getenv("USDA_API_KEY")

def search_food(food_name):
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={API_KEY}&query={food_name}"
    response = requests.get(url)
    if response.status_code != 200:
        print("Error:", response.status_code)
        return []
    data = response.json()
    return data.get("foods", [])

def get_calories(food_item):
    calories = None
    for nutrient in food_item.get("foodNutrients", []):
        if nutrient.get("nutrientName") == "Energy" and nutrient.get("unitName") == "KCAL":
            calories = nutrient.get("value")
    return calories

st.title("Calorie Tracker")

food_name = st.text_input("Enter food name:")




portion_type = st.selectbox(
    "Select portion type:",
    ["Plate", "Bowl", "Glass", "Piece / Slice"]
)

fraction_map = {
    "1/4": 0.25,
    "1/2": 0.5,
    "3/4": 0.75,
    "Full": 1.0
}

# USDA serving equivalents
portion_servings = {
    "Plate": 2.5,
    "Bowl": 1.75,
    "Glass": 1.0
}

if portion_type == "Piece / Slice":
    pieces = st.number_input(
        "Number of pieces / slices:",
        min_value=1,
        step=1
    )
else:
    fraction_label = st.selectbox(
        "Select portion size:",
        ["1/4", "1/2", "3/4", "Full"]
    )
    fraction = fraction_map[fraction_label]





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
                total_calories = base_calories * pieces
                st.write(
                    f"{results[0]['description']}: "
                    f"{total_calories:.0f} kcal "
                    f"({pieces} piece(s))"
                )
            else:
                servings = portion_servings[portion_type] * fraction
                total_calories = base_calories * servings
                st.write(
                    f"{results[0]['description']}: "
                    f"{total_calories:.0f} kcal "
                    f"({fraction_label} {portion_type.lower()})"
                )

