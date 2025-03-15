"""Plotting components for the Streamlit application.

This module renders interactive plots for the simulation results.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from puran_adm1.models.adm1_simulation import calculate_effluent_COD, calculate_biomass_yields

def render_simulation_plots(state):
    """
    Render interactive plots for simulation results
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
        
    Returns
    -------
    plotly.graph_objects.Figure
        The plotly figure object for export
    """
    # Determine which simulations have been run
    sim_ran = [res is not None and all(res) for res in state.sim_results]
    
    if not any(sim_ran):
        st.info("Run simulations to see plots here.")
        return None
    
    # Create tabs for different plot types
    tabs = st.tabs([
        "Effluent - Acids",
        "Effluent - Inorganic Carbon",
        "Effluent - Biomass",
        "Gas - Hydrogen",
        "Gas - Methane",
        "Total VFAs"
    ])
    
    # Extract systems, times and data for each simulation
    systems = []
    time_data = []
    for i, result in enumerate(state.sim_results):
        if sim_ran[i]:
            system, _, _, _ = result
            systems.append(system)
            time_data.append(system.t)
    
    # Create and render plots
    fig = make_plots(systems, time_data, sim_ran, tabs)
    
    return fig

def make_plots(systems, time_data, sim_ran, tabs):
    """
    Create plots for the simulation results
    
    Parameters
    ----------
    systems : list
        List of simulation systems
    time_data : list
        List of time arrays
    sim_ran : list
        List of booleans indicating which simulations were run
    tabs : list
        List of streamlit tabs for plot rendering
        
    Returns
    -------
    plotly.graph_objects.Figure
        The plotly figure object for export
    """
    # Color palette for the simulations
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # Create the main figure for export
    export_fig = make_subplots(rows=3, cols=2,
                              subplot_titles=("Effluent - Acids", "Effluent - Inorganic Carbon",
                                              "Effluent - Biomass", "Gas - Hydrogen",
                                              "Gas - Methane", "Total VFAs"),
                              vertical_spacing=0.1)
    
    # 1. Effluent - Acids plot
    with tabs[0]:
        fig1 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                effluent = system.get_dynamic_data('Effluent')
                fig1.add_trace(go.Scatter(x=time, y=effluent['S_va'], name=f"Sim {i+1} - Valerate", line=dict(color=colors[i], width=2)))
                fig1.add_trace(go.Scatter(x=time, y=effluent['S_bu'], name=f"Sim {i+1} - Butyrate", line=dict(color=colors[i], width=2, dash='dash')))
                fig1.add_trace(go.Scatter(x=time, y=effluent['S_pro'], name=f"Sim {i+1} - Propionate", line=dict(color=colors[i], width=2, dash='dot')))
                fig1.add_trace(go.Scatter(x=time, y=effluent['S_ac'], name=f"Sim {i+1} - Acetate", line=dict(color=colors[i], width=2, dash='dashdot')))
                
                # Add traces to export figure
                export_fig.add_trace(go.Scatter(x=time, y=effluent['S_va'], name=f"Sim {i+1} - Valerate", line=dict(color=colors[i], width=2)), row=1, col=1)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['S_bu'], name=f"Sim {i+1} - Butyrate", line=dict(color=colors[i], width=2, dash='dash')), row=1, col=1)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['S_pro'], name=f"Sim {i+1} - Propionate", line=dict(color=colors[i], width=2, dash='dot')), row=1, col=1)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['S_ac'], name=f"Sim {i+1} - Acetate", line=dict(color=colors[i], width=2, dash='dashdot')), row=1, col=1)
        
        fig1.update_layout(
            title="Effluent - VFA Concentrations",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg COD/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # 2. Effluent - Inorganic Carbon plot
    with tabs[1]:
        fig2 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                effluent = system.get_dynamic_data('Effluent')
                fig2.add_trace(go.Scatter(x=time, y=effluent['S_IC'], name=f"Sim {i+1} - IC", line=dict(color=colors[i], width=2)))
                
                # Add traces to export figure
                export_fig.add_trace(go.Scatter(x=time, y=effluent['S_IC'], name=f"Sim {i+1} - IC", line=dict(color=colors[i], width=2)), row=1, col=2)
        
        fig2.update_layout(
            title="Effluent - Inorganic Carbon",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg C/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 3. Effluent - Biomass plot
    with tabs[2]:
        fig3 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                effluent = system.get_dynamic_data('Effluent')
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_su'], name=f"Sim {i+1} - X_su", line=dict(color=colors[i], width=2)))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_aa'], name=f"Sim {i+1} - X_aa", line=dict(color=colors[i], width=2, dash='dash')))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_fa'], name=f"Sim {i+1} - X_fa", line=dict(color=colors[i], width=2, dash='dot')))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_c4'], name=f"Sim {i+1} - X_c4", line=dict(color=colors[i], width=2, dash='dashdot')))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_pro'], name=f"Sim {i+1} - X_pro", line=dict(color=colors[i], width=2, dash='longdash')))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_ac'], name=f"Sim {i+1} - X_ac", line=dict(color=colors[i], width=2, dash='longdashdot')))
                fig3.add_trace(go.Scatter(x=time, y=effluent['X_h2'], name=f"Sim {i+1} - X_h2", line=dict(color=colors[i], width=2, dash='solid')))
                
                # Add traces to export figure (simplified for clarity)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['X_su'], name=f"Sim {i+1} - X_su", line=dict(color=colors[i], width=2)), row=2, col=1)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['X_ac'], name=f"Sim {i+1} - X_ac", line=dict(color=colors[i], width=2, dash='dash')), row=2, col=1)
                export_fig.add_trace(go.Scatter(x=time, y=effluent['X_h2'], name=f"Sim {i+1} - X_h2", line=dict(color=colors[i], width=2, dash='dot')), row=2, col=1)
        
        fig3.update_layout(
            title="Effluent - Biomass Concentrations",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg COD/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # 4. Gas - Hydrogen plot
    with tabs[3]:
        fig4 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                biogas = system.get_dynamic_data('Biogas')
                fig4.add_trace(go.Scatter(x=time, y=biogas['S_h2'], name=f"Sim {i+1} - H2", line=dict(color=colors[i], width=2)))
                
                # Add traces to export figure
                export_fig.add_trace(go.Scatter(x=time, y=biogas['S_h2'], name=f"Sim {i+1} - H2", line=dict(color=colors[i], width=2)), row=2, col=2)
        
        fig4.update_layout(
            title="Biogas - Hydrogen",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg COD/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # 5. Gas - Methane plot
    with tabs[4]:
        fig5 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                biogas = system.get_dynamic_data('Biogas')
                fig5.add_trace(go.Scatter(x=time, y=biogas['S_ch4'], name=f"Sim {i+1} - CH4", line=dict(color=colors[i], width=2)))
                
                # Add traces to export figure
                export_fig.add_trace(go.Scatter(x=time, y=biogas['S_ch4'], name=f"Sim {i+1} - CH4", line=dict(color=colors[i], width=2)), row=3, col=1)
        
        fig5.update_layout(
            title="Biogas - Methane",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg COD/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig5, use_container_width=True)
    
    # 6. Total VFAs plot
    with tabs[5]:
        fig6 = go.Figure()
        for i, (system, time) in enumerate(zip(systems, time_data)):
            if sim_ran[i]:
                effluent = system.get_dynamic_data('Effluent')
                # Calculate total VFAs as sum of S_va, S_bu, S_pro, and S_ac
                total_vfa = effluent['S_va'] + effluent['S_bu'] + effluent['S_pro'] + effluent['S_ac']
                fig6.add_trace(go.Scatter(x=time, y=total_vfa, name=f"Sim {i+1} - Total VFAs", line=dict(color=colors[i], width=2)))
                
                # Add traces to export figure
                export_fig.add_trace(go.Scatter(x=time, y=total_vfa, name=f"Sim {i+1} - Total VFAs", line=dict(color=colors[i], width=2)), row=3, col=2)
        
        fig6.update_layout(
            title="Effluent - Total VFAs",
            xaxis_title="Time (days)",
            yaxis_title="Concentration (kg COD/m³)",
            legend_title="Simulation",
            height=600
        )
        st.plotly_chart(fig6, use_container_width=True)
    
    # Update export figure layout
    export_fig.update_layout(
        height=1800,
        width=1200,
        title_text="ADM1 Simulation Results",
        showlegend=True
    )
    
    return export_fig

def render_comparison_tables(state):
    """
    Render tables comparing key metrics across simulations
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    """
    # Determine which simulations have been run
    sim_ran = [res is not None and all(res) for res in state.sim_results]
    
    if not any(sim_ran):
        return
    
    st.subheader("Simulation Comparison")
    
    # Extract final values for each simulation
    data = {
        "Parameter": [
            "Temperature (K)",
            "HRT (days)",
            "Method",
            "Final pH",
            "Final Alkalinity (meq/L)",
            "COD Removal (%)",
            "Methane Content (%)",
            "Biogas Production (Nm³/d)",
            "VS Destruction (%)"
        ]
    }
    
    # Add data for each simulation
    for i, result in enumerate(state.sim_results):
        if sim_ran[i]:
            system, inf, eff, gas = result
            
            # Calculate performance metrics
            try:
                cod_in = inf.COD
                cod_out = eff.COD
                cod_removal = (1 - cod_out / cod_in) * 100
            except:
                cod_removal = 0
            
            try:
                vs_in = inf.get_VSS()
                vs_out = eff.get_VSS()
                vs_destruction = (1 - vs_out / vs_in) * 100
            except:
                vs_destruction = 0
            
            from puran_adm1.models.adm1_simulation import calculate_gas_properties
            gas_props = calculate_gas_properties(gas)
            
            # Add data to table
            data[f"Sim {i+1}"] = [
                f"{state.sim_params[i]['Temp']:.2f}",
                f"{state.sim_params[i]['HRT']:.1f}",
                state.sim_params[i]['method'],
                f"{getattr(eff, 'pH', 7.0):.2f}",
                f"{getattr(eff, 'SAlk', 0.0):.2f}",
                f"{cod_removal:.2f}",
                f"{gas_props['methane_percent']:.2f}",
                f"{gas_props['flow_total']:.2f}",
                f"{vs_destruction:.2f}"
            ]
    
    # Create and display the DataFrame
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)

def render_export_buttons(state, fig):
    """
    Render buttons for exporting simulation results
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    fig : plotly.graph_objects.Figure
        The plotly figure to export
    """
    # Determine which simulations have been run
    sim_ran = [res is not None and all(res) for res in state.sim_results]
    
    if not any(sim_ran) or fig is None:
        return
    
    st.subheader("Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export plot as HTML
        buffer = io.StringIO()
        fig.write_html(buffer)
        html_bytes = buffer.getvalue().encode()
        st.download_button(
            label="Download Interactive Plot (HTML)",
            data=html_bytes,
            file_name="adm1_simulation_plots.html",
            mime="text/html"
        )
    
    with col2:
        # Export data as CSV
        csv_data = generate_csv_data(state, sim_ran)
        st.download_button(
            label="Download Simulation Data (CSV)",
            data=csv_data,
            file_name="adm1_simulation_data.csv",
            mime="text/csv"
        )

def generate_csv_data(state, sim_ran):
    """
    Generate CSV data for download
    
    Parameters
    ----------
    state : streamlit.session_state
        The application's session state
    sim_ran : list
        List of booleans indicating which simulations were run
        
    Returns
    -------
    bytes
        CSV data as bytes
    """
    # Create a buffer for CSV data
    buffer = io.StringIO()
    
    # Extract data for each simulation
    dfs = []
    for i, result in enumerate(state.sim_results):
        if sim_ran[i]:
            system, inf, eff, gas = result
            
            # Create DataFrame for simulation results
            effluent = system.get_dynamic_data('Effluent')
            biogas = system.get_dynamic_data('Biogas')
            
            df = pd.DataFrame({
                'Time': system.t,
                f'Sim{i+1}_S_va': effluent['S_va'],
                f'Sim{i+1}_S_bu': effluent['S_bu'],
                f'Sim{i+1}_S_pro': effluent['S_pro'],
                f'Sim{i+1}_S_ac': effluent['S_ac'],
                f'Sim{i+1}_S_IC': effluent['S_IC'],
                f'Sim{i+1}_S_IN': effluent['S_IN'],
                f'Sim{i+1}_S_h2': biogas['S_h2'],
                f'Sim{i+1}_S_ch4': biogas['S_ch4'],
                f'Sim{i+1}_X_su': effluent['X_su'],
                f'Sim{i+1}_X_aa': effluent['X_aa'],
                f'Sim{i+1}_X_fa': effluent['X_fa'],
                f'Sim{i+1}_X_c4': effluent['X_c4'],
                f'Sim{i+1}_X_pro': effluent['X_pro'],
                f'Sim{i+1}_X_ac': effluent['X_ac'],
                f'Sim{i+1}_X_h2': effluent['X_h2']
            })
            
            dfs.append(df)
    
    # Merge all DataFrames on Time column
    if dfs:
        if len(dfs) == 1:
            merged_df = dfs[0]
        else:
            merged_df = dfs[0]
            for df in dfs[1:]:
                merged_df = pd.merge(merged_df, df, on='Time', how='outer')
        
        # Write to CSV
        merged_df.to_csv(buffer, index=False)
    
    # Get CSV data as bytes
    csv_data = buffer.getvalue()
    
    return csv_data.encode()