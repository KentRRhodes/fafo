"""
Stat Effect Handler

Manages temporary and permanent stat modifications, buffs, and debuffs for all characters.
"""
from evennia import DefaultScript
from evennia.utils.logger import log_trace
import time

class StatEffect:
    """
    Represents a single stat modification effect.
    """
    def __init__(self, stat, value, duration=None, is_percentage=False, 
                 source=None, stacks=False, priority=1, condition=None):
        """
        Initialize a stat effect.
        
        Args:
            stat (str): The stat being modified
            value (float): Modification value (positive or negative)
            duration (float, optional): Duration in seconds, None for permanent
            is_percentage (bool): If True, value is a percentage modifier
            source (str): Source of the effect (spell name, item, etc)
            stacks (bool): Whether multiple instances of this effect can stack
            priority (int): Order of application (higher = later)
            condition (callable, optional): Function that returns bool if effect should apply
        """
        self.stat = stat
        self.value = value
        self.duration = duration
        self.start_time = time.time()
        self.is_percentage = is_percentage
        self.source = source
        self.stacks = stacks
        self.priority = priority
        self.condition = condition
        
    def is_expired(self):
        """Check if effect has expired."""
        if self.duration is None:
            return False
        return time.time() >= self.start_time + self.duration
        
    def remaining_time(self):
        """Get remaining duration in seconds."""
        if self.duration is None:
            return float('inf')
        return max(0, (self.start_time + self.duration) - time.time())
        
    def should_apply(self, character):
        """Check if effect should currently apply to character."""
        if self.is_expired():
            return False
        if self.condition and callable(self.condition):
            try:
                return self.condition(character)
            except Exception:
                log_trace("Error in stat effect condition")
                return False
        return True

class StatEffectHandler(DefaultScript):
    """
    Script that manages all stat effects on characters.
    Runs every second to update effects and recalculate stats.
    """
    
    def at_script_creation(self):
        """Set up the script."""
        self.key = "stat_effect_handler"
        self.desc = "Manages character stat effects"
        self.interval = 1  # Check every second
        self.persistent = True
        
        # Initialize effect storage
        # Structure: {character_id: {stat_name: [StatEffect, ...]}}
        self.db.effects = {}
        
        # Cache of calculated stats
        # Structure: {character_id: {stat_name: value}}
        self.db.stat_cache = {}
        
    def add_effect(self, character, effect):
        """
        Add a new stat effect to a character.
        
        Args:
            character: The character to affect
            effect (StatEffect): The effect to apply
        """
        char_id = character.id
        if char_id not in self.db.effects:
            self.db.effects[char_id] = {}
            
        if effect.stat not in self.db.effects[char_id]:
            self.db.effects[char_id][effect.stat] = []
            
        # Check stacking rules
        if not effect.stacks:
            # Remove existing non-stacking effects from same source
            self.db.effects[char_id][effect.stat] = [
                e for e in self.db.effects[char_id][effect.stat]
                if e.source != effect.source or e.stacks
            ]
            
        self.db.effects[char_id][effect.stat].append(effect)
        self._invalidate_cache(char_id, effect.stat)
        
    def remove_effect(self, character, source=None, stat=None):
        """
        Remove effects from a character.
        
        Args:
            character: The character to affect
            source (str, optional): Remove effects from this source
            stat (str, optional): Remove effects for this stat
        """
        char_id = character.id
        if char_id not in self.db.effects:
            return
            
        if stat and stat in self.db.effects[char_id]:
            if source:
                self.db.effects[char_id][stat] = [
                    e for e in self.db.effects[char_id][stat]
                    if e.source != source
                ]
            else:
                self.db.effects[char_id][stat] = []
            self._invalidate_cache(char_id, stat)
        elif source:
            for stat in self.db.effects[char_id]:
                self.db.effects[char_id][stat] = [
                    e for e in self.db.effects[char_id][stat]
                    if e.source != source
                ]
                self._invalidate_cache(char_id, stat)
                
    def calculate_stat(self, character, stat):
        """
        Calculate final value for a stat including all effects.
        
        Args:
            character: The character to calculate for
            stat (str): The stat to calculate
            
        Returns:
            int: The final calculated stat value
        """
        char_id = character.id
        
        # Check cache first
        if char_id in self.db.stat_cache and stat in self.db.stat_cache[char_id]:
            return int(self.db.stat_cache[char_id][stat])
            
        # Get base value (now with base_ prefix)
        base_value = getattr(character, f"base_{stat}", None)
        if base_value is None:
            return None
            
        if char_id not in self.db.effects or stat not in self.db.effects[char_id]:
            return int(base_value)
            
        # Get all active effects
        active_effects = [
            e for e in self.db.effects[char_id][stat]
            if e.should_apply(character)
        ]
        
        # Sort by priority
        active_effects.sort(key=lambda e: e.priority)
        
        # Apply flat modifiers first
        value = base_value
        for effect in active_effects:
            if not effect.is_percentage:
                value += effect.value
                
        # Then percentage modifiers
        for effect in active_effects:
            if effect.is_percentage:
                value *= (1 + effect.value/100.0)
                
        # Convert to integer for combat stats
        value = int(value)
                
        # Cache the result
        if char_id not in self.db.stat_cache:
            self.db.stat_cache[char_id] = {}
        self.db.stat_cache[char_id][stat] = value
        
        return value
        
    def _invalidate_cache(self, char_id, stat):
        """Invalidate cached value for a stat."""
        if char_id in self.db.stat_cache and stat in self.db.stat_cache[char_id]:
            del self.db.stat_cache[char_id][stat]
            
    def clean_expired(self):
        """Remove all expired effects."""
        for char_id in self.db.effects:
            for stat in self.db.effects[char_id]:
                # Remove expired effects
                original_len = len(self.db.effects[char_id][stat])
                self.db.effects[char_id][stat] = [
                    e for e in self.db.effects[char_id][stat]
                    if not e.is_expired()
                ]
                # Invalidate cache if effects were removed
                if len(self.db.effects[char_id][stat]) != original_len:
                    self._invalidate_cache(char_id, stat)
                    
    def at_repeat(self):
        """Called every self.interval seconds."""
        self.clean_expired()