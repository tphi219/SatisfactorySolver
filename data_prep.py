import json
from collections import defaultdict

# Clean the item ID by removing Desc_ prefix and _C suffix
def clean_id(item_id):
    if item_id.startswith("Desc_") and item_id.endswith("_C"):
        return item_id[5:-2]
    return item_id

excluded_ingredients = {
    "Desc_Leaves_C", "Desc_Wood_C", "Desc_HogParts_C", "Desc_StingerParts_C",
    "Desc_HatcherParts_C", "Desc_SpitterParts_C", "Desc_AlienProtein_C",
    "Desc_Mycelia_C", "Desc_Biofuel_C", "Desc_LiquidBiofuel_C",
    "Desc_PackagedBiofuel_C", "Desc_CartridgeStandard_C", "Desc_GenericBiomass_C",
    "Desc_Crystal_mk2_C", "Desc_Crystal_C", "Desc_Crystal_mk3_C", "Desc_Gunpowder_C",
}
excluded_final_products = {
    "Desc_CompactedCoal_C", "Desc_FluidCanister_C", "Desc_GasTank_C",
    "Desc_PetroleumCoke_C", "Desc_LiquidFuel_C", "Desc_HeavyOilResidue_C",
    "Desc_IronScrew_C",
}
converter_exception = "Desc_Diamond_C"

# Set of raw ores and ingots to exclude from producedFrom inputs
excluded_production_inputs = {
    "OreIron",
    "OreGold",
    "OreCopper",
    "IronIngot",
    "CopperIngot",
    "SteelIngot",
    "GoldIngot",
    "AluminiumIngot",
    "OreBauxite",
    "RawQuartz",
}

with open("data1.0_no_screw.json", encoding="utf-8") as f:
    data = json.load(f)

item_graph = {}

for recipe in data["recipes"].values():
    time = recipe.get("time", 1)
    produced_in = recipe.get("producedIn", [])
    ingredients = recipe.get("ingredients", [])
    products = recipe.get("products", [])

    if not (recipe.get("inMachine") and not recipe.get("inWorkshop") and not recipe.get("alternate")):
        continue
    if any(ing["item"] in excluded_ingredients for ing in ingredients):
        continue
    if any(prod["item"] in excluded_final_products for prod in products):
        continue
    if ("Desc_Packager_C" in produced_in or "Desc_Converter_C" in produced_in) and not any(
        ing["item"] == converter_exception for ing in ingredients):
        continue

    # Get all cleaned input IDs
    input_ids = [clean_id(ing["item"]) for ing in ingredients]

    # Filter out excluded raw ores and ingots from inputs for producedFrom
    input_ids_filtered = [i for i in input_ids if i not in excluded_production_inputs]

    for product in products:
        raw_product_id = product["item"]
        product_id = clean_id(raw_product_id)
        product_amt = product["amount"]
        product_rate = (product_amt / time) * 60  # Output per minute

        if product_id not in item_graph:
            item_graph[product_id] = {
                "name": product_id,
                "producedFrom": {},
                "usedIn": {}
            }

        # Store producedFrom with filtered inputs and production rate
        item_graph[product_id]["producedFrom"] = {
            "inputs": input_ids_filtered,
            "rate": product_rate
        }
        # Still track usedIn for all inputs, including excluded ones
        for ing in ingredients:
            ing_id = clean_id(ing["item"])
            ing_amt = ing["amount"]
            ing_rate = (ing_amt / time) * 60  # consumption rate per minute

            if ing_id not in item_graph:
                item_graph[ing_id] = {
                    "name": ing_id,
                    "producedFrom": {},
                    "usedIn": {}
                }
            item_graph[ing_id]["usedIn"][product_id] = ing_rate

# Save the item graph to JSON file
with open("item_dependency_graph.json", "w") as f:
    json.dump(item_graph, f, indent=2)

# Preview some example items
print(json.dumps(item_graph.get("CrystalOscillator", {}), indent=2))
print(json.dumps(item_graph.get("Cable", {}), indent=2))
