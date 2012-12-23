''' Simple interface into mmo-champion to fetch wow object data. '''


from django.utils import simplejson as json
import urllib2,urllib
import socket
import re
import logging

from macro.data.wow_obj_base    import WowObject
from macro.interpret.slots      import DATA_TO_GAME_SLOTS


_REQ_OBJ = None
def get_mmochamp_object(obj_id, is_item=False, language="en", use_xml=False):
    global _REQ_OBJ
    if not _REQ_OBJ: _REQ_OBJ = MmoChampionRequest(language, use_xml)
    wow_obj = None
    if is_item:
        wow_obj = _REQ_OBJ.lookup_item(obj_id)
        if wow_obj: return MmoChampItem(wow_obj)
    else:
        wow_obj = _REQ_OBJ.lookup_spell(obj_id)
        if wow_obj: return MmoChampSpell(wow_obj)
    return wow_obj


class MmoChampionRequest():
    """Plain Request to mmo-champion.com"""

    def __init__(self, language, use_xml):
        self.__MMO_CHAMP_ITEM  = "i"
        self.__MMO_CHAMP_SPELL = "s"
        self.language  = language
        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4"
        
    def lookup_spell(self, obj_id):
        return self.__lookup(obj_id, self.__MMO_CHAMP_SPELL)
    def lookup_item(self, obj_id):
        return self.__lookup(obj_id, self.__MMO_CHAMP_ITEM)

    def __lookup(self, obj_id, obj_type):
        if not obj_id: return None
        try:
            name = self.__clean_name(obj_id)
            obj = self.__get(name, obj_type)
            ret_map = obj[0]['fields']
            ret_map['id'] = obj[0]['pk']
            
            # mmo-champion does prefix matching.  Make sure
            # we got exactly what we were looking for.
            if type(name) is int or name == self.__clean_name(ret_map['name']):
                return ret_map
        except:
            pass
        return {}
        
    def __clean_name(self, name):
        if not name: return name
        if type(name) is int: return name

        # Is this an item: lookup?
        if name[0:5].lower() == "item:":
            return int(name[5:])

        # Unfortunately, it also doesn't handle spell ranks well.
        # So, toss these.
        #
        # NOTE: removed to allow spell ranks to be handled via wowhead
        # backup.  If the user is specifically downranking in a macro,
        # then we should at least TRY to be correct.
        #
        #name = re.sub("(Rank \d+)", "", name).strip()

        # mmo-champion encodes spaces as dashes, and doesn't
        # like non-alphanumerics.
        name = re.sub("[^\w\s]", "", name).strip()
        name = re.sub("\s+", "-", name)
        return name


    def __get(self, obj, obj_type):
        ''' Uses JSON to query mmo-champion. '''
        url = "http://db.mmo-champion.com/"+ obj_type +"/" + str(obj) + "/json"
        response = urllib2.urlopen(url)
        return json.loads(response.read())


class MmoChampItem(WowObject):
    ''' Interface into the various backing stores for
    wow spell and item data.'''
    data_keys = ['id', 'name', 'slot']
    def __init__(self, data):
        ''' Init object, saving only the fields we need. '''
        self.is_found = len(data) > 0
        self.data = {}
        for k in self.data_keys:
            if k in data: self.data[k] = data[k]
            else:         self.data[k] = None
    def found(self):
        return self.is_found
    def get_id(self):
        return self.data['id']
    def get_slot(self):
        return self.data['slot']
    def get_name(self):
        return self.data['name']
    def test_item_slotid(self, slot_id=0):
        if self.data['slot'] in DATA_TO_GAME_SLOTS:
            return (slot_id in DATA_TO_GAME_SLOTS[self.data['slot']])
        return False
    def is_item(self):
        return True

class MmoChampSpell(WowObject):
    ''' Interface into the various backing stores for
    wow spell and item data.'''
    data_keys = ['id', 'name', 'category_cooldown_start', 'range_max', 'rank']
    def __init__(self, data={}):
        ''' Init object, saving only the fields we need. '''
        self.is_found = (len(data) > 0)
        self.data = {}
        for k in self.data_keys:
            if k in data: self.data[k] = data[k]
            else:         self.data[k] = None
        # Special processing for rank.
        if self.data['rank']:
            result = re.compile('Rank (\d+)').search(self.data['rank'])
            if result:
                self.data['rank'] = result.group(1)
    def found(self):
        return self.is_found
    def get_id(self):
        return self.data['id']
    def get_name(self):
        return self.data['name']
    def get_rank(self):
        return self.data['rank']
    def trips_gcd(self):
        return self.data['category_cooldown_start'] > 0
    def self_only(self):
        return (self.data['range_max'] is not None and self.data['range_max'] == 0)
    def is_spell(self):
        return True
    def __str__(self):
        return str(self.data)
