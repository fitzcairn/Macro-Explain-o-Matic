''' Simple interface into mmo-champion to fetch wow object data. '''


from django.utils import simplejson as json
import urllib2,urllib
import socket
import re
import logging

# Make use of the object already written for live lookups.
from macro.data.mmochampion.wow import get_mmochamp_object
# Things that trigger the GCD
from scan_external.util.gcd  import *


class MmoChampionRequest():
    """Plain Request to mmo-champion.com"""

    def __init__(self, language="en"):
        self.language  = language
        
    def get_spell(self, spell_id):
        spell = get_mmochamp_object(spell_id, is_item=False,
                                    language=self.language)
        if not spell or not spell.found():
            raise Exception("Spell not found!")
        
        data = {'spell_id': spell_id,
                'name':     spell.get_name(),
                'rank':     spell.get_rank(),
                'gcd':      spell.trips_gcd(),
                'self':     spell.self_only()}
        if not data['rank']: data['rank'] = ''

        # Only return if data is valid.
        if "name" in data               and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful spell.")
        return data
               


    def get_item(self, item_id):
        item = get_mmochamp_object(item_id, is_item=True,
                                    language=self.language)
        if not item or not item.found():
            raise Exception("Spell not found!")
        
        data = {'item_id':  item_id,
                'name':     item.get_name(),
                'slot':     item.get_slot(),
                }

        # Look up if using this item triggers the GCD.
        data["gcd"] = False
        if data["name"] in GCD_ITEMS: data["gcd"] = GCD_ITEMS[data["name"]]
        # Only return if data is valid.
        if "name" in data                  and \
               data["name"] != ""          and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful .")
        return data
