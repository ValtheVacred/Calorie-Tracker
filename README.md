# Calorie-Tracker
import os
import requests
from dotenv import load_dotenv

load_dotenv()  #access env. stuff

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
