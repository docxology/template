"""PCA, heatmap, and dendrogram visualizations."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visualization.advanced.labels import format_subfield_label
from visualization.style import VIZ_CONFIG

logger = logging.getLogger(__name__)


def plot_pca_embeddings(
    tfidf_matrix: np.ndarray,
    labels: list[str],
    feature_names: list[str],
    output_path: Path,
    *,
    n_loading_arrows: int = 8,
) -> Path:
    """Process plot pca embeddings."""
    from sklearn.decomposition import PCA

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 9), dpi=VIZ_CONFIG["dpi"])
    if tfidf_matrix.shape[0] < 2 or tfidf_matrix.shape[1] < 2:
        ax.text(
            0.5,
            0.5,
            "Insufficient data for PCA",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(tfidf_matrix)
    unique_labels = sorted(set(labels))
    subfield_colors = VIZ_CONFIG["subfield_colors"]
    palette = VIZ_CONFIG["palette"]
    for i, label in enumerate(unique_labels):
        mask = [lb == label for lb in labels]
        color = subfield_colors.get(label, palette[i % len(palette)])
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=color,
            label=format_subfield_label(label),
            alpha=0.65,
            s=40,
            edgecolors="white",
            linewidths=0.4,
        )

    if feature_names and n_loading_arrows > 0:
        loadings = pca.components_.T
        magnitude = np.sqrt(loadings[:, 0] ** 2 + loadings[:, 1] ** 2)
        top_idx = np.argsort(magnitude)[::-1][:n_loading_arrows]
        scale = max(abs(coords).max(), 1.0) * 0.7
        for idx in top_idx:
            dx, dy = loadings[idx] * scale
            ax.annotate(
                feature_names[idx],
                xy=(dx, dy),
                fontsize=max(VIZ_CONFIG["font_size"] - 3, 16),
                alpha=0.7,
                ha="center",
                arrowprops=dict(arrowstyle="<-", color="gray", lw=0.8),
                xytext=(dx * 1.15, dy * 1.15),
            )

    var1, var2 = pca.explained_variance_ratio_ * 100
    ax.set_xlabel(f"PC1 ({var1:.1f}% variance)", fontsize=VIZ_CONFIG["font_size"])
    ax.set_ylabel(f"PC2 ({var2:.1f}% variance)", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "PCA of TF-IDF Document Embeddings",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.legend(fontsize=max(VIZ_CONFIG["font_size"] - 2, 16), loc="best", ncol=2)
    ax.grid(alpha=VIZ_CONFIG["grid_alpha"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_term_heatmap(
    tfidf_matrix: np.ndarray,
    feature_names: list[str],
    labels: list[str],
    output_path: Path,
    *,
    n_terms: int = 20,
) -> Path:
    """Process plot term heatmap."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 8), dpi=VIZ_CONFIG["dpi"])
    if tfidf_matrix.size == 0 or not labels:
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    unique_labels = sorted(set(labels))
    label_arr = np.array(labels)
    means = np.zeros((len(unique_labels), tfidf_matrix.shape[1]))
    for i, lab in enumerate(unique_labels):
        mask = label_arr == lab
        if mask.any():
            means[i] = tfidf_matrix[mask].mean(axis=0)

    between_group_variance = means.var(axis=0)
    top_idx = np.argsort(between_group_variance)[::-1][:n_terms]
    heatmap_data = means[:, top_idx]
    term_labels = [feature_names[j] for j in top_idx]
    im = ax.imshow(heatmap_data, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(len(term_labels)))
    ax.set_xticklabels(
        term_labels,
        rotation=45,
        ha="right",
        fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
    )
    ax.set_yticks(range(len(unique_labels)))
    ax.set_yticklabels(
        [format_subfield_label(label) for label in unique_labels],
        fontsize=max(VIZ_CONFIG["font_size"] - 1, 16),
    )
    ax.set_title(
        "Term × Subfield Heatmap (Mean TF-IDF)",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    fig.colorbar(im, ax=ax, label="Mean TF-IDF Weight", shrink=0.8)
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_dendrogram(
    tfidf_matrix: np.ndarray,
    labels: list[str],
    output_path: Path,
) -> Path:
    """Process plot dendrogram."""
    from scipy.cluster.hierarchy import cophenet, dendrogram as scipy_dendrogram, linkage
    from scipy.spatial.distance import pdist

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 7), dpi=VIZ_CONFIG["dpi"])
    unique_labels = sorted(set(labels))
    if len(unique_labels) < 2:
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    label_arr = np.array(labels)
    centroids = np.array([tfidf_matrix[label_arr == lab].mean(axis=0) for lab in unique_labels])
    z_link = linkage(centroids, method="ward")
    scipy_dendrogram(
        z_link,
        labels=[format_subfield_label(label) for label in unique_labels],
        leaf_rotation=30,
        leaf_font_size=VIZ_CONFIG["font_size"],
        ax=ax,
        color_threshold=0,
        above_threshold_color=VIZ_CONFIG["palette"][0],
    )
    ax.set_title(
        "Subfield Hierarchical Clustering (Ward Linkage)",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.set_ylabel("Ward Distance", fontsize=VIZ_CONFIG["font_size"])
    coph_corr, _ = cophenet(z_link, pdist(centroids))
    ax.text(
        0.98,
        0.96,
        f"Cophenetic r = {coph_corr:.2f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
    )
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return output_path
