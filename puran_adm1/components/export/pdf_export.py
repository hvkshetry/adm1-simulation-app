"""
PDF Export functionality for ADM1 simulation results
"""
import os
import tempfile
import time
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
import streamlit as st
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to prevent GUI issues

from puran_adm1.models.adm1_simulation import calculate_biomass_yields, calculate_effluent_COD, calculate_gas_properties


class ADM1ReportPDF(FPDF):
    """Extended FPDF class for ADM1 reports with custom headers and footers"""
    
    def __init__(self, title="ADM1 Simulation Report"):
        super().__init__()
        self.title = title
        # Get current date and time
        self.report_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def header(self):
        # Logo
        try:
            # Try to load Puran Water logo
            self.image('puran_water_logo.png', 10, 8, 33)
        except Exception:
            # If logo fails to load, just use text
            pass
            
        # Title
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self.title, 0, 1, 'C')
        
        # Date
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generated: {self.report_datetime}', 0, 1, 'R')
        
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')


def generate_pdf_report(session_state, filename="adm1_simulation_report.pdf"):
    """
    Generate a comprehensive PDF report of all simulation inputs, results, and plots
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state containing simulation data
    filename : str, optional
        Filename for the PDF report, by default "adm1_simulation_report.pdf"
    
    Returns
    -------
    BytesIO
        BytesIO object containing the PDF data
    """
    # Check if any simulation has run
    any_sim_ran = any([res is not None and all(res) for res in session_state.sim_results])
    if not any_sim_ran:
        st.error("No simulation results available. Please run at least one simulation.")
        return None
    
    try:
        # Create PDF object
        pdf = ADM1ReportPDF()
        pdf.add_page()
        pdf.alias_nb_pages()  # For page numbering
    
    # Set up fonts
    pdf.set_font('Arial', 'B', 14)
    
    # Title and introduction
    pdf.cell(0, 10, "ADM1 Simulation Report", 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, "This report contains the results of Anaerobic Digestion Model No. 1 (ADM1) simulations. "
                         "The report includes simulation parameters, feedstock characteristics, and results for all simulations.")
    pdf.ln(5)
    
    # --- Section 1: Simulation Parameters ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "1. Simulation Parameters", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    # Common parameters
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "Common Parameters", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 6, f"Flow Rate (Q):", 0, 0)
    pdf.cell(0, 6, f"{session_state.Q} m³/d", 0, 1)
    pdf.cell(60, 6, f"Simulation Time:", 0, 0)
    pdf.cell(0, 6, f"{session_state.simulation_time} days", 0, 1)
    pdf.cell(60, 6, f"Time Step:", 0, 0)
    pdf.cell(0, 6, f"{session_state.t_step} days", 0, 1)
    pdf.ln(5)
    
    # Individual simulation parameters
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "Simulation Specific Parameters", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    # Create a table
    col_width = 45
    row_height = 6
    # Headers
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(col_width, row_height, "Parameter", 1, 0, 'C', True)
    for i in range(3):
        pdf.cell(col_width, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Temperature
    pdf.cell(col_width, row_height, "Temperature (K)", 1, 0)
    for i in range(3):
        value = session_state.sim_params[i].get('Temp', 'N/A')
        pdf.cell(col_width, row_height, f"{value}", 1, 0, 'C')
    pdf.ln(row_height)
    
    # HRT
    pdf.cell(col_width, row_height, "HRT (days)", 1, 0)
    for i in range(3):
        value = session_state.sim_params[i].get('HRT', 'N/A')
        pdf.cell(col_width, row_height, f"{value}", 1, 0, 'C')
    pdf.ln(row_height)
    
    # Integration Method
    pdf.cell(col_width, row_height, "Integration Method", 1, 0)
    for i in range(3):
        value = session_state.sim_params[i].get('method', 'N/A')
        pdf.cell(col_width, row_height, f"{value}", 1, 0, 'C')
    pdf.ln(row_height)
    pdf.ln(10)
    
    # --- Section 2: Feedstock Composition ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "2. Feedstock Composition", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    # Check page space
    if pdf.get_y() > 230:
        pdf.add_page()
    
    # Create a table for feedstock components
    pdf.set_font('Arial', 'B', 9)
    # Headers
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(70, row_height, "Component", 1, 0, 'C', True)
    pdf.cell(40, row_height, "Value", 1, 0, 'C', True)
    pdf.cell(80, row_height, "Description", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Component values
    pdf.set_font('Arial', '', 8)
    for key, value in session_state.influent_values.items():
        explanation = session_state.influent_explanations.get(key, "")
        # Truncate long explanations
        if len(explanation) > 50:
            explanation = explanation[:47] + "..."
            
        pdf.cell(70, row_height, key, 1, 0)
        pdf.cell(40, row_height, f"{value}", 1, 0, 'C')
        pdf.cell(80, row_height, explanation, 1, 0)
        pdf.ln(row_height)
        
        # Check page space, add new page if needed
        if pdf.get_y() > 250:
            pdf.add_page()
    
    pdf.ln(5)
    
    # --- Section 3: Kinetic Parameters (if used) ---
    if session_state.use_kinetics and session_state.kinetic_params:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "3. Kinetic Parameters", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        
        # Check page space
        if pdf.get_y() > 230:
            pdf.add_page()
        
        # Create a table for kinetic parameters
        pdf.set_font('Arial', 'B', 9)
        # Headers
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
        pdf.cell(40, row_height, "Value", 1, 0, 'C', True)
        pdf.cell(80, row_height, "Description", 1, 0, 'C', True)
        pdf.ln(row_height)
        
        # Parameter values
        pdf.set_font('Arial', '', 8)
        for key, value in session_state.kinetic_params.items():
            explanation = session_state.kinetic_explanations.get(key, "")
            # Truncate long explanations
            if len(explanation) > 50:
                explanation = explanation[:47] + "..."
                
            pdf.cell(70, row_height, key, 1, 0)
            pdf.cell(40, row_height, f"{value}", 1, 0, 'C')
            pdf.cell(80, row_height, explanation, 1, 0)
            pdf.ln(row_height)
            
            # Check page space, add new page if needed
            if pdf.get_y() > 250:
                pdf.add_page()
        
        pdf.ln(5)
    
    # --- Section 4: Simulation Results ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "4. Simulation Results", 0, 1, 'L')
    
    # --- Section 4.1: COD and Removal Efficiency ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "4.1 COD Values and Removal Efficiency", 0, 1, 'L')
    
    # Create a table for COD values
    pdf.set_font('Arial', 'B', 9)
    # Headers
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(45, row_height, "Parameter", 1, 0, 'C', True)
    for i in range(3):
        if session_state.sim_results[i] and all(session_state.sim_results[i]):
            pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Collect data
    cod_rows = ["Soluble COD (mg/L)", "Particulate COD (mg/L)", "Total COD (mg/L)", "COD Removal (%)"]
    cod_data = []
    
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, inf_i, eff_i, _ = sim_res
            
            # Calculate COD values
            try:
                cod_values = calculate_effluent_COD(eff_i)
                cod_removal = (1 - eff_i.COD/inf_i.COD) * 100
                
                cod_data.append([
                    f"{cod_values['soluble_COD']:.1f}",
                    f"{cod_values['particulate_COD']:.1f}",
                    f"{cod_values['total_COD']:.1f}",
                    f"{cod_removal:.1f}"
                ])
            except:
                cod_data.append(["N/A", "N/A", "N/A", "N/A"])
    
    # Display data
    pdf.set_font('Arial', '', 9)
    for row_idx, row_label in enumerate(cod_rows):
        pdf.cell(45, row_height, row_label, 1, 0)
        for col_idx in range(len(cod_data)):
            pdf.cell(45, row_height, cod_data[col_idx][row_idx], 1, 0, 'C')
        pdf.ln(row_height)
    
    pdf.ln(10)
    
    # --- Section 4.2: Biomass Yields ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "4.2 Biomass Yields", 0, 1, 'L')
    
    # Create a table for biomass yields
    pdf.set_font('Arial', 'B', 9)
    # Headers
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(45, row_height, "Parameter", 1, 0, 'C', True)
    for i in range(3):
        if session_state.sim_results[i] and all(session_state.sim_results[i]):
            pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Collect data
    yield_rows = ["VSS Yield (kg/kg COD)", "TSS Yield (kg/kg COD)"]
    yield_data = []
    
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, inf_i, eff_i, _ = sim_res
            
            # Calculate yields
            try:
                biomass_yields = calculate_biomass_yields(inf_i, eff_i)
                
                yield_data.append([
                    f"{biomass_yields['VSS_yield']:.4f}",
                    f"{biomass_yields['TSS_yield']:.4f}"
                ])
            except:
                yield_data.append(["N/A", "N/A"])
    
    # Display data
    pdf.set_font('Arial', '', 9)
    for row_idx, row_label in enumerate(yield_rows):
        pdf.cell(45, row_height, row_label, 1, 0)
        for col_idx in range(len(yield_data)):
            pdf.cell(45, row_height, yield_data[col_idx][row_idx], 1, 0, 'C')
        pdf.ln(row_height)
    
    pdf.ln(10)
    
    # --- Section 4.3: Biogas Production ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "4.3 Biogas Production", 0, 1, 'L')
    
    # Create a table for gas properties
    pdf.set_font('Arial', 'B', 9)
    # Headers
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(45, row_height, "Parameter", 1, 0, 'C', True)
    for i in range(3):
        if session_state.sim_results[i] and all(session_state.sim_results[i]):
            pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Collect data
    gas_rows = ["Flow (Nm³/d)", "Methane (%)", "CO2 (%)", "H2 (ppmv)"]
    gas_data = []
    
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, _, _, gas_i = sim_res
            
            # Calculate gas properties
            try:
                gas_props = calculate_gas_properties(gas_i)
                
                gas_data.append([
                    f"{gas_props['flow_total']:.2f}",
                    f"{gas_props['methane_percent']:.2f}",
                    f"{gas_props['co2_percent']:.2f}",
                    f"{gas_props['h2_ppmv']:.2f}"
                ])
            except:
                gas_data.append(["N/A", "N/A", "N/A", "N/A"])
    
    # Display data
    pdf.set_font('Arial', '', 9)
    for row_idx, row_label in enumerate(gas_rows):
        pdf.cell(45, row_height, row_label, 1, 0)
        for col_idx in range(len(gas_data)):
            pdf.cell(45, row_height, gas_data[col_idx][row_idx], 1, 0, 'C')
        pdf.ln(row_height)
    
    # --- Section 4.4: Detailed Effluent Composition ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "4.4 Detailed Effluent Composition", 0, 1, 'L')
    
    # Create comparisons for all key ADM1 components
    component_groups = {
        "Soluble Components": ["S_su", "S_aa", "S_fa", "S_va", "S_bu", "S_pro", "S_ac", "S_h2", "S_ch4", "S_IC", "S_IN", "S_I"],
        "Particulate Components": ["X_c", "X_ch", "X_pr", "X_li", "X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2", "X_I"]
    }
    
    # Display each component group in a separate table
    for group_name, components in component_groups.items():
        pdf.set_font('Arial', 'B', 9)
        pdf.ln(5)
        pdf.cell(0, 7, group_name, 0, 1, 'L')
        
        # Create a header row for the comparison table
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(45, row_height, "Component", 1, 0, 'C', True)
        for i in range(3):
            if session_state.sim_results[i] and all(session_state.sim_results[i]):
                pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
        pdf.ln(row_height)
        
        # Create rows for each component
        pdf.set_font('Arial', '', 8)
        for component in components:
            pdf.cell(45, row_height, component, 1, 0)
            
            for i, sim_res in enumerate(session_state.sim_results):
                if sim_res and all(sim_res):
                    _, _, eff_i, _ = sim_res
                    
                    # Try to extract the component concentration
                    try:
                        if component in eff_i.components.IDs:
                            idx = eff_i.components.index(component)
                            # Get final concentration from the last timepoint in the simulation
                            conc = eff_i.scope.record[-1, idx]
                            pdf.cell(45, row_height, f"{conc:.4f}", 1, 0, 'C')
                        else:
                            pdf.cell(45, row_height, "N/A", 1, 0, 'C')
                    except:
                        pdf.cell(45, row_height, "N/A", 1, 0, 'C')
            
            pdf.ln(row_height)
            
            # Check if we need to add a new page
            if pdf.get_y() > 250:
                pdf.add_page()
                # Reprint the header
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(200, 200, 200)
                pdf.cell(45, row_height, "Component", 1, 0, 'C', True)
                for i in range(3):
                    if session_state.sim_results[i] and all(session_state.sim_results[i]):
                        pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
                pdf.ln(row_height)
                pdf.set_font('Arial', '', 8)
    
    # --- Section 5: VFA Dynamics ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "5. VFA Dynamics", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, "This section shows the dynamics of volatile fatty acids (VFAs) over time for each simulation. "
                         "High VFA accumulation can indicate process instability or inhibition.")
    
    # VFA components to track in order of degradation pathway
    vfa_components = ["S_va", "S_bu", "S_pro", "S_ac"]
    vfa_names = ["Valerate", "Butyrate", "Propionate", "Acetate"]
    
    try:
        # Generate a specialized VFA plot
        fig = _generate_vfa_dynamics_for_pdf(session_state, vfa_components, vfa_names)
        if fig:
            # Save figure to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                temp_filename = tmpfile.name
                fig.savefig(temp_filename, dpi=300, bbox_inches='tight')
                plt.close(fig)
            
            # Calculate image dimensions to fit in PDF
            img_width = 180  # mm
            img_height = 120  # mm
            x_pos = (210 - img_width) / 2  # center image (A4 width is 210mm)
            
            # Add image to PDF
            pdf.image(temp_filename, x=x_pos, y=pdf.get_y(), w=img_width, h=img_height)
            
            # Remove temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            # Space after the image
            pdf.ln(img_height + 10)
    except Exception as e:
        pdf.ln(5)
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0, 5, f"Error generating VFA dynamics plot: {str(e)}")
        pdf.set_text_color(0, 0, 0)  # Reset text color
    
    # VFA Accumulation Ratio analysis
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "5.1 VFA Accumulation Ratio", 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, "The ratio of propionate to acetate is a key diagnostic indicator. "
                         "A ratio > 1.4 indicates potential process imbalance. "
                         "The table below shows the final values at the end of each simulation.")
    
    # Create table for VFA ratios
    try:
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(60, row_height, "Parameter", 1, 0, 'C', True)
    for i in range(3):
        if session_state.sim_results[i] and all(session_state.sim_results[i]):
            pdf.cell(40, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
    pdf.ln(row_height)
    
    # Generate VFA ratio data
    pdf.set_font('Arial', '', 9)
    ratio_params = ["Propionate (mg/L)", "Acetate (mg/L)", "Propionate/Acetate Ratio", "Status"]
    
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, _, eff_i, _ = sim_res
            
            # Find indices for the components
            idx_pro = eff_i.components.index("S_pro") if "S_pro" in eff_i.components.IDs else None
            idx_ac = eff_i.components.index("S_ac") if "S_ac" in eff_i.components.IDs else None
            
            if idx_pro is not None and idx_ac is not None:
                # Get final concentrations
                pro_conc = eff_i.scope.record[-1, idx_pro]
                ac_conc = eff_i.scope.record[-1, idx_ac]
                
                # Calculate ratio
                if ac_conc > 0:
                    ratio = pro_conc / ac_conc
                    status = "Imbalanced" if ratio > 1.4 else "Stable"
                else:
                    ratio = "N/A"
                    status = "N/A"
            else:
                pro_conc = "N/A"
                ac_conc = "N/A"
                ratio = "N/A"
                status = "N/A"
            
            # Store data
            if i == 0:
                pdf.cell(60, row_height, ratio_params[0], 1, 0)
                pdf.cell(40, row_height, f"{pro_conc if isinstance(pro_conc, str) else f'{pro_conc:.2f}'}", 1, 0, 'C')
            elif i == len(session_state.sim_results) - 1:
                pdf.cell(40, row_height, f"{pro_conc if isinstance(pro_conc, str) else f'{pro_conc:.2f}'}", 1, 1, 'C')
            else:
                pdf.cell(40, row_height, f"{pro_conc if isinstance(pro_conc, str) else f'{pro_conc:.2f}'}", 1, 0, 'C')
                
    # Repeat for acetate
    pdf.cell(60, row_height, ratio_params[1], 1, 0)
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, _, eff_i, _ = sim_res
            idx_ac = eff_i.components.index("S_ac") if "S_ac" in eff_i.components.IDs else None
            ac_conc = eff_i.scope.record[-1, idx_ac] if idx_ac is not None else "N/A"
            if i == len(session_state.sim_results) - 1:
                pdf.cell(40, row_height, f"{ac_conc if isinstance(ac_conc, str) else f'{ac_conc:.2f}'}", 1, 1, 'C')
            else:
                pdf.cell(40, row_height, f"{ac_conc if isinstance(ac_conc, str) else f'{ac_conc:.2f}'}", 1, 0, 'C')
    
    # Repeat for ratio
    pdf.cell(60, row_height, ratio_params[2], 1, 0)
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, _, eff_i, _ = sim_res
            idx_pro = eff_i.components.index("S_pro") if "S_pro" in eff_i.components.IDs else None
            idx_ac = eff_i.components.index("S_ac") if "S_ac" in eff_i.components.IDs else None
            
            if idx_pro is not None and idx_ac is not None:
                pro_conc = eff_i.scope.record[-1, idx_pro]
                ac_conc = eff_i.scope.record[-1, idx_ac]
                ratio = pro_conc / ac_conc if ac_conc > 0 else "N/A"
            else:
                ratio = "N/A"
                
            if i == len(session_state.sim_results) - 1:
                pdf.cell(40, row_height, f"{ratio if isinstance(ratio, str) else f'{ratio:.2f}'}", 1, 1, 'C')
            else:
                pdf.cell(40, row_height, f"{ratio if isinstance(ratio, str) else f'{ratio:.2f}'}", 1, 0, 'C')
    
    # Repeat for status
    pdf.cell(60, row_height, ratio_params[3], 1, 0)
    for i, sim_res in enumerate(session_state.sim_results):
        if sim_res and all(sim_res):
            _, _, eff_i, _ = sim_res
            idx_pro = eff_i.components.index("S_pro") if "S_pro" in eff_i.components.IDs else None
            idx_ac = eff_i.components.index("S_ac") if "S_ac" in eff_i.components.IDs else None
            
            if idx_pro is not None and idx_ac is not None:
                pro_conc = eff_i.scope.record[-1, idx_pro]
                ac_conc = eff_i.scope.record[-1, idx_ac]
                if ac_conc > 0:
                    ratio = pro_conc / ac_conc
                    status = "Imbalanced" if ratio > 1.4 else "Stable"
                else:
                    status = "N/A"
            else:
                status = "N/A"
                
            if i == len(session_state.sim_results) - 1:
                pdf.cell(40, row_height, status, 1, 1, 'C')
            else:
                pdf.cell(40, row_height, status, 1, 0, 'C')
    
    except Exception as e:
        pdf.ln(5)
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0, 5, f"Error generating VFA ratio table: {str(e)}")
        pdf.set_text_color(0, 0, 0)  # Reset text color
    
    # --- Section 6: Simulation Plots ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "6. Simulation Plots", 0, 1, 'L')
    
    # Plot types to include in the report
    plot_types = [
        "Effluent - Acids",
        "Effluent - Inorganic Carbon",
        "Effluent - Biomass Components",
        "Gas - Methane",
        "Total VFAs"
    ]
    
    for plot_idx, plot_type in enumerate(plot_types):
        try:
            # Generate plot
            fig = _generate_plot_for_pdf(session_state, plot_type)
            if fig is None:
                continue
                
            # Add plot title
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, f"6.{plot_idx+1} {plot_type}", 0, 1, 'L')
            
            # Save figure to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                temp_filename = tmpfile.name
                fig.savefig(temp_filename, dpi=300, bbox_inches='tight')
                plt.close(fig)
            
            # Calculate image dimensions to fit in PDF
            img_width = 180  # mm
            img_height = 120  # mm
            x_pos = (210 - img_width) / 2  # center image (A4 width is 210mm)
            
            # Add image to PDF
            pdf.image(temp_filename, x=x_pos, y=pdf.get_y(), w=img_width, h=img_height)
            
            # Remove temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            # Space after the image
            pdf.ln(img_height + 10)
            
            # Add a new page for the next plot, except for the last one
            if plot_idx < len(plot_types) - 1:
                pdf.add_page()
        except Exception as e:
            pdf.ln(5)
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 5, f"Error generating plot for {plot_type}: {str(e)}")
            pdf.set_text_color(0, 0, 0)  # Reset text color
            
            # Add a new page for the next plot, except for the last one
            if plot_idx < len(plot_types) - 1:
                pdf.add_page()
    
    # Return PDF as BytesIO object
    try:
        pdf_output = BytesIO()
        pdf_output.write(pdf.output(dest='S').encode('latin1'))
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        st.error(f"Error creating PDF file: {str(e)}")
        return None
    
except Exception as e:
    st.error(f"Error generating PDF report: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    return None


def _generate_vfa_dynamics_for_pdf(session_state, vfa_components, vfa_names):
    """
    Generate a specialized plot showing VFA dynamics for each simulation
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    vfa_components : list
        List of VFA component IDs to plot
    vfa_names : list
        List of readable names for the VFA components
    
    Returns
    -------
    matplotlib.figure.Figure or None
        Generated figure or None if no data available
    """
    try:
        # Check if any simulation has run
        any_sim_ran = any([res is not None and all(res) for res in session_state.sim_results])
        if not any_sim_ran:
            return None
        
        # Create a multi-panel figure - one subplot for each simulation
        fig, axes = plt.subplots(3, 1, figsize=(10, 15), sharex=True)
        plt.subplots_adjust(hspace=0.3)
        
        # Color cycle for different VFAs
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        # Keep track of which simulations have data
        valid_sims = 0
        
        # Iterate through simulations
        for i, (sys_i, inf_i, eff_i, _) in enumerate(session_state.sim_results):
            if not sys_i or not inf_i or not eff_i:
                continue
                
            ax = axes[i]
            valid_sims += 1
            
            t_stamp_eff = eff_i.scope.time_series
            cmps_obj = inf_i.components
            
            # Set title for this simulation subplot
            ax.set_title(f"Simulation {i+1}: HRT = {session_state.sim_params[i].get('HRT', 'N/A')} days, T = {session_state.sim_params[i].get('Temp', 'N/A')} K")
            
            # Plot each VFA on this subplot
            for j, (vfa_id, vfa_name) in enumerate(zip(vfa_components, vfa_names)):
                if vfa_id in cmps_obj.IDs:
                    idx = cmps_obj.index(vfa_id)
                    data = eff_i.scope.record[:, idx]
                    ax.plot(t_stamp_eff, data, label=vfa_name, color=colors[j])
            
            # Calculate and plot total VFAs
            try:
                vfa_indices = [cmps_obj.index(vfa) for vfa in vfa_components if vfa in cmps_obj.IDs]
                if vfa_indices:
                    vfa_matrix = eff_i.scope.record[:, vfa_indices]
                    total_vfa = np.sum(vfa_matrix, axis=1)
                    ax.plot(t_stamp_eff, total_vfa, label="Total VFAs", color='black', linestyle='--', linewidth=2)
            except:
                pass
                
            # Customize plot
            ax.set_ylabel("Concentration [mg/L]")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(loc='upper right')
        
        # If no valid simulations, return None
        if valid_sims == 0:
            plt.close(fig)
            return None
            
        # Set common x-axis label
        axes[-1].set_xlabel("Time [days]")
        
        # Set main figure title
        fig.suptitle("VFA Dynamics Across Simulations", fontsize=16, y=0.99)
        
        # Tight layout (but maintain space for suptitle)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        
        return fig
    except Exception as e:
        print(f"Error generating VFA dynamics plot: {str(e)}")
        return None


def _generate_plot_for_pdf(session_state, plot_type):
    """
    Generate a matplotlib figure for inclusion in PDF report
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    plot_type : str
        Type of plot to generate
        
    Returns
    -------
    matplotlib.figure.Figure or None
        Generated figure or None if no data available
    """
    try:
        # Check if any simulation has run
        any_sim_ran = any([res is not None and all(res) for res in session_state.sim_results])
        if not any_sim_ran:
            return None
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Color cycle for different simulations
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        # Line styles for different components
        line_styles = ['-', '--', ':', '-.', '-', '--', ':']
        
        # Keep track of whether we added any data to the plot
        has_data = False
        
        for i, (sys_i, inf_i, eff_i, gas_i) in enumerate(session_state.sim_results):
            if not sys_i or not inf_i or not eff_i or not gas_i:
                continue
                
            t_stamp_eff = eff_i.scope.time_series
            t_stamp_gas = gas_i.scope.time_series
            cmps_obj = inf_i.components
            
            # Process according to the plot type
            if plot_type == "Effluent - Acids":
                acid_list = ['S_su','S_aa','S_fa','S_va','S_bu','S_pro','S_ac']
                for j, acid in enumerate(acid_list):
                    if acid in cmps_obj.IDs:
                        idx = cmps_obj.index(acid)
                        data_acid = eff_i.scope.record[:, idx]
                        ax.plot(t_stamp_eff, data_acid, 
                                label=f"{acid} (Sim {i+1})",
                                color=colors[i],
                                linestyle=line_styles[j % len(line_styles)])
                        has_data = True
                    
            elif plot_type == "Effluent - Inorganic Carbon":
                if 'S_IC' in cmps_obj.IDs:
                    idx = cmps_obj.index('S_IC')
                    data_ic = eff_i.scope.record[:, idx]
                    ax.plot(t_stamp_eff, data_ic,
                            label=f"S_IC (Sim {i+1})",
                            color=colors[i])
                    has_data = True
                    
            elif plot_type == "Effluent - Biomass Components":
                bio_list = ['X_su','X_aa','X_fa','X_c4','X_pro','X_ac','X_h2']
                for j, bio in enumerate(bio_list):
                    if bio in cmps_obj.IDs:
                        idx = cmps_obj.index(bio)
                        data_bio = eff_i.scope.record[:, idx]
                        ax.plot(t_stamp_eff, data_bio,
                                label=f"{bio} (Sim {i+1})",
                                color=colors[i],
                                linestyle=line_styles[j % len(line_styles)])
                        has_data = True
                    
            elif plot_type == "Gas - Hydrogen":
                if 'S_h2' in cmps_obj.IDs:
                    idx = cmps_obj.index('S_h2')
                    data_h2 = gas_i.scope.record[:, idx]
                    ax.plot(t_stamp_gas, data_h2,
                            label=f"S_h2 (Sim {i+1})",
                            color=colors[i])
                    has_data = True
                    
            elif plot_type == "Gas - Methane":
                if 'S_ch4' in cmps_obj.IDs and 'S_IC' in cmps_obj.IDs:
                    idx_ch4 = cmps_obj.index('S_ch4')
                    idx_ic = cmps_obj.index('S_IC')
                    data_ch4 = gas_i.scope.record[:, idx_ch4]
                    data_ic = gas_i.scope.record[:, idx_ic]
                    ax.plot(t_stamp_gas, data_ch4,
                            label=f"S_ch4 (Sim {i+1})",
                            color=colors[i],
                            linestyle='-')
                    ax.plot(t_stamp_gas, data_ic,
                            label=f"S_IC (Sim {i+1})",
                            color=colors[i],
                            linestyle='--')
                    has_data = True
                    
            elif plot_type == "Total VFAs":
                vfa_list = ['S_va','S_bu','S_pro','S_ac']
                vfa_indices = [cmps_obj.index(vfa) for vfa in vfa_list if vfa in cmps_obj.IDs]
                
                if vfa_indices:
                    vfa_matrix = eff_i.scope.record[:, vfa_indices]
                    total_vfa = np.sum(vfa_matrix, axis=1)
                    ax.plot(t_stamp_eff, total_vfa,
                            label=f"Total VFAs (Sim {i+1})",
                            color=colors[i])
                    has_data = True
        
        # If no data was added to the plot, return None
        if not has_data:
            plt.close(fig)
            return None
            
        # Set plot labels and title
        ax.set_xlabel('Time [d]')
        ax.set_ylabel('Concentration [mg/L]')
        ax.set_title(plot_type)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend outside the plot area
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        
        # Tight layout
        fig.tight_layout()
        
        return fig
    except Exception as e:
        print(f"Error generating {plot_type} plot: {str(e)}")
        return None


def render_pdf_export_button(session_state):
    """
    Render a button to generate and download a PDF report

    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    if st.button("Export Complete PDF Report"):
        try:
            with st.spinner("Generating comprehensive PDF report..."):
                pdf_data = generate_pdf_report(session_state)
                
                if pdf_data:
                    # Provide download button for the PDF
                    st.success("PDF report generated successfully!")
                    st.download_button(
                        label="Download Simulation Report (PDF)",
                        data=pdf_data,
                        file_name="adm1_simulation_report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate PDF report. Please check if simulations have been run.")
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
