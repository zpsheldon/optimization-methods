import gurobipy as gp
from gurobipy import GRB
import numpy as np
from gurobipy import *


# INITIALIZE MODEL #
m = gp.Model("ExpressAirCargo")

# DATA # 
# Airports: A=0, B=1, C=2
airports = ['A', 'B', 'C']
days = [0, 1, 2, 3, 4]  # Monday to Friday (0-indexed)

# Cargo demand (Table 1)
cargo_demand = {
    (0, 1, 0): 100,  # A->B, Monday
    (0, 1, 1): 200,  # A->B, Tuesday
    (0, 1, 2): 100,  # A->B, Wednesday
    (0, 1, 3): 400,  # A->B, Thursday
    (0, 1, 4): 300,  # A->B, Friday
    (0, 2, 0): 50,   # A->C, all days
    (0, 2, 1): 50,
    (0, 2, 2): 50,
    (0, 2, 3): 50,
    (0, 2, 4): 50,
    (1, 0, 0): 25,   # B->A, all days
    (1, 0, 1): 25,
    (1, 0, 2): 25,
    (1, 0, 3): 25,
    (1, 0, 4): 25,
    (1, 2, 0): 25,   # B->C, all days
    (1, 2, 1): 25,
    (1, 2, 2): 25,
    (1, 2, 3): 25,
    (1, 2, 4): 25,
    (2, 0, 0): 40,   # C->A, all days
    (2, 0, 1): 40,
    (2, 0, 2): 40,
    (2, 0, 3): 40,
    (2, 0, 4): 40,
    (2, 1, 0): 400,  # C->B, Monday
    (2, 1, 1): 200,  # C->B, Tuesday
    (2, 1, 2): 300,  # C->B, Wednesday
    (2, 1, 3): 200,  # C->B, Thursday
    (2, 1, 4): 400,  # C->B, Friday
}

# Empty repositioning costs (Figure 1)
reposition_cost = {
    (0, 1): 7,   # A->B
    (0, 2): 6,   # A->C
    (1, 0): 7,   # B->A
    (1, 2): 3,   # B->C
    (2, 0): 6,   # C->A
    (2, 1): 3,   # C->B
}

# Holding cost per aircraft load per day
holding_cost = 10

# Total fleet size
total_fleet = 1200

# DECISION VARIABLES #
# X_ijt: cargo inventory (backlog) at airport i for destination j on day t
X = {}
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                X[i,j,t] = m.addVar(vtype=GRB.INTEGER, name=f"X_{i}_{j}_{t}")

# W_ijt: # of planes (with cargo) from airport i->j on day t
W = {}
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                W[i,j,t] = m.addVar(vtype=GRB.INTEGER, name=f"W_{i}_{j}_{t}")

# U_ijt: # of planes repositioned (empty) from airport i->j on day t
U = {}
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                U[i,j,t] = m.addVar(vtype=GRB.INTEGER, name=f"U_{i}_{j}_{t}")

# A_it: # of aircraft at airport i at start of day t (day 0..5, where day 5 is next Monday)
A = {}
for i in range(3):
    for t in range(6):
        A[i,t] = m.addVar(vtype=GRB.INTEGER, name=f"A_{i}_{t}")


############################################################
# OBJECTIVE FUNCTION
# Min: repositioning cost + holding cost
m.update()

objExpr = LinExpr()

# Repositioning costs
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j and (i, j) in reposition_cost:
                objExpr += reposition_cost[i, j] * U[i,j,t]

# Holding costs
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                objExpr += holding_cost * X[i,j,t]

m.setObjective(objExpr, GRB.MINIMIZE)

#  CONSTRAINTS 

# Fleet size constraint: total aircraft at start of Monday = 1200
sourceExpr = LinExpr()
for i in range(3):
    sourceExpr += A[i,0]
m.addConstr(sourceExpr == total_fleet, "fleet_size")

for i in range(3):
    initialExpr = LinExpr()
    
    # Aircraft going out from airport i on day 0
    for j in range(3):
        if i != j:
            initialExpr += W[i,j,0] + U[i,j,0]
    
    m.addConstr(initialExpr <= A[i,0], f"initial_availability_{i}")


# Aircraft flow balance constraint
# For all days t in {0,1,2,3,4} and all airports i
for t in range(5):
    for i in range(3):
        aircraftExpr = LinExpr()
        
        # A[i,t+1] = A[i,t] - (outgoing loaded + empty) + (incoming loaded + empty)
        # Rearranged: A[i,t+1] - A[i,t] + outgoing - incoming = 0
        
        aircraftExpr += A[i,t+1]
        aircraftExpr -= A[i,t]
        
        # Subtract outgoing flights
        for j in range(3):
            if i != j:
                aircraftExpr -= W[i,j,t] + U[i,j,t]
        
        # Add incoming flights
        for j in range(3):
            if i != j:
                aircraftExpr += W[j,i,t] + U[j,i,t]
        
        m.addConstr(aircraftExpr == 0, f"aircraft_flow_{i}_{t}")

# Weekly cycle constraint: aircraft at end of Friday = aircraft at start of Monday
for i in range(3):
    cycleExpr = LinExpr()
    cycleExpr += A[i,5]
    cycleExpr -= A[i,0]
    m.addConstr(cycleExpr == 0, f"weekly_cycle_{i}")

# # Cargo flow balance constraint
# # For all routes (i,j) and all days t
# for i in range(3):
#     for j in range(3):
#         for t in range(5):
#             if i != j:
#                 cargoExpr = LinExpr()                
#                 cargoExpr += X[i,j,t]
                
#                 prev = t - 1 if t > 0 else 4
#                 cargoExpr -= X[i,j,prev]
#                 cargoExpr += W[i,j,prev]
                
#                 demand_val = cargo_demand.get((i, j, t), 0)
#                 cargoExpr -= demand_val
                
#                 m.addConstr(cargoExpr == 0, f"cargo_flow_{i}_{j}_{t}")

for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                cargoExpr = LinExpr()
                cargoExpr += X[i,j,t]  # Inventory at END of day t
                
                # Previous day's inventory
                prev = t - 1 if t > 0 else 4
                cargoExpr -= X[i,j,prev]
                
                # Add demand arriving on day t
                demand_val = cargo_demand.get((i, j, t), 0)
                cargoExpr += demand_val
                
                # Subtract flights departing on day t (deplete inventory)
                cargoExpr -= W[i,j,t]  # ← Should be current day t
                
                m.addConstr(cargoExpr == 0, f"cargo_flow_{i}_{j}_{t}")

for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                m.addConstr(X[i,j,t] >= 0, f"nonnegativity_{i}_{j}_{t}")

# Loaded flights cannot exceed cargo inventory
# W[i,j,t] <= X[i,j,t]
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                loadExpr = LinExpr()
                loadExpr += W[i,j,t]
                loadExpr -= X[i,j,t]
                m.addConstr(loadExpr <= 0, f"load_limit_{i}_{j}_{t}")

#  OPTIMIZE 
m.optimize()

#  RESULTS 
print("\n Results:")

if m.status == GRB.OPTIMAL:
    print(f"\nOptimal Objective Value: {m.objVal:.2f}")
    
    # Initial aircraft distribution
    print("\ninitial dist. of aircrafts (A[i,0]):")
    for i in range(3):
        print(f"Airport {airports[i]}: {int(A[i,0].X)} aircraft")
    
    print("\n\n")
    # Daily aircraft movements (with cargo)
    print("DAILY AIRCRAFT MOVEMENTS (with cargo):")
    for t in range(5):
        print(f"\nDay {t}:")
        for i in range(3):
            for j in range(3):
                if i != j and W[i, j, t].X > 0:
                    print(f"  {airports[i]}->{airports[j]}: {int(W[i, j, t].X)} aircraft")
    
    print("\n\n")
    # Daily repositioning movements (empty)
    print("repositioning movements each day (empty):")
    for t in range(5):
        print(f"\nDay {t}:")
        for i in range(3):
            for j in range(3):
                if i != j and U[i, j, t].X > 0:
                    print(f"  {airports[i]}->{airports[j]}: {int(U[i, j, t].X)} aircraft")
    
    print("\n\n")
    # Daily cargo inventory
    print("cargo inventory daily (X_ijt):")
    for t in range(5):
        print(f"\nDay {t}:")
        for i in range(3):
            for j in range(3):
                if i != j and X[i, j, t].X > 0:
                    print(f"  {airports[i]}->{airports[j]}: {int(X[i, j, t].X)} loads")
    
    m.write("project_model.lp")
else:
    print("Optimization failed or was infeasible.")
    print(f"Status: {m.status}")