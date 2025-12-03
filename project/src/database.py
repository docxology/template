"""Database layer for Ways of Figuring Things Out research.

Converts MySQL dump to SQLite and provides ORM models for querying
the ways, rooms, questions, and other entities in Andrius Kulikauskas's
philosophical framework.
"""

import sqlite3
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship
from sqlalchemy.orm import Session as SQLAlchemySession


class Base(DeclarativeBase):
    """SQLAlchemy base class for all database models."""
    pass


# Association table for klausimobudai (question-ways relationships)
question_way_association = Table(
    'klausimobudai',
    Base.metadata,
    Column('klausimobudonr', Integer, primary_key=True),
    Column('klausimonr', Integer, ForeignKey('klausimai.klausimonr')),
    Column('budonr', Integer, ForeignKey('ways.ID'))
)


class Way(Base):
    """A way of figuring things out."""
    __tablename__ = 'ways'

    id: Mapped[int] = mapped_column('ID', Integer, primary_key=True)
    way: Mapped[str] = mapped_column(String(255))
    dialoguewith: Mapped[str] = mapped_column(String(255))
    dialoguetype: Mapped[str] = mapped_column(String(255))
    dialoguetypetype: Mapped[str] = mapped_column(String(255))
    wayurl: Mapped[str] = mapped_column(String(255))
    examples: Mapped[str] = mapped_column(Text)
    dialoguetypetypetype: Mapped[str] = mapped_column(String(100))
    mene: Mapped[str] = mapped_column(String(10))
    dievas: Mapped[str] = mapped_column(String(255))
    comments: Mapped[str] = mapped_column(String(500))
    laikinas: Mapped[str] = mapped_column(String(100))

    # Relationship to room through mene field
    room: Mapped[Optional['Room']] = relationship('Room', foreign_keys=[mene],
                                                  primaryjoin="Way.mene == Room.santrumpa")

    def __repr__(self) -> str:
        return f"Way(id={self.id}, way='{self.way[:30]}...', dialoguewith='{self.dialoguewith}')"


class Room(Base):
    """A room in the House of Knowledge."""
    __tablename__ = 'rooms'

    numeris: Mapped[int] = mapped_column(Integer, primary_key=True)
    santrumpa: Mapped[str] = mapped_column(String(50), unique=True)
    savoka: Mapped[str] = mapped_column(String(255))
    issiaiskinimas: Mapped[str] = mapped_column(String(255))
    eilestvarka: Mapped[int] = mapped_column(Integer)
    laipsnis: Mapped[int] = mapped_column(Integer)
    sparnas: Mapped[int] = mapped_column(Integer)
    rusis: Mapped[str] = mapped_column(String(50))
    pasnekovas: Mapped[str] = mapped_column(String(255))
    dievas: Mapped[str] = mapped_column(String(255))
    pastabos: Mapped[str] = mapped_column(String(500))
    label: Mapped[str] = mapped_column(String(50))

    # Ways in this room
    ways: Mapped[List[Way]] = relationship('Way', foreign_keys=[Way.mene],
                                          primaryjoin="Room.santrumpa == Way.mene")

    def __repr__(self) -> str:
        return f"Room(numeris={self.numeris}, santrumpa='{self.santrumpa}', savoka='{self.savoka}')"


class Question(Base):
    """A question in the philosophical framework."""
    __tablename__ = 'klausimai'

    klausimonr: Mapped[int] = mapped_column(Integer, primary_key=True)
    klausimas: Mapped[str] = mapped_column(String(500))
    mastytojas: Mapped[str] = mapped_column(String(250))
    svetaine: Mapped[str] = mapped_column(String(250))
    pasisakymas: Mapped[str] = mapped_column(Text)
    patarimas: Mapped[str] = mapped_column(Text)
    menes: Mapped[str] = mapped_column(String(500))

    # Ways associated with this question
    ways: Mapped[List[Way]] = relationship('Way', secondary=question_way_association,
                                          primaryjoin="Question.klausimonr == klausimobudai.c.klausimonr",
                                          secondaryjoin="Way.id == klausimobudai.c.budonr")

    def __repr__(self) -> str:
        return f"Question(klausimonr={self.klausimonr}, klausimas='{self.klausimas[:50]}...')"


class Example(Base):
    """An example from the 2010 pavyzdžiai table."""
    __tablename__ = 'examples'

    # Auto-generated ID since the original table doesn't have one
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    way: Mapped[str] = mapped_column(String(250))
    rusis: Mapped[str] = mapped_column(String(250))
    pavyzdziai: Mapped[str] = mapped_column(String(250))

    def __repr__(self) -> str:
        return f"Example(way='{self.way[:30]}...', rusis='{self.rusis}')"


class WaysDatabase:
    """Main interface for the Ways database."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to project/db/ways.db
            project_root = Path(__file__).parent.parent
            db_path = project_root / "db" / "ways.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine and session
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def initialize_from_mysql_dump(self, mysql_dump_path: str = None) -> None:
        """Convert MySQL dump to SQLite database.

        Args:
            mysql_dump_path: Path to MySQL dump file. If None, uses default.
        """
        if mysql_dump_path is None:
            mysql_dump_path = self.db_path.parent / "andrius_ways.sql"

        if not Path(mysql_dump_path).exists():
            raise FileNotFoundError(f"MySQL dump not found at {mysql_dump_path}")

        # Check if database already has data
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ways'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                # Check if table has data
                cursor.execute("SELECT COUNT(*) FROM ways")
                count = cursor.fetchone()[0]
                if count > 0:
                    # Database already initialized with data
                    return

            # Parse and convert the MySQL dump (includes DROP TABLE statements)
            sqlite_sql = self._convert_mysql_to_sqlite(mysql_dump_path)

            # Execute statements one by one to handle errors gracefully
            statements = [s.strip() for s in sqlite_sql.split('\n') if s.strip()]

            for stmt in statements:
                try:
                    cursor.execute(stmt)
                except sqlite3.OperationalError as e:
                    # Log problematic statements but continue
                    print(f"Warning: Skipping problematic SQL statement: {e}")
                    print(f"Statement: {stmt[:100]}...")
                    continue

        # Note: We don't create SQLAlchemy tables since we imported the schema via raw SQL
        # The SQLAlchemy models are just for querying existing tables

    def _convert_mysql_to_sqlite(self, mysql_dump_path: str) -> str:
        """Convert MySQL dump to SQLite compatible SQL."""
        with open(mysql_dump_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split into statements
        statements = []
        current_statement = []
        in_multiline_comment = False
        in_create_table = False
        table_name = None

        for line in content.split('\n'):
            line = line.strip()

            # Skip MySQL-specific comments and settings
            if line.startswith('/*!') or line.startswith('--'):
                continue
            if line.startswith('SET ') or line.startswith('USE '):
                continue
            if line.startswith('LOCK TABLES') or line.startswith('UNLOCK TABLES'):
                continue

            # Handle multiline comments
            if '/*!' in line:
                in_multiline_comment = True
                continue
            if in_multiline_comment:
                if '*/' in line:
                    in_multiline_comment = False
                continue

            # Skip empty lines
            if not line:
                continue

            # Track CREATE TABLE statements
            if line.startswith('CREATE TABLE'):
                in_create_table = True
                table_name = line.split('`')[1] if '`' in line else None

            current_statement.append(line)

            # End of statement
            if line.endswith(';'):
                stmt = ' '.join(current_statement)
                current_statement = []

                # Convert MySQL syntax to SQLite
                converted_stmts = self._mysql_to_sqlite_syntax(stmt, table_name)
                statements.extend([s for s in converted_stmts if s])

                in_create_table = False
                table_name = None

        # Handle table renames for clarity and SQLite compatibility
        # Keep table names simple but avoid conflicts
        table_renames = {
            '`20100422ways`': '`ways`',
            '`20110421Birasai`': '`birasaai`',  # Rename to avoid numeric start
            '`20110421irasai`': '`irasai_old`',  # Rename to avoid numeric start
            '`20110422pavyzdziai`': '`pavyzdziai_old`',  # Rename to avoid numeric start
            '`klausimai`': '`klausimai`',
            '`2010pavyzdziai`': '`examples`'
            # Note: keeping 'menes' as-is to avoid conflicts with column names
        }

        # Also handle unquoted table names (for INSERT statements)
        unquoted_renames = {
            '20100422ways': 'ways',
            '20110421Birasai': 'birasaai',
            '20110421irasai': 'irasai_old',
            '20110422pavyzdziai': 'pavyzdziai_old',
            'klausimai': 'klausimai',
            '2010pavyzdziai': 'examples'
            # Note: keeping 'menes' as-is
        }

        converted_sql = []
        for stmt in statements:
            # Replace quoted table names
            for old_name, new_name in table_renames.items():
                stmt = stmt.replace(old_name, new_name)

            # Replace unquoted table names only in specific contexts
            if stmt.startswith('INSERT INTO '):
                # In INSERT INTO table_name, replace table name
                for old_name, new_name in unquoted_renames.items():
                    # Replace table name right after INSERT INTO
                    stmt = re.sub(rf'INSERT INTO\s+{re.escape(old_name)}\b', f'INSERT INTO {new_name}', stmt)
            elif stmt.startswith('CREATE INDEX '):
                # In CREATE INDEX name ON table_name, replace table name
                for old_name, new_name in unquoted_renames.items():
                    stmt = re.sub(rf'ON\s+{re.escape(old_name)}\b', f'ON {new_name}', stmt)

            converted_sql.append(stmt)

        # Fix index name conflicts and duplicates after table renames
        # SQLite doesn't allow index names to match any table name or duplicate globally
        final_sql = []
        used_index_names = set()  # Track all used index names globally

        # Collect all table names that will be created
        table_names = set()
        for stmt in converted_sql:
            if stmt.startswith('CREATE TABLE'):
                table_match = re.search(r'CREATE TABLE\s+`([^`]+)`', stmt)
                if table_match:
                    table_names.add(table_match.group(1))

        for stmt in converted_sql:
            if stmt.startswith('CREATE INDEX'):
                # Extract index name and table name
                index_match = re.search(r'CREATE INDEX\s+`([^`]+)`\s+ON\s+`([^`]+)`', stmt)
                if index_match:
                    index_name = index_match.group(1)
                    table_name = index_match.group(2)

                    # Rename index if it conflicts with any table name or is already used
                    original_name = index_name
                    while index_name in table_names or index_name in used_index_names:
                        if index_name in table_names:
                            index_name = f"{table_name}_{original_name}_idx"
                        else:
                            # Find a unique name
                            counter = 1
                            base_name = original_name
                            while f"{base_name}_{counter}" in used_index_names:
                                counter += 1
                            index_name = f"{base_name}_{counter}"

                    used_index_names.add(index_name)
                    stmt = stmt.replace(f'`{original_name}`', f'`{index_name}`', 1)

            final_sql.append(stmt)

        return '\n'.join(final_sql)

    def _mysql_to_sqlite_syntax(self, mysql_stmt: str, table_name: str = None) -> List[str]:
        """Convert MySQL syntax to SQLite. Returns list of statements."""
        # Remove MySQL-specific keywords
        stmt = re.sub(r'\s+AUTO_INCREMENT\s*=?\s*\d*', '', mysql_stmt)
        stmt = re.sub(r'\s+ENGINE\s*=\s*\w+', '', stmt)
        stmt = re.sub(r'\s+DEFAULT\s+CHARSET\s*=\s*\w+', '', stmt)
        stmt = re.sub(r'\s+COLLATE\s*=[\w_]+', '', stmt)
        stmt = re.sub(r'\s+CHARACTER\s+SET\s*=[\w_]+', '', stmt)
        # Remove COLLATE and CHARACTER SET from anywhere in the statement
        stmt = re.sub(r'COLLATE\s+[\w_]+', '', stmt)
        stmt = re.sub(r'CHARACTER\s+SET\s+[\w_]+', '', stmt)

        # Convert data types
        stmt = stmt.replace('int(11)', 'INTEGER')
        stmt = stmt.replace('varchar(255)', 'TEXT')
        stmt = stmt.replace('varchar(500)', 'TEXT')
        stmt = stmt.replace('varchar(100)', 'TEXT')
        stmt = stmt.replace('varchar(50)', 'TEXT')
        stmt = stmt.replace('varchar(250)', 'TEXT')
        stmt = stmt.replace('varchar(10)', 'TEXT')
        stmt = stmt.replace('varchar(1000)', 'TEXT')
        stmt = stmt.replace('varchar(5000)', 'TEXT')

        # Special handling: don't rename column names that match table names
        # The klausimai table has a column called 'menes' which should not be renamed to 'rooms'
        # This column is likely a foreign key or descriptive field

        statements = []

        # Handle CREATE TABLE with KEY statements
        if stmt.startswith('CREATE TABLE') and 'KEY' in stmt:
            # Extract KEY definitions (KEY statements after PRIMARY KEY)
            key_pattern = r',\s*KEY\s+`([^`]+)`\s*\(([^)]+)\)'
            keys = re.findall(key_pattern, stmt)

            # Remove KEY definitions from CREATE TABLE
            stmt = re.sub(key_pattern, '', stmt)

            # Clean up the statement - remove everything after the PRIMARY KEY closing paren
            # Find the position of PRIMARY KEY (...) and keep only up to the closing paren
            primary_key_match = re.search(r'PRIMARY KEY\s*\([^)]+\)', stmt)
            if primary_key_match:
                end_pos = primary_key_match.end()
                stmt = stmt[:end_pos] + ');'
            else:
                # Fallback: just remove everything after the last column definition
                last_column_match = re.findall(r'`[^`]+`\s+[^,]+', stmt)
                if last_column_match:
                    # Find position after the last complete column definition
                    for match in re.finditer(r'`[^`]+`\s+[^,]+,', stmt):
                        pass
                    if 'match' in locals():
                        stmt = stmt[:match.end()] + ');'
                    else:
                        stmt = stmt + ');'

            statements.append(stmt)

            # Create separate CREATE INDEX statements
            for key_name, columns in keys:
                # Handle multiple columns and function calls like examples(333)
                # SQLite doesn't support function calls in indexes, so extract column name
                if '(' in columns:
                    # Extract column name before the function call
                    # e.g., `examples`(333) -> `examples`
                    col_match = re.search(r'`([^`]+)`', columns)
                    if col_match:
                        col_spec = f"`{col_match.group(1)}`"
                    else:
                        # Fallback: use the part before the opening paren
                        col_spec = columns.split('(')[0].strip()
                else:
                    col_list = [col.strip().strip('`') for col in columns.split(',')]
                    col_spec = ', '.join(f'`{col}`' for col in col_list)
                
                # Rename index if it conflicts with table name (SQLite doesn't allow this)
                index_name = key_name
                if index_name == table_name:
                    index_name = f"{key_name}_idx"
                
                index_stmt = f"CREATE INDEX `{index_name}` ON `{table_name}` ({col_spec});"
                statements.append(index_stmt)

        # Handle CREATE INDEX statements - rename if index name conflicts with table name
        elif stmt.startswith('CREATE INDEX'):
            # Extract index name and table name
            index_match = re.search(r'CREATE INDEX\s+`([^`]+)`\s+ON\s+`([^`]+)`', stmt)
            if index_match:
                index_name = index_match.group(1)
                table_name_from_index = index_match.group(2)
                # Rename index if it conflicts with table name
                if index_name == table_name_from_index:
                    stmt = stmt.replace(f'`{index_name}`', f'`{index_name}_idx`', 1)
            statements.append(stmt)
        
        # Handle INSERT statements - ensure proper quoting and fix quotes
        elif stmt.startswith('INSERT INTO'):
            # Add backticks around column names if they're not already quoted
            # Pattern: INSERT INTO table (col1, col2, ...) VALUES
            insert_match = re.match(r'INSERT INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES', stmt)
            if insert_match:
                table_name = insert_match.group(1)
                columns_part = insert_match.group(2)
                # Add backticks around column names
                columns_quoted = ', '.join(f'`{col.strip()}`' for col in columns_part.split(','))
                stmt = stmt.replace(f'({columns_part})', f'({columns_quoted})')

            # Convert MySQL-style escaped quotes (\') to SQLite-style ('')
            stmt = stmt.replace("\\'", "''")
            statements.append(stmt)

        else:
            statements.append(stmt)

        return statements

    def get_session(self) -> SQLAlchemySession:
        """Get a database session."""
        return self.SessionLocal()

    def get_all_ways(self) -> List[Way]:
        """Get all ways."""
        with self.get_session() as session:
            return session.query(Way).all()

    def get_ways_by_room(self, room_short: str) -> List[Way]:
        """Get ways in a specific room."""
        with self.get_session() as session:
            return session.query(Way).filter(Way.mene == room_short).all()

    def get_room_by_short(self, short_name: str) -> Optional[Room]:
        """Get room by short name."""
        with self.get_session() as session:
            return session.query(Room).filter(Room.santrumpa == short_name).first()

    def get_all_rooms(self) -> List[Room]:
        """Get all rooms in the House of Knowledge."""
        with self.get_session() as session:
            return session.query(Room).order_by(Room.eilestvarka).all()

    def get_ways_by_dialogue_type(self, dialogue_type: str) -> List[Way]:
        """Get ways by dialogue type."""
        with self.get_session() as session:
            return session.query(Way).filter(Way.dialoguetype == dialogue_type).all()

    def get_questions(self) -> List[Question]:
        """Get all questions."""
        with self.get_session() as session:
            return session.query(Question).all()

    def get_examples(self) -> List[Example]:
        """Get all examples."""
        with self.get_session() as session:
            return session.query(Example).all()

    def get_way_statistics(self) -> Dict[str, Any]:
        """Get statistics about ways."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get total ways
        cursor.execute("SELECT COUNT(*) FROM ways")
        total_ways = cursor.fetchone()[0]

        # Count by dialogue type
        cursor.execute("SELECT dialoguetype, COUNT(*) FROM ways GROUP BY dialoguetype")
        dialogue_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Count by room
        cursor.execute("SELECT mene, COUNT(*) FROM ways GROUP BY mene")
        room_counts = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_ways': total_ways,
            'dialogue_types': dialogue_counts,
            'room_distribution': room_counts
        }

    def validate_database(self) -> Dict[str, Any]:
        """Validate database integrity and report statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        validation = {
            'tables': {},
            'total_rows': 0,
            'data_quality': {}
        }

        # Check all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                validation['tables'][table] = count
                validation['total_rows'] += count
            except:
                validation['tables'][table] = 'error'

        # Check data quality for ways table
        if 'ways' in validation['tables'] and validation['tables']['ways'] > 0:
            # Check for missing required fields
            cursor.execute("SELECT COUNT(*) FROM ways WHERE way = '' OR dialoguetype = ''")
            empty_fields = cursor.fetchone()[0]
            validation['data_quality']['empty_required_fields'] = empty_fields

            # Check for ways with examples
            cursor.execute("SELECT COUNT(*) FROM ways WHERE examples != ''")
            ways_with_examples = cursor.fetchone()[0]
            validation['data_quality']['ways_with_examples'] = ways_with_examples

        conn.close()
        return validation


# Convenience functions
def initialize_database(db_path: str = None, mysql_dump_path: str = None) -> WaysDatabase:
    """Initialize the database from MySQL dump."""
    db = WaysDatabase(db_path)
    db.initialize_from_mysql_dump(mysql_dump_path)
    return db


def get_database(db_path: str = None) -> WaysDatabase:
    """Get database instance (assumes already initialized)."""
    return WaysDatabase(db_path)
