import json
import networkx as nx
import matplotlib.pyplot as plt

# Load your recipe data
with open("data1.0.json", encoding="utf-8") as f:
    data = json.load(f)

# Build a directed graph
G = nx.DiGraph()

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
# Add edges from ingredients to products
for recipe in data["recipes"].values():
    if recipe.get("inMachine") and not recipe.get("inWorkshop"):
        ingredients = recipe.get("ingredients", [])
        products = recipe.get("products", [])
        for ing in ingredients:
            for prod in products:
                G.add_edge(ing["item"], prod["item"])

# Compute PageRank
ranks = nx.pagerank(G, alpha=0.85)

# Show top 10 most important items
for item, score in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
    print(f"{item}: {score:.4f}")

# Basic layout
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, k=0.5, iterations=50)

# Draw nodes and edges
nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", arrowsize=15, font_size=8)
plt.title("Crafting Dependency Graph")
plt.tight_layout()
plt.show()