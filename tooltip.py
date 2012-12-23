'''
Typeahead lookup.
'''

import os
import cgi
import logging
from google.appengine.ext             import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from macro.render.defs                import URL_MACRO_TT, GET_MACRO_LINK
from macro.render.page.tooltip        import generate_tooltip


# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')


class MacroToolTip(webapp.RequestHandler):
  '''
  Handles fast tooltip generation.
  '''

  # Simple fetch and display
  def get(self):
    '''
    Return rendered tooltip for macroid in url.
    '''
    # Generate tooltip, or nothing on error.
    tt  = ''
    try:
      # Get the macro id
      mid = self.request.get(GET_MACRO_LINK)
      tt = generate_tooltip(_TEMPLATE_PATH, mid)
    except Exception, inst:
      logging.error(inst)
    self.response.out.write(tt)

    
''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
  [
  (URL_MACRO_TT, MacroToolTip),
  ],
  debug=False)


def real_main():
  run_wsgi_app(application)

if __name__ == "__main__":
  real_main()

