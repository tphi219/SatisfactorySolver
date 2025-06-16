import json

# Load full JSON
with open("data1.0.json", encoding="utf-8") as f:
    full_data = json.load(f)

# Extract all recipes
all_recipes = full_data.get("recipes", {})

# Separate based on the 'alternate' attribute
alternate_recipes = {}
normal_recipes = {}

for key, recipe in all_recipes.items():
    if recipe.get("inMachine") and not recipe.get("inWorkshop"):
        if recipe.get("alternate", False):
            alternate_recipes[key] = recipe
        else:
            normal_recipes[key] = recipe

# Save alternate recipes
with open("alternate_recipes.json", "w", encoding="utf-8") as f:
    json.dump(alternate_recipes, f, indent=2)

# Save normal recipes
with open("normal_recipes.json", "w", encoding="utf-8") as f:
    json.dump(normal_recipes, f, indent=2)