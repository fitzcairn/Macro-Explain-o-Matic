'''
Typeahead lookup.
'''

import cgi
from google.appengine.ext             import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from macro.render.defs                import GET_SEARCH_QUERY,URL_TYPEAHEAD
from macro.data.appengine.macrotag    import get_macro_tags_for


class MacroTypeAhead(webapp.RequestHandler):
  '''
  Handles fast typeahead responses for tag search.
  '''

  # Simple fetch
  def get(self):
    '''
    Return JSON typeahead results.
    '''
    # Get the search term, if there is one.
    term = self.request.get(GET_SEARCH_QUERY)
    ret = get_macro_tags_for(term)
    if ret:
      # Output comma-delimited strings.
      self.response.out.write(",".join(ret))
    else:
      self.response.out.write('')

    
''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
  [
  (URL_TYPEAHEAD, MacroTypeAhead),
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

