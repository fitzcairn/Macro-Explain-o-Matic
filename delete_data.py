#!/usr/bin/python
import getpass
import sys
import datetime
import logging
import time

sys.path.append("C:\Program Files\Google\google_appengine")
sys.path.append("C:\Program Files\Google\google_appengine\lib\yaml\lib")

from google.appengine.ext import db
from macro.appengine.params import WOWSpell, WOWItem
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

# Backoff time on timeout, in seconds.
_BACKOFF = 3

# Set up the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s')
logger = logging.getLogger()

# Simple auth function.
def auth_func():
  return raw_input('Username:'), getpass.getpass('Password:')

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
    entities = q.fetch(batch_size)
    count = 0
    while entities:
      to_put = []
      to_delete = []
      for entity in entities:
        map_updates, map_deletes = self.map(entity)
        to_put.extend(map_updates)
        to_delete.extend(map_deletes)
      if to_put:
        db.put(to_put)
      if to_delete:
        retry = True
        while retry:
          try:
            db.delete(to_delete)
            retry = False
          except Exception, inst:
            logging.info("Got exception: %s" % inst)
            logging.info("Timeout.  Sleeping %s sec, then retrying..." % _BACKOFF)
            time.sleep(_BACKOFF)
            pass
      q = self.get_query()
      q.filter("__key__ >", entities[-1].key())
      entities = q.fetch(batch_size)
      count += 1
      logging.info("Handled batch %s..." % count)

class WOWSpellDeleter(Mapper):
  ''' Deleter for WOWSpell entities. '''
  KIND = WOWSpell
  def map(self, entity):
    return ([], [entity])

class WOWItemDeleter(Mapper):
  ''' Deleter for WOWSpell entities. '''
  KIND = WOWItem
  def map(self, entity):
    return ([], [entity])


# Parse command-line options.
if len(sys.argv) < 4:
  print "Usage: %s app_id [host] [spell|item]" % (sys.argv[0],)
  sys.exit(1)
app_id = sys.argv[1]
if len(sys.argv) > 2:
  host = sys.argv[2]
else:
  host = '%s.appspot.com' % app_id
if len(sys.argv) > 3:
  del_type = sys.argv[3]

# Use local dev server by passing in as parameter:  
# servername='localhost:8080'  
# Otherwise, remote_api assumes you are targeting APP_NAME.appspot.com  
remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

# Delete data.
if del_type[0] == "s" or del_type[0] == "S":
  deleter = WOWSpellDeleter()
  deleter.run()
elif del_type[0] == "i" or del_type[0] == "I":
  deleter = WOWItemDeleter()
  deleter.run()
else:
  raise Exception("type should be either spell or item.")
