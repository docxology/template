"""Tests for SQL query methods."""

import pytest
from src.sql_queries import WaysSQLQueries


class TestWaysSQLQueries:
    """Test SQL query methods."""

    @pytest.fixture
    def queries(self):
        """Get SQL queries instance."""
        return WaysSQLQueries()

    def test_get_all_ways_sql(self, queries):
        """Test getting all ways."""
        query, results = queries.get_all_ways_sql()
        assert isinstance(query, str)
        assert "SELECT" in query.upper()
        assert "FROM WAYS" in query.upper()
        assert len(results) == 210  # Expected number of ways
        assert len(results[0]) == 12  # Expected number of columns

    def test_get_ways_by_room_sql(self, queries):
        """Test filtering ways by room."""
        query, results = queries.get_ways_by_room_sql('B')
        assert isinstance(query, str)
        assert "WHERE mene = ?" in query
        assert len(results) >= 0
        # All results should be in the specified room
        for row in results:
            assert row[8] == 'B'  # mene column

    def test_count_ways_by_type_sql(self, queries):
        """Test dialogue type distribution."""
        query, results = queries.count_ways_by_type_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguetype" in query
        assert len(results) > 0
        # Check that results are ordered by count descending
        counts = [row[1] for row in results]
        assert counts == sorted(counts, reverse=True)

    def test_get_network_edges_sql(self, queries):
        """Test network edge generation."""
        query, results = queries.get_network_edges_sql()
        assert isinstance(query, str)
        assert len(results) > 0
        # Each edge should have way1_id < way2_id (to avoid duplicates)
        for row in results:
            way1_id, way2_id = row[0], row[1]
            assert way1_id < way2_id

    def test_get_central_ways_sql(self, queries):
        """Test most connected ways query."""
        query, results = queries.get_central_ways_sql(5)
        assert isinstance(query, str)
        assert len(results) <= 5
        if results:
            # Should be ordered by connection count descending
            connections = [row[2] for row in results]
            assert connections == sorted(connections, reverse=True)

    def test_get_ways_with_examples_sql(self, queries):
        """Test ways with examples query."""
        query, results = queries.get_ways_with_examples_sql()
        assert isinstance(query, str)
        assert len(results) > 0
        # All results should have examples (non-empty)
        for row in results:
            examples_length = row[2]
            assert examples_length > 0

    def test_query_performance(self, queries):
        """Test that queries execute reasonably fast."""
        import time

        start = time.time()
        query, results = queries.get_all_ways_sql()
        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0
        assert len(results) == 210
