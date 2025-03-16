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
    
    # Calculate two sets of overall inhibition values
    # 1. With substrate limitation (for the original display)
    # 2. Without substrate limitation (for the health assessment)
    overall_inhibition = []
    overall_inhibition_no_substrate = []
    
    # Create expanded inhibition factors to match process names length
    h2_inhibition_expanded = [1.0, 1.0, h2_inhibition[0], h2_inhibition[1], 
                             h2_inhibition[2], h2_inhibition[3], 1.0, 1.0]
    
    nh3_inhibition_expanded = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, nh3_inhibition, 1.0]
    
    for i, process in enumerate(process_names):
        # Each inhibition factor is between 0-1, where 1 means no inhibition
        # Calculate overall inhibition with substrate limitation
        if i == 6:  # Acetate uptake affected by ammonia
            with_substrate = pH_inhibition[i] * n_limitation * nh3_inhibition * substrate_limitation[i]
            no_substrate = pH_inhibition[i] * n_limitation * nh3_inhibition
        elif i in [2, 3, 4, 5]:  # LCFA, valerate, butyrate, propionate uptake affected by H2
            with_substrate = pH_inhibition[i] * n_limitation * h2_inhibition_expanded[i] * substrate_limitation[i]
            no_substrate = pH_inhibition[i] * n_limitation * h2_inhibition_expanded[i]
        else:  # Other processes
            with_substrate = pH_inhibition[i] * n_limitation * substrate_limitation[i]
            no_substrate = pH_inhibition[i] * n_limitation
        
        overall_inhibition.append(with_substrate)
        overall_inhibition_no_substrate.append(no_substrate)
    
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
        'Safety Margin (%)': [inhibition_degree(x) for x in substrate_limitation],
        'Overall (without substrate) (%)': [inhibition_degree(x) for x in overall_inhibition_no_substrate],
        'Overall Inhibition (%)': [inhibition_degree(x) for x in overall_inhibition],
        'Process Rate': process_rates
    })
    
    # Display dashboard with tabs
    st.markdown("## Reactor Health Analysis")
    st.write(f"Current pH: {pH_value:.2f}")
    
    tabs = st.tabs(["Inhibition Factors", "Process Rates", "Summary"])
    
    with tabs[0]:
        # Helper function to color-code cells based on inhibition severity
        def color_inhibition(val, col_name=None):
            try:
                val = float(val.strip('%'))
                
                # Special coloring for Safety Margin (substrate availability)
                if col_name and 'Safety Margin' in col_name:
                    # For safety margin in table, we're showing substrate limitation %
                    # Higher values (green) = more limitation = higher safety margin
                    if val > 60:  # More than 60% limitation means high safety margin
                        return f'background-color: #4CAF50; color: white'  # Green - High safety
                    elif val > 30:  # More than 30% limitation means good safety margin
                        return f'background-color: #8BC34A; color: black'  # Light Green - Good safety
                    elif val > 10:  # More than 10% limitation means moderate safety margin
                        return f'background-color: #FFEB3B; color: black'  # Yellow - Moderate safety
                    else:  # Less than 10% limitation means low safety margin
                        return f'background-color: #F44336; color: white'  # Red - Low safety margin
                else:  # Standard inhibition coloring (lower is better)
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
            lambda v, col=None: color_inhibition(v, col),
            subset=[col for col in inhibition_display.columns if '(%)' in col]
        )
        
        st.dataframe(styled_df)
        
        # Add a safety margin explanation to the dashboard
        st.markdown("""
        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-top: 10px;">
        <h5 style="margin-top: 0;">💡 Understanding the Safety Margin</h5>
        <p style="margin-bottom: 0;">The <b>Safety Margin</b> column shows substrate limitation percentages. 
        <ul>
          <li><b>High values</b> (green): Greater substrate limitation = <b>higher safety margin</b> = more reserve capacity</li>
          <li><b>Low values</b> (red/orange): Less substrate limitation = <b>lower safety margin</b> = operating closer to maximum capacity</li>
        </ul>
        <p>A high safety margin (substrate limitation) means your system is not kinetically saturated and has reserve capacity to handle shock loads and toxic inhibitors.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### Interpretation Guide:
        - **0-10%**: Low/No inhibition (Green)
        - **10-30%**: Moderate inhibition (Yellow)
        - **30-60%**: High inhibition (Orange)
        - **>60%**: Severe inhibition (Red)
        
        ### Inhibition Types and Safety Factors:
        - **pH Inhibition**: Occurs when pH is outside the optimal range for specific microorganisms
        - **H₂ Inhibition**: High hydrogen partial pressure inhibits syntrophic bacteria
        - **N Limitation**: Insufficient nitrogen for microbial growth
        - **NH₃ Inhibition**: Free ammonia inhibits methanogenic activity
        - **Safety Margin**: Higher values indicate greater substrate limitation, providing better protection against shock loads and inhibitors
        """)
    
    with tabs[1]:
        # Create a dataframe for process rates
        rate_df = pd.DataFrame({
            'Process': process_names,
            'Rate': process_rates,
            'Overall Inhibition (%)': [inhibition_degree(x) for x in overall_inhibition_no_substrate],
        })
        
        # Create a bar chart of process rates
        st.bar_chart(rate_df.set_index('Process')['Rate'], use_container_width=True)
        
        st.write("Process rates are affected by inhibition factors and substrate availability.")
        st.write("Low process rates may indicate poor conversion efficiency.")
    
    with tabs[2]:
        # Calculate overall inhibition values from true inhibition factors (no substrate limitation)
        true_inhibition_values = [inhibition_degree(x) for x in overall_inhibition_no_substrate]
            
        # Use maximum inhibition value instead of average (processes are in series)
        max_inhibition = max(true_inhibition_values)
        max_inhibition_process = process_names[true_inhibition_values.index(max_inhibition)]
        
        # We'll still calculate average for reference purposes
        avg_inhibition = np.mean(true_inhibition_values)
        
        # Define health status based on maximum inhibition (worst case)
        if max_inhibition < 10:
            health_status = "Excellent"
            color = "#4CAF50"  # Green
        elif max_inhibition < 20:
            health_status = "Good"
            color = "#8BC34A"  # Light Green
        elif max_inhibition < 40:
            health_status = "Fair"
            color = "#FFEB3B"  # Yellow
        elif max_inhibition < 60:
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
            <h4 style="margin: 0; text-align: center;">Maximum Inhibition: {max_inhibition:.1f}%</h4>
            <p style="margin: 0; text-align: center;">Rate-limiting process: {max_inhibition_process}</p>
        </div>
        <p style="margin-top: 10px;"><small>Note: Health status is based on the maximum inhibition since biogas production 
        is limited by the slowest process in the series.</small></p>
        """, unsafe_allow_html=True)
        
        # Identify most significant inhibition factors
        st.markdown("### Key Inhibition Factors")
        
        # Calculate maximum inhibition by type (excluding substrate limitation)
        # For inhibition factors, we want the maximum value as it represents the worst case
        max_ph_inhibition = max([inhibition_degree(x) for x in pH_inhibition])
        max_h2_inhibition = max([inhibition_degree(x) for x in h2_inhibition]) if len(h2_inhibition) > 0 else 0
        max_n_limitation = inhibition_degree(n_limitation)
        max_nh3_inhibition = inhibition_degree(nh3_inhibition)
        
        # Calculate safety margin directly from limitation percentages
        # Higher substrate limitation percentage = higher safety margin
        safety_margin_values = [inhibition_degree(x) for x in substrate_limitation]
        # Find the minimum limitation value (worst case - lowest safety margin)
        min_safety_margin = min(safety_margin_values) if safety_margin_values else 0
        min_safety_idx = safety_margin_values.index(min_safety_margin) if safety_margin_values else 0
        min_safety_margin_process = process_names[min_safety_idx]
        
        # Create inhibition summary dataframe (excluding substrate limitation)
        # Using maximum values instead of averages
        summary_df = pd.DataFrame({
            'Inhibition Type': [
                'pH Inhibition', 
                'H₂ Inhibition',
                'N Limitation',
                'NH₃ Inhibition'
            ],
            'Maximum Inhibition (%)': [
                max_ph_inhibition,
                max_h2_inhibition,
                max_n_limitation,
                max_nh3_inhibition
            ]
        }).sort_values('Maximum Inhibition (%)', ascending=False)
        
        # Display safety margin separately
        st.markdown(f"### Safety Margin Assessment")
        
        # Evaluate safety margin based on substrate limitation percentage
        # Higher limitation percentage = better safety margin
        if min_safety_margin > 60:
            safety_status = "High"
            safety_color = "#4CAF50"  # Green
            safety_message = "The system has a high safety margin against shock loads and inhibitory conditions."
        elif min_safety_margin > 30:
            safety_status = "Good"
            safety_color = "#8BC34A"  # Light Green
            safety_message = "The system has a good safety margin, providing adequate buffer against upsets."
        elif min_safety_margin > 10:
            safety_status = "Moderate"
            safety_color = "#FFEB3B"  # Yellow
            safety_message = "The system has a moderate safety margin. Consider monitoring closely."
        else:
            safety_status = "Low"
            safety_color = "#F44336"  # Red
            safety_message = "The system has a low safety margin and may be operating near maximum substrate utilization rate."
            
        st.markdown(f"""
        <div style="background-color: {safety_color}; padding: 10px; border-radius: 5px; color: black; margin-bottom: 20px;">
            <h4 style="margin: 0; text-align: center;">Safety Margin: {safety_status} ({min_safety_margin:.1f}% substrate limitation)</h4>
            <p style="margin: 0; text-align: center;">Limiting process: {min_safety_margin_process}</p>
        </div>
        {safety_message}
        <p style="margin-top: 10px;"><small>Note: Safety margin assessment is based on substrate limitation percentage, 
        with higher limitation values indicating greater reserve capacity against shock loads and inhibitors.</small></p>
        """, unsafe_allow_html=True)
        
        st.markdown("### Key Inhibition Factors")
        
        st.dataframe(summary_df)
        
        # Recommendations based on the most significant inhibition factor
        st.markdown("### Recommendations")
        
        top_inhibition = summary_df.iloc[0]['Inhibition Type']
        top_value = summary_df.iloc[0]['Maximum Inhibition (%)']
        
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
                
            # We no longer have 'Substrate Limitation' in our top inhibition factors
            # Instead, display safety margin recommendations separately
            
        # Display safety margin recommendations
        st.markdown("### Safety Margin Recommendations")
        
        if min_safety_margin > 60:
            st.success(f"""
            **High Safety Margin ({min_safety_margin:.1f}% substrate limitation)**
            
            Your system has significant reserve capacity and is well-protected against:
            - Shock organic loads
            - Toxic inhibition
            - Temperature fluctuations
            
            Consider:
            - Increasing organic loading rate to improve biogas production
            - Evaluating if HRT can be reduced to increase throughput
            """)
        elif min_safety_margin > 30:
            st.info(f"""
            **Good Safety Margin ({min_safety_margin:.1f}% substrate limitation)**
            
            Your system has adequate reserve capacity for normal operation.
            
            Consider:
            - Maintaining current organic loading rate
            - Gradually testing higher loading rates if increased production is desired
            """)
        elif min_safety_margin > 10:
            st.info(f"""
            **Moderate Safety Margin ({min_safety_margin:.1f}% substrate limitation)**
            
            Your system has limited buffer against upsets.
            
            Consider:
            - Monitoring process closely
            - Maintaining consistent feeding patterns
            - Avoiding rapid changes in feedstock composition
            """)
        else:
            st.warning(f"""
            **Low Safety Margin ({min_safety_margin:.1f}% substrate limitation)**
            
            Your system is operating close to maximum substrate utilization rate with minimal safety margin.
            
            Recommendations:
            - Consider reducing HRT to introduce more substrate limitation
            - Maintain consistent operating conditions
            - Monitor for inhibitory compounds that could slow the process further
            - Consider adding additional biomass to increase safety margin
            """)
