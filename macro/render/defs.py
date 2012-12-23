'''
Collection of rendering-specific constants.
'''


''' Default number of search results. '''
DEF_SEARCH_RESULTS = 5


'''
IMPORTANT
This turns profiling on/off site-wide.
'''
DO_PROFILE = True

''' Macro Explainer email. '''
MACRO_EMAIL_REPLY_ADDRESS = "do-not-reply@macroexplain.com"
MACRO_EMAIL_SUBJECT       = "Your World of Warcraft Macro"
MACRO_EMAIL_BODY          = """
Greetings!

You've been sent a World of Warcraft macro from Fitzcairn's Macro Explain-o-matic by %(from)s.

Visit the link below to view the macro, and get a full explanation of what it does.

%(link)s

Thank you for using the Macro Explain-o-matic!



---
This message was generated automatically from http://www.macroexplain.com.  Please do not reply.
"""

''' Armory link template '''
ARMORY_LINK = """<a class="author" href="http://%s.battle.net/wow/en/character/%s/%s/">%s</a>"""

''' Error html '''
MACRO_CHANGED = """
Note: your macro was cleaned up a bit during
interpretatation. The cleaned version has been
substituted in the input box.
"""

''' Current WoW version '''
MAJOR_VERSION = 4
MINOR_VERSION = 0
PATCH_VERSION = 6


''' Static URL '''
STATIC_URL = """http://static.macroexplain.com"""


''' Process URLS '''
URL_MACRO_SEARCH  = '/s/.*'
URL_MACRO_VIEW    = '/m.*'
URL_MACRO_XML     = '/xml/m.*'
URL_MACRO_JSON    = '/json/m.*'
URL_MACRO_PROCESS = '/'
URL_SAVE_PROCESS  = '/save'
URL_SAVE_ERROR    = '/error'
URL_LINKS         = '/links'
URL_ABOUT         = '/about'
URL_TOOLS         = '/tools'
URL_SEARCH        = '/search'
URL_TYPEAHEAD     = '/_ta'
URL_RATE          = '/_rate'
URL_MACRO_TT      = '/_tt'


''' CGI Vars '''
GET_MACRO_EXPLAIN = 'i'
GET_MACRO_LINK    = 'm'
GET_SEARCH_QUERY  = 'q'
GET_SEARCH_SORT   = 'sr'
GET_MACRO_RATING  = 'r'
FORM_MACRO_EMAIL  = 'e'


''' Search Vars '''
FORM_SEARCH_PAGE   = 'p'
FORM_SEARCH_CURSOR = 'c'


''' Email form vars '''
FORM_EMAIL_INPUT  = 'ei'
FORM_EMAIL_TO     = 'et'
FORM_EMAIL_FROM   = 'ef'
FORM_MACRO_ID     = 'id'


''' Save form Vars '''
FORM_MACRO_INPUT  = 'i'
FORM_MACRO_ESC    = 'esc'
FORM_QUERY_ESC    = 'qesc'
FORM_SAVE_TITLE   = 't'
FORM_SAVE_NAME    = 'n'
FORM_SAVE_NOTES   = 'nts'
FORM_SAVE_SERVER  = 'r'
FORM_SAVE_CLASSES = 'c'
FORM_SAVE_TAGS    = 'g'

''' HTML VARS '''
NOTES_TEXT_LENGTH = 512
ALL_TAGS_MAX_LENGTH = 128
SINGLE_TAG_MAX_LENGTH = 32
MAX_RATING = 5
NAME_MAX_LENGTH = 12
TITLE_MAX_LENGTH = 40
SERVER_MAX_LENGTH = 128

''' Error Text '''
FORM_SAVE_REQ_ERROR   = {
    FORM_SAVE_TITLE   : 'Require a name for this macro.',
    FORM_SAVE_NAME    : 'Require an author name.',
    FORM_SAVE_CLASSES : 'Please select at least one valid class.',
    FORM_SAVE_TAGS    : 'Please enter at least one valid tag.',
    }

''' Help text '''
FORM_MACRO_INPUT_HELP   = """Type or paste your World of Warcraft macro here."""
FORM_SEARCH_INPUT_HELP  = """Poop!"""

''' Form Options '''
CLASS_LIST = [
    'Death Knight',
    'Druid',
    'Hunter',
    'Mage',
    'Paladin',
    'Priest',
    'Rogue',
    'Shaman',
    'Warlock',
    'Warrior',
    ]

TAG_LIST = [
    'Arenas',
    'Battlegrounds',
    'Chat',
    'Party/Raid',
    'PvE',
    'PvP',
    'Pets',
    'Professions',
    'Questing',    
    'Roleplaying',
    'Mounts',
    ]

