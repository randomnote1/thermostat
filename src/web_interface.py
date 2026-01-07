#!/usr/bin/env python3
"""
Web interface for thermostat monitoring
Simple Flask-based dashboard for local network access
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, render_template, jsonify, request
from threading import Thread, Lock

# Import temperature conversion utilities
from temperature_utils import convert_temperature, get_unit_symbol

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Shared state (thread-safe)
state_lock = Lock()
current_state = {
    'system_temp': None,
    'target_temp_heat': None,
    'target_temp_cool': None,
    'hvac_state': {},
    'sensor_readings': [],
    'compromised_sensors': [],
    'last_update': None,
    'hvac_mode': 'off'
}

# Control callback (set by thermostat controller)
control_callback = None
database = None  # Database reference for schedules and history


def set_control_callback(callback):
    """Set callback function for control commands"""
    global control_callback
    control_callback = callback


def set_database(db):
    """Set database reference for direct access"""
    global database
    database = db


def update_state(controller_state: Dict) -> None:
    """Update shared state from thermostat controller"""
    global current_state
    with state_lock:
        current_state.update(controller_state)
        current_state['last_update'] = datetime.now().isoformat()


def get_state() -> Dict:
    """Get current state (thread-safe)"""
    with state_lock:
        return current_state.copy()


def get_temperature_units() -> str:
    """Get current temperature units preference from database"""
    if database:
        settings = database.load_settings()
        if settings:
            return settings.get('temperature_units', 'F')
    return 'F'  # Default to Fahrenheit


def convert_state_temperatures(state: Dict, to_units: str) -> Dict:
    """Convert all temperatures in state dict from Celsius to specified units
    
    Args:
        state: State dictionary with temperatures in Celsius
        to_units: Target temperature units ('F', 'C', or 'K')
        
    Returns:
        State dict with converted temperatures
    """
    converted = state.copy()
    
    # Convert scalar temperatures
    if state.get('system_temp') is not None:
        converted['system_temp'] = convert_temperature(state['system_temp'], 'C', to_units)
    
    if state.get('target_temp_heat') is not None:
        converted['target_temp_heat'] = convert_temperature(state['target_temp_heat'], 'C', to_units)
    
    if state.get('target_temp_cool') is not None:
        converted['target_temp_cool'] = convert_temperature(state['target_temp_cool'], 'C', to_units)
    
    # Convert sensor readings
    if 'sensor_readings' in state:
        converted['sensor_readings'] = []
        for reading in state['sensor_readings']:
            converted_reading = reading.copy()
            if 'temperature' in reading and reading['temperature'] is not None:
                converted_reading['temperature'] = convert_temperature(
                    reading['temperature'], 'C', to_units
                )
            converted['sensor_readings'].append(converted_reading)
    
    # Add unit info to state
    converted['temperature_units'] = to_units
    converted['temperature_symbol'] = get_unit_symbol(to_units)
    
    return converted


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/schedules')
def schedules_page():
    """Schedules management page"""
    return render_template('schedules.html')


@app.route('/history')
def history_page():
    """History viewing page"""
    return render_template('history.html')


@app.route('/settings')
def settings_page():
    """Settings page"""
    return render_template('settings.html')


@app.route('/api/status')
def api_status():
    """API endpoint for current status"""
    state = get_state()
    units = get_temperature_units()
    converted_state = convert_state_temperatures(state, units)
    return jsonify(converted_state)


@app.route('/api/sensors')
def api_sensors():
    """API endpoint for sensor details"""
    state = get_state()
    units = get_temperature_units()
    sensors = []
    
    for reading in state.get('sensor_readings', []):
        temp_celsius = reading.get('temperature')
        temp_display = convert_temperature(temp_celsius, 'C', units) if temp_celsius is not None else None
        
        sensors.append({
            'id': reading.get('id'),
            'name': reading.get('name'),
            'temperature': temp_display,
            'timestamp': reading.get('timestamp'),
            'compromised': reading.get('id') in state.get('compromised_sensors', [])
        })
    
    return jsonify({
        'sensors': sensors,
        'temperature_units': units,
        'temperature_symbol': get_unit_symbol(units)
    })


@app.route('/api/hvac')
def api_hvac():
    """API endpoint for HVAC status"""
    state = get_state()
    units = get_temperature_units()
    
    # Convert temperatures for display
    target_heat = convert_temperature(state.get('target_temp_heat'), 'C', units) if state.get('target_temp_heat') is not None else None
    target_cool = convert_temperature(state.get('target_temp_cool'), 'C', units) if state.get('target_temp_cool') is not None else None
    system_temp = convert_temperature(state.get('system_temp'), 'C', units) if state.get('system_temp') is not None else None
    
    return jsonify({
        'mode': state.get('hvac_mode'),
        'state': state.get('hvac_state'),
        'target_heat': target_heat,
        'target_cool': target_cool,
        'system_temp': system_temp,
        'temperature_units': units,
        'temperature_symbol': get_unit_symbol(units)
    })


@app.route('/api/control/temperature', methods=['POST'])
def api_control_temperature():
    """API endpoint to set target temperature"""
    if not control_callback:
        return jsonify({'error': 'Control not available'}), 503
    
    try:
        data = request.json
        temp_type = data.get('type')  # 'heat' or 'cool'
        temperature = float(data.get('temperature'))
        
        # Get current temperature units to know what the user sent
        units = get_temperature_units()
        
        # Define validation ranges based on units
        if units == 'F':
            min_temp, max_temp = 50, 90
        elif units == 'C':
            min_temp, max_temp = 10, 32
        else:  # Kelvin
            min_temp, max_temp = 283, 305
        
        # Validate temperature range
        if temperature < min_temp or temperature > max_temp:
            symbol = get_unit_symbol(units)
            return jsonify({'error': f'Temperature out of range ({min_temp}-{max_temp}{symbol})'}), 400
        
        # Convert to Celsius for internal use
        temperature_celsius = convert_temperature(temperature, units, 'C')
        
        # Send control command (expects Celsius)
        result = control_callback('set_temperature', {
            'type': temp_type,
            'temperature': temperature_celsius
        })
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/control/mode', methods=['POST'])
def api_control_mode():
    """API endpoint to set HVAC mode"""
    if not control_callback:
        return jsonify({'error': 'Control not available'}), 503
    
    try:
        data = request.json
        mode = data.get('mode')  # 'heat', 'cool', 'auto', 'off'
        
        # Validate mode
        if mode not in ['heat', 'cool', 'auto', 'off']:
            return jsonify({'error': 'Invalid mode'}), 400
        
        # Send control command
        result = control_callback('set_mode', {'mode': mode})
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/control/fan', methods=['POST'])
def api_control_fan():
    """API endpoint to control fan"""
    if not control_callback:
        return jsonify({'error': 'Control not available'}), 503
    
    try:
        data = request.json
        fan_on = data.get('fan_on', False)
        
        # Send control command
        result = control_callback('set_fan', {'fan_on': fan_on})
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/control/units', methods=['POST'])
def api_control_units():
    """API endpoint to set temperature display units"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        units = data.get('units', 'F').upper()
        
        # Validate units
        if units not in ['F', 'C', 'K']:
            return jsonify({'error': 'Invalid units (must be F, C, or K)'}), 400
        
        # Load current settings
        settings = database.load_settings()
        if not settings:
            return jsonify({'error': 'No settings found'}), 500
        
        # Update temperature units
        database.save_settings(
            target_temp_heat=settings['target_temp_heat'],
            target_temp_cool=settings['target_temp_cool'],
            hvac_mode=settings['hvac_mode'],
            fan_mode=settings.get('fan_mode', 'auto'),
            temperature_units=units
        )
        
        # Log the change
        database.log_setting_change('temperature_units', 
                                   settings.get('temperature_units', 'F'), 
                                   units, 'web_interface')
        
        return jsonify({
            'success': True, 
            'message': f'Temperature units set to {get_unit_symbol(units)}',
            'units': units
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SCHEDULE ENDPOINTS ====================

@app.route('/api/schedules', methods=['GET'])
def api_get_schedules():
    """Get all schedules"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        schedules = database.get_schedules()
        units = get_temperature_units()
        
        # Convert temperatures in schedules
        for schedule in schedules:
            if schedule.get('target_temp_heat') is not None:
                schedule['target_temp_heat'] = convert_temperature(
                    schedule['target_temp_heat'], 'C', units
                )
            if schedule.get('target_temp_cool') is not None:
                schedule['target_temp_cool'] = convert_temperature(
                    schedule['target_temp_cool'], 'C', units
                )
        
        return jsonify({
            'schedules': schedules,
            'temperature_units': units,
            'temperature_symbol': get_unit_symbol(units)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedules', methods=['POST'])
def api_create_schedule():
    """Create a new schedule"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        units = get_temperature_units()
        
        # Convert temperatures from user units to Celsius for storage
        target_temp_heat = data.get('target_temp_heat')
        target_temp_cool = data.get('target_temp_cool')
        
        if target_temp_heat is not None:
            target_temp_heat = convert_temperature(target_temp_heat, units, 'C')
        if target_temp_cool is not None:
            target_temp_cool = convert_temperature(target_temp_cool, units, 'C')
        
        schedule_id = database.create_schedule(
            name=data['name'],
            days_of_week=data['days_of_week'],
            time_str=data['time'],
            target_temp_heat=target_temp_heat,
            target_temp_cool=target_temp_cool,
            hvac_mode=data.get('hvac_mode')
        )
        return jsonify({'success': True, 'schedule_id': schedule_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
def api_update_schedule(schedule_id):
    """Update a schedule"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        units = get_temperature_units()
        
        # Convert temperatures from user units to Celsius if provided
        if 'target_temp_heat' in data and data['target_temp_heat'] is not None:
            data['target_temp_heat'] = convert_temperature(data['target_temp_heat'], units, 'C')
        if 'target_temp_cool' in data and data['target_temp_cool'] is not None:
            data['target_temp_cool'] = convert_temperature(data['target_temp_cool'], units, 'C')
        
        database.update_schedule(schedule_id, **data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def api_delete_schedule(schedule_id):
    """Delete a schedule"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        database.delete_schedule(schedule_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/schedules/control', methods=['POST'])
def api_schedule_control():
    """Control schedule system (enable/disable/resume)"""
    if not control_callback:
        return jsonify({'error': 'Control not available'}), 503
    
    data = request.json
    action = data.get('action')
    
    if action == 'enable':
        result = control_callback('set_schedule_enabled', {'enabled': True})
    elif action == 'disable':
        result = control_callback('set_schedule_enabled', {'enabled': False})
    elif action == 'resume':
        result = control_callback('resume_schedules', {})
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    return jsonify(result)


# ==================== HISTORY ENDPOINTS ====================

@app.route('/api/history/sensors', methods=['GET'])
def api_sensor_history():
    """Get sensor reading history"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        sensor_id = request.args.get('sensor_id')
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 1000))
        units = get_temperature_units()
        
        history = database.get_sensor_history(sensor_id=sensor_id, hours=hours, limit=limit)
        
        # Convert temperatures in history
        for entry in history:
            if 'temperature' in entry and entry['temperature'] is not None:
                entry['temperature'] = convert_temperature(entry['temperature'], 'C', units)
        
        return jsonify({
            'history': history,
            'temperature_units': units,
            'temperature_symbol': get_unit_symbol(units)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/hvac', methods=['GET'])
def api_hvac_history():
    """Get HVAC history"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 1000))
        units = get_temperature_units()
        
        history = database.get_hvac_history(hours=hours, limit=limit)
        
        # Convert temperatures in history
        for entry in history:
            if 'system_temp' in entry and entry['system_temp'] is not None:
                entry['system_temp'] = convert_temperature(entry['system_temp'], 'C', units)
            if 'target_temp' in entry and entry['target_temp'] is not None:
                entry['target_temp'] = convert_temperature(entry['target_temp'], 'C', units)
        
        return jsonify({
            'history': history,
            'temperature_units': units,
            'temperature_symbol': get_unit_symbol(units)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/settings', methods=['GET'])
def api_settings_history():
    """Get setting change history"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = int(request.args.get('limit', 100))
        
        history = database.get_setting_history(limit=limit)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensors/config', methods=['GET'])
def api_get_sensor_configs():
    """Get all sensor configurations from database"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        sensors = database.get_sensors(enabled_only=False)
        return jsonify({'sensors': sensors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensors/config/<sensor_id>', methods=['PUT'])
def api_update_sensor_config(sensor_id):
    """Update sensor configuration"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        name = data.get('name')
        enabled = data.get('enabled')
        # Automatically set monitored to match enabled state (all enabled sensors are monitored)
        monitored = enabled if enabled is not None else data.get('monitored')
        
        if not database.update_sensor(sensor_id, name=name, enabled=enabled, monitored=monitored):
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Notify controller to reload sensors
        if control_callback:
            control_callback('reload_sensors', {})
        
        return jsonify({'success': True, 'sensor_id': sensor_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensors/config/<sensor_id>', methods=['DELETE'])
def api_delete_sensor_config(sensor_id):
    """Delete sensor configuration"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        if not database.delete_sensor(sensor_id):
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Notify controller to reload sensors
        if control_callback:
            control_callback('reload_sensors', {})
        
        return jsonify({'success': True, 'sensor_id': sensor_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
def api_database_stats():
    """Get database statistics"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        stats = database.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """Run Flask web server in background thread"""
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def start_web_interface(host='0.0.0.0', port=5000):
    """Start web interface in background thread"""
    thread = Thread(target=run_web_server, args=(host, port, False), daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    # Test mode with mock data and mock control callback
    current_state = {
        'system_temp': 72.5,
        'target_temp_heat': 68.0,
        'target_temp_cool': 74.0,
        'hvac_state': {'heat': True, 'cool': False, 'fan': True, 'heat2': False},
        'sensor_readings': [
            {'id': 's1', 'name': 'Living Room', 'temperature': 72.0, 'timestamp': datetime.now().isoformat()},
            {'id': 's2', 'name': 'Bedroom', 'temperature': 73.0, 'timestamp': datetime.now().isoformat()},
        ],
        'compromised_sensors': [],
        'last_update': datetime.now().isoformat(),
        'hvac_mode': 'heat',
        'schedule_enabled': True,
        'schedule_on_hold': False
    }
    
    # Mock control callback for demo mode
    def mock_control_callback(command: str, params: Dict) -> Dict:
        """Mock control callback that updates demo state"""
        print(f"[DEMO] Control command: {command} with params: {params}")
        
        with state_lock:
            if command == 'set_temperature':
                if params.get('type') == 'heat':
                    current_state['target_temp_heat'] = params.get('temperature')
                elif params.get('type') == 'cool':
                    current_state['target_temp_cool'] = params.get('temperature')
            
            elif command == 'set_mode':
                current_state['hvac_mode'] = params.get('mode')
                # Simulate HVAC state changes
                mode = params.get('mode')
                if mode == 'off':
                    current_state['hvac_state'] = {'heat': False, 'cool': False, 'fan': False, 'heat2': False}
                elif mode == 'heat':
                    current_state['hvac_state'] = {'heat': True, 'cool': False, 'fan': True, 'heat2': False}
                elif mode == 'cool':
                    current_state['hvac_state'] = {'heat': False, 'cool': True, 'fan': True, 'heat2': False}
            
            elif command == 'set_fan':
                current_state['hvac_state']['fan'] = params.get('fan_on', False)
            
            elif command == 'resume_schedules':
                current_state['schedule_on_hold'] = False
                print("[DEMO] Schedules resumed")
            
            elif command == 'set_schedule_enabled':
                current_state['schedule_enabled'] = params.get('enabled', True)
                if not current_state['schedule_enabled']:
                    current_state['schedule_on_hold'] = False
                print(f"[DEMO] Schedules {'enabled' if current_state['schedule_enabled'] else 'disabled'}")
            
            current_state['last_update'] = datetime.now().isoformat()
        
        return {'success': True, 'message': 'Demo mode - control simulated'}
    
    # Set the mock callback
    set_control_callback(mock_control_callback)
    
    print("Starting web interface on http://0.0.0.0:5000")
    print("Access from any device: http://<raspberry-pi-ip>:5000")
    print("\n[DEMO MODE] Controls are simulated - no real hardware will be affected")
    app.run(host='0.0.0.0', port=5000, debug=True)
