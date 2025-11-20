Minimize
    1175 xp1w1 + 1580 xp1w2 + 1430 xp2w1 + 1700 xp2w2 + 1370 xw1r1 + 1505 xw1r2 + 1490 xw1r3 + 1190 xw2r1 + 1210 xw2r2 + 1240 xw2r3
Subject To
    p1SupplyConst: 1175 xp1w1 + 1580 xp1w2 = 600
    p2SupplyConst: 1430 xp2w1 + 1700 xp2w2 = 900
    r1DemandConst: -1370 xw1r1 - 1190 xw2r1 = -450
    r2DemandConst: -1505 xw1r2 - 1210 xw2r2 = -600
    r3DemandConst: -1490 xw1r3 - 1240 xw2r3 = -450
    w1Const: 1370 xw1r1 + 1505 xw1r2 + 1490 xw1r3 - 1175 xp1w1 - 1430 xp2w1 = 0
    w2Const: 1190 xw2r1 + 1210 xw2r2 + 1240 xw2r3 - 1580 xp1w2 - 1700 xp2w2 = 0
Bounds
    xp1w1 <= 375
    xp1w2 <= 450
    xp2w1 <= 525
    xp2w2 <= 600
    xw1r1 <= 300
    xw1r2 <= 450
    xw1r3 <= 300
    xw2r1 <= 375
    xw2r2 <= 450
    xw2r3 <= 225
End