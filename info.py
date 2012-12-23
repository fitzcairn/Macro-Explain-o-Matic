'''
Non-interpreter pages.  Made a seperate file for efficiency, i.e.
decrease the modules loaded.
'''

import os
import cgi
from google.appengine.ext             import webapp
from google.appengine.ext.webapp      import template
from google.appengine.ext.webapp.util import run_wsgi_app

from macro.render.defs                import URL_TOOLS, URL_LINKS, URL_ABOUT, DO_PROFILE
from macro.render.util                import render_template

# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')

class MacroTools(webapp.RequestHandler):
  '''
  Handles displaying tools page.
  '''

  # Simple fetch
  def get(self):
    '''
    Display tools page.
    '''
    links = template.render(os.path.join(_TEMPLATE_PATH,
                                         "tools.template"),
                            {});
    self.response.out.write(render_template("base.template",
                                            path=_TEMPLATE_PATH,
                                            template_vars={'content': links}))
    

class MacroLinks(webapp.RequestHandler):
  '''
  Handles displaying links page.
  '''

  # Simple fetch
  def get(self):
    '''
    Display links page.
    '''
    links = template.render(os.path.join(_TEMPLATE_PATH,
                                         "links.template"),
                            {});
    self.response.out.write(render_template("base.template",
                                            path=_TEMPLATE_PATH,
                                            template_vars={'content': links}))
    

class MacroAbout(webapp.RequestHandler):
  '''
  Handles displaying about page.
  '''

  # Simple fetch
  def get(self):
    '''
    Display links page.
    '''
    about = template.render(os.path.join(_TEMPLATE_PATH,
                                         "about.template"),
                            {});
    self.response.out.write(render_template("base.template",
                                            path=_TEMPLATE_PATH,
                                            template_vars={'content': about}))
    
''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
  [(URL_LINKS, MacroLinks),
   (URL_ABOUT, MacroAbout),
   (URL_TOOLS, MacroTools),
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
  stats.sort_stats("time")  # Or cumulative
  stats.print_stats(80)  # 80 = how many to print
  # The rest is optional.
  # stats.print_callees()
  # stats.print_callers()
  print "</pre>"

if __name__ == "__main__":
  if DO_PROFILE: profile_main()
  else: real_main()

