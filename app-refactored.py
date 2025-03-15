"""
ADM1 Simulation Application

This is the main entry point for the ADM1 simulation application.
It includes a patch for QSDsan's WasteStream class to fix the TSS calculation
for soluble components like acetate (S_ac).
"""
import sys
import os
import functools
from chemicals.elements import molecular_weight as get_mw

# Define molecular weights
C_mw = get_mw({'C': 1})
N_mw = get_mw({'N': 1})

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the pH and alkalinity calculation module
try:
    from calculate_ph_and_alkalinity_fixed import update_ph_and_alkalinity
    CALCULATE_PH_AVAILABLE = True
except ImportError:
    try:
        from calculate_ph_and_alkalinity import update_ph_and_alkalinity
        CALCULATE_PH_AVAILABLE = True
    except ImportError:
        print("Warning: pH calculation module not found. pH and alkalinity will use default values.")
        CALCULATE_PH_AVAILABLE = False

# Import qsdsan before we apply the monkey patch
from qsdsan import WasteStream

# Store the original get_TSS method
original_get_TSS = WasteStream.get_TSS

@functools.wraps(original_get_TSS)
def patched_get_TSS(self, particle_size=None):
    """
    Return the total suspended solids concentration of the stream.
    
    This patched version ensures soluble components (particle_size='s') 
    are excluded from TSS calculations even if they have an i_mass value.
    
    Parameters
    ----------
    particle_size : str or None
        Options include 's' for soluble, 'c' for colloidal, and 'x' for
        particulate. If None, will include all particles that are not soluble.
    
    Returns
    -------
    float
        Total suspended solids concentration in mg/L.
    """
    # If a specific particle size is requested, use the standard method
    if particle_size in ('s', 'c', 'x'):
        return original_get_TSS(self, particle_size)
    
    # For default behavior (particle_size=None), calculate TSS as the sum of only 
    # particulate and colloidal components, explicitly excluding soluble components
    particulate_tss = self.composite('solids', particle_size='x')
    colloidal_tss = self.composite('solids', particle_size='c')
    
    return particulate_tss + colloidal_tss

# Apply the patch
WasteStream.get_TSS = patched_get_TSS

# Now import and run the main application
from puran_adm1.views.main_view import render_main_view

if __name__ == "__main__":
    render_main_view()
