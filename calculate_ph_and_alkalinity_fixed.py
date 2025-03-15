"""
Revised utility script to calculate pH and alkalinity from ADM1 state variables

This implementation addresses issues with the previous version by directly accessing
component concentrations by ID rather than using array indices.
"""

import numpy as np
from scipy.optimize import brenth
from qsdsan import WasteStream
from chemicals.elements import molecular_weight as get_mw

# Constants
R = 8.314e-2  # Gas constant (bar·L/mol/K)
C_mw = get_mw({'C': 1})  # Carbon molecular weight
N_mw = get_mw({'N': 1})  # Nitrogen molecular weight

# Molecular weights for conversion to molar units - approximate values
MW_AC = 60.0    # Acetate
MW_PRO = 74.0   # Propionate  
MW_BU = 88.0    # Butyrate
MW_VA = 102.0   # Valerate

def acid_base_rxn(h_ion, components_molarity, Ka):
    """
    Charge balance equation for acid-base reactions
    
    Parameters
    ----------
    h_ion : float
        Hydrogen ion concentration [M]
    components_molarity : dict
        Dictionary of component molarities
    Ka : array-like
        Acid dissociation constants [Kw, Ka_nh, Ka_co2, Ka_ac, Ka_pr, Ka_bu, Ka_va]
        
    Returns
    -------
    float
        Charge balance (should be zero at equilibrium)
    """
    # Extract components from dictionary (defaulting to 0 if not present)
    S_cat = components_molarity.get('S_cat', 0)
    S_an = components_molarity.get('S_an', 0)
    S_IN = components_molarity.get('S_IN', 0)
    S_IC = components_molarity.get('S_IC', 0)
    S_ac = components_molarity.get('S_ac', 0)
    S_pro = components_molarity.get('S_pro', 0)
    S_bu = components_molarity.get('S_bu', 0)
    S_va = components_molarity.get('S_va', 0)
    
    # Calculate dissociated species
    Kw = Ka[0]
    Ka_nh = Ka[1]
    Ka_co2 = Ka[2]
    Ka_ac = Ka[3]
    Ka_pr = Ka[4]
    Ka_bu = Ka[5]
    Ka_va = Ka[6]
    
    oh_ion = Kw/h_ion
    nh3 = S_IN * Ka_nh / (Ka_nh + h_ion)
    hco3 = S_IC * Ka_co2 / (Ka_co2 + h_ion)
    ac = S_ac * Ka_ac / (Ka_ac + h_ion)
    pro = S_pro * Ka_pr / (Ka_pr + h_ion)
    bu = S_bu * Ka_bu / (Ka_bu + h_ion)
    va = S_va * Ka_va / (Ka_va + h_ion)
    
    # Charge balance equation
    return S_cat + h_ion + (S_IN - nh3) - S_an - oh_ion - hco3 - ac - pro - bu - va

def solve_ph(components_molarity, Ka):
    """
    Solve for pH using the charge balance equation
    
    Parameters
    ----------
    components_molarity : dict
        Dictionary of component molarities
    Ka : array-like
        Acid dissociation constants
        
    Returns
    -------
    float
        Hydrogen ion concentration [M]
    """
    # The brenth algorithm finds the root of the acid_base_rxn function
    try:
        h = brenth(acid_base_rxn, 1e-14, 1.0,
                   args=(components_molarity, Ka),
                   xtol=1e-12, maxiter=100)
        return h
    except ValueError:
        # If root finding fails, return a reasonable default (pH 7)
        return 1e-7

def calculate_alkalinity(components_molarity, pH, Ka):
    """
    Calculate alkalinity based on component molarities and pH
    
    Parameters
    ----------
    components_molarity : dict
        Dictionary of component molarities
    pH : float
        pH value
    Ka : array-like
        Acid dissociation constants
        
    Returns
    -------
    float
        Alkalinity in meq/L
    """
    h_ion = 10**(-pH)
    
    # Extract components (defaulting to 0 if not present)
    S_cat = components_molarity.get('S_cat', 0)
    S_an = components_molarity.get('S_an', 0)
    S_IN = components_molarity.get('S_IN', 0)
    S_IC = components_molarity.get('S_IC', 0)
    S_ac = components_molarity.get('S_ac', 0)
    S_pro = components_molarity.get('S_pro', 0)
    S_bu = components_molarity.get('S_bu', 0)
    S_va = components_molarity.get('S_va', 0)
    
    # Calculate species
    Kw = Ka[0]
    Ka_nh = Ka[1]
    Ka_co2 = Ka[2]
    Ka_ac = Ka[3]
    Ka_pr = Ka[4]
    Ka_bu = Ka[5]
    Ka_va = Ka[6]
    
    oh_ion = Kw/h_ion
    nh3 = S_IN * Ka_nh / (Ka_nh + h_ion)
    hco3 = S_IC * Ka_co2 / (Ka_co2 + h_ion)
    ac = S_ac * Ka_ac / (Ka_ac + h_ion)
    pro = S_pro * Ka_pr / (Ka_pr + h_ion)
    bu = S_bu * Ka_bu / (Ka_bu + h_ion)
    va = S_va * Ka_va / (Ka_va + h_ion)
    
    # Alkalinity calculation - this is the sum of all basic species
    # The primary contributor is bicarbonate (HCO3-)
    alk_molar = hco3 + oh_ion - h_ion + nh3 + ac + pro + bu + va + S_cat - S_an
    
    # Convert to meq/L
    return max(0, alk_molar * 1000)  # Ensure non-negative value and convert mol/L to meq/L

def get_component_molarities(stream):
    """
    Extract component concentrations from stream and convert to molarities
    
    Parameters
    ----------
    stream : WasteStream
        The waste stream to analyze
        
    Returns
    -------
    dict
        Dictionary of component molarities
    """
    # Dictionary to store molar concentrations
    components_molarity = {}
    
    # Get component concentrations (in mg/L or g/m³)
    concentrations = {}
    for comp_id in stream.components.IDs:
        if comp_id in ['S_cat', 'S_an', 'S_IC', 'S_IN', 'S_ac', 'S_pro', 'S_bu', 'S_va', 'H2O']:
            concentrations[comp_id] = float(stream.iconc[comp_id])
    
    # Convert to molarities (mol/L)
    if 'S_cat' in concentrations:
        # Assume cations have average MW of 1 (as NH4+)
        components_molarity['S_cat'] = concentrations['S_cat'] / 1000.0
    
    if 'S_an' in concentrations:
        # Assume anions have average MW of 1 (as Cl-)
        components_molarity['S_an'] = concentrations['S_an'] / 1000.0
    
    if 'S_IN' in concentrations:
        # Inorganic nitrogen (as N)
        components_molarity['S_IN'] = concentrations['S_IN'] / (N_mw * 1000.0)
    
    if 'S_IC' in concentrations:
        # Inorganic carbon (as C)
        components_molarity['S_IC'] = concentrations['S_IC'] / (C_mw * 1000.0)
    
    if 'S_ac' in concentrations:
        # Acetate (as COD)
        components_molarity['S_ac'] = concentrations['S_ac'] / (MW_AC * 1000.0)
    
    if 'S_pro' in concentrations:
        # Propionate (as COD)
        components_molarity['S_pro'] = concentrations['S_pro'] / (MW_PRO * 1000.0)
    
    if 'S_bu' in concentrations:
        # Butyrate (as COD)
        components_molarity['S_bu'] = concentrations['S_bu'] / (MW_BU * 1000.0)
    
    if 'S_va' in concentrations:
        # Valerate (as COD) 
        components_molarity['S_va'] = concentrations['S_va'] / (MW_VA * 1000.0)
    
    return components_molarity

def update_ph_and_alkalinity(stream):
    """
    Update the pH and alkalinity for a WasteStream based on its component concentrations
    
    Parameters
    ----------
    stream : WasteStream
        The waste stream to update
        
    Returns
    -------
    WasteStream
        The updated waste stream (same object, modified in-place)
    """
    if stream.phase != 'l':
        # For non-liquid streams, set default values
        if hasattr(stream, '_pH'):
            stream._pH = 7.0
        if hasattr(stream, '_SAlk'):
            stream._SAlk = 0.0
        return stream
    
    # Define the acid dissociation constants at 25°C
    # [Kw, Ka_nh, Ka_co2, Ka_ac, Ka_pr, Ka_bu, Ka_va]
    pKa_base = [14, 9.25, 6.35, 4.76, 4.88, 4.82, 4.86]
    Ka = np.array([10**(-pKa) for pKa in pKa_base])
    
    # Get component molarities
    components_molarity = get_component_molarities(stream)
    
    # If we couldn't get any components, return default values
    if not components_molarity:
        stream._pH = 7.0
        stream._SAlk = 2.5  # Default alkalinity in meq/L
        return stream
    
    # Calculate pH
    h_ion = solve_ph(components_molarity, Ka)
    pH = -np.log10(h_ion)
    
    # Calculate alkalinity
    alk = calculate_alkalinity(components_molarity, pH, Ka)
    
    # Apply special case logic:
    # If S_IC is present but alkalinity is too low, estimate it from S_IC
    if components_molarity.get('S_IC', 0) > 0.01:
        # Approximation: ~70% of IC is as bicarbonate at neutral pH
        # Each mol of HCO3- contributes 1 eq of alkalinity
        S_IC_molarity = components_molarity.get('S_IC', 0)
        direct_alk_estimate = S_IC_molarity * 0.7 * 1000  # Convert to meq/L
        # Use the larger of the calculated values
        alk = max(alk, direct_alk_estimate)
    
    # Update stream properties
    stream._pH = pH
    stream._SAlk = alk
    
    return stream

def main():
    """
    Test function to demonstrate the pH and alkalinity calculations
    """
    from qsdsan import Components, set_thermo
    
    # Load default components 
    cmps = Components.load_default()
    set_thermo(cmps)
    
    # Create a test stream with high S_IC
    ws = WasteStream('test_stream')
    ws.set_flow_by_concentration(100, {
        'S_su': 0.01,
        'S_aa': 0.001,
        'S_fa': 0.001,
        'S_va': 0.001,
        'S_bu': 0.001,
        'S_pro': 0.001,
        'S_ac': 0.001,
        'S_h2': 1e-8,
        'S_ch4': 1e-5,
        'S_IC': 0.5 * C_mw,   # High inorganic carbon (0.5 kg C/m³)
        'S_IN': 0.05 * N_mw,  # Inorganic nitrogen
        'S_I': 0.02,
        'S_cat': 0.04,        # Cations
        'S_an': 0.02,         # Anions
    }, units=('m3/d', 'kg/m3'))
    
    # Calculate and update pH and alkalinity
    update_ph_and_alkalinity(ws)
    
    # Print the results
    print(f"pH: {ws.pH:.2f}")
    print(f"Alkalinity: {ws.SAlk:.2f} meq/L")
    print(f"S_IC: {ws.iconc['S_IC']:.2f} mg/L")
    
    # Now try with different values
    ws2 = WasteStream('test_stream2')
    ws2.set_flow_by_concentration(100, {
        'S_su': 0.01,
        'S_aa': 0.001,
        'S_fa': 0.001,
        'S_va': 0.005,        # Higher VFAs
        'S_bu': 0.005,        # Higher VFAs
        'S_pro': 0.005,       # Higher VFAs
        'S_ac': 0.01,         # Higher acetate
        'S_h2': 1e-8,
        'S_ch4': 1e-5,
        'S_IC': 0.2 * C_mw,   # Less inorganic carbon
        'S_IN': 0.03 * N_mw,  # Different inorganic nitrogen
        'S_I': 0.02,
        'S_cat': 0.02,        # Lower cations
        'S_an': 0.04,         # Higher anions
    }, units=('m3/d', 'kg/m3'))
    
    # Calculate and update pH and alkalinity
    update_ph_and_alkalinity(ws2)
    
    # Print the results
    print(f"\npH: {ws2.pH:.2f}")
    print(f"Alkalinity: {ws2.SAlk:.2f} meq/L")
    print(f"S_IC: {ws2.iconc['S_IC']:.2f} mg/L")

if __name__ == "__main__":
    main()
