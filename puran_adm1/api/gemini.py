"""
Gemini API integration for the Puran ADM1 Simulation Package
"""
import json
import re
import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiClient:
    """
    Client for interacting with the Gemini API
    """
    
    def __init__(self):
        """
        Initialize the GeminiClient
        """
        self.model = self._setup_model()
    
    def _setup_model(self):
        """
        Initialize the Gemini model
        """
        if not GEMINI_API_KEY:
            st.error("Please set your Gemini API key in the .env file.")
            return None
        
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-pro-exp-02-05"
            )
            return model
        except Exception as e:
            st.error(f"Error initializing Gemini model: {e}")
            return None

    def get_adm1_recommendations(self, feedstock_description, include_kinetics=True):
        """
        Get recommendations for ADM1 model parameters based on feedstock description
        
        Parameters
        ----------
        feedstock_description : str
            Description of the feedstock
        include_kinetics : bool, optional
            Whether to include kinetic parameters in the recommendations, by default True
            
        Returns
        -------
        str
            JSON string containing the recommendations
        """
        if not self.model:
            return None

        google_search_tool = {
            'function_declarations': [
                {
                    'name': 'search',
                    'description': 'Search for information on the web',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'The search query'
                            }
                        },
                        'required': ['query']
                    }
                }
            ]
        }
        
        if include_kinetics:
            # Full prompt: feedstock + kinetics
            prompt = self._build_full_prompt(feedstock_description)
        else:
            # Prompt for feedstock only
            prompt = self._build_feedstock_prompt(feedstock_description)
        
        try:
            response = self.model.generate_content(
                contents=prompt,
                tools=google_search_tool
            )
            return response.text
        except Exception as e:
            st.error(f"Error getting AI recommendations: {e}")
            return None
    
    def _build_full_prompt(self, feedstock_description):
        """
        Build prompt for full recommendation (feedstock + kinetics)
        
        Parameters
        ----------
        feedstock_description : str
            Description of the feedstock
            
        Returns
        -------
        str
            Full prompt for the Gemini API
        """
        return f"""
        You are an expert in anaerobic digestion modeling and specifically the ADM1 model.

        I need you to recommend:
        1) Feedstock state variable values (S_su, S_aa, S_fa, ..., X_su, X_fa, etc.) 
        with the same JSON structure as before.

        2) Substrate-dependent kinetic parameters (including disintegration, hydrolysis, 
        uptake, decay, yields, and fractionation) relevant to ADM1. 
        Provide them in the same JSON structure but with distinct keys 
        (e.g., "k_su": [value, "d^-1", "explanation"], "K_su": [value, "kg COD/m³", "explanation"], etc.).

        The overall JSON must look like this (one single JSON object) with both sets 
        of keys. Example:
        Please provide your recommendations for these state variables in JSON format with these specific keys:
        
        {{
            "S_su": [value, "kg/m3", "explanation"],
            "S_aa": [value, "kg/m3", "explanation"],
            "S_fa": [value, "kg/m3", "explanation"],
            "S_va": [value, "kg/m3", "explanation"],
            "S_bu": [value, "kg/m3", "explanation"],
            "S_pro": [value, "kg/m3", "explanation"],
            "S_ac": [value, "kg/m3", "explanation"],
            "S_h2": [value, "kg/m3", "explanation"],
            "S_ch4": [value, "kg/m3", "explanation"],
            "S_IC": [value, "kg/m3", "explanation"],
            "S_IN": [value, "kg/m3", "explanation"],
            "S_I": [value, "kg/m3", "explanation"],
            "X_c": [value, "kg/m3", "explanation"],
            "X_ch": [value, "kg/m3", "explanation"],
            "X_pr": [value, "kg/m3", "explanation"],
            "X_li": [value, "kg/m3", "explanation"],
            "X_su": [value, "kg/m3", "explanation"],
            "X_aa": [value, "kg/m3", "explanation"],
            "X_fa": [value, "kg/m3", "explanation"],
            "X_c4": [value, "kg/m3", "explanation"],
            "X_pro": [value, "kg/m3", "explanation"],
            "X_ac": [value, "kg/m3", "explanation"],
            "X_h2": [value, "kg/m3", "explanation"],
            "X_I": [value, "kg/m3", "explanation"]
            "S_cat": [value, "kg/m3", "explanation"]
            "S_an": [value, "kg/m3", "explanation"]
            "q_dis": [value, "kg/m3", "explanation"],
            "q_ch_hyd": [value, "kg/m3", "explanation"],
            "q_pr_hyd": [value, "kg/m3", "explanation"],
            "q_li_hyd": [value, "kg/m3", "explanation"],
            "k_su": [value, "d^-1", "explanation"],
            "k_aa": [value, "d^-1", "explanation"],
            "k_fa": [value, "d^-1", "explanation"],
            "k_c4": [value, "d^-1", "explanation"],
            "k_pro": [value, "d^-1", "explanation"],
            "k_ac": [value, "d^-1", "explanation"],
            "k_h2": [value, "d^-1", "explanation"],
            "b_su": [value, "kg/m3", "explanation"],
            "b_aa": [value, "kg/m3", "explanation"],
            "b_fa": [value, "kg/m3", "explanation"],
            "b_c4": [value, "kg/m3", "explanation"],
            "b_pro": [value, "kg/m3", "explanation"],
            "b_ac": [value, "kg/m3", "explanation"],
            "b_h2": [value, "kg/m3", "explanation"],
            "K_su": [value, "kg COD/m³", "explanation"],
            "K_aa": [value, "kg COD/m³", "explanation"],
            "K_fa": [value, "kg COD/m³", "explanation"],
            "K_c4": [value, "kg COD/m³", "explanation"],
            "K_pro": [value, "kg COD/m³", "explanation"],
            "K_ac": [value, "kg COD/m³", "explanation"],
            "K_h2": [value, "kg COD/m³", "explanation"],
            "KI_h2_fa": [value, "kg COD/m³", "explanation"],
            "KI_h2_c4": [value, "kg COD/m³", "explanation"],
            "KI_h2_pro": [value, "kg COD/m³", "explanation"],
            "KI_nh3": [value, "M", "explanation"],
            "KS_IN": [value, "M", "explanation],
            "Y_su": [value, "kg COD/kg COD", "explanation"],
            "Y_aa": [value, "kg COD/kg COD", "explanation"],
            "Y_fa": [value, "kg COD/kg COD", "explanation"],
            "Y_c4": [value, "kg COD/kg COD", "explanation"],
            "Y_pro": [value, "kg COD/kg COD", "explanation"],
            "Y_ac": [value, "kg COD/kg COD", "explanation"],
            "Y_h2": [value, "kg COD/kg COD", "explanation"],
            "f_bu_su": [value, "kg COD/kg COD", "explanation"],
            "f_pro_su": [value, "kg COD/kg COD", "explanation"],
            "f_ac_su": [value, "kg COD/kg COD", "explanation"],
            "f_va_aa": [value, "kg COD/kg COD", "explanation"],
            "f_bu_aa": [value, "kg COD/kg COD", "explanation"],
            "f_pro_aa": [value, "kg COD/kg COD", "explanation"],
            "f_ac_aa": [value, "kg COD/kg COD", "explanation"],
            "f_ac_fa": [value, "kg COD/kg COD", "explanation"],
            "f_pro_va": [value, "kg COD/kg COD", "explanation"],
            "f_ac_va": [value, "kg COD/kg COD", "explanation"],
            "f_ac_bu": [value, "kg COD/kg COD", "explanation"],
            "f_ac_pro": [value, "kg COD/kg COD", "explanation"]
        }}

        In which:
        **S_su**: Monosaccharides, **S_aa**: Amino acids, **S_fa**: Total long-chain fatty acids, **S_va**: Total valerate, **S_bu**: Total butyrate, 
        **S_pro**: Total propionate, **S_ac**: Total acetate, **S_h2**: Hydrogen gas, **S_ch4**: Methane gas, **S_IC**: Inorganic carbon, **S_IN**: Inorganic nitrogen, 
        **S_I**: Soluble inerts (i.e. recalcitrant soluble COD), **X_c**: Composites, **X_ch**: Carobohydrates, **X_pr**: Proteins, **X_li**: Lipids, **X_su**: Biomass uptaking sugars, **X_aa**: Biomass uptaking amino acids, 
        **X_fa**: Biomass uptaking long chain fatty acids, **X_c4**: Biomass uptaking c4 fatty acids (valerate and butyrate), **X_pro**: Biomass uptaking propionate, 
        **X_ac**: Biomass uptaking acetate, **X_h2**: Biomass uptaking hydrogen, **X_I**: Particulate inerts (i.e. recalcitrant particulate COD), **S_cat**: Other cations, **S_an**: Other anions 
        q_dis: Composite disintegration rate constant,
        q_ch_hyd: Carbohydrate (sugar) hydrolysis rate constant,
        q_pr_hyd: Protein hydrolysis rate constant,
        q_li_hyd: Lipid hydrolysis rate constant,
        k_su: Sugar uptake rate constant,
        k_aa: Amino acid uptake rate constant,
        k_fa: LCFA (long-chain fatty acid) uptake rate constant,
        k_c4: C₄ fatty acid (butyrate/valerate) uptake rate constant,
        k_pro: Propionate uptake rate constant,
        k_ac: Acetate uptake rate constant,
        k_h2: Hydrogen uptake rate constant,
        b_su: Decay rate constant for sugar-degrading biomass,
        b_aa: Decay rate constant for amino acid-degrading biomass,
        b_fa: Decay rate constant for LCFA-degrading biomass,
        b_c4: Decay rate constant for butyrate/valerate-degrading biomass,
        b_pro: Decay rate constant for propionate-degrading biomass,
        b_ac: Decay rate constant for acetate-degrading biomass,
        b_h2: Decay rate constant for hydrogen-degrading biomass,
        K_su: Half-saturation coefficient for sugar uptake,
        K_aa: Half-saturation coefficient for amino acid uptake,
        K_fa: Half-saturation coefficient for LCFA uptake,
        K_c4: Half-saturation coefficient for butyrate/valerate uptake,
        K_pro: Half-saturation coefficient for propionate uptake,
        K_ac: Half-saturation coefficient for acetate uptake,
        K_h2: Half-saturation coefficient for hydrogen uptake,
        KI_h2_fa: Hydrogen inhibition coefficient for LCFA uptake,
        KI_h2_c4: Hydrogen inhibition coefficient for butyrate/valerate uptake,
        KI_h2_pro: Hydrogen inhibition coefficient for propionate uptake,
        KI_nh3: Free ammonia inhibition coefficient for acetate uptake,
        KS_IN: Inorganic nitrogen inhibition coefficient for substrate uptake,
        Y_su: Biomass yield for sugar uptake,
        Y_aa: Biomass yield for amino acid uptake,
        Y_fa: Biomass yield for LCFA uptake,
        Y_c4: Biomass yield for butyrate/valerate uptake,
        Y_pro: Biomass yield for propionate uptake,
        Y_ac: Biomass yield for acetate uptake,
        Y_h2: Biomass yield for hydrogen uptake,
        f_bu_su: Fraction of sugars converted to butyrate,
        f_pro_su: Fraction of sugars converted to propionate,
        f_ac_su: Fraction of sugars converted to acetate,
        f_va_aa: Fraction of amino acids converted to valerate,
        f_bu_aa: Fraction of amino acids converted to butyrate,
        f_pro_aa: Fraction of amino acids converted to propionate,
        f_ac_aa: Fraction of amino acids converted to acetate,
        f_ac_fa: Fraction of LCFAs converted to acetate,
        f_pro_va: Fraction of LCFAs (via valerate) converted to propionate,
        f_ac_va: Fraction of valerate converted to acetate,
        f_ac_bu: Fraction of butyrate converted to acetate, and
        f_ac_pro: Fraction of propionate converted to acetate.
        
        Units of S_su, S_aa, S_fa, S_va, S_bu, S_pro, S_ac, S_h2, S_ch4, S_I, X_c, X_ch, X_pr, X_li, X_aa, X_fa, X_c4, X_pro, X_ac, X_h2, X_I are kg COD/m3.
        
        Units of S_IC are kg C/m3.
        
        Units of S_IN are kg N/m3.
        
        Units of S_cat and S_an are kg/m3 as cations and anions, respectively.

        Make sure you provide the explanation for why each value is chosen 
        (the domain reason, such as typical range for certain feedstock). 
        Also ensure that if a feedstock COD concentration is provided, the sum of 
        your state variable estimates is consistent with that COD.

        Here is the feedstock description:

        {feedstock_description}

        Return ONLY this JSON object. 
        """
    
    def _build_feedstock_prompt(self, feedstock_description):
        """
        Build prompt for feedstock recommendations only
        
        Parameters
        ----------
        feedstock_description : str
            Description of the feedstock
            
        Returns
        -------
        str
            Feedstock prompt for the Gemini API
        """
        return f"""
        You are an expert in anaerobic digestion modeling and specifically the ADM1 model. 
        
        I need you to recommend state variable values for the following feedstock:
        
        {feedstock_description}
        
        Please provide your recommendations for these state variables in JSON format with these specific keys:
        
        {{
            "S_su": [value, "kg/m3", "explanation"],
            "S_aa": [value, "kg/m3", "explanation"],
            "S_fa": [value, "kg/m3", "explanation"],
            "S_va": [value, "kg/m3", "explanation"],
            "S_bu": [value, "kg/m3", "explanation"],
            "S_pro": [value, "kg/m3", "explanation"],
            "S_ac": [value, "kg/m3", "explanation"],
            "S_h2": [value, "kg/m3", "explanation"],
            "S_ch4": [value, "kg/m3", "explanation"],
            "S_IC": [value, "kg/m3", "explanation"],
            "S_IN": [value, "kg/m3", "explanation"],
            "S_I": [value, "kg/m3", "explanation"],
            "X_c": [value, "kg/m3", "explanation"],
            "X_ch": [value, "kg/m3", "explanation"],
            "X_pr": [value, "kg/m3", "explanation"],
            "X_li": [value, "kg/m3", "explanation"],
            "X_su": [value, "kg/m3", "explanation"],
            "X_aa": [value, "kg/m3", "explanation"],
            "X_fa": [value, "kg/m3", "explanation"],
            "X_c4": [value, "kg/m3", "explanation"],
            "X_pro": [value, "kg/m3", "explanation"],
            "X_ac": [value, "kg/m3", "explanation"],
            "X_h2": [value, "kg/m3", "explanation"],
            "X_I": [value, "kg/m3", "explanation"]
            "S_cat": [value, "kg/m3", "explanation"]
            "S_an": [value, "kg/m3", "explanation"]
        }}
        
        In which:
        **S_su**: Monosaccharides, **S_aa**: Amino acids, **S_fa**: Total long-chain fatty acids, **S_va**: Total valerate, **S_bu**: Total butyrate, 
        **S_pro**: Total propionate, **S_ac**: Total acetate, **S_h2**: Hydrogen gas, **S_ch4**: Methane gas, **S_IC**: Inorganic carbon, **S_IN**: Inorganic nitrogen, 
        **S_I**: Soluble inerts (i.e. recalcitrant soluble COD), **X_c**: Composites, **X_ch**: Carobohydrates, **X_pr**: Proteins, **X_li**: Lipids, **X_su**: Biomass uptaking sugars, **X_aa**: Biomass uptaking amino acids, 
        **X_fa**: Biomass uptaking long chain fatty acids, **X_c4**: Biomass uptaking c4 fatty acids (valerate and butyrate), **X_pro**: Biomass uptaking propionate, 
        **X_ac**: Biomass uptaking acetate, **X_h2**: Biomass uptaking hydrogen, **X_I**: Particulate inerts (i.e. recalcitrant particulate COD), **S_cat**: Other cations, **S_an**: Other anions 
        
        Units of S_su, S_aa, S_fa, S_va, S_bu, S_pro, S_ac, S_h2, S_ch4, S_I, X_c, X_ch, X_pr, X_li, X_aa, X_fa, X_c4, X_pro, X_ac, X_h2, X_I are kg COD/m3.
        
        Units of S_IC are kg C/m3.
        
        Units of S_IN are kg N/m3.
        
        Units of S_cat and S_an are kg/m3 as cations and anions, respectively.
        
        **IF A COD CONCENTRATION OF THE FEEDSTOCK IS PROVIDED IN THE FEEDSTOCK DESCRIPTION** - ensure the COD concentration calculated based on your 
        estimates are equivalent to the COD concentration provided in the feedstock description.
        
        Only include these exact state variables and provide values with appropriate units for ADM1 model inputs.
        """

    def parse_recommendations(self, response_text, include_kinetics=True):
        """
        Parse the response from the Gemini API into dictionaries
        
        Parameters
        ----------
        response_text : str
            Response text from the Gemini API
        include_kinetics : bool, optional
            Whether to parse kinetic parameters, by default True
            
        Returns
        -------
        tuple
            (feedstock_values, feedstock_explanations, kinetic_values, kinetic_explanations)
        """
        # Known feedstock keys
        feedstock_keys = {
            "S_su","S_aa","S_fa","S_va","S_bu","S_pro","S_ac","S_h2","S_ch4","S_IC","S_IN","S_I",
            "X_c","X_ch","X_pr","X_li","X_su","X_aa","X_fa","X_c4","X_pro","X_ac","X_h2","X_I",
            "S_cat","S_an"
        }
        # Known kinetic keys
        kinetic_keys = {
            "q_dis","q_ch_hyd","q_pr_hyd","q_li_hyd",
            "k_su","k_aa","k_fa","k_c4","k_pro","k_ac","k_h2",
            "b_su","b_aa","b_fa","b_c4","b_pro","b_ac","b_h2",
            "K_su","K_aa","K_fa","K_c4","K_pro","K_ac","K_h2",
            "KI_h2_fa","KI_h2_c4","KI_h2_pro","KI_nh3","KS_IN",
            "Y_su","Y_aa","Y_fa","Y_c4","Y_pro","Y_ac","Y_h2",
            "f_bu_su","f_pro_su","f_ac_su","f_va_aa","f_bu_aa",
            "f_pro_aa","f_ac_aa","f_ac_fa","f_pro_va","f_ac_va",
            "f_ac_bu","f_ac_pro"
        }
        
        feedstock_values = {}
        feedstock_explanations = {}
        kinetic_values = {}
        kinetic_explanations = {}
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return (feedstock_values, feedstock_explanations, kinetic_values, kinetic_explanations)
        
        try:
            data = json.loads(json_match.group())
            for key, arr in data.items():
                if not isinstance(arr, list) or len(arr) < 3:
                    continue
                val = float(arr[0])
                explanation = arr[2]

                # Feedstock check
                if key in feedstock_keys:
                    feedstock_values[key] = val
                    feedstock_explanations[key] = explanation
                # Only parse kinetic if we're including it
                elif include_kinetics and (key in kinetic_keys):
                    kinetic_values[key] = val
                    kinetic_explanations[key] = explanation
            
            return (feedstock_values, feedstock_explanations, kinetic_values, kinetic_explanations)
        except Exception as e:
            raise ValueError(f"Error parsing AI JSON: {e}")