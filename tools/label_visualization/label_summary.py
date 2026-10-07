import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator

# ==============================
# Load data
# ==============================
df = pd.read_excel(
    "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG/stress_label_84.xlsx"
)
df = df.set_index("Numéro")

# ==============================
# Helper: annotate bars
# ==============================
def annotate_hist(ax, counts, patches, fontsize=9):
    for count, patch in zip(counts, patches):
        if count > 0:
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                count,
                int(count),
                ha="center",
                va="bottom",
                fontsize=fontsize
            )

def annotate_bar(ax, bars, fontsize=10):
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                int(height),
                ha="center",
                va="bottom",
                fontsize=fontsize
            )

# ==============================
# Figure layout
# ==============================
fig, axes = plt.subplots(3, 6, figsize=(24, 12))

# ======================================================
# Column 1 — Dataset statistics
# ======================================================
# Age
ages = df["Age"].dropna()
counts, bins, patches = axes[0, 0].hist(
    ages,
    bins=range(int(ages.min()), int(ages.max()) + 2),
    edgecolor="black",
    color="#90CAF9",
    alpha=0.8
)
annotate_hist(axes[0, 0], counts, patches)

axes[0, 0].set_title("Age Distribution")
axes[0, 0].set_xlabel("Age (years)")
axes[0, 0].set_ylabel("Count")
axes[0, 0].yaxis.set_major_locator(MaxNLocator(integer=True))
axes[0, 0].grid(axis="y", linestyle="--", alpha=0.6)

# Gender
genders = df["Genre"].dropna()
gender_counts = genders.value_counts()
bars = axes[1, 0].bar(
    ["Male", "Female"],
    [gender_counts.get("M", 0), gender_counts.get("F", 0)],
    color=["#42A5F5", "#EF5350"],
    edgecolor="black"
)
annotate_bar(axes[1, 0], bars)

axes[1, 0].set_title("Gender Distribution")
axes[1, 0].set_ylabel("Count")
axes[1, 0].yaxis.set_major_locator(MaxNLocator(integer=True))
axes[1, 0].grid(axis="y", linestyle="--", alpha=0.6)
max_count = max(gender_counts.get("M", 0), gender_counts.get("F", 0))
axes[1, 0].set_ylim(0, int(max_count*1.1))

# Amateur / Pro
pro = df["Amateur/Pro/Pré"].dropna()
pro_counts = pro.value_counts()
bars = axes[2, 0].bar(
    ["Amateur", "professionnelle"],
    [pro_counts.get("Amateur", 0), pro_counts.get("préprofessionnelle", 0)],
    color=["#568203", "#FFFACD"],
    edgecolor="black"
)
annotate_bar(axes[2, 0], bars)

axes[2, 0].set_title("Professional Distribution")
axes[2, 0].set_ylabel("Count")
axes[2, 0].yaxis.set_major_locator(MaxNLocator(integer=True))
axes[2, 0].grid(axis="y", linestyle="--", alpha=0.6)
max_count = max(pro_counts.get("Amateur", 0), pro_counts.get("préprofessionnelle", 0))
axes[2, 0].set_ylim(0, int(max_count*1.1))

# ======================================================
# Helper plotting functions
# ======================================================
def plot_pdf(ax, data, title, color, annotate=True, low=0, degree=10):
    # FORCE numeric conversion
    data = pd.to_numeric(data, errors="coerce").dropna()

    if data.empty:
        ax.set_title(title + " (no data)")
        ax.axis("off")
        return

    counts, bins, patches = ax.hist(
        data,
        bins=range(int(data.min()), int(data.max()) + 2),
        edgecolor="black",
        color=color,
        alpha=0.8
    )

    if annotate:
        annotate_hist(ax, counts, patches)

    ax.set_xlim(low, degree)
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", linestyle="--", alpha=0.6)

def plot_cdf(ax, data, title, color):
    data = np.sort(data.astype(float))
    cdf = np.arange(1, len(data) + 1) / len(data)
    ax.plot(data, cdf, linewidth=3)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("CDF")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.6)

# ======================================================
# Column 2 — EX1
# ======================================================
plot_pdf(
    axes[0, 1],
    df["stress perçu EX1 juge 1"].dropna(),
    "EX1 – Judge Stress (PDF)",
    "#1E88E5"
)

plot_cdf(
    axes[0, 2],
    df["stress perçu EX1 juge 1"].dropna(),
    "EX1 – Judge Stress (CDF)",
    "#1E88E5"
)

plot_pdf(
    axes[0, 3],
    df["Stress ressenti plié (EX1)"].dropna(),
    "EX1 – Self-Reported Stress",
    "#FFB74D"
)

# ======================================================
# Column 3 — EX2
# ======================================================
plot_pdf(
    axes[1, 1],
    df["stress perçu EX2 juge 1"].dropna(),
    "EX2 – Judge Stress (PDF)",
    "#2E7D32"
)

plot_cdf(
    axes[1, 2],
    df["stress perçu EX2 juge 1"].dropna(),
    "EX2 – Judge Stress (CDF)",
    "#2E7D32"
)

plot_pdf(
    axes[1, 3],
    df["Stress ressenti frappé (EX2)"].dropna(),
    "EX2 – Self-Reported Stress",
    "#FFA726"
)

# ======================================================
# Column 4 — EX3
# ======================================================
plot_pdf(
    axes[2, 1],
    df["stress perçu EX3 juge 1"].dropna(),
    "EX3 – Judge Stress (PDF)",
    "#8E24AA"
)

plot_cdf(
    axes[2, 2],
    df["stress perçu EX3 juge 1"].dropna(),
    "EX3 – Judge Stress (CDF)",
    "#8E24AA"
)

plot_pdf(
    axes[2, 3],
    df["Stress ressenti battement (EX3)"].dropna(),
    "EX3 – Self-Reported Stress",
    "#FB8C00"
)

# ======================================================
# Column 5 — Well Perform
# ======================================================

plot_pdf(
    axes[0, 4],
    df["Exécution EX1 juge 1"].dropna(),
    "EX1 – Well Perform",
    "#B5563E",
    degree=20
)

plot_pdf(
    axes[1, 4],
    df["Exécution EX2 juge 1"].dropna(),
    "EX2 – Well Perform",
    "#B5563E",
    degree=20
)

plot_pdf(
    axes[2, 4],
    df["Exécution EX3 juge 1"].dropna(),
    "EX3 – Well Perform",
    "#B5563E",
    degree=20
)

# ======================================================
# Column 6 — TAS
# ======================================================

plot_pdf(
    axes[0, 5],
    df["TAS-20"].dropna(),
    "TAS-20",
    "#5DB0A8",
    low=26,
    degree=78
)

plot_pdf(
    axes[1, 5],
    df["Stress Cohen"].dropna(),
    "Stress Cohen",
    "#5DB0A8",
    low=10,
    degree=39
)

plot_pdf(
    axes[2, 5],
    df["STAI-Y trait"].dropna(),
    "STAI-Y trait",
    "#5DB0A8",
    low=28,
    degree=73
)

# ======================================================
# Global adjustments
# ======================================================
fig.suptitle("Dance Stress Dataset Overview", fontsize=18, fontweight="bold")
fig.text(
    0.5, 0.94,
    "(84 dancers, Judge-annotated + self-reported stress)",
    ha="center",
    fontsize=13,
    color="gray"
)

plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig("Dataset_Summary_Aligned_EXs.png", dpi=500)
plt.show()

