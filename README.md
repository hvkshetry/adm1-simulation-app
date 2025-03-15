# ADM1 Simulation Application

This repository contains a refactored Streamlit application for simulating the Anaerobic Digestion Model No. 1 (ADM1). The application includes an important fix for QSDsan's WasteStream class to correctly calculate Total Suspended Solids (TSS) for streams containing soluble components.

## Key Features

- **Multiple Concurrent Simulations**: Run and compare three ADM1 simulations with different reactor parameters on the same feedstock
- **Fixed TSS Calculation**: Patched WasteStream.get_TSS() method to correctly exclude soluble components from TSS calculations
- **Interactive Dashboard**: User-friendly interface for setting parameters and visualizing results
- **pH and Alkalinity Calculation**: Accurate pH and alkalinity calculations based on acid-base equilibria

## TSS Calculation Fix

The application includes a patch for QSDsan's WasteStream class to fix the TSS calculation for soluble components. See [TSS_FIX_README.md](TSS_FIX_README.md) for details about the bug and the implemented solution.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/hvkshetry/adm1-simulation-app.git
   cd adm1-simulation-app
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app-refactored.py
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

## Project Structure

- `app-refactored.py`: Main entry point with TSS calculation monkey patch
- `calculate_ph_and_alkalinity_fixed.py`: pH and alkalinity calculations
- `puran_adm1/`: Core simulation package
  - `models/`: Simulation models including ADM1
  - `views/`: Streamlit UI components and views
  - `components/`: UI components and widgets
  - `utils/`: Utility functions
  - `api/`: API integration for the AI assistant

## Usage

After launching the application with `streamlit run app-refactored.py`, you can:

1. Configure feedstock composition
2. Set reactor parameters for three different simulations
3. Run simulations concurrently
4. Compare results across different operating conditions

## License

This project is licensed under the MIT License - see the LICENSE file for details.