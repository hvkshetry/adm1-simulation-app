# ADM1 Simulation Application

This repository contains a Streamlit-based application for simulating the Anaerobic Digestion Model No. 1 (ADM1). The application includes an important fix for QSDsan's WasteStream class to correctly calculate Total Suspended Solids (TSS) for streams containing soluble components.

## Key Features

- **Multiple Concurrent Simulations**: Run and compare three ADM1 simulations with different reactor parameters on the same feedstock
- **Fixed TSS Calculation**: Patched WasteStream.get_TSS() method to correctly exclude soluble components from TSS calculations
- **Interactive Dashboard**: User-friendly interface for setting parameters and visualizing results
- **pH and Alkalinity Calculation**: Accurate pH and alkalinity calculations based on acid-base equilibria
- **AI Assistant**: Get recommendations for feedstock parameters through natural language descriptions (requires Gemini API key)

## TSS Calculation Fix

The application includes a patch for QSDsan's WasteStream class to fix the TSS calculation for soluble components. See [TSS_FIX_README.md](TSS_FIX_README.md) for details about the bug and the implemented solution.

## Installation

### Clone the Repository

```bash
git clone https://github.com/hvkshetry/adm1-simulation-app.git
cd adm1-simulation-app
```

### Method 1: Install Using pip

```bash
pip install -e .
```

### Method 2: Install Dependencies Directly

```bash
pip install -r requirements.txt
```

## Configuration

1. For AI assistant functionality, copy the `.env.template` file to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit the `.env` file to add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   You can obtain a Gemini API key from [Google AI Studio](https://ai.google.dev/).
   
   Note: The application will still function without a Gemini API key, but the AI recommendations feature will not be available.

## Usage

### Running the Application

```bash
streamlit run app-refactored.py
```

### Using the Application

1. **Configure feedstock composition**:
   - Manually adjust the ADM1 state variables in the feedstock editor
   - Or use the AI assistant to get recommendations based on a natural language description

2. **Set simulation parameters**:
   - Configure flow rate, temperature, HRT, and other parameters for each simulation
   - Select the integration method (BDF is recommended for most cases)

3. **Run simulations**:
   - Click "Run All Simulations" to execute the model with your parameters
   - The application will run all three simulations concurrently

4. **Analyze results**:
   - View stream properties (influent, effluent, biogas) for each simulation
   - Explore various plots to visualize and compare results
   - Export data as CSV or plots as HTML for further analysis

## Project Structure

```
adm1-simulation-app/
├── app-refactored.py                  # Main application entry point
├── calculate_ph_and_alkalinity.py     # Original pH calculation module
├── calculate_ph_and_alkalinity_fixed.py # Improved pH calculation module
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package installation script
├── LICENSE                            # MIT License
├── README.md                          # This file
├── TSS_FIX_README.md                  # Details about the TSS calculation fix
├── .env.template                      # Template for environment variables
├── .gitignore                         # Git ignore file
└── puran_adm1/                        # Core package
    ├── __init__.py                    # Package initialization
    ├── api/                           # API integration modules
    │   ├── __init__.py
    │   └── ai_assistant.py            # Gemini AI integration
    ├── components/                    # UI components
    │   ├── __init__.py
    │   ├── feedstock_editor.py        # Feedstock parameters editor
    │   ├── plotting.py                # Plotting components
    │   ├── sidebar.py                 # Sidebar controls
    │   └── stream_display.py          # Stream data display
    ├── models/                        # Simulation models
    │   ├── __init__.py
    │   └── adm1_simulation.py         # ADM1 simulation implementation
    ├── utils/                         # Utility modules
    │   ├── __init__.py
    │   └── styling.py                 # UI styling utilities
    └── views/                         # Application views
        ├── __init__.py
        └── main_view.py               # Main view implementation
```

## Dependencies

- streamlit
- pandas
- numpy
- matplotlib
- plotly
- qsdsan
- exposan
- chemicals
- python-dotenv
- google-generativeai (for AI recommendations)

## About ADM1

The Anaerobic Digestion Model No. 1 (ADM1) is a mathematical model for simulating the anaerobic digestion process, widely used for the design and optimization of biogas plants. This implementation uses QSDsan and EXPOsan packages for the core ADM1 model.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.