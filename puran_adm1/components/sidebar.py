"""Sidebar component for the Streamlit application.

This module renders the sidebar with parameter controls and run buttons.
"""
import streamlit as st
import numpy as np
from puran_adm1.models.adm1_simulation import run_simulation
from puran_adm1.api.ai_assistant import get_ai_recommendations

def render_sidebar(state):
    """
    Render the sidebar with simulation parameters and run buttons
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
        
    Returns
    -------
    bool
        True if simulations were run, False otherwise
    """
    with st.sidebar:
        st.title("Simulation Controls")
        
        # AI Assistant
        st.header("AI Feedstock Assistant")
        ai_description = st.text_area(
            "Describe your feedstock in plain language",
            "Food waste consisting of 30% carbohydrates, 15% proteins, and 10% lipids.",
            help="Describe your feedstock composition and characteristics in natural language"
        )
        
        use_kinetics = st.checkbox(
            "Include kinetic parameters in recommendations",
            value=state.use_kinetics,
            help="Get kinetic parameter recommendations in addition to feedstock composition"
        )
        
        if use_kinetics != state.use_kinetics:
            state.use_kinetics = use_kinetics
        
        if st.button("Get AI Recommendations"):
            with st.spinner("Getting AI recommendations..."):
                try:
                    recommendations = get_ai_recommendations(ai_description, use_kinetics)
                    if 'influent_values' in recommendations:
                        state.influent_values = recommendations['influent_values']
                    if 'influent_explanations' in recommendations:
                        state.influent_explanations = recommendations['influent_explanations']
                    if use_kinetics and 'kinetic_params' in recommendations:
                        state.kinetic_params = recommendations['kinetic_params']
                    if use_kinetics and 'kinetic_explanations' in recommendations:
                        state.kinetic_explanations = recommendations['kinetic_explanations']
                    state.ai_recommendations = recommendations  # Store the full response
                    st.success("Recommendations applied!")
                except Exception as e:
                    st.error(f"Error getting AI recommendations: {str(e)}")
        
        # Common Settings
        st.header("Common Settings")
        
        # Influent flow rate (same for all three simulations)
        state.Q = st.number_input(
            "Influent Flow (m³/d)",
            min_value=10.0,
            max_value=1000.0,
            value=state.Q,
            step=10.0,
            help="Flow rate of the influent stream"
        )
        
        # Simulation parameters for each simulation
        st.header("Simulation Parameters")
        
        # Simulation 1 parameters
        with st.expander("Simulation 1", expanded=True):
            state.sim_params[0]['Temp'] = st.number_input(
                "Temperature (K) - Sim 1",
                min_value=273.15,
                max_value=373.15,
                value=state.sim_params[0]['Temp'],
                step=1.0,
                help="Operating temperature for the digester"
            )
            state.sim_params[0]['HRT'] = st.number_input(
                "HRT (days) - Sim 1",
                min_value=1.0,
                max_value=100.0,
                value=state.sim_params[0]['HRT'],
                step=1.0,
                help="Hydraulic Retention Time"
            )
            state.sim_params[0]['method'] = st.selectbox(
                "Integration Method - Sim 1",
                ["BDF", "RK45", "RK23", "DOP853", "Radau", "LSODA"],
                index=0,
                help="Numerical integration method (BDF is best for stiff systems)"
            )
        
        # Simulation 2 parameters
        with st.expander("Simulation 2", expanded=True):
            state.sim_params[1]['Temp'] = st.number_input(
                "Temperature (K) - Sim 2",
                min_value=273.15,
                max_value=373.15,
                value=state.sim_params[1]['Temp'],
                step=1.0
            )
            state.sim_params[1]['HRT'] = st.number_input(
                "HRT (days) - Sim 2",
                min_value=1.0,
                max_value=100.0,
                value=state.sim_params[1]['HRT'],
                step=1.0
            )
            state.sim_params[1]['method'] = st.selectbox(
                "Integration Method - Sim 2",
                ["BDF", "RK45", "RK23", "DOP853", "Radau", "LSODA"],
                index=0
            )
        
        # Simulation 3 parameters
        with st.expander("Simulation 3", expanded=True):
            state.sim_params[2]['Temp'] = st.number_input(
                "Temperature (K) - Sim 3",
                min_value=273.15,
                max_value=373.15,
                value=state.sim_params[2]['Temp'],
                step=1.0
            )
            state.sim_params[2]['HRT'] = st.number_input(
                "HRT (days) - Sim 3",
                min_value=1.0,
                max_value=100.0,
                value=state.sim_params[2]['HRT'],
                step=1.0
            )
            state.sim_params[2]['method'] = st.selectbox(
                "Integration Method - Sim 3",
                ["BDF", "RK45", "RK23", "DOP853", "Radau", "LSODA"],
                index=0
            )
        
        # Simulation time settings
        st.header("Simulation Time")
        
        state.simulation_time = st.number_input(
            "Duration (days)",
            min_value=10.0,
            max_value=500.0,
            value=state.simulation_time,
            step=10.0,
            help="Total simulation duration"
        )
        
        state.t_step = st.number_input(
            "Time Step (days)",
            min_value=0.01,
            max_value=1.0,
            value=state.t_step,
            step=0.01,
            help="Time step for numerical integration"
        )
        
        # Run button
        st.header("Run Simulations")
        
        run_button = st.button("Run All Simulations", use_container_width=True)
        
        if run_button:
            sims_run = run_all_simulations(state)
            st.success("Simulations complete!")
            return sims_run
    
    return False

def run_all_simulations(state):
    """
    Run all three simulations with the current parameters
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
        
    Returns
    -------
    bool
        True if all simulations were run successfully, False otherwise
    """
    # Clear previous results
    state.sim_results = [None, None, None]
    
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        for i in range(3):
            # Update progress
            progress = (i / 3) * 100
            progress_bar.progress(int(progress))
            status_text.text(f"Running simulation {i+1}/3...")
            
            # Run simulation
            result = run_simulation(
                Q=state.Q,
                Temp=state.sim_params[i]['Temp'],
                HRT=state.sim_params[i]['HRT'],
                concentrations=state.influent_values,
                kinetic_params=state.kinetic_params if state.use_kinetics else {},
                simulation_time=state.simulation_time,
                t_step=state.t_step,
                method=state.sim_params[i]['method'],
                use_kinetics=state.use_kinetics
            )
            
            # Store result
            state.sim_results[i] = result
        
        # Update progress to 100%
        progress_bar.progress(100)
        status_text.text("All simulations complete!")
        
        return True
    
    except Exception as e:
        st.sidebar.error(f"Error running simulations: {str(e)}")
        return False
    
    finally:
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()