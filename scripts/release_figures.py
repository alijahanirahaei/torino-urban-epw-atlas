"""Scientific atlas figures from the same corrected table as the downloads."""

import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir() + "/torino-atlas-mpl")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
import numpy as np
from build_release import K_COLORS, CATEGORIES, SOURCE_FEATURES


def generate(repo, grid, profiles, metrics, boundary):
    folder = repo / "data/figures"
    folder.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 13,
            "axes.titlesize": 17,
            "axes.labelsize": 13,
            "savefig.dpi": 220,
        }
    )
    for k in (4, 7, 8):
        fig, ax = plt.subplots(figsize=(9, 10))
        grid.plot(
            ax=ax,
            color=grid[f"cluster_k{k}_provisional"]
            .map({c: color for c, color in enumerate(K_COLORS[k])})
            .fillna("#cccccc"),
            linewidth=0,
        )
        boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.6)
        ax.set_title(
            f"Torino morphology | k={k}\nCorrected fixed assignments, v0.2.0", pad=16
        )
        ax.set_axis_off()
        ax.legend(
            handles=[
                Patch(color=color, label=f"C{c}") for c, color in enumerate(K_COLORS[k])
            ]
            + [Patch(color="#cccccc", label="Unassigned")],
            loc="lower right",
            frameon=False,
        )
        fig.text(
            0.5,
            0.02,
            "100 m assignment pitch; overlapping 500 m morphology supports",
            ha="center",
            fontsize=12,
        )
        fig.savefig(folder / f"map_clusters_k{k}.png", bbox_inches="tight")
        plt.close(fig)
        values = profiles.loc[profiles.k == k].pivot(
            index="cluster", columns="variable", values="scaled_median"
        )[SOURCE_FEATURES]
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
        ax.set_xticks(
            range(5),
            [
                "Building\nfraction",
                "Mean\nheight",
                "Facade /\nsite",
                "Tree\ncover",
                "Grass\ncover",
            ],
        )
        ax.set_yticks(range(k), [f"C{c}" for c in range(k)])
        for i in range(k):
            for j in range(5):
                v = values.iloc[i, j]
                ax.text(
                    j,
                    i,
                    f"{v:.2f}",
                    ha="center",
                    va="center",
                    color="white" if abs(v) > 1.2 else "#222222",
                    fontsize=13,
                )
        ax.set_title(
            f"k={k} morphology profiles | corrected strict-fit population", pad=16
        )
        fig.colorbar(
            im, ax=ax, label="Median relative to archived median / IQR", extend="both"
        )
        fig.tight_layout()
        fig.savefig(folder / f"cluster_profiles_k{k}.png", bbox_inches="tight")
        plt.close(fig)
    periods = [
        "annual",
        "summer_apr_sep",
        "winter_oct_mar",
        "daytime_07_18",
        "nighttime_19_06",
    ]
    fig, ax = plt.subplots(figsize=(11, 6))
    for i, (cat, meta) in enumerate(CATEGORIES.items()):
        v = (
            metrics.loc[metrics.category == cat]
            .set_index("period")
            .loc[periods, "uhi_mean_c"]
        )
        ax.bar(
            np.arange(5) + (i - 1.5) * 0.2,
            v,
            width=0.19,
            label=cat,
            color=meta["color"],
            edgecolor="#444444",
            linewidth=0.4,
        )
    ax.set_xticks(range(5), ["Annual", "Apr-Sep", "Oct-Mar", "07-18", "19-06"])
    ax.set_ylabel("Mean modeled temperature difference (C)")
    ax.set_title("Representative UWG outputs relative to AvMY Caselle", pad=16)
    ax.set_ylim(bottom=0)
    ax.legend(title="Weather category", ncol=4, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.5,
        0.015,
        "One-decimal released EPWs; model output, not measured local UHI",
        ha="center",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(folder / "epw_uhi_by_period.png", bbox_inches="tight")
    plt.close(fig)
