"""
Combined figure: all 3 panels in one image for single-upload platforms.

Layout:
  ┌────────────────────────┬──────────────┐
  │   A. Mexico Map        │              │
  │        (Fig 1)         │  C. Export   │
  ├──────────┬─────────────│     Rate     │
  │ B-left   │  B-right    │  Lollipop    │
  │ Histogram│  OOP bars   │    (Fig 3)   │
  └──────────┴─────────────┴──────────────┘
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as pe
import geopandas as gpd
import warnings; warnings.filterwarnings("ignore")

OUT = "/Users/dariorocha/Desktop/TransplantDeserts_Figures/Fig_Combined_All3.png"
DATA = "/Users/dariorocha/Desktop/TransplantDeserts_Audit/data/"

# ── Palette ──────────────────────────────────────────────────────────────────
C_HUB    = "#2271B2"
C_DB_CTR = "#E69F00"
C_DB_NO  = "#8B1A2E"
C_PART   = "#009E73"
C_GRAY   = "#6A6A6A"

# ── Data ─────────────────────────────────────────────────────────────────────
ss      = pd.read_csv(DATA + "cenatra_state_summary.csv")
oop_dist = pd.read_csv(DATA + "oop_distribution_base.csv")
oop_scen = pd.read_csv(DATA + "oop_results_by_scenario.csv")

HUBS         = {"CDMX", "Jalisco", "Nuevo León"}
PARTIAL      = {"Sonora", "San Luis Potosí"}
DB_NO_CENTER = {
    "Aguascalientes","Baja California Sur","Campeche","Colima","Chiapas",
    "Durango","Guerrero","Hidalgo","Michoacán","Nayarit","Oaxaca","Zacatecas"
}
CAT_COLOR = {"hub":C_HUB, "db_center":C_DB_CTR, "db_no":C_DB_NO, "partial":C_PART}

LABELS = {
    "Aguascalientes":"AGS","Baja California":"BC","Baja California Sur":"BCS",
    "Campeche":"CAM","Coahuila":"COAH","Colima":"COL","Chiapas":"CHIS",
    "Chihuahua":"CHIH","Distrito Federal":"CDMX","Durango":"DUR",
    "Guanajuato":"GTO","Guerrero":"GRO","Hidalgo":"HGO","Jalisco":"JAL",
    "México":"EdoMex","Michoacán":"MICH","Morelos":"MOR","Nayarit":"NAY",
    "Nuevo León":"NL","Oaxaca":"OAX","Puebla":"PUE","Querétaro":"QRO",
    "Quintana Roo":"QROO","San Luis Potosí":"SLP","Sinaloa":"SIN",
    "Sonora":"SON","Tabasco":"TAB","Tamaulipas":"TAMS","Tlaxcala":"TLAX",
    "Veracruz":"VER","Yucatán":"YUC","Zacatecas":"ZAC",
}
LABEL_OVERRIDES = {
    "CDMX":(-99.15,19.4),"TLAX":(-98.25,19.35),"MOR":(-99.05,18.7),
    "AGS":(-102.3,21.8),"COL":(-104.0,19.2),"QRO":(-100.0,20.6),
    "EdoMex":(-99.75,19.6),"HGO":(-98.7,20.15),
}

def get_category(name):
    if name in HUBS:          return "hub"
    if name in PARTIAL:       return "partial"
    if name in DB_NO_CENTER:  return "db_no"
    return "db_center"

ABB = {
    "Aguascalientes":"AGS","Baja California":"BC","Baja California Sur":"BCS",
    "Campeche":"CAM","Coahuila":"COAH","Colima":"COL","Chiapas":"CHIS",
    "Chihuahua":"CHIH","CDMX":"CDMX","Durango":"DUR","Guanajuato":"GTO",
    "Guerrero":"GRO","Hidalgo":"HGO","Jalisco":"JAL","Estado de México":"EdoMex",
    "Michoacán":"MICH","Morelos":"MOR","Nayarit":"NAY","Nuevo León":"NL",
    "Oaxaca":"OAX","Puebla":"PUE","Querétaro":"QRO","Quintana Roo":"QROO",
    "San Luis Potosí":"SLP","Sinaloa":"SIN","Sonora":"SON","Tabasco":"TAB",
    "Tamaulipas":"TAMS","Tlaxcala":"TLAX","Veracruz":"VER","Yucatán":"YUC",
    "Zacatecas":"ZAC",
}

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(26, 20), facecolor="white")

# Outer grid: 1 row × 2 cols  (left panels | right lollipop)
outer = gridspec.GridSpec(1, 2,
    width_ratios=[1.55, 1],
    wspace=0.06,
    left=0.03, right=0.97, top=0.93, bottom=0.04)

# Left side: 2 rows (map on top, hist+oop below)
left_gs = gridspec.GridSpecFromSubplotSpec(2, 2,
    subplot_spec=outer[0],
    height_ratios=[1.25, 1],
    hspace=0.22,
    wspace=0.12)

ax_map  = fig.add_subplot(left_gs[0, 0:2])   # Map spans both left columns
ax_hist = fig.add_subplot(left_gs[1, 0])      # Histogram
ax_oop  = fig.add_subplot(left_gs[1, 1])      # OOP bars

# Right side: full-height lollipop
ax_lolly = fig.add_subplot(outer[1])

# Panel labels
for ax, lbl in [(ax_map,"A"),(ax_hist,"B"),(ax_oop,"B (cont.)"),(ax_lolly,"C")]:
    ax.text(-0.01, 1.03, lbl, transform=ax.transAxes,
            fontsize=14, fontweight="bold", color=C_DB_NO, va="top")

# ─────────────────────────────────────────────────────────────────────────────
# A — MEXICO MAP
# ─────────────────────────────────────────────────────────────────────────────
print("Plotting A: Map...")
gdf = gpd.read_file("/tmp/ne_admin1.zip")
mex = gdf[(gdf["iso_a2"]=="MX") & gdf["name"].notna()].copy()
mex["category"] = mex["name"].apply(get_category)
mex["label"]    = mex["name"].map(LABELS).fillna(mex["name"].str[:4])
mex["color"]    = mex["category"].map(CAT_COLOR)
mex = mex.to_crs("EPSG:4326")
mex["centroid"] = mex.geometry.centroid

mex.plot(ax=ax_map, color=mex["color"], edgecolor="white", linewidth=0.8)

for _, row in mex.iterrows():
    lbl = row["label"]
    x, y = (LABEL_OVERRIDES[lbl] if lbl in LABEL_OVERRIDES
             else (row["centroid"].x, row["centroid"].y))
    ax_map.text(x, y, lbl, ha="center", va="center",
                fontsize=8, fontweight="bold", color="white",
                path_effects=[pe.withStroke(linewidth=2, foreground="black")])

box_kw = dict(boxstyle="round,pad=0.45", ec="white", lw=1.8)
ax_map.annotate("27/32 states\nDouble Burden\n(84.4%)",
    xy=(-117,24), fontsize=11, fontweight="bold", color="white",
    bbox=dict(**box_kw, fc=C_DB_NO), ha="center", va="center")
ax_map.annotate("3 hub states:\n90.5% of all Tx performed",
    xy=(-97.5,29.5), fontsize=11, fontweight="bold", color="white",
    bbox=dict(**box_kw, fc=C_HUB), ha="center", va="center")
ax_map.annotate("12 states · zero licensed centers\n325 organs donated  →  0 local Tx",
    xy=(-95,15.5), fontsize=10.5, fontweight="bold", color="white",
    bbox=dict(**box_kw, fc=C_DB_NO), ha="center", va="center")

legend_map = [
    mpatches.Patch(fc=C_HUB,    ec="white", label="Hub Center  (n=3)\n  90.5% of all Tx performed here"),
    mpatches.Patch(fc=C_DB_CTR, ec="white", label="DB — Has Center  (n=15)\n  Exports organs AND patients"),
    mpatches.Patch(fc=C_DB_NO,  ec="white", label="DB — No Center  (n=12)\n  325 organs donated · 0 local Tx"),
    mpatches.Patch(fc=C_PART,   ec="white", label="Partial  (n=2)\n  Net exporter · <70% exported"),
]
ax_map.legend(handles=legend_map, loc="lower left", frameon=True,
              facecolor="white", edgecolor="#aaa", fontsize=10,
              title="State Category", title_fontsize=11,
              handlelength=1.4, handleheight=1.4)
ax_map.set_title(
    "Mexico's Transplant Deserts — 4-Category Geographic Classification  (CENATRA 2007–2024)",
    fontsize=13, fontweight="bold", color=C_DB_NO, pad=8)
ax_map.axis("off")

# ─────────────────────────────────────────────────────────────────────────────
# B — DISTANCE HISTOGRAM
# ─────────────────────────────────────────────────────────────────────────────
print("Plotting B: Displacement histogram...")
N_DISPLACED = 1583
all_dist    = oop_dist["dist_km"].values
MED_REP, Q3_REP, PCT1000 = 324, 684, 14.4

under = all_dist[all_dist <= 1000]
over  = all_dist[all_dist >  1000]
bins  = list(range(0, 2001, 100))

ax_hist.hist(under, bins=[b for b in bins if b<=1000],
             color="#5B9BD5", edgecolor="white", linewidth=0.4, label="≤1,000 km")
ax_hist.hist(over,  bins=[b for b in bins if b>1000],
             color="#C0392B", edgecolor="white", linewidth=0.4, label=">1,000 km")
ax_hist.axvline(MED_REP, color="black",   lw=1.8, ls="--", label=f"Median: {MED_REP} km")
ax_hist.axvline(Q3_REP,  color="#E69F00", lw=1.5, ls=":",  label=f"Q3: {Q3_REP} km")

fig.canvas.draw()
ylim = ax_hist.get_ylim()[1]
ax_hist.annotate(f"{PCT1000}%\ntraveled\n≥1,000 km",
    xy=(1350, ylim*0.58), fontsize=9, color="white", ha="center", va="center",
    bbox=dict(boxstyle="round,pad=0.4", fc="#C0392B", ec="white"))

ax_hist.set_xlabel("Road Distance to Transplant Center (km)", fontsize=10)
ax_hist.set_ylabel("Number of Patients", fontsize=10)
ax_hist.set_title(f"Travel Distance\n{N_DISPLACED:,} out-of-state patients (54.7% of cohort)",
                  fontsize=10, fontweight="bold")
ax_hist.legend(fontsize=8.5, framealpha=0.9)
ax_hist.set_xlim(0, 2100)
ax_hist.spines[["top","right"]].set_visible(False)

# ─────────────────────────────────────────────────────────────────────────────
# B (cont.) — OOP BAR CHART
# ─────────────────────────────────────────────────────────────────────────────
print("Plotting B (cont.): OOP bars...")
MONTHLY_WAGE = 425.14
oop_vals = {
    "Conservative\n(3 trips, 5 nights)": (642,  151, "#5B9BD5"),
    "Base\n(4 trips, 7 nights)":         (873,  205, "#E69F00"),
    "Liberal\n(6 trips, 14 nights)":     (1478, 348, "#C0392B"),
}
pct_notes = {
    "Conservative\n(3 trips, 5 nights)":
        f"{int(oop_scen[oop_scen.scenario=='Conservative']['pct_exceed_1x_wage'].values[0])}% >1×MW\n"
        f"{int(oop_scen[oop_scen.scenario=='Conservative']['pct_exceed_2x_wage'].values[0])}% >2×MW",
    "Base\n(4 trips, 7 nights)":
        f"100% >1×MW\n{int(oop_scen[oop_scen.scenario=='Base']['pct_exceed_2x_wage'].values[0])}% >2×MW",
    "Liberal\n(6 trips, 14 nights)":
        f"100% >1×MW\n{int(oop_scen[oop_scen.scenario=='Liberal']['pct_exceed_2x_wage'].values[0])}% >2×MW",
}

xlbls  = list(oop_vals.keys())
x      = np.arange(len(xlbls))
pcts   = [v[1] for v in oop_vals.values()]
usds   = [v[0] for v in oop_vals.values()]
colors = [v[2] for v in oop_vals.values()]

bars = ax_oop.bar(x, pcts, color=colors, width=0.6, edgecolor="white", linewidth=1)
ax_oop.axhline(100, color="#2ECC71", ls="--", lw=1.5, label="1× min wage ($425)")
ax_oop.axhline(200, color="#E74C3C", ls="--", lw=1.5, label="2× min wage ($850)")

for bar, pct, usd, note in zip(bars, pcts, usds, pct_notes.values()):
    ax_oop.text(bar.get_x()+bar.get_width()/2, pct+6,
                f"{pct}%\n(${usd:,})", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="black")
    ax_oop.text(bar.get_x()+bar.get_width()/2, -35,
                note, ha="center", va="top", fontsize=8, color=C_GRAY)

ax_oop.set_xticks(x); ax_oop.set_xticklabels(xlbls, fontsize=9)
ax_oop.set_ylabel("Modeled OOP as % of Monthly\nMinimum Wage (CONASAMI 2024)", fontsize=9)
ax_oop.set_title("Modeled Out-of-Pocket Financial Burden\nby Cost Scenario",
                 fontsize=10, fontweight="bold")
ax_oop.set_ylim(-70, max(pcts)*1.18)
ax_oop.legend(fontsize=8, loc="upper left", framealpha=0.9)
ax_oop.spines[["top","right"]].set_visible(False)

# ─────────────────────────────────────────────────────────────────────────────
# C — EXPORT RATE LOLLIPOP
# ─────────────────────────────────────────────────────────────────────────────
print("Plotting C: Lollipop...")

def assign_cat(row):
    n = row["state"]
    if row["is_hub"]:       return "hub"
    if n in PARTIAL:        return "partial"
    if n in DB_NO_CENTER:   return "db_no"
    return "db_center"

ss2 = ss.copy()
ss2["category"] = ss2.apply(assign_cat, axis=1)
ss2["net_bal"]  = ss2["n_donations"] - ss2["n_tx_performed"]
ss2["abbr"]     = ss2["state"].map(ABB).fillna(ss2["state"])
order = {"hub":0,"partial":1,"db_center":2,"db_no":3}
ss2["sort_key"] = ss2["category"].map(order)
ss2 = ss2.sort_values(["sort_key","export_rate_pct"], ascending=[True,True]).reset_index(drop=True)

y_pos   = np.arange(len(ss2))
colors3 = ss2["category"].map(CAT_COLOR).values

ax_lolly.hlines(y_pos, 0, ss2["export_rate_pct"], color=colors3, lw=2.0, alpha=0.85)
ax_lolly.scatter(ss2["export_rate_pct"], y_pos, color=colors3, s=65, zorder=5)

ax_lolly.axvline(70, color=C_GRAY, lw=1.4, ls="--", alpha=0.7)
ax_lolly.text(70.8, len(ss2)-0.5, "70%\nthreshold",
              fontsize=9, color=C_GRAY, va="top", fontweight="bold")

for i, row in ss2.iterrows():
    nb = row["net_bal"]
    if nb != 0:
        lbl = f"net +{int(nb)}" if nb >= 0 else f"net {int(nb)}"
        ax_lolly.text(row["export_rate_pct"]-0.8, i, lbl,
                      ha="right", va="center", fontsize=8,
                      color="black", fontweight="bold")

# Separator
hub_rows     = ss2[ss2["category"]=="hub"].index
partial_rows = ss2[ss2["category"]=="partial"].index
sep = (partial_rows.max()+0.5) if len(partial_rows) else (hub_rows.max()+0.5)
ax_lolly.axhline(sep, color=C_GRAY, ls=":", lw=1.5, alpha=0.7)
ax_lolly.text(1, sep+0.2, "← Peripheral states",
              fontsize=9, color=C_GRAY, va="bottom", fontstyle="italic")
ax_lolly.text(1, sep-0.2, "← Hub states",
              fontsize=9, color=C_GRAY, va="top", fontstyle="italic")

# Net donation bars
ax_r = ax_lolly.twinx()
ax_r.barh(y_pos, ss2["net_bal"].clip(lower=0), left=101, height=0.55,
          color=colors3, alpha=0.3)
ax_r.set_yticks([]); ax_r.set_ylabel("Organs\nDonated", fontsize=9, color=C_GRAY)
ax_r.set_xlim(0, 200)

ax_lolly.set_yticks(y_pos)
ax_lolly.set_yticklabels(ss2["abbr"].values, fontsize=10, fontweight="bold")
for tick, cat in zip(ax_lolly.get_yticklabels(), ss2["category"].values):
    tick.set_color(CAT_COLOR[cat])

leg3 = [
    mpatches.Patch(fc=C_HUB,    ec="none", label="Hub Center (n=3)"),
    mpatches.Patch(fc=C_DB_CTR, ec="none", label="DB — Has Center (n=15)"),
    mpatches.Patch(fc=C_DB_NO,  ec="none", label="DB — No Center (n=12)"),
    mpatches.Patch(fc=C_PART,   ec="none", label="Partial — SLP/Sonora (n=2)"),
]
ax_lolly.legend(handles=leg3, loc="lower right", fontsize=9.5,
                framealpha=0.95, title="Category", title_fontsize=10.5,
                handlelength=1.4)
ax_lolly.set_xlabel("Patients Transplanted Out-of-State (%)", fontsize=11)
ax_lolly.set_xlim(-5, 128)
ax_lolly.tick_params(axis="x", labelsize=9.5)
ax_lolly.spines[["top","right"]].set_visible(False)
ax_lolly.set_title(
    "Double Burden: Patient Export Rate by State\nCENATRA 2007–2024",
    fontsize=12, fontweight="bold", color=C_DB_NO, pad=8)

# ─────────────────────────────────────────────────────────────────────────────
# Super-title + save
# ─────────────────────────────────────────────────────────────────────────────
fig.suptitle(
    "Transplant Deserts in Mexico  \u00b7  CENATRA 2007\u20132024  \u00b7  N = 2,896 liver transplants",
    fontsize=15, fontweight="bold", color=C_DB_NO, y=0.97)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"\nCombined figure saved: {OUT}")
