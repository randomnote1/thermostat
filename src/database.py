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
                    target_temp REAL,
                    hvac_mode TEXT,
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
    
    # ==================== SETTINGS ====================
    
    def save_settings(self, target_temp_heat: float, target_temp_cool: float, 
                     hvac_mode: str, fan_mode: str = 'auto') -> None:
        """Save current thermostat settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (id, target_temp_heat, target_temp_cool, 
                                                hvac_mode, fan_mode, updated_at)
                VALUES (1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (target_temp_heat, target_temp_cool, hvac_mode, fan_mode))
            logger.debug(f"Settings saved: heat={target_temp_heat}, cool={target_temp_cool}, mode={hvac_mode}")
    
    def load_settings(self) -> Optional[Dict]:
        """Load current thermostat settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                return {
                    'target_temp_heat': row['target_temp_heat'],
                    'target_temp_cool': row['target_temp_cool'],
                    'hvac_mode': row['hvac_mode'],
                    'fan_mode': row['fan_mode'],
                    'updated_at': row['updated_at']
                }
            return None
    
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
                SELECT * FROM setting_history 
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
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if sensor_id:
                cursor.execute('''
                    SELECT * FROM sensor_history 
                    WHERE sensor_id = ? 
                    AND timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (sensor_id, hours, limit))
            else:
                cursor.execute('''
                    SELECT * FROM sensor_history 
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (hours, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== HVAC HISTORY ====================
    
    def log_hvac_state(self, system_temp: Optional[float], target_temp: Optional[float],
                      hvac_mode: str, heat: bool, cool: bool, fan: bool, heat2: bool) -> None:
        """Log HVAC state"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hvac_history (system_temp, target_temp, hvac_mode, 
                                        heat_active, cool_active, fan_active, heat2_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (system_temp, target_temp, hvac_mode, 
                  1 if heat else 0, 1 if cool else 0, 1 if fan else 0, 1 if heat2 else 0))
    
    def get_hvac_history(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get HVAC history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM hvac_history 
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
