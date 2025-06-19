import pulp as pl

# Create problem
prob = pl.LpProblem("Maximize_Reinforced_Plates", pl.LpMaximize)

input_limit = 480  # Example input limit for first step processed materials.

# === Machine variables (machines running per minute) ===
RPlate = pl.LpVariable("ReinforcedPlates", lowBound=0)
plate = pl.LpVariable("IronPlates", lowBound=0)
wire = pl.LpVariable("Wire", lowBound=0)
rod = pl.LpVariable("IronRods", lowBound=0)
con = pl.LpVariable("concrete", lowBound=0)  # directly used
mod = pl.LpVariable("ModularFrames", lowBound=0)
Enc = pl.LpVariable("Encased", lowBound=0)
Hea = pl.LpVariable("HeavyMod", lowBound=0)
beam = pl.LpVariable("SteelBeams", lowBound=0)
pipe = pl.LpVariable("SteelPipes", lowBound=0)

# === Objective ===
prob += Hea
# === Objective: Maximize Heavy Modular Frames + weighted surplus ===
# Surplus weights are small to prioritize Hea but still allow surplus production.


# === Input limits for raw materials ===
prob += 30 * plate + 15 * rod <= input_limit  # Iron Ingots per minute
prob += 15 * wire <= input_limit              # Copper Ingots per minute
prob += 20.625 * Hea + 36 * Enc <= input_limit  # Concrete
prob += 60 * beam + 30 * pipe <= input_limit  # Steel Ingots per minute

# === Intermediate constraints (no explicit surplus variables) ===
SURPLUS = 0  # fixed surplus per item per minute

# === Intermediate constraints with minimum surplus ===
# Generic form : Item Production rate from previous step >= sum(reqruired rate * next recipe) + surplus 
prob += 15 * rod >= 12 * mod + SURPLUS
prob += 20 * plate >= 18.75 * RPlate + SURPLUS
prob += 30 * wire >= 37.5 * RPlate + SURPLUS
prob += 5.625 * RPlate >= 3 * mod + SURPLUS
prob += 2 * mod >= 7.5 * Hea + SURPLUS
prob += 6 * Enc >= 9.375 * Hea + SURPLUS
prob += 20 * beam >= 18 * Enc + SURPLUS
prob += 20 * pipe >= 33.75 * Hea + SURPLUS


# === Solve ===
prob.solve()

# === Output ===
Hea_m = pl.value(Hea)
HeavyRate = 2.8125 * Hea_m  # Heavy Modular Frames produced per minute

print("\n--- All Machine Variable Results ---")
for var in prob.variables():
    print(f"{var.name}: {var.varValue:.4f}")

print(f"\nStatus: {pl.LpStatus[prob.status]}")
print(f"Heavy Modular Frames produced per minute: {HeavyRate:.4f}")

# === Surplus Output Rate Calculation ===
rod_surplus_rate = 15 * rod.varValue - 12 * mod.varValue
plate_surplus_rate = 20 * plate.varValue - 18.75 * RPlate.varValue
wire_surplus_rate = 30 * wire.varValue - 37.5 * RPlate.varValue
RPlate_surplus_rate = 5.625 * RPlate.varValue - 3 * mod.varValue
mod_surplus_rate = 2 * mod.varValue - 7.5 * Hea.varValue
Enc_surplus_rate = 6 * Enc.varValue - 9.375 * Hea.varValue
beam_surplus_rate = 20 * beam.varValue - 18 * Enc.varValue
pipe_surplus_rate = 20 * pipe.varValue - 33.75 * Hea.varValue

print("\n--- Surplus Production Rates (items/min not used by next step) ---")
print(f"Rod surplus rate:         {rod_surplus_rate:.2f}")
print(f"Plate surplus rate:       {plate_surplus_rate:.2f}")
print(f"Wire surplus rate:        {wire_surplus_rate:.2f}")
print(f"Reinforced Plate surplus: {RPlate_surplus_rate:.2f}")
print(f"Modular Frame surplus:    {mod_surplus_rate:.2f}")
print(f"Encased Beam surplus:     {Enc_surplus_rate:.2f}")
print(f"Steel Beam surplus:       {beam_surplus_rate:.2f}")
print(f"Steel Pipe surplus:       {pipe_surplus_rate:.2f}")

# === Calculate raw resource usage ===
iron_ingots_used = 30 * plate.varValue + 15 * rod.varValue
copper_ingots_used = 15 * wire.varValue
concrete_used = 20.625 * Hea.varValue + 36 * Enc.varValue
steel_ingots_used = 60 * beam.varValue + 30 * pipe.varValue

print("\n--- Resource Usage ---")
print(f"Iron Ingots used:    {iron_ingots_used:.2f} / {input_limit}")
print(f"Copper Ingots used:  {copper_ingots_used:.2f} / {input_limit}")
print(f"Concrete used:       {concrete_used:.2f} / {input_limit}")
print(f"Steel Ingots used:   {steel_ingots_used:.2f} / {input_limit}")


# Information required for setting it up 
# Recipe: Name 
# Ingredient items + rate (units/min)
# output + rate (units/min)
