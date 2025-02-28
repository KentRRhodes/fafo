"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.
"""
from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty
from evennia import GLOBAL_SCRIPTS
import random
from .objects import ObjectParent

# Valid body parts for targeting and wounds
VALID_BODY_PARTS = [
    "head", "neck", "chest", "back", "abdomen",
    "right_arm", "left_arm", "right_hand", "left_hand",
    "right_leg", "left_leg", "right_eye", "left_eye"
]

class Character(ObjectParent, DefaultCharacter):
    """
    Base character typeclass for the game.
    
    Attributes:
        # Core Stats
        power (int): Raw physical strength and damage potential
        agility (int): Dexterity, balance, and fine motor control
        speed (int): Movement and action speed
        vitality (int): Health and stamina
        resistance (int): Physical and mental resilience
        focus (int): Mental acuity and concentration
        discipline (int): Self-control and training
        intelligence (int): Problem solving and knowledge
        wisdom (int): Insight and decision making
        charisma (int): Personality and leadership
        
        # Combat Stats
        attack (int): Character's base attack value
        defense (int): Character's base defense value
        max_health (int): Maximum health points
        current_health (int): Current health points
        experience (int): Experience points earned
        left_hand (Object): Item held in left hand
        right_hand (Object): Item held in right hand
        wounds (dict): Current wounds on different body parts
        scars (dict): Permanent scars on different body parts
        
        # Skills
        weapons (int): Proficiency with weapons
        shields (int): Proficiency with shields
        armor (int): Proficiency with armor
        physical_fitness (int): Physical fitness level
        combat_prowess (int): Combat prowess
        evasive_maneuvers (int): Skill in evasive maneuvers
    """
    
    # Core Stats with default values
    base_power = AttributeProperty(default=1, autocreate=True)
    base_agility = AttributeProperty(default=1, autocreate=True)
    base_speed = AttributeProperty(default=1, autocreate=True)
    base_vitality = AttributeProperty(default=1, autocreate=True)
    base_resistance = AttributeProperty(default=1, autocreate=True)
    base_focus = AttributeProperty(default=1, autocreate=True)
    base_discipline = AttributeProperty(default=1, autocreate=True)
    base_intelligence = AttributeProperty(default=1, autocreate=True)
    base_wisdom = AttributeProperty(default=1, autocreate=True)
    base_charisma = AttributeProperty(default=1, autocreate=True)
    
    # Skills with default values
    base_weapons = AttributeProperty(default=1, autocreate=True)
    base_shields = AttributeProperty(default=1, autocreate=True)
    base_armor = AttributeProperty(default=1, autocreate=True)
    base_physical_fitness = AttributeProperty(default=1, autocreate=True)
    base_combat_prowess = AttributeProperty(default=1, autocreate=True)
    base_evasive_maneuvers = AttributeProperty(default=1, autocreate=True)
    
    # Combat attributes
    _aim = AttributeProperty(default=None, autocreate=True)  # Currently aimed body part
    
    @property
    def aim(self):
        """Get current aim location."""
        return self._aim
        
    @aim.setter
    def aim(self, value):
        """Set aim location with validation."""
        if value is None or value in VALID_BODY_PARTS:
            self._aim = value
        else:
            # Convert valid body parts to display format (spaces instead of underscores)
            valid_parts = [part.replace('_', ' ') for part in VALID_BODY_PARTS]
            raise ValueError(f"Invalid body part. Must be one of: {', '.join(valid_parts)}")
    
    # Combat stats
    base_defense = AttributeProperty(default=1, autocreate=True)
    max_health = AttributeProperty(default=10, autocreate=True)
    current_health = AttributeProperty(default=10, autocreate=True)
    experience = AttributeProperty(default=0, autocreate=True)

    def get_modified_stat(self, stat):
        """
        Get a stat's value after all effects are applied.
        
        Args:
            stat (str): The stat to get
            
        Returns:
            float: The final calculated stat value
        """
        effect_handler = GLOBAL_SCRIPTS.stat_effect_handler
        if effect_handler:
            return effect_handler.calculate_stat(self, stat)
        base_stat = getattr(self, f"base_{stat}")
        return base_stat if base_stat is not None else 1

    def get_modified_skill(self, skill):
        """
        Get a skill's value after all effects are applied.
        
        Args:
            skill (str): The skill to get
            
        Returns:
            float: The final calculated skill value
        """
        effect_handler = GLOBAL_SCRIPTS.stat_effect_handler
        if effect_handler:
            return effect_handler.calculate_stat(self, skill)  # Skills use same effect system
        return getattr(self, skill)

    @property
    def attack(self):
        """Calculate attack value from modified agility and speed."""
        return self.agility + self.speed + self.weapons
        
    @property
    def power(self):
        return self.get_modified_stat('power')
        
    @property
    def agility(self):
        return self.get_modified_stat('agility')
        
    @property
    def speed(self):
        return self.get_modified_stat('speed')
        
    @property
    def vitality(self):
        return self.get_modified_stat('vitality')
        
    @property
    def resistance(self):
        return self.get_modified_stat('resistance')
        
    @property
    def focus(self):
        return self.get_modified_stat('focus')
        
    @property
    def discipline(self):
        return self.get_modified_stat('discipline')
        
    @property
    def intelligence(self):
        return self.get_modified_stat('intelligence')
        
    @property
    def wisdom(self):
        return self.get_modified_stat('wisdom')
        
    @property
    def charisma(self):
        return self.get_modified_stat('charisma')
        
    @property
    def weapons(self):
        return self.get_modified_skill('weapons')
        
    @property
    def shields(self):
        return self.get_modified_skill('shields')
        
    @property
    def armor(self):
        return self.get_modified_skill('armor')
        
    @property
    def physical_fitness(self):
        return self.get_modified_skill('physical_fitness')
        
    @property
    def combat_prowess(self):
        return self.get_modified_skill('combat_prowess')
        
    @property
    def evasive_maneuvers(self):
        return self.get_modified_skill('evasive_maneuvers')
        
    @property
    def defense(self):
        """Calculate defense value from agility, speed, and shield if equipped."""
        base_defense = self.agility + self.speed
        shield_bonus = self.shields if self.left_hand else 0  # Get shield bonus if shield equipped
        return base_defense + shield_bonus
    
    # Equipment slots (None means empty)
    left_hand = AttributeProperty(default=None, autocreate=True)
    right_hand = AttributeProperty(default=None, autocreate=True)

    # Wound and scar tracking
    wounds = AttributeProperty(
        default={part: [] for part in VALID_BODY_PARTS},
        autocreate=True
    )
    
    scars = AttributeProperty(
        default={part: [] for part in VALID_BODY_PARTS},
        autocreate=True
    )

    def at_object_creation(self):
        """
        Called when object is first created.
        """
        super().at_object_creation()
        self.db.roundtime = None
        self.db.vulnerability = None

    def cleanup_vulnerability(self):
        """Clean up any vulnerability timers and restore normal defense calculation."""
        vulnerability_scripts = self.scripts.get("vulnerability_script")
        if vulnerability_scripts:
            for script in vulnerability_scripts:
                self.msg("You manage to recover your guard.")
                script.stop()
        self.db.vulnerability = None
        
    def cleanup_timers(self):
        """Clean up any timer scripts attached to this character."""
        # Clean up roundtime
        roundtime_scripts = self.scripts.get("roundtime_script")
        if roundtime_scripts:
            for script in roundtime_scripts:
                script.stop()
        self.db.roundtime = None
        
        # Clean up vulnerability with proper messaging
        self.cleanup_vulnerability()
        
    def at_server_reload(self):
        """Called when server reloads."""
        self.cleanup_timers()
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        self.cleanup_timers()

    def get_stats(self):
        """
        Get the character's current stats.
        
        Returns:
            dict: All character stats including core and combat stats
        """
        return {
            # Core stats
            "power": self.power,
            "agility": self.agility,
            "speed": self.speed,
            "vitality": self.vitality,
            "resistance": self.resistance,
            "focus": self.focus,
            "discipline": self.discipline,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            # Combat stats
            "attack": self.attack,
            "defense": self.defense,
            "current_health": self.current_health,
            "max_health": self.max_health,
            "experience": self.experience,
            # Skills
            "weapons": self.weapons,
            "shields": self.shields,
            "armor": self.armor,
            "physical_fitness": self.physical_fitness,
            "combat_prowess": self.combat_prowess,
            "evasive_maneuvers": self.evasive_maneuvers
        }

    def add_wound(self, location, wound_desc):
        """
        Add a wound to a specific body location.
        
        Args:
            location (str): Body location to wound
            wound_desc (str): Description of the wound
        """
        if location in self.wounds:
            self.wounds[location].append(wound_desc)

    def heal_wound(self, location, wound_desc):
        """
        Heal a specific wound, potentially leaving a scar.
        
        Args:
            location (str): Body location to heal
            wound_desc (str): Description of the wound to heal
        """
        if location in self.wounds and wound_desc in self.wounds[location]:
            self.wounds[location].remove(wound_desc)
            # 50% chance to leave a scar
            if random.random() < 0.5:
                scar_desc = f"Scar from: {wound_desc}"
                self.scars[location].append(scar_desc)

    def get_wounds(self, location=None):
        """
        Get all wounds or wounds for a specific location.
        
        Args:
            location (str, optional): Specific body location to check
            
        Returns:
            dict or list: All wounds or wounds at specified location
        """
        if location:
            return self.wounds.get(location, [])
        return self.wounds

    def get_scars(self, location=None):
        """
        Get all scars or scars for a specific location.
        
        Args:
            location (str, optional): Specific body location to check
            
        Returns:
            dict or list: All scars or scars at specified location
        """
        if location:
            return self.scars.get(location, [])
        return self.scars

    def gain_experience(self, amount):
        """
        Add experience points to the character.
        
        Args:
            amount (int): Amount of experience to gain
            
        Returns:
            int: Total amount of experience after gain
        """
        self.db.experience = self.db.experience + amount
        self.msg(f"You gain {amount} experience points!")
        return self.db.experience

    def get_weapon_finesse(self):
        """
        Get character's weapon finesse talent value.
        Placeholder until talent system is implemented.
        """
        return 0  # Default to 0 until talent system exists

