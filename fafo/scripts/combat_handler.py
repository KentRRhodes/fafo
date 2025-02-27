"""
Combat handler script for processing combat actions.
"""
import random
from evennia import DefaultScript, create_script
from evennia.utils import lazy_property
from evennia.utils.utils import time_format
import time

class RoundtimeScript(DefaultScript):
    """
    A script that manages a character's roundtime.
    The script will automatically delete itself when roundtime expires.
    """
    def at_script_creation(self):
        """Set up the script."""
        self.key = "roundtime_script"
        self.desc = "Handles character roundtime"
        self.interval = 1  # Check every second
        self.persistent = False
        
        # Initialize with defaults, these will be set properly after creation
        self.db.start_time = time.time()
        self.db.duration = 5  # Default 5 seconds
        
    def at_repeat(self):
        """Called every self.interval seconds."""
        if time.time() >= self.db.start_time + self.db.duration:
            # Notify the character roundtime is done
            self.obj.msg("You have recovered.")
            self.stop()
            
    def extend_time(self, seconds):
        """
        Extend the roundtime by the given number of seconds.
        
        Args:
            seconds (float): Number of seconds to add
        """
        self.db.duration += seconds
        
    def time_remaining(self):
        """
        Get the remaining roundtime in seconds.
        
        Returns:
            float: Seconds remaining in roundtime
        """
        return max(0, (self.db.start_time + self.db.duration) - time.time())

class CombatHandler(DefaultScript):
    """
    Combat handler script that manages combat calculations.
    """
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.persistent = True
        self.key = "combat_handler"
        self.desc = "Handles combat calculations"
        
    def is_in_roundtime(self, character):
        """
        Check if a character is currently in roundtime.
        
        Args:
            character (Object): The character to check
            
        Returns:
            tuple: (bool in_roundtime, float remaining_time)
        """
        script = character.scripts.get("roundtime_script")
        if script:
            return True, script[0].time_remaining()
        return False, 0

    def set_roundtime(self, character, duration, extend=False):
        """
        Set or extend a character's roundtime.
        
        Args:
            character (Object): The character to set roundtime for
            duration (float): Number of seconds for roundtime
            extend (bool): If True, add to existing roundtime
            
        Returns:
            RoundtimeScript: The roundtime script
        """
        script = character.scripts.get("roundtime_script")
        
        if script and extend:
            # Extend existing roundtime
            script[0].extend_time(duration)
            return script[0]
        elif script:
            # Replace existing roundtime
            script[0].stop()
            
        # Create new roundtime script and set its properties after creation
        new_script = create_script(
            "scripts.combat_handler.RoundtimeScript",
            obj=character
        )
        new_script.db.duration = duration
        new_script.db.start_time = time.time()
        return new_script

    def calculate_hit(self, attacker, defender):
        """
        Calculate if an attack hits based on attacker's attack vs defender's defense + d100.
        
        Args:
            attacker (Object): The attacking character/monster
            defender (Object): The defending character/monster
            
        Returns:
            bool: Whether the attack hits
        """
        attack_roll = random.randint(1, 100)
        total_attack = attacker.attack + attack_roll
        
        return total_attack > defender.defense
        
    def calculate_damage(self, attacker):
        """
        Calculate base damage for an attack.
        
        Args:
            attacker (Object): The attacking character/monster
            
        Returns:
            int: Amount of damage to deal
        """
        # Basic damage of 1-10 for now
        return random.randint(1, 10)
        
    def process_attack(self, attacker, defender):
        """
        Process a complete attack sequence.
        
        Args:
            attacker (Object): The attacking character/monster
            defender (Object): The defending character/monster
            
        Returns:
            tuple: (bool hit, int damage, RoundtimeScript)
        """
        # Check if attacker is in roundtime, regardless of type
        in_roundtime, remaining = self.is_in_roundtime(attacker)
        if in_roundtime:
            if hasattr(attacker, 'msg'):  # Only message if it's a player character
                attacker.msg(f"You are still recovering from your last action! ({time_format(remaining, 1)} remaining)")
            return False, 0, None
            
        # Set base 5 second roundtime
        roundtime = self.set_roundtime(attacker, 5)
        
        # Check if attack hits
        if self.calculate_hit(attacker, defender):
            damage = self.calculate_damage(attacker)
            defender.take_damage(damage)
            
            # Announce hit
            attacker.msg(f"You hit {defender.key} for {damage} damage!")
            defender.msg(f"{attacker.key} hits you for {damage} damage!")
            if attacker.location:
                # Announce to others in room
                for obj in attacker.location.contents:
                    if obj != attacker and obj != defender and hasattr(obj, 'msg'):
                        obj.msg(f"{attacker.key} hits {defender.key} for {damage} damage!")
                        
            # Check for death
            if defender.current_health <= 0:
                self.handle_death(attacker, defender)
                
            return True, damage, roundtime
            
        else:
            # Announce miss
            attacker.msg(f"You miss {defender.key}!")
            defender.msg(f"{attacker.key} misses you!")
            if attacker.location:
                # Announce to others in room
                for obj in attacker.location.contents:
                    if obj != attacker and obj != defender and hasattr(obj, 'msg'):
                        obj.msg(f"{attacker.key} misses {defender.key}!")
                        
            return False, 0, roundtime
            
    def handle_death(self, attacker, defender):
        """
        Handle a combatant's death.
        
        Args:
            attacker (Object): The killing character/monster
            defender (Object): The dying character/monster
        """
        if hasattr(defender, 'experience'):
            # Award XP if defender has experience value
            attacker.gain_experience(defender.experience)
            
        # Announce death
        if attacker.location:
            attacker.location.msg_contents(f"{defender.key} has been slain by {attacker.key}!")
            
        # Handle death cleanup
        defender.delete()
        
    def at_repeat(self):
        """
        Called every self.interval seconds (1 minute).
        Clean up old roundtimes to prevent memory bloat.
        """
        # Nothing to do for now - will be used for more complex combat tracking later
        pass