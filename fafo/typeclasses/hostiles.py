"""
Monsters

Hostile NPCs that can engage in combat with players.
This module contains various monster types and base classes.
"""
from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty
from evennia import GLOBAL_SCRIPTS
from .objects import ObjectParent
import random

class Hostile(ObjectParent, DefaultCharacter):
    """
    Base hostile monster class.
    
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
        attack (int): Monster's base attack value
        defense (int): Monster's base defense value
        max_health (int): Maximum health points
        current_health (int): Current health points
        experience (int): Experience value when defeated
        left_hand (Object): Item held in left hand
        right_hand (Object): Item held in right hand
        wounds (dict): Current wounds on different body parts
        scars (dict): Permanent scars on different body parts
        
        # Skills
        weapons (int): Proficiency with weapons
        shields (int): Proficiency with shields
        armor (int): Proficiency with armor
        physical_fitness (int): Physical fitness level
        combat_prowess (int): Combat prowess level
        evasive_maneuvers (int): Evasive maneuvers proficiency
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
    
    # Combat stats
    base_defense = AttributeProperty(default=1, autocreate=True)
    max_health = AttributeProperty(default=100, autocreate=True)
    current_health = AttributeProperty(default=100, autocreate=True)
    experience = AttributeProperty(default=1, autocreate=True)

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
        return self.get_modified_stat('weapons')
        
    @property
    def shields(self):
        return self.get_modified_stat('shields')
        
    @property
    def armor(self):
        return self.get_modified_stat('armor')
        
    @property
    def physical_fitness(self):
        return self.get_modified_stat('physical_fitness')
        
    @property
    def combat_prowess(self):
        return self.get_modified_stat('combat_prowess')
        
    @property
    def evasive_maneuvers(self):
        return self.get_modified_stat('evasive_maneuvers')

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
        default={
            "head": [], "neck": [], "chest": [], "back": [],
            "abdomen": [], "right_arm": [], "left_arm": [],
            "right_hand": [], "left_hand": [], "right_leg": [],
            "left_leg": [], "right_eye": [], "left_eye": []
        },
        autocreate=True
    )
    
    scars = AttributeProperty(
        default={
            "head": [], "neck": [], "chest": [], "back": [],
            "abdomen": [], "right_arm": [], "left_arm": [],
            "right_hand": [], "left_hand": [], "right_leg": [],
            "left_leg": [], "right_eye": [], "left_eye": []
        },
        autocreate=True
    )

    def at_object_creation(self):
        """
        Called when object is first created.
        """
        super().at_object_creation()
        self.db.corpse = False
        self.db.inactive = False
        self.db.roundtime = None

    def cleanup_roundtime(self):
        """Clean up any roundtime scripts attached to this hostile."""
        roundtime_scripts = self.scripts.get("roundtime_script")
        if roundtime_scripts:
            for script in roundtime_scripts:
                script.stop()
        self.db.roundtime = None
        
    def at_server_reload(self):
        """Called when server reloads."""
        self.cleanup_roundtime()
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        self.cleanup_roundtime()

    def is_alive(self):
        """Check if this hostile is alive and attackable."""
        return not (self.db.corpse or self.db.inactive)

    def get_stats(self):
        """
        Get the monster's current stats and skills.
        
        Returns:
            dict: All monster stats and skills
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
        
    def heal(self, amount):
        """
        Heal the monster by the given amount, not exceeding max_health.
        
        Args:
            amount (int): Amount of health to restore
            
        Returns:
            int: Amount of health actually restored
        """
        old_health = self.current_health
        self.current_health = min(self.current_health + amount, self.max_health)
        return self.current_health - old_health
        
    def take_damage(self, amount):
        """
        Deal damage to the monster.
        
        Args:
            amount (int): Amount of damage to deal
            
        Returns:
            int: Amount of damage actually dealt
        """
        old_health = self.current_health
        self.current_health = max(0, self.current_health - amount)
        return old_health - self.current_health

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

    def npc_attack(self, target):
        """
        Initiate an attack against a target, respecting roundtime.
        
        Args:
            target (Object): The target to attack
            
        Returns:
            bool: Whether the attack was attempted
        """
        combat = GLOBAL_SCRIPTS.combat_handler
        in_roundtime, _ = combat.is_in_roundtime(self)
        if in_roundtime:
            return False
            
        hit, damage, roundtime = combat.process_attack(self, target)
        return True

    def gain_experience(self, amount):
        """
        Add experience points to the hostile NPC.
        
        Args:
            amount (int): Amount of experience to gain
            
        Returns:
            int: Total amount of experience after gain
        """
        self.db.experience = self.db.experience + amount
        return self.db.experience
