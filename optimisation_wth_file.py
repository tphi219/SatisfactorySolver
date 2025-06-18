import pulp as pl
import json
import networkx as nx

# --- Config ---
min_stock = 1
max_stock = 10
input_limit = 480000
reward_terminal_use = 1000

manual_weights = {
    'Desc_SpaceElevatorPart_10_C': 0.1,
    'Desc_SpaceElevatorPart_11_C': 0.1,
    'Desc_SpaceElevatorPart_12_C': 0.1,
    'Desc_Battery_C': 2.5,
    'Desc_NuclearFuelRod_C': 0.1,
    'Desc_PlutoniumFuelRod_C': 0.001,
    'Desc_FicsoniumFuelRod_C': 0.1,
    'Desc_AlienPowerFuel_C': 0.0001
}

excluded_ingredients = {
    "Desc_Leaves_C", "Desc_Wood_C", "Desc_HogParts_C", "Desc_StingerParts_C",
    "Desc_HatcherParts_C", "Desc_SpitterParts_C", "Desc_AlienProtein_C",
    "Desc_Mycelia_C", "Desc_Biofuel_C", "Desc_LiquidBiofuel_C", "Desc_PackagedBiofuel_C",
    "Desc_CartridgeStandard_C", "Desc_GenericBiomass_C", "Desc_Crystal_mk2_C",
    "Desc_Crystal_C", "Desc_Crystal_mk3_C", "Desc_Gunpowder_C",
}

excluded_final_products = {
    "Desc_CompactedCoal_C", "Desc_FluidCanister_C", "Desc_GasTank_C",
    "Desc_PetroleumCoke_C", "Desc_LiquidFuel_C", "Desc_HeavyOilResidue_C",
    "Desc_IronScrew_C",
}

converter_exception = "Desc_Diamond_C"

# --- Load Data & Build Graph ---
with open("data1.0_no_screw.json", encoding="utf-8") as f:
    data = json.load(f)

G = nx.DiGraph()
for recipe in data["recipes"].values():
    if not (recipe.get("inMachine") and not recipe.get("inWorkshop") and not recipe.get("alternate")):
        continue

    produced_in = recipe.get("producedIn", [])
    ingredients = recipe.get("ingredients", [])
    products = recipe.get("products", [])
    if any(ing["item"] in excluded_ingredients for ing in ingredients):
        continue
    if any(prod["item"] in excluded_final_products for prod in products):
        continue
    if ("Desc_Packager_C" in produced_in or "Desc_Converter_C" in produced_in) and not any(
        ing["item"] == converter_exception for ing in ingredients):
        continue

    for ing in ingredients:
        for prod in products:
            rate = round((ing["amount"] / recipe["time"]) * 60, 2)
            G.add_edge(ing["item"], prod["item"], rate=rate)

# --- Node Classification ---
entry_nodes = [n for n in G.nodes if G.in_degree(n) == 0]
terminal_nodes = [n for n in G.nodes if G.out_degree(n) == 0]
intermediate_nodes = [n for n in G.nodes if n not in entry_nodes and n not in terminal_nodes]

# --- LP Variables ---
nodes_to_optimize = intermediate_nodes + terminal_nodes
part_recipe = {node: pl.LpVariable(f"var_{node}", lowBound=0) for node in nodes_to_optimize}
stockpile_vars = {node: pl.LpVariable(f"stockpile_{node}", lowBound=min_stock, upBound=max_stock) for node in intermediate_nodes}
terminal_usage = {node: pl.LpVariable(f"use_{node}", cat='Binary') for node in terminal_nodes}

# --- LP Problem Setup ---
prob = pl.LpProblem("Production_Optimization", pl.LpMaximize)

# --- Objective Function ---
# objective = pl.lpSum([
#     manual_weights.get(node, 1.0) * part_recipe[node] for node in terminal_nodes if node in part_recipe
# ]) + reward_terminal_use * pl.lpSum(terminal_usage.values())
# prob += objective

# --- Choose a specific intermediate node to maximize ---
target_node = "Desc_ModularFrame_C"  # Change to the item you want to maximize

# --- Objective Function ---
if target_node in part_recipe:
    prob.setObjective(part_recipe[target_node])
else:
    raise ValueError(f"Target node '{target_node}' is not part of the optimization variables.")



# --- Link terminal usage ---
M = 1000
for node in terminal_nodes:
    for pred in G.predecessors(node):
        if pred in part_recipe:
            prob += part_recipe[pred] <= M * terminal_usage[node], f"Link_{node}_{pred}"

# --- Input Limits ---
for node in entry_nodes:
    consumption = []
    for succ in G.successors(node):
        if succ in part_recipe:
            rate = G[node][succ].get("rate", 0)
            consumption.append(part_recipe[succ] * rate)
    if consumption:
        prob += pl.lpSum(consumption) <= input_limit, f"InputLimit_{node}"

# --- Balance Intermediates ---
for node in intermediate_nodes:
    production = []
    consumption = []
    for pred in G.predecessors(node):
        if pred in part_recipe:
            production.append(part_recipe[pred] * G[pred][node].get("rate", 0))
    for succ in G.successors(node):
        if succ in part_recipe:
            consumption.append(part_recipe[succ] * G[node][succ].get("rate", 0))
    if production and consumption:
        prob += pl.lpSum(production) >= pl.lpSum(consumption) + stockpile_vars[node], f"Balance_{node}"

# --- Solve ---
status = prob.solve()

# --- Results ---
print("\n--- Optimization Results ---")
print(f"Status: {pl.LpStatus[status]}")
print(f"Objective value (machines for {target_node}): {part_recipe[target_node].varValue:.2f}")

# List all used nodes and their machine counts
print("\n--- Machine Counts ---")
for node, var in part_recipe.items():
    if var.varValue and var.varValue > 0.01:
        print(f"{node}: {var.varValue:.2f} machines")

# List only terminals that were used
print("\n--- Terminals Used ---")
for node in terminal_nodes:
    var = part_recipe.get(node)
    if var and var.varValue and var.varValue > 0.01:
        print(f"{node}: {var.varValue:.2f} machines")

# If you want to show intermediates too
print("\n--- Intermediates Used ---")
for node in intermediate_nodes:
    var = part_recipe.get(node)
    if var and var.varValue and var.varValue > 0.01:
        print(f"{node}: {var.varValue:.2f} machines")
