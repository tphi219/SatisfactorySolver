import json
import pulp as pl

# === Toggle: print all constraint rules ===
PRINT_RULES = False
SOLVE = True
# Load your item graph JSON
with open("item_dependency_graph.json", "r") as f:
    item_graph = json.load(f)

# Create LP problem
prob = pl.LpProblem("ProductionOptimization", pl.LpMaximize)

# Create LP variables for each item (machines producing per minute)
item_vars = {
    item: pl.LpVariable(item, lowBound=0)
    for item in item_graph
}

SURPLUS = 0  # fixed surplus amount for all items

# Set input limits for raw resources
input_limits = {
    "IronIngot": 480,
    "CopperIngot": 480,
    "Cement": 480,
    "SteelIngot": 480,
    "GoldIngot": 480,
    "RawQuartz": 480,
    "AluminumIngot": 480,
}

# === Apply input limit constraints ===
for raw_input, limit in input_limits.items():
    if raw_input in item_graph:
        used_sum = pl.lpSum(
            item_vars[dest] * rate
            for dest, rate in item_graph[raw_input].get("usedIn", {}).items()
        )
        prob += used_sum <= limit, f"InputLimit_{raw_input}"
        if PRINT_RULES:
            print(f"InputLimit_{raw_input}: {used_sum} <= {limit}")
print("////////////////////////////////////////////////////")
# === Apply flow balance constraints ===
for item, data in item_graph.items():
    production_rate = data.get("producedFrom", {}).get("rate", 0)
    consumers = data.get("usedIn", {})

    # Skip if the item isn't crafted (no production rate)
    if production_rate == 0:
        continue

    produced_sum = item_vars[item] * production_rate
    used_sum = pl.lpSum([item_vars[dest] * rate for dest, rate in consumers.items()])

    if item in input_limits:
        # Skip adding balance constraint for raw inputs with input limits
        if PRINT_RULES:
            print(f"Skipped Balance_{item}: (input limit applies instead)")
    else:
        prob += produced_sum >= used_sum + SURPLUS, f"Balance_{item}"
        if PRINT_RULES:
            print(f"Balance_{item}: {production_rate} * {item} >= " + " + ".join(
                [f"{rate} * {dest}" for dest, rate in consumers.items()]
            ) + f" + {SURPLUS}")
# === Objective: maximize one item, e.g., HeavyMod
target = "CrystalOscillator"
penalty = 0.1  # small penalty weight for non-target items

if target in item_vars:
    # prob += (
    #     item_vars[target] - penalty * pl.lpSum(var for name, var in item_vars.items() if name != target)
    # ), f"Maximize_{target}"
    prob += item_vars[target], f"Maximize_{target}"
if SOLVE:
    # Solve the problem
    status = prob.solve()
    print("\nStatus:", pl.LpStatus[status])

    if pl.LpStatus[status] == "Optimal":
        # Only print results if solution is optimal
        print("\n--- Machine Usage and Production Rate Per Item ---")
        usage_list = []
        for item, var in item_vars.items():
            if var.varValue and var.varValue > 0:
                output_rate = item_graph[item].get("producedFrom", {}).get("rate", 0)
                actual_output = var.varValue * output_rate
                usage_list.append((item, var.varValue, actual_output))

        usage_list.sort(key=lambda x: x[1], reverse=True)

        for item, machines, output in usage_list:
            print(f"{item}: {machines:.2f} machines, Output = {output:.2f} units/min")

        print("\n--- Surplus Production Per Item (units/min) ---")
        for item, data in item_graph.items():
            prod_from = data.get("producedFrom", {})
            output_rate = prod_from.get("rate", 0)

            if output_rate == 0 or item_vars[item].varValue is None:
                continue

            produced = item_vars[item].varValue * output_rate

            used = 0.0
            for dest, rate in data.get("usedIn", {}).items():
                var = item_vars.get(dest)
                if var is not None and var.varValue is not None:
                    used += var.varValue * rate

            surplus = produced - used
            if surplus > 0.01:
                print(f"{item}: Surplus = {surplus:.2f} units/min")
    else:
        print("No optimal solution found. Problem may be infeasible or unbounded.")
