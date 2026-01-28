"""Text analysis utilities for Ento-Linguistic research.

This module provides core text processing functionality for analyzing scientific
literature in entomology, including tokenization, normalization, and linguistic
feature extraction.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

# Domain-specific stop words for scientific text
SCIENTIFIC_STOP_WORDS = {
    "fig",
    "figure",
    "table",
    "et",
    "al",
    "etc",
    "ie",
    "eg",
    "vs",
    "cf",
    "respectively",
    "however",
    "therefore",
    "thus",
    "although",
    "whereas",
    "furthermore",
    "moreover",
    "addition",
    "similarly",
    "consequently",
    "subsequently",
    "accordingly",
    "nevertheless",
    "nonetheless",
    "notwithstanding",
}


class TextProcessor:
    """Process and normalize scientific text for analysis.

    This class handles the preprocessing pipeline for entomological literature,
    ensuring consistent tokenization and normalization across different text sources.
    """

    def __init__(
        self, language: str = "english", custom_stop_words: Optional[Set[str]] = None
    ):
        """Initialize text processor.

        Args:
            language: Language for NLTK processing
            custom_stop_words: Additional domain-specific stop words
        """
        self.language = language
        self.lemmatizer = WordNetLemmatizer()

        # Combine standard and scientific stop words
        self.stop_words = set(stopwords.words(language))
        self.stop_words.update(SCIENTIFIC_STOP_WORDS)
        if custom_stop_words:
            self.stop_words.update(custom_stop_words)

        # Scientific terminology that should not be split
        self.scientific_terms = {
            "superorganism",
            "eusocial",
            "eusociality",
            "hymenoptera",
            "formicidae",
            "myrmicinae",
            "ponerinae",
            "dorylinae",
            "phylogenetic",
            "ontogenetic",
            "phenotypic",
            "genotypic",
        }

    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing.

        Args:
            text: Raw input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation (keep alphanumeric, spaces, and hyphens)
        text = re.sub(r"[^\w\s\-]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        return text

    def tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        return sent_tokenize(text)

    def tokenize_words(self, text: str, preserve_scientific: bool = True) -> List[str]:
        """Tokenize text into words with scientific term preservation.

        Args:
            text: Input text
            preserve_scientific: Whether to preserve scientific terminology

        Returns:
            List of word tokens
        """
        # First pass: standard tokenization
        tokens = word_tokenize(text)

        if preserve_scientific:
            # Second pass: merge scientific terms that were split
            merged_tokens = []
            i = 0
            while i < len(tokens):
                # Check for multi-word scientific terms
                merged = False
                for term in self.scientific_terms:
                    term_words = term.split()
                    if (
                        i + len(term_words) <= len(tokens)
                        and [t.lower() for t in tokens[i : i + len(term_words)]]
                        == term_words
                    ):
                        merged_tokens.append(term)
                        i += len(term_words)
                        merged = True
                        break
                if not merged:
                    merged_tokens.append(tokens[i])
                    i += 1
            tokens = merged_tokens

        return tokens

    def remove_punctuation(self, tokens: List[str]) -> List[str]:
        """Remove punctuation from tokens.

        Args:
            tokens: Input tokens

        Returns:
            Tokens with punctuation removed
        """
        clean_tokens = []
        for token in tokens:
            # Remove punctuation from token
            clean_token = re.sub(r"[^\w\-_]", "", token)
            # Keep token if it's not empty and contains alphanumeric characters
            if clean_token and re.search(r"[a-zA-Z0-9]", clean_token):
                clean_tokens.append(clean_token)
        return clean_tokens

    def remove_stop_words(self, tokens: List[str]) -> List[str]:
        """Remove stop words from token list.

        Args:
            tokens: Input tokens

        Returns:
            Tokens with stop words removed
        """
        return [token for token in tokens if token.lower() not in self.stop_words]

    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens to base forms.

        Args:
            tokens: Input tokens

        Returns:
            Lemmatized tokens
        """
        return [self.lemmatizer.lemmatize(token) for token in tokens]

    def process_text(
        self, text: str, lemmatize: bool = True, remove_stops: bool = True
    ) -> List[str]:
        """Complete text processing pipeline.

        Args:
            text: Raw input text
            lemmatize: Whether to lemmatize tokens
            remove_stops: Whether to remove stop words

        Returns:
            Processed tokens
        """
        # Normalization
        normalized = self.normalize_text(text)

        # Tokenization
        tokens = self.tokenize_words(normalized)

        # Punctuation removal
        tokens = self.remove_punctuation(tokens)

        # Stop word removal
        if remove_stops:
            tokens = self.remove_stop_words(tokens)

        # Lemmatization
        if lemmatize:
            tokens = self.lemmatize_tokens(tokens)

        return tokens

    def extract_ngrams(
        self, tokens: List[str], n: int = 2, min_freq: int = 1
    ) -> Dict[str, int]:
        """Extract n-grams from token list.

        Args:
            tokens: Input tokens
            n: N-gram size
            min_freq: Minimum frequency to include

        Returns:
            Dictionary of n-grams and their frequencies
        """
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i : i + n])
            ngrams.append(ngram)

        ngram_counts = Counter(ngrams)
        return {
            ngram: count for ngram, count in ngram_counts.items() if count >= min_freq
        }

    def get_vocabulary_stats(self, texts: List[str]) -> Dict[str, Any]:
        """Compute vocabulary statistics across multiple texts.

        Args:
            texts: List of input texts

        Returns:
            Dictionary with vocabulary statistics
        """
        all_tokens = []
        total_chars = 0

        for text in texts:
            tokens = self.process_text(text)
            all_tokens.extend(tokens)
            total_chars += len(text)

        vocab = set(all_tokens)
        token_counts = Counter(all_tokens)

        return {
            "total_tokens": len(all_tokens),
            "unique_tokens": len(vocab),
            "total_characters": total_chars,
            "avg_token_length": (
                sum(len(t) for t in all_tokens) / len(all_tokens) if all_tokens else 0
            ),
            "most_common_tokens": token_counts.most_common(20),
            "type_token_ratio": len(vocab) / len(all_tokens) if all_tokens else 0,
        }


class LinguisticFeatureExtractor:
    """Extract linguistic features from text for analysis.

    This class provides methods for extracting features relevant to
    Ento-Linguistic analysis, including term patterns and linguistic structures.
    """

    def __init__(self):
        """Initialize feature extractor."""
        # Linguistic patterns for different framing types
        self.anthropomorphic_patterns = [
            r"\b(choose|decide|prefer|select|opt)\b",
            r"\b(communicate|signal|inform|warn)\b",
            r"\b(cooperate|compete|negotiate|trade)\b",
            r"\b(recognize|identify|distinguish|know)\b",
        ]

        self.hierarchical_patterns = [
            r"\b(superior|inferior|dominant|subordinate)\b",
            r"\b(command|control|authority|obey)\b",
            r"\b(leader|follower|boss|worker)\b",
            r"\b(ruler|subject|governor|citizen)\b",
        ]

        self.economic_patterns = [
            r"\b(invest|profit|cost|benefit)\b",
            r"\b(trade|exchange|transaction|market)\b",
            r"\b(resource|allocation|distribution|share)\b",
            r"\b(value|worth|price|commodity)\b",
        ]

    def extract_framing_features(self, text: str) -> Dict[str, int]:
        """Extract framing-related linguistic features.

        Args:
            text: Input text

        Returns:
            Dictionary of framing feature counts
        """
        text_lower = text.lower()

        features = {
            "anthropomorphic_terms": 0,
            "hierarchical_terms": 0,
            "economic_terms": 0,
            "total_words": len(text.split()),
        }

        # Count anthropomorphic terms
        for pattern in self.anthropomorphic_patterns:
            matches = re.findall(pattern, text_lower)
            features["anthropomorphic_terms"] += len(matches)

        # Count hierarchical terms
        for pattern in self.hierarchical_patterns:
            matches = re.findall(pattern, text_lower)
            features["hierarchical_terms"] += len(matches)

        # Count economic terms
        for pattern in self.economic_patterns:
            matches = re.findall(pattern, text_lower)
            features["economic_terms"] += len(matches)

        # Calculate densities
        if features["total_words"] > 0:
            features["anthropomorphic_density"] = (
                features["anthropomorphic_terms"] / features["total_words"]
            )
            features["hierarchical_density"] = (
                features["hierarchical_terms"] / features["total_words"]
            )
            features["economic_density"] = (
                features["economic_terms"] / features["total_words"]
            )

        return features

    def detect_terminology_patterns(self, tokens: List[str]) -> Dict[str, Any]:
        """Detect patterns in terminology usage.

        Args:
            tokens: Processed tokens

        Returns:
            Dictionary of terminology patterns
        """
        patterns = {
            "compound_terms": [],
            "hyphenated_terms": [],
            "scientific_abbreviations": [],
            "latin_terms": [],
        }

        # Find compound terms (multiple words)
        for i in range(len(tokens) - 1):
            if (
                len(tokens[i]) > 3
                and len(tokens[i + 1]) > 3
                and not tokens[i].endswith(".")
                and not tokens[i + 1].startswith(".")
            ):
                compound = f"{tokens[i]} {tokens[i+1]}"
                patterns["compound_terms"].append(compound)

        # Find hyphenated terms
        for token in tokens:
            if "-" in token and len(token) > 7:  # Likely a compound term
                patterns["hyphenated_terms"].append(token)

        # Find scientific abbreviations (capital letters)
        for token in tokens:
            if len(token) >= 2 and token.isupper() and re.match(r"^[A-Z]{2,}$", token):
                patterns["scientific_abbreviations"].append(token)

        # Find Latin terms (italicized or specific patterns)
        latin_indicators = ["spp", "sp", "subsp", "var", "ssp"]
        for token in tokens:
            if any(indicator in token.lower() for indicator in latin_indicators):
                patterns["latin_terms"].append(token)

        return patterns

    def analyze_sentence_complexity(self, text: str) -> Dict[str, float]:
        """Analyze sentence complexity features.

        Args:
            text: Input text

        Returns:
            Dictionary of complexity metrics
        """
        sentences = sent_tokenize(text)
        words = text.split()

        if not sentences:
            return {
                "sentence_count": 0,
                "avg_sentence_length": 0.0,
                "complexity_ratio": 0.0,
                "total_words": len(text.split()),
            }

        avg_sentence_length = len(words) / len(sentences)

        # Count complex sentence structures
        complex_sentences = 0
        for sentence in sentences:
            # Count clauses (approximate)
            clauses = len(
                re.findall(
                    r"\b(and|or|but|although|because|while|since|unless)\b",
                    sentence.lower(),
                )
            )
            if clauses > 0 or "," in sentence:
                complex_sentences += 1

        complexity_ratio = complex_sentences / len(sentences) if sentences else 0

        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "complexity_ratio": complexity_ratio,
            "total_words": len(words),
        }
