"""
Plotting components for the application
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from puran_adm1.models.adm1_simulation import calculate_biomass_yields, calculate_effluent_COD, calculate_gas_properties
from puran_adm1.components.export.pdf_export_enhanced import render_pdf_export_button

def render_simulation_plots(session_state):
    """
    Render the simulation result plots
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
        
    Returns
    -------
    go.Figure
        The plotly figure object
    """
    # Check if any simulation has run
    any_sim_ran = any([res is not None and all(res) for res in session_state.sim_results])
    if not any_sim_ran:
        st.info("Run the simulations to see results here.")
        return None

    plot_type = st.selectbox(
        "Select Plot Type",
        [
            "Effluent - Acids",
            "Effluent - Inorganic Carbon",
            "Effluent - Biomass Components",
            "Gas - Hydrogen",
            "Gas - Methane",
            "Total VFAs"
        ]
    )

    fig = go.Figure()

    for i, (sys_i, inf_i, eff_i, gas_i) in enumerate(session_state.sim_results):
        if not sys_i or not inf_i or not eff_i or not gas_i:
            continue
            
        t_stamp_eff = eff_i.scope.time_series
        t_stamp_gas = gas_i.scope.time_series
        cmps_obj = inf_i.components

        if plot_type == "Effluent - Acids":
            acid_list = ['S_su','S_aa','S_fa','S_va','S_bu','S_pro','S_ac']
            for acid in acid_list:
                idx = cmps_obj.index(acid)
                data_acid = eff_i.scope.record[:, idx]
                fig.add_trace(go.Scatter(
                    x=t_stamp_eff,
                    y=data_acid,
                    mode='lines',
                    name=f"{acid} (Sim {i+1})"
                ))
        elif plot_type == "Effluent - Inorganic Carbon":
            idx = cmps_obj.index('S_IC')
            data_ic = eff_i.scope.record[:, idx]
            fig.add_trace(go.Scatter(
                x=t_stamp_eff,
                y=data_ic,
                mode='lines',
                name=f"S_IC (Sim {i+1})"
            ))
        elif plot_type == "Effluent - Biomass Components":
            bio_list = ['X_su','X_aa','X_fa','X_c4','X_pro','X_ac','X_h2']
            for bio in bio_list:
                idx = cmps_obj.index(bio)
                data_bio = eff_i.scope.record[:, idx]
                fig.add_trace(go.Scatter(
                    x=t_stamp_eff,
                    y=data_bio,
                    mode='lines',
                    name=f"{bio} (Sim {i+1})"
                ))
        elif plot_type == "Gas - Hydrogen":
            idx = cmps_obj.index('S_h2')
            data_h2 = gas_i.scope.record[:, idx]
            fig.add_trace(go.Scatter(
                x=t_stamp_gas,
                y=data_h2,
                mode='lines',
                name=f"S_h2 (Sim {i+1})"
            ))
        elif plot_type == "Gas - Methane":
            idx_ch4 = cmps_obj.index('S_ch4')
            idx_ic = cmps_obj.index('S_IC')
            data_ch4 = gas_i.scope.record[:, idx_ch4]
            data_ic = gas_i.scope.record[:, idx_ic]
            fig.add_trace(go.Scatter(
                x=t_stamp_gas,
                y=data_ch4,
                mode='lines',
                name=f"S_ch4 (Sim {i+1})"
            ))
            fig.add_trace(go.Scatter(
                x=t_stamp_gas,
                y=data_ic,
                mode='lines',
                name=f"S_IC (Sim {i+1})"
            ))
        elif plot_type == "Total VFAs":
            idx_vfa = cmps_obj.indices(['S_va','S_bu','S_pro','S_ac'])
            vfa_matrix = eff_i.scope.record[:, idx_vfa]
            total_vfa = np.sum(vfa_matrix, axis=1)
            fig.add_trace(go.Scatter(
                x=t_stamp_eff,
                y=total_vfa,
                mode='lines',
                name=f"Total VFAs (Sim {i+1})"
            ))

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='closest',
        height=600
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)',
        title="Time [d]"
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)',
        title="Concentration [mg/L]"
    )

    st.plotly_chart(fig, use_container_width=True)
    return fig

def render_comparison_tables(session_state):
    """
    Render the comparison tables for the simulation results
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    st.header("Comparison of Simulation Results")
    
    # Create comparison tables
    yield_data = []
    cod_data = []
    
    for i, sim_res in enumerate(session_state.sim_results):
        if not sim_res or not all(sim_res):
            continue
            
        sys_i, inf_i, eff_i, _ = sim_res
        
        # Get simulation parameters
        temp = session_state.sim_params[i]['Temp']
        hrt = session_state.sim_params[i]['HRT']
        
        # Calculate yields
        biomass_yields = calculate_biomass_yields(inf_i, eff_i)
        
        # Calculate COD values
        cod_values = calculate_effluent_COD(eff_i)
        cod_removal = (1 - eff_i.COD/inf_i.COD) * 100
        
        # Add to data tables
        yield_data.append({
            'Simulation': f"Sim {i+1}",
            'Temperature (K)': temp,
            'HRT (days)': hrt,
            'VSS Yield (kg/kg COD)': biomass_yields['VSS_yield'],
            'TSS Yield (kg/kg COD)': biomass_yields['TSS_yield']
        })
        
        cod_data.append({
            'Simulation': f"Sim {i+1}",
            'Temperature (K)': temp,
            'HRT (days)': hrt,
            'Soluble COD (mg/L)': cod_values['soluble_COD'],
            'Particulate COD (mg/L)': cod_values['particulate_COD'],
            'Total COD (mg/L)': cod_values['total_COD'],
            'COD Removal (%)': cod_removal
        })
    
    # Display comparison tables
    if yield_data:
        st.subheader("Biomass Yield Comparison")
        st.dataframe(pd.DataFrame(yield_data))
        
    if cod_data:
        st.subheader("COD Comparison")
        st.dataframe(pd.DataFrame(cod_data))

def render_export_buttons(session_state, fig=None):
    """
    Render the export/download buttons
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    fig : go.Figure, optional
        The plotly figure to export, by default None
    """
    # Export buttons
    c1, c2, c3 = st.columns(3)
    
    # Export plot button
    with c1:
        if st.button("Export Plot") and fig:
            fig.write_html("adm1_three_sim_plot.html")
            with open("adm1_three_sim_plot.html", "rb") as file:
                st.download_button(
                    label="Download Interactive Plot (HTML)",
                    data=file,
                    file_name="adm1_three_sim_plot.html",
                    mime="text/html"
                )
    
    # Export data button
    with c2:
        if st.button("Export Data"):
            plot_type = st.session_state.get('plot_type', "Total VFAs")
            df_list = []
            for i, (sys_i, inf_i, eff_i, gas_i) in enumerate(session_state.sim_results):
                if eff_i and gas_i:
                    t_eff = eff_i.scope.time_series
                    df_sim = pd.DataFrame({"Time_d": t_eff})
                    
                    if plot_type == "Total VFAs":
                        idx_vfa = inf_i.components.indices(['S_va','S_bu','S_pro','S_ac'])
                        vfa_matrix = eff_i.scope.record[:, idx_vfa]
                        total_vfa = np.sum(vfa_matrix, axis=1)
                        df_sim[f"Total_VFA_Sim{i+1}"] = total_vfa
                    elif plot_type == "Effluent - Acids":
                        acid_list = ['S_su','S_aa','S_fa','S_va','S_bu','S_pro','S_ac']
                        for acid in acid_list:
                            idx = inf_i.components.index(acid)
                            df_sim[f"{acid}_Sim{i+1}"] = eff_i.scope.record[:, idx]
                    elif plot_type == "Effluent - Inorganic Carbon":
                        idx = inf_i.components.index('S_IC')
                        df_sim[f"S_IC_Sim{i+1}"] = eff_i.scope.record[:, idx]
                    elif plot_type == "Effluent - Biomass Components":
                        bio_list = ['X_su','X_aa','X_fa','X_c4','X_pro','X_ac','X_h2']
                        for bio in bio_list:
                            idx = inf_i.components.index(bio)
                            df_sim[f"{bio}_Sim{i+1}"] = eff_i.scope.record[:, idx]
                    elif plot_type == "Gas - Hydrogen":
                        idx_h2 = inf_i.components.index('S_h2')
                        df_sim[f"S_h2_Sim{i+1}"] = gas_i.scope.record[:, idx_h2]
                    elif plot_type == "Gas - Methane":
                        idx_ch4 = inf_i.components.index('S_ch4')
                        idx_ic = inf_i.components.index('S_IC')
                        df_sim[f"S_ch4_Sim{i+1}"] = gas_i.scope.record[:, idx_ch4]
                        df_sim[f"S_IC_Sim{i+1}"] = gas_i.scope.record[:, idx_ic]
                    
                    df_list.append(df_sim)
            
            if df_list:
                df_merged = df_list[0]
                for d in df_list[1:]:
                    df_merged = pd.merge(df_merged, d, on="Time_d", how="outer")
                df_merged.sort_values(by="Time_d", inplace=True)
                csv_data = df_merged.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="adm1_three_sim_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data available to export.")
    
    # Comprehensive PDF export button
    with c3:
        # Render the PDF export button for comprehensive simulation report
        render_pdf_export_button(session_state)