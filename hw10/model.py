import numpy as np
import pandas as pd
from gurobipy import *
import openpyxl
from openpyxl.styles import PatternFill

# load data
raw_data = pd.read_csv("raw_paper_data.csv")

# problem formulation
nPapers = raw_data.shape[0]
nRefs = raw_data.shape[1]-1
nRevsPerPaper = 3
cost_dict = {
    "yes": 1,
    "maybe": 2,
    "no": 5,
    "conflict": 100
}
cost_arr = [[cost_dict[row[f"Referee{j}"]] for j in range(1,nRefs+1)] for i,row in raw_data.iterrows()]

# init model
model = Model("paper-model")

# decision variables
all_vars = [[0 for j in range(nRefs)] for i in range(nPapers)] # paper -> ref
for p in range(nPapers):
    for r in range(nRefs):
        curr_var = model.addVar(vtype = GRB.BINARY, name = "Paper"+str(p+1) + "_Referee"+str(r+1))
        all_vars[p][r] = curr_var
sink_vars = [0 for j in range(nRefs)] # ref -> sink
for r in range(nRefs):
    curr_var = model.addVar(vtype = GRB.INTEGER, name = "Referee"+str(r+1)+"s")
    sink_vars[r] = curr_var
model.update()

# objective function
objExpr = LinExpr()
for p in range(nPapers):
    for r in range(nRefs):
        objExpr += cost_arr[p][r] * all_vars[p][r]
model.setObjective(objExpr, GRB.MINIMIZE)

#### constraints
# supply
for p in range(nPapers):
    constExpr = LinExpr()
    for r in range(nRefs):
        curr_var = all_vars[p][r]
        constExpr += 1.0 * curr_var
    model.addLConstr(lhs = constExpr, sense = GRB.EQUAL, rhs = 3, name = "supply_x"+str(p+1))
# demand
constExpr = LinExpr()
for r in range(nRefs):
    curr_var = sink_vars[r]
    constExpr += -1.0 * curr_var
model.addLConstr(lhs = constExpr, sense = GRB.EQUAL, rhs = -int(nPapers*nRevsPerPaper), name = "demand")
# intermediate
for r in range(nRefs):
    constExpr = LinExpr()
    curr_sink_var = sink_vars[r]
    constExpr += 1.0* curr_sink_var
    for p in range(nPapers):
        curr_var = all_vars[p][r]
        constExpr += -1.0 * curr_var
    model.addLConstr(lhs = constExpr, sense = GRB.EQUAL, rhs = 0, name = "intermed_"+str(r+1))

# integrate objective and constraints into the model
model.update()

# write the model in a file to make sure it is constructed correctly
model.write(filename = "output.lp")

# optimize the model
model.optimize()

# check for no optimal solution
curStatus = model.status
if curStatus in (GRB.Status.INF_OR_UNBD, GRB.Status.INFEASIBLE, GRB.Status.UNBOUNDED):
    print("Could not find the optimal solution")
    exit(1)

# print optimal objective and optimal solution and write output to file
print( "\nOptimal Objective: " + str(model.ObjVal))
print( "\nOptimal Solution:" )
myVars = model.getVars()

# output data
out_data = pd.DataFrame(columns=["Paper"]+[f"Referee{i}" for i in range(1, nRefs+1)])
out_data["Paper"] = [f"Paper{i}" for i in range(1,nPapers+1)]
for i in range(nRefs):
    out_data[f"Referee{i+1}"] = [0]*nPapers

for curVar in myVars:
    print(curVar.varName + " " + str(curVar.x))
    if curVar.varName[0] == "P":
        currCombo = curVar.varName.split("_")
        p = currCombo[0]
        r = currCombo[1]
        p_num = int(p[5:])
        r_num = int(r[7:])
        out_data.iloc[p_num-1, r_num] = int(curVar.x)
        
out_data.to_csv("review_allocation.csv")