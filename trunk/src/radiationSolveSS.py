## @package src.radiationSolveSS
#  Provides functions to solve the steady-state S-2 equations. Also provides
#  means of employing solver to be used in temporal discretizations.

import math
import numpy as np
from numpy import array

from mesh import Mesh
from utilityFunctions import getIndex
from radUtilities import mu, computeScalarFlux
import globalConstants as GC
from radiation import Radiation

## Steady-state solve function for the S-2 equations.
#
#  @param[in] mesh     a mesh object
#  @param[in] cross_x  list of cross sections for each element, stored as tuple
#                      for each cell.
#  @param[in] Q        \f$\tilde{\mathcal{Q}}\f$ as defined in documentation
#                      for time-dependent solvers. This is passed in as a vector
#                      with the same global numbering as $\Psi$ unknowns.
#  @param[in] diag_add_term       \f$\alpha\f$ as defined in documentation for
#                                 time-dependent solvers
#  @param[in] implicit_scale      \f$\beta\f$ as defined in documentation for
#                                 time-dependent solvers
#  @param[in] bound_curr_lt       left  boundary current data, \f$j^+\f$
#  @param[in] bound_curr_rt       right boundary current data, \f$j^-\f$
#  @param[in] bound_flux_left     left  boundary psi
#  @param[in] bound_flux_right    right boundary psi
#
#  @return 
#          -# \f$\Psi^+\f$, angular flux in plus directions multiplied by \f$2\pi\f$
#          -# \f$\Psi^-\f$, angular flux in minus directions multiplied by \f$2\pi\f$
#          -# \f$\mathcal{E}\f$: radiation energy
#          -# \f$\mathcal{F}\f$: radiation flux
#
def radiationSolveSS(mesh, cross_x, Q, diag_add_term=0.0, implicit_scale=1.0,
    bound_curr_lt=0.0, bound_curr_rt=0.0,
    bc_psi_left = None, bc_psi_right = None):

    # abbreviation for the scale term
    beta = implicit_scale

    # compute boundary fluxes based on incoming currents if there is no specified
    # fluxes.  If fluxes are specified, they will overwrite current value. Default 
    # is zero current
    if bc_psi_left != None and bound_curr_lt != 0.0:
        raise ValueError("You cannot specify a current and boundary flux, on left")
    if bc_psi_right != None and bound_curr_rt != 0.0:
        raise ValueError("You cannot specify a current and boundary flux, on right")

    if bc_psi_left == None:
        bc_psi_left  =  bound_curr_lt / (0.5)

    if bc_psi_right == None:
        bc_psi_right = bound_curr_rt / (0.5)


    # initialize numpy arrays for system matrix and rhs
    n = 4*mesh.n_elems
    matrix = np.zeros((n, n))
    rhs    = np.zeros(n)

    # loop over interior cells
    for i in xrange(mesh.n_elems):
       # compute indices
       iprevRplus  = getIndex(i-1,"R","+") # dof i-1,R,+
       iLminus     = getIndex(i,  "L","-") # dof i,  L,-
       iLplus      = getIndex(i,  "L","+") # dof i,  L,+
       iRminus     = getIndex(i,  "R","-") # dof i,  R,-
       iRplus      = getIndex(i,  "R","+") # dof i,  R,+
       inextLminus = getIndex(i+1,"L","-") # dof i+1,L,-

       # get cell size
       h = mesh.getElement(i).dx

       # get cross sections
       cx_sL = cross_x[i][0].sig_s # Left  scattering
       cx_sR = cross_x[i][1].sig_s # Right scattering
       cx_tL = cross_x[i][0].sig_t # Left  total
       cx_tR = cross_x[i][1].sig_t # Right total

       # get sources
       QLminus = Q[iLminus] # minus direction, Left
       QLplus  = Q[iLplus]  # plus  direction, Left
       QRminus = Q[iRminus] # minus direction, Right
       QRplus  = Q[iRplus]  # plus  direction, Right

       # Left control volume, minus direction
       row = np.zeros(n)
       row[iLminus]    = -beta*mu["-"]/h + (beta*cx_tL + diag_add_term) - 0.5*beta*cx_sL
       row[iLplus]     = -0.5*beta*cx_sL
       row[iRminus]    = beta*mu["-"]/h
       matrix[iLminus] = row
       rhs[iLminus]    = QLminus
      
       # Left control volume, plus direction
       row = np.zeros(n)
       if i == 0:
          rhs[iLplus] = 2.0*beta*mu["+"]/h*bc_psi_left
       else:
          row[iprevRplus] = -2.0*beta*mu["+"]/h
       row[iLminus]    = -0.5*beta*cx_sL
       row[iLplus]     = beta*mu["+"]/h + (beta*cx_tL + diag_add_term) - 0.5*beta*cx_sL
       row[iRplus]     = beta*mu["+"]/h
       matrix[iLplus]  = row
       rhs[iLplus]    += QLplus

       # Right control volume, minus direction
       row = np.zeros(n)
       row[iLminus]     = -beta*mu["-"]/h
       row[iRminus]     = -beta*mu["-"]/h + (beta*cx_tR + diag_add_term) - 0.5*beta*cx_sR
       row[iRplus]      = -0.5*beta*cx_sR
       if i == mesh.n_elems-1:
          rhs[iRminus] = -2.0*beta*mu["-"]/h*bc_psi_right
       else:
          row[inextLminus] = 2.0*beta*mu["-"]/h
       matrix[iRminus]  = row
       rhs[iRminus]    += QRminus

       # Right control volume, plus direction
       row = np.zeros(n)
       row[iLplus]      = -beta*mu["+"]/h
       row[iRminus]     = -0.5*beta*cx_sR
       row[iRplus]      = beta*mu["+"]/h + (beta*cx_tR + diag_add_term) - 0.5*beta*cx_sR
       matrix[iRplus]   = row
       rhs[iRplus]      = QRplus

    # solve linear system
    solution = np.linalg.solve(matrix, rhs)

    #return solution
    return Radiation(solution)

