#!/usr/bin/env python3
"""Database setup script for Ways of Figuring Things Out research.

Initializes SQLite database from MySQL dump and validates the conversion.
"""

import sys
from pathlib import Path

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from database import initialize_database
from models import (
    HouseOfKnowledge,
    WaysStatistics,
    way_from_sqlalchemy,
    room_from_sqlalchemy,
)


def main():
    """Main setup function."""
    print("Setting up Ways database...")

    # Initialize database from MySQL dump
    try:
        db = initialize_database()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return 1

    # Test database connectivity and basic queries
    try:
        # Get SQLAlchemy objects and convert to dataclasses
        sql_ways = db.get_all_ways()
        sql_rooms = db.get_all_rooms()

        # Convert SQLAlchemy objects to dataclasses
        ways = [way_from_sqlalchemy(sql_way) for sql_way in sql_ways]
        rooms = [room_from_sqlalchemy(sql_room) for sql_room in sql_rooms]

        print(f"✓ Found {len(ways)} ways and {len(rooms)} rooms")

        # Build House of Knowledge
        house = HouseOfKnowledge(rooms=rooms, ways=ways)

        # Link ways to rooms using dataclass instances
        # Create a lookup dictionary for rooms by short name
        room_lookup = {room.santrumpa: room for room in rooms}

        # Link ways to rooms
        for way in ways:
            room = room_lookup.get(way.mene)
            if room:
                way.room = room

        # Link ways to rooms (reverse relationship)
        for room in rooms:
            # Use HouseOfKnowledge method to get ways in this room
            room.ways = house.get_ways_in_room(room.santrumpa)

        # Get statistics
        stats = house.get_statistics()
        print(f"✓ Statistics computed:")
        print(f"  - Total ways: {stats.total_ways}")
        print(f"  - Ways with examples: {stats.ways_with_examples}")
        print(f"  - Most common dialogue type: {stats.most_common_dialogue_type}")
        print(f"  - Most populated room: {stats.most_populated_room}")

        # Show room distribution
        print("\n✓ Room distribution:")
        for room_short, count in sorted(stats.room_counts.items()):
            room = house.get_room_by_short(room_short)
            room_name = room.savoka if room else room_short
            print(f"  {room_short}: {count} ways ({room_name})")

        # Show dialogue type distribution
        print("\n✓ Dialogue type distribution:")
        for dt, count in sorted(stats.dialogue_type_counts.items()):
            print(f"  {dt}: {count} ways")

        print("\n✓ Database setup complete!")
        return 0

    except Exception as e:
        print(f"✗ Database validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

