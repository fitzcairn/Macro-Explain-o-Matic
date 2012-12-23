'''
Datastore methods for saving a macro.
'''

import re
import logging
import urllib
import os
from google.appengine.api               import memcache
from google.appengine.ext               import db

from macro.util                         import encode
from macro.exceptions                   import InvalidSearchError
from macro.data.appengine.gated_counter import init_count, get_count, incr_count
from macro.data.appengine.macrotag      import save_macro_tags


# Memcached prefix
_MCD_PREFIX = ''
try:
    _MCD_PREFIX = os.environ["CURRENT_VERSION_ID"]
except:
    pass

# Default key defs
_MACRO_KEY      = "m%s"
_MACRO_COUNTER  = "_macro"

# The saved macro information from the database.  Fairly light, doesn't
# change ever = long TTL (12hrs)
_MEMCACHED_SAVED_MACRO = 43200

# Search Memcache times
_MEMCACHED_SEARCH = 60
_MEMCACHED_CURSOR = 300  # Much lighter, save longer

# Number of search results to give back
_NUM_RESULTS=10

# Max length of string fields to return for search results
_MAX_RESULT_ENTRY_LEN = 64

# Failsafe max query length
_MAX_QUERY_LENGTH = 32

# Rating max
MAX_RATING = 5


# Datastore class for macro index
class MacroIndex(db.Model):
    ''' Macro index for creating tinyurls.  '''
    curr_index = db.IntegerProperty(required=True,
                                    default=0)


# Datastore class for macros.
class SavedMacro(db.Model):
    ''' Wrapper around a bigtable class for saving macros.
    Key for this class is the encoded count.'''

    # The macro
    macro = db.TextProperty(required=True)

    # Description
    notes = db.TextProperty()

    # Title of the macro
    title = db.StringProperty()
    
    # Character name
    name = db.StringProperty()

    # Client version
    version = db.StringProperty(required=True)
    
    # Possible values are enumerated in template
    server  = db.StringProperty()
    classes = db.ListProperty(str, required=True)

    # This will come from both a set and user input.
    tags    = db.ListProperty(str, required=True)

    # Encoded link for this macro, from the sharded count.
    index   = db.IntegerProperty(required=True, default=0)
    link_id = db.StringProperty(required=True)

    # Rating, a running sum.
    rating    = db.IntegerProperty(default=0)
    num_rates = db.IntegerProperty(default=0)
    
    # Views, a count.
    views     = db.IntegerProperty(default=0)
    
    # Num. sent to friends
    sends     = db.IntegerProperty(default=0)



class SavedMacroOps(object):
    ''' TODO: write me. '''

    def __init__(self, key):
        ''' Construct object.  Requires a valid SavedMacro
        entity key.  Raises exception on failure.'''
        self.entity = self.get_macro_entity(key)
        if not self.entity:
            raise Exception("Couldn't find macro for %s" % key)


    # Save macro data, returning an encoded id.
    @classmethod
    def save_macro(self, macro, notes, title, name, classes, tags, version, server=''):
        ''' Create a new macro entry in the datastore.
        This function assumes data has already been validated.
        
        Note that this function involves two writes to the datastore
        in order to have a serialized count across all macro entites.
        This sucks donkey balls but ensures a) that we can page through
        macros in search results, and b) we can generate unique ids
        for each macro.
        
        This is a classmethod function, can use without needing a
        SavedMacroOps object.
        
        Parameters:
        Correspond with the params in SavedMacro
        
        '''
        saved_macro = None
        
        # Add the classes to the tags, lower, dedup, and sort the tags
        # prior to saving.
        tags = list(set([t.lower() for t in tags + classes]))
        tags.sort()

        # Get a serialized macro count.
        # Need this in order to get unique encoded links.
        # Only needs to be done once on save.
        def index_txn():
            macro_index = MacroIndex.get_by_key_name(_MACRO_COUNTER)
            if macro_index is None:
                macro_index = MacroIndex(key_name=_MACRO_COUNTER)
            new_index = macro_index.curr_index
            macro_index.curr_index += 1
            macro_index.put()    
            return new_index

        # Get macro index for this macro.
        new_index = db.run_in_transaction(index_txn)
        
        # Create a new entity for this macro.
        def txn():
            # Create the macro.  Since macros are never edited, this
            # means the only locking is when a new macro is created,
            # Which hopefully is << the number of times a macro is read.
            enc_index = _MACRO_KEY % encode(int(new_index))
            saved_macro = SavedMacro(key_name = enc_index,
                                     notes    = notes,
                                     macro    = macro,
                                     title    = title,
                                     name     = name,
                                     server   = server,
                                     version  = version,
                                     classes  = classes,
                                     tags     = tags,
                                     index    = new_index,
                                     link_id  = enc_index)
            saved_macro.put()
            return saved_macro
    
        # Create and save, both in datastore and memcache
        saved_macro = db.run_in_transaction(txn)
        memcache.add(cache_key(saved_macro.link_id), saved_macro,
                     _MEMCACHED_SAVED_MACRO)

        # Create the tag entries.
        #logging.debug(tags)
        save_macro_tags(tags)

        # Init the memcache counters.
        init_count(saved_macro.link_id, "views")

        return saved_macro.link_id


    # Fetch a macro instance from the key
    @classmethod
    def get_macro_entity(self, key):
        ''' Gets a macro from its macro_id from memcached or datastore,
        unquotes it, and places it in memcached before returning the
        object.

        Class method, can be called without object.
        '''
        saved_macro = memcache.get(cache_key(key))
        if saved_macro is None:
            saved_macro = SavedMacro.get_by_key_name(key)

        # If we got something, update and save it.
        if saved_macro is not None:
            # Cache it.
            memcache.add(cache_key(key), saved_macro,
                         _MEMCACHED_SAVED_MACRO)    
        return saved_macro


    # Helper function to convert a rating into a data structure
    # for rendering it.  Classmethod.
    @classmethod
    def get_rating_dict(self, rating):
        ''' Given a float rating, translate it into a structure
        for rendering it on a page. '''
        int_rating = int(rating)
        
        # Create a structure for rendering the rating.
        rating_stars = [{'id': i, 'half': False, 'on': (i <= rating), 'off': (i > rating)} for i in range(MAX_RATING+1)[1:]]
        if (int_rating != rating):
            rating_stars[int_rating]['off']  = False
            rating_stars[int_rating]['half'] = True 
        return rating_stars
        

    # Helper function to calculate a rating float.  Classmethod.
    @classmethod
    def get_rating_score(self, rating, num_rates, do_round=True):
        ''' Calculate rating in float form.  If specified,
        this function can round to the nearest half star.'''
        # Determine the rating in stars
        if num_rates == 0: return 0
        stars = (float(rating) / float(num_rates))
        if not do_round: return stars
        # Round to nearest half star
        int_stars = float(int(stars))
        float_stars = stars - int_stars
        if float_stars: float_stars = 1.0 if float_stars > 0.5 else 0.5
        return int_stars + float_stars


    # Handle rating
    def get_rating(self, rating=None, num_rates=None, do_round=True):
        ''' Calculate rating from counters for this entity,
        returning the rating in float form.  If specified,
        this function can round to the nearest half star.'''
        if rating is None or num_rates is None:
            num_rates = get_count(self.entity.link_id, 'num_rates',
                                  entity_val=self.entity.num_rates)
            rating    = get_count(self.entity.link_id, 'rating',
                                  entity_val=self.entity.rating)
        return self.get_rating_score(rating, num_rates, do_round)

            
    def add_rating(self, rating=0):
        ''' Add a rating for a SavedMacro. Returns the rating rounded
        to the largest half star.'''
        #logging.debug("      Adding a rating of %s" % rating)
        
        # Make sure it's a valid rating.
        if (rating < 1) or (rating > MAX_RATING):
            return self.get_rating()
        # Need to update two counters: num_rates and rating.
        else:
            num_rates = incr_count(self.entity.link_id, 'num_rates',
                                   update_count, entity_val=self.entity.num_rates)
            rating    = incr_count(self.entity.link_id, 'rating',
                                   update_count, incr_amt=rating, entity_val=self.entity.rating)
            return self.get_rating(rating, num_rates)


    # Send count.
    def add_to_send_count(self):
        ''' Update send count for a SavedMacro.'''
        #logging.debug("      Incrementing send count.")

        # Execute increment, accounting for older objects without a
        # send field.
        try:
            init_val = self.entity.sends
        except:
            init_val = 0
        ret = incr_count(self.entity.link_id, 'sends',
                         update_count, entity_val=init_val)
        return ret


    def add_to_view_count(self):
        ''' Update view count for a SavedMacro.'''
        #logging.debug("      Incrementing view count.")

        # Execute increment, accounting for older objects without a
        # view field.
        try:
            init_val = self.entity.views
        except:
            init_val = 0
        ret = incr_count(self.entity.link_id, 'views',
                         update_count, entity_val=init_val)
        return ret


    # Saerch for a tag
    @classmethod
    def search(self, tag, page=1, sort="-views", num=_NUM_RESULTS):
        ''' Search macros for a given tag, return num results.
        Returns ([results], is_next_page), where is_next_page is
        True if there are more than this page of results, F otherwise.

        Each result in [results] is an object in dict form for use in
        template output.

        Class method, can be called without object.
        '''
        memcached_ret_key = _MCD_PREFIX  + "%s%s%s%s_results"
        memcached_cur_key = _MCD_PREFIX  + "%s%s%s%s_next"
        memcached_max_key = _MCD_PREFIX  + "%s_max_results" % tag
        is_next_page      = False
        ret_list          = []

        #logging.info("Sorting by: " + sort)

        # Ensure that our input is of the correct size; else, we're
        # done.
        if len(tag) > _MAX_QUERY_LENGTH:
            return (ret_list, is_next_page)

        # Check memcached for results first, fetch after
        mcd_val = memcache.get(memcached_ret_key % (tag, page, num, sort))
        if mcd_val:
            (ret_list, is_next_page) = mcd_val
            return (ret_list, is_next_page)

        # Missed in memcached.   Do search
        q = SavedMacro.all()
        q.filter("tags =", tag)
        q.order(sort)
 
        # Do we have a cursor saved from a previous search?
        page_cursor = memcache.get(memcached_cur_key  % (tag, page, num, sort))
        if page_cursor:
            q.with_cursor(page_cursor)
            ret_list = q.fetch(num)
        # Otherwise, are we getting a page other than 1?
        elif page > 1:
            # Is this page out of bounds?  This is in place
            # to prevent DDOS by deep pagination.
            max_items = memcache.get(memcached_max_key)
            #logging.warning("Max items: %s" % max_items)
            if not max_items or max_items >= (num * (page - 1)):
                # Need to unfortunately fetch a large set of
                # results and get the last page worth.
                # This case should be infrequent.
                orig_list = q.fetch(num * page)
                ret_list = orig_list[(num * (page - 1)):]
                #logging.warning("Saving max: %s" % len(orig_list))

                # Save the max number of results for this query so that
                # repeated out-of-bounds pagination requesets don't DOS
                # the site.
                memcache.add(memcached_max_key, len(orig_list),
                             _MEMCACHED_CURSOR)
            #else:
            #    logging.warning("Max key query averted")
            
        # First page
        else:
            ret_list = q.fetch(num)

        # If the number of results == num, save a cursor and do
        # pagination.
        if len(ret_list) == num:
            new_cursor = q.cursor()
        
            # Do a peekahead to see if there are more results.
            # Unfortunately, can't do this all with one fetch because
            # of the need to save page cursors.
            q.with_cursor(new_cursor)
            if q.fetch(1):
                is_next_page = True
                memcache.add(memcached_cur_key  % (tag, (page+1), num, sort),
                             new_cursor, _MEMCACHED_CURSOR)
                            
        # Put results into dict form.
        ret_list = [{'macro':   trunc(o.macro),        \
                     'title':   o.title or '-', \
                     'id':      o.link_id, \
                     'server':  o.server,              \
                     'tags':    trunc(", ".join(o.tags)), \
                     'rating':  SavedMacroOps.get_rating_score(o.rating, o.num_rates),   \
                     'stars':   SavedMacroOps.get_rating_dict(SavedMacroOps.get_rating_score(o.rating, o.num_rates)),   \
                     'classes': [c.replace(" ", "_") for c in o.classes], \
                     'name':    o.name or '-', \
                     'version': o.version,             \
                     'views':   o.views} for o in ret_list]

        # Save results
        memcache.add(memcached_ret_key  % (tag, page, num, sort),
                     (ret_list, is_next_page), _MEMCACHED_SEARCH)        
        return (ret_list, is_next_page)


# Helper function to update counter fields.
def update_count(key, incr, field):
    entity = SavedMacro.get_by_key_name(key)
    if not entity: raise Exception("Failed fetch for %s" % key)
    val = 0
    if field == 'views':
        entity.views += incr
        val = entity.views
    elif field == 'sends':
        entity.sends += incr
        val = entity.sends
    elif field == 'rating':
        entity.rating += incr
        val = entity.rating
    elif field == 'num_rates':
        entity.num_rates += incr
        val = entity.num_rates
    entity.put()
    return val


# Simple string truncation helper.
t_regexp = re.compile("\r*\n+")
r_regexp = re.compile("([\]\=\:\;\,])")
def trunc(s):
    s = r_regexp.sub(r'\1 ', s)
    s = " ".join(t_regexp.split(s))
    if len(s) < _MAX_RESULT_ENTRY_LEN: return s
    return s[0:(_MAX_RESULT_ENTRY_LEN - 3)] + "..."


# Encode a macro for sending as web data.
#  Unicode -> UTF-8 -> urllib encoded
def encode_text(text):
    return urllib.quote_plus(text.encode('utf-8'))


# Decode a macro sent to us over a post.
#  unicode -> UTF-8 urllib encoded -> UTF-8 -> unicode
def decode_text(text):
    # Appengine has helpfully decoded encoded utf-8 into unicode.
    # First RE-encode it into utf8
    enc_utf8_text = text.encode('utf8')
    # Now decode it with unquote_plus, which also returns utf-8.
    utf8_text = urllib.unquote_plus(enc_utf8_text)
    # NOW decode that into unicode, and return so that life may continue.
    return unicode(utf8_text, 'utf-8')


# Helper to get a macro key for caching
def cache_key(macro_id):
    return _MCD_PREFIX + macro_id
