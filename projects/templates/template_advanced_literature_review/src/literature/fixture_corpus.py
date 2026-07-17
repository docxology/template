"""Deterministic synthetic fixture-corpus builder.

The template ships an offline, idempotent default run, which requires a committed
seed corpus so the pipeline produces identical artifacts with no network access.
This module builds that corpus for a configured term (default "exoplanet atmospheres") as
**clearly-synthetic** records:

* DOIs use the reserved ``10.5555/`` test prefix (never a real DOI).
* Author names are generated, not real people.
* Titles/abstracts are composed from topic fragments so every downstream analysis
  path (subfield classification, temporal trends, TF-IDF/NMF topics, entities,
  embeddings, citation network) receives meaningful signal.

Determinism: a fixed RNG seed makes the output byte-stable across runs. The same
``(term, n, seed)`` always yields an identical corpus.

Live runs (engines enabled + network) replace this with real retrieved records; the
synthetic corpus exists only so CI and a fresh clone can exercise the full pipeline
offline.
"""

from __future__ import annotations

import random
from datetime import date

from literature.corpus import Corpus
from literature.models import Author, Paper

DEFAULT_SEED = 42
DEFAULT_TERM = "exoplanet atmospheres"
DEFAULT_N = 80

# Subfield -> (title fragments, abstract sentences). These are synthetic records
# for pipeline validation, never evidence of an empirical literature.
TOPICS: dict[str, dict[str, list[str]]] = {
    "atmospheric_modeling": {
        "titles": [
            "Forward models for exoplanet atmospheric spectra",
            "Radiative transfer in cloudy exoplanet atmospheres",
            "Retrieval priors for atmospheric composition",
            "Climate models of irradiated exoplanets",
        ],
        "sentences": [
            "Forward models connect atmospheric composition to synthetic transmission spectra.",
            "Cloud opacity changes the retrieved abundance of atmospheric species.",
            "Radiative transfer assumptions affect uncertainty in exoplanet retrievals.",
            "Climate simulations explore temperature structure in irradiated atmospheres.",
        ],
    },
    "observational_methods": {
        "titles": [
            "Transit spectroscopy of exoplanet atmospheres",
            "Instrument systematics in exoplanet observations",
            "Photometric monitoring of transiting exoplanets",
            "High-resolution spectroscopy for atmospheric studies",
        ],
        "sentences": [
            "Transit spectroscopy constrains atmospheric scale height and composition.",
            "Instrument systematics are modelled alongside astrophysical signals.",
            "Photometric light curves provide repeatable observations of transiting planets.",
            "High-resolution spectra separate planetary and stellar contributions.",
        ],
    },
    "molecular_detection": {
        "titles": [
            "Water-vapour signatures in exoplanet atmospheres",
            "Carbon dioxide detection in a transiting exoplanet",
            "Methane constraints from transmission spectra",
            "Sodium and potassium lines in hot Jupiter atmospheres",
        ],
        "sentences": [
            "Water vapour signatures are evaluated against competing opacity sources.",
            "Carbon dioxide abundance is constrained by simulated and observed spectra.",
            "Methane retrievals depend on spectral coverage and prior assumptions.",
            "Alkali-metal lines provide diagnostics of temperature and atmospheric pressure.",
        ],
    },
    "jwst_instrumentation": {
        "titles": [
            "JWST NIRSpec observations of exoplanet atmospheres",
            "MIRI spectroscopy and thermal emission from exoplanets",
            "NIRCam transit photometry for atmospheric characterization",
            "Calibration of JWST exoplanet transmission spectra",
        ],
        "sentences": [
            "JWST spectra extend wavelength coverage for atmospheric characterization.",
            "Thermal emission measurements constrain dayside temperature structure.",
            "NIRCam photometry is combined with transit observations and retrieval models.",
            "Calibration choices are reported as uncertainty sources in JWST analyses.",
        ],
    },
    "retrieval_statistics": {
        "titles": [
            "Uncertainty quantification for atmospheric retrievals",
            "Benchmarking exoplanet atmospheric inference pipelines",
            "Bayesian model comparison for molecular detections",
            "Reproducibility of exoplanet spectral analyses",
        ],
        "sentences": [
            "Uncertainty intervals quantify the effect of noise and model misspecification.",
            "Benchmark datasets compare retrieval accuracy across analysis pipelines.",
            "Bayesian model comparison tests competing molecular explanations.",
            "Reproducibility checks record data, code, and configuration dependencies.",
        ],
    },
    "comparative_planetology": {
        "titles": [
            "Comparative atmospheric composition across exoplanet populations",
            "Metallicity and temperature trends in giant exoplanets",
            "Population-level analysis of transmission spectra",
            "Atmospheric diversity across stellar irradiation regimes",
        ],
        "sentences": [
            "Comparative analysis separates population trends from target-specific effects.",
            "Metallicity and temperature covariates explain part of the observed variation.",
            "Population studies require harmonized preprocessing and uncertainty reporting.",
            "Atmospheric diversity is evaluated across stellar irradiation regimes.",
        ],
    },
}

VENUES = [
    "The Astrophysical Journal",
    "Astronomy and Astrophysics",
    "Monthly Notices of the Royal Astronomical Society",
    "Nature Astronomy",
    "The Astronomical Journal",
    "Publications of the Astronomical Society of the Pacific",
    "Icarus",
    "Research Notes of the AAS",
]
GIVEN = ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "J.", "K.", "L.", "M."]
FAMILY = [
    "Almeida",
    "Bishop",
    "Carter",
    "Devlin",
    "Esposito",
    "Fournier",
    "Garrido",
    "Hassan",
    "Ito",
    "Jensen",
    "Kowalski",
    "Lindgren",
    "Moreau",
    "Nakamura",
    "Owens",
    "Petrov",
    "Quinn",
    "Rossi",
    "Singh",
    "Tanaka",
]


def build_synthetic_corpus(term: str = DEFAULT_TERM, n: int = DEFAULT_N, seed: int = DEFAULT_SEED) -> Corpus:
    """Build a deterministic synthetic corpus of ``n`` records for ``term``.

    The same ``(term, n, seed)`` always yields an identical corpus. Records span
    1990-2024 with a realistic growth curve, are distributed across the topic
    subfields, carry generated authors/venues/identifiers, and cite a few earlier
    records to form a connected citation network.
    """
    rng = random.Random(seed)
    subfields = list(TOPICS.keys())
    papers: list[Paper] = []
    canonical_ids: list[str] = []

    for i in range(n):
        sub = subfields[i % len(subfields)]
        topic = TOPICS[sub]
        # Year skewed toward recent (literature grows over time).
        year = int(1990 + (2024 - 1990) * (rng.random() ** 0.6))
        title_base = topic["titles"][rng.randrange(len(topic["titles"]))]
        title = f"{title_base} ({year}) [{i:03d}]"
        n_sent = rng.randint(2, 4)
        abstract = " ".join(rng.sample(topic["sentences"], k=min(n_sent, len(topic["sentences"]))))
        n_auth = rng.randint(1, 5)
        authors = [Author(name=f"{rng.choice(GIVEN)} {rng.choice(FAMILY)}") for _ in range(n_auth)]
        doi = f"10.5555/{term}.{i:04d}"  # reserved test prefix -> clearly synthetic
        is_oa = rng.random() < 0.45
        paper = Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            year=year,
            doi=doi,
            venue=rng.choice(VENUES),
            citation_count=int(rng.expovariate(1 / 25.0)) + (2024 - year),
            publication_date=date(year, rng.randint(1, 12), rng.randint(1, 28)),
            is_open_access=is_oa,
            pdf_url=(f"https://example.org/oa/{term}/{i:04d}.pdf" if is_oa else None),
            full_text_source=("repository" if is_oa else None),
        )
        if i % 7 == 0:
            paper.openalex_id = f"W{1000000 + i}"
        papers.append(paper)
        canonical_ids.append(paper.canonical_id)

    # Build a citation network: each paper cites up to 4 earlier papers.
    for idx, paper in enumerate(papers):
        if idx == 0:
            continue
        k = min(rng.randint(0, 4), idx)
        if k:
            paper.references = rng.sample(canonical_ids[:idx], k=k)

    corpus = Corpus()
    for paper in papers:
        corpus.add(paper)
    return corpus
