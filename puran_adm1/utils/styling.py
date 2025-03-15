"""Styling utilities for the Streamlit application.

This module provides functions for setting page styling, displaying branding elements,
and other visual customizations.
"""
import streamlit as st
import base64
import os

def set_page_styling():
    """
    Set custom CSS styles for the application
    """
    # Define custom CSS
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #004080;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f0f0;
            border-radius: 4px 4px 0 0;
            border: 1px solid #ddd;
            border-bottom: none;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #004080;
            color: white;
        }
        
        .sidebar .sidebar-content {
            background-image: linear-gradient(#f0f8ff, #e0f0ff);
        }
        
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        div[data-testid="stDataFrame"] {
            margin-bottom: 1rem;
        }
        
        section[data-testid="stSidebar"] > div > div:nth-child(1) > div > div > div > button {
            background-color: #004080;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

def display_branding_header():
    """
    Display branding header with logo and title
    """
    # Check if custom logos are available in the repository
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            "puran_water_logo.png")
    qsdsan_logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                  "qsdsan_logo.png")
    
    # Create columns for logos and title
    col1, col2, col3 = st.columns([1, 3, 1])
    
    # Display Puran Water logo if available
    if os.path.exists(logo_path):
        with col1:
            st.image(logo_path, width=150)
    else:
        # If logo is not available, display a placeholder or text
        with col1:
            st.markdown("## Puran Water")
    
    # Display QSDsan logo if available
    if os.path.exists(qsdsan_logo_path):
        with col3:
            st.image(qsdsan_logo_path, width=150)
    
    # Add a separator
    st.markdown("<hr>", unsafe_allow_html=True)

def display_footer():
    """
    Display footer with copyright and version information
    """
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>Developed using QSDsan and EXPOsan packages | ADM1 Simulation App v0.1.0</p>
        <p>&copy; 2025 Puran Water | <a href="https://github.com/hvkshetry/adm1-simulation-app" target="_blank">GitHub Repository</a></p>
    </div>
    """, unsafe_allow_html=True)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """
    Create a download link for a binary file
    
    Parameters
    ----------
    bin_file : bytes
        Binary file data
    file_label : str
        Label for the download link
        
    Returns
    -------
    str
        HTML for the download link
    """
    b64 = base64.b64encode(bin_file).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_label}">Download {file_label}</a>'