"""Raw SQL query methods for Ways database analysis.

Provides comprehensive SQL queries for reading, characterizing, analyzing,
and visualizing the ways, rooms, questions, and examples data from
Andrius Kulikauskas's philosophical framework.
"""

from typing import List, Dict, Any, Tuple, Optional
import sqlite3


class WaysSQLQueries:
    """SQL query methods for Ways database operations."""

    def __init__(self, db_path: str = None):
        """Initialize with database path."""
        from pathlib import Path
        self.db_path = db_path or str(Path(__file__).parent.parent / "db" / "ways.db")

    def _execute_query(self, query: str, params: Tuple = None) -> List[Tuple]:
        """Execute a SQL query and return results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            conn.close()

    def _execute_query_single(self, query: str, params: Tuple = None) -> Any:
        """Execute a query and return single result."""
        results = self._execute_query(query, params)
        return results[0][0] if results else None

    # ============================================================================
    # READING METHODS
    # ============================================================================

    def get_all_ways_sql(self) -> Tuple[str, List[Tuple]]:
        """Get all ways with all fields."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        ORDER BY id
        """
        return query, self._execute_query(query)

    def get_ways_by_room_sql(self, room_short: str) -> Tuple[str, List[Tuple]]:
        """Get ways in a specific room."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        WHERE mene = ?
        ORDER BY id
        """
        return query, self._execute_query(query, (room_short,))

    def get_ways_by_dialogue_type_sql(self, dialogue_type: str) -> Tuple[str, List[Tuple]]:
        """Get ways by dialogue type."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        WHERE dialoguetype = ?
        ORDER BY id
        """
        return query, self._execute_query(query, (dialogue_type,))

    def get_ways_by_partner_sql(self, partner: str) -> Tuple[str, List[Tuple]]:
        """Get ways by dialogue partner."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        WHERE dialoguewith = ?
        ORDER BY id
        """
        return query, self._execute_query(query, (partner,))

    def get_way_by_id_sql(self, way_id: int) -> Tuple[str, Optional[Tuple]]:
        """Get specific way by ID."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        WHERE id = ?
        """
        results = self._execute_query(query, (way_id,))
        return query, results[0] if results else None

    def get_ways_by_god_relationship_sql(self, relationship: str) -> Tuple[str, List[Tuple]]:
        """Get ways by God relationship (dievas field)."""
        query = """
        SELECT id, way, dialoguewith, dialoguetype, dialoguetypetype,
               wayurl, examples, dialoguetypetypetype, mene, dievas,
               comments, laikinas
        FROM ways
        WHERE dievas LIKE ?
        ORDER BY id
        """
        return query, self._execute_query(query, (f"%{relationship}%",))

    def get_rooms_sql(self) -> Tuple[str, List[Tuple]]:
        """Get all rooms in the House of Knowledge."""
        query = """
        SELECT numeris, santrumpa, savoka, issiaiskinimas, eilestvarka,
               laipsnis, sparnas, rusis, pasnekovas, dievas, pastabos, label
        FROM menes
        ORDER BY eilestvarka
        """
        return query, self._execute_query(query)

    def get_questions_sql(self) -> Tuple[str, List[Tuple]]:
        """Get all questions."""
        query = """
        SELECT klausimonr, klausimas, mastytojas, svetaine, pasisakymas,
               patarimas, menes
        FROM klausimai
        ORDER BY klausimonr
        """
        return query, self._execute_query(query)

    def get_examples_sql(self) -> Tuple[str, List[Tuple]]:
        """Get all examples."""
        query = """
        SELECT way, rusis, pavyzdziai
        FROM examples
        ORDER BY way
        """
        return query, self._execute_query(query)

    def get_question_way_relationships_sql(self) -> Tuple[str, List[Tuple]]:
        """Get klausimobudai relationships between questions and ways."""
        query = """
        SELECT klausimobudonr, klausimonr, budonr
        FROM klausimobudai
        ORDER BY klausimobudonr
        """
        return query, self._execute_query(query)

    # ============================================================================
    # CHARACTERIZATION METHODS
    # ============================================================================

    def count_ways_by_type_sql(self) -> Tuple[str, List[Tuple]]:
        """Count ways by dialogue type."""
        query = """
        SELECT dialoguetype, COUNT(*) as count
        FROM ways
        GROUP BY dialoguetype
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def count_ways_by_room_sql(self) -> Tuple[str, List[Tuple]]:
        """Count ways per room."""
        query = """
        SELECT mene, COUNT(*) as count
        FROM ways
        GROUP BY mene
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def count_ways_by_partner_sql(self) -> Tuple[str, List[Tuple]]:
        """Count ways per dialogue partner."""
        query = """
        SELECT dialoguewith, COUNT(*) as count
        FROM ways
        GROUP BY dialoguewith
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def get_room_statistics_sql(self) -> Tuple[str, List[Tuple]]:
        """Statistics per room."""
        query = """
        SELECT
            m.santrumpa,
            m.savoka,
            COUNT(w.id) as way_count,
            AVG(LENGTH(w.way)) as avg_way_length,
            AVG(LENGTH(w.examples)) as avg_examples_length
        FROM menes m
        LEFT JOIN ways w ON m.santrumpa = w.mene
        GROUP BY m.santrumpa, m.savoka
        ORDER BY m.eilestvarka
        """
        return query, self._execute_query(query)

    def get_dialogue_type_distribution_sql(self) -> Tuple[str, List[Tuple]]:
        """Distribution analysis of dialogue types."""
        query = """
        SELECT
            dialoguetype,
            COUNT(*) as count,
            COUNT(DISTINCT mene) as room_count,
            AVG(LENGTH(examples)) as avg_examples_length
        FROM ways
        GROUP BY dialoguetype
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def get_most_common_rooms_sql(self, limit: int = 10) -> Tuple[str, List[Tuple]]:
        """Top N rooms by way count."""
        query = f"""
        SELECT mene, COUNT(*) as count
        FROM ways
        GROUP BY mene
        ORDER BY count DESC
        LIMIT {limit}
        """
        return query, self._execute_query(query)

    def get_most_common_partners_sql(self, limit: int = 10) -> Tuple[str, List[Tuple]]:
        """Top N dialogue partners."""
        query = f"""
        SELECT dialoguewith, COUNT(*) as count
        FROM ways
        GROUP BY dialoguewith
        ORDER BY count DESC
        LIMIT {limit}
        """
        return query, self._execute_query(query)

    def get_ways_with_examples_sql(self) -> Tuple[str, List[Tuple]]:
        """Ways that have examples."""
        query = """
        SELECT id, way, LENGTH(examples) as examples_length
        FROM ways
        WHERE examples != ''
        ORDER BY examples_length DESC
        """
        return query, self._execute_query(query)

    def get_ways_by_example_length_sql(self, min_length: int = 100) -> Tuple[str, List[Tuple]]:
        """Filter ways by minimum example length."""
        query = f"""
        SELECT id, way, LENGTH(examples) as examples_length, examples
        FROM ways
        WHERE LENGTH(examples) >= {min_length}
        ORDER BY examples_length DESC
        """
        return query, self._execute_query(query)

    # ============================================================================
    # ANALYSIS METHODS
    # ============================================================================

    def cross_tabulate_type_room_sql(self) -> Tuple[str, List[Tuple]]:
        """Type × Room cross-tabulation."""
        query = """
        SELECT dialoguetype, mene, COUNT(*) as count
        FROM ways
        GROUP BY dialoguetype, mene
        ORDER BY dialoguetype, mene
        """
        return query, self._execute_query(query)

    def cross_tabulate_type_partner_sql(self) -> Tuple[str, List[Tuple]]:
        """Type × Partner cross-tabulation."""
        query = """
        SELECT dialoguetype, dialoguewith, COUNT(*) as count
        FROM ways
        GROUP BY dialoguetype, dialoguewith
        ORDER BY dialoguetype, dialoguewith
        """
        return query, self._execute_query(query)

    def get_room_cooccurrence_sql(self) -> Tuple[str, List[Tuple]]:
        """Ways in multiple rooms (currently single room per way)."""
        query = """
        SELECT mene, COUNT(*) as ways_in_room
        FROM ways
        GROUP BY mene
        HAVING ways_in_room > 1
        ORDER BY ways_in_room DESC
        """
        return query, self._execute_query(query)

    def get_partner_room_relationships_sql(self) -> Tuple[str, List[Tuple]]:
        """Partner × Room patterns."""
        query = """
        SELECT dialoguewith, mene, COUNT(*) as count
        FROM ways
        GROUP BY dialoguewith, mene
        ORDER BY dialoguewith, mene
        """
        return query, self._execute_query(query)

    def get_god_relationship_distribution_sql(self) -> Tuple[str, List[Tuple]]:
        """Dievas field analysis."""
        query = """
        SELECT dievas, COUNT(*) as count
        FROM ways
        WHERE dievas != ''
        GROUP BY dievas
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def get_dialogue_type_type_distribution_sql(self) -> Tuple[str, List[Tuple]]:
        """Sub-type analysis (dialoguetypetype)."""
        query = """
        SELECT dialoguetypetype, COUNT(*) as count
        FROM ways
        GROUP BY dialoguetypetype
        ORDER BY count DESC
        """
        return query, self._execute_query(query)

    def get_way_text_analysis_sql(self) -> Tuple[str, List[Tuple]]:
        """Text statistics (length, word count)."""
        query = """
        SELECT
            id,
            way,
            LENGTH(way) as way_length,
            LENGTH(examples) as examples_length,
            LENGTH(comments) as comments_length,
            (LENGTH(way) + LENGTH(examples) + LENGTH(comments)) as total_length
        FROM ways
        ORDER BY total_length DESC
        """
        return query, self._execute_query(query)

    # ============================================================================
    # NETWORK ANALYSIS SQL
    # ============================================================================

    def get_shared_partner_ways_sql(self, way_id: int) -> Tuple[str, List[Tuple]]:
        """Ways sharing dialogue partner with given way."""
        query = """
        SELECT w2.id, w2.way, w2.mene
        FROM ways w1
        JOIN ways w2 ON w1.dialoguewith = w2.dialoguewith
        WHERE w1.id = ? AND w2.id != ?
        ORDER BY w2.id
        """
        return query, self._execute_query(query, (way_id, way_id))

    def get_shared_room_ways_sql(self, way_id: int) -> Tuple[str, List[Tuple]]:
        """Ways in same room as given way."""
        query = """
        SELECT w2.id, w2.way, w2.dialoguewith
        FROM ways w1
        JOIN ways w2 ON w1.mene = w2.mene
        WHERE w1.id = ? AND w2.id != ?
        ORDER BY w2.id
        """
        return query, self._execute_query(query, (way_id, way_id))

    def get_way_connections_sql(self, way_id: int) -> Tuple[str, List[Tuple]]:
        """All connections for a way (shared partner or room)."""
        query = """
        SELECT DISTINCT w2.id, w2.way, w2.mene, w2.dialoguewith,
               CASE
                   WHEN w1.mene = w2.mene THEN 'same_room'
                   WHEN w1.dialoguewith = w2.dialoguewith THEN 'same_partner'
                   ELSE 'other'
               END as connection_type
        FROM ways w1
        JOIN ways w2 ON (w1.mene = w2.mene OR w1.dialoguewith = w2.dialoguewith)
        WHERE w1.id = ? AND w2.id != ?
        ORDER BY w2.id
        """
        return query, self._execute_query(query, (way_id, way_id))

    def get_network_edges_sql(self) -> Tuple[str, List[Tuple]]:
        """All way-to-way relationships."""
        query = """
        SELECT DISTINCT
            CASE WHEN w1.id < w2.id THEN w1.id ELSE w2.id END as way1_id,
            CASE WHEN w1.id < w2.id THEN w2.id ELSE w1.id END as way2_id,
            CASE
                WHEN w1.mene = w2.mene THEN 'same_room'
                WHEN w1.dialoguewith = w2.dialoguewith THEN 'same_partner'
                ELSE 'other'
            END as edge_type,
            w1.mene as room1,
            w2.mene as room2,
            w1.dialoguewith as partner1,
            w2.dialoguewith as partner2
        FROM ways w1
        JOIN ways w2 ON (
            (w1.mene = w2.mene AND w1.id < w2.id) OR
            (w1.dialoguewith = w2.dialoguewith AND w1.id < w2.id)
        )
        ORDER BY way1_id, way2_id
        """
        return query, self._execute_query(query)

    def get_central_ways_sql(self, limit: int = 20) -> Tuple[str, List[Tuple]]:
        """Ways with most connections."""
        query = f"""
        WITH way_connections AS (
            SELECT w1.id as way_id, COUNT(DISTINCT w2.id) as connection_count
            FROM ways w1
            JOIN ways w2 ON (
                w1.mene = w2.mene OR
                w1.dialoguewith = w2.dialoguewith
            )
            WHERE w1.id != w2.id
            GROUP BY w1.id
        )
        SELECT wc.way_id, w.way, wc.connection_count, w.mene, w.dialoguetype
        FROM way_connections wc
        JOIN ways w ON wc.way_id = w.id
        ORDER BY wc.connection_count DESC
        LIMIT {limit}
        """
        return query, self._execute_query(query)


# Convenience functions
def get_ways_sql_queries(db_path: str = None) -> WaysSQLQueries:
    """Get WaysSQLQueries instance."""
    return WaysSQLQueries(db_path)


def execute_ways_query(query_func: str, *args, **kwargs) -> Tuple[str, List[Tuple]]:
    """Execute a ways query by function name."""
    queries = WaysSQLQueries()
    method = getattr(queries, query_func)
    return method(*args, **kwargs)
