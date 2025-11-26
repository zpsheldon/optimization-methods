import numpy as np
import pandas as pd
from gurobipy import *

# load data
dps = pd.read_excel("data.xlsx", sheet_name="DPs")
fcs = pd.read_excel("data.xlsx", sheet_name="FCs")

# data
nDPs = 20
nFCs = 10
nOpenFCs = [1, 2, 3]
nYearsOpen = [6, 5, 9]
distances = np.array([[0]*nFCs for i in range(nDPs)])
for i,dp_row in dps.iterrows():
    for j,fc_row in fcs.iterrows():
        distances[i][j] = np.linalg.norm(np.array(fc_row.x, fc_row.y) - np.array(dp_row.x, dp_row.y))

# init model
model = Model("fulfillment-center-model")

# decision variables
xs = np.array([[0]*len(nOpenFCs) for j in range(nFCs)],dtype="object")
for j in range(nFCs):
    for k in range(len(nOpenFCs)):
        curr_var = model.addVar(vtype=GRB.BINARY, name=f"x_FC{j+1}_k{k+1}")
        xs[j][k] = curr_var
ys = np.array([[[0]*nFCs]*nDPs for i in range(len(nOpenFCs))],dtype="object")
for k in range(len(nOpenFCs)):
    for i in range(nDPs):
        for j in range(nFCs):
            curr_var = model.addVar(vtype=GRB.BINARY, name=f"y_k{k+1}_DP{i+1}_FC{j+1}")
            ys[k][i][j] = curr_var
model.update()

# objective function
objExpr = LinExpr()
for t,k in zip(nYearsOpen, range(len(nOpenFCs))):
    for i in range(nDPs):
        for j in range(nFCs):
            objExpr += t * distances[i][j] * ys[k][i][j]
model.setObjective(objExpr, GRB.MINIMIZE)

#### constraints
# each DP is served by 1 FC
for k in range(len(nOpenFCs)):
    for i in range(nDPs):
        constExpr = LinExpr()
        for j in range(nFCs):
            curr_y = ys[k][i][j]
            constExpr += 1.0 * curr_y
        model.addLConstr(lhs=constExpr, sense=GRB.EQUAL, rhs=1, name=f"singleDP{i+1}_k{k+1}")

# FC serving a DP must be one of the FC's chosen to be active
for k in range(len(nOpenFCs)):
    for i in range(nDPs):
        for j in range(nFCs):
            curr_y = ys[k][i][j]
            curr_x = xs[j][k]
            constExpr = LinExpr()
            constExpr += 1.0 * curr_x
            constExpr -= 1.0 * curr_y
            model.addLConstr(lhs=constExpr, sense=GRB.GREATER_EQUAL, rhs=0, name=f"equality-k{k+1}_DP{i+1}_FC{j+1}")

# set number of active FCs per year based on data
for k_idx,k in enumerate(nOpenFCs):
    constExpr = LinExpr()
    for j in range(nFCs):
        curr_x = xs[j][k_idx]
        constExpr += 1.0 * curr_x
    model.addLConstr(lhs=constExpr, sense=GRB.EQUAL, rhs=k, name=f"numActiveFCs-k{k}")

# once an FC stays open, it remains open
for j in range(nFCs):
    for k in range(1, len(nOpenFCs)):
        curr_x = xs[j][k]
        prev_x = xs[j][k-1]
        constExpr = LinExpr()
        constExpr += 1.0 * curr_x
        constExpr -= 1.0 * prev_x
        model.addLConstr(lhs=constExpr, sense=GRB.GREATER_EQUAL, rhs=0, name=f"constActiveFCs-x{j+1}{k}_x{j+1}{k-1}")

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
for curVar in myVars:
    print(curVar.varName + " " + str(curVar.x))