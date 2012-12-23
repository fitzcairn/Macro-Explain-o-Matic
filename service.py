'''
Remote access script for Fitzcairns Macro Interpreter.
'''

import os
import cgi
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

# Get macro appengine components
from macro.util                      import decode_text
from macro.render.defs               import URL_MACRO_XML,URL_MACRO_JSON,DO_PROFILE
from macro.render.util               import throttle_action
from macro.render.api.response       import generate_api_response
from macro.exceptions                import OtherError


# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')

class MacroRemoteProcess(webapp.RequestHandler):
    '''
    Handles web UI for macro interpretation.
    '''

    # This is pretty much it for the REST API
    # Saves request parameters in the object.
    def unpack_request(self):
        self.format, self.macro_id = self.request.path[1:].split("/");
        self.format = self.format.lower()
        
        # Required--macro_id.
        if not self.macro_id: 
            # TODO: Make custom exception, define better
            raise Exception("no input")

        # Optional--return format, default to xml
        if not self.format: self.format = 'xml'

    # Just display normal UI, unless a macro id is passed.
    def get(self):
        '''
        Display interpret page.  If a macro id is passed, will load
        macro for editing.
        '''
        # Make sure the request is encoded.
        self.request.encoding = "UTF-8"

        # Decode request
        self.unpack_request()

        # Attempt to respond
        #try:
        self.response.out.write(generate_api_response(path     = _TEMPLATE_PATH,
                                                      macro_id = self.macro_id,
                                                      r_type   = self.format))

        #except Exception, inst:
        #    logging.error("Macro: %s\nError: %s" % (m, inst))
        #    self.response.out.write('')


''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication(
    [(URL_MACRO_XML,  MacroRemoteProcess),
     (URL_MACRO_JSON, MacroRemoteProcess),
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
    print "<pre style='color: GRAY;'>"
    stats = pstats.Stats(prof)
    stats.sort_stats("time")    # Or cumulative
    stats.print_stats(80)    # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    #if DO_PROFILE: profile_main()
    #else: real_main()
    real_main()
