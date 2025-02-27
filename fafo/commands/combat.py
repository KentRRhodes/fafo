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
    aliases = ["attack", "hit"]
    locks = "cmd:all()"
    help_category = "Combat"
    
    def func(self):
        """Handle the kill command."""
        if not self.args:
            self.caller.msg("Kill what?")
            return
            
        target = self.caller.search(self.args)
        if not target:
            # search handled error message
            return
            
        # Check target is a valid combatant (Character or Hostile)
        if not (isinstance(target, (Character, Hostile))):
            self.caller.msg("You can't attack that!")
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