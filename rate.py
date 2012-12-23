'''
Handle asynchronous rating.
'''

import os
import cgi
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from macro.render.defs               import *
from macro.data.appengine.savedmacro import SavedMacroOps


class MacroRate(webapp.RequestHandler):
  '''
  Handles fast asynchronous macro rating.
  '''

  def __do_rating(self, macro_id, rating):
    ''' Helper function to do the rating. '''
    # Increment macro rating, and return the
    # rating, rounded to the nearest half-star.
    saved_macro = SavedMacroOps(macro_id)
    return saved_macro.add_rating(rating)
        
  def get(self):
    '''
    Save rating, and return the new rating.
    '''
    try:
      self.response.out.write(self.__do_rating(self.request.get(GET_MACRO_LINK),
                                               int(self.request.get(GET_MACRO_RATING))))
    except:
      self.response.out.write('')

    
''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
  [
  (URL_RATE, MacroRate),
  ],
  debug=False)


def real_main():
  run_wsgi_app(application)

def profile_main():
  # This is the main function for profiling 
  # We've renamed our original main() above to real_main()
  import cProfile, pstats
  prof = cProfile.Profile()
  prof = prof.runctx("real_main()", globals(), locals())
  print "<pre>"
  stats = pstats.Stats(prof)
  stats.sort_stats("time")  # Or cumulative
  stats.print_stats(80)  # 80 = how many to print
  # The rest is optional.
  # stats.print_callees()
  # stats.print_callers()
  print "</pre>"

if __name__ == "__main__":
  real_main()

