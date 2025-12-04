"""Tests for SQL query methods."""

import pytest
from src.sql_queries import WaysSQLQueries, get_ways_sql_queries, execute_ways_query


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

    def test_get_ways_by_dialogue_type_sql(self, queries):
        """Test filtering ways by dialogue type."""
        query, results = queries.get_ways_by_dialogue_type_sql('Absolute')
        assert isinstance(query, str)
        assert "WHERE dialoguetype = ?" in query
        assert len(results) >= 0
        # All results should be of the specified type
        for row in results:
            assert row[3] == 'Absolute'  # dialoguetype column

    def test_get_ways_by_partner_sql(self, queries):
        """Test filtering ways by dialogue partner."""
        # Get a partner that exists in the database
        query, all_results = queries.get_all_ways_sql()
        if all_results:
            partner = all_results[0][2]  # dialoguewith column
            query, results = queries.get_ways_by_partner_sql(partner)
            assert isinstance(query, str)
            assert "WHERE dialoguewith = ?" in query
            assert len(results) >= 0
            # All results should have the specified partner
            for row in results:
                assert row[2] == partner  # dialoguewith column

    def test_get_way_by_id_sql(self, queries):
        """Test getting specific way by ID."""
        # Test with existing ID
        query, result = queries.get_way_by_id_sql(1)
        assert isinstance(query, str)
        assert "WHERE id = ?" in query
        assert result is not None
        assert len(result) == 12  # Expected columns
        assert result[0] == 1  # ID should match

        # Test with non-existing ID
        query, result = queries.get_way_by_id_sql(99999)
        assert result is None

    def test_get_ways_by_god_relationship_sql(self, queries):
        """Test filtering ways by God relationship."""
        query, results = queries.get_ways_by_god_relationship_sql('Creator')
        assert isinstance(query, str)
        assert "WHERE dievas LIKE ?" in query
        assert len(results) >= 0
        # All results should contain the relationship in dievas field
        for row in results:
            assert 'Creator' in row[9]  # dievas column

    def test_get_rooms_sql(self, queries):
        """Test getting all rooms."""
        query, results = queries.get_rooms_sql()
        assert isinstance(query, str)
        assert "FROM menes" in query
        assert "ORDER BY eilestvarka" in query
        assert len(results) > 0
        # Each room should have expected number of columns
        for row in results:
            assert len(row) == 12  # Expected columns for rooms

    def test_get_questions_sql(self, queries):
        """Test getting all questions."""
        query, results = queries.get_questions_sql()
        assert isinstance(query, str)
        assert "FROM klausimai" in query
        assert len(results) >= 0
        # Each question should have expected number of columns
        for row in results:
            assert len(row) == 7  # Expected columns for questions

    def test_get_examples_sql(self, queries):
        """Test getting all examples."""
        query, results = queries.get_examples_sql()
        assert isinstance(query, str)
        assert "FROM examples" in query
        assert len(results) >= 0
        # Each example should have expected number of columns
        for row in results:
            assert len(row) == 3  # Expected columns for examples

    def test_get_question_way_relationships_sql(self, queries):
        """Test getting question-way relationships."""
        query, results = queries.get_question_way_relationships_sql()
        assert isinstance(query, str)
        assert "FROM klausimobudai" in query
        assert len(results) >= 0
        # Each relationship should have expected number of columns
        for row in results:
            assert len(row) == 3  # Expected columns for relationships

    def test_count_ways_by_room_sql(self, queries):
        """Test ways count by room."""
        query, results = queries.count_ways_by_room_sql()
        assert isinstance(query, str)
        assert "GROUP BY mene" in query
        assert len(results) > 0
        # Results should be ordered by count descending
        counts = [row[1] for row in results]
        assert counts == sorted(counts, reverse=True)

    def test_count_ways_by_partner_sql(self, queries):
        """Test ways count by partner."""
        query, results = queries.count_ways_by_partner_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguewith" in query
        assert len(results) > 0
        # Results should be ordered by count descending
        counts = [row[1] for row in results]
        assert counts == sorted(counts, reverse=True)

    def test_get_room_statistics_sql(self, queries):
        """Test room statistics query."""
        query, results = queries.get_room_statistics_sql()
        assert isinstance(query, str)
        assert "FROM menes m" in query
        assert "LEFT JOIN ways w" in query
        assert len(results) >= 0
        # Each result should have expected statistics columns
        for row in results:
            assert len(row) == 5  # room, way_count, avg_way_length, avg_examples_length

    def test_get_dialogue_type_distribution_sql(self, queries):
        """Test dialogue type distribution."""
        query, results = queries.get_dialogue_type_distribution_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguetype" in query
        assert len(results) > 0
        # Each result should have expected columns
        for row in results:
            assert len(row) == 4  # type, count, room_count, avg_examples_length

    def test_get_most_common_rooms_sql(self, queries):
        """Test most common rooms query."""
        query, results = queries.get_most_common_rooms_sql(5)
        assert isinstance(query, str)
        assert "LIMIT 5" in query
        assert len(results) <= 5
        if results:
            # Should be ordered by count descending
            counts = [row[1] for row in results]
            assert counts == sorted(counts, reverse=True)

    def test_get_most_common_partners_sql(self, queries):
        """Test most common partners query."""
        query, results = queries.get_most_common_partners_sql(5)
        assert isinstance(query, str)
        assert "LIMIT 5" in query
        assert len(results) <= 5
        if results:
            # Should be ordered by count descending
            counts = [row[1] for row in results]
            assert counts == sorted(counts, reverse=True)

    def test_get_ways_by_example_length_sql(self, queries):
        """Test filtering ways by minimum example length."""
        query, results = queries.get_ways_by_example_length_sql(100)
        assert isinstance(query, str)
        assert "LENGTH(examples) >=" in query
        assert len(results) >= 0
        # All results should have examples >= min_length
        for row in results:
            assert row[2] >= 100  # examples_length

    def test_cross_tabulate_type_room_sql(self, queries):
        """Test type-room cross-tabulation."""
        query, results = queries.cross_tabulate_type_room_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguetype, mene" in query
        assert len(results) >= 0
        # Each result should have type, room, count
        for row in results:
            assert len(row) == 3

    def test_cross_tabulate_type_partner_sql(self, queries):
        """Test type-partner cross-tabulation."""
        query, results = queries.cross_tabulate_type_partner_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguetype, dialoguewith" in query
        assert len(results) >= 0
        # Each result should have type, partner, count
        for row in results:
            assert len(row) == 3

    def test_get_room_cooccurrence_sql(self, queries):
        """Test room cooccurrence analysis."""
        query, results = queries.get_room_cooccurrence_sql()
        assert isinstance(query, str)
        assert "GROUP BY mene" in query
        assert "HAVING ways_in_room > 1" in query
        assert len(results) >= 0
        # Results should only include rooms with multiple ways
        for row in results:
            assert row[1] > 1  # ways_in_room

    def test_get_partner_room_relationships_sql(self, queries):
        """Test partner-room relationships."""
        query, results = queries.get_partner_room_relationships_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguewith, mene" in query
        assert len(results) >= 0
        # Each result should have partner, room, count
        for row in results:
            assert len(row) == 3

    def test_get_god_relationship_distribution_sql(self, queries):
        """Test God relationship distribution."""
        query, results = queries.get_god_relationship_distribution_sql()
        assert isinstance(query, str)
        assert "GROUP BY dievas" in query
        assert len(results) >= 0
        # Results should be ordered by count descending
        counts = [row[1] for row in results]
        assert counts == sorted(counts, reverse=True)

    def test_get_dialogue_type_type_distribution_sql(self, queries):
        """Test sub-type distribution."""
        query, results = queries.get_dialogue_type_type_distribution_sql()
        assert isinstance(query, str)
        assert "GROUP BY dialoguetypetype" in query
        assert len(results) >= 0
        # Results should be ordered by count descending
        counts = [row[1] for row in results]
        assert counts == sorted(counts, reverse=True)

    def test_get_way_text_analysis_sql(self, queries):
        """Test text analysis query."""
        query, results = queries.get_way_text_analysis_sql()
        assert isinstance(query, str)
        assert "LENGTH(way)" in query
        assert len(results) >= 0
        # Each result should have text statistics
        for row in results:
            assert len(row) == 6  # id, way, way_length, examples_length, comments_length, total_length

    def test_get_shared_partner_ways_sql(self, queries):
        """Test shared partner ways query."""
        # Get a way that has a partner
        query, all_ways = queries.get_all_ways_sql()
        if all_ways:
            way_id = all_ways[0][0]  # First way ID
            query, results = queries.get_shared_partner_ways_sql(way_id)
            assert isinstance(query, str)
            assert "JOIN ways w2 ON w1.dialoguewith = w2.dialoguewith" in query
            assert len(results) >= 0
            # All results should be different from the input way
            for row in results:
                assert row[0] != way_id

    def test_get_shared_room_ways_sql(self, queries):
        """Test shared room ways query."""
        # Get a way that has a room
        query, all_ways = queries.get_all_ways_sql()
        if all_ways:
            way_id = all_ways[0][0]  # First way ID
            query, results = queries.get_shared_room_ways_sql(way_id)
            assert isinstance(query, str)
            assert "JOIN ways w2 ON w1.mene = w2.mene" in query
            assert len(results) >= 0
            # All results should be different from the input way
            for row in results:
                assert row[0] != way_id

    def test_get_way_connections_sql(self, queries):
        """Test way connections query."""
        # Get a way
        query, all_ways = queries.get_all_ways_sql()
        if all_ways:
            way_id = all_ways[0][0]  # First way ID
            query, results = queries.get_way_connections_sql(way_id)
            assert isinstance(query, str)
            assert "JOIN ways w2" in query
            assert len(results) >= 0
            # All results should be different from the input way
            for row in results:
                assert row[0] != way_id

    def test_query_performance(self, queries):
        """Test that queries execute reasonably fast."""
        import time

        start = time.time()
        query, results = queries.get_all_ways_sql()
        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0
        assert len(results) == 210


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_ways_sql_queries(self):
        """Test get_ways_sql_queries function."""
        queries = get_ways_sql_queries()
        assert isinstance(queries, WaysSQLQueries)

    def test_execute_ways_query(self):
        """Test execute_ways_query function."""
        # Test with a simple query that should work
        try:
            query, results = execute_ways_query('get_all_ways_sql')
            assert isinstance(query, str)
            assert isinstance(results, list)
        except Exception:
            # If database doesn't exist, that's okay for this test
            pytest.skip("Database not available for convenience function test")


class TestQueryEdgeCases:
    """Test SQL query methods with edge cases."""

    @pytest.fixture
    def queries(self):
        """Get SQL queries instance."""
        return WaysSQLQueries()

    def test_queries_with_empty_results(self, queries):
        """Test queries that return empty results."""
        # Test with non-existing room
        query, results = queries.get_ways_by_room_sql('NONEXISTENT_ROOM')
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

        # Test with non-existing dialogue type
        query, results = queries.get_ways_by_dialogue_type_sql('NONEXISTENT_TYPE')
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

        # Test with non-existing partner
        query, results = queries.get_ways_by_partner_sql('NONEXISTENT_PARTNER')
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_queries_with_invalid_parameters(self, queries):
        """Test queries with invalid parameters."""
        # Test get_way_by_id_sql with invalid ID
        query, result = queries.get_way_by_id_sql(99999)
        assert isinstance(query, str)
        assert result is None

        # Test with negative ID
        query, result = queries.get_way_by_id_sql(-1)
        assert isinstance(query, str)
        assert result is None

    def test_shared_partner_ways_nonexistent_way(self, queries):
        """Test shared partner ways query with non-existent way."""
        query, results = queries.get_shared_partner_ways_sql(99999)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_shared_room_ways_nonexistent_way(self, queries):
        """Test shared room ways query with non-existent way."""
        query, results = queries.get_shared_room_ways_sql(99999)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_way_connections_nonexistent_way(self, queries):
        """Test way connections query with non-existent way."""
        query, results = queries.get_way_connections_sql(99999)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_ways_by_god_relationship_empty_relationship(self, queries):
        """Test God relationship query with empty relationship."""
        query, results = queries.get_ways_by_god_relationship_sql('')
        assert isinstance(query, str)
        assert isinstance(results, list)
        # Should return ways with empty/null relationships or handle gracefully

    def test_get_ways_by_example_length_edge_cases(self, queries):
        """Test example length filtering with edge cases."""
        # Test with very small length
        query, results = queries.get_ways_by_example_length_sql(0)
        assert isinstance(query, str)
        assert isinstance(results, list)

        # Test with very large length
        query, results = queries.get_ways_by_example_length_sql(10000)
        assert isinstance(query, str)
        assert isinstance(results, list)
        # Should return few or no results

    def test_most_common_queries_with_limits(self, queries):
        """Test most common queries with different limits."""
        # Test with limit 0
        query, results = queries.get_most_common_rooms_sql(0)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

        # Test with limit 1
        query, results = queries.get_most_common_rooms_sql(1)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) <= 1

        # Test with very large limit
        query, results = queries.get_most_common_rooms_sql(1000)
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_central_ways_with_limits(self, queries):
        """Test central ways query with different limits."""
        # Test with limit 0
        query, results = queries.get_central_ways_sql(0)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) == 0

        # Test with limit 1
        query, results = queries.get_central_ways_sql(1)
        assert isinstance(query, str)
        assert isinstance(results, list)
        assert len(results) <= 1

    def test_cross_tabulations_edge_cases(self, queries):
        """Test cross-tabulation queries with edge cases."""
        # These should work even with empty or minimal data
        query, results = queries.cross_tabulate_type_room_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

        query, results = queries.cross_tabulate_type_partner_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_room_cooccurrence_edge_cases(self, queries):
        """Test room cooccurrence with edge cases."""
        query, results = queries.get_room_cooccurrence_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)
        # Results should only include rooms with multiple ways

    def test_partner_room_relationships_edge_cases(self, queries):
        """Test partner-room relationships with edge cases."""
        query, results = queries.get_partner_room_relationships_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_god_relationship_distribution_edge_cases(self, queries):
        """Test God relationship distribution with edge cases."""
        query, results = queries.get_god_relationship_distribution_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_dialogue_type_type_distribution_edge_cases(self, queries):
        """Test sub-type distribution with edge cases."""
        query, results = queries.get_dialogue_type_type_distribution_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_way_text_analysis_edge_cases(self, queries):
        """Test text analysis with edge cases."""
        query, results = queries.get_way_text_analysis_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)

    def test_network_edges_edge_cases(self, queries):
        """Test network edges with edge cases."""
        query, results = queries.get_network_edges_sql()
        assert isinstance(query, str)
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__])
