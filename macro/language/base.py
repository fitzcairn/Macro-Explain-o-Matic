'''
Base class for classes describing the WoW macro languages, along
with associated shared tools.
'''

# TODO: MAKE IMPORTS EXPLICIT
from macro.util           import *


# Stub function for assembly
# All assembly functions must return a list.
def default_assemble_function(*args):
    return []
    

# Base class for a language primitive
class LanguagePart():
    ''' Base class for all macro language parts.  Each macro part is a
    collection of attriubutes describing the function of the macro
    unit.

    assemble_function: (Optional)
    Reference to a function for assembling the description
    of this function.
    Default: stub defined above.

    token: (Optional)
    Reference to the token this LanguagePart describes.

    desc: (Optional)
    Base of the english description for this macro part.
    If not defined, uses the token data.

    alt_desc: (Optional)
    An alternate description for use in specific cases
    Default None
     
    error_msg: (Optional)
    A macro part-specific error message.
    Default None

    '''
    # Static attrs hash for overriding by subclasses.
    attr_defaults = {}
    
    # Constructor saves the shared attributes.
    def __init__(self, **kargs):
        self.__kargs    = kargs

        # Add default values for base-required attributes.
        self.attr_defaults['token']             = None
        self.attr_defaults['desc']              = ''
        self.attr_defaults['alt_desc']          = ''
        self.attr_defaults['error_msg']         = ''
        if 'assemble_function' not in self.attr_defaults:
            self.attr_defaults['assemble_function'] = default_assemble_function


    # Overridding __getattr__ allows for lazy init of class objects.
    # This is important since we create a lot of objects at execution
    # time.  An object-specific list of attributes is saved at object
    # create time.  A static class-specific list of default attribute
    # vals is used to init with defaults where no object-specific
    # attribute value is given.
    def __getattr__(self, name):
        if name in self.attr_defaults:
            if name in self.__kargs:
                val = self.__kargs[name]
            else:
                val = self.attr_defaults[name]
            self.__dict__[name] = val
            return val
        raise AttributeError("%s doesn't contain attribute %s." % \
                             (self.__class__, name))


    # Debug--output language part attributes
    def __str__(self):
        return str(self.__kargs)

        
