import matplotlib.pyplot

# this array includes the coordinates of fulfillment centers
# there are 10 fulfillment center locations
# for each fulfillment center, we keep x and y coordinates
nofcs = 10
fcs = [ 0 for j in range ( nofcs ) ]
fcs[0] = [60 , 15]
fcs[1] = [26 , 36]
fcs[2] = [73 , 34]
fcs[3] = [57 , 54]
fcs[4] = [18 , 19]
fcs[5] = [11 , 1]
fcs[6] = [60 , 77]
fcs[7] = [68 , 44]
fcs[8] = [97 , 65]
fcs[9] = [4 , 79]

# this array includes the coordinates of demand points
# for each demand point, we keep x and y coordinates
# for this example, there are 20 demand points
nodps = 20
dps = [ 0 for j in range ( nodps ) ]
dps[0] = [25 , 75]
dps[1] = [49 , 7]
dps[2] = [17 , 8]
dps[3] = [12 , 84]
dps[4] = [3 , 83]
dps[5] = [57 , 5]
dps[6] = [46 , 39]
dps[7] = [83 , 89]
dps[8] = [78 , 96]
dps[9] = [27 , 44]
dps[10] = [64 , 16]
dps[11] = [52 , 86]
dps[12] = [57 , 72]
dps[13] = [33 , 55]
dps[14] = [66 , 47]
dps[15] = [25 , 28]
dps[16] = [9 , 97]
dps[17] = [85 , 87]
dps[18] = [98 , 3]
dps[19] = [19 , 97]

# this array includes which fulfillment center each demand point is connected to
# for this example, dem pnt 0 is connected to full cen 1, but dem pnt 8 is connected to full cen 6
assgns = [ 0 for j in range ( nodps ) ]
assgns[0] = 3
assgns[1] = 3
assgns[2] = 3
assgns[3] = 3
assgns[4] = 3
assgns[5] = 3
assgns[6] = 3
assgns[7] = 3
assgns[8] = 3
assgns[9] = 3
assgns[10] = 3
assgns[11] = 3
assgns[12] = 3
assgns[13] = 3
assgns[14] = 3
assgns[15] = 3
assgns[16] = 3
assgns[17] = 3
assgns[18] = 3
assgns[19] = 3

for fc in range( nofcs ):
    matplotlib.pyplot.plot( fcs[ fc ][ 0 ]  , fcs[ fc ][ 1 ] , 'ro' , color = "green" , lw = 9)

for dp in range( nodps ):
    matplotlib.pyplot.plot( dps[ dp ][ 0 ]  , dps[ dp ][ 1 ] , 'ro' , color = "red" , lw = 9)

for dp in range( nodps ):
    dpx = dps[ dp ][ 0 ]
    dpy = dps[ dp ][ 1 ]
    fcx = fcs[ assgns[ dp ] ][ 0 ]
    fcy = fcs[ assgns[ dp ] ][ 1 ]
    matplotlib.pyplot.plot( [ dpx , fcx ], [ dpy , fcy ]  , color = "black"  , ls = "--")

matplotlib.pyplot.title("k = 1 | t = [1, 2, 3, 4, 5, 6]")
matplotlib.pyplot.show()