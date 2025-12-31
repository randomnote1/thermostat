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


@app.route('/api/status')
def api_status():
    """API endpoint for current status"""
    state = get_state()
    return jsonify(state)


@app.route('/api/sensors')
def api_sensors():
    """API endpoint for sensor details"""
    state = get_state()
    sensors = []
    
    for reading in state.get('sensor_readings', []):
        sensors.append({
            'id': reading.get('id'),
            'name': reading.get('name'),
            'temperature': reading.get('temperature'),
            'timestamp': reading.get('timestamp'),
            'compromised': reading.get('id') in state.get('compromised_sensors', [])
        })
    
    return jsonify({'sensors': sensors})


@app.route('/api/hvac')
def api_hvac():
    """API endpoint for HVAC status"""
    state = get_state()
    return jsonify({
        'mode': state.get('hvac_mode'),
        'state': state.get('hvac_state'),
        'target_heat': state.get('target_temp_heat'),
        'target_cool': state.get('target_temp_cool'),
        'system_temp': state.get('system_temp')
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
        
        # Validate temperature range
        if temperature < 50 or temperature > 90:
            return jsonify({'error': 'Temperature out of range (50-90°F)'}), 400
        
        # Send control command
        result = control_callback('set_temperature', {
            'type': temp_type,
            'temperature': temperature
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


# ==================== SCHEDULE ENDPOINTS ====================

@app.route('/api/schedules', methods=['GET'])
def api_get_schedules():
    """Get all schedules"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        schedules = database.get_schedules()
        return jsonify({'schedules': schedules})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedules', methods=['POST'])
def api_create_schedule():
    """Create a new schedule"""
    if not database:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        schedule_id = database.create_schedule(
            name=data['name'],
            days_of_week=data['days_of_week'],
            time_str=data['time'],
            target_temp_heat=data.get('target_temp_heat'),
            target_temp_cool=data.get('target_temp_cool'),
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
        
        history = database.get_sensor_history(sensor_id=sensor_id, hours=hours, limit=limit)
        return jsonify({'history': history})
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
        
        history = database.get_hvac_history(hours=hours, limit=limit)
        return jsonify({'history': history})
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
