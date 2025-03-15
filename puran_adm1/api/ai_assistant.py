"""AI Assistant for feedstock recommendations.

This module handles interactions with the Google Gemini API to get AI recommendations
for feedstock composition and kinetic parameters.
"""
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from chemicals.elements import molecular_weight as get_mw

# Load API key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables")

# Define molecular weights
C_mw = get_mw({'C': 1})
N_mw = get_mw({'N': 1})

def get_ai_recommendations(description, include_kinetics=False):
    """
    Get AI recommendations for feedstock composition and kinetic parameters.
    
    Parameters
    ----------
    description : str
        Natural language description of the feedstock
    include_kinetics : bool
        Whether to include kinetic parameters in recommendations
        
    Returns
    -------
    dict
        Dictionary of recommended values and explanations
    """
    if not GEMINI_API_KEY:
        # Return mock data for testing (without API key)
        return get_mock_recommendations(include_kinetics)
    
    try:
        # Set up the model and prompt for feedstock recommendations
        model = genai.GenerativeModel('gemini-pro')
        
        # Basic prompt for feedstock composition
        prompt = f"""
        You are an anaerobic digestion expert. I'm using the ADM1 (Anaerobic Digestion Model No. 1) 
        for modeling biogas production. Based on the following feedstock description, 
        provide suitable ADM1 state variable values:
        
        Feedstock description: {description}
        
        For your reference, here are the state variables used in ADM1:
        - S_su: Monosaccharides (sugars) [kg COD/m³]
        - S_aa: Amino acids [kg COD/m³]
        - S_fa: Long chain fatty acids [kg COD/m³]
        - S_va: Valerate [kg COD/m³]
        - S_bu: Butyrate [kg COD/m³]
        - S_pro: Propionate [kg COD/m³]
        - S_ac: Acetate [kg COD/m³]
        - S_h2: Hydrogen [kg COD/m³]
        - S_ch4: Methane [kg COD/m³]
        - S_IC: Inorganic carbon [kg C/m³]
        - S_IN: Inorganic nitrogen [kg N/m³]
        - S_I: Soluble inerts [kg COD/m³]
        - X_c: Composite particulates [kg COD/m³]
        - X_ch: Carbohydrates [kg COD/m³]
        - X_pr: Proteins [kg COD/m³]
        - X_li: Lipids [kg COD/m³]
        - X_su: Sugar degraders [kg COD/m³]
        - X_aa: Amino acid degraders [kg COD/m³]
        - X_fa: LCFA degraders [kg COD/m³]
        - X_c4: Valerate & butyrate degraders [kg COD/m³]
        - X_pro: Propionate degraders [kg COD/m³]
        - X_ac: Acetate degraders [kg COD/m³]
        - X_h2: Hydrogen degraders [kg COD/m³]
        - X_I: Particulate inerts [kg COD/m³]
        - S_cat: Cations [kg/m³]
        - S_an: Anions [kg/m³]
        
        Respond with a JSON object containing two nested objects:
        1. "influent_values": key-value pairs for each ADM1 state variable
        2. "influent_explanations": key-value pairs explaining why you recommended each value
        
        Be realistic with your values, considering the nature of the feedstock. For biomass groups (X_su, X_aa, etc.),
        use small values (0.01-0.1 kg COD/m³) as these represent initial seed populations. For main components like
        X_ch, X_pr, X_li, use values consistent with the feedstock's composition.
        """
        
        # Extend prompt for kinetic parameters if requested
        if include_kinetics:
            prompt += """
            Also include kinetic parameters for the ADM1 model. Key parameters include:
            - k_dis: Disintegration rate [d^-1]
            - k_hyd_ch: Hydrolysis rate for carbohydrates [d^-1]
            - k_hyd_pr: Hydrolysis rate for proteins [d^-1]
            - k_hyd_li: Hydrolysis rate for lipids [d^-1]
            - k_m_su: Maximum uptake rate for sugars [d^-1]
            - k_m_aa: Maximum uptake rate for amino acids [d^-1]
            - k_m_fa: Maximum uptake rate for fatty acids [d^-1]
            - k_m_c4: Maximum uptake rate for valerate and butyrate [d^-1]
            - k_m_pro: Maximum uptake rate for propionate [d^-1]
            - k_m_ac: Maximum uptake rate for acetate [d^-1]
            - k_m_h2: Maximum uptake rate for hydrogen [d^-1]
            - K_S_su: Half saturation constant for sugars [kg COD/m^3]
            - K_S_aa: Half saturation constant for amino acids [kg COD/m^3]
            - K_S_fa: Half saturation constant for fatty acids [kg COD/m^3]
            - K_S_c4: Half saturation constant for valerate and butyrate [kg COD/m^3]
            - K_S_pro: Half saturation constant for propionate [kg COD/m^3]
            - K_S_ac: Half saturation constant for acetate [kg COD/m^3]
            - K_S_h2: Half saturation constant for hydrogen [kg COD/m^3]
            - pH_UL_aa, pH_LL_aa: Upper and lower pH limits for amino acid degraders
            - pH_UL_ac, pH_LL_ac: Upper and lower pH limits for acetate degraders
            - pH_UL_h2, pH_LL_h2: Upper and lower pH limits for hydrogen degraders
            - Y_su, Y_aa, Y_fa, Y_c4, Y_pro, Y_ac, Y_h2: Biomass yields [kg COD/kg COD]
            - k_dec_X_su, k_dec_X_aa, k_dec_X_fa, k_dec_X_c4, k_dec_X_pro, k_dec_X_ac, k_dec_X_h2: Decay rates [d^-1]
            
            Add two more objects to your JSON response:
            3. "kinetic_params": key-value pairs for each kinetic parameter
            4. "kinetic_explanations": key-value pairs explaining why you recommended each value
            
            Suggest realistic values based on the feedstock characteristics. Consider that hydrolysis rates
            may be affected by the feedstock's structure (e.g., lignocellulosic materials have slower hydrolysis).
            """
        
        prompt += """
        Format your response as valid JSON, like this:
        {
            "influent_values": {
                "S_su": 0.01,
                ...
            },
            "influent_explanations": {
                "S_su": "Explanation for recommended value",
                ...
            }
        }
        
        Start your response with ```json and end with ```, I will parse the JSON directly.
        """
        
        # Generate a response from the model
        response = model.generate_content(prompt)
        
        # Extract the JSON string from the response
        json_string = extract_json_from_response(response.text)
        
        # Parse the JSON string into a Python dictionary
        recommendations = json.loads(json_string)
        
        # Apply C_mw and N_mw to S_IC and S_IN values
        if 'influent_values' in recommendations and 'S_IC' in recommendations['influent_values']:
            recommendations['influent_values']['S_IC'] *= C_mw
        if 'influent_values' in recommendations and 'S_IN' in recommendations['influent_values']:
            recommendations['influent_values']['S_IN'] *= N_mw
        
        return recommendations
    
    except Exception as e:
        # Return mock data if there's an error
        print(f"Error getting AI recommendations: {str(e)}")
        return get_mock_recommendations(include_kinetics)

def extract_json_from_response(response_text):
    """
    Extract JSON string from the response text.
    
    Parameters
    ----------
    response_text : str
        Response text from the API
        
    Returns
    -------
    str
        JSON string
    """
    # Remove code fences and whitespace
    cleaned_text = response_text.strip()
    
    # Remove ```json at the beginning if present
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]
    elif cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]
    
    # Remove ``` at the end if present
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]
    
    return cleaned_text.strip()

def get_mock_recommendations(include_kinetics=False):
    """
    Get mock recommendations for testing.
    
    Parameters
    ----------
    include_kinetics : bool
        Whether to include kinetic parameters in recommendations
        
    Returns
    -------
    dict
        Dictionary of mock recommendations
    """
    recommendations = {
        "influent_values": {
            "S_su": 0.01,
            "S_aa": 0.001,
            "S_fa": 0.001,
            "S_va": 0.001,
            "S_bu": 0.001,
            "S_pro": 0.001,
            "S_ac": 0.001,
            "S_h2": 1e-8,
            "S_ch4": 1e-5,
            "S_IC": 0.04 * C_mw,
            "S_IN": 0.01 * N_mw,
            "S_I": 0.02,
            "X_c": 2.0,
            "X_ch": 5.0,
            "X_pr": 5.0,
            "X_li": 3.0,
            "X_su": 0.01,
            "X_aa": 0.01,
            "X_fa": 0.01,
            "X_c4": 0.01,
            "X_pro": 0.01,
            "X_ac": 0.01,
            "X_h2": 0.01,
            "X_I": 25.0,
            "S_cat": 0.04,
            "S_an": 0.02,
        },
        "influent_explanations": {
            "S_su": "Default value for monosaccharides",
            "X_ch": "Based on carbohydrate content of typical food waste",
            "X_pr": "Based on protein content of typical food waste",
            "X_li": "Based on lipid content of typical food waste",
        }
    }
    
    if include_kinetics:
        recommendations.update({
            "kinetic_params": {
                "k_dis": 0.5,
                "k_hyd_ch": 10.0,
                "k_hyd_pr": 10.0,
                "k_hyd_li": 10.0,
                "k_m_su": 30.0,
                "k_m_aa": 50.0,
                "k_m_fa": 6.0,
                "k_m_c4": 20.0,
                "k_m_pro": 13.0,
                "k_m_ac": 8.0,
                "k_m_h2": 35.0,
                "K_S_su": 0.5,
                "K_S_aa": 0.3,
                "K_S_fa": 0.4,
                "K_S_c4": 0.2,
                "K_S_pro": 0.1,
                "K_S_ac": 0.15,
                "K_S_h2": 7e-6,
                "pH_UL_aa": 5.5,
                "pH_LL_aa": 4.0,
                "pH_UL_ac": 7.0,
                "pH_LL_ac": 6.0,
                "pH_UL_h2": 6.0,
                "pH_LL_h2": 5.0,
                "Y_su": 0.1,
                "Y_aa": 0.08,
                "Y_fa": 0.06,
                "Y_c4": 0.06,
                "Y_pro": 0.04,
                "Y_ac": 0.05,
                "Y_h2": 0.06,
                "k_dec_X_su": 0.02,
                "k_dec_X_aa": 0.02,
                "k_dec_X_fa": 0.02,
                "k_dec_X_c4": 0.02,
                "k_dec_X_pro": 0.02,
                "k_dec_X_ac": 0.02,
                "k_dec_X_h2": 0.02,
            },
            "kinetic_explanations": {
                "k_dis": "Default disintegration rate",
                "k_hyd_ch": "Default hydrolysis rate for carbohydrates",
                "k_hyd_pr": "Default hydrolysis rate for proteins",
                "k_hyd_li": "Default hydrolysis rate for lipids",
            }
        })
    
    return recommendations