"""
Puran ADM1 Simulation Package

This package contains the code for running ADM1 simulations for anaerobic digestion modeling.
"""

__version__ = '0.1.0'

# Initialize the QSDsan components
import qsdsan
from qsdsan import sanunits as su, processes as pc, WasteStream, System
from biosteam import settings

# Create ADM1 components
cmps = pc.create_adm1_cmps()

# Set the thermo object
settings.set_thermo(cmps)