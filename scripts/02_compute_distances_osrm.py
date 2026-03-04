"""
TRANSPLANT DESERTS — Script 02: Compute road distances via OSRM
===============================================================
Input:
  - ../data/cenatra_liver_cohort.csv

Output:
  - ../data/state_pair_distances.csv  (road km between each displaced-patient state pair)

Method:
  - Uses Open Source Routing Machine (OSRM) public API (driving)
  - Distances are STATE CENTROID to STATE CENTROID (approximation)
  - NOTE: Original paper used patient-level municipality → transplant hospital distances,
    which gives more precise results. This centroid approach underestimates median distance
    by ~55 km (269 km computed vs 324 km reported).

Dependencies:
  pip install requests pandas
"""

import pandas as pd
import numpy as np
import requests
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# State centroids (lat, lon) — approximate geographic centers
STATE_COORDS = {
    1: (21.8818, -102.2916), 2: (30.7196, -115.4583), 3: (26.0192, -111.3484),
    4: (18.0042,  -92.7117), 5: (25.4260, -101.0000), 6: (19.1223, -104.0067),
    7: (16.7569,  -93.1292), 8: (28.6329, -106.0691), 9: (19.4326,  -99.1332),
   10: (24.0277, -104.6532),11: (21.0190, -101.2574),12: (17.5507,  -99.5051),
   13: (20.0911,  -98.7624),14: (20.6597, -103.3496),15: (19.2826,  -99.6557),
   16: (19.7008, -101.1844),17: (18.9242,  -99.2216),18: (21.7514, -105.2114),
   19: (25.6866, -100.3161),20: (17.0732,  -96.7266),21: (19.0414,  -98.2063),
   22: (20.5888, -100.3899),23: (19.1817,  -88.4791),24: (22.1565, -100.9855),
   25: (24.8087, -107.3940),26: (29.2972, -110.3309),27: (17.9869,  -92.9303),
   28: (23.7369,  -99.1411),29: (19.3139,  -98.2404),30: (19.1738,  -96.1342),
   31: (20.9674,  -89.5926),32: (22.7709, -102.5832),
}

def osrm_distance(lat1, lon1, lat2, lon2, retries=3):
    """Get driving distance in km from OSRM public API."""
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get('code') == 'Ok':
                    return data['routes'][0]['distance'] / 1000  # meters → km
        except Exception:
            pass
        time.sleep(1)
    return np.nan

# Load cohort
cohort = pd.read_csv(DATA_DIR / "cenatra_liver_cohort.csv")
disp = cohort[cohort['cod_res'] != cohort['cod_tx']].copy()

# Get unique state pairs
pairs = disp.groupby(['cod_res', 'cod_tx']).size().reset_index(name='n')
pairs = pairs[pairs['cod_res'].between(1,32) & pairs['cod_tx'].between(1,32)]
print(f"Unique displaced state pairs: {len(pairs)}")

# Check for existing results to skip
out_path = DATA_DIR / "state_pair_distances.csv"
if out_path.exists():
    existing = pd.read_csv(out_path)
    done_pairs = set(zip(existing['code_res'], existing['code_tx']))
    print(f"Already computed: {len(done_pairs)} pairs")
else:
    existing = pd.DataFrame()
    done_pairs = set()

# Compute missing pairs
results = [] if not out_path.exists() else existing.to_dict('records')
for i, row in pairs.iterrows():
    key = (int(row['cod_res']), int(row['cod_tx']))
    if key in done_pairs:
        continue
    lat1, lon1 = STATE_COORDS[key[0]]
    lat2, lon2 = STATE_COORDS[key[1]]
    dist = osrm_distance(lat1, lon1, lat2, lon2)
    results.append({'code_res': key[0], 'code_tx': key[1], 'n': int(row['n']), 'dist_km': dist})
    print(f"  {key[0]} → {key[1]}: {dist:.1f} km")
    time.sleep(0.1)

df_out = pd.DataFrame(results)
df_out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}  ({len(df_out)} pairs)")
print("Done — Script 02 complete.")
print("\nNOTE: To improve precision, replace STATE_COORDS with municipality-level coordinates")
print("for each patient's residence and the transplant hospital's exact location.")
