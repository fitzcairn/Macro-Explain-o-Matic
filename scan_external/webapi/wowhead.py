import urllib2,urllib
from xml.dom.minidom import parse, parseString
import socket
import re
import logging

# Things that trigger the GCD
from scan_external.util.gcd  import *

# Simple request class for Wowhead.com
class WowheadRequest():
    """Plain Request to wowhead api"""
    
    def __init__(self,language):
        self.language = language
        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4"
        self.tree = None
        
    def get_item(self, item_id):
        # Fetch the XML from wowhead.
        try:
            self.tree = parseString( self.__get_xml(item_id, type="item") )
        except:
            raise Exception("Item not parseable")

        # Did wowhead return an error?
        try:
            error = self._getNode("error",0,0)
        except:
            pass
        if error:
            raise Exception("Got an error back from wowhead")

        data = {}
        data["item_id"] = item_id
        data["name"] = self._getNode("name",0,0)
        data["slot"] = self._getAttribute("inventorySlot",0,"id")

        # Look up if using this item triggers the GCD.
        data["gcd"] = False
        if data["name"] in GCD_ITEMS: data["gcd"] = GCD_ITEMS[data["name"]]

        # Only return if data is valid.
        if "name" in data               and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful item.")

    
    # Spells.
    def get_spell(self, spell_id):
        # Unfortunately, there is no XML for spells, so we'll get
        # what we need by stripping the page.
        page = None
        try:
            page = self.__get_xml(spell_id, type="spell")
        except:
            raise Exception("Couldn't fetch spell page.")
        data = {"spell_id": spell_id,
                "self": False,
                "gcd": True}

        # Filter spells to things cast by players only.
        #
        # Triggered by a proc
        # Test: http://www.wowhead.com/?spell=35079
        # vs
        # http://www.wowhead.com/?spell=34477
        #
        # Used by an item
        # Test: http://www.wowhead.com/?spell=14253
        # vs
        # http://www.wowhead.com/?spell=2893
        #
        # Used by an npc
        # Test: http://www.wowhead.com/?spell=61693
        for f in ("triggered-by", "used-by-item", "used-by-npc"):
            spell_name_obj = re.compile(f)
            results = spell_name_obj.search(page)
            if (results is not None):
                raise Exception("Spell not found.")

        # If there is a "taught by" field, mark this spell as taught.
        # This helps clear the crap out of uncategorized spells.
        # Note that some spells are gained through talents.
        # Test: http://www.wowhead.com/?spell=34074
        # vs (non-preferred)
        # http://www.wowhead.com/?spell=34075
        spell_name_obj = re.compile("taught-by-npc")
        results = spell_name_obj.search(page)
        if (results is not None):
            data["taught"] = True

        # Use regular expressions to fill in name.
        spell_name_obj = re.compile("name\:\s+'(.+?)'\}")
        results = spell_name_obj.search(page)
        if (results is not None):
            data["name"] = results.group(1).replace("\\'", "'")
        else:
            raise Exception("Couldn't find spell.")

        # Get whether or not its a self-cast
        spell_name_obj = re.compile("<small>\(Self\)</small>")
        results = spell_name_obj.search(page)
        if (results is not None):
            data["self"] = True
            
        # Look up if this spell triggers the GCD.
        data["gcd"] = True
        if data["name"] in NO_GCD_SPELLS:
            data["gcd"] = NO_GCD_SPELLS[data["name"]]
      
        # Get the rank, if there is one
        data["rank"] = ''
        spell_name_obj = re.compile('<b class="q0">Rank (\d+)</b>')
        results = spell_name_obj.search(page)
        if (results is not None):
            try:
                data["rank"] = int(results.group(1))
            except:
                pass

        # Only return if data is valid.
        if "name" in data               and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful spell.")
        return data

        
    def __get_xml(self, id, type="item"):
        strFile = ""
        try:
            url = "http://www.wowhead.com/?"+type+"="+str(id)+"&xml"
            values = {}
            headers = { 'User-Agent' : self.userAgent }
            data = urllib.urlencode(values)
            socket.setdefaulttimeout(2)
            req = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(req)
            strFile = response.read()
        except Exception, e:
            raise WowHeadConectionProblem()
        finally:
            return strFile
    
    def _getAttribute(self,node,number,attribute):
        try:
            return self.tree.getElementsByTagName(node)[number].getAttribute(attribute)
        except:
            return None
        
    def _getNode(self,node,number,child):
        try:
            return self.tree.getElementsByTagName(node)[number].childNodes[child].data
        except:
            return None
