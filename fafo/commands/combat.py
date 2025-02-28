"""
Combat commands module.
"""
from evennia import Command, GLOBAL_SCRIPTS
from evennia.utils.utils import time_format
from typeclasses.characters import Character
from typeclasses.hostiles import Hostile
import time

class CmdKill(Command):
    """
    Attack another character or NPC.
    
    Usage:
      kill <target>
      
    Initiates combat with the specified target.
    """
    key = "kill"
    aliases = ["attack", "k", "kil"]
    locks = "cmd:all()"
    help_category = "Combat"
    
    def func(self):
        """Handle the kill command."""
        target = None
        
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                # search handled error message
                return
        else:
            # No target specified, look for the first hostile in the room
            if self.caller.location:
                for obj in self.caller.location.contents:
                    if isinstance(obj, Hostile) and obj.is_alive():
                        target = obj
                        break
            
            if not target:
                self.caller.msg("No valid targets found!")
                return
            
        # Check target is a valid combatant (Character or Hostile)
        if not (isinstance(target, (Character, Hostile))):
            self.caller.msg("You can't attack that!")
            return
            
        # Check if target is a corpse
        if isinstance(target, Hostile) and not target.is_alive():
            self.caller.msg(f"{target.key} is already dead!")
            return
            
        # Check we're not in roundtime
        combat = GLOBAL_SCRIPTS.combat_handler
        in_roundtime, remaining = combat.is_in_roundtime(self.caller)
        if in_roundtime:
            self.caller.msg(f"You are still recovering from your last action! ({time_format(remaining, 1)} remaining)")
            return
            
        # Process the attack through combat handler
        hit, damage, roundtime_script = combat.process_attack(self.caller, target)
        
        # Set roundtime
        self.caller.db.roundtime = roundtime_script

class CmdAim(Command):
    """
    Target a specific body part for your next attack.
    
    Usage:
      aim <body part>
      aim clear
      aim
      
    Examples:
      aim head     - Target the head
      aim clear    - Clear current aim
      aim         - Show current aim
    """
    key = "aim"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def normalize_body_part(self, target):
        """
        Normalize body part input to match valid format.
        Handles various input formats like 'right arm', 'r arm', 'rarm', etc.
        """
        target = target.lower().strip()
        
        # Handle 'clear' command
        if target == "clear":
            return "clear"
            
        # Simple body parts that don't need processing
        if target in ["head", "neck", "chest", "back", "abdomen"]:
            return target
            
        # Process sides (right/left)
        if target.startswith(('right', 'left', 'r', 'l')):
            # Split into words
            parts = target.split()
            if len(parts) == 1:  # Combined word like 'rarm' or 'lleg'
                if target.startswith('r'):
                    side = 'right'
                    part = target[1:]
                else:
                    side = 'left'
                    part = target[1:]
            else:  # Separate words like 'r arm' or 'left leg'
                side = 'right' if parts[0] in ['r', 'right'] else 'left'
                part = parts[1] if len(parts) > 1 else ''
                
            # Validate part
            if part in ['arm', 'hand', 'leg', 'eye']:
                return f"{side}_{part}"
                
        return target  # Return original if no matches
        
    def func(self):
        """Handle the aim command."""
        if not self.args:
            if self.caller.aim:
                self.caller.msg(f"You are currently aiming at: {self.caller.aim.replace('_', ' ')}")
            else:
                self.caller.msg("You are not currently aiming at any body part.")
            return
            
        # Normalize the input
        target = self.normalize_body_part(self.args)
        
        if target == "clear":
            self.caller.aim = None
            self.caller.msg("You clear your targeted aim.")
            return
            
        try:
            self.caller.aim = target
            self.caller.msg(f"You will target the {target.replace('_', ' ')} with your next attack.")
        except ValueError as e:
            self.caller.msg(str(e))