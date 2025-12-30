"""Tests for text_analysis.py module.

This module contains comprehensive tests for the text analysis functionality
used in Ento-Linguistic research.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from typing import List

from src.text_analysis import TextProcessor, LinguisticFeatureExtractor


class TestTextProcessor:
    """Test TextProcessor class functionality."""

    @pytest.fixture
    def processor(self) -> TextProcessor:
        """Create a TextProcessor instance for testing."""
        return TextProcessor()

    @pytest.fixture
    def sample_text(self) -> str:
        """Sample entomological text for testing."""
        return """
        Ant colonies exhibit complex social behaviors. The queen ant lays eggs
        while worker ants forage for food. In eusocial insects, division of labor
        is a key feature of colony organization. Foraging behavior varies among
        different ant species, with some species using pheromone trails to locate
        food sources. The colony acts as a superorganism with emergent properties
        that cannot be predicted from individual ant behavior alone.
        """

    def test_normalization(self, processor: TextProcessor) -> None:
        """Test text normalization functionality."""
        text = "ANT colonies exhibit COMPLEX behaviors!"
        normalized = processor.normalize_text(text)

        assert normalized == "ant colonies exhibit complex behaviors"
        assert normalized.islower()
        assert not any(char in normalized for char in "!@#$%^&*()")

    def test_empty_text_normalization(self, processor: TextProcessor) -> None:
        """Test normalization of empty or whitespace-only text."""
        assert processor.normalize_text("") == ""
        assert processor.normalize_text("   \n\t   ") == ""

    def test_sentence_tokenization(self, processor: TextProcessor, sample_text: str) -> None:
        """Test sentence tokenization."""
        sentences = processor.tokenize_sentences(sample_text)

        # Should split on periods
        assert len(sentences) >= 3
        assert all(isinstance(s, str) for s in sentences)
        assert all(len(s.strip()) > 0 for s in sentences)

    def test_word_tokenization(self, processor: TextProcessor) -> None:
        """Test word tokenization with scientific terms."""
        text = "eusocial insects use pheromone trails"
        tokens = processor.tokenize_words(text)

        assert "eusocial" in tokens
        assert "insects" in tokens
        assert "pheromone" in tokens
        assert "trails" in tokens

    def test_scientific_term_preservation(self, processor: TextProcessor) -> None:
        """Test that scientific compound terms are preserved."""
        text = "superorganism eusociality division of labor"
        tokens = processor.tokenize_words(text)

        # These should be single tokens
        assert "superorganism" in tokens
        assert "eusociality" in tokens

        # "division of labor" should be separate tokens
        assert "division" in tokens
        assert "of" in tokens
        assert "labor" in tokens

    def test_punctuation_removal(self, processor: TextProcessor) -> None:
        """Test punctuation removal from tokens."""
        tokens = ["ant,", "colony.", "behavior!", "eusocial?"]
        clean_tokens = processor.remove_punctuation(tokens)

        assert "ant," not in clean_tokens
        assert "colony." not in clean_tokens
        assert "ant" in clean_tokens
        assert "colony" in clean_tokens

    def test_stop_word_removal(self, processor: TextProcessor) -> None:
        """Test stop word filtering."""
        tokens = ["the", "ant", "colony", "is", "eusocial", "and", "complex"]
        filtered = processor.remove_stop_words(tokens)

        # Stop words should be removed
        assert "the" not in filtered
        assert "is" not in filtered
        assert "and" not in filtered

        # Content words should remain
        assert "ant" in filtered
        assert "colony" in filtered
        assert "eusocial" in filtered
        assert "complex" in filtered

    def test_lemmatization(self, processor: TextProcessor) -> None:
        """Test word lemmatization."""
        tokens = ["ants", "behaviors", "colonies", "complex"]
        lemmas = processor.lemmatize_tokens(tokens)

        # Basic lemmatization should work
        assert "ants" in lemmas or "ant" in lemmas
        assert "behaviors" in lemmas or "behavior" in lemmas

    def test_complete_processing_pipeline(self, processor: TextProcessor) -> None:
        """Test the complete text processing pipeline."""
        text = "Ant colonies exhibit COMPLEX social behaviors!"
        processed = processor.process_text(text)

        # Should be lowercase, tokenized, cleaned, and lemmatized
        assert isinstance(processed, list)
        assert len(processed) > 0
        assert all(isinstance(token, str) for token in processed)
        assert all(token.islower() for token in processed)

        # Should not contain punctuation or stop words
        assert not any(char in ' '.join(processed) for char in '!@#$%^&*()')

    def test_ngram_extraction(self, processor: TextProcessor) -> None:
        """Test n-gram extraction functionality."""
        tokens = ["ant", "colony", "eusocial", "insect", "behavior", "complex"]
        bigrams = processor.extract_ngrams(tokens, n=2)

        assert len(bigrams) > 0
        assert ("ant", "colony") in [' '.join(k) for k in bigrams.keys()] or "ant colony" in bigrams

    def test_vocabulary_statistics(self, processor: TextProcessor) -> None:
        """Test vocabulary statistics computation."""
        texts = [
            "Ant colonies are eusocial insects.",
            "Worker ants forage for food.",
            "Queen ants lay eggs in the colony."
        ]

        stats = processor.get_vocabulary_stats(texts)

        assert 'total_tokens' in stats
        assert 'unique_tokens' in stats
        assert 'type_token_ratio' in stats
        assert 'most_common_tokens' in stats

        assert stats['total_tokens'] > 0
        assert stats['unique_tokens'] > 0
        assert stats['type_token_ratio'] > 0

        # Type-token ratio should be reasonable
        assert 0.1 < stats['type_token_ratio'] < 1.0


class TestLinguisticFeatureExtractor:
    """Test LinguisticFeatureExtractor class functionality."""

    @pytest.fixture
    def extractor(self) -> LinguisticFeatureExtractor:
        """Create a LinguisticFeatureExtractor instance."""
        return LinguisticFeatureExtractor()

    def test_anthropomorphic_feature_extraction(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test extraction of anthropomorphic linguistic features."""
        text = "Ants choose to cooperate with their colony members. The colony decides how to allocate resources."

        features = extractor.extract_framing_features(text)

        assert 'anthropomorphic_terms' in features
        assert 'total_words' in features
        assert features['anthropomorphic_terms'] > 0
        assert 'anthropomorphic_density' in features

    def test_hierarchical_feature_extraction(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test extraction of hierarchical linguistic features."""
        text = "The queen dominates the colony hierarchy. Workers submit to the dominant female."

        features = extractor.extract_framing_features(text)

        assert 'hierarchical_terms' in features
        assert features['hierarchical_terms'] > 0

    def test_economic_feature_extraction(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test extraction of economic linguistic features."""
        text = "Ants trade resources with colony members. They invest in the common good."

        features = extractor.extract_framing_features(text)

        assert 'economic_terms' in features
        assert features['economic_terms'] > 0

    def test_terminology_pattern_detection(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test detection of terminology patterns."""
        tokens = ["eusocial", "insect", "division-of-labor", "super_organism", "colony", "ant"]

        patterns = extractor.detect_terminology_patterns(tokens)

        assert 'compound_terms' in patterns
        assert 'hyphenated_terms' in patterns

        # Should detect hyphenated and underscore terms
        assert len(patterns['hyphenated_terms']) > 0
        assert any('division-of-labor' in term for term in patterns['hyphenated_terms'])

    def test_sentence_complexity_analysis(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test sentence complexity analysis."""
        text = "Ant colonies are complex. They exhibit division of labor, which involves many different tasks and requires sophisticated communication between individuals."

        complexity = extractor.analyze_sentence_complexity(text)

        assert 'sentence_count' in complexity
        assert 'avg_sentence_length' in complexity
        assert 'complexity_ratio' in complexity
        assert 'total_words' in complexity

        assert complexity['sentence_count'] == 2
        assert complexity['total_words'] > 0
        assert 0 <= complexity['complexity_ratio'] <= 1

    def test_empty_text_handling(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test handling of empty or minimal text."""
        features = extractor.extract_framing_features("")
        assert features['total_words'] == 0
        assert features['anthropomorphic_terms'] == 0

        complexity = extractor.analyze_sentence_complexity("")
        assert complexity['sentence_count'] == 0
        assert complexity['total_words'] == 0

    def test_feature_density_calculation(self, extractor: LinguisticFeatureExtractor) -> None:
        """Test that feature densities are calculated correctly."""
        text = "Ants choose to cooperate. The colony decides. Workers submit to hierarchy."

        features = extractor.extract_framing_features(text)

        # Should have density calculations
        assert 'anthropomorphic_density' in features
        assert 'hierarchical_density' in features
        assert 'economic_density' in features

        # Densities should be reasonable
        total_words = features['total_words']
        if total_words > 0:
            assert 0 <= features['anthropomorphic_density'] <= 1
            assert 0 <= features['hierarchical_density'] <= 1
            assert 0 <= features['economic_density'] <= 1


class TestTextAnalysisIntegration:
    """Integration tests for text analysis components."""

    def test_processor_extractor_integration(self) -> None:
        """Test integration between TextProcessor and LinguisticFeatureExtractor."""
        processor = TextProcessor()
        extractor = LinguisticFeatureExtractor()

        text = "Ants choose complex foraging strategies. The colony exhibits hierarchical organization."

        # Process text
        tokens = processor.process_text(text)

        # Extract features
        features = extractor.extract_framing_features(text)
        patterns = extractor.detect_terminology_patterns(tokens)

        # Integration should work
        assert isinstance(tokens, list)
        assert isinstance(features, dict)
        assert isinstance(patterns, dict)

        # Features should be based on the processed text
        assert features['total_words'] > 0

    def test_real_entomological_text_processing(self) -> None:
        """Test processing of real entomological text."""
        processor = TextProcessor()

        # Real excerpt from entomological literature
        text = """
        The evolution of eusociality in insects represents a major transition
        in individual fitness. In ant colonies, the queen monopolizes reproduction
        while workers sacrifice their own reproductive potential for the benefit
        of the colony. This division of labor creates a superorganism where
        individual selection is subordinated to colony-level selection.
        """

        tokens = processor.process_text(text)

        # Should extract meaningful terms
        assert len(tokens) > 0
        assert any(term in tokens for term in ['eusociality', 'colony', 'queen', 'worker'])

        # Should not contain stop words or punctuation
        assert 'the' not in tokens
        assert 'a' not in tokens
        assert not any(char in ' '.join(tokens) for char in '.,!?')

    def test_feature_extraction_consistency(self) -> None:
        """Test that feature extraction is consistent across similar texts."""
        extractor = LinguisticFeatureExtractor()

        text1 = "Ants choose to cooperate in complex ways."
        text2 = "Ants decide to work together in sophisticated manners."

        features1 = extractor.extract_framing_features(text1)
        features2 = extractor.extract_framing_features(text2)

        # Both should detect anthropomorphic language
        assert features1['anthropomorphic_terms'] > 0
        assert features2['anthropomorphic_terms'] > 0

        # Word counts should be similar
        assert abs(features1['total_words'] - features2['total_words']) <= 2