"""
Stream display components
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from chemicals.elements import molecular_weight as get_mw
from puran_adm1.models.adm1_simulation import calculate_biomass_yields, calculate_effluent_COD, calculate_gas_properties
from puran_adm1.components.inhibition_display import display_inhibition_dashboard

# Define molecular weights here
C_mw = get_mw({'C': 1})
N_mw = get_mw({'N': 1})

def display_liquid_stream(stream):
    """
    Display key properties of a liquid stream (influent/effluent)
    
    Parameters
    ----------
    stream : WasteStream
        The liquid stream to display
    """
    flow = 0
    try:
        flow = stream.get_total_flow('m3/d')
    except:
        try:
            flow = stream.F_vol / 1000 * 24
        except:
            pass
    
    def safe_composite(stream, param, particle_size=None, organic=None, volatile=None, subgroup=None):
        """
        Safely get composite property value with special handling for solids to fix TSS calculation
        
        Parameters
        ----------
        stream : WasteStream
            The stream to get property from
        param : str
            The property to get
        particle_size : str or None
            Particle size filter to apply
        organic : bool or None
            Filter for organic/inorganic components
        volatile : bool or None
            Filter for volatile/non-volatile components
        subgroup : list or None
            Specific subgroup of components to consider
            
        Returns
        -------
        float or 'N/A'
            The property value or 'N/A' if not available
        """
        try:
            if hasattr(stream, 'composite'):
                # Special handling for solids (TSS calculation)
                if param == 'solids' and particle_size is None:
                    # Calculate TSS correctly by only including particulate and colloidal components
                    particulate = stream.composite('solids', particle_size='x')
                    colloidal = stream.composite('solids', particle_size='c')
                    return particulate + colloidal
                return stream.composite(param, particle_size=particle_size, 
                                       organic=organic, volatile=volatile, 
                                       subgroup=subgroup)
            return 'N/A'
        except:
            return 'N/A'
    
    def safe_get(stream, method_name, *args, **kwargs):
        """
        Safely call a method on the stream if it exists
        
        Parameters
        ----------
        stream : WasteStream
            The stream object
        method_name : str
            Name of the method to call
        *args, **kwargs
            Arguments to pass to the method
            
        Returns
        -------
        Result of the method or 'N/A' if method doesn't exist or fails
        """
        try:
            if hasattr(stream, method_name):
                method = getattr(stream, method_name)
                if callable(method):
                    return method(*args, **kwargs)
            return 'N/A'
        except:
            return 'N/A'
            
    def get_component_conc(stream, component_id):
        """Helper function to safely get a component's concentration in mg/L"""
        try:
            # Check if component exists
            if component_id not in stream.components.IDs:
                return "N/A"
            
            # Try different methods to get the concentration
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
                # Fallback to calculating from mass
                if stream.F_vol > 0:
                    try:
                        return stream.imass[component_id] * 1000 / stream.F_vol  # kg/m3 to mg/L
                    except:
                        pass
            
            # One more attempt with state data if available
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
    
    # Calculate all required values
    tss_value = safe_composite(stream, 'solids')  # Particulate + colloidal
    vss_value = safe_get(stream, 'get_VSS')
    iss_value = safe_get(stream, 'get_ISS')
    tds_value = safe_get(stream, 'get_TDS', include_colloidal=False)  # Pure dissolved solids
    
    # Map ADM1 component names to nitrogen species
    # The ADM1 model might use different component names than typical wastewater models
    # In ADM1, S_IN is inorganic nitrogen which is primarily ammonia
    ammonia_component = 'S_NH4' if 'S_NH4' in stream.components.IDs else 'S_IN'
    nitrite_component = 'S_NO2' if 'S_NO2' in stream.components.IDs else None
    nitrate_component = 'S_NO3' if 'S_NO3' in stream.components.IDs else None
    
    # Get nitrogen component concentrations
    ammonia_conc = get_component_conc(stream, ammonia_component)
    
    # For nitrite and nitrate, assume 0.0 mg/L for ADM1 influent streams
    # In anaerobic digestion, these are typically near zero
    if nitrite_component and isinstance(get_component_conc(stream, nitrite_component), (int, float)):
        nitrite_conc = get_component_conc(stream, nitrite_component)
    else:
        nitrite_conc = 0.0
        
    if nitrate_component and isinstance(get_component_conc(stream, nitrate_component), (int, float)):
        nitrate_conc = get_component_conc(stream, nitrate_component)
    else:
        nitrate_conc = 0.0
    
    # Map ADM1 component names for VFAs
    acetate_component = 'S_ac' if 'S_ac' in stream.components.IDs else 'S_Ac'
    propionate_component = 'S_pro' if 'S_pro' in stream.components.IDs else 'S_Prop'
    
    # Get VFA concentrations
    acetate_conc = get_component_conc(stream, acetate_component)
    propionate_conc = get_component_conc(stream, propionate_component)
    
    # Calculate total VFAs if both values are numeric
    if isinstance(acetate_conc, (int, float)) and isinstance(propionate_conc, (int, float)):
        total_vfa = acetate_conc + propionate_conc
    else:
        total_vfa = "N/A"
    
    # Main stream parameters (basic)
    basic_params = {
        'Parameter': [
            'Flow', 'pH', 'Alkalinity'
        ],
        'Value': [
            f"{flow:,.2f} m³/d",
            f"{getattr(stream, 'pH', 'N/A')}",
            f"{getattr(stream, 'SAlk', 'N/A')} meq/L"  # Fixed: using SAlk instead of alkalinity
        ]
    }
    
    # Oxygen demand parameters
    od_params = {
        'Parameter': [
            'COD', 'BOD', 'uBOD', 'ThOD', 'cnBOD'
        ],
        'Value': [
            f"{safe_composite(stream, 'COD'):,.1f} mg/L" if safe_composite(stream, 'COD') != 'N/A' else "N/A mg/L",
            f"{safe_composite(stream, 'BOD'):,.1f} mg/L" if safe_composite(stream, 'BOD') != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'uBOD', safe_composite(stream, 'uBOD')):,.1f} mg/L" if getattr(stream, 'uBOD', safe_composite(stream, 'uBOD')) != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'ThOD', safe_composite(stream, 'ThOD')):,.1f} mg/L" if getattr(stream, 'ThOD', safe_composite(stream, 'ThOD')) != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'cnBOD', safe_composite(stream, 'cnBOD')):,.1f} mg/L" if getattr(stream, 'cnBOD', safe_composite(stream, 'cnBOD')) != 'N/A' else "N/A mg/L"
        ]
    }
    
    # Carbon parameters
    carbon_params = {
        'Parameter': [
            'TC', 'TOC'
        ],
        'Value': [
            f"{getattr(stream, 'TC', safe_composite(stream, 'C')):,.1f} mg/L" if getattr(stream, 'TC', safe_composite(stream, 'C')) != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'TOC', safe_composite(stream, 'C', organic=True)):,.1f} mg/L" if getattr(stream, 'TOC', safe_composite(stream, 'C', organic=True)) != 'N/A' else "N/A mg/L"
        ]
    }
    
    # Nitrogen parameters
    nitrogen_params = {
        'Parameter': [
            'TN', 'TKN',
            'Ammonia-N', 'Nitrite-N', 'Nitrate-N'
        ],
        'Value': [
            f"{safe_composite(stream, 'N'):,.1f} mg/L" if safe_composite(stream, 'N') != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'TKN', 'N/A'):,.1f} mg/L" if getattr(stream, 'TKN', 'N/A') != 'N/A' else "N/A mg/L",
            f"{ammonia_conc:,.1f} mg/L" if isinstance(ammonia_conc, (int, float)) else "N/A mg/L",
            f"{nitrite_conc:,.1f} mg/L" if isinstance(nitrite_conc, (int, float)) else "N/A mg/L",
            f"{nitrate_conc:,.1f} mg/L" if isinstance(nitrate_conc, (int, float)) else "N/A mg/L"
        ]
    }
    
    # Other nutrients
    nutrient_params = {
        'Parameter': [
            'TP', 'TK', 'TMg', 'TCa'
        ],
        'Value': [
            f"{safe_composite(stream, 'P'):,.1f} mg/L" if safe_composite(stream, 'P') != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'TK', safe_composite(stream, 'K')):,.1f} mg/L" if getattr(stream, 'TK', safe_composite(stream, 'K')) != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'TMg', safe_composite(stream, 'Mg')):,.1f} mg/L" if getattr(stream, 'TMg', safe_composite(stream, 'Mg')) != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'TCa', safe_composite(stream, 'Ca')):,.1f} mg/L" if getattr(stream, 'TCa', safe_composite(stream, 'Ca')) != 'N/A' else "N/A mg/L"
        ]
    }
    
    # Solids parameters
    solids_params = {
        'Parameter': [
            'TSS', 'VSS', 'ISS', 'TDS', 'TS'
        ],
        'Value': [
            f"{tss_value:,.1f} mg/L" if tss_value != 'N/A' else "N/A mg/L",
            f"{vss_value:,.1f} mg/L" if vss_value != 'N/A' else "N/A mg/L",
            f"{iss_value:,.1f} mg/L" if iss_value != 'N/A' else "N/A mg/L",
            f"{tds_value:,.1f} mg/L" if tds_value != 'N/A' else "N/A mg/L",
            f"{getattr(stream, 'dry_mass', 'N/A'):,.1f} mg/L" if getattr(stream, 'dry_mass', 'N/A') != 'N/A' else "N/A mg/L"
        ]
    }
    
    # VFA parameters (particularly relevant for ADM1)
    vfa_params = {
        'Parameter': [
            'Acetate', 'Propionate', 'Total VFAs'
        ],
        'Value': [
            f"{acetate_conc:,.1f} mg/L" if isinstance(acetate_conc, (int, float)) else "N/A mg/L",
            f"{propionate_conc:,.1f} mg/L" if isinstance(propionate_conc, (int, float)) else "N/A mg/L",
            f"{total_vfa:,.1f} mg/L" if isinstance(total_vfa, (int, float)) else "N/A mg/L"
        ]
    }
    
    # Display in organized tabs to keep the interface clean
    tabs = st.tabs(["Basic", "Oxygen Demand", "Carbon", "Nitrogen", "Other Nutrients", "Solids", "VFAs"])
    
    with tabs[0]:
        st.dataframe(pd.DataFrame(basic_params), hide_index=True)
    
    with tabs[1]:
        st.dataframe(pd.DataFrame(od_params), hide_index=True)
    
    with tabs[2]:
        st.dataframe(pd.DataFrame(carbon_params), hide_index=True)
    
    with tabs[3]:
        st.dataframe(pd.DataFrame(nitrogen_params), hide_index=True)
    
    with tabs[4]:
        st.dataframe(pd.DataFrame(nutrient_params), hide_index=True)
    
    with tabs[5]:
        st.dataframe(pd.DataFrame(solids_params), hide_index=True)
    
    with tabs[6]:
        st.dataframe(pd.DataFrame(vfa_params), hide_index=True)

def display_liquid_stream_enhanced(stream, inf_stream=None):
    """
    Display key properties of a liquid stream with enhanced information
    
    Parameters
    ----------
    stream : WasteStream
        The liquid stream to display
    inf_stream : WasteStream, optional
        The influent stream for comparison, by default None
    """
    # Print component IDs for debugging
    st.markdown("<details><summary>Debug Information</summary>", unsafe_allow_html=True)
    st.write("Component IDs available:")
    st.code(", ".join(stream.components.IDs))
    
    # Check if specific components exist
    st.write("Checking for specific components:")
    important_components = ['S_NH4', 'S_IN', 'S_NO2', 'S_NO3', 'S_ac', 'S_Ac', 'S_pro', 'S_Prop']
    for comp in important_components:
        st.write(f"{comp}: {'Present' if comp in stream.components.IDs else 'Not found'}")
    st.markdown("</details>", unsafe_allow_html=True)
    
    # First display the basic information using the original function
    display_liquid_stream(stream)
    
    # If this is an effluent stream and we have an influent for comparison, show yields
    if inf_stream is not None:
        st.markdown("**Biomass Yields:**")
        try:
            biomass_yields = calculate_biomass_yields(inf_stream, stream)
            st.write(f"- VSS Yield: {biomass_yields['VSS_yield']:.4f} kg VSS/kg COD")
            st.write(f"- TSS Yield: {biomass_yields['TSS_yield']:.4f} kg TSS/kg COD")
        except Exception as e:
            st.error(f"Error calculating biomass yields: {str(e)}")
    
    # Show COD values for any liquid stream
    st.markdown("**COD Values:**")
    try:
        cod_values = calculate_effluent_COD(stream)
        st.write(f"- Soluble COD: {cod_values['soluble_COD']:.1f} mg/L")
        st.write(f"- Particulate COD: {cod_values['particulate_COD']:.1f} mg/L")
        st.write(f"- Total COD: {cod_values['total_COD']:.1f} mg/L")
        
        # If we have influent to compare, show removal efficiency
        if inf_stream is not None:
            cod_removal = (1 - stream.COD/inf_stream.COD) * 100
            st.write(f"- COD Removal Efficiency: {cod_removal:.1f}%")
    except Exception as e:
        st.error(f"Error calculating COD values: {str(e)}")

def display_gas_stream(stream):
    """
    Display gas stream properties
    
    Parameters
    ----------
    stream : WasteStream
        The gas stream to display
    """
    try:
        gas_props = calculate_gas_properties(stream)
        
        data = {
            'Parameter': ['Flow', 'Methane', 'CO2', 'H2'],
            'Value': [
                f"{gas_props['flow_total']:.2f} Nm³/d",
                f"{gas_props['methane_percent']:.2f} vol/vol%",
                f"{gas_props['co2_percent']:.2f} vol/vol%",
                f"{gas_props['h2_ppmv']:.2f} ppmv"
            ]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True)
    except Exception as e:
        st.error(f"Error displaying gas stream: {e}")

def render_stream_properties(session_state):
    """
    Render the stream properties section
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    from puran_adm1.models.adm1_simulation import create_influent_stream
    
    # Try to import the pH calculation module
    try:
        from calculate_ph_and_alkalinity_fixed import update_ph_and_alkalinity
        CALCULATE_PH_AVAILABLE = True
    except ImportError:
        try:
            from calculate_ph_and_alkalinity import update_ph_and_alkalinity
            CALCULATE_PH_AVAILABLE = True
        except ImportError:
            CALCULATE_PH_AVAILABLE = False
    
    # Add Inhibition & Process Health tab
    tabs = st.tabs(["Stream Properties", "Inhibition & Process Health"])
    
    with tabs[0]:
        with st.expander("Stream Properties", expanded=True):
            tabs_streams = st.tabs([
                "Influent (Common)",
                "Effluent Sim 1", "Biogas Sim 1",
                "Effluent Sim 2", "Biogas Sim 2",
                "Effluent Sim 3", "Biogas Sim 3"
            ])

            # Influent tab
            with tabs_streams[0]:
                st.markdown("**Influent**")
                try:
                    temp_inf = create_influent_stream(
                        Q=session_state.Q,
                        Temp=308.15,
                        concentrations=session_state.influent_values
                    )
                    if temp_inf:
                        display_liquid_stream_enhanced(temp_inf)
                except Exception as e:
                    st.error(f"Error displaying influent: {e}")
            
            # Effluent and biogas tabs for each simulation
            for i in range(3):
                sys_res = session_state.sim_results[i]
                eff_tab = tabs_streams[1 + 2*i]
                gas_tab = tabs_streams[2 + 2*i]

                # Effluent tab
                with eff_tab:
                    st.markdown(f"**Effluent - Simulation {i+1}**")
                    if sys_res and all(sys_res):
                        _, inf_i, eff_i, _ = sys_res
                        
                        # For each effluent stream we display, calculate the pH and alkalinity
                        if CALCULATE_PH_AVAILABLE:
                            update_ph_and_alkalinity(eff_i)
                            
                        display_liquid_stream_enhanced(eff_i, inf_stream=inf_i)
                    else:
                        st.info(f"No results for Simulation {i+1} yet.")
                
                # Biogas tab
                with gas_tab:
                    st.markdown(f"**Biogas - Simulation {i+1}**")
                    if sys_res and all(sys_res):
                        _, _, _, gas_i = sys_res
                        
                        # For gas streams, we still call update_ph_and_alkalinity to set appropriate default values
                        if CALCULATE_PH_AVAILABLE:
                            update_ph_and_alkalinity(gas_i)
                            
                        display_gas_stream(gas_i)
                    else:
                        st.info(f"No results for Simulation {i+1} yet.")
    
    # Display inhibition dashboard in the second tab
    with tabs[1]:
        st.header("Process Health Analysis")
        # Add simulation selector
        sim_options = [f"Simulation {i+1}" for i in range(3) if session_state.sim_results[i] is not None and all(session_state.sim_results[i])]
        if not sim_options:
            st.info("Run at least one simulation to view process health analysis.")
        else:
            selected_sim = st.selectbox("Select Simulation", sim_options)
            sim_index = int(selected_sim.split()[1]) - 1
            if session_state.sim_results[sim_index] is not None and all(session_state.sim_results[sim_index]):
                display_inhibition_dashboard(simulation_results=session_state.sim_results[sim_index])
            else:
                st.info(f"No results available for {selected_sim}.")