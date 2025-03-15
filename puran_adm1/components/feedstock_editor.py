"""Feedstock editor component for the Streamlit application.

This module renders the feedstock editor UI with sliders for ADM1 state variables.
"""
import streamlit as st
from chemicals.elements import molecular_weight as get_mw

# Define molecular weights
C_mw = get_mw({'C': 1})
N_mw = get_mw({'N': 1})

def render_feedstock_editor(state):
    """
    Render the feedstock editor UI component
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    """
    with st.expander("Feedstock Composition", expanded=True):
        st.markdown("Set the concentrations of ADM1 state variables for the influent.")
        
        # Initialize default values if none exist
        if not state.influent_values:
            state.influent_values = get_default_influent_values()
        
        # Organize components by categories
        categories = {
            "Soluble Substrates": ["S_su", "S_aa", "S_fa"],
            "Volatile Fatty Acids": ["S_va", "S_bu", "S_pro", "S_ac"],
            "Gas Components": ["S_h2", "S_ch4"],
            "Inorganic Components": ["S_IC", "S_IN", "S_I", "S_cat", "S_an"],
            "Particulate Components": ["X_c", "X_ch", "X_pr", "X_li", "X_I"],
            "Biomass": ["X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2"]
        }
        
        # Use two columns for the feedstock editor
        for category, components in categories.items():
            st.subheader(category)
            cols = st.columns(2)
            
            for i, comp_id in enumerate(components):
                col = cols[i % 2]
                with col:
                    if comp_id == "S_IC":
                        # Special handling for S_IC (displayed as kg C/m³)
                        value = state.influent_values.get(comp_id, 0) / C_mw
                        new_value = st.number_input(
                            f"{comp_id} (kg C/m³)",
                            min_value=0.0,
                            max_value=1.0,
                            value=value,
                            step=0.01,
                            help=get_component_help(comp_id, state.influent_explanations)
                        )
                        state.influent_values[comp_id] = new_value * C_mw
                    elif comp_id == "S_IN":
                        # Special handling for S_IN (displayed as kg N/m³)
                        value = state.influent_values.get(comp_id, 0) / N_mw
                        new_value = st.number_input(
                            f"{comp_id} (kg N/m³)",
                            min_value=0.0,
                            max_value=0.5,
                            value=value,
                            step=0.01,
                            help=get_component_help(comp_id, state.influent_explanations)
                        )
                        state.influent_values[comp_id] = new_value * N_mw
                    else:
                        # Standard handling (displayed as kg COD/m³)
                        value = state.influent_values.get(comp_id, 0)
                        state.influent_values[comp_id] = st.number_input(
                            f"{comp_id} (kg COD/m³)",
                            min_value=0.0,
                            max_value=100.0 if comp_id.startswith("X_") else 10.0,
                            value=value,
                            step=0.01 if comp_id.startswith("S_") else 0.1,
                            help=get_component_help(comp_id, state.influent_explanations)
                        )

def render_kinetics_editor(state):
    """
    Render the kinetics editor UI component if use_kinetics is True
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    """
    if not state.use_kinetics:
        return
    
    with st.expander("Kinetic Parameters", expanded=False):
        st.markdown("Set the kinetic parameters for the ADM1 model.")
        
        # Initialize default values if none exist
        if not state.kinetic_params:
            state.kinetic_params = get_default_kinetic_values()
        
        # Organize parameters by categories
        categories = {
            "Disintegration & Hydrolysis": ["k_dis", "k_hyd_ch", "k_hyd_pr", "k_hyd_li"],
            "Uptake Rates": ["k_m_su", "k_m_aa", "k_m_fa", "k_m_c4", "k_m_pro", "k_m_ac", "k_m_h2"],
            "Half Saturation Constants": ["K_S_su", "K_S_aa", "K_S_fa", "K_S_c4", "K_S_pro", "K_S_ac", "K_S_h2"],
            "pH Inhibition": ["pH_UL_aa", "pH_LL_aa", "pH_UL_ac", "pH_LL_ac", "pH_UL_h2", "pH_LL_h2"],
            "Yields": ["Y_su", "Y_aa", "Y_fa", "Y_c4", "Y_pro", "Y_ac", "Y_h2"],
            "Decay Rates": ["k_dec_X_su", "k_dec_X_aa", "k_dec_X_fa", "k_dec_X_c4", "k_dec_X_pro", "k_dec_X_ac", "k_dec_X_h2"]
        }
        
        for category, parameters in categories.items():
            st.subheader(category)
            cols = st.columns(2)
            
            for i, param_id in enumerate(parameters):
                col = cols[i % 2]
                with col:
                    value = state.kinetic_params.get(param_id, 0)
                    
                    # Adjust min/max values based on parameter type
                    if param_id.startswith("k_"):
                        min_val, max_val, step = 0.0, 10.0, 0.1
                    elif param_id.startswith("K_S_"):
                        min_val, max_val, step = 0.0, 1.0, 0.01
                    elif param_id.startswith("pH_"):
                        min_val, max_val, step = 3.0, 10.0, 0.1
                    elif param_id.startswith("Y_"):
                        min_val, max_val, step = 0.0, 1.0, 0.01
                    else:
                        min_val, max_val, step = 0.0, 10.0, 0.1
                    
                    state.kinetic_params[param_id] = st.number_input(
                        param_id,
                        min_value=min_val,
                        max_value=max_val,
                        value=value,
                        step=step,
                        help=get_parameter_help(param_id, state.kinetic_explanations)
                    )

def get_default_influent_values():
    """
    Get default values for the influent state variables
    
    Returns
    -------
    dict
        Dictionary of default influent values
    """
    return {
        'S_su': 0.01,
        'S_aa': 0.001,
        'S_fa': 0.001,
        'S_va': 0.001,
        'S_bu': 0.001,
        'S_pro': 0.001,
        'S_ac': 0.001,
        'S_h2': 1e-8,
        'S_ch4': 1e-5,
        'S_IC': 0.04 * C_mw,
        'S_IN': 0.01 * N_mw,
        'S_I': 0.02,
        'X_c': 2.0,
        'X_ch': 5.0,
        'X_pr': 20.0,
        'X_li': 5.0,
        'X_su': 0.01,
        'X_aa': 0.01,
        'X_fa': 0.01,
        'X_c4': 0.01,
        'X_pro': 0.01,
        'X_ac': 0.01,
        'X_h2': 0.01,
        'X_I': 25.0,
        'S_cat': 0.04,
        'S_an': 0.02,
    }

def get_default_kinetic_values():
    """
    Get default values for the kinetic parameters
    
    Returns
    -------
    dict
        Dictionary of default kinetic values
    """
    return {
        'k_dis': 0.5,         # Disintegration rate [d^-1]
        'k_hyd_ch': 10.0,     # Hydrolysis rate for carbohydrates [d^-1]
        'k_hyd_pr': 10.0,     # Hydrolysis rate for proteins [d^-1] 
        'k_hyd_li': 10.0,     # Hydrolysis rate for lipids [d^-1]
        
        'k_m_su': 30.0,       # Maximum uptake rate for sugars [d^-1]
        'k_m_aa': 50.0,       # Maximum uptake rate for amino acids [d^-1]
        'k_m_fa': 6.0,        # Maximum uptake rate for fatty acids [d^-1]
        'k_m_c4': 20.0,       # Maximum uptake rate for valerate and butyrate [d^-1]
        'k_m_pro': 13.0,      # Maximum uptake rate for propionate [d^-1]
        'k_m_ac': 8.0,        # Maximum uptake rate for acetate [d^-1]
        'k_m_h2': 35.0,       # Maximum uptake rate for hydrogen [d^-1]
        
        'K_S_su': 0.5,        # Half saturation constant for sugars [kg COD/m^3]
        'K_S_aa': 0.3,        # Half saturation constant for amino acids [kg COD/m^3]
        'K_S_fa': 0.4,        # Half saturation constant for fatty acids [kg COD/m^3]
        'K_S_c4': 0.2,        # Half saturation constant for valerate and butyrate [kg COD/m^3]
        'K_S_pro': 0.1,       # Half saturation constant for propionate [kg COD/m^3]
        'K_S_ac': 0.15,       # Half saturation constant for acetate [kg COD/m^3]
        'K_S_h2': 7e-6,       # Half saturation constant for hydrogen [kg COD/m^3]
        
        'pH_UL_aa': 5.5,      # Upper limit of pH for amino acid degraders
        'pH_LL_aa': 4.0,      # Lower limit of pH for amino acid degraders
        'pH_UL_ac': 7.0,      # Upper limit of pH for acetate degraders
        'pH_LL_ac': 6.0,      # Lower limit of pH for acetate degraders
        'pH_UL_h2': 6.0,      # Upper limit of pH for hydrogen degraders
        'pH_LL_h2': 5.0,      # Lower limit of pH for hydrogen degraders
        
        'Y_su': 0.1,          # Yield of biomass on substrate, sugar degraders [kg COD/kg COD]
        'Y_aa': 0.08,         # Yield of biomass on substrate, amino acid degraders [kg COD/kg COD]
        'Y_fa': 0.06,         # Yield of biomass on substrate, LCFA degraders [kg COD/kg COD]
        'Y_c4': 0.06,         # Yield of biomass on substrate, valerate & butyrate degraders [kg COD/kg COD]
        'Y_pro': 0.04,        # Yield of biomass on substrate, propionate degraders [kg COD/kg COD]
        'Y_ac': 0.05,         # Yield of biomass on substrate, acetate degraders [kg COD/kg COD]
        'Y_h2': 0.06,         # Yield of biomass on substrate, hydrogen degraders [kg COD/kg COD]
        
        'k_dec_X_su': 0.02,   # Decay rate for sugar degraders [d^-1]
        'k_dec_X_aa': 0.02,   # Decay rate for amino acid degraders [d^-1]
        'k_dec_X_fa': 0.02,   # Decay rate for LCFA degraders [d^-1]
        'k_dec_X_c4': 0.02,   # Decay rate for valerate & butyrate degraders [d^-1]
        'k_dec_X_pro': 0.02,  # Decay rate for propionate degraders [d^-1]
        'k_dec_X_ac': 0.02,   # Decay rate for acetate degraders [d^-1]
        'k_dec_X_h2': 0.02,   # Decay rate for hydrogen degraders [d^-1]
    }

def get_component_help(comp_id, explanations):
    """
    Get help text for a component, including AI explanation if available
    
    Parameters
    ----------
    comp_id : str
        Component ID
    explanations : dict
        Dictionary of explanations from AI assistant
        
    Returns
    -------
    str
        Help text for the component
    """
    # Basic descriptions
    descriptions = {
        'S_su': "Monosaccharides (sugars)",
        'S_aa': "Amino acids",
        'S_fa': "Long chain fatty acids",
        'S_va': "Valerate",
        'S_bu': "Butyrate",
        'S_pro': "Propionate",
        'S_ac': "Acetate",
        'S_h2': "Hydrogen",
        'S_ch4': "Methane",
        'S_IC': "Inorganic carbon (bicarbonate)",
        'S_IN': "Inorganic nitrogen (ammonia)",
        'S_I': "Soluble inerts",
        'X_c': "Composite particulates",
        'X_ch': "Carbohydrates",
        'X_pr': "Proteins",
        'X_li': "Lipids",
        'X_su': "Sugar degraders",
        'X_aa': "Amino acid degraders",
        'X_fa': "LCFA degraders",
        'X_c4': "Valerate and butyrate degraders",
        'X_pro': "Propionate degraders",
        'X_ac': "Acetate degraders",
        'X_h2': "Hydrogen degraders",
        'X_I': "Particulate inerts",
        'S_cat': "Cations",
        'S_an': "Anions"
    }
    
    # Start with the basic description
    help_text = descriptions.get(comp_id, "")
    
    # Add AI explanation if available
    if explanations and comp_id in explanations:
        help_text += f"\n\nAI Suggestion: {explanations[comp_id]}"
    
    return help_text

def get_parameter_help(param_id, explanations):
    """
    Get help text for a parameter, including AI explanation if available
    
    Parameters
    ----------
    param_id : str
        Parameter ID
    explanations : dict
        Dictionary of explanations from AI assistant
        
    Returns
    -------
    str
        Help text for the parameter
    """
    # Basic descriptions
    descriptions = {
        'k_dis': "Disintegration rate constant",
        'k_hyd_ch': "Hydrolysis rate for carbohydrates",
        'k_hyd_pr': "Hydrolysis rate for proteins",
        'k_hyd_li': "Hydrolysis rate for lipids",
        'k_m_su': "Maximum uptake rate for sugars",
        'k_m_aa': "Maximum uptake rate for amino acids",
        'k_m_fa': "Maximum uptake rate for fatty acids",
        'k_m_c4': "Maximum uptake rate for valerate and butyrate",
        'k_m_pro': "Maximum uptake rate for propionate",
        'k_m_ac': "Maximum uptake rate for acetate",
        'k_m_h2': "Maximum uptake rate for hydrogen",
        'K_S_su': "Half saturation constant for sugars",
        'K_S_aa': "Half saturation constant for amino acids",
        'K_S_fa': "Half saturation constant for fatty acids",
        'K_S_c4': "Half saturation constant for valerate and butyrate",
        'K_S_pro': "Half saturation constant for propionate",
        'K_S_ac': "Half saturation constant for acetate",
        'K_S_h2': "Half saturation constant for hydrogen",
        'pH_UL_aa': "Upper limit of pH for amino acid degraders",
        'pH_LL_aa': "Lower limit of pH for amino acid degraders",
        'pH_UL_ac': "Upper limit of pH for acetate degraders",
        'pH_LL_ac': "Lower limit of pH for acetate degraders",
        'pH_UL_h2': "Upper limit of pH for hydrogen degraders",
        'pH_LL_h2': "Lower limit of pH for hydrogen degraders",
        'Y_su': "Yield of biomass on substrate, sugar degraders",
        'Y_aa': "Yield of biomass on substrate, amino acid degraders",
        'Y_fa': "Yield of biomass on substrate, LCFA degraders",
        'Y_c4': "Yield of biomass on substrate, valerate and butyrate degraders",
        'Y_pro': "Yield of biomass on substrate, propionate degraders",
        'Y_ac': "Yield of biomass on substrate, acetate degraders",
        'Y_h2': "Yield of biomass on substrate, hydrogen degraders",
        'k_dec_X_su': "Decay rate for sugar degraders",
        'k_dec_X_aa': "Decay rate for amino acid degraders",
        'k_dec_X_fa': "Decay rate for LCFA degraders",
        'k_dec_X_c4': "Decay rate for valerate and butyrate degraders",
        'k_dec_X_pro': "Decay rate for propionate degraders",
        'k_dec_X_ac': "Decay rate for acetate degraders",
        'k_dec_X_h2': "Decay rate for hydrogen degraders",
    }
    
    # Start with the basic description
    help_text = descriptions.get(param_id, "")
    
    # Add AI explanation if available
    if explanations and param_id in explanations:
        help_text += f"\n\nAI Suggestion: {explanations[param_id]}"
    
    return help_text