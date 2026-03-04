"""
TRANSPLANT DESERTS — Script 01: Build CENATRA liver cohort
===========================================================
Input:
  - Base CSV (2007–2020):  Downloads/CENATRA Trasplantes y Donadores/Trasplantes/Trasplantes.csv
  - Quarterly XLSX (2021–2024): same folder

Output:
  - ../data/cenatra_liver_cohort.csv   (one row per transplant, 2007–2024)
  - ../data/cenatra_state_summary.csv  (state-level aggregates)

Encoding note:
  - Base CSV is UTF-8 with BOM (utf-8-sig); organ values use proper UTF-8 (HÍGADO, RIÑÓN…)
  - Quarterly XLSX files are plain UTF-8 via openpyxl

Column mapping (final output):
  cod_res  = CODIGO ENTIDAD FEDERATIVA RESIDENCIA  (1–32; -1=VNPPE; 99=no disp)
  cod_tx   = CODIGO ENTIDAD FEDERATIVA TRASPLANTE  (1–32)
  cod_don  = CODIGO ENTIDAD FEDERATIVA ORGANO      (state where organ was procured)
  fecha    = FECHA TRASPLANTE
  year     = extracted from fecha
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_CSV  = Path("/Users/dariorocha/Downloads/CENATRA Trasplantes y Donadores /Trasplantes/Trasplantes.csv")
QTRLY_DIR = Path("/Users/dariorocha/Downloads/CENATRA Trasplantes y Donadores /Trasplantes/")
OUT_DIR   = Path(__file__).parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)

HUB_CODES = {9, 14, 19}   # CDMX=9, Jalisco=14, Nuevo León=19

# ── Helpers ────────────────────────────────────────────────────────────────────
def find_col(df, *keywords, exclude=()):
    """Find first column containing ALL keywords (and NONE of exclude keywords)."""
    matches = [c for c in df.columns
               if all(k in c for k in keywords) and not any(x in c for x in exclude)]
    return matches[0] if matches else None

# ── Load base CSV ─────────────────────────────────────────────────────────────
print("Loading base CSV...")
base = pd.read_csv(BASE_CSV, encoding='utf-8-sig', low_memory=False)
base.columns = [c.strip().lower().replace(' ', '_') for c in base.columns]

# Map columns
CR = find_col(base, 'codigo', 'residencia')
CT = find_col(base, 'codigo', 'trasplante', exclude=('organo',))
CD = find_col(base, 'codigo', 'organo')
FE = find_col(base, 'fecha', 'trasplante')

base_liver = base[base['organo'].str.upper().str.contains('H[IÍ]G', regex=True, na=False)].copy()
base_liver['year'] = pd.to_datetime(base_liver[FE], errors='coerce', dayfirst=True).dt.year
base_liver = base_liver[base_liver['year'] <= 2019].rename(
    columns={CR: 'cod_res', CT: 'cod_tx', CD: 'cod_don', FE: 'fecha'}
)[['cod_res', 'cod_tx', 'cod_don', 'fecha', 'year']]
print(f"  Base (≤2019): {len(base_liver)} liver transplants")

# ── Load quarterly XLSX ───────────────────────────────────────────────────────
print("Loading quarterly XLSX files...")
frames = []
for f in sorted(QTRLY_DIR.glob("Trasplantes*.xlsx")):
    try:
        q = pd.read_excel(f, engine='openpyxl')
        q.columns = [str(c).strip().lower().replace(' ', '_') for c in q.columns]
        CR = find_col(q, 'codigo', 'residencia')
        CT = find_col(q, 'codigo', 'trasplante', exclude=('organo',))
        CD = find_col(q, 'codigo', 'organo')
        FE = find_col(q, 'fecha', 'trasplante')
        OR = find_col(q, 'organo', exclude=('institucion', 'entidad', 'codigo'))
        if OR is None:
            continue
        ql = q[q[OR].str.upper().str.contains('H[IÍ]G', regex=True, na=False)].copy()
        ql['year'] = pd.to_datetime(ql[FE], errors='coerce', dayfirst=True).dt.year
        ql = ql.rename(columns={CR: 'cod_res', CT: 'cod_tx', CD: 'cod_don', FE: 'fecha'})
        for c in ['cod_res', 'cod_tx', 'cod_don']:
            if c not in ql.columns:
                ql[c] = np.nan
        frames.append(ql[['cod_res', 'cod_tx', 'cod_don', 'fecha', 'year']])
        print(f"  {f.name}: {len(ql)} liver rows")
    except Exception as e:
        print(f"  WARN {f.name}: {e}")

qtrly = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
qtrly_2020p = qtrly[qtrly['year'] >= 2020].copy()
print(f"  Quarterly (≥2020): {len(qtrly_2020p)}")

# ── Combine & clean ──────────────────────────────────────────────────────────
liver = pd.concat([base_liver, qtrly_2020p], ignore_index=True)
for c in ['cod_res', 'cod_tx', 'cod_don']:
    liver[c] = pd.to_numeric(liver[c], errors='coerce')

liver_valid = liver[liver['cod_res'].between(1, 32) & liver['cod_tx'].between(1, 32)].copy()
print(f"\nFinal cohort: {len(liver_valid)} liver transplants (valid state codes)")
print(f"Year range: {liver_valid['year'].min():.0f}–{liver_valid['year'].max():.0f}")

# ── Save cohort ───────────────────────────────────────────────────────────────
liver_valid.to_csv(OUT_DIR / "cenatra_liver_cohort.csv", index=False)
print(f"Saved: {OUT_DIR / 'cenatra_liver_cohort.csv'}")

# ── State-level summary ───────────────────────────────────────────────────────
state_names = {
    1:"Aguascalientes",2:"Baja California",3:"Baja California Sur",4:"Campeche",
    5:"Coahuila",6:"Colima",7:"Chiapas",8:"Chihuahua",9:"CDMX",10:"Durango",
    11:"Guanajuato",12:"Guerrero",13:"Hidalgo",14:"Jalisco",15:"Estado de México",
    16:"Michoacán",17:"Morelos",18:"Nayarit",19:"Nuevo León",20:"Oaxaca",
    21:"Puebla",22:"Querétaro",23:"Quintana Roo",24:"San Luis Potosí",25:"Sinaloa",
    26:"Sonora",27:"Tabasco",28:"Tamaulipas",29:"Tlaxcala",30:"Veracruz",
    31:"Yucatán",32:"Zacatecas"
}

disp = liver_valid[liver_valid['cod_res'] != liver_valid['cod_tx']]
sdf = pd.DataFrame({'code': range(1, 33)}).set_index('code')
sdf['state'] = pd.Series(state_names)
sdf['n_donations']    = liver_valid.groupby('cod_don').size()
sdf['n_tx_performed'] = liver_valid.groupby('cod_tx').size()
sdf['n_residents_tx'] = liver_valid.groupby('cod_res').size()
sdf['n_displaced']    = disp.groupby('cod_res').size()
sdf = sdf.fillna(0)
sdf['export_rate_pct'] = np.where(
    sdf['n_residents_tx'] > 0,
    sdf['n_displaced'] / sdf['n_residents_tx'] * 100, np.nan)
sdf['net_exporter']      = sdf['n_donations'] > sdf['n_tx_performed']
sdf['high_displacement'] = sdf['export_rate_pct'] >= 70
sdf['double_burden']     = sdf['net_exporter'] & sdf['high_displacement']
sdf['zero_center']       = sdf['n_tx_performed'] == 0
sdf['is_hub']            = sdf.index.isin(HUB_CODES)

sdf.reset_index().to_csv(OUT_DIR / "cenatra_state_summary.csv", index=False)
print(f"Saved: {OUT_DIR / 'cenatra_state_summary.csv'}")
print("\nDone — Script 01 complete.")
