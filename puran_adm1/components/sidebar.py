"""
Sidebar component for the Streamlit application
"""
import streamlit as st
from puran_adm1.api.gemini import GeminiClient

def render_sidebar(session_state):
    """
    Render the sidebar for the application
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
    """
    with st.sidebar:
        st.header("Feedstock & Simulation Setup")
        
        # --- AI Assistant Mode Selection ---
        st.subheader("AI Assistant Mode")
        mode = st.radio(
            "Choose what the AI should provide:",
            ("Feedstock State Variables Only", "Feedstock + Reaction Kinetics"),
            index=0
        )
        # This bool will decide if we ask for kinetics or not
        session_state.use_kinetics = (mode == "Feedstock + Reaction Kinetics")

        # --- AI Assistant for feedstock (and possibly kinetics) ---
        st.subheader("AI Feedstock Assistant")
        feedstock_description = st.text_area(
            "Describe your feedstock in natural language:",
            placeholder="Example: Food waste with ~40% carbs, ~20% proteins, ~10% lipids, etc."
        )
        if st.button("Get AI Recommendations"):
            with st.spinner("Getting AI recommendations..."):
                # Initialize the Gemini client
                gemini_client = GeminiClient()
                
                # Get recommendations
                response = gemini_client.get_adm1_recommendations(
                    feedstock_description,
                    include_kinetics=session_state.use_kinetics
                )
                
                if response:
                    session_state.ai_recommendations = response
                    # Parse the JSON
                    try:
                        (fv, fe, kv, ke) = gemini_client.parse_recommendations(
                            response,
                            include_kinetics=session_state.use_kinetics
                        )
                        
                        # Update session state
                        if fv:
                            session_state.influent_values.update(fv)
                        if fe:
                            session_state.influent_explanations.update(fe)
                        
                        # If user only wants feedstock, do not update or store kinetic data
                        if session_state.use_kinetics and kv:
                            session_state.kinetic_params.update(kv)
                        if session_state.use_kinetics and ke:
                            session_state.kinetic_explanations.update(ke)
                        
                        st.success("AI recommendations parsed and stored successfully!")
                    except Exception as e:
                        st.error(f"Error parsing recommendations: {e}")

        # --- Common Influent Flow ---
        st.subheader("Common Influent Flow")
        Q_new = st.number_input(
            "Influent Flow Rate (m³/d)",
            min_value=1.0,
            value=float(session_state.Q),
            step=1.0
        )
        if Q_new != session_state.Q:
            session_state.Q = Q_new

        # --- Reactor & Integration Parameters (Three Simulations) ---
        st.subheader("Parameters for Each Simulation")
        for i in range(3):
            st.markdown(f"**Simulation {i+1}**")
            temp_val = st.number_input(
                f"Temperature (K) for Sim {i+1}",
                min_value=273.15,
                value=float(session_state.sim_params[i]['Temp']),
                step=0.1,
                key=f"temp_sim_{i}"
            )
            hrt_val = st.number_input(
                f"HRT (days) for Sim {i+1}",
                min_value=1.0,
                value=float(session_state.sim_params[i]['HRT']),
                step=1.0,
                key=f"hrt_sim_{i}"
            )
            method_val = st.selectbox(
                f"Integration Method for Sim {i+1}",
                ["BDF","RK45","RK23","DOP853","Radau","LSODA"],
                index=["BDF","RK45","RK23","DOP853","Radau","LSODA"].index(
                    session_state.sim_params[i]['method']
                ),
                key=f"method_sim_{i}"
            )
            session_state.sim_params[i]['Temp'] = temp_val
            session_state.sim_params[i]['HRT'] = hrt_val
            session_state.sim_params[i]['method'] = method_val
        
        # --- Simulation time and step
        st.subheader("Simulation Time & Step")
        sim_time = st.slider(
            "Simulation Time (days)",
            10.0, 300.0,
            session_state.simulation_time,
            step=5.0
        )
        t_step = st.slider(
            "Time Step (days)",
            0.01, 1.0,
            session_state.t_step,
            step=0.01
        )
        session_state.simulation_time = sim_time
        session_state.t_step = t_step
        
        return _render_run_button(session_state)

def _render_run_button(session_state):
    """
    Render the "Run All Simulations" button and handle running the simulations
    
    Parameters
    ----------
    session_state : streamlit.session_state
        Streamlit session state
        
    Returns
    -------
    bool
        Whether the simulations were run successfully
    """
    from puran_adm1.models.adm1_simulation import create_influent_stream, run_simulation
    
    if st.button("Run All Simulations"):
        try:
            with st.spinner("Creating influent stream..."):
                common_inf = create_influent_stream(
                    Q=session_state.Q,
                    Temp=session_state.sim_params[0]['Temp'],
                    concentrations=session_state.influent_values
                )
            
            # Run each sim
            for i in range(3):
                with st.spinner(f"Running Simulation {i+1}..."):
                    sys_i, inf_i, eff_i, gas_i = run_simulation(
                        Q=session_state.Q,
                        Temp=session_state.sim_params[i]['Temp'],
                        HRT=session_state.sim_params[i]['HRT'],
                        concentrations=session_state.influent_values,
                        kinetic_params=session_state.kinetic_params,
                        simulation_time=session_state.simulation_time,
                        t_step=session_state.t_step,
                        method=session_state.sim_params[i]['method'],
                        use_kinetics=session_state.use_kinetics
                    )
                    session_state.sim_results[i] = (sys_i, inf_i, eff_i, gas_i)
            st.success("All simulations completed successfully!")
            return True
        except Exception as e:
            st.error(f"Error running simulations: {e}")
            return False
    return False