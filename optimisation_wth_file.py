import pulp as pl
import json
import networkx as nx
## Header notes is that this ignores packager use because yeah makes it even simpler for now
# Ignores alternate recipes using only base game will have change later to remove screw recipes def

def inspect_node(node):
    print(f"\n=== Node: {node} ===")
    
    # Node attributes (if any)
    print("Attributes:")
    print(G.nodes[node])

    # Predecessors (ingredients)
    print("\nPredecessors (ingredients):")
    for pred in G.predecessors(node):
        print(f"  {pred} -> {node}")
        print(f"    Edge data: {G[pred][node]}")

    # Successors (products)
    print("\nSuccessors (products):")
    for succ in G.successors(node):
        print(f"  {node} -> {succ}")
        print(f"    Edge data: {G[node][succ]}")

## Global Control variables 
findUnvisited = True

## User params
stockpile = 0 # This will probably be scaled by quantity needed for buildings
input_limit = 480  # This is the input limit for the raw materials per minute (input nodes for now is blanket)


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
    "Desc_LiquidBiofuel_C",
    "Desc_PackagedBiofuel_C",
    "Desc_CartridgeStandard_C",
    "Desc_GenericBiomass_C",
    "Desc_Crystal_mk2_C",
    "Desc_Crystal_C",
    "Desc_Crystal_mk3_C",
    "Desc_Gunpowder_C",

}
excluded_final_products = {
    "Desc_CompactedCoal_C",
    "Desc_FluidCanister_C",
    "Desc_GasTank_C",
    "Desc_PetroleumCoke_C",
    "Desc_LiquidFuel_C",
    "Desc_HeavyOilResidue_C",
}
converter_exception = "Desc_Diamond_C"

# Extracting the acceptable recipes (currently base game no alternate) with filter to remove unnecessary items
# Filter acceptable recipes
for recipe in data["recipes"].values():
    produced_in = recipe.get("producedIn", [])
    ingredients = recipe.get("ingredients", [])
    products = recipe.get("products", [])

    # Skip if any excluded ingredient is used
    if any(ing["item"] in excluded_ingredients for ing in ingredients):
        continue

    # Skip if any excluded item is a product
    if any(prod["item"] in excluded_final_products for prod in products):
        continue

    # Filter by machine, workshop, alternates, and exceptions
    if (
        recipe.get("inMachine")
        and not recipe.get("inWorkshop")
        and not recipe.get("alternate")
        and (
            ("Desc_Packager_C" not in produced_in and "Desc_Converter_C" not in produced_in)
            or any(ing["item"] == converter_exception for ing in ingredients)
        )
    ):
        for ing in ingredients:
            for prod in products:
                time_sec = recipe["time"]
                amount = ing["amount"]
                rate = (amount / time_sec) * 60  # items per minute
                G.add_edge(
                    ing["item"],
                    prod["item"],
                    amount=amount,
                    time=time_sec,
                    rate=rate,
                )

# Get the terminal and entry nodes
terminal_nodes = [node for node in G.nodes if G.out_degree(node) == 0]
entry_nodes = [node for node in G.nodes if G.in_degree(node) == 0]
print("----------------------------Tmans Satisfacotry optimiser------------------------------")
# Print the entry and exit nodes
print(f"Entry Nodes: {entry_nodes}")
print("________________________________________")
print(f"\nTerminal Nodes: {terminal_nodes}")
print("----------------------------------------------------------")


# Get all the intermediate nodes and terminal
internal_nodes = [
    node for node in G.nodes
    if G.in_degree(node) > 0
]

# See if any recipes are not visited when pathing from entry to terminal nodes (if returns set then all are visted)
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
print("---------------------------OPTIMISATION SECTION SOLVING-------------------------------")


prob = pl.LpProblem("Production_Optimization", pl.LpMaximize)
# Create a linear programming problem for every node
part_recipe = {
    node: pl.LpVariable(f"var_{node}", lowBound=0)
    for node in internal_nodes
}

# Generate the opjective function based on the final product nodes (stuff that leads no further)
prob += pl.lpSum([part_recipe[node] for node in terminal_nodes if node in part_recipe])

print("Objective function:")
print(prob.objective)


inspect_node("Desc_IronIngot_C")  # Example node to inspect
print("----------------------------------------------------------")
# Flow rate constraints of input items
for raw_mat in entry_nodes:
    # Gather all internal recipe nodes that consume this raw material
    consumption_terms = []

    for succ in G.successors(raw_mat):
        # 'succ' here is a recipe node that consumes 'raw_mat'
        if succ in part_recipe:  # make sure it's an internal node with a variable
            rate = G[raw_mat][succ].get("rate", 0)
            consumption_terms.append(part_recipe[succ] * rate)

    if consumption_terms:
        prob += pl.lpSum(consumption_terms) <= input_limit, f"Input_Limit_{raw_mat}"


for item in intermediate_nodes:  # nodes that have both in_degree and out_degree > 0
    # Production terms: sum over all recipes producing this item
    production_terms = []
    for pred in G.predecessors(item):
        if pred in part_recipe:
            rate = G[pred][item].get("rate", 0)
            production_terms.append(part_recipe[pred] * rate)
    
    # Consumption terms: sum over all recipes consuming this item
    consumption_terms = []
    for succ in G.successors(item):
        if succ in part_recipe:
            rate = G[item][succ].get("rate", 0)
            consumption_terms.append(part_recipe[succ] * rate)


    if production_terms and consumption_terms:
        prob += pl.lpSum(production_terms) >= pl.lpSum(consumption_terms) + stockpile, f"Balance_{item}"

# for name, constraint in prob.constraints.items():
#     print(f"{name}: {constraint}")

# Solve the problem
status = prob.solve()
# Print the results
print("\n--- Optimization Results ---")
for node, var in part_recipe.items():
    print(f"{node}: {var.varValue} machines")
print("Status:", pl.LpStatus[status])




