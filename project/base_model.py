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
# X_ijt: amount of cargo sent from airport i to destination j on day t after
# accounting for previous day's leftover cargo and incoming cargo
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
        for t in range(1,5):
            if i == j:
                continue
            objExpr += holding_cost * (X[i,j,t-1] - W[i,j,t-1])
for i in range(3):
    for j in range(3):
        if i == j:
            continue
        objExpr += holding_cost * (X[i,j,4] - W[i,j,4])

m.setObjective(objExpr, GRB.MINIMIZE)

############################################################

#  CONSTRAINTS 

# Fleet size constraint
for t in range(5):
    initExpr = LinExpr()
    for i in range(3):
        for j in range(3):
            if i==j:
                continue
            initExpr += W[i,j,t] + U[i,j,t]
    m.addLConstr(initExpr == total_fleet, f"total_fleet_size_{t}")

# Aircraft flow balance constraint
# For days t in {1,2,3,4} and all airports i
for t in range(1, 5):
    for i in range(3):
        aircraftExpr = LinExpr()
        for j in range(3):
            if i==j:
                continue
            
            aircraftExpr +=  W[i,j,t] + U[i,j,t]
            aircraftExpr -= (W[j,i,t-1] + U[j,i,t-1])
            
        m.addLConstr(aircraftExpr == 0, f"aircraft_flow_{i}_{t}")

# for each airport, friday --> monday
for i in range(3):
    wkndAircraftExpr = LinExpr()
    for j in range(3):
        if i==j:
            continue
        wkndAircraftExpr += W[i,j,0] + U[i,j,0]
        wkndAircraftExpr -= (W[j,i,4] + U[j,i,4])
    m.addLConstr(wkndAircraftExpr == 0, f"weekend_aircraft_flow_{i}_0")

# Cargo flow balance constraint -- days 2-5
for t in range(1,5):
    for i in range(3):
        for j in range(3):
            if i==j:
                continue
            cargoExpr = LinExpr()
            cargoExpr += X[i,j,t]
            cargoExpr -= X[i,j,t-1]
            cargoExpr += W[i,j,t-1]
            cargoExpr -= cargo_demand.get((i,j,t))
            m.addLConstr(cargoExpr==0, f"cargo_flow_{i}_{j}_{t}")
# cargo flow balance -- day 1
for i in range(3):
    for j in range(3):
        if i==j:
            continue
        cargoExpr = LinExpr()
        cargoExpr += X[i,j,0]
        cargoExpr -= X[i,j,4]
        cargoExpr += W[i,j,4]
        cargoExpr -= cargo_demand.get((i,j,0))
        m.addLConstr(cargoExpr==0, f"cargo_flow_{i}_{j}_0")

# Loaded flights cannot exceed cargo inventory
# W[i,j,t] <= X[i,j,t]
for i in range(3):
    for j in range(3):
        for t in range(5):
            if i != j:
                loadExpr = LinExpr()
                loadExpr += W[i,j,t]
                loadExpr -= X[i,j,t]
                m.addLConstr(loadExpr <= 0, f"load_limit_{i}_{j}_{t}")

#  OPTIMIZE 
m.optimize()

#  RESULTS 
print("\n Results:")

if m.status == GRB.OPTIMAL:
    print(f"\nOptimal Objective Value: {m.objVal:.2f}")
    
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
    
    print("\n\n")
    # Daily cargo leftover
    print("cargo leftover daily:")
    print("\nDay 0:")
    for i in range(3):
        for j in range(3):
            if i!=j and (X[i,j,4].X - W[i,j,4].X) > 0:
                print(f"  {airports[i]}->{airports[j]}: {int(X[i, j,4].X - W[i,j,4].X)} loads") 
    for t in range(1,5):
        print(f"\nDay {t}:")
        for i in range(3):
            for j in range(3):
                if i!= j and (X[i,j,t-1].X - W[i,j,t-1].X) > 0:
                    print(f"  {airports[i]}->{airports[j]}: {int(X[i, j,t-1].X - W[i,j,t-1].X)} loads")  
else:
    print("Optimization failed or was infeasible.")
    print(f"Status: {m.status}")

m.write("project_model.lp")