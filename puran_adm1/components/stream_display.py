"""Stream display component for the Streamlit application.

This module renders tables and metrics for the influent, effluent, and biogas streams.
"""
import streamlit as st
import pandas as pd
from puran_adm1.models.adm1_simulation import create_influent_stream, calculate_gas_properties

def render_stream_properties(state):
    """
    Render stream properties tables and metrics
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    """
    # Render each simulation's stream properties in tabs
    tab1, tab2, tab3 = st.tabs(["Simulation 1", "Simulation 2", "Simulation 3"])
    
    # Only show stream properties if simulations have been run
    any_sim_ran = any([res is not None and all(res) for res in state.sim_results])
    
    # If simulations haven't been run, create a temporary influent stream for display
    if not any_sim_ran:
        inf = create_influent_stream(
            Q=state.Q,
            Temp=state.sim_params[0]['Temp'],
            concentrations=state.influent_values
        )
        
        # Display influent properties in each tab
        tabs = [tab1, tab2, tab3]
        for i, tab in enumerate(tabs):
            with tab:
                st.subheader(f"Sim {i+1} Influent Properties")
                render_stream_table(inf, "Influent")
        
        return
    
    # For each simulation that has been run, display stream properties
    for i, result in enumerate(state.sim_results):
        tab = [tab1, tab2, tab3][i]
        
        if result is not None and all(result):
            sys, inf, eff, gas = result
            
            with tab:
                st.subheader(f"Sim {i+1} Stream Properties")
                
                # Create two columns for influent and effluent
                col1, col2 = st.columns(2)
                
                with col1:
                    render_stream_table(inf, "Influent")
                
                with col2:
                    render_stream_table(eff, "Effluent")
                
                # Display biogas properties
                render_biogas_table(gas)

def render_stream_table(stream, stream_name):
    """
    Render a table of stream properties
    
    Parameters
    ----------
    stream : WasteStream
        The stream to display
    stream_name : str
        The name of the stream
    """
    # Get stream properties
    flow = stream.get_total_flow('L/day')
    pH = getattr(stream, 'pH', 7.0)
    salk = getattr(stream, 'SAlk', 0.0)
    
    try:
        cod = stream.COD
    except:
        try:
            cod = stream.composite('COD')
        except:
            cod = 0.0
    
    try:
        bod = stream.BOD5
    except:
        try:
            bod = stream.composite('BOD5')
        except:
            bod = 0.0
    
    try:
        tn = stream.TN
    except:
        try:
            tn = stream.composite('N')
        except:
            tn = 0.0
    
    try:
        tp = stream.TP
    except:
        try:
            tp = stream.composite('P')
        except:
            tp = 0.0
    
    try:
        tss = stream.get_TSS()
    except:
        tss = 0.0
    
    try:
        vss = stream.get_VSS()
    except:
        vss = 0.0
    
    # Create a DataFrame of stream properties
    data = {
        'Property': [
            'Flow', 'pH', 'Alkalinity',
            'COD', 'BOD', 'TN', 'TP',
            'TSS', 'VSS'
        ],
        'Value': [
            f"{flow:.2f} m³/d",
            f"{pH:.2f}",
            f"{salk:.2f} meq/L",
            f"{cod:.2f} mg/L",
            f"{bod:.2f} mg/L",
            f"{tn:.2f} mg/L",
            f"{tp:.2f} mg/L",
            f"{tss:.2f} mg/L",
            f"{vss:.2f} mg/L"
        ]
    }
    
    st.markdown(f"##### {stream_name}")
    st.dataframe(pd.DataFrame(data), hide_index=True)

def render_biogas_table(gas_stream):
    """
    Render a table of biogas properties
    
    Parameters
    ----------
    gas_stream : WasteStream
        The gas stream to display
    """
    # Calculate gas properties
    gas_props = calculate_gas_properties(gas_stream)
    
    # Create a DataFrame of gas properties
    data = {
        'Property': [
            'Flow Rate',
            'Methane',
            'CO2',
            'H2'
        ],
        'Value': [
            f"{gas_props['flow_total']:.2f} Nm³/d",
            f"{gas_props['methane_percent']:.2f} %",
            f"{gas_props['co2_percent']:.2f} %",
            f"{gas_props['h2_ppmv']:.2f} ppmv"
        ]
    }
    
    st.markdown("##### Biogas")
    st.dataframe(pd.DataFrame(data), hide_index=True)