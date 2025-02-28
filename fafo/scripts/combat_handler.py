"""
Combat handler script for processing combat actions.
"""
import random
from evennia import DefaultScript, create_script, GLOBAL_SCRIPTS
from evennia.utils import lazy_property
from evennia.utils.utils import time_format
from typeclasses.hostiles import Hostile
from evennia.server.sessionhandler import SESSIONS
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
        self.persistent = False  # Ensure script doesn't persist through server restart
        
        # Initialize with defaults, these will be set properly after creation
        self.db.start_time = time.time()
        self.db.duration = 5  # Default 5 seconds
        
    def at_repeat(self):
        """Called every self.interval seconds."""
        if time.time() >= self.db.start_time + self.db.duration:
            # Notify the character roundtime is done
            self.obj.msg("You have recovered.")
            # Stop and delete the script
            self.stop()
            self.delete()
            return
            
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
        
    def at_script_stop(self):
        """Called when script is stopped for any reason."""
        # Clean up roundtime references
        if self.obj:
            if hasattr(self.obj, 'db'):
                if hasattr(self.obj, 'roundtime'):
                    self.obj.roundtime = None
            # Notify the character if online
            if hasattr(self.obj, 'msg'):
                self.obj.msg("Your roundtime has expired.")
        self.delete()
        
    def at_server_reload(self):
        """Called if server reloads."""
        self.stop()
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        self.stop()

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
        Calculate if an attack hits with two-stage system:
        1. ATT = agility + speed + weapon_skill + buffs - debuffs + d100
        2. If initial roll fails, check if power difference can overcome
        
        Args:
            attacker (Object): The attacking character/monster
            defender (Object): The defending character/monster
            
        Returns:
            tuple: (bool hit, dict roll_info)
        """
        # Calculate attacker's base attack value (before d100)
        attack_base = int(attacker.agility + 
                         attacker.speed + 
                         attacker.weapons)  # buffs/debuffs handled by stat system
        
        # Calculate defender's base defense value
        shield_bonus = int(defender.shields if hasattr(defender, 'left_hand') and defender.left_hand else 0)
        defense_base = int(defender.agility + 
                          defender.speed + 
                          shield_bonus)  # buffs/debuffs handled by stat system
        
        # Roll d100s
        attacker_roll = random.randint(1, 100)
        defender_roll = random.randint(1, 100)
        
        # Calculate final values
        attack_total = attack_base + attacker_roll
        defense_total = defense_base + defender_roll
        
        # Calculate initial end result
        end_roll = attack_total - defense_total
        
        # Calculate power difference (never negative)
        power_diff = int(max(0, attacker.power - defender.power))
        
        # Store all roll information
        roll_info = {
            'attack_base': attack_base,
            'attack_roll': attacker_roll,
            'attack_total': attack_total,
            'defense_base': defense_base,
            'defense_roll': defender_roll,
            'defense_total': defense_total,
            'end_roll': end_roll,
            'power_diff': power_diff,
            'power_hit': False  # Track if hit was due to power difference
        }
        
        # First check - standard hit
        if end_roll > 0:
            return True, roll_info
            
        # Second check - power-based hit
        if end_roll + power_diff >= 1:
            roll_info['power_hit'] = True
            return True, roll_info
            
        return False, roll_info

    def calculate_damage(self, attacker, power_hit=False, power_diff=0, end_roll=0):
        """
        Calculate base damage for an attack.
        Damage is linear based on either the endroll for normal hits,
        or the power difference for power-based hits.
        
        Args:
            attacker (Object): The attacking character/monster
            power_hit (bool): Whether this was a power-based hit
            power_diff (int): Power difference if it was a power-based hit
            end_roll (int): The end roll value for normal hits
            
        Returns:
            int: Amount of damage to deal
        """
        if power_hit:
            # Use power difference as the effective endroll
            return max(1, power_diff)
        else:
            # Use the actual endroll for damage
            return max(1, end_roll)
        
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
        
        # Check if attack hits and get the roll details
        hits, roll_info = self.calculate_hit(attacker, defender)
        
        # Construct the combat message
        if roll_info['power_hit']:
            combat_msg = (
                f"{attacker.key} powers through {defender.key}'s formidable defenses.\n"
                f"ATT: {roll_info['attack_base']} + {roll_info['attack_roll']}(d100) "
                f"vs DEF {roll_info['defense_total']} = {roll_info['end_roll']}\n"
            )
        else:
            combat_msg = (
                f"{attacker.key} attacks {defender.key}\n"
                f"ATT: {roll_info['attack_base']} + {roll_info['attack_roll']}(d100) "
                f"vs DEF {roll_info['defense_total']} = {roll_info['end_roll']}\n"
            )
        
        if hits:
            # Calculate damage based on whether it was a power hit
            damage = self.calculate_damage(attacker, 
                                        power_hit=roll_info['power_hit'], 
                                        power_diff=roll_info['power_diff'],
                                        end_roll=roll_info['end_roll'])
            defender.take_damage(damage)
            
            # Complete the message based on hit type
            if roll_info['power_hit']:
                combat_msg += f"A powerful strike lands for {damage} damage!"
            else:
                combat_msg += f"A clean hit for {damage} damage!"
            
            # Announce to all
            if attacker.location:
                attacker.location.msg_contents(combat_msg)
                        
            # Check for death
            if defender.current_health <= 0:
                self.handle_death(attacker, defender)
                
            return True, damage, roundtime
            
        else:
            # Complete the message for a miss
            combat_msg += "a miss."
            
            # Announce to all
            if attacker.location:
                attacker.location.msg_contents(combat_msg)
                        
            return False, 0, roundtime
            
    def handle_death(self, attacker, defender):
        """
        Handle a combatant's death.
        """
        if hasattr(defender, 'experience'):
            # Award XP if defender has experience value
            attacker.gain_experience(defender.experience)
            
        # Announce death
        if attacker.location:
            attacker.location.msg_contents(f"{defender.key} has been slain by {attacker.key}!")
            
        # If it's a hostile, turn it into a temporary corpse
        if isinstance(defender, Hostile):
            # Change the name to indicate it's a corpse
            original_name = defender.key
            defender.key = f"the body of {original_name}"
            defender.db.corpse = True  # Mark as a corpse
            
            # Set locks to prevent interaction
            defender.locks.add("get:false();delete:perm(Wizards);puppet:false()")
            
            # Disable combat-related attributes
            defender.db.inactive = True
            
            # Create corpse deletion script
            create_script(
                "scripts.combat_handler.CorpseScript",
                obj=defender,
                persistent=False,
                autostart=True
            )
        else:
            # For non-hostiles (like players), just handle normally
            defender.delete()
        
    def at_repeat(self):
        """
        Called every self.interval seconds (1 minute).
        Clean up old roundtimes to prevent memory bloat.
        """
        # Nothing to do for now - will be used for more complex combat tracking later
        pass

    def get_combat_details(self, attacker, defender, attacker_roll, defender_roll, endroll, power_diff):
        """
        Generate a detailed breakdown of combat calculations.
        """
        shield_bonus = defender.shields if hasattr(defender, 'left_hand') and defender.left_hand else 0
        
        attacker_msg = (
            f"\nAttack Roll Breakdown:"
            f"\n Base Attack: {attacker.attack}"
            f"\n Weapon Skill: +{attacker.weapons}"
            f"\n Your Roll: +{attacker_roll}"
            f"\n vs"
            f"\n Defense: {defender.defense}"
            f"\n Shield Bonus: +{shield_bonus}"
            f"\n Their Roll: +{defender_roll}"
            f"\n = Final Roll: {endroll}"
        )
        
        defender_msg = (
            f"\nDefense Roll Breakdown:"
            f"\n Their Attack: {attacker.attack}"
            f"\n Their Weapon Skill: +{attacker.weapons}"
            f"\n Their Roll: +{attacker_roll}"
            f"\n vs"
            f"\n Your Defense: {defender.defense}"
            f"\n Shield Bonus: +{shield_bonus}"
            f"\n Your Roll: +{defender_roll}"
            f"\n = Final Roll: {endroll}"
        )
        
        room_msg = f" (Roll: {endroll})"
        
        return attacker_msg, defender_msg, room_msg

class CorpseScript(DefaultScript):
    """A script that deletes a corpse after a delay."""
    
    def at_script_creation(self):
        """Set up the script."""
        self.key = "corpse_script"
        self.desc = "Deletes a corpse after delay"
        self.interval = 20  # 20 second delay
        self.persistent = False
        self.repeats = 1    # Run only once
        self.start_delay = True  # Important: This makes it wait before first repeat
        
    def at_repeat(self):
        """Called after the 20-second delay."""
        if self.obj and hasattr(self.obj, 'location'):
            # Announce the corpse disappearing
            self.obj.location.msg_contents(f"{self.obj.key} crumbles to dust.")
            # Delete the corpse
            self.obj.delete()
        self.stop()

    def at_start(self):
        """Called when script starts running."""
        # We don't need to do anything here, just wait for the interval
        pass