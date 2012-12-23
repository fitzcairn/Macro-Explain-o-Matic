'''
Collection of utility methods.
'''

import re
import string
import urllib

# Our modules
from macro.logger    import *

# Constants
NULL_POSITION = -1
NULL_TOKEN_ID = -1
NULL_TOKEN    = -1


# Clean up a macro.
# TODO: clean up unneeded spaces after punctuation!!
def clean_macro(macro, report_spaces=False, debug=False):
    # Normalize all spaces in the macro
    space_norm_re = re.compile('(\s{2,})')
    new_cmd, num_norm = space_norm_re.subn(' ', macro)
    if (num_norm > 0 and debug):
        logger.debug("Normalized spaces %s times." % (num_norm))
        logger.debug("\nOld Command: %s\nNew command: %s." % (macro, new_cmd))

    # Strip off begining/trailing spaces and newlines
    if report_spaces: return (new_cmd.strip(), num_norm)
    return new_cmd.strip()


# Simple input validator, may not need this
def valid(input=None):
    return input is not None and len(input) > 0 and not input.isspace()

# Go through a parse tree and deconstruct each MacroToken node into a
# list of raw base components.  Used as debug to compare parse trees.
def get_parse_tree_raw_list(item):
    out = []
    if type(item) is list or type(item) is tuple:
        for x in item:
            out.append(get_parse_tree_raw_list(x))
    else:
        try:
            out = item.get_list()
        except:
            out = item
    return out

        
# Quick recursive tree-to-string conversion.  Uses
# get_parse_tree_raw_list().
_tree_str_list = []
def get_tree_str(tree, space=''):
    global _tree_str_list
    tree_list = get_parse_tree_raw_list(tree)
    _tree_str_list = ['']
    _get_tree_str_helper(tree_list, space)
    return '\n'.join(_tree_str_list)


# Internal helper to the above.
def _get_tree_str_helper(item, space=''):
    global _tree_str_list
    if type(item) is list:
        _tree_str_list.append(space + "[")
        for x in item:
            _get_tree_str_helper(x, " " + space)
        _tree_str_list.append(space + "]")
    else:
        _tree_str_list.append("%s %s," % (space, item))


# Determine if a string is a number or not.
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# !!FOR TESTING ONLY!!
# Generate the test for a test function for a given macro.
def generate_test_function(macro, lex_c=None, parse_c=None, int_c=None, indent="    ",test_name=None):
    if not test_name:
        import inspect
        test_name = inspect.stack()[2][3]
    test_code = []
    args      = []
    
    # Mandatory: test name and macro to test.
    test_code.append("%sdef %s(self):" % (indent, test_name))
    test_code.append("%smacro = '''%s'''" % (2*indent, macro))

    # Append each test we're doing depending on input args.
    if lex_c is not None:
        args.append('lex_correct')
        test_code.append("%slex_correct = %s" % (2*indent, lex_c))
    if parse_c is not None:
        args.append('parse_correct')
        test_code.append("%sparse_correct = %s" % (2*indent, parse_c))
    if int_c is not None:
        args.append('int_correct')
        test_code.append("%sint_correct = %s" % (2*indent, int_c))

    # Add the test call, depending on arguments.
    if len(args) > 0:
        test_code.append("%sself.macro_test(macro, %s)" % \
                         (2*indent,
                          ", ".join(args)))
    else:
        test_code.append("%sself.macro_test(macro)" % \
                         (2*indent))

    # Done, return.
    return '\n'.join(test_code)


# Encode/decode a to/from base X, where X is the number of URL-safe
# characters.  Also assumed is that number is > 0. None is returned
# on error.
_URL_SAFE_SET = string.digits + string.ascii_letters + "_-"
def _10baseN(num,b,numerals=_URL_SAFE_SET):
    return ((num == 0) and  "0" ) or ( _10baseN(num // b, b).lstrip("0") + numerals[num % b])
def encode(num):
    if type(num) is not int or num < 0:
        raise Exception("num is not numeric or < 0!")
    return _10baseN(num, len(_URL_SAFE_SET), _URL_SAFE_SET)


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
    # Now decode it with unquote_plus, which also return utf-8.
    utf8_text = urllib.unquote_plus(enc_utf8_text)
    # NOW decode that into unicode, and return so that life may continue.
    return unicode(utf8_text, 'utf-8')


