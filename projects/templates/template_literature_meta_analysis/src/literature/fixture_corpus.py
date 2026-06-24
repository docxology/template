"""Deterministic synthetic fixture-corpus builder.

The template ships an offline, idempotent default run, which requires a committed
seed corpus so the pipeline produces identical artifacts with no network access.
This module builds that corpus for a configured term (default "modafinil") as
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
DEFAULT_TERM = "modafinil"
DEFAULT_N = 80

# Subfield -> (title fragments, abstract sentences). Domain content for the default
# term; a different term would supply its own fragments via config in a live run.
TOPICS: dict[str, dict[str, list[str]]] = {
    "clinical_sleep": {
        "titles": [
            "Modafinil for excessive daytime sleepiness in narcolepsy",
            "Armodafinil in shift-work disorder: a randomized trial",
            "Modafinil as adjunct therapy in obstructive sleep apnea",
            "Wakefulness outcomes with modafinil in idiopathic hypersomnia",
        ],
        "sentences": [
            "Modafinil significantly reduced excessive daytime sleepiness versus placebo.",
            "Patients with narcolepsy showed improved maintenance of wakefulness.",
            "Shift-work disorder symptoms improved on the Epworth Sleepiness Scale.",
            "Sleep-onset latency increased during the multiple sleep latency test.",
        ],
    },
    "cognition": {
        "titles": [
            "Modafinil and working memory under sleep deprivation",
            "Cognitive enhancement effects of modafinil in healthy adults",
            "Attention and vigilance after modafinil administration",
            "Executive function and psychomotor speed with modafinil",
        ],
        "sentences": [
            "Modafinil improved working memory accuracy in sleep-deprived participants.",
            "Sustained attention and vigilance increased relative to placebo.",
            "Effects on executive function were modest in well-rested subjects.",
            "Psychomotor vigilance task lapses decreased after dosing.",
        ],
    },
    "pharmacology": {
        "titles": [
            "Pharmacokinetics of modafinil and its enantiomers",
            "Dopamine transporter occupancy by modafinil",
            "Mechanism of action of modafinil revisited",
            "CYP3A4 metabolism and half-life of modafinil",
        ],
        "sentences": [
            "Modafinil inhibits the dopamine transporter increasing extracellular dopamine.",
            "Plasma half-life supports once-daily dosing in most patients.",
            "Bioavailability and metabolism were characterized in healthy volunteers.",
            "The mechanism of action involves multiple monoaminergic systems.",
        ],
    },
    "psychiatry": {
        "titles": [
            "Modafinil augmentation in major depressive disorder",
            "Modafinil for fatigue in multiple sclerosis",
            "Adjunctive modafinil in schizophrenia: cognition and negative symptoms",
            "Modafinil in adult ADHD: a controlled study",
        ],
        "sentences": [
            "Adjunctive modafinil reduced fatigue and improved residual symptoms.",
            "Negative symptoms and cognition showed small improvements.",
            "Depression severity decreased on augmentation versus placebo.",
            "Tolerability was acceptable across psychiatric populations.",
        ],
    },
    "safety": {
        "titles": [
            "Abuse potential of modafinil relative to classical stimulants",
            "Adverse-event profile of long-term modafinil use",
            "Modafinil and serious skin reactions: a safety review",
            "Dependence and tolerability of modafinil",
        ],
        "sentences": [
            "Modafinil showed lower abuse potential than amphetamine in human studies.",
            "The most common adverse effects were headache and nausea.",
            "Rare serious cutaneous reactions prompted regulatory warnings.",
            "No evidence of physical dependence emerged over the study period.",
        ],
    },
    "neuroscience": {
        "titles": [
            "Orexin signaling and the wake-promoting action of modafinil",
            "Functional MRI of modafinil effects on prefrontal cortex",
            "Hypothalamic mechanisms of modafinil-induced wakefulness",
            "EEG correlates of modafinil-induced alertness",
        ],
        "sentences": [
            "Modafinil activated orexinergic neurons in the hypothalamus.",
            "Functional imaging showed increased prefrontal activation during tasks.",
            "Histaminergic tone contributed to wake promotion.",
            "EEG showed reduced theta power consistent with increased alertness.",
        ],
    },
}

VENUES = [
    "Sleep",
    "Journal of Clinical Psychopharmacology",
    "Neuropsychopharmacology",
    "Psychopharmacology",
    "CNS Drugs",
    "Journal of Clinical Sleep Medicine",
    "Biological Psychiatry",
    "European Neuropsychopharmacology",
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
