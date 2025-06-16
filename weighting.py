import json
import networkx as nx
import matplotlib.pyplot as plt

# Load your recipe data
with open("data1.0.json", encoding="utf-8") as f:
    data = json.load(f)

# Build a directed graph
G = nx.DiGraph()

excluded_ingredients = {
    # All the bio shit 
    "Desc_Leaves_C",
    "Desc_Wood_C",
    "Desc_HogParts_C",
    "Desc_StingerParts_C",
    "Desc_HatcherParts_C",
    "Desc_SpitterParts_C",
    "Desc_AlienProtein_C",
    "Desc_Mycelia_C",
    "Desc_Biofuel_C",
    "Desc_CartridgeStandard_C",
    "Desc_GenericBiomass_C",
}
# Alternatives to include 


# Recipes to exclude based on what they produce
# excluded_products = {"Desc_GenericBiomass_C"}
# Add edges from ingredients to products
for recipe in data["recipes"].values():
    if recipe.get("inMachine") and not recipe.get("inWorkshop") and not recipe.get("alternate") and "Desc_Converter_C" not in recipe.get("producedIn", []):
        ingredients = recipe.get("ingredients", [])
        products = recipe.get("products", [])
        for ing in ingredients:
            if ing["item"] in excluded_ingredients:
                continue
            for prod in products:
                G.add_edge(ing["item"], prod["item"])

# Compute PageRank
ranks = nx.pagerank(G, alpha=0.85)
terminal_nodes = [node for node in G.nodes if G.out_degree(node) == 0]
entry_nodes = [node for node in G.nodes if G.in_degree(node) == 0]
# Print all the nodes
for item, score in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
    print(f"{item}: {score:.4f}")
print(f"\nTerminal Nodes: {terminal_nodes}")
print("######################################")
print(f"Entry Nodes: {entry_nodes}")
# Basic layout
plt.figure()
pos = nx.spring_layout(G, k=2.5)

# Draw nodes and edges
nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=300)

# Highlight terminal nodes in a different color (e.g., red)
nx.draw_networkx_nodes(G, pos, nodelist=terminal_nodes, node_color='red', node_size=500)
nx.draw_networkx_nodes(G, pos, nodelist=entry_nodes, node_color='green', node_size=500)

# Draw edges and labels
nx.draw_networkx_edges(G, pos, arrows=True)
nx.draw_networkx_labels(G, pos, font_size=8)

plt.title("Dependency Graph with Terminal Nodes Highlighted")
plt.show()