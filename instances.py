import json
from collections import defaultdict

# Load your JSON data (assuming it's already loaded into `data`)
with open("data1.0.json", encoding="utf-8") as f:
    data = json.load(f)

# # Extract only the "recipes" part
# recipes_data = data.get("recipes", {})

# # Save to a new file
# with open("recipes_only.json", "w", encoding="utf-8") as f:
#     json.dump(recipes_data, f, indent=2)
# Set of items you want to exclude from the ingredients list
excluded_ingredients = {
    "Desc_Leaves_C",
    "Desc_Wood_C",
    "Desc_HogParts_C",
    "Desc_StingerParts_C",
    "Desc_HatcherParts_C",
    "Desc_SpitterParts_C",
    
    
    # Add more if needed
}
# Alternatives to include 


# Recipes to exclude based on what they produce
excluded_products = {"Desc_GenericBiomass_C"}

# Dictionary to count total usage of each ingredient
ingredient_counts = defaultdict(float)

# Loop through all recipes extract number of instances of machinable recipes
for recipe in data["recipes"].values():
    if recipe.get("inMachine") and not recipe.get("inWorkshop"):

        product_items = [product["item"] for product in recipe.get("products", [])]

        if any(p in excluded_products for p in product_items):
            continue

        # Only count ingredients not in the exclusion list
        for ingredient in recipe.get("ingredients", []):
            item = ingredient["item"]
            if item not in excluded_ingredients:
                ingredient_counts[item] += 1  # Or += ingredient["amount"] for total

# Print out the total ingredient requirements
for item, count in sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{item}: {count}")
