'''
Search and browse.
'''

import os
import cgi
import logging
from google.appengine.ext             import webapp
from google.appengine.ext.webapp      import template
from google.appengine.ext.webapp.util import run_wsgi_app

from macro.render.defs                import *
from macro.render.encoding            import unescape
from macro.exceptions                 import NoInputError
from macro.render.page.search         import generate_search_page
from macro.render.page.error          import generate_error_page

# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')


class MacroSearch(webapp.RequestHandler):
    '''
    Handles search by tag.
    '''

    # Helper to render a search page.
    def __render_search_page(self):
        # Get the macro page, catching exceptions
        try:
            q = self.request.get(GET_SEARCH_QUERY)
            s = self.request.get(GET_SEARCH_SORT) or "-views"
            if self.request.get(FORM_QUERY_ESC): q = unescape(q)
            page = generate_search_page(_TEMPLATE_PATH,
                                        q.strip(),
                                        self.request.get(FORM_SEARCH_PAGE),
                                        sort=s)
          
        except NoInputError, inst:
            page = generate_error_page(_TEMPLATE_PATH, error=inst)
        except Exception, inst:
            logging.error(inst)
            page = generate_error_page(_TEMPLATE_PATH)
        self.response.out.write(page)


    # Handle a search.
    def get(self):
        '''
        Display search results page.
        '''

        # Get the search term, if there is one.
        return self.__render_search_page()

        
''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
    [(URL_SEARCH,        MacroSearch),
     ],
    debug=True)


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
    stats.sort_stats("time")    # Or cumulative
    stats.print_stats(80)    # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"

if __name__ == "__main__":
    #if DO_PROFILE: profile_main()
    #else: real_main()
    profile_main()
