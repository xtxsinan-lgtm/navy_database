"""Three Reddit-ready charts from data/export_2021_2025_commissioned.csv.
Run from repo root: python charts/make_charts.py
NOTE: the export holds tonnage *commissioned* per year (new entries into service), not total fleet tonnage.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

CSV = "data/export_2021_2025_commissioned.csv"
OUT = "charts"
WEST = "NATO-TR+JP+PH+TW+AU+NZ"
GROUPS = [("CN", "China", "#eb6834"), (WEST, "NATO (excl. Turkey) + JP/PH/TW/AU/NZ", "#2a78d6"), ("RU", "Russia", "#1baf7a")]
INK, MUTED, SURF = "#0b0b0b", "#52514e", "#fcfcfb"
YEARS = [2021, 2022, 2023, 2024, 2025]
SRC = "Source: Wikipedia-derived navy_database; commissioned ships 2021–2025. Class-level displacement (mixed full/standard/submerged); 11 ships w/o data counted as 0."

mpl.rcParams.update({"font.family": "DejaVu Sans", "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "text.color": INK, "axes.edgecolor": MUTED, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False})

d = pd.read_csv(CSV)
d["kt"] = d.class_displacement_t.fillna(0) / 1000
yr = d.pivot_table(index="service_year", columns="group", values="kt", aggfunc="sum").reindex(YEARS).fillna(0)

def style(ax):
    ax.yaxis.grid(True, color="#e3e2de", lw=0.8); ax.set_axisbelow(True)
    ax.tick_params(length=0)

def foot(fig):
    fig.text(0.02, 0.012, SRC, fontsize=7.5, color=MUTED, ha="left", va="bottom", wrap=True)

# ---- Chart 1: grouped bars -------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7.5), dpi=200)
w = 0.26
for i, (k, name, c) in enumerate(GROUPS):
    xs = [x + (i - 1) * (w + 0.02) for x in range(5)]
    bars = ax.bar(xs, yr[k], w, color=c, label=name, zorder=3)
    for b, v in zip(bars, yr[k]):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:,.0f}", ha="center", va="bottom", fontsize=9, color=INK)
ax.set_xticks(range(5)); ax.set_xticklabels(YEARS, fontsize=12)
ax.set_ylabel("Tonnage commissioned (thousand tonnes)"); style(ax)
ax.set_ylim(0, yr.values.max() * 1.12)
ax.legend(frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0), fontsize=9)
fig.suptitle("Warship tonnage commissioned per year, 2021–2025", x=0.02, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=(0, 0.05, 1, 0.95)); foot(fig)
fig.savefig(f"{OUT}/1_annual_commissioned_tonnage.png"); plt.close(fig)

# ---- Chart 2: China / West ratio -------------------------------------------
ann = yr["CN"] / yr[WEST]
cum = yr["CN"].cumsum() / yr[WEST].cumsum()
fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
ax.axhline(1, color=MUTED, lw=1, ls="--", zorder=2)
ax.set_xlim(-0.35, 4.35)
ax.text(-0.3, 1.04, "parity (1.0×)", color=MUTED, fontsize=9, ha="left")
ax.plot(range(5), ann, color="#eb6834", lw=1.5, alpha=0.45, marker="o", ms=7, zorder=3, label="Single year")
ax.plot(range(5), cum, color="#eb6834", lw=2.5, marker="o", ms=8, zorder=4, label="Cumulative since 2021")
for x, v in zip(range(1, 5), ann.iloc[1:]):
    if x == 4: ax.text(x - 0.07, v, f"{v:.2f}×", ha="right", va="center", fontsize=9, color=MUTED)
    else: ax.text(x + 0.07, v + 0.04, f"{v:.2f}×", ha="left", va="bottom", fontsize=9, color=MUTED)
for x, v in zip(range(5), cum):
    ax.text(x, v + 0.14, f"{v:.2f}×", ha="center", fontsize=10, fontweight="bold", color=INK)
ax.set_xticks(range(5)); ax.set_xticklabels(YEARS, fontsize=12)
ax.set_ylabel("China ÷ West tonnage commissioned"); style(ax); ax.set_ylim(0, max(ann.max(), cum.max()) * 1.2)
ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=10)
fig.suptitle("China's commissioning pace vs. the US-aligned bloc", x=0.02, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=(0, 0.06, 1, 0.95)); foot(fig)
fig.savefig(f"{OUT}/2_china_vs_west_ratio.png"); plt.close(fig)

# ---- Chart 3: by ship type, 2021-2025 total --------------------------------
def kind(c):
    s = c.lower()
    if "aircraft carrier" in s: return "Aircraft carrier"
    if any(t in s for t in ["landing", "amphibious", "juan carlos", "trieste"]): return "Amphibious"
    if "submarine" in s: return "Submarine"
    if any(t in s for t in ["destroyer"]): return "Destroyer"
    if "frigate" in s: return "Frigate"
    return "Corvette / patrol / mine / LCS"
d["type"] = d["class"].map(kind)
order = ["Aircraft carrier", "Amphibious", "Destroyer", "Frigate", "Submarine", "Corvette / patrol / mine / LCS"]
tcol = {"Aircraft carrier": "#6250d6", "Amphibious": "#e87ba4", "Destroyer": "#2a78d6", "Frigate": "#1baf7a",
        "Submarine": "#eda100", "Corvette / patrol / mine / LCS": "#9b9a94"}
t = d.pivot_table(index="group", columns="type", values="kt", aggfunc="sum").reindex(columns=order).fillna(0)
fig, ax = plt.subplots(figsize=(10, 7), dpi=200)
labels = [n for _, n, _ in GROUPS]
for xi, (k, _, _) in enumerate(GROUPS):
    bottom = 0
    for ty in order:
        v = t.loc[k, ty]
        if v <= 0: continue
        ax.bar(xi, v, 0.55, bottom=bottom, color=tcol[ty], edgecolor=SURF, linewidth=2, zorder=3, label=ty if xi == 0 else None)
        if v > 25: ax.text(xi, bottom + v / 2, f"{v:,.0f}", ha="center", va="center", fontsize=9, color=INK, fontweight="bold")
        bottom += v
    ax.text(xi, bottom + 6, f"{bottom:,.0f} kt", ha="center", fontsize=11, fontweight="bold")
ax.set_xticks(range(3)); ax.set_xticklabels(["China", "NATO (excl. TR)\n+ JP/PH/TW/AU/NZ", "Russia"], fontsize=11)
ax.set_ylabel("Tonnage commissioned 2021–2025 (thousand tonnes)"); style(ax); ax.set_ylim(0, t.sum(axis=1).max() * 1.1)
h, l = ax.get_legend_handles_labels(); seen = {}
for hh, ll in zip(h, l): seen.setdefault(ll, hh)
ax.legend([seen[o] for o in order if o in seen], [o for o in order if o in seen], frameon=False, loc="upper right", fontsize=9)
fig.suptitle("What was commissioned, 2021–2025, by ship type", x=0.02, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=(0, 0.05, 1, 0.95)); foot(fig)
fig.savefig(f"{OUT}/3_by_ship_type.png"); plt.close(fig)

print(yr.round(1)); print(ann.round(2).to_dict(), cum.round(2).to_dict()); print(t.round(1))
