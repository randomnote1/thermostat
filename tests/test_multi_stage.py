#!/usr/bin/env python3
"""
Test script for multi-stage HVAC functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import ThermostatDatabase
import tempfile

def test_hvac_stages():
    """Test HVAC stage database operations"""
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    print(f"Creating test database: {db_path}\n")
    
    try:
        db = ThermostatDatabase(db_path)
        
        # Test 1: Check default stages were created
        print("=" * 60)
        print("TEST 1: Check default stages")
        print("=" * 60)
        
        heat_stages = db.get_hvac_stages(stage_type='heat')
        cool_stages = db.get_hvac_stages(stage_type='cool')
        
        print(f"\nHeating Stages: {len(heat_stages)}")
        for stage in heat_stages:
            print(f"  Stage {stage['stage_number']}: GPIO {stage['gpio_pin']}, "
                  f"offset {stage['temp_offset']}°C, "
                  f"min_run={stage['min_run_time']}s - {stage['description']}")
        
        print(f"\nCooling Stages: {len(cool_stages)}")
        for stage in cool_stages:
            print(f"  Stage {stage['stage_number']}: GPIO {stage['gpio_pin']}, "
                  f"offset {stage['temp_offset']}°C, "
                  f"min_run={stage['min_run_time']}s - {stage['description']}")
        
        assert len(heat_stages) == 2, "Should have 2 default heating stages"
        assert len(cool_stages) == 1, "Should have 1 default cooling stage"
        print("\n✓ Default stages created correctly")
        
        # Test 2: Add a new stage
        print("\n" + "=" * 60)
        print("TEST 2: Add a third heating stage")
        print("=" * 60)
        
        stage_id = db.add_hvac_stage(
            stage_type='heat',
            stage_number=3,
            gpio_pin=24,
            temp_offset=2.78,  # ~5°F
            min_run_time=300,
            enabled=True,
            description='Emergency heat'
        )
        
        print(f"\nAdded stage with ID: {stage_id}")
        
        heat_stages = db.get_hvac_stages(stage_type='heat')
        print(f"Total heating stages: {len(heat_stages)}")
        for stage in heat_stages:
            print(f"  Stage {stage['stage_number']}: {stage['description']}")
        
        assert len(heat_stages) == 3, "Should now have 3 heating stages"
        print("\n✓ Successfully added new stage")
        
        # Test 3: Update a stage
        print("\n" + "=" * 60)
        print("TEST 3: Update stage configuration")
        print("=" * 60)
        
        success = db.update_hvac_stage(
            stage_id=stage_id,
            temp_offset=3.33,  # Change from 5°F to 6°F
            description='Emergency heat (updated)'
        )
        
        print(f"\nUpdate successful: {success}")
        
        heat_stages = db.get_hvac_stages(stage_type='heat')
        stage_3 = next((s for s in heat_stages if s['stage_number'] == 3), None)
        print(f"Stage 3 temp_offset: {stage_3['temp_offset']}")
        print(f"Stage 3 description: {stage_3['description']}")
        
        assert stage_3['temp_offset'] == 3.33, "Temp offset should be updated"
        print("\n✓ Successfully updated stage")
        
        # Test 4: Disable a stage
        print("\n" + "=" * 60)
        print("TEST 4: Disable a stage")
        print("=" * 60)
        
        db.update_hvac_stage(stage_id=stage_id, enabled=0)
        
        enabled_stages = db.get_hvac_stages(stage_type='heat', enabled_only=True)
        all_stages = db.get_hvac_stages(stage_type='heat', enabled_only=False)
        
        print(f"\nEnabled heating stages: {len(enabled_stages)}")
        print(f"Total heating stages: {len(all_stages)}")
        
        assert len(enabled_stages) == 2, "Should have 2 enabled stages"
        assert len(all_stages) == 3, "Should still have 3 total stages"
        print("\n✓ Successfully disabled stage")
        
        # Test 5: Delete a stage
        print("\n" + "=" * 60)
        print("TEST 5: Delete a stage")
        print("=" * 60)
        
        success = db.delete_hvac_stage(stage_id)
        print(f"\nDelete successful: {success}")
        
        heat_stages = db.get_hvac_stages(stage_type='heat', enabled_only=False)
        print(f"Remaining heating stages: {len(heat_stages)}")
        
        assert len(heat_stages) == 2, "Should be back to 2 heating stages"
        print("\n✓ Successfully deleted stage")
        
        # Test 6: Add a second cooling stage
        print("\n" + "=" * 60)
        print("TEST 6: Add second cooling stage")
        print("=" * 60)
        
        db.add_hvac_stage(
            stage_type='cool',
            stage_number=2,
            gpio_pin=16,
            temp_offset=1.67,  # ~3°F
            min_run_time=300,
            enabled=True,
            description='High-speed cooling'
        )
        
        cool_stages = db.get_hvac_stages(stage_type='cool')
        print(f"\nTotal cooling stages: {len(cool_stages)}")
        for stage in cool_stages:
            print(f"  Stage {stage['stage_number']}: {stage['description']}")
        
        assert len(cool_stages) == 2, "Should have 2 cooling stages"
        print("\n✓ Successfully added cooling stage")
        
        # Test 7: Test HVAC history with active stages
        print("\n" + "=" * 60)
        print("TEST 7: Log HVAC history with active stages")
        print("=" * 60)
        
        active_stages = [
            {'type': 'heat', 'number': 1, 'gpio_pin': 17},
            {'type': 'heat', 'number': 2, 'gpio_pin': 23}
        ]
        
        db.log_hvac_state(
            system_temp=18.0,
            target_temp_heat=20.0,
            target_temp_cool=24.0,
            hvac_mode='heat',
            fan_mode='auto',
            heat=True,
            cool=False,
            fan=True,
            heat2=True,
            active_stages=active_stages
        )
        
        print("\nLogged HVAC state with active stages")
        
        history = db.get_hvac_history(hours=1, limit=1)
        if history:
            latest = history[0]
            print(f"Latest history entry:")
            print(f"  System temp: {latest['system_temp']}°C")
            print(f"  Active stages: {latest['active_stages']}")
            
            assert latest['active_stages'] is not None, "Should have active_stages data"
            print("\n✓ Successfully logged with active stages")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    finally:
        # Cleanup
        import os
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\nCleaned up test database: {db_path}")

if __name__ == '__main__':
    test_hvac_stages()
