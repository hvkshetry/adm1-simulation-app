"""
Styling utilities for the Streamlit application
"""
import streamlit as st
import base64
from io import BytesIO

def get_base64_of_bin_file(bin_file):
    """
    Load binary file and encode in base64
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_page_styling():
    """
    Set custom CSS styling according to Puran Water brand guidelines
    """
    primary_blue = "#40a4df"
    secondary_slate = "#708090"
    
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: white;
        }}
        h1, h2, h3 {{
            color: {primary_blue};
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-weight: bold;
        }}
        .st-emotion-cache-16txtl3 h1 {{
            margin-top: -3rem;
        }}
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: white;
            color: {secondary_slate};
            text-align: center;
            padding: 10px;
            font-size: 14px;
            border-top: 1px solid #f0f0f0;
        }}
        .branding-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            background-color: white;
            margin-bottom: 1rem;
        }}
        .powered-by {{
            font-size: 12px;
            color: {secondary_slate};
            text-align: right;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .powered-by img {{
            height: 30px;
        }}
        .sidebar-header {{
            color: {primary_blue};
            font-weight: bold;
            margin-top: 15px;
        }}
        </style>
    """, unsafe_allow_html=True)

def display_branding_header():
    """
    Display the Puran Water and QSDsan branding header
    """
    col1, col2 = st.columns([6, 6])
    with col1:
        try:
            st.image("puran_water_logo.png", width=250)
        except:
            st.write("Puran Water Logo Here")
    with col2:
        try:
            qsdsan_b64 = get_base64_of_bin_file("qsdsan_logo.png")
            st.markdown(f"""
                <div class="powered-by">
                    Powered by: <img src="data:image/png;base64,{qsdsan_b64}" alt="QSDsan">
                </div>
            """, unsafe_allow_html=True)
        except:
            st.write("Powered by QSDsan")

def display_footer():
    """
    Display the footer with copyright and contact information
    """
    st.markdown("""
        <div class="footer">
            © 2025 Puran Water LLC. All rights reserved.
            For engineering consulting services, contact us at hersh@puranwater.com.
        </div>
    """, unsafe_allow_html=True)