"""
Component for editing feedstock parameters
"""
import streamlit as st
from chemicals.elements import molecular_weight as get_mw

def render_feedstock_editor(session_state):
    """
    Render the feedstock editor component
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    with st.expander("Manual Feedstock Parameter Input", expanded=False):
        C_mw = get_mw({'C':1})
        N_mw = get_mw({'N':1})
        
        feedstock_defaults = {
            'S_su': 0.01,
            'S_aa': 1e-3,
            'S_fa': 1e-3,
            'S_va': 1e-3,
            'S_bu': 1e-3,
            'S_pro': 1e-3,
            'S_ac': 1e-3,
            'S_h2': 1e-8,
            'S_ch4': 1e-5,
            'S_IC': 0.04*C_mw,
            'S_IN': 0.01*N_mw,
            'S_I': 0.02,
            'X_c': 2.0,
            'X_ch': 5.0,
            'X_pr': 20.0,
            'X_li': 5.0,
            'X_su': 1e-2,
            'X_aa': 1e-2,
            'X_fa': 1e-2,
            'X_c4': 1e-2,
            'X_pro': 1e-2,
            'X_ac': 1e-2,
            'X_h2': 1e-2,
            'X_I': 25,
            'S_cat': 0.04,
            'S_an': 0.02,
        }
        
        # Update defaults with session values
        for k,v in session_state.influent_values.items():
            feedstock_defaults[k] = v
        
        # Soluble components section
        st.subheader("Soluble Components (S_)")
        sol_keys = ['S_su','S_aa','S_fa','S_va','S_bu','S_pro','S_ac','S_h2','S_ch4','S_IC','S_IN','S_I','S_cat','S_an']
        cols_s = st.columns(3)
        for i, key in enumerate(sol_keys):
            with cols_s[i % 3]:
                val = st.number_input(
                    f"{key} [kg/m³]",
                    value=float(feedstock_defaults.get(key, 0.0)),
                    format="%.6f",
                    key=f"feed_{key}"
                )
                session_state.influent_values[key] = val
        
        # Particulate components section
        st.markdown("---")
        st.subheader("Particulate Components (X_)")
        part_keys = ['X_c','X_ch','X_pr','X_li','X_su','X_aa','X_fa','X_c4','X_pro','X_ac','X_h2','X_I']
        cols_x = st.columns(3)
        for i, key in enumerate(part_keys):
            with cols_x[i % 3]:
                val = st.number_input(
                    f"{key} [kg/m³]",
                    value=float(feedstock_defaults.get(key, 0.0)),
                    format="%.4f",
                    key=f"feed_{key}"
                )
                session_state.influent_values[key] = val
        
        if st.button("Update Feedstock Parameters"):
            st.success("Feedstock parameters updated!")

def render_kinetics_editor(session_state):
    """
    Render the kinetics editor component
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    if not session_state.use_kinetics:
        return
        
    with st.expander("Manual Kinetic Parameter Input", expanded=False):
        kinetic_defaults = {
            "q_dis": 0.5,
            "q_ch_hyd": 10.0,
            "q_pr_hyd": 10.0,
            "q_li_hyd": 10.0,
            "k_su": 30.0,
            "k_aa": 50.0,
            "k_fa": 6.0,
            "k_c4": 20.0,
            "k_pro": 13.0,
            "k_ac": 8.0,
            "k_h2": 35.0,
            "b_su": 0.02,
            "b_aa": 0.02,
            "b_fa": 0.02,
            "b_c4": 0.02,
            "b_pro": 0.02,
            "b_ac": 0.02,
            "b_h2": 0.02,
            "K_su": 0.5,
            "K_aa": 0.3,
            "K_fa": 0.4,
            "K_c4": 0.2,
            "K_pro": 0.1,
            "K_ac": 0.15,
            "K_h2": 7e-6,
            "KI_h2_fa": 5e-6,
            "KI_h2_c4": 1e-5,
            "KI_h2_pro": 3.5e-6,
            "KI_nh3": 1.8e-3,
            "KS_IN": 1e-4,
            "Y_su": 0.1,
            "Y_aa": 0.08,
            "Y_fa": 0.06,
            "Y_c4": 0.06,
            "Y_pro": 0.04,
            "Y_ac": 0.05,
            "Y_h2": 0.06,
            "f_bu_su": 0.13,
            "f_pro_su": 0.27,
            "f_ac_su": 0.41,
            "f_va_aa": 0.23,
            "f_bu_aa": 0.26,
            "f_pro_aa": 0.05,
            "f_ac_aa": 0.40,
            "f_ac_fa": 0.7,
            "f_pro_va": 0.54,
            "f_ac_va": 0.31,
            "f_ac_bu": 0.8,
            "f_ac_pro": 0.57
        }
        
        # Update defaults with session values
        for k,v in session_state.kinetic_params.items():
            kinetic_defaults[k] = v
        
        param_list = sorted(list(kinetic_defaults.keys()))
        cols_k = st.columns(3)
        for i, p in enumerate(param_list):
            with cols_k[i % 3]:
                val = st.number_input(
                    f"{p}",
                    value=float(kinetic_defaults[p]),
                    format="%.6f",
                    key=f"kin_{p}"
                )
                session_state.kinetic_params[p] = val
        
        if st.button("Update Kinetic Parameters"):
            st.success("Kinetic parameters updated!")