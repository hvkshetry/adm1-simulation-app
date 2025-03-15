# TSS Calculation Fix for QSDsan

## Problem

The QSDsan library has an issue with TSS (Total Suspended Solids) calculations where soluble components like acetate (S_ac) are incorrectly contributing to the TSS value, even though they are dissolved substances. This leads to unrealistic TSS values for streams containing soluble components.

For example, a pure acetate stream with S_ac = 50 kg/m³ was showing a TSS value of 46,129.9 mg/L despite acetate being classified as a soluble component (`particle_size = "Soluble"`) in the QSDsan component database.

## Root Cause

After examining the QSDsan codebase, I found that:

1. In the `_waste_stream.py` file, the `get_TSS()` method calls `composite('solids', particle_size='x')` when a specific particle size is provided.

2. However, when called with the default `particle_size=None`, the original implementation doesn't properly exclude soluble components.

3. The `composite()` function calculates solids content based on components' `i_mass` property, which is defined for all components including soluble ones.

4. When a WasteStream contains soluble components with non-zero `i_mass` values (like acetate), these incorrectly contribute to the TSS calculation.

## Solution

The solution applies a simple but effective patch to the `WasteStream.get_TSS()` method:

1. When a specific particle size is requested (`'s'`, `'c'`, or `'x'`), we use the original method.

2. For the default case (when `particle_size=None`), we explicitly calculate TSS as the sum of particulate and colloidal components only:
   ```python
   particulate_tss = self.composite('solids', particle_size='x')
   colloidal_tss = self.composite('solids', particle_size='c')
   return particulate_tss + colloidal_tss
   ```

This ensures that soluble components like acetate (S_ac) never contribute to TSS calculations, regardless of their other properties.

## Universal Applicability

This solution is universally applicable because:

1. It maintains the original API and function signature of `get_TSS()`
2. It preserves all existing behaviors for specific particle size requests
3. It correctly handles the default case by explicitly excluding soluble components
4. It works for all component types in the QSDsan database
5. The monkey patching approach allows the fix to be applied without modifying the QSDsan source code

For streams containing acetate and other soluble components, this fix will ensure TSS calculations accurately reflect only the suspended (non-dissolved) solids in the stream, providing more realistic results for wastewater treatment simulations.