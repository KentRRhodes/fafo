"""
Monsters

Hostile NPCs that can engage in combat with players.
This module contains various monster types and base classes.
"""
from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty
from .objects import ObjectParent
from evennia import GLOBAL_SCRIPTS
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
    """
    
    # Core Stats with default values
    power = AttributeProperty(default=1, autocreate=True)
    agility = AttributeProperty(default=1, autocreate=True)
    speed = AttributeProperty(default=1, autocreate=True)
    vitality = AttributeProperty(default=1, autocreate=True)
    resistance = AttributeProperty(default=1, autocreate=True)
    focus = AttributeProperty(default=1, autocreate=True)
    discipline = AttributeProperty(default=1, autocreate=True)
    intelligence = AttributeProperty(default=1, autocreate=True)
    wisdom = AttributeProperty(default=1, autocreate=True)
    charisma = AttributeProperty(default=1, autocreate=True)
    
    # Basic combat stats with default values
    @property
    def attack(self):
        """Calculate attack value from agility and speed."""
        return self.agility + self.speed
        
    defense = AttributeProperty(default=1, autocreate=True)
    max_health = AttributeProperty(default=10, autocreate=True)  # Keeping this higher for playability
    current_health = AttributeProperty(default=10, autocreate=True)  # Matching max_health
    experience = AttributeProperty(default=1, autocreate=True)  # Default XP value when defeated
    
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
        
    def get_stats(self):
        """
        Get the monster's current stats.
        
        Returns:
            dict: All monster stats including core and combat stats
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
            "experience": self.experience
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
