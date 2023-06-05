# grid.py: functions & parameters related to numerical grids
# functions: Automatic loop output, output C code needed for gridfunction memory I/O, gridfunction registration

# Author: Zachariah B. Etienne
#         zachetie **at** gmail **dot* com

import grid as gri      # NRPy+: gridding
import os

####################
# TO BE DEPRECATED
def output__gridfunction_defines_h__return_gf_lists(outdir):
    with open(os.path.join(outdir, "gridfunction_defines.h"), "w") as file:
        file.write("/* This file is automatically generated by NRPy+. Do not edit. */\n\n")
        file.write(gri.gridfunction_defines())
    return gri.gridfunction_lists()
####################