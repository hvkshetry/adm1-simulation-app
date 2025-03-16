"""
Enhanced PDF Export functionality for ADM1 simulation results with AI-generated narratives
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
import google.generativeai as genai
from dotenv import load_dotenv

# Import from other modules
from puran_adm1.models.adm1_simulation import calculate_biomass_yields, calculate_effluent_COD, calculate_gas_properties
from puran_adm1.components.inhibition_display import calculate_inhibition_factors

# Load environment variables for Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def replace_unicode_chars(text):
    """
    Replace Unicode characters that can't be encoded in latin-1 with ASCII equivalents
    
    Parameters
    ----------
    text : str
        Text to process
        
    Returns
    -------
    str
        Text with Unicode characters replaced
    """
    if not isinstance(text, str):
        return text
        
    # Define replacements for problematic characters
    replacements = {
        '\u2080': '0',  # subscript 0
        '\u2081': '1',  # subscript 1
        '\u2082': '2',  # subscript 2
        '\u2083': '3',  # subscript 3
        '\u2084': '4',  # subscript 4
        '\u2085': '5',  # subscript 5
        '\u2086': '6',  # subscript 6
        '\u2087': '7',  # subscript 7
        '\u2088': '8',  # subscript 8
        '\u2089': '9',  # subscript 9
        '\u2090': 'a',  # subscript a
        '\u2091': 'e',  # subscript e
        '\u2092': 'o',  # subscript o
        '\u2093': 'x',  # subscript x
        '\u2095': 'h',  # subscript h
        '\u2096': 'k',  # subscript k
        '\u2097': 'l',  # subscript l
        '\u2098': 'm',  # subscript m
        '\u2099': 'n',  # subscript n
        '\u00B2': '2',  # superscript 2
        '\u00B3': '3',  # superscript 3
        '\u2074': '4',  # superscript 4
        '\u2075': '5',  # superscript 5
        '\u2076': '6',  # superscript 6
        '\u2077': '7',  # superscript 7
        '\u2078': '8',  # superscript 8
        '\u2079': '9',  # superscript 9
        '\u207A': '+',  # superscript +
        '\u207B': '-',  # superscript -
        '\u207C': '=',  # superscript =
        '\u207D': '(',  # superscript (
        '\u207E': ')',  # superscript )
        '\u207F': 'n',  # superscript n
        '\u00B0': 'deg',  # degree symbol
        '\u03B1': 'alpha',  # alpha
        '\u03B2': 'beta',  # beta
        '\u03B3': 'gamma',  # gamma
        '\u03B4': 'delta',  # delta
        '\u03B5': 'epsilon',  # epsilon
        '\u03B6': 'zeta',  # zeta
        '\u03B7': 'eta',  # eta
        '\u03B8': 'theta',  # theta
        '\u03B9': 'iota',  # iota
        '\u03BA': 'kappa',  # kappa
        '\u03BB': 'lambda',  # lambda
        '\u03BC': 'mu',  # mu
        '\u03BD': 'nu',  # nu
        '\u03BE': 'xi',  # xi
        '\u03BF': 'omicron',  # omicron
        '\u03C0': 'pi',  # pi
        '\u03C1': 'rho',  # rho
        '\u03C2': 'final sigma',  # final sigma
        '\u03C3': 'sigma',  # sigma
        '\u03C4': 'tau',  # tau
        '\u03C5': 'upsilon',  # upsilon
        '\u03C6': 'phi',  # phi
        '\u03C7': 'chi',  # chi
        '\u03C8': 'psi',  # psi
        '\u03C9': 'omega',  # omega
    }
    
    # Replace special characters
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Replace common chemical formulas with ASCII versions
    text = text.replace('CO₂', 'CO2')
    text = text.replace('H₂', 'H2')
    text = text.replace('CH₄', 'CH4')
    text = text.replace('NH₃', 'NH3')
    text = text.replace('N₂', 'N2')
    text = text.replace('O₂', 'O2')
    text = text.replace('H₂O', 'H2O')
    text = text.replace('H₂S', 'H2S')
    
    # Try to encode and decode to catch any remaining problematic characters
    try:
        return text.encode('latin-1').decode('latin-1')
    except UnicodeEncodeError:
        # If there are still problematic characters, replace them with '?'
        return text.encode('latin-1', errors='replace').decode('latin-1')


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
    
    # Override multi_cell method to handle Unicode character encoding
    def multi_cell(self, w, h, txt='', border=0, align='J', fill=False):
        # Safely handle Unicode characters by replacing them with ASCII equivalents
        txt = replace_unicode_chars(txt)
        super().multi_cell(w, h, txt, border, align, fill)
    
    # Override cell method to handle Unicode character encoding
    def cell(self, w, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        # Safely handle Unicode characters by replacing them with ASCII equivalents
        txt = replace_unicode_chars(txt)
        super().cell(w, h, txt, border, ln, align, fill, link)


def generate_ai_narrative(prompt, max_retries=3):
    """
    Generate a narrative using Gemini
    
    Parameters
    ----------
    prompt : str
        Prompt for Gemini
    max_retries : int, optional
        Maximum number of retries, by default 3
        
    Returns
    -------
    str
        Generated narrative or error message
    """
    if not GEMINI_API_KEY:
        return "API key for Gemini not found. Narrative generation is not available."
    
    # Make sure the prompt doesn't have any problematic Unicode characters
    prompt = replace_unicode_chars(prompt)
    
    retries = 0
    while retries < max_retries:
        try:
            model = genai.GenerativeModel(model_name="gemini-2.0-pro-exp-02-05")
            response = model.generate_content(prompt)
            return replace_unicode_chars(response.text)
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                return f"Error generating narrative: {str(e)}"
            time.sleep(1)  # Wait before retrying


def get_feedstock_narrative(feedstock_description, influent_values):
    """
    Generate a narrative description of the feedstock
    
    Parameters
    ----------
    feedstock_description : str
        User-provided description of the feedstock
    influent_values : dict
        Dictionary of influent values
        
    Returns
    -------
    str
        Narrative description of the feedstock
    """
    # Format the influent values for the prompt
    influent_str = "ADM1 State Variables:\n"
    for key, value in influent_values.items():
        influent_str += f"{key}: {value} kg/m³\n"
    
    prompt = f"""
    You are an expert in anaerobic digestion and wastewater treatment. Please provide a comprehensive 
    description of the following feedstock for an Anaerobic Digestion Model No. 1 (ADM1) simulation.
    
    User's description: {feedstock_description}
    
    Here are the ADM1 state variables that were set up for this feedstock:
    {influent_str}
    
    Write a 2-3 paragraph technical description of this feedstock, explaining:
    1. The general composition and characteristics
    2. Its suitability for anaerobic digestion
    3. Expected challenges or benefits for the digestion process
    4. Typical biodegradability and methane potential
    
    Be specific, technical, and informative in your description. Remember that this is an initial screening of this feedstock as a candidate for anaerobic digestion using the ADM1 model and not data from an operating digester - your narrative should be written with this in mind.
    """
    
    return generate_ai_narrative(prompt)


def get_process_health_narrative(inhibition_data, sim_params):
    """
    Generate a narrative description of the process health
    
    Parameters
    ----------
    inhibition_data : dict
        Dictionary containing inhibition factors
    sim_params : dict
        Dictionary of simulation parameters
        
    Returns
    -------
    str
        Narrative description of process health
    """
    if inhibition_data is None:
        return "Insufficient data to generate process health narrative."
    
    # Process names and their importance
    process_names = [
        "Sugar Uptake", "Amino Acid Uptake", "LCFA Uptake", "Valerate Uptake",
        "Butyrate Uptake", "Propionate Uptake", "Acetate Uptake", "H2 Uptake"
    ]
    
    # Get inhibition factors
    pH_inhibition = inhibition_data['pH_Inhibition']
    h2_inhibition = inhibition_data.get('H2_Inhibition', [1, 1, 1, 1])
    n_limitation = inhibition_data.get('Nitrogen_Limitation', 1)
    nh3_inhibition = inhibition_data.get('Ammonia_Inhibition', 1)
    substrate_limitation = inhibition_data.get('Substrate_Limitation', [1, 1, 1, 1, 1, 1, 1, 1])
    process_rates = inhibition_data.get('Process_Rates', [0, 0, 0, 0, 0, 0, 0, 0])
    pH_value = inhibition_data.get('pH_Value', 7.0)
    
    # Calculate inhibition degree (0-100%)
    def inhibition_degree(factor):
        return (1 - factor) * 100
    
    # Create expanded inhibition factors to match process names length
    h2_inhibition_expanded = [1.0, 1.0, h2_inhibition[0], h2_inhibition[1], 
                            h2_inhibition[2], h2_inhibition[3], 1.0, 1.0]
    
    nh3_inhibition_expanded = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, nh3_inhibition, 1.0]
    
    # Calculate overall inhibition
    overall_inhibition_no_substrate = []
    for i, process in enumerate(process_names):
        # Each inhibition factor is between 0-1, where 1 means no inhibition
        if i == 6:  # Acetate uptake affected by ammonia
            no_substrate = pH_inhibition[i] * n_limitation * nh3_inhibition
        elif i in [2, 3, 4, 5]:  # LCFA, valerate, butyrate, propionate uptake affected by H2
            no_substrate = pH_inhibition[i] * n_limitation * h2_inhibition_expanded[i]
        else:  # Other processes
            no_substrate = pH_inhibition[i] * n_limitation
        overall_inhibition_no_substrate.append(no_substrate)
    
    # Calculate maximum inhibition
    inhibition_values = [inhibition_degree(x) for x in overall_inhibition_no_substrate]
    max_inhibition = max(inhibition_values)
    max_inhibition_process = process_names[inhibition_values.index(max_inhibition)]
    
    # Safety margin calculations
    safety_margin_values = [inhibition_degree(x) for x in substrate_limitation]
    min_safety_margin = min(safety_margin_values) if safety_margin_values else 0
    min_safety_idx = safety_margin_values.index(min_safety_margin) if safety_margin_values else 0
    min_safety_margin_process = process_names[min_safety_idx]
    
    # Format inhibition data for the prompt
    inhibition_str = f"""
    Simulation Parameters:
    - Temperature: {sim_params.get('Temp', 'N/A')} K
    - HRT: {sim_params.get('HRT', 'N/A')} days
    
    Process Health Indicators:
    - Current pH: {pH_value:.2f}
    - Maximum Inhibition: {max_inhibition:.1f}% (in {max_inhibition_process})
    - Safety Margin: {min_safety_margin:.1f}% substrate limitation (in {min_safety_margin_process})
    
    Inhibition Factors:
    - pH Inhibition: {[f"{inhibition_degree(x):.1f}%" for x in pH_inhibition]}
    - H2 Inhibition: {[f"{inhibition_degree(x):.1f}%" for x in h2_inhibition]}
    - N Limitation: {inhibition_degree(n_limitation):.1f}%
    - NH3 Inhibition: {inhibition_degree(nh3_inhibition):.1f}%
    """
    
    prompt = f"""
    You are an expert in anaerobic digestion process monitoring and troubleshooting.
    
    Based on the following inhibition data from an Anaerobic Digestion Model No. 1 (ADM1) simulation,
    provide a comprehensive 2-3 paragraph analysis of the reactor's health and stability.

    **NOTE THE FOLLOWING**

    "Substrate limitation" has been termed "safety margin". For "Substrate limitation", high percentages suggested large room for the substrate concentration to grow without "saturating" the biomass 
    (i.e. the typical Monod kinetic equation).  So higher values indicate higher reserves and better protection against shock loads and inhibitors. These higher values indicate higher reserves and better protection against shock loads and inhibitors.


    
    {inhibition_str}
    
    Your analysis should include:
    
    1. An overall assessment of the reactor's health and stability
    2. Identification of any significant inhibition factors and their potential causes
    3. An explanation of the safety margin and its implications for process stability
    4. Specific recommendations for optimizing reactor performance
    
    Be concise, technical, and provide actionable insights. Remember that this is an initial screening of this feedstock as a candidate for anaerobic digestion using the ADM1 model and not data from an operating digester - your narrative should be written with this in mind.

    Unless VFA accumulation is occuring, the digester health should be considered stable - however, high levels of inhibition should be highlighted as potentially risky if substrate utilization approaches 100% (i.e. safety margin approaches 0%).
    """
    
    return generate_ai_narrative(prompt)


def get_simulation_results_narrative(inf_stream, eff_stream, gas_stream, sim_params):
    """
    Generate a narrative description of the simulation results
    
    Parameters
    ----------
    inf_stream : WasteStream
        Influent stream
    eff_stream : WasteStream
        Effluent stream
    gas_stream : WasteStream
        Gas stream
    sim_params : dict
        Dictionary of simulation parameters
        
    Returns
    -------
    str
        Narrative description of simulation results
    """
    try:
        # Calculate key performance metrics
        cod_values = calculate_effluent_COD(eff_stream)
        cod_removal = (1 - eff_stream.COD/inf_stream.COD) * 100
        biomass_yields = calculate_biomass_yields(inf_stream, eff_stream)
        gas_props = calculate_gas_properties(gas_stream)
        
        # Format data for the prompt
        results_str = f"""
        Simulation Parameters:
        - Temperature: {sim_params.get('Temp', 'N/A')} K
        - HRT: {sim_params.get('HRT', 'N/A')} days
        
        Performance Metrics:
        - Influent COD: {inf_stream.COD:.1f} mg/L
        - Effluent COD: {eff_stream.COD:.1f} mg/L
        - COD Removal Efficiency: {cod_removal:.1f}%
        - Soluble COD: {cod_values['soluble_COD']:.1f} mg/L
        - Particulate COD: {cod_values['particulate_COD']:.1f} mg/L
        
        Biomass Yields:
        - VSS Yield: {biomass_yields['VSS_yield']:.4f} kg VSS/kg COD
        - TSS Yield: {biomass_yields['TSS_yield']:.4f} kg TSS/kg COD
        
        Biogas Production:
        - Total Flow: {gas_props['flow_total']:.2f} Nm3/d
        - Methane Content: {gas_props['methane_percent']:.2f}%
        - CO2 Content: {gas_props['co2_percent']:.2f}%
        - H2 Content: {gas_props['h2_ppmv']:.2f} ppmv
        """
        
        prompt = f"""
        You are an expert in anaerobic digestion process engineering and modeling.
        
        Based on the following results from an Anaerobic Digestion Model No. 1 (ADM1) simulation,
        provide a concise 2-paragraph technical analysis of the performance.
        
        {results_str}
        
        Your analysis should include:
        
        1. An evaluation of the overall performance (COD removal, biogas production)
        2. An assessment of the methane content and its implications
        3. Comments on the biomass yields and what they indicate
        4. Brief recommendations for optimization if applicable
        
        Keep your analysis concise, technical, and focused on the key performance indicators. Remember that this is an initial screening of this feedstock as a candidate for anaerobic digestion using the ADM1 model and not data from an operating digester - your narrative should be written with this in mind.
        """
        
        return generate_ai_narrative(prompt)
    except Exception as e:
        return f"Error generating simulation results narrative: {str(e)}"


def generate_pdf_report(session_state, filename="adm1_simulation_report.pdf"):
    """
    Generate a comprehensive PDF report of all simulation inputs, results, and plots
    with AI-generated narratives
    
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
        
        # --- Section 2: Feedstock Description (AI-Generated) ---
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "2. Feedstock Description", 0, 1, 'L')
        
        # Generate feedstock narrative with Gemini
        from puran_adm1.models.adm1_simulation import create_influent_stream
        try:
            # Create temporary stream to analyze
            temp_inf = create_influent_stream(
                Q=session_state.Q,
                Temp=308.15,
                concentrations=session_state.influent_values
            )
            
            feedstock_description = session_state.get('ai_recommendations', "No feedstock description provided.")
            if feedstock_description and len(feedstock_description) > 10:
                # Get AI narrative about the feedstock
                narrative = get_feedstock_narrative(feedstock_description, session_state.influent_values)
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, narrative)
            else:
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, "No detailed feedstock description available. The simulation is using the specified ADM1 parameters without additional context.")
        except Exception as e:
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Error generating feedstock description: {str(e)}")
        
        pdf.ln(5)
        
        # --- Section 3: Influent Characteristics ---
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "3. Influent Characteristics", 0, 1, 'L')
        
        # Create temporary influent stream to display all properties
        try:
            temp_inf = create_influent_stream(
                Q=session_state.Q,
                Temp=308.15,
                concentrations=session_state.influent_values
            )
            
            # Display composite stream characteristics instead of individual state variables
            row_height = 6
            pdf.set_font('Arial', 'B', 10)
            
            # Basic Parameters
            pdf.cell(0, 8, "Basic Parameters", 0, 1, 'L')
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
            pdf.cell(70, row_height, "Value", 1, 0, 'C', True)
            pdf.ln(row_height)
            pdf.set_font('Arial', '', 9)
            
            # Add basic parameters
            basic_params = [
                ("Flow", f"{temp_inf.get_total_flow('m3/d'):.2f} m³/d"),
                ("pH", f"{getattr(temp_inf, 'pH', 'N/A')}"),
                ("Alkalinity", f"{getattr(temp_inf, 'SAlk', 'N/A')} meq/L")
            ]
            for param, value in basic_params:
                pdf.cell(70, row_height, param, 1, 0)
                pdf.cell(70, row_height, value, 1, 0)
                pdf.ln(row_height)
            
            pdf.ln(5)
            
            # Oxygen Demand Parameters
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Oxygen Demand", 0, 1, 'L')
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
            pdf.cell(70, row_height, "Value", 1, 0, 'C', True)
            pdf.ln(row_height)
            pdf.set_font('Arial', '', 9)
            
            # Safe composite function
            def safe_composite(stream, param, particle_size=None, organic=None, volatile=None, subgroup=None):
                try:
                    if hasattr(stream, 'composite'):
                        if param == 'solids' and particle_size is None:
                            particulate = stream.composite('solids', particle_size='x')
                            colloidal = stream.composite('solids', particle_size='c')
                            return particulate + colloidal
                        return stream.composite(param, particle_size=particle_size, 
                                            organic=organic, volatile=volatile, 
                                            subgroup=subgroup)
                    return 'N/A'
                except:
                    return 'N/A'
            
            # Add oxygen demand parameters
            od_params = [
                ("COD", safe_composite(temp_inf, 'COD')),
                ("BOD", safe_composite(temp_inf, 'BOD')),
                ("uBOD", getattr(temp_inf, 'uBOD', safe_composite(temp_inf, 'uBOD')))
            ]
            for param, value in od_params:
                pdf.cell(70, row_height, param, 1, 0)
                if isinstance(value, (int, float)):
                    pdf.cell(70, row_height, f"{value:,.1f} mg/L", 1, 0)
                else:
                    pdf.cell(70, row_height, "N/A", 1, 0)
                pdf.ln(row_height)
            
            pdf.ln(5)
            
            # Carbon Parameters
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Carbon Content", 0, 1, 'L')
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
            pdf.cell(70, row_height, "Value", 1, 0, 'C', True)
            pdf.ln(row_height)
            pdf.set_font('Arial', '', 9)
            
            # Add carbon parameters
            carbon_params = [
                ("TC", getattr(temp_inf, 'TC', safe_composite(temp_inf, 'C'))),
                ("TOC", getattr(temp_inf, 'TOC', safe_composite(temp_inf, 'C', organic=True)))
            ]
            for param, value in carbon_params:
                pdf.cell(70, row_height, param, 1, 0)
                if isinstance(value, (int, float)):
                    pdf.cell(70, row_height, f"{value:,.1f} mg/L", 1, 0)
                else:
                    pdf.cell(70, row_height, "N/A", 1, 0)
                pdf.ln(row_height)
            
            pdf.ln(5)
            
            # Nitrogen Parameters
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Nitrogen Content", 0, 1, 'L')
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
            pdf.cell(70, row_height, "Value", 1, 0, 'C', True)
            pdf.ln(row_height)
            pdf.set_font('Arial', '', 9)
            
            # Helper function to get component concentrations
            def get_component_conc(stream, component_id):
                try:
                    if component_id not in stream.components.IDs:
                        return "N/A"
                    
                    if hasattr(stream, 'get_mass_concentration'):
                        try:
                            concentrations = stream.get_mass_concentration(IDs=[component_id])
                            return concentrations[0]
                        except:
                            pass
                    
                    if hasattr(stream, 'iconc'):
                        try:
                            return stream.iconc[component_id]
                        except:
                            pass
                            
                    if hasattr(stream, 'mass'):
                        if stream.F_vol > 0:
                            try:
                                return stream.imass[component_id] * 1000 / stream.F_vol  # kg/m3 to mg/L
                            except:
                                pass
                    
                    if hasattr(stream, 'state') and stream.state is not None:
                        try:
                            idx = stream.components.index(component_id)
                            if idx < len(stream.state) - 1:  # -1 for flow at the end
                                return stream.state[idx]
                        except:
                            pass
                            
                    return "N/A"
                except:
                    return "N/A"
            
            # Map ADM1 component names to nitrogen species
            ammonia_component = 'S_NH4' if 'S_NH4' in temp_inf.components.IDs else 'S_IN'
            nitrite_component = 'S_NO2' if 'S_NO2' in temp_inf.components.IDs else None
            nitrate_component = 'S_NO3' if 'S_NO3' in temp_inf.components.IDs else None
            
            # Get nitrogen component concentrations
            ammonia_conc = get_component_conc(temp_inf, ammonia_component)
            nitrite_conc = get_component_conc(temp_inf, nitrite_component) if nitrite_component else 0.0
            nitrate_conc = get_component_conc(temp_inf, nitrate_component) if nitrate_component else 0.0
            
            # Add nitrogen parameters
            nitrogen_params = [
                ("TN", safe_composite(temp_inf, 'N')),
                ("TKN", getattr(temp_inf, 'TKN', 'N/A')),
                ("Ammonia-N", ammonia_conc),
                ("Nitrite-N", nitrite_conc),
                ("Nitrate-N", nitrate_conc)
            ]
            for param, value in nitrogen_params:
                pdf.cell(70, row_height, param, 1, 0)
                if isinstance(value, (int, float)):
                    pdf.cell(70, row_height, f"{value:,.1f} mg/L", 1, 0)
                else:
                    pdf.cell(70, row_height, "N/A", 1, 0)
                pdf.ln(row_height)
            
            pdf.ln(5)
            
            # Solids Parameters
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Solids Content", 0, 1, 'L')
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(70, row_height, "Parameter", 1, 0, 'C', True)
            pdf.cell(70, row_height, "Value", 1, 0, 'C', True)
            pdf.ln(row_height)
            pdf.set_font('Arial', '', 9)
            
            # Safe function for methods
            def safe_get(stream, method_name, *args, **kwargs):
                try:
                    if hasattr(stream, method_name):
                        method = getattr(stream, method_name)
                        if callable(method):
                            return method(*args, **kwargs)
                    return 'N/A'
                except:
                    return 'N/A'
            
            # Calculate solids values
            tss_value = safe_composite(temp_inf, 'solids')
            vss_value = safe_get(temp_inf, 'get_VSS')
            iss_value = safe_get(temp_inf, 'get_ISS')
            tds_value = safe_get(temp_inf, 'get_TDS', include_colloidal=False)
            
            # Add solids parameters
            solids_params = [
                ("TSS", tss_value),
                ("VSS", vss_value),
                ("ISS", iss_value),
                ("TDS", tds_value),
                ("TS", getattr(temp_inf, 'dry_mass', 'N/A'))
            ]
            for param, value in solids_params:
                pdf.cell(70, row_height, param, 1, 0)
                if isinstance(value, (int, float)):
                    pdf.cell(70, row_height, f"{value:,.1f} mg/L", 1, 0)
                else:
                    pdf.cell(70, row_height, "N/A", 1, 0)
                pdf.ln(row_height)
                
        except Exception as e:
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Error displaying influent characteristics: {str(e)}")
        
        pdf.ln(5)
        
        # --- Section 4: Simulation Results ---
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "4. Simulation Results", 0, 1, 'L')
        
        # --- Section 4.1: Results Overview ---
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, "4.1 Results Overview", 0, 1, 'L')
        
        # Generate comparison tables for COD removal and biogas production
        # COD Removal
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(45, row_height, "Parameter", 1, 0, 'C', True)
        for i in range(3):
            if session_state.sim_results[i] and all(session_state.sim_results[i]):
                pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
        pdf.ln(row_height)
        
        # Collect data
        cod_rows = ["Influent COD (mg/L)", "Effluent COD (mg/L)", "COD Removal (%)"]
        cod_data = []
        
        for i, sim_res in enumerate(session_state.sim_results):
            if sim_res and all(sim_res):
                _, inf_i, eff_i, _ = sim_res
                
                # Calculate COD values
                try:
                    inf_cod = inf_i.COD
                    eff_cod = eff_i.COD
                    cod_removal = (1 - eff_i.COD/inf_i.COD) * 100
                    
                    cod_data.append([
                        f"{inf_cod:.1f}",
                        f"{eff_cod:.1f}",
                        f"{cod_removal:.1f}"
                    ])
                except:
                    cod_data.append(["N/A", "N/A", "N/A"])
        
        # Display data
        pdf.set_font('Arial', '', 9)
        for row_idx, row_label in enumerate(cod_rows):
            pdf.cell(45, row_height, row_label, 1, 0)
            for col_idx in range(len(cod_data)):
                pdf.cell(45, row_height, cod_data[col_idx][row_idx], 1, 0, 'C')
            pdf.ln(row_height)
        
        pdf.ln(10)
        
        # Biogas Production
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, "Biogas Production", 0, 1, 'L')
        
        # Create a table for gas properties
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(45, row_height, "Parameter", 1, 0, 'C', True)
        for i in range(3):
            if session_state.sim_results[i] and all(session_state.sim_results[i]):
                pdf.cell(45, row_height, f"Simulation {i+1}", 1, 0, 'C', True)
        pdf.ln(row_height)
        
        # Collect data
        gas_rows = ["Flow (Nm³/d)", "Methane (%)", "CO2 (%)"]
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
                        f"{gas_props['co2_percent']:.2f}"
                    ])
                except:
                    gas_data.append(["N/A", "N/A", "N/A"])
        
        # Display data
        pdf.set_font('Arial', '', 9)
        for row_idx, row_label in enumerate(gas_rows):
            pdf.cell(45, row_height, row_label, 1, 0)
            for col_idx in range(len(gas_data)):
                pdf.cell(45, row_height, gas_data[col_idx][row_idx], 1, 0, 'C')
            pdf.ln(row_height)
        
        pdf.ln(10)
        
        # Add Biomass Yield table
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, "Biomass Yield", 0, 1, 'L')
        
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
        yield_rows = ["VSS Yield (kgVSS/kgCODr)", "TSS Yield (kgTSS/kgCODr)"]
        yield_data = []
        
        for i, sim_res in enumerate(session_state.sim_results):
            if sim_res and all(sim_res):
                _, inf_i, eff_i, _ = sim_res
                
                # Calculate yields
                try:
                    biomass_yields = calculate_biomass_yields(inf_i, eff_i)
                    
                    yield_data.append([
                        f"{biomass_yields['VSS_yield']:.3f}",
                        f"{biomass_yields['TSS_yield']:.3f}"
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
        
        # Generate AI narrative for each simulation's results
        for i, sim_res in enumerate(session_state.sim_results):
            if sim_res and all(sim_res):
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 10, f"Simulation {i+1} Analysis", 0, 1, 'L')
                
                # Generate narrative for this simulation
                try:
                    sys_i, inf_i, eff_i, gas_i = sim_res
                    sim_params = session_state.sim_params[i]
                    
                    narrative = get_simulation_results_narrative(inf_i, eff_i, gas_i, sim_params)
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, narrative)
                    pdf.ln(5)
                except Exception as e:
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, f"Error generating simulation narrative: {str(e)}")
                    pdf.ln(5)
        
        # --- Section 5: Process Health Analysis ---
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "5. Process Health Analysis", 0, 1, 'L')
        
        # For each simulation, generate inhibition dashboard snapshot
        for i, sim_res in enumerate(session_state.sim_results):
            if sim_res and all(sim_res):
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 10, f"5.{i+1} Simulation {i+1} Process Health", 0, 1, 'L')
                
                # Get inhibition data for this simulation
                try:
                    sys_i, inf_i, eff_i, gas_i = sim_res
                    inhibition_data = calculate_inhibition_factors(None, simulation_results=sim_res)
                    
                    if inhibition_data:
                        # Process health summary data
                        process_names = [
                            "Sugar Uptake", "Amino Acid Uptake", "LCFA Uptake", "Valerate Uptake",
                            "Butyrate Uptake", "Propionate Uptake", "Acetate Uptake", "H2 Uptake"
                        ]
                        
                        # Process-specific inhibition factors
                        pH_inhibition = inhibition_data['pH_Inhibition']
                        h2_inhibition = inhibition_data['H2_Inhibition']
                        n_limitation = inhibition_data['Nitrogen_Limitation']
                        nh3_inhibition = inhibition_data['Ammonia_Inhibition']
                        substrate_limitation = inhibition_data['Substrate_Limitation']
                        process_rates = inhibition_data['Process_Rates']
                        pH_value = inhibition_data['pH_Value']
                        
                        # Convert inhibition values to degrees of inhibition (0-100%)
                        def inhibition_degree(factor):
                            return (1 - factor) * 100
                        
                        # Create expanded inhibition factors to match process names length
                        h2_inhibition_expanded = [1.0, 1.0, h2_inhibition[0], h2_inhibition[1], 
                                                h2_inhibition[2], h2_inhibition[3], 1.0, 1.0]
                        
                        nh3_inhibition_expanded = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, nh3_inhibition, 1.0]
                        
                        # Display pH
                        pdf.set_font('Arial', '', 10)
                        pdf.cell(0, 8, f"Current pH: {pH_value:.2f}", 0, 1, 'L')
                        
                        # Create inhibition factors table
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(200, 200, 200)
                        pdf.cell(55, row_height, "Process", 1, 0, 'C', True)
                        pdf.cell(28, row_height, "pH Inhib. (%)", 1, 0, 'C', True)
                        pdf.cell(28, row_height, "H2 Inhib. (%)", 1, 0, 'C', True)
                        pdf.cell(28, row_height, "N Limit. (%)", 1, 0, 'C', True)
                        pdf.cell(28, row_height, "NH3 Inhib. (%)", 1, 0, 'C', True)
                        pdf.cell(28, row_height, "Safety (%)", 1, 0, 'C', True)
                        pdf.ln(row_height)
                        
                        # Add rows
                        pdf.set_font('Arial', '', 8)
                        for idx, process in enumerate(process_names):
                            pdf.cell(55, row_height, process, 1, 0)
                            pdf.cell(28, row_height, f"{inhibition_degree(pH_inhibition[idx]):.1f}%", 1, 0, 'C')
                            pdf.cell(28, row_height, f"{inhibition_degree(h2_inhibition_expanded[idx]):.1f}%", 1, 0, 'C')
                            pdf.cell(28, row_height, f"{inhibition_degree(n_limitation):.1f}%", 1, 0, 'C')
                            pdf.cell(28, row_height, f"{inhibition_degree(nh3_inhibition_expanded[idx]):.1f}%", 1, 0, 'C')
                            pdf.cell(28, row_height, f"{inhibition_degree(substrate_limitation[idx]):.1f}%", 1, 0, 'C')
                            pdf.ln(row_height)
                        
                        pdf.ln(5)
                        
                        # Generate AI analysis of process health
                        pdf.set_font('Arial', 'B', 10)
                        pdf.cell(0, 8, "Process Health Analysis", 0, 1, 'L')
                        
                        # Get narrative for process health
                        narrative = get_process_health_narrative(inhibition_data, session_state.sim_params[i])
                        pdf.set_font('Arial', '', 9)
                        pdf.multi_cell(0, 5, narrative)
                        pdf.ln(5)
                    else:
                        pdf.set_font('Arial', '', 9)
                        pdf.multi_cell(0, 5, "Inhibition data not available for this simulation.")
                except Exception as e:
                    pdf.set_font('Arial', '', 9)
                    pdf.multi_cell(0, 5, f"Error generating process health analysis: {str(e)}")
                
                pdf.ln(5)
        
        # --- Section 6: Total VFA Dynamics Plots ---
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "6. Total VFA Dynamics", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 5, "This section shows the dynamics of total volatile fatty acids (VFAs) over time for each simulation. "
                            "VFAs are key intermediate products in anaerobic digestion and their accumulation can indicate process instability.")
        
        # Generate VFA plot for each simulation
        try:
            # Generate a single plot with all simulations
            fig = _generate_vfa_plot_for_pdf(session_state)
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


def _generate_vfa_plot_for_pdf(session_state):
    """
    Generate a total VFA plot for all simulations
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    
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
        
        # Create a figure for total VFAs only
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Color cycle for different simulations
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        # Keep track of whether we added any data to the plot
        has_data = False
        
        for i, (sys_i, inf_i, eff_i, _) in enumerate(session_state.sim_results):
            if not sys_i or not inf_i or not eff_i:
                continue
                
            t_stamp_eff = eff_i.scope.time_series
            cmps_obj = inf_i.components
            
            # Calculate total VFAs
            vfa_list = ['S_va','S_bu','S_pro','S_ac']
            vfa_indices = [cmps_obj.index(vfa) for vfa in vfa_list if vfa in cmps_obj.IDs]
            
            if vfa_indices:
                vfa_matrix = eff_i.scope.record[:, vfa_indices]
                total_vfa = np.sum(vfa_matrix, axis=1)
                
                # Add to plot with simulation parameters in the legend
                temp = session_state.sim_params[i]['Temp']
                hrt = session_state.sim_params[i]['HRT']
                
                ax.plot(t_stamp_eff, total_vfa,
                        label=f"Sim {i+1} (HRT={hrt}d, T={temp}K)",
                        color=colors[i], linewidth=2)
                has_data = True
        
        # If no data was added to the plot, return None
        if not has_data:
            plt.close(fig)
            return None
            
        # Set plot labels and title
        ax.set_xlabel('Time [days]')
        ax.set_ylabel('Total VFA Concentration [mg/L]')
        ax.set_title('Total VFA Dynamics Across Simulations')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend with better positioning
        ax.legend(loc='best')
        
        # Tight layout
        fig.tight_layout()
        
        return fig
    except Exception as e:
        print(f"Error generating Total VFA plot: {str(e)}")
        return None


def render_pdf_export_button(session_state):
    """
    Render a button to generate and download an enhanced PDF report
    with AI-generated narratives
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    if st.button("Export Complete PDF Report"):
        try:
            with st.spinner("Generating comprehensive PDF report with AI-generated analysis..."):
                pdf_data = generate_pdf_report(session_state)
                
                if pdf_data:
                    # Provide download button for the PDF
                    st.success("Enhanced PDF report generated successfully!")
                    st.download_button(
                        label="Download Complete Simulation Report (PDF)",
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