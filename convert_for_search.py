#!/usr/bin/python
import getpass
import sys
import datetime
import logging
import time
import csv
import copy

#sys.path.append("C:\Program Files\Google\google_appengine")
#sys.path.append("C:\Program Files\Google\google_appengine\lib\yaml\lib")

from google.appengine.ext            import db
from macro.data.appengine.macrotag   import save_macro_tags
from macro.data.appengine.savedmacro import SavedMacro
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext            import db

# Backoff time on timeout, in seconds.
_BACKOFF = 3

# Number of retries allowed on failure
_MAX_RETRY = 3

# Simple auth function.
def auth_func():
    return raw_input('Username:'), getpass.getpass('Password:')


# Helper to output entities:
def str_entity(e, is_item=False):
    if is_item: return "name: [%s] slot: [%s] id: [%s]" % \
       (e.name, e.slot, e.id)
    return "name: [%s] buff: [%s] gcd: [%s] id: [%s] rank: [%s]" % \
           (e.name, e.buff, e.gcd, e.id, e.rank)


# Helper to manage retries on urlib, etc exception
def do_w_retry(func, arg=None, num_retries=_MAX_RETRY):
    tries = 0
    while True:
        try:
            if arg: return func(arg)
            else:   return func()
        except Exception, inst:
            logger.info("FAIL: attempt %s of %s returned an error." % ((tries + 1), num_retries))
            logger.info("Got exception: %s" % inst)
            logger.info("Function: %s" % func)
            logger.info("Args: %s" % arg)
            logger.info("  Sleeping %s sec, then retrying..." % _BACKOFF)
            time.sleep(_BACKOFF)
            tries += 1
            if tries >= num_retries:
                logging.error("Dying with %s" % inst)
                raise
            pass    
    

# Taken from example online.
class Mapper(object):
    # Subclasses should replace this with a model class (eg,
    # model.Person).
    KIND = None

    # Subclasses can replace this with a list of (property, value)
    # tuples to filter by.
    FILTERS = []
    
    def map(self, entity):
        """Updates a single entity.
     
        Implementers should return a tuple containing two iterables
        (to_update, to_delete).
        """
        return ([], [])

    def get_query(self):
        """Returns a query over the specified kind, with any appropriate
        filters applied."""
        q = self.KIND.all()
        for prop, value in self.FILTERS:
            q.filter("%s =" % prop, value)
        q.order("__key__")
        return q

    def run(self, batch_size=100):
        """Executes the map procedure over all matching entities."""
        q = self.get_query()
        entities = do_w_retry(q.fetch, batch_size)
        count = 0
        while entities:
            to_put = []
            to_delete = []
            for entity in entities:
                map_updates, map_deletes = self.map(entity)
                to_put.extend(map_updates)
                to_delete.extend(map_deletes)
            if to_delete:
                do_w_retry(db.delete, to_delete)
            if to_put:
                do_w_retry(db.put, to_put)
            q = do_w_retry(self.get_query)
            q.filter("__key__ >", entities[-1].key())
            entities = do_w_retry(q.fetch, batch_size)
            count += 1
            logger.info("Handled batch %s..." % count)


class MacroUpdater(Mapper):
    ''' Updater for SavedMacro entities. '''
    def __init__(self):
        self.KIND = SavedMacro
          
    def map(self, entity):
        ''' Lowercase and add/clean the tags field,
        and create the MacroTags objects for this macro.
        '''
        # Add the classes to the tags, lower, dedup, and sort the tags
        # prior to saving.
        tags = list(set([t.lower() for t in entity.tags + entity.classes]))
        tags.sort()

        # Update the entity and add for writing back.
        entity.tags = tags

        # Create tags for the macro.
        save_macro_tags(tags)
        return ([entity], [])
    

#### MAIN #####
if __name__ == "__main__":
    # Set up the logger
    logging.basicConfig(level=logging.INFO,
                        format='%(message)s')
    logger = logging.getLogger('upload')

    # Parse command-line options.
    if len(sys.argv) < 3:
        print "Usage: %s app_id host" % (sys.argv[0],)
        sys.exit(1)
    app_id    = sys.argv[1]
    if len(sys.argv) > 2:
        host = sys.argv[2]
    else:
        host = '%s.appspot.com' % app_id

    # Report what we're doing.
    logger.info("About to update SavedMacros for app %s on host %s" %\
                 (app_id, host))

    # Use local dev server by passing in as parameter:  
    # servername='localhost:8080'  
    # Otherwise, remote_api assumes you are targeting APP_NAME.appspot.com  
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

    # Update data.
    logger.info("Updating existing data...")
    MacroUpdater().run()

    # Done.
    logger.info("Process complete.")
