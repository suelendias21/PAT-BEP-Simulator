# PAT — Desktop BEP Simulator (Section 2.2)

This first version of the simulator uses correlations to estimate the turbine-mode best efficiency point (BEP) from the pump-mode BEP. It uses **PySide6** for the desktop interface, Matplotlib for charts, and a separate calculation module, `models.py`.

## Installation and launch on Windows

1. Install Python 3.11 or later on Windows and select the option to add it to PATH.
2. Open a terminal in the project folder and run the following commands.

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   python app.py
   ```

   You can also run `iniciar_windows.bat` after installing the dependencies in your default Python environment.

## Input fields

| Field | Unit | Required? |
|---|---|---|
| Pump efficiency at BEP, ηp | % | Yes |
| Hydraulic efficiency, ηh | % | Optional (required for Schmiedl) |
| Pump flow rate at BEP, Qp | m³/h | Optional |
| Pump head at BEP, Hp | m | Optional |

The simulator converts efficiencies from percentages to fractions before calculating (70% = 0.70). Enter hydraulic efficiency separately from overall pump efficiency. If you omit ηh, the table marks the Schmiedl result as unavailable.

The simulator reports the head ratio `h` and the flow rate ratio `q`. When you supply the corresponding pump values, it also reports `Ht,BEP = h × Hp,BEP` and `Qt,BEP = q × Qp,BEP`.

Section 2.2 provides correlations for head and flow rate. Turbine-mode efficiency and power at BEP are outside the scope of these correlations.

## Implemented equations (section 2.2, p. 2)

- Stepanoff (1957): `h = 1/ηp`; `q = 1/√ηp`
- Childs (1962): `h = 1/ηp`; `q = 1/ηp`
- Sharma (1985): `h = 1/(ηp^1.2)`; `q = 1/(ηp^0.8)`
- Alatorre-Frenk (1994): `h = 1/(0.85 ηp^5 + 0.385)`; `q = (0.85 ηp^5 + 0.385)/(2 ηp^9.5 + 0.205)`
- Schmiedl (1988): `h = -1.4 + 2.5/ηh`; `q = -1.5 + 2.4/ηh²`

The simulator uses the formulas exactly as transcribed in the source document. The document discusses the limits of empirical correlations and leaves the validity ranges for the five methods unspecified. The simulator flags atypical results and reports their calculated values. For scientific use, check the formulas against the original papers and validate the predictions against experimental results.

## Tests

```powershell
python -m pip install pytest
python -m pytest -q
```

## Build a Windows executable

After installing Python, run `gerar_executavel_windows.bat`. PyInstaller creates a portable executable in `dist\PAT_BEP_Desktop\` for Windows machines with a compatible architecture. You can use Inno Setup or an equivalent tool to create a separate installer with a shortcut and an uninstaller.

Run the build on Windows.

## Project structure

- `models.py` — equations and validation, independent of Qt.
- `app.py` — PySide6 interface and Matplotlib charts.
- `tests/test_models.py` — automated calculation tests.
- `requirements.txt` — interface dependencies.
- `gerar_executavel_windows.bat` — Windows packaging.

Source — *Modelos y correlaciones físicas candidatas para el modelado híbrido (física + ML) de bombas operando como turbinas (PAT)* [Candidate physical models and correlations for hybrid modeling (physics + ML) of pumps operating as turbines (PAT)], Sebastián Valencia et al., September 2026. Equations (1)–(6), sections 2.1 and 2.2.
