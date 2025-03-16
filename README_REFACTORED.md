# ADM1 Simulation Application

This is a Streamlit application for running Anaerobic Digestion Model No. 1 (ADM1) simulations.

## Features

- Run three concurrent ADM1 simulations with different reactor parameters on the same feedstock
- Use AI recommendations to generate feedstock state variables and kinetic parameters
- Visualize simulation results with interactive plots
- Compare biomass yields and COD values across simulations
- Export simulation results for further analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/puranwater/adm1-simulation.git
cd adm1-simulation

# Install the package in development mode
pip install -e .
```

## Usage

### Windows

```bash
# Run the application using the batch file
run_adm1.bat
```

### Linux/Mac

```bash
# Run the application using the Python script
python run_adm1.py
```

## Structure

The application is structured as follows:

```
puran_adm1/
├── __init__.py           # Package initialization and thermo setup
├── api/
│   ├── __init__.py
│   └── gemini.py         # Google Gemini API integration
├── components/
│   ├── __init__.py
│   ├── feedstock_editor.py # Feedstock and kinetics editor components
│   ├── plotting.py       # Plotting components
│   ├── sidebar.py        # Sidebar components
│   └── stream_display.py # Stream display components
├── models/
│   ├── __init__.py
│   └── adm1_simulation.py # ADM1 simulation models
├── utils/
│   ├── __init__.py
│   └── styling.py        # Styling utilities
└── views/
    ├── __init__.py
    └── main_view.py      # Main application view
```

## Troubleshooting

If you encounter import errors or Thermo object errors:

1. Make sure the package is properly installed:
   ```bash
   pip install -e .
   ```

2. Use the run_adm1.py script or run_adm1.bat file to start the application, as they properly set up the Python path and ensure all components are initialized.

3. If you have issues with QSDsan, make sure it's installed:
   ```bash
   pip install qsdsan
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## License

MIT License