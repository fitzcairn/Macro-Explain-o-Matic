# Utilities around wowdb
import urllib2,urllib
import socket
import re

# Things that trigger the GCD
from scan_external.util.gcd  import *


# Simple request class for wowdb.com
# No XML interface for this, so straight up HTML scraping.
class WowdbRequest():
    """Plain Request to wowhead api"""
    
    def __init__(self, language="en"):
        self.language = language
        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4"
        
    def get_item(self, item_id):
        try:
            str_data = self.__get_html(item_id, type="item")
        except:
            raise Exception("Item not found.")

        # Parse str_data
        data = {'item_id': item_id }

        # Name
        result = re.compile('h1 id="ctl00_MainContent_PageHeader" title=".+?">(.+?)<').search(str_data)
        data['name'] = result.group(1).strip()

        # Look up if this spell triggers the GCD.
        data["gcd"] = False
        if data["name"] in GCD_ITEMS:
            data["gcd"] = GCD_ITEMS[data["name"]]

        # No slot avaialble in wowdb. :(
        data['slot'] = ''

        # Only return if data is valid.
        if "name" in data               and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful item.")
        return data


    # Spells.
    def get_spell(self, spell_id):
        try:
            str_data = self.__get_html(spell_id, type="spell")
        except:
            raise Exception("Spell not found.")

        # If here, so far, so good.  Check to see if we found
        # something.  If not, raise exception.
        spell_name_obj = re.compile("Spell Not Found")
        results = spell_name_obj.search(str_data)
        if (results is not None): raise Exception("Spell not found.")

        # Ok, now check to ensure that it was discovered in-game.
        # Lots of spells don't have this tag, so we don't want them.
        spell_name_obj = re.compile("Discovered</span> in")
        results = spell_name_obj.search(str_data)
        # We WANT this string to be present.
        if (results is None): raise Exception("Spell likely spurious.")

        # Parse str_data
        data = {'spell_id': spell_id }

        # Name
        result = re.compile('h1 id="ctl00_MainContent_PageHeader" title=".+?">(.+?)<').search(str_data)
        data['name'] = result.group(1).strip()

        # Look up if this spell triggers the GCD.
        data["gcd"] = True
        if data["name"] in NO_GCD_SPELLS:
            data["gcd"] = NO_GCD_SPELLS[data["name"]]

        # Rank
        result = re.compile('class=r0>Rank (\d+)<').search(str_data)
        data['rank'] = ''
        if result: 
            data['rank'] = result.group(1)

        # Self cast?
        result = re.compile('<small>\(Self Only\)</small>').search(str_data)
        data['self'] = False
        if result: 
            data['self'] = True

        # Only return if data is valid.
        if "name" in data               and \
               data["name"] is not None    and \
               "TEST" not in data["name"]  and \
               "OLD" not in data["name"]   and \
               "Alex" not in data["name"]:
            return data
        raise Exception("Not a useful spell.")
        return data


    # Get data from wowdb.
    def __get_html(self, id, type="item"):
        url = "http://www.wowdb.com/%s.aspx?id=%s" % (type, str(id))
        values = {}
        headers = { 'User-Agent' : self.userAgent }
        data = urllib.urlencode(values)
        socket.setdefaulttimeout(2)
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        strFile = response.read()
        return strFile
