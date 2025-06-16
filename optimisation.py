import pulp as pl

# Create problem
prob = pl.LpProblem("Maximize_Reinforced_Plates", pl.LpMaximize)

# Variables
x = pl.LpVariable("ReinforcedPlates", lowBound=0)  # Number of RP/min
p = pl.LpVariable("IronPlates", lowBound=0)        # Number of IP recipes/min
w = pl.LpVariable("Wire", lowBound=0)              # Number of Wire recipes/min
r = pl.LpVariable("IronRods", lowBound=0)          # Number of IR recipes/min)
# Objective
prob += x

stockpile = 10 # amount of stockpile per minute for each resource 

# Constraints
prob += 30*p + 15*r <= 480            # Iron ingot limit
prob += 15*w <= 480            # Copper ingot limit
prob += 18.75*x + stockpile <= 20*p   # Plate consumption + stockpile
prob += 37.5*x + stockpile <= 30*w    # Wire consumption + stockpile

# Solve
prob.solve()

# Results
reinforced_plates = pl.value(x)
iron_plate_recipes = pl.value(p)
wire_recipes = pl.value(w)

print(f"\n== Optimal Output ==")
print(f"Reinforced Plates/min: {reinforced_plates:.2f}")
print(f"Iron Plate machines (20/min each): {iron_plate_recipes:.2f}")
print(f"Wire machines (30/min each): {wire_recipes:.2f}")

# Machine and Rate Calculations
iron_ingots_used = 30 * iron_plate_recipes
copper_ingots_used = 15 * wire_recipes
plates_produced = 20 * iron_plate_recipes
wire_produced = 30 * wire_recipes

plates_used = 18.75 * reinforced_plates
wire_used = 37.5 * reinforced_plates

print(f"\n== Resource Usage ==")
print(f"Iron Ingots used/min: {iron_ingots_used:.2f} / 480")
print(f"Copper Ingots used/min: {copper_ingots_used:.2f} / 480")

print(f"\n== Material Flow ==")
print(f"Plates produced: {plates_produced:.2f} → used: {plates_used:.2f} → stockpile: {plates_produced - plates_used:.2f}")
print(f"Wire produced:   {wire_produced:.2f} → used: {wire_used:.2f} → stockpile: {wire_produced - wire_used:.2f}")
