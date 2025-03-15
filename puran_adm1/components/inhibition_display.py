"""
Inhibition and nutrient limitation display components for ADM1 simulation
"""
import streamlit as st
import pandas as pd
import numpy as np

def calculate_inhibition_factors(simulation_state, simulation_results=None):
    """
    Calculate inhibition and nutrient limitation factors from the simulation state
    
    Parameters
    ----------
    simulation_state : System
        The simulation system with results
    simulation_results : tuple, optional
        Tuple containing (sys, inf, eff, gas) if already available
        
    Returns
    -------
    dict
        Dictionary containing all inhibition factors
    """
    if simulation_results is None and simulation_state is None:
        return None
    
    if simulation_results is not None:
        sys, inf, eff, gas = simulation_results
    else:
        # Retrieve values from the system state if results not provided
        sys = simulation_state
    
    # Try to access the inhibition data stored by the ADM1 model during the last simulation step
    try:
        # The ADM1 model in QSDsan stores inhibition data in the model's root attribute
        # This is stored during rate calculation in the _rhos_adm1 function
        root_data = sys._path[0].model.rate_function._params['root'].data
        
        if root_data is None:
            return None
        
        # Extract inhibition factors
        inhibition_factors = {
            'pH_Inhibition': root_data.get('Iph', [1, 1, 1, 1, 1, 1, 1, 1]),
            'H2_Inhibition': root_data.get('Ih2', [1, 1, 1, 1]),
            'Nitrogen_Limitation': root_data.get('Iin', 1),
            'Ammonia_Inhibition': root_data.get('Inh3', 1),
            'Substrate_Limitation': root_data.get('Monod', [1, 1, 1, 1, 1, 1, 1, 1]),
            'Process_Rates': root_data.get('rhos', [0, 0, 0, 0, 0, 0, 0, 0]),
            'pH_Value': root_data.get('pH', 7.0)
        }
        
        return inhibition_factors
    
    except (KeyError, AttributeError, IndexError) as e:
        # If the inhibition data isn't available, return None
        return None

def display_inhibition_dashboard(simulation_state=None, simulation_results=None):
    """
    Display inhibition and nutrient limitation factors in a dashboard
    
    Parameters
    ----------
    simulation_state : System
        The simulation system with results
    simulation_results : tuple, optional
        Tuple containing (sys, inf, eff, gas) if already available
    """
    inhibition_data = calculate_inhibition_factors(simulation_state, simulation_results)
    
    if inhibition_data is None:
        st.info("No inhibition data available. Run a simulation first.")
        return
    
    # Define process names for better display
    process_names = [
        "Sugar Uptake", 
        "Amino Acid Uptake", 
        "LCFA Uptake", 
        "Valerate Uptake",
        "Butyrate Uptake", 
        "Propionate Uptake", 
        "Acetate Uptake", 
        "H₂ Uptake"
    ]
    
    # Process-specific inhibition factors
    pH_inhibition = inhibition_data['pH_Inhibition']
    h2_inhibition = inhibition_data['H2_Inhibition']
    n_limitation = inhibition_data['Nitrogen_Limitation']
    nh3_inhibition = inhibition_data['Ammonia_Inhibition']
    substrate_limitation = inhibition_data['Substrate_Limitation']
    process_rates = inhibition_data['Process_Rates']
    pH_value = inhibition_data['pH_Value']
    
    # Calculate overall inhibition for each process
    overall_inhibition = []
    
    # Create expanded inhibition factors to match process names length
    h2_inhibition_expanded = [1.0, 1.0, h2_inhibition[0], h2_inhibition[1], 
                             h2_inhibition[2], h2_inhibition[3], 1.0, 1.0]
    
    nh3_inhibition_expanded = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, nh3_inhibition, 1.0]
    
    for i, process in enumerate(process_names):
        # Each inhibition factor is between 0-1, where 1 means no inhibition
        # Calculate overall inhibition as the product of all applicable factors
        if i == 6:  # Acetate uptake affected by ammonia
            overall = pH_inhibition[i] * n_limitation * nh3_inhibition * substrate_limitation[i]
        elif i in [2, 3, 4, 5]:  # LCFA, valerate, butyrate, propionate uptake affected by H2
            overall = pH_inhibition[i] * n_limitation * h2_inhibition_expanded[i] * substrate_limitation[i]
        else:  # Other processes
            overall = pH_inhibition[i] * n_limitation * substrate_limitation[i]
        
        overall_inhibition.append(overall)
    
    # Convert inhibition values to degrees of inhibition (0-100%)
    def inhibition_degree(factor):
        return (1 - factor) * 100
    
    # Prepare data for the dashboard
    inhibition_df = pd.DataFrame({
        'Process': process_names,
        'pH Inhibition (%)': [inhibition_degree(x) for x in pH_inhibition],
        'H₂ Inhibition (%)': [inhibition_degree(x) for x in h2_inhibition_expanded],
        'N Limitation (%)': [inhibition_degree(n_limitation)] * len(process_names),
        'NH₃ Inhibition (%)': [inhibition_degree(x) for x in nh3_inhibition_expanded],
        'Substrate Limitation (%)': [inhibition_degree(x) for x in substrate_limitation],
        'Overall Inhibition (%)': [inhibition_degree(x) for x in overall_inhibition],
        'Process Rate': process_rates
    })
    
    # Display dashboard with tabs
    st.markdown("## Reactor Health Analysis")
    st.write(f"Current pH: {pH_value:.2f}")
    
    tabs = st.tabs(["Inhibition Factors", "Process Rates", "Summary"])
    
    with tabs[0]:
        # Helper function to color-code cells based on inhibition severity
        def color_inhibition(val):
            try:
                val = float(val.strip('%'))
                if val < 10:
                    return f'background-color: #4CAF50; color: white'  # Green - Low inhibition
                elif val < 30:
                    return f'background-color: #FFEB3B; color: black'  # Yellow - Moderate inhibition
                elif val < 60:
                    return f'background-color: #FF9800; color: black'  # Orange - High inhibition
                else:
                    return f'background-color: #F44336; color: white'  # Red - Severe inhibition
            except:
                return ''
                
        # Format percentages
        inhibition_display = inhibition_df.copy()
        for col in inhibition_display.columns:
            if '(%)' in col:
                inhibition_display[col] = inhibition_display[col].apply(lambda x: f"{x:.1f}%")
        
        # Apply styling
        styled_df = inhibition_display.style.applymap(
            color_inhibition, 
            subset=[col for col in inhibition_display.columns if '(%)' in col]
        )
        
        st.dataframe(styled_df)
        
        st.markdown("""
        ### Interpretation Guide:
        - **0-10%**: Low/No inhibition (Green)
        - **10-30%**: Moderate inhibition (Yellow)
        - **30-60%**: High inhibition (Orange)
        - **>60%**: Severe inhibition (Red)
        
        ### Inhibition Types:
        - **pH Inhibition**: Occurs when pH is outside the optimal range for specific microorganisms
        - **H₂ Inhibition**: High hydrogen partial pressure inhibits syntrophic bacteria
        - **N Limitation**: Insufficient nitrogen for microbial growth
        - **NH₃ Inhibition**: Free ammonia inhibits methanogenic activity
        - **Substrate Limitation**: Insufficient substrate concentration limits growth rate
        """)
    
    with tabs[1]:
        # Create a dataframe for process rates
        rate_df = pd.DataFrame({
            'Process': process_names,
            'Rate': process_rates,
            'Overall Inhibition (%)': [inhibition_degree(x) for x in overall_inhibition],
        })
        
        # Create a bar chart of process rates
        st.bar_chart(rate_df.set_index('Process')['Rate'], use_container_width=True)
        
        st.write("Process rates are affected by inhibition factors and substrate availability.")
        st.write("Low process rates may indicate poor conversion efficiency.")
    
    with tabs[2]:
        # Calculate overall reactor health
        avg_inhibition = np.mean([inhibition_degree(x) for x in overall_inhibition])
        
        # Define health status based on average inhibition
        if avg_inhibition < 10:
            health_status = "Excellent"
            color = "#4CAF50"  # Green
        elif avg_inhibition < 20:
            health_status = "Good"
            color = "#8BC34A"  # Light Green
        elif avg_inhibition < 40:
            health_status = "Fair"
            color = "#FFEB3B"  # Yellow
        elif avg_inhibition < 60:
            health_status = "Poor"
            color = "#FF9800"  # Orange
        else:
            health_status = "Critical"
            color = "#F44336"  # Red
        
        # Display summary
        st.markdown(f"""
        ### Reactor Health Summary
        
        <div style="background-color: {color}; padding: 10px; border-radius: 5px; color: white;">
            <h3 style="margin: 0; text-align: center;">Health Status: {health_status}</h3>
            <h4 style="margin: 0; text-align: center;">Average Inhibition: {avg_inhibition:.1f}%</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Identify most significant inhibition factors
        st.markdown("### Key Inhibition Factors")
        
        # Calculate average inhibition by type
        avg_ph_inhibition = np.mean([inhibition_degree(x) for x in pH_inhibition])
        avg_h2_inhibition = np.mean([inhibition_degree(x) for x in h2_inhibition])
        avg_n_limitation = inhibition_degree(n_limitation)
        avg_nh3_inhibition = inhibition_degree(nh3_inhibition)
        avg_substrate_limitation = np.mean([inhibition_degree(x) for x in substrate_limitation])
        
        # Create summary dataframe
        summary_df = pd.DataFrame({
            'Inhibition Type': [
                'pH Inhibition', 
                'H₂ Inhibition',
                'N Limitation',
                'NH₃ Inhibition',
                'Substrate Limitation'
            ],
            'Average Inhibition (%)': [
                avg_ph_inhibition,
                avg_h2_inhibition,
                avg_n_limitation,
                avg_nh3_inhibition,
                avg_substrate_limitation
            ]
        }).sort_values('Average Inhibition (%)', ascending=False)
        
        st.dataframe(summary_df)
        
        # Recommendations based on the most significant inhibition factor
        st.markdown("### Recommendations")
        
        top_inhibition = summary_df.iloc[0]['Inhibition Type']
        top_value = summary_df.iloc[0]['Average Inhibition (%)']
        
        if top_value < 10:
            st.success("The reactor is operating optimally. No adjustments needed.")
        else:
            if top_inhibition == 'pH Inhibition':
                st.warning(f"""
                **pH Inhibition Detected ({top_value:.1f}%)**
                
                Current pH: {pH_value:.2f}
                
                Recommendations:
                - If pH is too low: Add alkalinity (e.g., sodium bicarbonate)
                - If pH is too high: Consider adding CO₂ or reducing alkalinity
                - Monitor VFA accumulation which can cause pH drops
                """)
            
            elif top_inhibition == 'H₂ Inhibition':
                st.warning(f"""
                **H₂ Inhibition Detected ({top_value:.1f}%)**
                
                Recommendations:
                - Optimize mixing to enhance H₂ transfer to methanogens
                - Ensure healthy hydrogenotrophic methanogen population
                - Consider reducing organic loading rate temporarily
                """)
                
            elif top_inhibition == 'N Limitation':
                st.warning(f"""
                **Nitrogen Limitation Detected ({top_value:.1f}%)**
                
                Recommendations:
                - Supplement feedstock with nitrogen-rich substrates
                - Consider adding ammonium or urea as nitrogen source
                - Maintain C:N ratio between 20:1 and 30:1
                """)
                
            elif top_inhibition == 'NH₃ Inhibition':
                st.warning(f"""
                **Ammonia Inhibition Detected ({top_value:.1f}%)**
                
                Recommendations:
                - Reduce nitrogen-rich feedstocks
                - Consider lowering pH slightly (within safe range) to reduce free ammonia
                - Dilute reactor contents or increase HRT
                - Investigate ammonia-tolerant methanogen species
                """)
                
            elif top_inhibition == 'Substrate Limitation':
                st.warning(f"""
                **Substrate Limitation Detected ({top_value:.1f}%)**
                
                Recommendations:
                - Increase organic loading rate if other parameters allow
                - Ensure proper mixing for substrate distribution
                - Consider feedstock pre-treatment to improve biodegradability
                """)
