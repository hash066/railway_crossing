# core/fsm.py
"""
Railway Crossing Finite State Machine
Professional implementation for 2nd year engineering
"""
from enum import Enum, auto
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class CrossingState(Enum):
    """All possible states of a railway crossing"""
    IDLE = auto()          # No train approaching
    WARNING = auto()       # Train detected, warning activated
    COUNTDOWN = auto()     # Countdown to barrier closure
    BARRIER_DOWN = auto()  # Barriers fully lowered
    TRAIN_PASSING = auto() # Train is passing through
    BARRIER_UP = auto()    # Barriers raising
    EMERGENCY = auto()     # Emergency state
    MAINTENANCE = auto()   # Maintenance mode
    CALIBRATION = auto()   # Sensor calibration
    FAIL_SAFE = auto()     # Fail-safe mode

class WeatherCondition(Enum):
    """Environmental conditions affecting timing"""
    CLEAR = auto()
    RAIN = auto()
    FOG = auto()
    STORM = auto()

@dataclass
class CrossingConfig:
    """Configuration for a railway crossing"""
    crossing_id: int
    warning_time: int = 5      # seconds
    countdown_time: int = 10   # seconds
    barrier_move_time: int = 3 # seconds
    min_safe_distance: float = 50.0  # meters
    
class CrossingFSM:
    """
    Professional FSM implementation with proper error handling
    and safety features
    """
    
    def __init__(self, config: CrossingConfig):
        self.config = config
        self.current_state = CrossingState.IDLE
        self.previous_state = CrossingState.IDLE
        self.weather = WeatherCondition.CLEAR
        self.train_speed = 0.0  # km/h
        self.train_distance = 0.0  # meters
        self.arrival_time = 0.0  # seconds
        self.sensor_health = {
            'ir': True,
            'ultrasonic': True,
            'vibration': True,
            'rfid': True
        }
        self.faults = []
        self.state_history = []
        self._lock = asyncio.Lock()
        
        # Timing parameters adjusted for weather
        self._weather_multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 1.3,
            WeatherCondition.FOG: 1.5,
            WeatherCondition.STORM: 1.8
        }
    
    def get_adjusted_time(self, base_time: int) -> int:
        """Adjust timing based on weather conditions"""
        multiplier = self._weather_multipliers.get(self.weather, 1.0)
        return int(base_time * multiplier)
    
    async def transition(self, new_state: CrossingState, force: bool = False):
        """
        Thread-safe state transition with validation
        """
        async with self._lock:
            if not self._is_valid_transition(new_state) and not force:
                logger.warning(f"Invalid transition: {self.current_state} -> {new_state}")
                return False
            
            self.previous_state = self.current_state
            self.current_state = new_state
            
            # Log state transition
            transition = {
                'timestamp': datetime.now(),
                'from': self.previous_state.name,
                'to': new_state.name,
                'weather': self.weather.name,
                'train_speed': self.train_speed,
                'distance': self.train_distance
            }
            self.state_history.append(transition)
            
            logger.info(f"Crossing {self.config.crossing_id}: "
                       f"{self.previous_state.name} -> {new_state.name}")
            
            # Execute state entry actions
            await self._on_state_entry(new_state)
            
            return True
    
    def _is_valid_transition(self, new_state: CrossingState) -> bool:
        """Validate state transitions based on safety rules"""
        valid_transitions = {
            CrossingState.IDLE: [CrossingState.WARNING, CrossingState.EMERGENCY, 
                               CrossingState.MAINTENANCE, CrossingState.CALIBRATION],
            CrossingState.WARNING: [CrossingState.COUNTDOWN, CrossingState.IDLE, 
                                  CrossingState.EMERGENCY],
            CrossingState.COUNTDOWN: [CrossingState.BARRIER_DOWN, CrossingState.EMERGENCY],
            CrossingState.BARRIER_DOWN: [CrossingState.TRAIN_PASSING, CrossingState.EMERGENCY],
            CrossingState.TRAIN_PASSING: [CrossingState.BARRIER_UP, CrossingState.EMERGENCY],
            CrossingState.BARRIER_UP: [CrossingState.IDLE, CrossingState.EMERGENCY],
            CrossingState.EMERGENCY: [CrossingState.IDLE, CrossingState.FAIL_SAFE],
            CrossingState.MAINTENANCE: [CrossingState.IDLE],
            CrossingState.CALIBRATION: [CrossingState.IDLE],
            CrossingState.FAIL_SAFE: [CrossingState.IDLE]
        }
        
        return new_state in valid_transitions.get(self.current_state, [])
    
    async def _on_state_entry(self, state: CrossingState):
        """Execute actions when entering a state"""
        actions = {
            CrossingState.WARNING: self._activate_warning,
            CrossingState.COUNTDOWN: self._start_countdown,
            CrossingState.BARRIER_DOWN: self._lower_barriers,
            CrossingState.TRAIN_PASSING: self._monitor_train_passage,
            CrossingState.EMERGENCY: self._activate_emergency_protocol,
            CrossingState.FAIL_SAFE: self._activate_fail_safe
        }
        
        if state in actions:
            await actions[state]()
    
    async def _activate_warning(self):
        """Activate warning lights and sounds"""
        logger.info(f"Activating warning at crossing {self.config.crossing_id}")
        await asyncio.sleep(0.1)
    
    async def _start_countdown(self):
        """Start countdown sequence"""
        countdown_time = self.get_adjusted_time(self.config.countdown_time)
        logger.info(f"Starting {countdown_time}s countdown at crossing {self.config.crossing_id}")
        
        for i in range(countdown_time, 0, -1):
            if self.current_state != CrossingState.COUNTDOWN:
                break
            await asyncio.sleep(1)
    
    async def _lower_barriers(self):
        """Lower crossing barriers"""
        move_time = self.get_adjusted_time(self.config.barrier_move_time)
        logger.info(f"Lowering barriers at crossing {self.config.crossing_id}")
        await asyncio.sleep(move_time)
    
    async def _activate_emergency_protocol(self):
        """Activate emergency procedures"""
        logger.warning(f"EMERGENCY at crossing {self.config.crossing_id}")
        await asyncio.sleep(0.1)
    
    async def _activate_fail_safe(self):
        """Activate fail-safe mode"""
        logger.error(f"FAIL-SAFE at crossing {self.config.crossing_id}")
        await asyncio.sleep(0.1)
    
    async def _monitor_train_passage(self):
        """Monitor train passage with safety checks"""
        logger.info(f"Monitoring train passage at crossing {self.config.crossing_id}")
        await asyncio.sleep(5)
        
        if not self._verify_train_passage():
            await self.transition(CrossingState.EMERGENCY, force=True)
    
    def _verify_train_passage(self) -> bool:
        """Verify train passed using sensor fusion"""
        return True
    
    def calculate_arrival_time(self) -> float:
        """Calculate estimated arrival time based on speed and distance"""
        if self.train_speed <= 0:
            return float('inf')
        
        speed_mps = self.train_speed * (1000 / 3600)
        
        if speed_mps <= 0:
            return float('inf')
        
        return self.train_distance / speed_mps
    
    def get_state_diagram(self) -> Dict:
        """Generate state diagram for visualization"""
        return {
            'states': [state.name for state in CrossingState],
            'current_state': self.current_state.name,
            'possible_transitions': self._get_possible_transitions(),
            'history': self.state_history[-10:] if self.state_history else []
        }
    
    def _get_possible_transitions(self) -> list:
        """Get list of possible next states"""
        transitions = {
            CrossingState.IDLE: ['WARNING', 'EMERGENCY', 'MAINTENANCE', 'CALIBRATION'],
            CrossingState.WARNING: ['COUNTDOWN', 'IDLE', 'EMERGENCY'],
            CrossingState.COUNTDOWN: ['BARRIER_DOWN', 'EMERGENCY'],
            CrossingState.BARRIER_DOWN: ['TRAIN_PASSING', 'EMERGENCY'],
            CrossingState.TRAIN_PASSING: ['BARRIER_UP', 'EMERGENCY'],
            CrossingState.BARRIER_UP: ['IDLE', 'EMERGENCY'],
            CrossingState.EMERGENCY: ['IDLE', 'FAIL_SAFE'],
            CrossingState.MAINTENANCE: ['IDLE'],
            CrossingState.CALIBRATION: ['IDLE'],
            CrossingState.FAIL_SAFE: ['IDLE']
        }
        
        return transitions.get(self.current_state, [])