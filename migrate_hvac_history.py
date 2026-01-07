#!/usr/bin/env python3
"""
Database migration script to update hvac_history table schema
Adds target_temp_heat, target_temp_cool, and fan_mode columns
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str) -> None:
    """Migrate hvac_history table to new schema
    
    This migration:
    1. Adds target_temp_heat, target_temp_cool, and fan_mode columns
    2. Migrates existing target_temp data based on hvac_mode
    3. Preserves all existing data
    
    Args:
        db_path: Path to thermostat.db
    """
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(hvac_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'target_temp_heat' in columns and 'target_temp_cool' in columns:
            print("✓ Database already migrated")
            return
        
        print("Starting migration...")
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Create new table with updated schema
        cursor.execute('''
            CREATE TABLE hvac_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_temp REAL,
                target_temp_heat REAL,
                target_temp_cool REAL,
                hvac_mode TEXT,
                fan_mode TEXT,
                heat_active INTEGER,
                cool_active INTEGER,
                fan_active INTEGER,
                heat2_active INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created new table schema")
        
        # Migrate data from old table
        # For old records, map target_temp to appropriate column based on hvac_mode
        cursor.execute('''
            INSERT INTO hvac_history_new 
                (id, system_temp, target_temp_heat, target_temp_cool, hvac_mode, fan_mode,
                 heat_active, cool_active, fan_active, heat2_active, timestamp)
            SELECT 
                id,
                system_temp,
                CASE 
                    WHEN hvac_mode = 'heat' THEN target_temp
                    WHEN hvac_mode = 'auto' THEN target_temp
                    ELSE NULL
                END as target_temp_heat,
                CASE 
                    WHEN hvac_mode = 'cool' THEN target_temp
                    WHEN hvac_mode = 'auto' THEN target_temp
                    ELSE NULL
                END as target_temp_cool,
                hvac_mode,
                'auto' as fan_mode,
                heat_active,
                cool_active,
                fan_active,
                heat2_active,
                timestamp
            FROM hvac_history
        ''')
        
        migrated_count = cursor.rowcount
        print(f"✓ Migrated {migrated_count} HVAC history records")
        
        # Drop old table
        cursor.execute("DROP TABLE hvac_history")
        print("✓ Removed old table")
        
        # Rename new table
        cursor.execute("ALTER TABLE hvac_history_new RENAME TO hvac_history")
        print("✓ Renamed new table")
        
        # Recreate index
        cursor.execute('''
            CREATE INDEX idx_hvac_history_timestamp 
            ON hvac_history(timestamp)
        ''')
        print("✓ Recreated indexes")
        
        # Commit transaction
        conn.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    # Default database path
    db_path = 'thermostat.db'
    
    # Allow custom path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        print("Usage: python migrate_hvac_history.py [path/to/thermostat.db]")
        sys.exit(1)
    
    # Backup recommendation
    print("⚠️  IMPORTANT: Back up your database before running migration!")
    print(f"   cp {db_path} {db_path}.backup")
    response = input("\nContinue with migration? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled")
        sys.exit(0)
    
    try:
        migrate_database(db_path)
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)
