#!/usr/bin/env python3
"""
Database module for thermostat persistence
Handles settings, schedules, and history logging
"""

import sqlite3
import logging
from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ThermostatDatabase:
    """Manages SQLite database for thermostat data"""
    
    def __init__(self, db_path: str = 'thermostat.db'):
        self.db_path = db_path
        self._init_database()
        self._migrate_schema()  # Auto-migrate on initialization
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Settings table - current thermostat settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    target_temp_heat REAL NOT NULL,
                    target_temp_cool REAL NOT NULL,
                    hvac_mode TEXT NOT NULL,
                    fan_mode TEXT DEFAULT 'auto',
                    temperature_units TEXT DEFAULT 'F',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Schedules table - time-based temperature programs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    days_of_week TEXT NOT NULL,
                    time TEXT NOT NULL,
                    target_temp_heat REAL,
                    target_temp_cool REAL,
                    hvac_mode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sensors table - sensor configuration and labels
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensors (
                    sensor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    monitored INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Setting history - audit log of setting changes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS setting_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sensor history - temperature readings over time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    sensor_name TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    is_compromised INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # HVAC history - track when HVAC runs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hvac_history (
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
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_history_timestamp 
                ON sensor_history(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_history_sensor_id 
                ON sensor_history(sensor_id, timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_setting_history_timestamp 
                ON setting_history(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hvac_history_timestamp 
                ON hvac_history(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedules_enabled 
                ON schedules(enabled, days_of_week, time)
            ''')
            
            logger.info(f"Database initialized at {self.db_path}")
    
    def _migrate_schema(self) -> None:
        """Apply schema migrations for database upgrades"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Migration: Add target_temp_heat, target_temp_cool, fan_mode to hvac_history
            cursor.execute("PRAGMA table_info(hvac_history)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'target_temp_heat' not in columns or 'target_temp_cool' not in columns:
                logger.info("Migrating hvac_history table schema...")
                
                try:
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
                    
                    # Migrate data from old table (handle legacy target_temp field)
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
                    
                    # Drop old table and rename new one
                    cursor.execute("DROP TABLE hvac_history")
                    cursor.execute("ALTER TABLE hvac_history_new RENAME TO hvac_history")
                    
                    # Recreate index
                    cursor.execute('''
                        CREATE INDEX idx_hvac_history_timestamp 
                        ON hvac_history(timestamp)
                    ''')
                    
                    logger.info("✓ hvac_history table migration completed")
                except Exception as e:
                    logger.error(f"Schema migration failed: {e}")
                    raise
    
    # ==================== SETTINGS ====================
    
    def save_settings(self, target_temp_heat: float, target_temp_cool: float, 
                     hvac_mode: str, fan_mode: str = 'auto', 
                     temperature_units: str = 'F') -> None:
        """Save current thermostat settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (id, target_temp_heat, target_temp_cool, 
                                                hvac_mode, fan_mode, temperature_units, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (target_temp_heat, target_temp_cool, hvac_mode, fan_mode, temperature_units))
            logger.debug(f"Settings saved: heat={target_temp_heat}, cool={target_temp_cool}, mode={hvac_mode}, units={temperature_units}")
    
    def load_settings(self) -> Optional[Dict]:
        """Load current thermostat settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                # Handle temperature_units column that might not exist in old databases
                try:
                    temperature_units = row['temperature_units']
                except (KeyError, IndexError):
                    temperature_units = 'F'
                
                return {
                    'target_temp_heat': row['target_temp_heat'],
                    'target_temp_cool': row['target_temp_cool'],
                    'hvac_mode': row['hvac_mode'],
                    'fan_mode': row['fan_mode'],
                    'temperature_units': temperature_units,
                    'updated_at': row['updated_at']
                }
            return None
    
    # ==================== SENSORS ====================
    
    def add_sensor(self, sensor_id: str, name: str, enabled: bool = True, 
                   monitored: bool = False) -> None:
        """Add a new sensor to the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sensors (sensor_id, name, enabled, monitored, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (sensor_id, name, int(enabled), int(monitored)))
            logger.debug(f"Sensor added/updated: {sensor_id} -> {name} (enabled={enabled}, monitored={monitored})")
    
    def get_sensor(self, sensor_id: str) -> Optional[Dict]:
        """Get a single sensor by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sensors WHERE sensor_id = ?', (sensor_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'sensor_id': row['sensor_id'],
                    'name': row['name'],
                    'enabled': bool(row['enabled']),
                    'monitored': bool(row['monitored']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
    
    def get_sensors(self, enabled_only: bool = False) -> List[Dict]:
        """Get all sensors from the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if enabled_only:
                cursor.execute('SELECT * FROM sensors WHERE enabled = 1 ORDER BY name')
            else:
                cursor.execute('SELECT * FROM sensors ORDER BY name')
            
            rows = cursor.fetchall()
            sensors = []
            
            for row in rows:
                sensors.append({
                    'sensor_id': row['sensor_id'],
                    'name': row['name'],
                    'enabled': bool(row['enabled']),
                    'monitored': bool(row['monitored']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return sensors
    
    def update_sensor(self, sensor_id: str, name: str = None, 
                     enabled: bool = None, monitored: bool = None) -> bool:
        """Update sensor properties"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically based on provided parameters
            updates = []
            params = []
            
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            
            if enabled is not None:
                updates.append('enabled = ?')
                params.append(int(enabled))
            
            if monitored is not None:
                updates.append('monitored = ?')
                params.append(int(monitored))
            
            if not updates:
                return False
            
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(sensor_id)
            
            query = f"UPDATE sensors SET {', '.join(updates)} WHERE sensor_id = ?"
            cursor.execute(query, params)
            
            if cursor.rowcount > 0:
                logger.debug(f"Sensor updated: {sensor_id}")
                return True
            return False
    
    def delete_sensor(self, sensor_id: str) -> bool:
        """Delete a sensor from the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sensors WHERE sensor_id = ?', (sensor_id,))
            
            if cursor.rowcount > 0:
                logger.debug(f"Sensor deleted: {sensor_id}")
                return True
            return False
    
    # ==================== SETTING HISTORY ====================
    
    def log_setting_change(self, setting_name: str, old_value: str, 
                          new_value: str, source: str = 'manual') -> None:
        """Log a setting change to history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO setting_history (setting_name, old_value, new_value, source)
                VALUES (?, ?, ?, ?)
            ''', (setting_name, old_value, new_value, source))
            logger.debug(f"Logged setting change: {setting_name} {old_value} -> {new_value} ({source})")
    
    def get_setting_history(self, limit: int = 100) -> List[Dict]:
        """Get recent setting changes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    id,
                    setting_name,
                    old_value,
                    new_value,
                    timestamp || 'Z' as timestamp
                FROM setting_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SCHEDULES ====================
    
    def create_schedule(self, name: str, days_of_week: str, time_str: str,
                       target_temp_heat: Optional[float] = None,
                       target_temp_cool: Optional[float] = None,
                       hvac_mode: Optional[str] = None) -> int:
        """Create a new schedule
        
        Args:
            name: Schedule name (e.g., "Weekday Morning")
            days_of_week: Comma-separated days (e.g., "Mon,Tue,Wed,Thu,Fri" or "0,1,2,3,4")
            time_str: Time in HH:MM format (e.g., "06:00")
            target_temp_heat: Optional heating setpoint
            target_temp_cool: Optional cooling setpoint
            hvac_mode: Optional mode override (heat/cool/auto/off)
        
        Returns:
            Schedule ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO schedules (name, days_of_week, time, target_temp_heat, 
                                     target_temp_cool, hvac_mode)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, days_of_week, time_str, target_temp_heat, target_temp_cool, hvac_mode))
            
            schedule_id = cursor.lastrowid
            logger.info(f"Created schedule: {name} at {time_str} on {days_of_week}")
            return schedule_id
    
    def get_schedules(self, enabled_only: bool = False) -> List[Dict]:
        """Get all schedules"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if enabled_only:
                cursor.execute('SELECT * FROM schedules WHERE enabled = 1 ORDER BY time')
            else:
                cursor.execute('SELECT * FROM schedules ORDER BY time')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_schedule(self, schedule_id: int, **kwargs) -> None:
        """Update a schedule"""
        allowed_fields = ['name', 'enabled', 'days_of_week', 'time', 
                         'target_temp_heat', 'target_temp_cool', 'hvac_mode']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return
        
        updates['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [schedule_id]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE schedules 
                SET {set_clause}
                WHERE id = ?
            ''', values)
            logger.info(f"Updated schedule {schedule_id}: {updates}")
    
    def delete_schedule(self, schedule_id: int) -> None:
        """Delete a schedule"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
            logger.info(f"Deleted schedule {schedule_id}")
    
    def get_active_schedules(self, current_time: datetime) -> List[Dict]:
        """Get schedules that should be active now"""
        day_of_week = current_time.strftime('%a')  # Mon, Tue, etc.
        day_number = str(current_time.weekday())  # 0-6
        current_time_str = current_time.strftime('%H:%M')
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM schedules 
                WHERE enabled = 1 
                AND (days_of_week LIKE ? OR days_of_week LIKE ?)
                AND time = ?
            ''', (f'%{day_of_week}%', f'%{day_number}%', current_time_str))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SENSOR HISTORY ====================
    
    def log_sensor_reading(self, sensor_id: str, sensor_name: str, 
                          temperature: float, is_compromised: bool = False) -> None:
        """Log a sensor reading"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sensor_history (sensor_id, sensor_name, temperature, is_compromised)
                VALUES (?, ?, ?, ?)
            ''', (sensor_id, sensor_name, temperature, 1 if is_compromised else 0))
    
    def log_sensor_readings_batch(self, readings: List[Tuple[str, str, float, bool]]) -> None:
        """Log multiple sensor readings at once"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO sensor_history (sensor_id, sensor_name, temperature, is_compromised)
                VALUES (?, ?, ?, ?)
            ''', readings)
            logger.debug(f"Logged {len(readings)} sensor readings")
    
    def get_sensor_history(self, sensor_id: Optional[str] = None, 
                          hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get sensor reading history
        
        Args:
            sensor_id: Optional sensor ID to filter by
            hours: Number of hours of history to retrieve
            limit: Maximum number of records
            
        Returns current sensor name from sensors table via JOIN
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if sensor_id:
                cursor.execute('''
                    SELECT 
                        sh.id,
                        sh.sensor_id,
                        COALESCE(s.name, sh.sensor_name) as sensor_name,
                        sh.temperature,
                        sh.is_compromised,
                        sh.timestamp || 'Z' as timestamp
                    FROM sensor_history sh
                    LEFT JOIN sensors s ON sh.sensor_id = s.sensor_id
                    WHERE sh.sensor_id = ? 
                    AND sh.timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY sh.timestamp DESC 
                    LIMIT ?
                ''', (sensor_id, hours, limit))
            else:
                cursor.execute('''
                    SELECT 
                        sh.id,
                        sh.sensor_id,
                        COALESCE(s.name, sh.sensor_name) as sensor_name,
                        sh.temperature,
                        sh.is_compromised,
                        sh.timestamp || 'Z' as timestamp
                    FROM sensor_history sh
                    LEFT JOIN sensors s ON sh.sensor_id = s.sensor_id
                    WHERE sh.timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY sh.timestamp DESC 
                    LIMIT ?
                ''', (hours, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== HVAC HISTORY ====================
    
    def log_hvac_state(self, system_temp: Optional[float], 
                      target_temp_heat: Optional[float], target_temp_cool: Optional[float],
                      hvac_mode: str, fan_mode: str, heat: bool, cool: bool, fan: bool, heat2: bool) -> None:
        """Log HVAC state with both target temperatures
        
        Args:
            system_temp: Current system temperature
            target_temp_heat: Heating setpoint
            target_temp_cool: Cooling setpoint
            hvac_mode: HVAC mode (heat/cool/auto/off)
            fan_mode: Fan mode (auto/on)
            heat: Heat relay state
            cool: Cool relay state
            fan: Fan relay state
            heat2: Heat2 relay state (aux/emergency heat)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hvac_history (system_temp, target_temp_heat, target_temp_cool, 
                                        hvac_mode, fan_mode, heat_active, cool_active, 
                                        fan_active, heat2_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (system_temp, target_temp_heat, target_temp_cool, hvac_mode, fan_mode,
                  1 if heat else 0, 1 if cool else 0, 1 if fan else 0, 1 if heat2 else 0))
    
    def get_hvac_history(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get HVAC history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    id,
                    system_temperature,
                    target_temp_heat,
                    target_temp_cool,
                    hvac_mode,
                    fan_mode,
                    heat,
                    cool,
                    fan,
                    heat2,
                    timestamp || 'Z' as timestamp
                FROM hvac_history 
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (hours, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== MAINTENANCE ====================
    
    def cleanup_old_history(self, days_to_keep: int = 30) -> None:
        """Remove old history records"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Keep setting history forever (it's small)
            
            # Clean sensor history
            cursor.execute('''
                DELETE FROM sensor_history 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days_to_keep,))
            sensor_deleted = cursor.rowcount
            
            # Clean HVAC history
            cursor.execute('''
                DELETE FROM hvac_history 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days_to_keep,))
            hvac_deleted = cursor.rowcount
            
            logger.info(f"Cleaned up old history: {sensor_deleted} sensor, {hvac_deleted} HVAC records")
    
    def smart_cleanup(self, min_days_to_keep: int = 1825, max_disk_percent: float = 50.0) -> None:
        """Smart cleanup that respects both time and disk space constraints
        
        Args:
            min_days_to_keep: Minimum retention period (default 5 years = 1825 days)
            max_disk_percent: Maximum % of disk space database can use (default 50%)
        """
        import shutil
        
        db_path = Path(self.db_path)
        if not db_path.exists():
            return
        
        # Get disk usage
        disk_usage = shutil.disk_usage(db_path.parent)
        total_space = disk_usage.total
        db_size = db_path.stat().st_size
        db_percent = (db_size / total_space) * 100
        
        logger.info(f"Database size: {db_size / (1024*1024):.1f} MB ({db_percent:.2f}% of disk)")
        
        # Always clean up records older than minimum retention
        if min_days_to_keep > 0:
            self.cleanup_old_history(min_days_to_keep)
        
        # If still over disk limit, gradually delete older data
        if db_percent > max_disk_percent:
            logger.warning(f"Database exceeds {max_disk_percent}% disk limit ({db_percent:.2f}%)")
            
            # Delete in 30-day increments beyond minimum retention
            days_to_delete = min_days_to_keep + 30
            max_iterations = 10  # Safety limit
            
            for i in range(max_iterations):
                self.cleanup_old_history(days_to_delete)
                
                # Recalculate size after cleanup and VACUUM
                with self._get_connection() as conn:
                    conn.execute('VACUUM')
                
                db_size = db_path.stat().st_size
                db_percent = (db_size / total_space) * 100
                
                logger.info(f"After cleanup: {db_size / (1024*1024):.1f} MB ({db_percent:.2f}% of disk)")
                
                if db_percent <= max_disk_percent:
                    logger.info(f"Database now within {max_disk_percent}% disk limit")
                    break
                
                days_to_delete += 30
            
            if db_percent > max_disk_percent:
                logger.error(f"Unable to reduce database below {max_disk_percent}% limit after {max_iterations} iterations")
        else:
            logger.info(f"Database within {max_disk_percent}% disk limit")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            for table in ['settings', 'schedules', 'setting_history', 'sensor_history', 'hvac_history']:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Database file size
            if Path(self.db_path).exists():
                stats['db_size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            return stats
