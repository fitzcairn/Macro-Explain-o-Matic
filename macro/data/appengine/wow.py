'''
Datastore methods for looking up items.
'''

import logging
from google.appengine.ext import db

from macro.data.wow_obj_base  import WowObject
from macro.data.appengine.defs import DATA_KEY

class WOWItem2(db.Model):
    ''' Wrapper around a bigtable class for Items.
    Local to this module only. '''
    id            = db.IntegerProperty(required=True)
    name          = db.StringProperty(required=True)
    equipSlot     = db.ListProperty(int, default=[])

    # Don't need
    #subclass      = db.StringProperty(required=True)
    #class         = db.StringProperty(required=True)
    #link          = db.StringProperty(required=True)
    #quality       = db.StringProperty(required=True)
    #iLevel        = db.IntegerProperty()
    #reqLevel      = db.IntegerProperty()
    #maxStack      = db.IntegerProperty()
    #texture       = db.StringProperty(required=True)
    #vendorPrice   = db.IntegerProperty()


class WOWSpell2(db.Model):
    ''' Wrapper around a bigtable class for Spells.
    Local to this module only. '''
    id          = db.IntegerProperty(required=True)
    name        = db.StringProperty(required=True)
    rank        = db.StringProperty() # Not all spells have ranks
    isFunnel    = db.BooleanProperty() # If present, true else false
    castingTime = db.IntegerProperty(required=True)
    minRange    = db.IntegerProperty(required=True)
    maxRange    = db.IntegerProperty(required=True)

    # Don't need
    #icon        = db.StringProperty(required=True)
    #powerCost   = db.IntegerProperty(required=True)
    #powerType   = db.StringProperty(required=True)


# Centralized key functions.
def get_item_key(name):
    return _normalize(name)
def get_spell_key(name):
    return _normalize(name)

def get_item(name):
    '''Retrieve an item from the datastore, and cache it in memcache.'''
    if len(name) == 0: return None
    key  = get_item_key(name)
    item = WOWItem2.get_by_key_name(key)
    return item

def get_spell(name):
    '''Retrieve a spell from the datastore, and cache it in memcache.'''
    if len(name) == 0: return None
    key   = get_spell_key(name)
    spell = WOWSpell2.get_by_key_name(key)
    return spell

# Helper for normalizing parameters to do the best possible matching.
def _normalize(name):
    return name.lower()
    #return ''.join([c.lower() for c in name if c.isalnum()])


class DatastoreItem(WowObject):
    ''' Wrapper around item data from Datastore '''
    def __init__(self, data):
        self.data = data
    def found(self):
        return (self.data is not None)
    def get_name(self):
        return self.data.name
    def get_id(self):
        return self.data.id
    def get_slot(self):
        ''' Returns the wow slot.  NOTE: can return a set.'''
        if self.data: return self.data.equipSlot
    def test_item_slotid(self, slot_id=0):
        ''' Test to see if this item is equippable in this slot.'''
        if self.data and self.data.equipSlot is not None:
            return (slot_id in self.data.equipSlot)
        return False
    def is_item(self):
        return True

class DatastoreSpell(WowObject):
    ''' Wrapper around spell data.'''
    def __init__(self, data):
        self.data  = data
    def found(self):
        return (self.data is not None)
    def get_name(self):
        return self.data.name
    def get_id(self):
        return self.data.id    
    def self_only(self):
        ''' Self-buff?  True/False. '''
        # TODO: clean data, blizzard really fucks this up with GetSpellInfo
        #if self.data: return (self.data.maxRange == 0)
        return False
    def get_rank(self):
        ''' Spells with no ranks return None.
        NOTE: Returns a string now.'''
        if self.data and self.data.rank: return self.data.rank
        return None
    def trips_gcd(self):
        ''' Whether or not the spell trips the GCD.
        Most spells do, with only a few known to NOT trip it.'''
        # TODO: where to get this?
        return True
    def is_spell(self):
        return True
    

# Easy fetch helper for upstream callers.
def get_datastore_object(obj_id, is_item):
    obj = None
    if is_item:
        obj = get_item(obj_id)
        if obj:
            return DatastoreItem(obj)
    else:
        obj = get_spell(obj_id)
        if obj:
            return DatastoreSpell(obj)
    return obj
