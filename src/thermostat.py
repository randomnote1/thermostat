#!/usr/bin/env python3
"""
Raspberry Pi Multi-Zone Thermostat
Main control application
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from statistics import median
from typing import Dict, List, Optional
from dotenv import load_dotenv

try:
    import RPi.GPIO as GPIO
    from w1thermsensor import W1ThermSensor, Sensor
except ImportError:
    print("Warning: Running without GPIO/Sensor libraries (development mode)")
    GPIO = None
    W1ThermSensor = None

# Import temperature conversion utilities
from temperature_utils import (
    convert_temperature,
    fahrenheit_to_celsius,
    get_unit_symbol,
    format_temperature
)

# Try to import web interface (optional)
try:
    from web_interface import start_web_interface, update_state
    WEB_INTERFACE_AVAILABLE = True
except ImportError:
    WEB_INTERFACE_AVAILABLE = False
    print("Warning: Web interface not available (Flask not installed)")

# Import database module
try:
    from database import ThermostatDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Warning: Database module not available")

# Load configuration from project root
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.env')
load_dotenv(config_path)

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', '/var/log/thermostat.log')

# Create handlers list
handlers = [logging.StreamHandler(sys.stdout)]

# Add file handler if possible
try:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        # Try to create log directory
        os.makedirs(log_dir, exist_ok=True)
    handlers.append(logging.FileHandler(log_file))
except (PermissionError, OSError) as e:
    # Fall back to local log file if /var/log is not writable
    local_log_file = os.path.join(os.path.dirname(__file__), '..', 'thermostat.log')
    try:
        handlers.append(logging.FileHandler(local_log_file))
        print(f"Warning: Cannot write to {log_file}, logging to {local_log_file}")
    except Exception as e2:
        print(f"Warning: File logging disabled - {e}")

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


class SensorReading:
    """Represents a temperature reading from a sensor"""
    def __init__(self, sensor_id: str, name: str, temperature: float, timestamp: datetime):
        self.sensor_id = sensor_id
        self.name = name
        self.temperature = temperature
        self.timestamp = timestamp
        self.is_compromised = False


class ThermostatController:
    """Main thermostat control logic"""
    
    def __init__(self):
        # Initialize database
        self.db = None
        if DATABASE_AVAILABLE:
            db_path = os.getenv('DATABASE_PATH', 'thermostat.db')
            if db_path:  # Only create database if path is set
                self.db = ThermostatDatabase(db_path)
                logger.info(f"Database initialized: {db_path}")
        
        # Load configuration from environment (defaults in Fahrenheit, converted to Celsius)
        # Config file values are in Fahrenheit for user convenience
        self.target_temp_heat = fahrenheit_to_celsius(float(os.getenv('TARGET_TEMP_HEAT', 68.0)))
        self.target_temp_cool = fahrenheit_to_celsius(float(os.getenv('TARGET_TEMP_COOL', 74.0)))
        self.hysteresis = fahrenheit_to_celsius(float(os.getenv('HYSTERESIS', 0.5))) - fahrenheit_to_celsius(0)  # Convert delta
        self.sensor_read_interval = int(os.getenv('SENSOR_READ_INTERVAL', 30))
        self.anomaly_threshold = fahrenheit_to_celsius(float(os.getenv('SENSOR_ANOMALY_THRESHOLD', 3.0))) - fahrenheit_to_celsius(0)  # Convert delta
        self.deviation_threshold = fahrenheit_to_celsius(float(os.getenv('SENSOR_DEVIATION_THRESHOLD', 5.0))) - fahrenheit_to_celsius(0)  # Convert delta
        self.ignore_duration = int(os.getenv('SENSOR_IGNORE_DURATION', 3600))
        self.hvac_min_run_time = int(os.getenv('HVAC_MIN_RUN_TIME', 300))
        self.hvac_min_rest_time = int(os.getenv('HVAC_MIN_REST_TIME', 300))
        self.hvac_mode = os.getenv('HVAC_MODE', 'heat')
        self.history_log_interval = int(os.getenv('HISTORY_LOG_INTERVAL', 300))  # 5 minutes
        self.history_retention_days = int(os.getenv('HISTORY_RETENTION_DAYS', '1825'))  # 5 years
        self.history_max_disk_percent = float(os.getenv('HISTORY_MAX_DISK_PERCENT', '50.0'))  # 50%
        
        # Load persisted settings from database (stored in Celsius, overrides env)
        self.manual_fan_mode = False  # Default: fan is automatic (will be overridden by database if saved)
        if self.db:
            saved_settings = self.db.load_settings()
            if saved_settings:
                self.target_temp_heat = saved_settings['target_temp_heat']
                self.target_temp_cool = saved_settings['target_temp_cool']
                self.hvac_mode = saved_settings['hvac_mode']
                # Load fan mode setting
                fan_mode = saved_settings.get('fan_mode', 'auto')
                self.manual_fan_mode = (fan_mode == 'on')
                logger.info(f"Loaded persisted settings: heat={self.target_temp_heat}°C, "
                          f"cool={self.target_temp_cool}°C, mode={self.hvac_mode}, fan_mode={fan_mode}")
        
        # Load HVAC stages from database (dynamic N+1 stage support)
        self.heating_stages = []
        self.cooling_stages = []
        self.fan_gpio_pin = int(os.getenv('GPIO_RELAY_FAN', 22))
        
        if self.db:
            self._load_hvac_stages()
        else:
            # Fallback to config for backwards compatibility if no database
            self._load_stages_from_config()
        
        # Sensor mapping - load from database first, fall back to env
        self.sensor_map = {}
        self.monitored_sensors = []
        if self.db:
            self._load_sensors_from_database()
        
        # Load monitored sensor list from config (if not loaded from database)
        if not self.monitored_sensors:
            monitored = os.getenv('MONITORED_SENSORS', '')
            if monitored:
                self.monitored_sensors = [s.strip() for s in monitored.split(',') if s.strip()]
        
        # State tracking
        self.sensor_history: Dict[str, List[SensorReading]] = {}
        self.compromised_sensors: Dict[str, datetime] = {}
        # Track stage states dynamically
        self.active_heat_stages: List[int] = []  # List of active heating stage numbers
        self.active_cool_stages: List[int] = []  # List of active cooling stage numbers
        # Backwards compatible hvac_state for web interface
        self.hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        self.last_hvac_change = datetime.now()
        self.last_stage_changes: Dict[Tuple[str, int], datetime] = {}  # Track per-stage timing
        self.last_sensor_read = datetime.now() - timedelta(seconds=self.sensor_read_interval)
        self.last_history_log = datetime.now()
        self.last_schedule_check = datetime.now()
        self.last_cleanup = datetime.now()
        self.latest_readings: List[SensorReading] = []
        self.latest_system_temp: Optional[float] = None
        
        # Schedule control
        self.schedule_enabled = os.getenv('SCHEDULE_ENABLED', 'true').lower() == 'true'
        self.schedule_hold_until: Optional[datetime] = None  # Hold manual changes until this time
        self.schedule_hold_hours = int(os.getenv('SCHEDULE_HOLD_HOURS', '2'))  # Default 2 hours
        
        # Initialize web interface if enabled
        self.web_enabled = os.getenv('WEB_INTERFACE_ENABLED', 'true').lower() == 'true'
        if self.web_enabled and WEB_INTERFACE_AVAILABLE:
            from web_interface import set_control_callback, set_database
            web_port = int(os.getenv('WEB_PORT', 5000))
            start_web_interface(port=web_port)
            set_control_callback(self.handle_control_command)
            if self.db:
                set_database(self.db)
            logger.info(f"Web interface started on port {web_port}")
        
        # Initialize GPIO
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            # Initialize fan pin
            GPIO.setup(self.fan_gpio_pin, GPIO.OUT, initial=GPIO.LOW)
            # Initialize all stage pins
            for stage in self.heating_stages:
                GPIO.setup(stage['gpio_pin'], GPIO.OUT, initial=GPIO.LOW)
                logger.debug(f"Initialized heat stage {stage['stage_number']}: GPIO {stage['gpio_pin']}")
            for stage in self.cooling_stages:
                GPIO.setup(stage['gpio_pin'], GPIO.OUT, initial=GPIO.LOW)
                logger.debug(f"Initialized cool stage {stage['stage_number']}: GPIO {stage['gpio_pin']}")
            logger.info(f"GPIO initialized: {len(self.heating_stages)} heat stages, "
                       f"{len(self.cooling_stages)} cool stages")
        
        logger.info(f"Thermostat initialized - Mode: {self.hvac_mode}, "
                   f"Heat: {self.target_temp_heat}°F, Cool: {self.target_temp_cool}°F")
    
    def _load_hvac_stages(self) -> None:
        """Load HVAC stage configurations from database"""
        if not self.db:
            return
        
        # Load heating stages
        heat_stages = self.db.get_hvac_stages(stage_type='heat', enabled_only=True)
        self.heating_stages = heat_stages
        logger.info(f"Loaded {len(self.heating_stages)} heating stages from database")
        
        # Load cooling stages
        cool_stages = self.db.get_hvac_stages(stage_type='cool', enabled_only=True)
        self.cooling_stages = cool_stages
        logger.info(f"Loaded {len(self.cooling_stages)} cooling stages from database")
        
        # Log stage details
        for stage in self.heating_stages:
            logger.debug(f"  Heat Stage {stage['stage_number']}: GPIO {stage['gpio_pin']}, "
                        f"offset {stage['temp_offset']}°C, min_run={stage['min_run_time']}s")
        for stage in self.cooling_stages:
            logger.debug(f"  Cool Stage {stage['stage_number']}: GPIO {stage['gpio_pin']}, "
                        f"offset {stage['temp_offset']}°C, min_run={stage['min_run_time']}s")
    
    def _load_stages_from_config(self) -> None:
        """Fallback: Load stages from config.env if no database available"""
        logger.warning("Loading stages from config.env (database not available)")
        
        # Create default heating stages
        self.heating_stages = [
            {
                'id': 1,
                'stage_type': 'heat',
                'stage_number': 1,
                'gpio_pin': int(os.getenv('GPIO_RELAY_HEAT', 17)),
                'temp_offset': 0.28,  # ~0.5°F
                'min_run_time': self.hvac_min_run_time,
                'enabled': 1,
                'description': 'Primary heating'
            },
            {
                'id': 2,
                'stage_type': 'heat',
                'stage_number': 2,
                'gpio_pin': int(os.getenv('GPIO_RELAY_HEAT2', 23)),
                'temp_offset': 1.67,  # ~3°F
                'min_run_time': self.hvac_min_run_time,
                'enabled': 1,
                'description': 'Secondary/auxiliary heating'
            }
        ]
        
        # Create default cooling stages
        self.cooling_stages = [
            {
                'id': 3,
                'stage_type': 'cool',
                'stage_number': 1,
                'gpio_pin': int(os.getenv('GPIO_RELAY_COOL', 27)),
                'temp_offset': 0.28,  # ~0.5°F
                'min_run_time': self.hvac_min_run_time,
                'enabled': 1,
                'description': 'Primary cooling'
            }
        ]
    
    def _load_sensors_from_database(self) -> None:
        """Load sensor configuration from database"""
        if not self.db:
            return
        
        sensors = self.db.get_sensors(enabled_only=True)
        self.sensor_map = {}
        self.monitored_sensors = []
        
        for sensor in sensors:
            self.sensor_map[sensor['sensor_id']] = sensor['name']
            # Only add sensors that are both enabled AND monitored
            if sensor.get('monitored', False):
                self.monitored_sensors.append(sensor['sensor_id'])
        
        logger.debug(f"Loaded {len(self.sensor_map)} enabled sensors from database "
                    f"({len(self.monitored_sensors)} monitored for system temperature)")
    
    def _register_new_sensors(self, detected_sensors: List[str]) -> None:
        """Auto-register newly detected sensors in the database"""
        if not self.db:
            return
        
        for sensor_id in detected_sensors:
            existing = self.db.get_sensor(sensor_id)
            if not existing:
                # Auto-register with a default name
                name = f"Sensor {sensor_id[-6:]}"  # Last 6 chars of ID
                self.db.add_sensor(sensor_id, name, enabled=True, monitored=False)
                logger.info(f"Auto-registered new sensor: {sensor_id} as '{name}'")
                
                # Reload sensor map to include the new sensor
                self._load_sensors_from_database()
    
    def read_sensors(self) -> List[SensorReading]:
        """Read all temperature sensors (stores in Celsius)"""
        readings = []
        
        if not W1ThermSensor:
            # Development mode - return mock data in Celsius
            logger.debug("Using mock sensor data (development mode)")
            for sensor_id, name in self.sensor_map.items():
                temp_c = 20.0 + (hash(sensor_id) % 5)
                readings.append(SensorReading(sensor_id, name, temp_c, datetime.now()))
            return readings
        
        try:
            detected_sensor_ids = []
            for sensor in W1ThermSensor.get_available_sensors():
                sensor_id = sensor.id
                detected_sensor_ids.append(sensor_id)
                temp_c = sensor.get_temperature()
                
                # Use configured name if available, otherwise use sensor ID
                if sensor_id in self.sensor_map:
                    name = self.sensor_map[sensor_id]
                    logger.debug(f"Sensor {name}: {temp_c:.1f}°C")
                else:
                    name = f"Unconfigured ({sensor_id[:8]})"
                    logger.debug(f"Sensor {sensor_id} (unconfigured): {temp_c:.1f}°C")
                
                readings.append(SensorReading(sensor_id, name, temp_c, datetime.now()))
            
            # Auto-register any new sensors in the database
            if self.db and detected_sensor_ids:
                self._register_new_sensors(detected_sensor_ids)
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
        
        return readings
    
    def detect_anomalies(self, readings: List[SensorReading]) -> None:
        """Detect compromised sensors (e.g., near active fireplace)
        
        All enabled sensors are automatically monitored for anomalies like rapid
        temperature changes and deviations from the average.
        """
        if len(readings) < 2:
            return
        
        # Calculate average temperature (excluding already compromised sensors)
        valid_temps = [r.temperature for r in readings 
                      if not self._is_sensor_compromised(r.sensor_id)]
        if not valid_temps:
            return
        
        avg_temp = sum(valid_temps) / len(valid_temps)
        
        # Check each monitored sensor
        for reading in readings:
            if reading.sensor_id not in self.monitored_sensors:
                continue
            
            # Check for rapid temperature change
            if reading.sensor_id in self.sensor_history:
                history = self.sensor_history[reading.sensor_id]
                if history:
                    # Check readings from 5 minutes ago
                    five_min_ago = datetime.now() - timedelta(minutes=5)
                    old_readings = [r for r in history if r.timestamp <= five_min_ago]
                    if old_readings:
                        temp_change = reading.temperature - old_readings[-1].temperature
                        if abs(temp_change) > self.anomaly_threshold:
                            self._mark_sensor_compromised(reading.sensor_id, 
                                f"Rapid change: {temp_change:.1f}°F in 5 min")
            
            # Check for deviation from average
            deviation = reading.temperature - avg_temp
            if deviation > self.deviation_threshold:
                self._mark_sensor_compromised(reading.sensor_id,
                    f"Deviation: {deviation:.1f}°F above average")
        
        # Clear expired compromised flags
        now = datetime.now()
        expired = [sid for sid, expire_time in self.compromised_sensors.items() 
                  if now > expire_time]
        for sensor_id in expired:
            del self.compromised_sensors[sensor_id]
            logger.info(f"Sensor {self.sensor_map.get(sensor_id, sensor_id)} "
                       f"cleared from compromised status")
    
    def _mark_sensor_compromised(self, sensor_id: str, reason: str) -> None:
        """Mark a sensor as compromised"""
        if sensor_id not in self.compromised_sensors:
            expire_time = datetime.now() + timedelta(seconds=self.ignore_duration)
            self.compromised_sensors[sensor_id] = expire_time
            logger.warning(f"Sensor {self.sensor_map.get(sensor_id, sensor_id)} "
                         f"marked as compromised: {reason}")
    
    def _is_sensor_compromised(self, sensor_id: str) -> bool:
        """Check if a sensor is currently compromised"""
        if sensor_id not in self.compromised_sensors:
            return False
        return datetime.now() < self.compromised_sensors[sensor_id]
    
    def calculate_system_temperature(self, readings: List[SensorReading]) -> Optional[float]:
        """Calculate the system temperature using median of valid sensors"""
        valid_temps = [r.temperature for r in readings 
                      if not self._is_sensor_compromised(r.sensor_id)]
        
        if not valid_temps:
            logger.error("No valid temperature readings available!")
            return None
        
        system_temp = median(valid_temps)
        logger.debug(f"System temperature: {system_temp:.1f}°F "
                    f"(from {len(valid_temps)}/{len(readings)} sensors)")
        return system_temp
    
    def control_hvac(self, system_temp: float) -> None:
        """Control HVAC system with dynamic multi-stage support"""
        # Determine fan state based on manual mode or auto mode
        def get_fan_state(hvac_active: bool) -> bool:
            if self.manual_fan_mode:
                return True  # Manual continuous mode - always on
            else:
                return hvac_active  # Auto mode - on when HVAC is active
        
        if self.hvac_mode == 'off':
            # Turn off all stages and set fan per mode
            fan_state = get_fan_state(False)
            self._deactivate_all_stages(fan=fan_state)
            return
        
        # Check global minimum rest time (don't turn on HVAC if recently turned off)
        now = datetime.now()
        time_since_last_change = (now - self.last_hvac_change).total_seconds()
        hvac_currently_active = len(self.active_heat_stages) > 0 or len(self.active_cool_stages) > 0
        
        if not hvac_currently_active and time_since_last_change < self.hvac_min_rest_time:
            logger.debug(f"HVAC minimum rest time not met ({time_since_last_change:.0f}s < {self.hvac_min_rest_time}s)")
            return
        
        # Heating mode
        if self.hvac_mode in ['heat', 'auto']:
            temp_below_target = self.target_temp_heat - system_temp
            
            if temp_below_target > self.hysteresis:
                # Need heating - determine which stages to activate
                self._control_heating_stages(temp_below_target, get_fan_state(True))
            elif temp_below_target < -self.hysteresis:
                # Too hot - turn off heating
                self._deactivate_heating_stages(get_fan_state(False))
            else:
                # Within hysteresis - maintain current state or turn off if just reached comfortable
                if self.active_heat_stages:
                    # Don't turn off immediately - hysteresis should keep it running
                    pass
                else:
                    # Not running - ensure it stays off
                    self._deactivate_heating_stages(get_fan_state(False))
        
        # Cooling mode  
        if self.hvac_mode in ['cool', 'auto']:
            temp_above_target = system_temp - self.target_temp_cool
            
            if temp_above_target > self.hysteresis:
                # Need cooling - determine which stages to activate
                self._control_cooling_stages(temp_above_target, get_fan_state(True))
            elif temp_above_target < -self.hysteresis:
                # Too cool - turn off cooling
                self._deactivate_cooling_stages(get_fan_state(False))
            else:
                # Within hysteresis - maintain current state or turn off if just reached comfortable
                if self.active_cool_stages:
                    # Don't turn off immediately - hysteresis should keep it running
                    pass
                else:
                    # Not running - ensure it stays off
                    self._deactivate_cooling_stages(get_fan_state(False))
    
    def _control_heating_stages(self, temp_deficit: float, fan_state: bool) -> None:
        """Activate heating stages based on temperature deficit"""
        stages_to_activate = []
        
        # Determine which stages should be active based on temperature deficit
        for stage in self.heating_stages:
            if temp_deficit >= stage['temp_offset']:
                stages_to_activate.append(stage['stage_number'])
        
        # Ensure at least stage 1 is active if we need heat
        if not stages_to_activate and self.heating_stages:
            stages_to_activate.append(1)
        
        # Update stage states
        self._update_stages('heat', stages_to_activate, fan_state)
    
    def _control_cooling_stages(self, temp_excess: float, fan_state: bool) -> None:
        """Activate cooling stages based on temperature excess"""
        stages_to_activate = []
        
        # Determine which stages should be active based on temperature excess
        for stage in self.cooling_stages:
            if temp_excess >= stage['temp_offset']:
                stages_to_activate.append(stage['stage_number'])
        
        # Ensure at least stage 1 is active if we need cooling
        if not stages_to_activate and self.cooling_stages:
            stages_to_activate.append(1)
        
        # Update stage states
        self._update_stages('cool', stages_to_activate, fan_state)
    
    def _deactivate_heating_stages(self, fan_state: bool) -> None:
        """Deactivate all heating stages"""
        self._update_stages('heat', [], fan_state)
    
    def _deactivate_cooling_stages(self, fan_state: bool) -> None:
        """Deactivate all cooling stages"""
        self._update_stages('cool', [], fan_state)
    
    def _deactivate_all_stages(self, fan: bool) -> None:
        """Deactivate all HVAC stages"""
        self._update_stages('heat', [], fan)
        self._update_stages('cool', [], fan)
    
    def _update_stages(self, stage_type: str, stages_to_activate: List[int], fan_state: bool) -> None:
        """Update stage relay states with timing protection
        
        Args:
            stage_type: 'heat' or 'cool'
            stages_to_activate: List of stage numbers that should be active
            fan_state: Desired fan state
        """
        now = datetime.now()
        
        # Get current active stages and stage list
        if stage_type == 'heat':
            current_active = self.active_heat_stages.copy()
            stage_list = self.heating_stages
        else:  # cool
            current_active = self.active_cool_stages.copy()
            stage_list = self.cooling_stages
        
        # Check minimum run/rest time for any currently active stage
        for stage_num in current_active:
            stage_key = (stage_type, stage_num)
            if stage_key in self.last_stage_changes:
                time_since_change = (now - self.last_stage_changes[stage_key]).total_seconds()
                stage = next((s for s in stage_list if s['stage_number'] == stage_num), None)
                if stage and time_since_change < stage.get('min_run_time', 300):
                    logger.debug(f"{stage_type} stage {stage_num} minimum run time not met "
                               f"({time_since_change:.0f}s < {stage.get('min_run_time', 300)}s)")
                    return  # Don't change anything yet
        
        # Check minimum rest time for stages we want to activate
        for stage_num in stages_to_activate:
            if stage_num not in current_active:
                stage_key = (stage_type, stage_num)
                if stage_key in self.last_stage_changes:
                    time_since_change = (now - self.last_stage_changes[stage_key]).total_seconds()
                    stage = next((s for s in stage_list if s['stage_number'] == stage_num), None)
                    if stage and time_since_change < stage.get('min_run_time', 300):
                        logger.debug(f"{stage_type} stage {stage_num} minimum rest time not met "
                                   f"({time_since_change:.0f}s < {stage.get('min_run_time', 300)}s)")
                        return  # Don't activate yet
        
        # Safety check: don't activate both heat and cool
        if stage_type == 'heat' and stages_to_activate and self.active_cool_stages:
            logger.error("Safety violation: Attempted to activate heat while cooling is active!")
            return
        if stage_type == 'cool' and stages_to_activate and self.active_heat_stages:
            logger.error("Safety violation: Attempted to activate cool while heating is active!")
            return
        
        # Check if anything is actually changing (GPIO-wise)
        gpio_changes = stages_to_activate != current_active or fan_state != self.hvac_state['fan']
        
        if not gpio_changes:
            # Still update hvac_state to ensure consistency even if GPIO doesn't change
            self.hvac_state['heat'] = len(self.active_heat_stages) > 0
            self.hvac_state['cool'] = len(self.active_cool_stages) > 0
            self.hvac_state['fan'] = fan_state
            self.hvac_state['heat2'] = 2 in self.active_heat_stages
            return
        
        # Update GPIO pins for changed stages
        if GPIO:
            for stage in stage_list:
                stage_num = stage['stage_number']
                should_be_active = stage_num in stages_to_activate
                is_currently_active = stage_num in current_active
                
                if should_be_active != is_currently_active:
                    GPIO.output(stage['gpio_pin'], GPIO.HIGH if should_be_active else GPIO.LOW)
                    self.last_stage_changes[(stage_type, stage_num)] = now
                    logger.info(f"{stage_type.title()} Stage {stage_num} ({'ON' if should_be_active else 'OFF'}): "
                               f"GPIO {stage['gpio_pin']}")
            
            # Update fan
            GPIO.output(self.fan_gpio_pin, GPIO.HIGH if fan_state else GPIO.LOW)
        
        # Update active stage lists
        if stage_type == 'heat':
            self.active_heat_stages = stages_to_activate
        else:
            self.active_cool_stages = stages_to_activate
        
        # Update backwards-compatible hvac_state for web interface
        self.hvac_state['heat'] = len(self.active_heat_stages) > 0
        self.hvac_state['cool'] = len(self.active_cool_stages) > 0
        self.hvac_state['fan'] = fan_state
        self.hvac_state['heat2'] = 2 in self.active_heat_stages  # Backwards compat
        self.last_hvac_change = now
        
        # Log state change
        active_desc = []
        if self.active_heat_stages:
            active_desc.append(f"HEAT{self.active_heat_stages}")
        if self.active_cool_stages:
            active_desc.append(f"COOL{self.active_cool_stages}")
        if fan_state:
            active_desc.append("FAN")
        logger.info(f"HVAC state: {' + '.join(active_desc) if active_desc else 'OFF'}")
    
    def update_sensor_history(self, readings: List[SensorReading]) -> None:
        """Update sensor reading history"""
        for reading in readings:
            if reading.sensor_id not in self.sensor_history:
                self.sensor_history[reading.sensor_id] = []
            
            self.sensor_history[reading.sensor_id].append(reading)
            
            # Keep only last 30 minutes of history
            cutoff_time = datetime.now() - timedelta(minutes=30)
            self.sensor_history[reading.sensor_id] = [
                r for r in self.sensor_history[reading.sensor_id] 
                if r.timestamp > cutoff_time
            ]
    
    def get_status(self) -> Dict:
        """Get current system status"""
        status = {
            'hvac_mode': self.hvac_mode,
            'hvac_state': self.hvac_state.copy(),
            'manual_fan_mode': self.manual_fan_mode,
            'target_temp_heat': self.target_temp_heat,
            'target_temp_cool': self.target_temp_cool,
            'compromised_sensors': list(self.compromised_sensors.keys()),
            'sensor_count': len(self.sensor_map),
            'system_temp': self.latest_system_temp,
            'schedule_enabled': self.schedule_enabled,
            'schedule_on_hold': self.schedule_hold_until is not None,
            'sensor_readings': [
                {
                    'id': r.sensor_id,
                    'name': r.name,
                    'temperature': r.temperature,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.latest_readings
            ]
        }
        
        # Add hold expiration time if active
        if self.schedule_hold_until:
            status['schedule_hold_until'] = self.schedule_hold_until.isoformat()
        
        return status
    
    @property
    def fan_mode(self) -> str:
        """Get current fan mode as string ('on' for continuous, 'auto' for automatic)"""
        return 'on' if self.manual_fan_mode else 'auto'
    
    def _update_web_interface(self) -> None:
        """Update web interface with current state"""
        if self.web_enabled and WEB_INTERFACE_AVAILABLE:
            try:
                update_state(self.get_status())
            except Exception as e:
                logger.debug(f"Web interface update failed: {e}")
    
    def run(self) -> None:
        """Main control loop"""
        logger.info("Starting thermostat control loop")
        
        try:
            while True:
                now = datetime.now()
                
                # Check schedules (every minute)
                if (now - self.last_schedule_check).total_seconds() >= 60:
                    self._check_schedules(now)
                    self.last_schedule_check = now
                
                # Read sensors
                if (now - self.last_sensor_read).total_seconds() >= self.sensor_read_interval:
                    readings = self.read_sensors()
                    
                    if readings:
                        # Update history and detect anomalies
                        self.update_sensor_history(readings)
                        self.detect_anomalies(readings)
                        
                        # Calculate system temperature
                        system_temp = self.calculate_system_temperature(readings)
                        
                        # Store latest readings for web interface
                        self.latest_readings = readings
                        self.latest_system_temp = system_temp
                        
                        # Control HVAC
                        if system_temp is not None:
                            self.control_hvac(system_temp)
                        
                        # Log sensor readings to database
                        if self.db and (now - self.last_history_log).total_seconds() >= self.history_log_interval:
                            self._log_sensor_history(readings)
                            self._log_hvac_history(system_temp)
                            self.last_history_log = now
                        
                        # Clean up old history once per day
                        if self.db and (now - self.last_cleanup).total_seconds() >= 86400:  # 24 hours
                            logger.info("Running daily database cleanup...")
                            try:
                                self.db.smart_cleanup(self.history_retention_days, self.history_max_disk_percent)
                            except Exception as e:
                                logger.error(f"Database cleanup failed: {e}")
                            self.last_cleanup = now
                        
                        # Update web interface
                        self._update_web_interface()
                        
                        # Log status
                        status = self.get_status()
                        logger.info(f"System temp: {system_temp:.1f}°F, "
                                   f"HVAC: {status['hvac_state']}, "
                                   f"Compromised sensors: {len(status['compromised_sensors'])}")
                    
                    self.last_sensor_read = now
                
                # Sleep to prevent CPU spinning
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("Cleaning up...")
        if GPIO:
            # Turn off all stage relays
            for stage in self.heating_stages:
                GPIO.output(stage['gpio_pin'], GPIO.LOW)
            for stage in self.cooling_stages:
                GPIO.output(stage['gpio_pin'], GPIO.LOW)
            # Turn off fan
            GPIO.output(self.fan_gpio_pin, GPIO.LOW)
            GPIO.cleanup()
        logger.info("Cleanup complete")
    
    def _check_schedules(self, current_time: datetime) -> None:
        """Check and apply active schedules"""
        if not self.db:
            return
        
        # Check if schedules are globally disabled
        if not self.schedule_enabled:
            return
        
        # Check if there's an active manual hold
        if self.schedule_hold_until and current_time < self.schedule_hold_until:
            logger.debug(f"Schedules on hold until {self.schedule_hold_until}")
            return
        
        # Clear expired hold
        if self.schedule_hold_until and current_time >= self.schedule_hold_until:
            logger.info("Schedule hold expired, resuming automatic schedules")
            self.schedule_hold_until = None
        
        active_schedules = self.db.get_active_schedules(current_time)
        
        for schedule in active_schedules:
            logger.info(f"Applying schedule: {schedule['name']}")
            
            # Apply temperature changes
            if schedule['target_temp_heat'] is not None:
                old_temp = self.target_temp_heat
                self.target_temp_heat = schedule['target_temp_heat']
                self.db.log_setting_change('target_temp_heat', str(old_temp), 
                                          str(self.target_temp_heat), f"schedule:{schedule['name']}")
            
            if schedule['target_temp_cool'] is not None:
                old_temp = self.target_temp_cool
                self.target_temp_cool = schedule['target_temp_cool']
                self.db.log_setting_change('target_temp_cool', str(old_temp), 
                                          str(self.target_temp_cool), f"schedule:{schedule['name']}")
            
            # Apply mode change
            if schedule['hvac_mode'] is not None:
                old_mode = self.hvac_mode
                self.hvac_mode = schedule['hvac_mode']
                self.db.log_setting_change('hvac_mode', old_mode, 
                                          self.hvac_mode, f"schedule:{schedule['name']}")
            
            # Persist changes
            self.db.save_settings(self.target_temp_heat, self.target_temp_cool, 
                                self.hvac_mode, self.fan_mode)
            
            logger.info(f"Schedule applied: heat={self.target_temp_heat}°F, "
                       f"cool={self.target_temp_cool}°F, mode={self.hvac_mode}")
    
    def _log_sensor_history(self, readings: List[SensorReading]) -> None:
        """Log sensor readings to database"""
        if not self.db:
            return
        
        batch_data = [
            (r.sensor_id, r.name, r.temperature, r.is_compromised)
            for r in readings
        ]
        self.db.log_sensor_readings_batch(batch_data)
        logger.debug(f"Logged {len(readings)} sensor readings to history")
    
    def _log_hvac_history(self, system_temp: Optional[float]) -> None:
        """Log HVAC state to database with active stage information"""
        if not self.db:
            return
        
        # Build active stages list for logging
        active_stages_list = []
        for stage_num in self.active_heat_stages:
            stage = next((s for s in self.heating_stages if s['stage_number'] == stage_num), None)
            if stage:
                active_stages_list.append({
                    'type': 'heat',
                    'number': stage_num,
                    'gpio_pin': stage['gpio_pin']
                })
        for stage_num in self.active_cool_stages:
            stage = next((s for s in self.cooling_stages if s['stage_number'] == stage_num), None)
            if stage:
                active_stages_list.append({
                    'type': 'cool',
                    'number': stage_num,
                    'gpio_pin': stage['gpio_pin']
                })
        
        self.db.log_hvac_state(
            system_temp=system_temp,
            target_temp_heat=self.target_temp_heat,
            target_temp_cool=self.target_temp_cool,
            hvac_mode=self.hvac_mode,
            fan_mode=self.fan_mode,
            heat=self.hvac_state['heat'],
            cool=self.hvac_state['cool'],
            fan=self.hvac_state['fan'],
            heat2=self.hvac_state['heat2'],
            active_stages=active_stages_list if active_stages_list else None
        )
    
    def handle_control_command(self, command: str, params: Dict) -> Dict:
        """Handle control commands from web interface
        
        Args:
            command: Command type ('set_temperature', 'set_mode', 'set_fan')
            params: Command parameters
            
        Returns:
            Dict with result status
        """
        logger.info(f"Control command received: {command} with params {params}")
        
        try:
            if command == 'set_temperature':
                temp_type = params.get('type')
                temperature = params.get('temperature')  # Expects Celsius from web interface
                
                # Validate temperature range (10°C to 32°C, roughly 50°F to 90°F)
                if temperature < 10 or temperature > 32:
                    logger.warning(f"Temperature {temperature}°C out of range")
                    return {'success': False, 'error': 'Temperature out of range (10-32°C)'}
                
                if temp_type == 'heat':
                    old_temp = self.target_temp_heat
                    self.target_temp_heat = temperature
                    logger.info(f"Target heat temperature set to {temperature}°C")
                    
                    # Persist to database and log change
                    if self.db:
                        self.db.save_settings(self.target_temp_heat, self.target_temp_cool, 
                                            self.hvac_mode, self.fan_mode)
                        self.db.log_setting_change('target_temp_heat', str(old_temp), str(temperature), 'web_interface')
                    
                    # Set schedule hold
                    self._set_schedule_hold()
                
                elif temp_type == 'cool':
                    old_temp = self.target_temp_cool
                    self.target_temp_cool = temperature
                    logger.info(f"Target cool temperature set to {temperature}°C")
                    
                    # Persist to database and log change
                    if self.db:
                        self.db.save_settings(self.target_temp_heat, self.target_temp_cool, 
                                            self.hvac_mode, self.fan_mode)
                        self.db.log_setting_change('target_temp_cool', str(old_temp), str(temperature), 'web_interface')
                    
                    # Set schedule hold
                    self._set_schedule_hold()
                
                else:
                    return {'success': False, 'error': 'Invalid temperature type'}
                
                return {'success': True, 'message': f'Target {temp_type} temperature set to {temperature}°C'}
            
            elif command == 'set_mode':
                mode = params.get('mode')
                
                # Validate mode
                if mode not in ['heat', 'cool', 'auto', 'off']:
                    logger.warning(f"Invalid mode: {mode}")
                    return {'success': False, 'error': 'Invalid mode'}
                
                old_mode = self.hvac_mode
                self.hvac_mode = mode
                logger.info(f"HVAC mode set to {mode}")
                
                # Persist to database and log change
                if self.db:
                    self.db.save_settings(self.target_temp_heat, self.target_temp_cool, 
                                        self.hvac_mode, self.fan_mode)
                    self.db.log_setting_change('hvac_mode', old_mode, mode, 'web_interface')
                    
                    # Immediately log to HVAC history so it appears right away
                    system_temp = self.calculate_system_temperature(self.latest_readings)
                    self._log_hvac_history(system_temp)
                
                # Set schedule hold
                self._set_schedule_hold()
                
                # If mode is 'off', turn off all HVAC
                if mode == 'off':
                    fan_state = False if not self.manual_fan_mode else True
                    self._deactivate_all_stages(fan=fan_state)
                
                return {'success': True, 'message': f'HVAC mode set to {mode}'}
            
            elif command == 'set_fan':
                fan_on = params.get('fan_on', False)
                
                # Toggle manual fan mode based on state
                # If fan_on=True, enable manual continuous mode
                # If fan_on=False, disable manual mode (return to auto)
                old_manual_mode = self.manual_fan_mode
                
                self.manual_fan_mode = fan_on  # True = continuous, False = auto
                
                logger.info(f"Fan set to {'CONTINUOUS' if fan_on else 'AUTO'} (manual_fan_mode={self.manual_fan_mode})")
                
                # Determine desired fan state
                # In manual mode, fan should be ON
                # In auto mode, fan follows HVAC state (on if heating or cooling)
                desired_fan_state = fan_on if self.manual_fan_mode else (len(self.active_heat_stages) > 0 or len(self.active_cool_stages) > 0)
                
                # Update fan state (both GPIO and internal state)
                if GPIO:
                    GPIO.output(self.fan_gpio_pin, GPIO.HIGH if desired_fan_state else GPIO.LOW)
                    logger.info(f"Fan GPIO set to {'ON' if desired_fan_state else 'OFF'}")
                
                # Always update internal state regardless of GPIO availability
                self.hvac_state['fan'] = desired_fan_state
                
                # Persist fan mode setting and log to both histories
                if self.db:
                    # Save fan mode to database
                    fan_mode = 'on' if fan_on else 'auto'
                    self.db.save_settings(self.target_temp_heat, self.target_temp_cool, self.hvac_mode, fan_mode)
                    
                    # Log to settings history
                    old_fan_mode = 'on' if old_manual_mode else 'auto'
                    self.db.log_setting_change('fan_mode', old_fan_mode, fan_mode, 'web_interface')
                    
                    # Log to HVAC history
                    system_temp = self.calculate_system_temperature(self.latest_readings)
                    self._log_hvac_history(system_temp)
                
                return {'success': True, 'message': f"Fan set to {'CONTINUOUS' if fan_on else 'AUTO'}"}
            
            elif command == 'resume_schedules':
                return self.resume_schedules()
            
            elif command == 'set_schedule_enabled':
                enabled = params.get('enabled', True)
                return self.set_schedule_enabled(enabled)
            
            elif command == 'reload_sensors':
                # Reload sensor configuration from database
                if self.db:
                    self._load_sensors_from_database()
                    logger.info("Sensor configuration reloaded from database")
                    return {'success': True, 'message': 'Sensor configuration reloaded'}
                else:
                    return {'success': False, 'error': 'Database not available'}
            
            elif command == 'reload_stages':
                # Reload HVAC stage configuration from database
                if self.db:
                    self._load_hvac_stages()
                    logger.info("HVAC stage configuration reloaded from database")
                    return {'success': True, 'message': 'HVAC stage configuration reloaded'}
                else:
                    return {'success': False, 'error': 'Database not available'}
            
            else:
                logger.warning(f"Unknown command: {command}")
                return {'success': False, 'error': 'Unknown command'}
        
        except Exception as e:
            logger.error(f"Error handling control command: {e}")
            return {'success': False, 'error': str(e)}
    
    def _set_schedule_hold(self) -> None:
        """Set a temporary hold on schedules after manual changes
        
        Only activates if schedules exist in the database. If no schedules
        are configured, there's nothing to override, so manual changes just
        become the current active values.
        """
        # Don't set hold if no database or schedules configured
        if not self.db:
            return
        
        # Check if any schedules exist (enabled or disabled)
        schedules = self.db.get_schedules(enabled_only=False)
        if not schedules:
            logger.debug("No schedules configured, manual change applied without hold")
            return
        
        # Set hold only if configured and schedules exist
        if self.schedule_hold_hours > 0:
            self.schedule_hold_until = datetime.now() + timedelta(hours=self.schedule_hold_hours)
            logger.info(f"Schedule hold activated until {self.schedule_hold_until}")
    
    def resume_schedules(self) -> Dict:
        """Clear schedule hold and resume automatic scheduling"""
        self.schedule_hold_until = None
        logger.info("Schedule hold cleared, automatic scheduling resumed")
        return {'success': True, 'message': 'Schedules resumed'}
    
    def set_schedule_enabled(self, enabled: bool) -> Dict:
        """Enable or disable schedule system globally"""
        self.schedule_enabled = enabled
        if not enabled:
            self.schedule_hold_until = None  # Clear hold when disabling
        logger.info(f"Schedules globally {'enabled' if enabled else 'disabled'}")
        return {'success': True, 'message': f"Schedules {'enabled' if enabled else 'disabled'}"}


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Raspberry Pi Multi-Zone Thermostat Starting")
    logger.info("=" * 60)
    
    controller = ThermostatController()
    controller.run()


if __name__ == '__main__':
    main()
