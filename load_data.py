import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
from macro.appengine.params import WOWSpell, get_spell_key, WOWItem, get_item_key

class ItemLoader(bulkloader.Loader):
  def __init__(self):
    self.use_id_for_key = False
    
    # Load a WOWItem
    bulkloader.Loader.__init__(self, 'WOWItem',
                             [('name', str),
                              ('slot',
                               lambda x: int(x) if len(x) > 0 else 0),
                              ('gcd', bool),
                              ('id', int),
                              ])

  # Whether or not to load with item ids or name as the keys.
  def initialize(self, filename, loader_opts):
    if loader_opts:
      self.use_id_for_key = True
    bulkloader.CheckFile(filename)

  # Generate a key
  def generate_key(self, i, values):
    if self.use_id_for_key:
      return get_item_key(values[3])
    return get_item_key(values[0])


class SpellLoader(bulkloader.Loader):
  def __init__(self):
    # Load a WOWSpell
    bulkloader.Loader.__init__(self, 'WOWSpell',
                             [('name', str),
                              ('buff', bool),
                              ('gcd', bool),
                              ('id', int),
                              ('rank',
                               lambda x: int(x) if len(x) > 0 else 0),
                              ])

  # Generate a key
  def generate_key(self, i, values):
    return get_spell_key(values[0])


loaders = [ItemLoader, SpellLoader]


