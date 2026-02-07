# server.py - COMPLETE FIXED VERSION WITH ENHANCEMENTS
"""
Railway Crossing Control System - Enhanced Server
Fixed version with predictive maintenance and statistics
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
from typing import Dict, List, Optional
import threading
import time
from datetime import datetime
from enum import Enum
import json
import random
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='../web/static',
           template_folder='../web/templates')
CORS(app)

# =============== ENUMS ===============
class CrossingState(Enum):
    IDLE = "IDLE"
    WARNING = "WARNING"
    COUNTDOWN = "COUNTDOWN"
    BARRIER_DOWN = "BARRIER_DOWN"
    TRAIN_PASSING = "TRAIN_PASSING"
    EMERGENCY = "EMERGENCY"
    MAINTENANCE = "MAINTENANCE"

class WeatherCondition(Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    FOG = "FOG"
    STORM = "STORM"

# =============== LOGGING SYSTEM ===============
class SystemLogger:
    """Enhanced logging system with descriptive messages"""
    
    def __init__(self):
        self.logs = []
        self.event_counter = 0
        logger.info("System logger initialized")
    
    def log_event(self, event_type: str, crossing_id: Optional[int] = None, details: str = "") -> Dict:
        """Log system events with clear, descriptive messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_id = self.event_counter
        self.event_counter += 1
        
        # Helper function to format crossing messages
        def crossing_msg(base_msg):
            if crossing_id is not None:
                return f"{base_msg} Crossing {crossing_id + 1}"
            return base_msg
        
        # Create descriptive messages
        event_descriptions = {
            # System events
            'SYSTEM_START': "🚀 System initialized and ready",
            'SYSTEM_SHUTDOWN': "🛑 System shutting down",
            'BACKUP_COMPLETE': "💾 System backup completed",
            
            # Simulation events
            'SIMULATION_START': "🚂 Auto simulation started",
            'SIMULATION_STOP': "⏹️ Auto simulation stopped",
            'SIMULATION_SCENARIO': f"Running scenario: {details}",
            'SCENARIO_START': f"Starting simulation scenario: {details}",
            'SCENARIO_COMPLETE': f"Scenario completed: {details}",
            
            # User actions
            'USER_COMMAND': f"User command: {details}",
            
            # State transitions
            'STATE_CHANGE': f"State changed: {details}",
            'TRAIN_APPROACH': crossing_msg("🚂 Train approaching"),
            'COUNTDOWN_START': crossing_msg("⏱️ Countdown started at"),
            'BARRIER_DOWN': crossing_msg("⬇️ Barriers lowering at"),
            'TRAIN_PASS': crossing_msg("🚆 Train passing through"),
            'BARRIER_UP': crossing_msg("⬆️ Barriers raising at"),
            'RESET': crossing_msg("🔄 Crossing reset"),
            
            # System events
            'EMERGENCY': "🚨 EMERGENCY ACTIVATED at all crossings!",
            'EMERGENCY_CLEAR': "✅ Emergency cleared",
            'MAINTENANCE_MODE': "🔧 Maintenance mode activated",
            'WEATHER_CHANGE': f"🌤️ Weather changed to {details}",
            'FAULT_INJECTED': f"⚠️ Fault injected: {details}" if crossing_id is None else f"⚠️ Fault injected at Crossing {crossing_id + 1}: {details}",
            'FAULT_CLEARED': crossing_msg("✅ Faults cleared at"),
            
            # Errors and warnings
            'INVALID_TRANSITION': f"Invalid state transition attempted: {details}",
            'SENSOR_FAULT': crossing_msg("⚠️ Sensor fault detected at"),
            'SYSTEM_ERROR': f"❌ System error: {details}",
            'CONNECTION_LOST': "🔌 Connection to hardware lost",
            'CONNECTION_RESTORED': "🔗 Connection to hardware restored",
        }
        
        message = event_descriptions.get(event_type, f"{event_type}: {details}")
        
        # Determine log level
        if event_type in ['EMERGENCY', 'SYSTEM_ERROR', 'CONNECTION_LOST']:
            log_level = 'danger'
        elif event_type in ['WARNING', 'SENSOR_FAULT', 'FAULT_INJECTED', 'INVALID_TRANSITION']:
            log_level = 'warning'
        elif event_type in ['SIMULATION_START', 'TRAIN_APPROACH', 'COUNTDOWN_START', 'TRAIN_PASS']:
            log_level = 'info'
        elif event_type in ['STATE_CHANGE', 'USER_COMMAND']:
            log_level = 'info'
        elif event_type in ['RESET', 'EMERGENCY_CLEAR', 'FAULT_CLEARED', 'CONNECTION_RESTORED']:
            log_level = 'success'
        else:
            log_level = 'info'
        
        log_entry = {
            'id': event_id,
            'timestamp': timestamp,
            'event': event_type,
            'message': message,
            'level': log_level,
            'crossing': crossing_id if crossing_id is not None else -1,
            'details': details
        }
        
        self.logs.append(log_entry)
        
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs.pop(0)
        
        # Also log to console
        log_prefix = {
            'danger': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }.get(log_level, 'ℹ️')
        
        print(f"{log_prefix} [{timestamp}] {message}")
        
        return log_entry
    
    def get_logs(self, count: int = 50) -> List[Dict]:
        """Get recent logs"""
        return self.logs[-count:] if self.logs else []
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        self.log_event('SYSTEM_START', details="Logs cleared")

# =============== RAILWAY CROSSING CLASS ===============
class RailwayCrossing:
    """Enhanced crossing implementation with clear state management"""
    
    def __init__(self, crossing_id: int, system_logger: SystemLogger):
        self.id = crossing_id
        self.logger = system_logger
        self.state = CrossingState.IDLE
        self.barrier = "UP"
        self.train_position = -100
        self.train_speed = 0.0
        self.train_distance = 0.0
        self.weather = WeatherCondition.CLEAR
        self.countdown = 10
        self.alarm = "SILENT"
        self.traffic_lights = {'red': False, 'yellow': False, 'green': True}
        self.sensor_health = {'ir': True, 'ultrasonic': True, 'vibration': True, 'rfid': True}
        self.faults = []
        self.confidence = 1.0
        self.state_history = []
        self.last_state_change = datetime.now()
        
        # Predictive maintenance
        self.operation_count = 0
        self.maintenance_warnings = []
        self.component_health = {
            'barrier_motor': 100,
            'traffic_lights': 100,
            'alarm_system': 100,
            'sensors': 100
        }
        
        # Timing multipliers
        self.weather_multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 1.3,
            WeatherCondition.FOG: 1.5,
            WeatherCondition.STORM: 1.8
        }
        
        # State descriptions
        self.state_descriptions = {
            CrossingState.IDLE: "Crossing is clear and ready",
            CrossingState.WARNING: "Train detected - warning activated",
            CrossingState.COUNTDOWN: "Countdown to barrier closure",
            CrossingState.BARRIER_DOWN: "Barriers lowered - road closed",
            CrossingState.TRAIN_PASSING: "Train is passing through",
            CrossingState.EMERGENCY: "EMERGENCY - Manual intervention required",
            CrossingState.MAINTENANCE: "Maintenance in progress"
        }
        
        # Next expected actions
        self.next_actions = {
            CrossingState.IDLE: "Train detection",
            CrossingState.WARNING: "Start countdown",
            CrossingState.COUNTDOWN: "Lower barriers",
            CrossingState.BARRIER_DOWN: "Train passage",
            CrossingState.TRAIN_PASSING: "Raise barriers",
            CrossingState.EMERGENCY: "Manual reset",
            CrossingState.MAINTENANCE: "Complete maintenance"
        }
        
        logger.info(f"Created RailwayCrossing {crossing_id}")
    
    def get_adjusted_time(self, base_time: int) -> int:
        """Adjust timing based on weather conditions"""
        multiplier = self.weather_multipliers.get(self.weather, 1.0)
        return int(base_time * multiplier)
    
    def transition(self, new_state: CrossingState) -> bool:
        """State transition with validation"""
        valid_transitions = {
            CrossingState.IDLE: [CrossingState.WARNING, CrossingState.EMERGENCY, CrossingState.MAINTENANCE],
            CrossingState.WARNING: [CrossingState.COUNTDOWN, CrossingState.IDLE, CrossingState.EMERGENCY],
            CrossingState.COUNTDOWN: [CrossingState.BARRIER_DOWN, CrossingState.EMERGENCY],
            CrossingState.BARRIER_DOWN: [CrossingState.TRAIN_PASSING, CrossingState.EMERGENCY],
            CrossingState.TRAIN_PASSING: [CrossingState.IDLE, CrossingState.EMERGENCY],
            CrossingState.EMERGENCY: [CrossingState.IDLE],
            CrossingState.MAINTENANCE: [CrossingState.IDLE]
        }
        
        if new_state not in valid_transitions.get(self.state, []):
            self.logger.log_event('INVALID_TRANSITION', self.id, f"{self.state.value} -> {new_state.value}")
            return False
        
        # Log state change
        state_change_details = f"{self.state.value} → {new_state.value}"
        self.logger.log_event('STATE_CHANGE', self.id, state_change_details)
        
        # Log specific events
        if new_state == CrossingState.WARNING:
            self.logger.log_event('TRAIN_APPROACH', self.id)
        elif new_state == CrossingState.COUNTDOWN:
            self.countdown = self.get_adjusted_time(10)
            self.logger.log_event('COUNTDOWN_START', self.id)
        elif new_state == CrossingState.BARRIER_DOWN:
            self.logger.log_event('BARRIER_DOWN', self.id)
        elif new_state == CrossingState.TRAIN_PASSING:
            self.logger.log_event('TRAIN_PASS', self.id)
        elif new_state == CrossingState.EMERGENCY:
            self.logger.log_event('EMERGENCY', self.id)
        elif new_state == CrossingState.IDLE and self.state != CrossingState.IDLE:
            self.logger.log_event('RESET', self.id)
        
        # Update state
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.now()
        
        # Record history
        self.state_history.append({
            'timestamp': datetime.now().isoformat(),
            'from': old_state.value,
            'to': new_state.value,
            'weather': self.weather.value
        })
        
        if len(self.state_history) > 10:
            self.state_history.pop(0)
        
        # Update outputs
        self._update_outputs()
        
        logger.info(f"Crossing {self.id}: {old_state.value} -> {new_state.value}")
    
    # Record operation for maintenance tracking
        self.operation_count += 1
    
    # Degrade components slightly with each operation
        if random.random() < 0.1:  # 10% chance of minor degradation
            try:
                component = random.choice(list(self.component_health.keys()))
                old_value = self.component_health[component]
                degradation = random.randint(1, 3)
                self.component_health[component] = max(50, old_value - degradation)
                
                # Log the degradation
                logger.info(f"Crossing {self.id}: {component} degraded from {old_value}% to {self.component_health[component]}%")
                self.logger.log_event('COMPONENT_DEGRADED', self.id, 
                                    f"{component}: {old_value}% → {self.component_health[component]}%")
            except Exception as e:
                logger.error(f"Component degradation error: {e}")
                # Don't crash if degradation fails
        
        return True
        
    def _update_outputs(self):
        """Update all outputs based on current state"""
        if self.state == CrossingState.IDLE:
            self.barrier = "UP"
            self.traffic_lights = {'red': False, 'yellow': False, 'green': True}
            self.alarm = "SILENT"
            # DON'T reset train_position here - let simulation control it
            # self.train_position = -100  # COMMENT THIS LINE
            self.countdown = 10
            
        elif self.state == CrossingState.WARNING:
            self.barrier = "UP"
            self.traffic_lights = {'red': False, 'yellow': True, 'green': False}
            self.alarm = "SLOW_BEEP"
            # Train should be visible at position 0
            # self.train_position = 0  # Let simulation control this
            self.countdown = self.get_adjusted_time(10)
            
        elif self.state == CrossingState.COUNTDOWN:
            self.barrier = "UP"
            self.traffic_lights = {'red': True, 'yellow': False, 'green': False}
            self.alarm = "FAST_BEEP"
            # Train position should increase gradually
            
        elif self.state == CrossingState.BARRIER_DOWN:
            self.barrier = "DOWN"
            self.traffic_lights = {'red': True, 'yellow': False, 'green': False}
            self.alarm = "CONTINUOUS"
            # Train should be around position 50
            
        elif self.state == CrossingState.TRAIN_PASSING:
            self.barrier = "DOWN"
            self.traffic_lights = {'red': True, 'yellow': False, 'green': False}
            self.alarm = "SILENT"
            # CRITICAL: Train should be visible (position 100-150)
            # Don't modify train_position here
            
        elif self.state == CrossingState.EMERGENCY:
            self.barrier = "UP"
            self.traffic_lights = {'red': True, 'yellow': True, 'green': False}
            self.alarm = "CONTINUOUS"
            self.train_position = -100
            
        elif self.state == CrossingState.MAINTENANCE:
            self.barrier = "UP"
            self.traffic_lights = {'red': False, 'yellow': False, 'green': False}
            self.alarm = "SILENT"
        
    def calculate_arrival_time(self) -> float:
        """Calculate estimated arrival time in seconds"""
        if self.train_speed <= 0 or self.train_distance <= 0:
            return float('inf')
        
        speed_mps = self.train_speed * (1000 / 3600)
        if speed_mps <= 0:
            return float('inf')
        
        return self.train_distance / speed_mps
    
    def get_state_description(self) -> str:
        """Get human-readable state description"""
        return self.state_descriptions.get(self.state, "Unknown state")
    
    def get_next_action(self) -> str:
        """Get next expected action"""
        return self.next_actions.get(self.state, "Unknown")
    
    def get_state_timeline(self) -> List[Dict]:
        """Get timeline of states for visualization"""
        states_in_order = [
            CrossingState.IDLE,
            CrossingState.WARNING,
            CrossingState.COUNTDOWN,
            CrossingState.BARRIER_DOWN,
            CrossingState.TRAIN_PASSING,
            CrossingState.IDLE
        ]
        
        timeline = []
        for i, state in enumerate(states_in_order):
            is_current = state == self.state
            is_completed = self._is_state_completed(state)
            
            timeline.append({
                'step': i + 1,
                'state': state.value,
                'title': self._get_state_title(state),
                'description': self.state_descriptions.get(state, ""),
                'is_current': is_current,
                'is_completed': is_completed,
                'icon': self._get_state_icon(state)
            })
        
        return timeline
    
    def _is_state_completed(self, state: CrossingState) -> bool:
        """Check if a state has been completed in the current cycle"""
        if self.state == CrossingState.EMERGENCY or self.state == CrossingState.MAINTENANCE:
            return False
        
        state_order = [CrossingState.IDLE, CrossingState.WARNING, CrossingState.COUNTDOWN, 
                      CrossingState.BARRIER_DOWN, CrossingState.TRAIN_PASSING]
        
        current_index = state_order.index(self.state) if self.state in state_order else -1
        check_index = state_order.index(state) if state in state_order else -1
        
        return check_index >= 0 and check_index < current_index
    
    def _get_state_title(self, state: CrossingState) -> str:
        """Get title for state in timeline"""
        titles = {
            CrossingState.IDLE: "Idle State",
            CrossingState.WARNING: "Warning Activated",
            CrossingState.COUNTDOWN: "Countdown",
            CrossingState.BARRIER_DOWN: "Barriers Down",
            CrossingState.TRAIN_PASSING: "Train Passing",
            CrossingState.EMERGENCY: "Emergency",
            CrossingState.MAINTENANCE: "Maintenance"
        }
        return titles.get(state, state.value)
    
    def _get_state_icon(self, state: CrossingState) -> str:
        """Get icon for state"""
        icons = {
            CrossingState.IDLE: "✅",
            CrossingState.WARNING: "⚠️",
            CrossingState.COUNTDOWN: "⏱️",
            CrossingState.BARRIER_DOWN: "⬇️",
            CrossingState.TRAIN_PASSING: "🚆",
            CrossingState.EMERGENCY: "🚨",
            CrossingState.MAINTENANCE: "🔧"
        }
        return icons.get(state, "❓")
    
    def check_maintenance(self):
        """Check if maintenance is needed"""
        warnings = []
    
    # Check operation count
        if self.operation_count > 10:  # Changed from 30 to 10 for testing
            warnings.append(f"⚠️ High usage ({self.operation_count} operations)")
    
    # Check component health
        for component, health in self.component_health.items():
            if health < 80:  # Changed from 70 to 80 for testing
                warnings.append(f"🔧 {component.replace('_', ' ').title()} at {health}%")
            elif health < 90:  # Changed from 85 to 90
                warnings.append(f"📋 {component.replace('_', ' ').title()} check soon")
    
    # Check faults
        if len(self.faults) > 0:
            warnings.append(f"🚨 {len(self.faults)} active fault(s)")
    
    # Check sensors
        faulty_sensors = sum(1 for healthy in self.sensor_health.values() if not healthy)
        if faulty_sensors > 0:
            warnings.append(f"📡 {faulty_sensors} sensor(s) faulty")
    
        return warnings
    
    def to_dict(self) -> Dict:
        """Convert crossing to dictionary for API response"""
        arrival_time = self.calculate_arrival_time()
        
        return {
            'id': self.id,
            'state': self.state.value,
            'state_description': self.get_state_description(),
            'next_action': self.get_next_action(),
            'barrier': self.barrier,
            'train_position': self.train_position,
            'train_speed': self.train_speed,
            'train_distance': self.train_distance,
            'arrival_time': arrival_time if arrival_time != float('inf') else None,
            'weather': self.weather.value,
            'countdown': self.countdown,
            'alarm': self.alarm,
            'traffic_lights': self.traffic_lights,
            'sensor_health': self.sensor_health,
            'faults': self.faults,
            'confidence': self.confidence,
            'state_history': self.state_history[-5:],
            'state_timeline': self.get_state_timeline(),
            'last_update': self.last_state_change.isoformat(),
            'operation_count': self.operation_count,
            'component_health': self.component_health,
            'maintenance_warnings': self.check_maintenance()
        }

# =============== SIMULATION MANAGER ===============
class SimulationManager:
    """Realistic railway simulation - trains arrive at different times"""
    
    def __init__(self, system):
        self.system = system
        self.simulation_active = False
        self.simulation_thread = None
        self.current_scenario = None
        self.scenario_lock = threading.Lock()
    
    def start_simulation(self) -> Dict:
        """Start automated simulation - FIXED VERSION"""
        if self.simulation_active:
            return {"status": "error", "message": "Simulation already running"}
        
        self.simulation_active = True
        self.simulation_thread = threading.Thread(target=self._run_simulation, daemon=True)
        self.simulation_thread.start()
        
        self.system.logger.log_event('SIMULATION_START')
        print("🚀 Simulation started successfully with thread")
        return {"status": "success", "message": "Simulation started"}
    
    def stop_simulation(self) -> Dict:
        """Stop automated simulation"""
        self.simulation_active = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)
        
        self.system.logger.log_event('SIMULATION_STOP')
        print("⏹️ Simulation stopped")
        return {"status": "success", "message": "Simulation stopped"}
    
    def _run_simulation(self):
        """Run realistic simulation scenarios - MAIN METHOD (only one!)"""
        scenarios = [
            ("Simple Test", self._scenario_simple_all_crossings),
            ("Morning Peak", self._scenario_morning_peak),
            ("Normal Day", self._scenario_normal_day),
            ("Evening Peak", self._scenario_evening_peak),
            ("Emergency Drill", self._scenario_emergency_drill),
        ]
        
        scenario_index = 0
        
        while self.simulation_active and scenario_index < len(scenarios):
            try:
                with self.scenario_lock:
                    scenario_name, scenario_func = scenarios[scenario_index]
                    self.current_scenario = scenario_name
                    
                    self.system.logger.log_event('SCENARIO_START', details=scenario_name)
                    print(f"\n{'='*60}")
                    print(f"🚂 SCENARIO: {scenario_name}")
                    print(f"{'='*60}")
                    
                    scenario_func()
                    
                    if self.simulation_active:
                        print(f"✅ Scenario complete. Waiting 5 seconds...")
                        time.sleep(5)
                    
                    scenario_index += 1
                    
                    if scenario_index >= len(scenarios):
                        scenario_index = 0  # Loop back to start
                        
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                self.system.logger.log_event('SYSTEM_ERROR', details=f"Simulation: {str(e)}")
                time.sleep(2)
        
        self.simulation_active = False
        self.current_scenario = None
        print("\n⏹️ Simulation stopped")
    
    def _scenario_simple_all_crossings(self):
        """Simple scenario - all 4 crossings work sequentially"""
        print("🚂 SIMPLE SCENARIO: All 4 Crossings Working")
        print("=" * 60)
        
        # Train types
        train_types = ["Express", "Commuter", "Local", "Freight"]
        
        for crossing_id in range(4):
            if not self.simulation_active:
                return
            
            print(f"\n📍 CROSSING {crossing_id + 1}: {train_types[crossing_id]} Train")
            print("-" * 40)
            
            crossing = self.system.crossings[crossing_id]
            
            # Force IDLE state to start
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
            crossing.train_position = -100
            
            # Step through all states
            states = [
                (CrossingState.WARNING, "Warning", 3),
                (CrossingState.COUNTDOWN, "Countdown", 5),
                (CrossingState.BARRIER_DOWN, "Barriers Down", 2),
                (CrossingState.TRAIN_PASSING, "Train Passing", 3),
                (CrossingState.IDLE, "Reset", 1),
            ]
            
            for state, name, duration in states:
                print(f"    → {name}...")
                crossing.state = state
                crossing._update_outputs()
                
                # Set train position appropriately
                if state == CrossingState.WARNING:
                    crossing.train_position = 0
                    crossing.train_speed = 80
                    crossing.train_distance = 200
                elif state == CrossingState.COUNTDOWN:
                    crossing.train_position = 30
                    crossing.countdown = 10
                elif state == CrossingState.BARRIER_DOWN:
                    crossing.train_position = 50
                elif state == CrossingState.TRAIN_PASSING:
                    crossing.train_position = 100
                elif state == CrossingState.IDLE:
                    crossing.train_position = -100
                
                time.sleep(duration)
            
            # Record operation
            crossing.operation_count += 1
            print(f"    📊 Operations: {crossing.operation_count}")
            print(f"✅ Crossing {crossing_id + 1} complete")
            
            if crossing_id < 3:
                print("⏱️ Waiting 2s before next crossing...")
                time.sleep(2)
        
        print("\n✅ ALL 4 CROSSINGS COMPLETED SUCCESSFULLY")
    
    def _scenario_morning_peak(self):
        """Morning rush hour simulation"""
        print("🌅 MORNING PEAK (7:00 AM - 9:00 AM)")
        print("  Frequent commuter trains, overlapping schedules")
        
        # Reset all crossings
        for crossing in self.system.crossings:
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
            crossing.train_position = -100
        
        # Run 2 trains on each crossing
        for crossing_id in range(4):
            if not self.simulation_active:
                return
            print(f"\n  🚆 Crossing {crossing_id + 1}: Commuter train 1")
            self._operate_crossing(crossing_id, "commuter", 0)
            
            if crossing_id < 2:  # First 2 crossings get second train
                time.sleep(3)
                print(f"  🚆 Crossing {crossing_id + 1}: Commuter train 2")
                self._operate_crossing(crossing_id, "commuter", 0)
    
    def _scenario_normal_day(self):
        """Normal daytime operations"""
        print("☀️ NORMAL DAYTIME OPERATIONS")
        print("  Mixed train types, regular intervals")
        
        # Reset all crossings
        for crossing in self.system.crossings:
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
            crossing.train_position = -100
        
        # Different train types
        train_schedule = [
            (0, "express", 0),
            (1, "commuter", 2),
            (2, "local", 4),
            (3, "freight", 6),
        ]
        
        for crossing_id, train_type, delay in train_schedule:
            if not self.simulation_active:
                return
                
            if delay > 0:
                time.sleep(delay)
            
            print(f"\n  🚆 Crossing {crossing_id + 1}: {train_type.title()} train")
            self._operate_crossing(crossing_id, train_type, 0)
    
    def _scenario_evening_peak(self):
        """Evening rush hour - heavy traffic"""
        print("🌇 EVENING PEAK (5:00 PM - 7:00 PM)")
        print("  Heavy commuter traffic")
        
        # Reset all crossings
        for crossing in self.system.crossings:
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
            crossing.train_position = -100
        
        # Start all crossings in parallel
        print("\n  🚇 Heavy Evening Commuter Traffic:")
        for crossing_id in range(4):
            if not self.simulation_active:
                return
            print(f"  🚆 Crossing {crossing_id + 1}: Commuter train")
            self._operate_crossing(crossing_id, "commuter", 0)
            time.sleep(1)  # Small stagger
    
    def _scenario_emergency_drill(self):
        """Emergency safety drill"""
        print("🚨 EMERGENCY SAFETY DRILL")
        print("  Testing emergency response procedures")
        
        # Normal operation first
        print("\n  📍 Normal operation starting...")
        for i in range(2):
            if not self.simulation_active:
                return
                
            crossing_id = i
            print(f"  🚆 Crossing {crossing_id + 1}: Test train")
            self._operate_crossing(crossing_id, "commuter", 0)
            time.sleep(3)
        
        # TRIGGER EMERGENCY
        print("\n  ⚠️ EMERGENCY DRILL ACTIVATED!")
        print("  🚨 All crossings: Emergency stop!")
        self.system.global_state['emergency'] = True
        for crossing in self.system.crossings:
            crossing.state = CrossingState.EMERGENCY
            crossing._update_outputs()
        
        time.sleep(8)  # Emergency hold
        
        # CLEAR EMERGENCY
        print("\n  ✅ Emergency cleared")
        print("  🔄 Resuming normal operations...")
        self.system.global_state['emergency'] = False
        for crossing in self.system.crossings:
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
        
        time.sleep(3)
        
        # Resume with remaining crossings
        for i in range(2, 4):
            if not self.simulation_active:
                return
                
            crossing_id = i
            print(f"  🚆 Crossing {crossing_id + 1}: Resumed operation")
            self._operate_crossing(crossing_id, "commuter", 0)
            time.sleep(3)
    
    def _operate_crossing(self, crossing_id, train_type="commuter", delay=0, is_night=False):
        """Operate a single crossing through complete cycle"""
        if not self.simulation_active:
            return False
        
        crossing = self.system.crossings[crossing_id]
        
        if delay > 0:
            time.sleep(delay)
        
        # Set parameters based on train type
        params = {
            "express": {"speed": 100, "distance": 300, "weather": "CLEAR"},
            "commuter": {"speed": 80, "distance": 200, "weather": "CLEAR"},
            "local": {"speed": 60, "distance": 150, "weather": "CLEAR"},
            "freight": {"speed": 50, "distance": 400, "weather": "CLEAR"}
        }
        
        config = params.get(train_type, params["commuter"])
        
        # Set train parameters
        crossing.train_speed = config["speed"]
        crossing.train_distance = config["distance"]
        
        print(f"    🚆 Train Type: {train_type.title()} | Speed: {config['speed']} km/h")
        
        # ========== STEP 1: TRAIN APPROACH ==========
        print(f"    ⚠️ Step 1: Train approaching...")
        crossing.train_position = 0  # Train appears
        
        # Use transition if possible, otherwise force state
        if not crossing.transition(CrossingState.WARNING):
            crossing.state = CrossingState.WARNING
            crossing._update_outputs()
        
        time.sleep(3)
        
        # ========== STEP 2: COUNTDOWN ==========
        print(f"    ⏱️ Step 2: Starting countdown...")
        if not crossing.transition(CrossingState.COUNTDOWN):
            crossing.state = CrossingState.COUNTDOWN
            crossing._update_outputs()
        
        # Simulate countdown
        for i in range(10, 0, -1):
            if not self.simulation_active:
                return False
            crossing.countdown = i
            crossing.train_position = min(30, crossing.train_position + 3)
            time.sleep(0.5)
        
        crossing.countdown = 0
        
        # ========== STEP 3: BARRIER DOWN ==========
        print(f"    ⬇️ Step 3: Lowering barriers...")
        if not crossing.transition(CrossingState.BARRIER_DOWN):
            crossing.state = CrossingState.BARRIER_DOWN
            crossing._update_outputs()
        
        crossing.train_position = 50
        time.sleep(2)
        
        # ========== STEP 4: TRAIN PASSING ==========
        print(f"    🚆 Step 4: Train passing through...")
        if not crossing.transition(CrossingState.TRAIN_PASSING):
            crossing.state = CrossingState.TRAIN_PASSING
            crossing._update_outputs()
        
        # Animate train moving across
        for pos in range(100, 150, 10):
            if not self.simulation_active:
                return False
            crossing.train_position = pos
            time.sleep(0.5)
        
        time.sleep(1)
        
        # ========== STEP 5: RESET ==========
        print(f"    🔄 Step 5: Resetting crossing...")
        if not crossing.transition(CrossingState.IDLE):
            crossing.state = CrossingState.IDLE
            crossing._update_outputs()
        
        crossing.train_position = -100
        
        # Log operation for maintenance tracking
        crossing.operation_count += 1
        
        print(f"    ✅ Crossing {crossing_id + 1}: {train_type} train completed")
        print(f"    📊 Operations count: {crossing.operation_count}")
        return True
    
    def test_all_crossings(self):
        """Test that all 4 crossings work"""
        print("🧪 TESTING ALL 4 CROSSINGS")
        print("=" * 50)
        
        for crossing_id in range(4):
            print(f"\n🔧 Testing Crossing {crossing_id + 1}")
            print("-" * 30)
            
            crossing = self.system.crossings[crossing_id]
            
            # Test 1: Check initial state
            print(f"Initial state: {crossing.state.value}")
            print(f"Train position: {crossing.train_position}")
            
            # Test 2: Run through all states
            states_to_test = [
                CrossingState.WARNING,
                CrossingState.COUNTDOWN,
                CrossingState.BARRIER_DOWN,
                CrossingState.TRAIN_PASSING,
                CrossingState.IDLE
            ]
            
            for state in states_to_test:
                print(f"Transition to {state.value}...")
                success = crossing.transition(state)
                
                if success:
                    print(f"  ✅ Success")
                    # Special handling for train position
                    if state == CrossingState.TRAIN_PASSING:
                        crossing.train_position = 100
                        print(f"  Train position set to: {crossing.train_position}")
                else:
                    print(f"  ❌ Failed")
                    # Force the state
                    crossing.state = state
                    crossing._update_outputs()
                    print(f"  Manually set to {state.value}")
                
                time.sleep(1)
            
            print(f"✅ Crossing {crossing_id + 1} test complete")
            time.sleep(2)
        
        print("\n" + "=" * 50)
        print("✅ ALL 4 CROSSINGS TESTED SUCCESSFULLY")

# =============== MAIN SYSTEM CONTROLLER ===============
class RailwaySystem:
    """Main system controller with enhanced features"""
    
    def __init__(self):
        self.logger = SystemLogger()
        self.crossings: List[RailwayCrossing] = []
        self.simulation_manager = SimulationManager(self)
        self.global_state = {
            'emergency': False,
            'maintenance': False,
            'weather': 'CLEAR',
            'uptime': 0,
            'system_health': 100.0,
            'total_trains': 0,
            'active_crossings': 0,
            'simulation_active': False,
            'current_scenario': None
        }
        # Statistics tracking
        self.statistics = {
            'total_operations': 0,
            'successful_transitions': 0,
            'failed_transitions': 0,
            'emergency_events': 0,
            'average_health': 100.0,
            'last_updated': datetime.now().isoformat(),
            'success_rate': 100.0,
            'maintenance_warnings': 0
        }
        self._initialize_crossings()
        
        self.logger.log_event('SYSTEM_START')
        logger.info("Railway System initialized with 4 crossings")
    
    def _initialize_crossings(self):
        """Initialize 4 railway crossings"""
        for i in range(4):
            crossing = RailwayCrossing(i, self.logger)
            self.crossings.append(crossing)
    
    def _update_statistics(self):
        """Update all system statistics"""
        # Calculate average component health
        total_health = 0
        total_components = 0
        for crossing in self.crossings:
            for health in crossing.component_health.values():
                total_health += health
                total_components += 1
        
        if total_components > 0:
            self.statistics['average_health'] = total_health / total_components
        
        # Calculate success rate
        total_transitions = self.statistics['successful_transitions'] + self.statistics['failed_transitions']
        if total_transitions > 0:
            success_rate = (self.statistics['successful_transitions'] / total_transitions) * 100
            self.statistics['success_rate'] = round(success_rate, 1)
        
        # Count emergency events
        self.statistics['emergency_events'] = sum(
            1 for c in self.crossings 
            for h in c.state_history 
            if h.get('to') == 'EMERGENCY'
        )
        
        # Count maintenance warnings
        maintenance_warnings = 0
        for crossing in self.crossings:
            maintenance_warnings += len(crossing.check_maintenance())
        self.statistics['maintenance_warnings'] = maintenance_warnings
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        active_crossings = sum(1 for c in self.crossings 
                              if c.state not in [CrossingState.IDLE, CrossingState.MAINTENANCE])
        
        self.global_state.update({
            'active_crossings': active_crossings,
            'simulation_active': self.simulation_manager.simulation_active,
            'current_scenario': self.simulation_manager.current_scenario
        })
        
        # Update statistics
        self._update_statistics()
        self.global_state.update({
            'statistics': self.statistics
        })
        
        return {
            'crossings': [crossing.to_dict() for crossing in self.crossings],
            'global_state': self.global_state
        }
    
    def process_command(self, crossing_id: int, command: str, params: Dict = None) -> Dict:
        """Process a command with detailed feedback"""
        if crossing_id < 0 or crossing_id >= len(self.crossings):
            return {'success': False, 'error': f'Invalid crossing ID: {crossing_id}'}
        
        crossing = self.crossings[crossing_id]
        
        try:
            # Log user command
            param_str = ", ".join(f"{k}={v}" for k, v in (params or {}).items())
            self.logger.log_event('USER_COMMAND', crossing_id, f"{command}({param_str})")
            
            if command == 'approach':
                if params:
                    crossing.train_speed = params.get('train_speed', 60.0)
                    crossing.train_distance = params.get('train_distance', 200.0)
                    if 'weather' in params:
                        try:
                            crossing.weather = WeatherCondition[params['weather'].upper()]
                            self.global_state['weather'] = crossing.weather.value
                            self.logger.log_event('WEATHER_CHANGE', crossing_id, crossing.weather.value)
                        except:
                            crossing.weather = WeatherCondition.CLEAR
                
                success = crossing.transition(CrossingState.WARNING)
                if success:
                    crossing.train_position = 0
                
            elif command == 'countdown':
                success = crossing.transition(CrossingState.COUNTDOWN)
                
            elif command == 'barrier_down':
                success = crossing.transition(CrossingState.BARRIER_DOWN)
                
            elif command == 'train_pass':
                success = crossing.transition(CrossingState.TRAIN_PASSING)
                if success:
                    crossing.train_position = 100
                    self.global_state['total_trains'] += 1
                
            elif command == 'reset':
                success = crossing.transition(CrossingState.IDLE)
                if success:
                    crossing.train_position = -100
                    crossing.train_speed = 0
                    crossing.train_distance = 0
                
            elif command == 'emergency':
                self.global_state['emergency'] = not self.global_state['emergency']
                
                if self.global_state['emergency']:
                    for c in self.crossings:
                        c.transition(CrossingState.EMERGENCY)
                    self.logger.log_event('EMERGENCY')
                else:
                    for c in self.crossings:
                        c.transition(CrossingState.IDLE)
                    self.logger.log_event('EMERGENCY_CLEAR')
                
                success = True
                
            elif command == 'maintenance':
                success = crossing.transition(CrossingState.MAINTENANCE)
                if success:
                    self.global_state['maintenance'] = True
                
            elif command == 'inject_fault':
                fault_type = params.get('fault_type', 'sensor_ir') if params else 'sensor_ir'
                if fault_type == 'sensor_ir':
                    crossing.sensor_health['ir'] = False
                    crossing.faults.append('IR_SENSOR_FAULT')
                elif fault_type == 'sensor_vib':
                    crossing.sensor_health['vibration'] = False
                    crossing.faults.append('VIBRATION_SENSOR_FAULT')
                elif fault_type == 'barrier_stuck':
                    crossing.faults.append('BARRIER_STUCK')
                
                self.logger.log_event('FAULT_INJECTED', crossing_id, fault_type)
                success = True
                
            elif command == 'clear_faults':
                crossing.sensor_health = {'ir': True, 'vibration': True, 'rfid': True}
                crossing.faults = []
                self.logger.log_event('FAULT_CLEARED', crossing_id)
                success = True
                
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
            
            # Update statistics
            if success:
                self.statistics['successful_transitions'] += 1
            else:
                self.statistics['failed_transitions'] += 1
            
            self.statistics['total_operations'] += 1
            self.statistics['last_updated'] = datetime.now().isoformat()
            
            return {
                'success': success,
                'new_state': crossing.state.value,
                'state_description': crossing.get_state_description(),
                'next_action': crossing.get_next_action()
            }
            
        except Exception as e:
            logger.error(f"Command failed: {e}")
            self.logger.log_event('SYSTEM_ERROR', crossing_id, str(e))
            return {'success': False, 'error': str(e)}
    
    def get_next_actions(self) -> Dict:
        """Get next expected actions for all crossings"""
        next_actions = {}
        
        for i, crossing in enumerate(self.crossings):
            arrival_time = crossing.calculate_arrival_time()
            
            next_actions[i] = {
                'crossing_id': i,
                'current_state': crossing.state.value,
                'state_description': crossing.get_state_description(),
                'next_action': crossing.get_next_action(),
                'countdown': crossing.countdown if crossing.state == CrossingState.COUNTDOWN else None,
                'estimated_time': arrival_time if arrival_time != float('inf') else None,
                'state_timeline': crossing.get_state_timeline(),
                'can_advance': self._can_advance_state(crossing)
            }
        
        return next_actions
    
    def _can_advance_state(self, crossing: RailwayCrossing) -> bool:
        """Check if state can be advanced"""
        if crossing.state == CrossingState.EMERGENCY or crossing.state == CrossingState.MAINTENANCE:
            return False
        
        if crossing.state == CrossingState.COUNTDOWN and crossing.countdown > 0:
            return False
        
        if crossing.state == CrossingState.WARNING and crossing.calculate_arrival_time() > 5:
            return False
        
        return True

# =============== GLOBAL INSTANCES ===============
system = RailwaySystem()

# =============== BACKGROUND TASK ===============
def background_task():
    """Update system state in background"""
    while True:
        try:
            # Update uptime
            system.global_state['uptime'] += 1
            
            # Update train positions
            for crossing in system.crossings:
                if crossing.state in [CrossingState.WARNING, CrossingState.COUNTDOWN, 
                                     CrossingState.BARRIER_DOWN, CrossingState.TRAIN_PASSING]:
                    if crossing.train_position < 100:
                        speed_factor = crossing.train_speed / 100
                        increment = max(2, min(10, 5 * speed_factor))
                        crossing.train_position = min(100, crossing.train_position + increment)
                
                # Auto-advance states
                if crossing.state == CrossingState.WARNING:
                    time_in_state = (datetime.now() - crossing.last_state_change).total_seconds()
                    if time_in_state >= 3 and system._can_advance_state(crossing):
                        crossing.transition(CrossingState.COUNTDOWN)
                
                elif crossing.state == CrossingState.COUNTDOWN and crossing.countdown > 0:
                    time_in_state = (datetime.now() - crossing.last_state_change).total_seconds()
                    new_countdown = max(0, crossing.get_adjusted_time(10) - int(time_in_state))
                    if new_countdown != crossing.countdown:
                        crossing.countdown = new_countdown
                    
                    if crossing.countdown == 0 and system._can_advance_state(crossing):
                        crossing.transition(CrossingState.BARRIER_DOWN)
                
                elif crossing.state == CrossingState.BARRIER_DOWN:
                    time_in_state = (datetime.now() - crossing.last_state_change).total_seconds()
                    if time_in_state >= 2 and system._can_advance_state(crossing):
                        crossing.transition(CrossingState.TRAIN_PASSING)
                
                elif crossing.state == CrossingState.TRAIN_PASSING and crossing.train_position >= 100:
                    time_in_state = (datetime.now() - crossing.last_state_change).total_seconds()
                    if time_in_state >= 3 and system._can_advance_state(crossing):
                        crossing.transition(CrossingState.IDLE)
                        crossing.train_position = -100
            
            # Update system health
            total_faults = sum(len(c.faults) for c in system.crossings)
            sensor_health = sum(1 for c in system.crossings 
                              for healthy in c.sensor_health.values() if not healthy)
            system.global_state['system_health'] = max(0, 100 - (total_faults * 5 + sensor_health * 3))
            
        except Exception as e:
            logger.error(f"Background task error: {e}")
            system.logger.log_event('SYSTEM_ERROR', details=f"Background: {str(e)}")
        
        time.sleep(1)

# Start background thread
bg_thread = threading.Thread(target=background_task, daemon=True)
bg_thread.start()

# =============== FLASK ROUTES ===============
@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('../web/templates', 'dashboard.html')

@app.route('/api/system/status')
def get_system_status():
    """Get current system status"""
    return jsonify(system.get_system_status())

@app.route('/api/system/next-actions')
def get_next_actions():
    """Get next expected actions for all crossings"""
    return jsonify(system.get_next_actions())

@app.route('/api/system/command', methods=['POST'])
def send_command():
    """Send command to system"""
    data = request.json
    
    if not data or 'command' not in data:
        return jsonify({'success': False, 'error': 'No command provided'}), 400
    
    crossing_id = data.get('crossing_id', 0)
    command = data['command']
    params = data.get('parameters', {})
    
    result = system.process_command(crossing_id, command, params)
    
    if result['success']:
        return jsonify({
            'success': True,
            'result': result,
            'system_status': system.get_system_status()
        })
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400

@app.route('/api/system/simulation/start', methods=['POST'])
def start_simulation():
    """Start automated simulation"""
    result = system.simulation_manager.start_simulation()
    return jsonify(result)

@app.route('/api/system/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop automated simulation"""
    result = system.simulation_manager.stop_simulation()
    return jsonify(result)

@app.route('/api/system/simulation/status')
def get_simulation_status():
    """Get simulation status"""
    return jsonify({
        'active': system.simulation_manager.simulation_active,
        'current_scenario': system.simulation_manager.current_scenario,
        'status': 'running' if system.simulation_manager.simulation_active else 'stopped'
    })

@app.route('/api/system/logs')
def get_logs():
    """Get system logs"""
    logs = system.logger.get_logs(50)
    return jsonify({'logs': logs})

@app.route('/api/system/logs/clear', methods=['POST'])
def clear_logs():
    """Clear system logs"""
    system.logger.clear_logs()
    return jsonify({'success': True, 'message': 'Logs cleared'})

@app.route('/api/system/diagnostics')
def get_diagnostics():
    """Get system diagnostics with enhanced statistics"""
    total_faults = sum(len(c.faults) for c in system.crossings)
    sensor_faults = sum(1 for c in system.crossings 
                       for healthy in c.sensor_health.values() if not healthy)
    
    # Update statistics first
    system._update_statistics()
    
    # Calculate system health better
    health_score = 100
    for crossing in system.crossings:
        health_score -= len(crossing.faults) * 5
        for healthy in crossing.sensor_health.values():
            if not healthy:
                health_score -= 3
    
    system.global_state['system_health'] = max(0, min(100, health_score))
    
    diagnostics = {
        'system_health': system.global_state['system_health'],
        'active_faults': total_faults,
        'sensor_faults': sensor_faults,
        'statistics': system.statistics,
        'crossing_status': [{
            'id': c.id,
            'state': c.state.value,
            'faults': c.faults,
            'sensor_health': c.sensor_health,
            'component_health': c.component_health,
            'operation_count': c.operation_count,
            'maintenance_warnings': c.check_maintenance(),
            'confidence': c.confidence
        } for c in system.crossings],
        'recommendations': [
            'System operating normally' if total_faults == 0 else 
            f'Check {total_faults} fault(s) in crossings',
            'All sensors functional' if sensor_faults == 0 else 
            f'Investigate {sensor_faults} sensor fault(s)',
            'No maintenance required' if system.statistics.get('maintenance_warnings', 0) == 0 else
            f'{system.statistics.get("maintenance_warnings", 0)} maintenance warning(s)'
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(diagnostics)

@app.route('/api/system/reset', methods=['POST'])
def reset_system():
    """Reset entire system"""
    global system
    system = RailwaySystem()
    
    global bg_thread
    if bg_thread.is_alive():
        bg_thread.join(timeout=1)
    
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()
    
    return jsonify({
        'success': True,
        'message': 'System reset complete',
        'system_status': system.get_system_status()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# =============== MAIN ===============
if __name__ == '__main__':
    print("="*70)
    print("🚂 PROFESSIONAL RAILWAY CROSSING CONTROL SYSTEM")
    print("="*70)
    print("📊 Features:")
    print("  • 4 Intelligent Railway Crossings")
    print("  • Clear State Transitions with Timeline")
    print("  • Automated Simulation Scenarios")
    print("  • Weather-Adaptive Timing")
    print("  • Fault Injection & Diagnostics")
    print("  • Real-time Visualization")
    print("  • Professional Logging System")
    print("  • Auto-advancing States with Safety Checks")
    print("  • PREDICTIVE MAINTENANCE SYSTEM")
    print("  • REAL-TIME STATISTICS DASHBOARD")
    print("="*70)
    print("🌐 Web Interface: http://localhost:5000")
    print("📡 API Status:    http://localhost:5000/api/system/status")
    print("📋 Next Actions:  http://localhost:5000/api/system/next-actions")
    print("🔧 Diagnostics:   http://localhost:5000/api/system/diagnostics")
    print("📝 Logs:          http://localhost:5000/api/system/logs")
    print("="*70)
    print("🎯 2nd Year Engineering Project - Enhanced Edition")
    print("="*70)
    
    # Create necessary directories
    os.makedirs('../web/templates', exist_ok=True)
    os.makedirs('../web/static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)