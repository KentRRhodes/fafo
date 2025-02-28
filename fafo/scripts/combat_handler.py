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
            self.obj.msg("Roundtime expired.")
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
                self.obj.msg("Roundtime expired.")
        self.delete()
        
    def at_server_reload(self):
        """Called if server reloads."""
        self.stop()
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        self.stop()

class VulnerabilityScript(DefaultScript):
    """
    A script that manages a character's vulnerability timer and effects.
    """
    def at_script_creation(self):
        """Set up the script."""
        self.key = "vulnerability_script"
        self.desc = "Handles character vulnerability period"
        self.interval = 1  # Check every second
        self.persistent = False
        
        # Initialize with defaults
        self.db.start_time = time.time()
        self.db.duration = 5  # Default 5 seconds
        self.db.vuln_type = None  # Type of vulnerability
        self.db.def_reduction = 0  # Percentage reduction to defense
        
    def at_repeat(self):
        """Called every self.interval seconds."""
        if time.time() >= self.db.start_time + self.db.duration:
            # Notify the character vulnerability is done
            self.obj.msg("You manage to recover your guard.")
            # Stop and delete the script
            self.stop()
            self.delete()
            return
            
    def set_vulnerability(self, vuln_type, def_reduction):
        """
        Set the vulnerability type and its effects.
        
        Args:
            vuln_type (str): Type of vulnerability (e.g. "miss")
            def_reduction (float): Percentage reduction to defense
        """
        self.db.vuln_type = vuln_type
        self.db.def_reduction = def_reduction
        
    def get_defense_modifier(self):
        """
        Get the current defense modification.
        
        Returns:
            float: Multiplier for defense (e.g. 0.5 for 50% reduction)
        """
        return max(0, 1 - (self.db.def_reduction / 100))
        
    def extend_time(self, seconds):
        """
        Extend the vulnerability by the given number of seconds.
        
        Args:
            seconds (float): Number of seconds to add
        """
        self.db.duration += seconds
        
    def time_remaining(self):
        """
        Get the remaining vulnerability time in seconds.
        
        Returns:
            float: Seconds remaining in vulnerability
        """
        return max(0, (self.db.start_time + self.db.duration) - time.time())
        
    def at_script_stop(self):
        """Called when script is stopped for any reason."""
        # Clean up vulnerability references
        if self.obj:
            if hasattr(self.obj, 'db'):
                if hasattr(self.obj, 'vulnerability'):
                    self.obj.vulnerability = None
            # Notify the character if online
            if hasattr(self.obj, 'msg'):
                self.obj.msg("You manage to recover your guard.")
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

    def set_vulnerability(self, character, duration):
        """
        Set or extend a character's vulnerability timer.
        
        Args:
            character (Object): The character to set vulnerability for
            duration (float): Number of seconds for vulnerability
            
        Returns:
            VulnerabilityScript: The vulnerability script
        """
        script = character.scripts.get("vulnerability_script")
        
        if script:
            # Replace existing vulnerability
            script[0].stop()
            
        # Create new vulnerability script
        new_script = create_script(
            "scripts.combat_handler.VulnerabilityScript",
            obj=character,
            persistent=False,
            autostart=True
        )
        new_script.db.duration = duration
        new_script.db.start_time = time.time()
        return new_script
        
    def calculate_vulnerability_time(self, attacker):
        """Calculate vulnerability time based on weapon speed and finesse."""
        # Get weapon speed from equipped weapon, default to 5 if no weapon
        weapon_speed = 5  # Default vulnerability time
        if hasattr(attacker, 'right_hand') and attacker.right_hand:
            if hasattr(attacker.right_hand, 'weapon_speed'):
                weapon_speed = attacker.right_hand.weapon_speed
                
        # Get attacker's weapon finesse
        finesse = attacker.get_weapon_finesse()
        
        # Calculate base time (50% of weapon speed)
        base_time = weapon_speed * 0.5
        
        # Reduce by weapon finesse (10% per point)
        reduction = finesse * 0.1 * base_time
        
        # Return final time with minimum of 1 second
        return max(1.0, base_time - reduction)
        
    def calculate_vulnerability_defense_reduction(self, attacker):
        """Calculate defense reduction percentage based on weapon finesse."""
        finesse = attacker.get_weapon_finesse()
        # Base 50% reduction, decreased by 10% per point of finesse
        reduction = 50 - (finesse * 10)
        # Ensure reduction stays between 0% and 50%
        return max(0, min(50, reduction))

    def calculate_hit(self, attacker, defender):
        """
        Calculate if an attack hits with two-stage system.
        Takes into account vulnerability defense reductions.
        """
        # Calculate attacker's base attack value (before d100)
        attack_base = int(attacker.agility + 
                         attacker.speed + 
                         attacker.weapons)
        
        # Calculate defender's base defense value
        shield_bonus = int(defender.shields if hasattr(defender, 'left_hand') and defender.left_hand else 0)
        defense_base = int(defender.agility + 
                          defender.speed + 
                          shield_bonus)
        
        # Check for vulnerability effects on defender
        vulnerability = defender.scripts.get("vulnerability_script")
        if vulnerability:
            # Apply defense reduction before d100
            defense_base = int(defense_base * vulnerability[0].get_defense_modifier())
        
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
            'power_hit': False
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
        
    def get_vulnerability_chance(self, attacker):
        """
        Calculate chance of vulnerability on miss based on weapon finesse rank.
        
        Args:
            attacker (Object): The attacking character/monster
            
        Returns:
            float: Chance of vulnerability (0.0 to 1.0)
        """
        finesse = attacker.get_weapon_finesse()
        if finesse <= 1:
            return 0.5  # 50% base chance
        elif finesse <= 3:
            return 0.4  # 40% chance at rank 2-3
        else:  # 4-5
            return 0.3  # 30% chance at rank 4-5
            
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
                f"ATT: {roll_info['attack_base']} + {roll_info['attack_roll']}(d100) [{roll_info['attack_total']}] "
                f"vs DEF [{roll_info['defense_total']}] = {roll_info['end_roll']}\n"
            )
        else:
            combat_msg = (
                f"{attacker.key} attacks {defender.key}\n"
                f"ATT: {roll_info['attack_base']} + {roll_info['attack_roll']}(d100) [{roll_info['attack_total']}] "
                f"vs DEF [{roll_info['defense_total']}] = {roll_info['end_roll']}\n"
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
            # Only apply vulnerability if both checks failed (not a power hit)
            if not roll_info['power_hit']:
                # Roll for vulnerability chance
                vuln_chance = self.get_vulnerability_chance(attacker)
                if random.random() < vuln_chance:
                    vuln_time = self.calculate_vulnerability_time(attacker)
                    def_reduction = self.calculate_vulnerability_defense_reduction(attacker)
                    
                    # Create vulnerability script
                    vuln_script = self.set_vulnerability(attacker, vuln_time)
                    vuln_script.set_vulnerability("miss", def_reduction)
                    
                    # Complete the message for a vulnerable miss
                    combat_msg += "Your failed attack leaves you feeling exposed."
                    
                    if hasattr(attacker, 'msg'):
                        attacker.msg(f"Defense reduced by {def_reduction}% for {vuln_time:.1f} seconds!")
                elif hasattr(attacker, 'msg'):
                    # Complete the message for a non-vulnerable miss
                    combat_msg += "a miss."
                    attacker.msg("Your weapon finesse helps you maintain your defenses despite the miss!")
            else:
                # Complete the message for a power-check miss
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
        """Generate a detailed breakdown of combat calculations."""
        shield_bonus = defender.shields if hasattr(defender, 'left_hand') and defender.left_hand else 0
        
        # Calculate totals for display
        attack_total = attacker.attack + attacker.weapons + attacker_roll
        defense_total = defender.defense + shield_bonus + defender_roll
        
        attacker_msg = (
            f"\nAttack Roll Breakdown:"
            f"\n Base Attack: {attacker.attack}"
            f"\n Weapon Skill: +{attacker.weapons}"
            f"\n Your Roll: +{attacker_roll}"
            f"\n vs"
            f"\n Defense: {defender.defense}"
            f"\n Shield Bonus: +{shield_bonus}"
            f"\n Their Roll: +{defender_roll}"
            f"\n = ATT [{attack_total}] vs DEF [{defense_total}] = {endroll}"
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
            f"\n = ATT [{attack_total}] vs DEF [{defense_total}] = {endroll}"
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