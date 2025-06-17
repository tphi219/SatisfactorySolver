import pulp as pl

# Create problem
prob = pl.LpProblem("Maximize_Reinforced_Plates", pl.LpMaximize)


# === Machine variables (machines running per minute) ===
x = pl.LpVariable("ReinforcedPlates", lowBound=0)
p = pl.LpVariable("IronPlates", lowBound=0)
w = pl.LpVariable("Wire", lowBound=0)
r = pl.LpVariable("IronRods", lowBound=0)
s = pl.LpVariable("CopperSheets", lowBound=0)
m = pl.LpVariable("ModularFrames", lowBound=0)

# === Usage variables (used in other recipes) ===
x_used = pl.LpVariable("ReinforcedPlates_Used", lowBound=0)
r_used = pl.LpVariable("IronRods_Used", lowBound=0)
p_used = pl.LpVariable("IronPlates_Used", lowBound=0)
w_used = pl.LpVariable("Wire_Used", lowBound=0)
s_used = pl.LpVariable("CopperSheets_Used", lowBound=0)

# === Stockpile rate (units/min) ===
stockpile = 10

# === Objective ===
prob += m  # Maximize Modular Frames produced per minute

# Current plan for project: 
# use the page rank weighting for the final termainl products to bias which is which in the objective function
# every node will have a required stockpile of atm 10 but this may have to be reduced for further levels i.e maybe scale by importnace for player to 
# be able to build with it (count instances for building recipes as reference normallised )

# === Input constraints (raw material limits) ===
prob += 30*p + 15*r <= 480     # Iron Ingots per minute
prob += 15*w + 20*s <= 480     # Copper Ingots per minute

# === Internal recipe constraints ===

# 1. Reinforced Plates require Iron Plates and Wire
prob += p_used == 18.75 * x
prob += w_used == 37.5 * x
prob += 20 * p >= p_used + stockpile
prob += 30 * w >= w_used + stockpile

# 2. Modular Frames require Reinforced Plates and Iron Rods
prob += x_used == 3 * m
prob += r_used == 12 * m
prob += 5.63 * x >= x_used + stockpile
prob += 15 * r >= r_used + stockpile

# 3. Copper Sheets (no usage in this chain, just stockpile)
prob += 10 * s >= stockpile
# Solve
prob.solve()

# Results are the number of machines needed for
reinforced_plates_m = pl.value(x)
iron_plate_m = pl.value(p)
wire_m = pl.value(w)
iron_rod_m = pl.value(r)
copper_sheet_m = pl.value(s)
modular_frames_m = pl.value(m)


print(f"\n== Machine Count ==")
print(f"Reinforced Plates machines: {reinforced_plates_m:.2f}")
print(f"Iron Plate machines (20/min each): {iron_plate_m:.2f}")
print(f"Wire machines (30/min each): {wire_m:.2f}")
print(f"Iron Rod machines (15/min each): {iron_rod_m:.2f}")
print(f"Copper Sheet machines (10/min each): {copper_sheet_m:.2f}")
print(f"Modular Frames machines: {modular_frames_m:.2f}")

#Rate Calculations
reinforced_plates_produced = 5.63 * reinforced_plates_m
iron_ingots_used = 30 * iron_plate_m + 15 * iron_rod_m
copper_ingots_used = 15 * wire_m + 20 * copper_sheet_m
plates_produced = 20 * iron_plate_m
wire_produced = 30 * wire_m
iron_rod_produced = 15 * iron_rod_m
copper_sheet_produced = 10 * copper_sheet_m
modular_frames_produced = 2 * modular_frames_m  



# Used in next step 
plates_used = 18.75 * reinforced_plates_m
wire_used = 37.5 * reinforced_plates_m
iron_rod_used = 12 * iron_rod_m  
reinforced_plates_used = 3 * modular_frames_m 
copper_sheet_used = 0 * copper_sheet_m  # Not used in this calculation
modular_frames_used = 0 * modular_frames_m  # Not used in this calculation


print(f"\n== Resource Usage ==")
print(f"Iron Ingots used/min: {iron_ingots_used:.2f} / 480")
print(f"Copper Ingots used/min: {copper_ingots_used:.2f} / 480")
print(f"Reinforced Plates produced/min: {reinforced_plates_produced:.2f}")
print(f"Iron Plates produced: {plates_produced:.2f}")
print(f"Wire produced: {wire_produced:.2f}")
print(f"Iron Rods produced: {iron_rod_produced:.2f}")
print(f"Copper Sheets produced: {copper_sheet_produced:.2f}")
print(f"Modular Frames produced: {modular_frames_produced:.2f}")

print(f"\n== Material Flow (units/min) ==")
print(f"Plates produced: {plates_produced:.2f} → used: {plates_used:.2f} → stockpile: {plates_produced - plates_used:.2f}")
print(f"Wire produced:   {wire_produced:.2f} → used: {wire_used:.2f} → stockpile: {wire_produced - wire_used:.2f}")
print(f"Iron Rods produced: {iron_rod_produced:.2f} → used: {iron_rod_used:.2f} → stockpile: {iron_rod_produced - iron_rod_used:.2f}")
print(f"Copper Sheets produced: {copper_sheet_produced:.2f} → used: {copper_sheet_used:.2f} → stockpile: {copper_sheet_produced - copper_sheet_used:.2f}")
print(f"Reinforced Plates produced: {reinforced_plates_produced:.2f} → used: {reinforced_plates_used:.2f} → stockpile: {reinforced_plates_produced - reinforced_plates_used:.2f}")
print(f"Modular Frames produced: {modular_frames_produced:.2f} → used: {modular_frames_used:.2f} → stockpile: {modular_frames_produced - modular_frames_used:.2f}")