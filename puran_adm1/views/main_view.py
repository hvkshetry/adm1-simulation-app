"""Main view for the Streamlit application
"""
import streamlit as st
from puran_adm1.components.sidebar import render_sidebar
from puran_adm1.components.feedstock_editor import render_feedstock_editor, render_kinetics_editor
from puran_adm1.components.stream_display import render_stream_properties
from puran_adm1.components.plotting import (
    render_simulation_plots, 
    render_comparison_tables,
    render_export_buttons
)
from puran_adm1.utils.styling import set_page_styling, display_branding_header, display_footer

def initialize_session_state():
    """
    Initialize session state variables if they don't exist
    
    Returns
    -------
    streamlit.session_state
        The initialized session state
    """
    # 1) Feedstock composition
    if 'influent_values' not in st.session_state:
        st.session_state.influent_values = {}
    if 'influent_explanations' not in st.session_state:
        st.session_state.influent_explanations = {}
    
    # 2) Kinetic parameters
    if 'kinetic_params' not in st.session_state:
        st.session_state.kinetic_params = {}
    if 'kinetic_explanations' not in st.session_state:
        st.session_state.kinetic_explanations = {}
    
    # 3) Whether or not we are including kinetics
    if 'use_kinetics' not in st.session_state:
        st.session_state.use_kinetics = False  # default

    # 4) Common flow
    if 'Q' not in st.session_state:
        st.session_state.Q = 170.0
    
    # 5) Simulation parameters for each of the three concurrent sims
    if 'sim_params' not in st.session_state:
        st.session_state.sim_params = [
            {'Temp': 308.15, 'HRT': 30.0, 'method': 'BDF'},
            {'Temp': 308.15, 'HRT': 45.0, 'method': 'BDF'},
            {'Temp': 308.15, 'HRT': 60.0, 'method': 'BDF'}
        ]
    
    # 6) Store results of all three simulations
    if 'sim_results' not in st.session_state:
        st.session_state.sim_results = [None, None, None]
    
    # 7) Simulation time & step
    if 'simulation_time' not in st.session_state:
        st.session_state.simulation_time = 150.0
    if 't_step' not in st.session_state:
        st.session_state.t_step = 0.1
    
    # 8) AI raw response storage
    if 'ai_recommendations' not in st.session_state:
        st.session_state.ai_recommendations = None
        
    return st.session_state

def render_main_view():
    """
    Render the main view of the application
    """
    # Set up the page
    st.set_page_config(page_title="Puran Water ADM1 Simulation", layout="wide")
    set_page_styling()
    display_branding_header()
    
    # Initialize session state
    session_state = initialize_session_state()
    
    # Page title and description
    st.title("Anaerobic Digestion Model No. 1 (ADM1) Simulation Dashboard")
    st.markdown("""
    This dashboard allows you to run **three concurrent ADM1 simulations** with different reactor 
    parameters on the **same feedstock**. Use the AI assistant to get recommended feedstock 
    state variables (and optionally kinetic parameters), then compare simulation results.
    """)
    
    # Render sidebar (returns True if simulations were run)
    render_sidebar(session_state)
    
    # Main content layout
    col1, col2 = st.columns([1, 2])
    
    # Left column: Model & Stream Data
    with col1:
        st.header("Model & Stream Data")
        
        # Display AI recommendations (if any)
        if session_state.ai_recommendations:
            with st.expander("AI Recommendations (Raw JSON)", expanded=False):
                st.markdown(f"```\n{session_state.ai_recommendations}\n```")
        
        # Render feedstock and kinetics editors
        render_feedstock_editor(session_state)
        render_kinetics_editor(session_state)
        
        # Render stream properties
        render_stream_properties(session_state)
    
    # Right column: Simulation Results
    with col2:
        st.header("Simulation Results")
        
        # Check if any simulation has run
        any_sim_ran = any([res is not None and all(res) for res in session_state.sim_results])
        if not any_sim_ran:
            st.info("Run the simulations to see results here.")
            display_footer()
            return
        
        # Render simulation plots
        fig = render_simulation_plots(session_state)
        
        # Render comparison tables
        render_comparison_tables(session_state)
        
        # Render export buttons
        render_export_buttons(session_state, fig)
    
    # Display footer
    display_footer()