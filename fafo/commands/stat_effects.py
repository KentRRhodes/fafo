"""
Commands for testing and managing stat effects.
"""
from evennia import Command, GLOBAL_SCRIPTS
from evennia.utils.utils import time_format
from scripts.stat_handler import StatEffect

class CmdEffect(Command):
    """
    Add or remove stat effects for testing.
    
    Usage:
      effect add <stat> <value> [duration=<seconds>] [%]
      effect remove <stat|all>
      effect list
      
    Examples:
      effect add speed 2 duration=30    - Add +2 speed for 30 seconds
      effect add agility -1 duration=60  - Reduce agility by 1 for 1 minute
      effect add power 50% duration=10   - Add 50% power for 10 seconds
      effect list                       - List all active effects
      effect remove speed               - Remove all speed effects
      effect remove all                 - Remove all effects
    """
    key = "effect"
    locks = "cmd:all()"
    help_category = "Test"
    
    def func(self):
        """Handle the effect command."""
        if not self.args:
            self.caller.msg("Usage: effect <add|remove|list> [args]")
            return
            
        effect_handler = GLOBAL_SCRIPTS.stat_effect_handler
        if not effect_handler:
            self.caller.msg("Error: Stat effect handler not found!")
            return
            
        args = self.args.split()
        if args[0] == "list":
            # Show active effects
            char_id = self.caller.id
            if char_id not in effect_handler.db.effects:
                self.caller.msg("You have no active effects.")
                return
                
            effects = effect_handler.db.effects[char_id]
            if not effects:
                self.caller.msg("You have no active effects.")
                return
                
            self.caller.msg("Your active effects:")
            for stat, stat_effects in effects.items():
                for effect in stat_effects:
                    if effect.is_percentage:
                        value = f"{effect.value}%"
                    else:
                        value = effect.value
                    remaining = effect.remaining_time()
                    if remaining == float('inf'):
                        duration = "permanent"
                    else:
                        duration = time_format(remaining, 1)
                    self.caller.msg(f"  {stat}: {value} ({duration} remaining)")
                    
        elif args[0] == "add" and len(args) >= 3:
            # Parse effect parameters
            stat = args[1]
            value = args[2]
            duration = None
            is_percentage = False
            
            # Check for percentage modifier
            if value.endswith('%'):
                is_percentage = True
                value = value[:-1]
            
            try:
                value = float(value)
            except ValueError:
                self.caller.msg("Value must be a number!")
                return
                
            # Check for duration
            if len(args) > 3:
                for arg in args[3:]:
                    if arg.startswith('duration='):
                        try:
                            duration = float(arg.split('=')[1])
                        except (IndexError, ValueError):
                            self.caller.msg("Duration must be a number of seconds!")
                            return
                            
            # Create and add the effect
            effect = StatEffect(
                stat=stat,
                value=value,
                duration=duration,
                is_percentage=is_percentage,
                source="test",
                stacks=True
            )
            effect_handler.add_effect(self.caller, effect)
            
            if duration:
                self.caller.msg(f"Added {value}{'%' if is_percentage else ''} {stat} effect for {duration} seconds.")
            else:
                self.caller.msg(f"Added permanent {value}{('%' if is_percentage else '')} {stat} effect.")
                
        elif args[0] == "remove":
            if len(args) < 2:
                self.caller.msg("Specify what to remove!")
                return
                
            if args[1] == "all":
                # Remove all effects
                for stat in list(effect_handler.db.effects.get(self.caller.id, {}).keys()):
                    effect_handler.remove_effect(self.caller, stat=stat)
                self.caller.msg("Removed all effects.")
            else:
                # Remove specific stat effects
                effect_handler.remove_effect(self.caller, stat=args[1])
                self.caller.msg(f"Removed all {args[1]} effects.")
        else:
            self.caller.msg("Invalid command. Use 'help effect' for usage.")