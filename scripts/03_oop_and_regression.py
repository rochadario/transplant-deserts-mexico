"""
TRANSPLANT DESERTS — Script 03: OOP costs + OLS regression
===========================================================
Input:
  - ../data/cenatra_liver_cohort.csv
  - ../data/state_pair_distances.csv
  - ../data/cenatra_regression_inputs.csv  (state-level: poverty, GDP — see notes)

Output:
  - ../data/oop_results_by_scenario.csv
  - ../data/oop_distribution_base.csv
  - ../data/regression_results.csv
  - ../data/regression_summary.txt

OOP Formula (confirmed from ACS_Abstract_FINAL_v2.docx):
  Transport = MXN $1.80/km × distance × 2 (round-trip) × n_trips × 2 (persons)
  Lodging   = MXN $600/night × n_nights   (1 room)
  Lost wages= MXN $248/day × n_nights     (patient only; CONASAMI 2024)
  Total MXN → USD at exchange rate MXN $17.50/USD

Monthly minimum wage (CONASAMI 2024): MXN $248/day × 30 = MXN $7,440 = USD $425.14

Scenarios:
  Conservative: 3 trips, 5 nights
  Base:         4 trips, 7 nights  ← PRIMARY (used in abstract)
  Liberal:      6 trips, 14 nights

Regression inputs (must be prepared separately):
  - poverty_pct:  CONEVAL 2020 multidimensional poverty rate by state
  - gdp_usd:      INEGI 2022 GDP per capita (MXN), converted at MXN $17.50/USD
  - log_don:      log(n_donations + 1), from CENATRA
  - median_dist:  road distance to nearest hub (CDMX/Jalisco/Nuevo León), from Script 02

Dependencies: pip install pandas numpy statsmodels
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    import statsmodels.api as sm
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'statsmodels', '-q'])
    import statsmodels.api as sm

DATA_DIR = Path(__file__).parent.parent / "data"

# OOP parameters
MXN_KM       = 1.80
MXN_NIGHT    = 600.0
MXN_WAGE_DAY = 248.0    # CONASAMI 2024
FX           = 17.50    # MXN/USD
MONTHLY_MXN  = MXN_WAGE_DAY * 30
MONTHLY_USD  = MONTHLY_MXN / FX

SCENARIOS = {
    'Conservative': {'trips': 3, 'nights': 5},
    'Base':         {'trips': 4, 'nights': 7},
    'Liberal':      {'trips': 6, 'nights': 14},
}

def oop_usd(dist_km, trips, nights):
    transport = MXN_KM * dist_km * 2 * trips * 2
    lodging   = MXN_NIGHT * nights
    wages     = MXN_WAGE_DAY * nights
    return (transport + lodging + wages) / FX

# ── Load data ──────────────────────────────────────────────────────────────────
cohort = pd.read_csv(DATA_DIR / "cenatra_liver_cohort.csv")
dist_df = pd.read_csv(DATA_DIR / "state_pair_distances.csv")

disp = cohort[cohort['cod_res'] != cohort['cod_tx']].copy()
disp = disp.merge(dist_df[['code_res','code_tx','dist_km']],
                  left_on=['cod_res','cod_tx'], right_on=['code_res','code_tx'], how='left')
dv = disp['dist_km'].dropna()
print(f"Displaced patients with distance data: {len(dv)}/{len(disp)}")
print(f"Median distance: {dv.median():.0f} km  [IQR {dv.quantile(.25):.0f}–{dv.quantile(.75):.0f}]")
print(f"Monthly min wage: MXN {MONTHLY_MXN:,.0f} = USD ${MONTHLY_USD:.2f}")

# ── OOP by scenario ────────────────────────────────────────────────────────────
print("\n── OOP calculations ──")
oop_rows = []
for name, p in SCENARIOS.items():
    vals = dv.apply(lambda d: oop_usd(d, p['trips'], p['nights']))
    spot_computed = oop_usd(dv.median(), p['trips'], p['nights'])
    spot_reported = oop_usd(324, p['trips'], p['nights'])
    row = {
        'scenario': name, 'trips': p['trips'], 'nights': p['nights'],
        'median_oop_usd': round(vals.median(), 0),
        'median_oop_pct_wage': round(vals.median() / MONTHLY_USD * 100, 1),
        'at_median_dist_computed_usd': round(spot_computed, 0),
        'at_median_dist_reported_usd': round(spot_reported, 0),
        'at_reported_pct_wage': round(spot_reported / MONTHLY_USD * 100, 1),
        'pct_exceed_1x_wage': round((vals >= MONTHLY_USD).mean() * 100, 1),
        'pct_exceed_2x_wage': round((vals >= 2*MONTHLY_USD).mean() * 100, 1),
        'pct_exceed_3x_wage': round((vals >= 3*MONTHLY_USD).mean() * 100, 1),
    }
    oop_rows.append(row)
    print(f"  [{name}] median=${row['median_oop_usd']:.0f}  ({row['median_oop_pct_wage']:.0f}% wage)  "
          f"  at reported 324km=${spot_reported:.0f} ({row['at_reported_pct_wage']:.0f}%)")

pd.DataFrame(oop_rows).to_csv(DATA_DIR / "oop_results_by_scenario.csv", index=False)
print(f"Saved: {DATA_DIR / 'oop_results_by_scenario.csv'}")

# Save base scenario patient-level distribution
base = dv.apply(lambda d: oop_usd(d, 4, 7))
pd.DataFrame({'dist_km': dv.values, 'oop_base_usd': base.values}).to_csv(
    DATA_DIR / "oop_distribution_base.csv", index=False)
print(f"Saved: {DATA_DIR / 'oop_distribution_base.csv'}")

# ── OLS Regression ──────────────────────────────────────────────────────────────
print("\n── OLS Regression ──")
reg_path = DATA_DIR / "cenatra_regression_inputs.csv"
# Try pre-computed file (from previous session)
alt_path = DATA_DIR / "cenatra_regression_data.csv"
if not reg_path.exists() and alt_path.exists():
    reg_path = alt_path

if reg_path.exists():
    reg = pd.read_csv(reg_path)
    print(f"  Loaded: {reg_path.name}  ({len(reg)} states)")

    # Detect z-scored columns or compute them
    if 'z_log_don' not in reg.columns:
        for col in ['log_don', 'median_dist_km', 'poverty_pct', 'gdp_usd']:
            if col in reg.columns:
                reg[f'z_{col.replace("_km","").replace("_pct","").replace("_usd","")}'] = \
                    (reg[col] - reg[col].mean()) / reg[col].std()

    y = reg['export_rate']
    X = sm.add_constant(reg[['z_log_don','z_dist','z_poverty','z_gdp']])
    mdl = sm.OLS(y, X).fit()

    print(mdl.summary())
    print(f"\n  R²={mdl.rsquared:.4f}   Adj-R²={mdl.rsquared_adj:.4f}")

    # Save coefficient table
    coef_df = pd.DataFrame({
        'predictor': mdl.params.index,
        'beta': mdl.params.values,
        'std_err': mdl.bse.values,
        't_stat': mdl.tvalues.values,
        'p_value': mdl.pvalues.values,
        'ci_lo': mdl.conf_int()[0].values,
        'ci_hi': mdl.conf_int()[1].values,
    })
    coef_df.to_csv(DATA_DIR / "regression_results.csv", index=False)
    with open(DATA_DIR / "regression_summary.txt", 'w') as f:
        f.write(str(mdl.summary()))
    print(f"Saved: regression_results.csv, regression_summary.txt")
else:
    print(f"  Regression input file not found at: {reg_path}")
    print("  Please provide cenatra_regression_inputs.csv with columns:")
    print("  code, state, export_rate, log_don, median_dist_km, poverty_pct, gdp_usd")

print("\nDone — Script 03 complete.")
