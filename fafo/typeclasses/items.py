"""
Items Module

Contains the base Item class and all item type subclasses.
"""
from evennia.objects.objects import DefaultObject
from evennia.typeclasses.attributes import AttributeProperty
from .objects import ObjectParent

class Item(ObjectParent, DefaultObject):
    """Base class for all items."""
    
    def at_object_creation(self):
        """Called when object is first created."""
        super().at_object_creation()

class Weapon(Item):
    """Weapon items that can be used in combat."""
    pass

class Shield(Item):
    """Shield items for defense."""
    pass

class Armor(Item):
    """Armor items for protection."""
    pass

class Container(Item):
    """Items that can hold other items."""
    pass

class Clothing(Item):
    """Wearable items."""
    pass

class Widget(Item):
    """Miscellaneous items with special functions."""
    pass