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

# Load configuration
load_dotenv('config.env')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', '/var/log/thermostat.log')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
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
        # Load configuration
        self.target_temp_heat = float(os.getenv('TARGET_TEMP_HEAT', 68.0))
        self.target_temp_cool = float(os.getenv('TARGET_TEMP_COOL', 74.0))
        self.hysteresis = float(os.getenv('HYSTERESIS', 0.5))
        self.sensor_read_interval = int(os.getenv('SENSOR_READ_INTERVAL', 30))
        self.anomaly_threshold = float(os.getenv('SENSOR_ANOMALY_THRESHOLD', 3.0))
        self.deviation_threshold = float(os.getenv('SENSOR_DEVIATION_THRESHOLD', 5.0))
        self.ignore_duration = int(os.getenv('SENSOR_IGNORE_DURATION', 3600))
        self.hvac_min_run_time = int(os.getenv('HVAC_MIN_RUN_TIME', 300))
        self.hvac_min_rest_time = int(os.getenv('HVAC_MIN_REST_TIME', 300))
        self.hvac_mode = os.getenv('HVAC_MODE', 'heat')
        
        # GPIO configuration
        self.gpio_relay_heat = int(os.getenv('GPIO_RELAY_HEAT', 17))
        self.gpio_relay_cool = int(os.getenv('GPIO_RELAY_COOL', 27))
        self.gpio_relay_fan = int(os.getenv('GPIO_RELAY_FAN', 22))
        self.gpio_relay_heat2 = int(os.getenv('GPIO_RELAY_HEAT2', 23))
        
        # Sensor mapping
        self.sensor_map = self._load_sensor_map()
        self.monitored_sensors = os.getenv('MONITORED_SENSORS', '').split(',')
        
        # State tracking
        self.sensor_history: Dict[str, List[SensorReading]] = {}
        self.compromised_sensors: Dict[str, datetime] = {}
        self.hvac_state = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
        self.last_hvac_change = datetime.now()
        self.last_sensor_read = datetime.now() - timedelta(seconds=self.sensor_read_interval)
        
        # Initialize GPIO
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_relay_heat, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.gpio_relay_cool, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.gpio_relay_fan, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.gpio_relay_heat2, GPIO.OUT, initial=GPIO.LOW)
            logger.info("GPIO initialized")
        
        logger.info(f"Thermostat initialized - Mode: {self.hvac_mode}, "
                   f"Heat: {self.target_temp_heat}°F, Cool: {self.target_temp_cool}°F")
    
    def _load_sensor_map(self) -> Dict[str, str]:
        """Load sensor ID to name mapping from environment"""
        sensor_map = {}
        for key, value in os.environ.items():
            if key.startswith('SENSOR_') and not key.startswith('SENSOR_READ') \
               and not key.startswith('SENSOR_ANOMALY') and not key.startswith('SENSOR_DEVIATION') \
               and not key.startswith('SENSOR_IGNORE'):
                sensor_name = key.replace('SENSOR_', '').replace('_', ' ').title()
                sensor_map[value] = sensor_name
        return sensor_map
    
    def read_sensors(self) -> List[SensorReading]:
        """Read all temperature sensors"""
        readings = []
        
        if not W1ThermSensor:
            # Development mode - return mock data
            logger.debug("Using mock sensor data (development mode)")
            for sensor_id, name in self.sensor_map.items():
                temp_c = 20.0 + (hash(sensor_id) % 5)
                temp_f = (temp_c * 9/5) + 32
                readings.append(SensorReading(sensor_id, name, temp_f, datetime.now()))
            return readings
        
        try:
            for sensor in W1ThermSensor.get_available_sensors():
                sensor_id = sensor.id
                if sensor_id in self.sensor_map:
                    temp_c = sensor.get_temperature()
                    temp_f = (temp_c * 9/5) + 32
                    name = self.sensor_map[sensor_id]
                    readings.append(SensorReading(sensor_id, name, temp_f, datetime.now()))
                    logger.debug(f"Sensor {name}: {temp_f:.1f}°F")
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
        
        return readings
    
    def detect_anomalies(self, readings: List[SensorReading]) -> None:
        """Detect compromised sensors (e.g., near active fireplace)"""
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
        """Control HVAC system based on system temperature"""
        if self.hvac_mode == 'off':
            self._set_hvac_state(heat=False, cool=False, fan=False, heat2=False)
            return
        
        # Check minimum run/rest time constraints
        time_since_change = (datetime.now() - self.last_hvac_change).total_seconds()
        
        current_running = self.hvac_state['heat'] or self.hvac_state['cool']
        if current_running and time_since_change < self.hvac_min_run_time:
            logger.debug(f"HVAC minimum run time not met ({time_since_change:.0f}s < "
                        f"{self.hvac_min_run_time}s)")
            return
        
        if not current_running and time_since_change < self.hvac_min_rest_time:
            logger.debug(f"HVAC minimum rest time not met ({time_since_change:.0f}s < "
                        f"{self.hvac_min_rest_time}s)")
            return
        
        # Heating mode
        if self.hvac_mode in ['heat', 'auto']:
            if system_temp < self.target_temp_heat - self.hysteresis:
                self._set_hvac_state(heat=True, cool=False, fan=True)
                # Enable secondary heat if temperature is very low
                if system_temp < self.target_temp_heat - 3.0:
                    self.hvac_state['heat2'] = True
                    if GPIO:
                        GPIO.output(self.gpio_relay_heat2, GPIO.HIGH)
            elif system_temp > self.target_temp_heat + self.hysteresis:
                self._set_hvac_state(heat=False, cool=False, fan=False, heat2=False)
        
        # Cooling mode
        if self.hvac_mode in ['cool', 'auto']:
            if system_temp > self.target_temp_cool + self.hysteresis:
                self._set_hvac_state(heat=False, cool=True, fan=True)
            elif system_temp < self.target_temp_cool - self.hysteresis:
                self._set_hvac_state(heat=False, cool=False, fan=False)
    
    def _set_hvac_state(self, heat: bool, cool: bool, fan: bool, heat2: bool = False) -> None:
        """Set HVAC relay states"""
        # Safety: Never activate heat and cool simultaneously
        if heat and cool:
            logger.error("Safety violation: Attempted to activate heat and cool simultaneously!")
            return
        
        # Check if state is changing
        new_state = {'heat': heat, 'cool': cool, 'fan': fan, 'heat2': heat2}
        if new_state == self.hvac_state:
            return
        
        # Update relays
        if GPIO:
            GPIO.output(self.gpio_relay_heat, GPIO.HIGH if heat else GPIO.LOW)
            GPIO.output(self.gpio_relay_cool, GPIO.HIGH if cool else GPIO.LOW)
            GPIO.output(self.gpio_relay_fan, GPIO.HIGH if fan else GPIO.LOW)
            GPIO.output(self.gpio_relay_heat2, GPIO.HIGH if heat2 else GPIO.LOW)
        
        self.hvac_state = new_state
        self.last_hvac_change = datetime.now()
        
        status = []
        if heat: status.append("HEAT")
        if cool: status.append("COOL")
        if fan: status.append("FAN")
        if heat2: status.append("HEAT2")
        logger.info(f"HVAC state changed: {' + '.join(status) if status else 'OFF'}")
    
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
        return {
            'hvac_mode': self.hvac_mode,
            'hvac_state': self.hvac_state.copy(),
            'target_temp_heat': self.target_temp_heat,
            'target_temp_cool': self.target_temp_cool,
            'compromised_sensors': list(self.compromised_sensors.keys()),
            'sensor_count': len(self.sensor_map)
        }
    
    def run(self) -> None:
        """Main control loop"""
        logger.info("Starting thermostat control loop")
        
        try:
            while True:
                # Read sensors
                if (datetime.now() - self.last_sensor_read).total_seconds() >= self.sensor_read_interval:
                    readings = self.read_sensors()
                    
                    if readings:
                        # Update history and detect anomalies
                        self.update_sensor_history(readings)
                        self.detect_anomalies(readings)
                        
                        # Calculate system temperature
                        system_temp = self.calculate_system_temperature(readings)
                        
                        # Control HVAC
                        if system_temp is not None:
                            self.control_hvac(system_temp)
                        
                        # Log status
                        status = self.get_status()
                        logger.info(f"System temp: {system_temp:.1f}°F, "
                                   f"HVAC: {status['hvac_state']}, "
                                   f"Compromised sensors: {len(status['compromised_sensors'])}")
                    
                    self.last_sensor_read = datetime.now()
                
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
            # Turn off all relays
            GPIO.output(self.gpio_relay_heat, GPIO.LOW)
            GPIO.output(self.gpio_relay_cool, GPIO.LOW)
            GPIO.output(self.gpio_relay_fan, GPIO.LOW)
            GPIO.output(self.gpio_relay_heat2, GPIO.LOW)
            GPIO.cleanup()
        logger.info("Cleanup complete")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Raspberry Pi Multi-Zone Thermostat Starting")
    logger.info("=" * 60)
    
    controller = ThermostatController()
    controller.run()


if __name__ == '__main__':
    main()
