"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.
"""

from evennia import default_cmds, CmdSet
from commands.builder import (CmdBuildRoom, CmdBuildGrid, CmdBuildMaze, 
                            CmdInitCoords, CmdCheckCoords, CmdDeleteBlock,
                            CmdAddRegion)
from commands.compass import (CmdNorth, CmdSouth, CmdEast, CmdWest,
                            CmdNortheast, CmdNorthwest, CmdSoutheast, CmdSouthwest)

class CompassCmdSet(CmdSet):
    """
    This cmdset holds basic directional movement commands.
    """
    key = "CompassCmdSet"
    priority = 0  # Lower priority so building commands take precedence
    
    def at_cmdset_creation(self):
        """
        Add basic movement commands that all characters should have
        """
        self.add(CmdNorth())
        self.add(CmdSouth())
        self.add(CmdEast())
        self.add(CmdWest())
        self.add(CmdNortheast())
        self.add(CmdNorthwest())
        self.add(CmdSoutheast())
        self.add(CmdSouthwest())

class BuilderCmdSet(CmdSet):
    """
    This cmdset holds builder commands for creating rooms and structures.
    """
    key = "BuilderCmdSet"
    priority = 1  # Higher priority to override navigation commands if needed
    
    def at_cmdset_creation(self):
        """
        Add building commands that only builders should have
        """
        self.add(CmdInitCoords())
        self.add(CmdCheckCoords())
        self.add(CmdDeleteBlock())
        self.add(CmdBuildRoom())
        self.add(CmdBuildGrid())
        self.add(CmdBuildMaze())
        self.add(CmdAddRegion())

class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CompassCmdSet)  # Add navigation commands (available to all)
        self.add(BuilderCmdSet)  # Add builder commands (permission controlled)


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
