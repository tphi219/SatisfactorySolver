import json
import networkx as nx
import matplotlib.pyplot as plt
import pulp as pl

# Load your recipe data
with open("data1.0.json", encoding="utf-8") as f:
    data = json.load(f)

# Build a directed graph
G = nx.DiGraph()


optimise = False
makeplot = True
findUnvisited = True


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
    "Desc_LiquidBiofuel_C",
    "Desc_PackagedBiofuel_C",
    "Desc_CartridgeStandard_C",
    "Desc_GenericBiomass_C",
    "Desc_Crystal_mk2_C",
    "Desc_Crystal_C",
    "Desc_Crystal_mk3_C",
    "Desc_Gunpowder_C",

}

converter_exception = "Desc_Diamond_C"

for recipe in data["recipes"].values():
    produced_in = recipe.get("producedIn", [])
    ingredients = recipe.get("ingredients", [])
    products = recipe.get("products", [])

    # Skip if any excluded ingredient is used
    if any(ing["item"] in excluded_ingredients for ing in ingredients):
        continue

    # Allows if:
    # - it's produced in a machine
    # - not produced in workshop
    # - not an alternate recipe
    # - either not in Converter, or contains Diamond (is the one exception here)
    if (
        recipe.get("inMachine")
        and not recipe.get("inWorkshop")
        and not recipe.get("alternate")
        and (
            "Desc_Packager_C" not in produced_in and "Desc_Converter_C" not in produced_in
            or any(ing["item"] == converter_exception for ing in ingredients)
        )
    ):
        for ing in ingredients:
            
            for prod in products:
                time_sec = recipe["time"]
                amount = ing["amount"]
                rate = (amount / time_sec) * 60  # items per minute
                G.add_edge(ing["item"], prod["item"], amount=amount,time=time_sec, rate=rate,)

# Compute PageRank
ranks = nx.pagerank(G, alpha=0.85)

node = "Desc_IronIngot_C"  # example node

print(f"--- Outgoing edges (products made using {node}) ---")
for _, target, attr in G.out_edges(node, data=True):
    print(f"{node} → {target}: amount = {attr.get('amount', 'N/A')}, time = {attr.get('time', 'N/A')}, rate = {attr.get('rate', 'N/A')}")

print(f"\n--- Incoming edges (ingredients required to make {node}) ---")
for source, _, attr in G.in_edges(node, data=True):
    print(f"{source} → {node}: amount = {attr.get('amount', 'N/A')}, time = {attr.get('time', 'N/A')}, rate = {attr.get('rate', 'N/A')}")
print("\n========================================")


# Get the terminal and entry nodes
terminal_nodes = [node for node in G.nodes if G.out_degree(node) == 0]
entry_nodes = [node for node in G.nodes if G.in_degree(node) == 0]

# Print all the nodes
for item, score in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
    print(f"{item}: {score:.4f}")
print(f"\nTerminal Nodes: {terminal_nodes}")
print("######################################")
print(f"Entry Nodes: {entry_nodes}")

if findUnvisited:
    visited = set()
    for source in entry_nodes:
        for target in terminal_nodes:
            for path in nx.all_simple_paths(G, source=source, target=target):
                visited.update(path)

    # Intermediate nodes
    intermediate_nodes = {n for n in G.nodes if n not in entry_nodes and n not in terminal_nodes}

    # Check which intermediates were visited
    unvisited = intermediate_nodes - visited
    print("Unvisited intermediates:", unvisited)


# paths = []
# target_node = "Desc_ComputerSuper_C" 
# print(target_node in G)  # Should print True if it exists      
# for entry in entry_nodes:
#     try:
#         path = nx.all_simple_paths(G, source=entry, target=target_node)
#         paths.extend(path)
#     except nx.NetworkXNoPath:
#         continue  # skip if no path exists

# # Result: list of paths to the target node from all entry nodes
# for path in paths:
#     print(" -> ".join(path))


if makeplot:
    # Basic layout
    plt.figure()
    # pos = nx.spring_layout(G, k=1.5, iterations=1000, scale=10)
    pos = nx.kamada_kawai_layout(G)
    # pos = nx.spectral_layout(G)
    # pos = nx.shell_layout(G)


    # Draw nodes and edges
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=500)

    # Highlight terminal nodes and entry nodes
    nx.draw_networkx_nodes(G, pos, nodelist=terminal_nodes, node_color='red', node_size=500)
    nx.draw_networkx_nodes(G, pos, nodelist=entry_nodes, node_color='green', node_size=500)

    # Draw edges and labels
    nx.draw_networkx_edges(G, pos, arrows=True)
    nx.draw_networkx_labels(G, pos, font_size=8)

    plt.title("Dependency Graph with Terminal Nodes Highlighted")
    plt.show()

if optimise:
    prob = pl.LpProblem("MaxProduction", pl.LpMaximize)

    # Variables: one for each recipe
    vars = {}
    for recipe_name, recipe in data["recipes"].items():
        if recipe.get("inMachine") and not recipe.get("inWorkshop") and not recipe.get("alternate"):
            vars[recipe_name] = pl.LpVariable(recipe_name, lowBound=0)

    # Objective: maximize production rate of target product (e.g., Reinforced Plate)
    target_item = "Desc_ReinforcedPlate_C"
    objective_expr = []

    for recipe_name, var in vars.items():
        recipe = data["recipes"][recipe_name]
        time_sec = recipe["time"]
        products = recipe.get("products", [])
        for prod in products:
            if prod["item"] == target_item:
                rate_per_min = (prod["amount"] / time_sec) * 60
                objective_expr.append(rate_per_min * var)

    prob += pl.lpSum(objective_expr)

    # Constraints: Input limits for entry nodes (raw materials)
    input_limits = {item: 480 for item in entry_nodes}

    for input_item in entry_nodes:
        usage_expr = []
        for recipe_name, var in vars.items():
            recipe = data["recipes"][recipe_name]
            time_sec = recipe["time"]
            ingredients = recipe.get("ingredients", [])
            for ing in ingredients:
                if ing["item"] == input_item:
                    usage_rate = (ing["amount"] / time_sec) * 60
                    usage_expr.append(usage_rate * var)
        if usage_expr:
            prob += pl.lpSum(usage_expr) <= input_limits[input_item]

    # Solve and print results
    prob.solve()
    print("Status:", pl.LpStatus[prob.status])

    for recipe_name, var in vars.items():
        val = pl.value(var)
        if val and val > 1e-5:
            print(f"{recipe_name}: {val:.2f} cycles per minute")