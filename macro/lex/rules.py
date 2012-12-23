''' Parsing rules for WoW Macros.

This used to be parsed from an XML file, but that doesnt make a lot of
sense in terms of performance of a web app.  Really we can just encode
them here.
'''

import re
from macro.language   import option, parameter, target, verb
from macro.lex.ids    import *


#
# Internal Functions
#

# Rule count functions--internal to this class only.
def _is_rule_matched(name):
    global _rule_count
    if name not in _rule_count:
        _rule_count[name] = False
    return _rule_count[name]

def _rule_is_matched(name):
    global _rule_count
    _rule_count[name] = True

# Representation for comparison in testing.
def _test(rule):
    (name, token_type, desc, flags, re_obj, subrules) = rule
    return [name, token_type, [t._test() for t in subrules] if subrules else ()]


#
# Module Interface
#


# Decompose a rule, returning:
# (name, token_type, desc, flags, re_obj, subrules)
def decompose_rule(rule):
    (name, token_type, desc, flags, re_obj, subrules) = rule
    return (name, token_type, desc, flags, re_obj, subrules)


# Apply the regexp, returning (match, remainder, start, end)
# If we require a match for this rule, throw an exception.
def apply_rule(rule, input, start_index=0):
    # Decompose the rule
    (name, token_type, desc, flags, re_obj, subrules) = rule

    # Do we even need to try the match?
    if _rule_is_matched(name) and match_only_once(flags):
        return (None, input, 0, 0)
    
    if re_obj is None:
        from macro.exceptions import ConfigError
        raise ConfigError("Malformed lexing rule: " + str(rule))

    # Try the match
    result = re_obj.search(input)
    if result is None:
        # Did we miss a required match?
        if match_required(flags):
            from macro.exceptions import LexErrorRequiredMatchFailed
            raise LexErrorRequiredMatchFailed(input, start_index,
                                              start_index+len(input),
                                              rule)
        return (None, input, 0, 0)
    else:
        # Save that we matched this rule
        _rule_is_matched(name)

    # Fetch the match and remaining command, return
    return (result.group(1).strip(),
            result.group(2),
            start_index + result.start(1),
            start_index + result.end(1))


# Rule count data structure and external function to clear the rule
# count.  Rule counts need to be cleared before each macro command is
# parsed.
_rule_count = {}
def clear_rule_match():
    global _rule_count
    _rule_count = {}


# Generate a regular expression for 
def gen_regexp_from_map(map, filter=lambda p: True, boundries=True, neg=False, end=False):
    if neg:
        cmd_data_list = [term[1:] for term,obj in map.items() if filter(obj)]
        return r'(?:' + r')|(?:'.join(cmd_data_list) + r')'
    else:
        cmd_data_list = [term for term,obj in map.items() if filter(obj)]
        if boundries: return r'(?:(?:' + r'\b)|(?:'.join(cmd_data_list) + r'\b))'
        if end:       return r'(?:(?:' + r'$)|(?:'.join(cmd_data_list) + r'$))'
        return r'(?:(?:' + r')|(?:'.join(cmd_data_list) + r'))'


# Generate and return a regexp object
def get_regexp_obj(regexp):
    # Parse the regexp if there is one.
    if regexp is None:
        from macro.exceptions import ConfigError
        raise ConfigError("Require matching regexp!")
    return re.compile(regexp, re.IGNORECASE)


# FLAGS for a rule, stored efficiently as tuple of bools
# [match_repeat, match_once, match_req, space_after, add_space_after]
def get_flags(match_repeat=False, match_only_once=False,
              match_required=False, space_after=False,
              add_space_after=False, can_take_empty=False):
    return (match_repeat, match_only_once,
            match_required, space_after,
            add_space_after, can_take_empty)


# Check if a specific flag is on.
def match_repeat(flags):       return flags[0]
def match_only_once(flags):    return flags[1]
def match_required(flags):     return flags[2]
def space_after(flags):        return flags[3]
def add_space_after(flags):    return flags[4]
def can_take_empty(flags):     return flags[5]


# Simple helpers to expose specific rules.
def get_target_parse_rule():
    return _RULE_TARGET_MODIFIER

# Get a rule description.
def get_rule_desc(rule):
    return decompose_rule(rule)[2]

# Return whether or not a rule can take empty input.
def rule_takes_empty(rule):
    return decompose_rule(rule)[3][5]



#
# Parse Rules
#


# Any rule with no subrules produces a terminal.
# Map entries are:
# (name, token_type, desc, FLAGS, re_obj, (subrule refs))

# Regexp for allowed option words--repeated use, so save once.
_KNOWN_OPTION_WORD_REGEXP = gen_regexp_from_map(option.OPTION_MAP)

# Need to differentiate between secure commands and insecure verbs.
# This is because whether or not the command is secure effects how
# parameters are parsed.
_TERMINAL_INSECURE_COMMAND_VERB   = ("_TERMINAL_INSECURE_COMMAND_VERB",
                                     COMMAND_VERB,
                                     "a command verb",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*("+gen_regexp_from_map(verb.VERB_MAP, filter=lambda v: not v.secure)+")(.*)$"),
                                     None)

_TERMINAL_COMMAND_VERB            = ("_TERMINAL_COMMAND_VERB",
                                     COMMAND_VERB,
                                     "a command verb",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*(\/\w+)(.*)$"),
                                     None)

# If a macro line is commented out, mark it as such
_TERMINAL_COMMENTED_LINE          = ("_TERMINAL_COMMENTED_LINE",
                                     COMMENTED_LINE,
                                     "a commented line",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^((?:[\#|\/]{2,}|[\-]+).*)()$"),
                                     None)

_TERMINAL_META_COMMAND_VERB       = ("_TERMINAL_META_COMMAND_VERB",
                                     META_COMMAND_VERB,
                                     "a meta command verb",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*(\#\w+)(.*)$"),
                                     None)

_TERMINAL_MODIFIER                = ("_TERMINAL_MODIFIER",
                                     MODIFIER,
                                     "a command modifier",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\w+)(\s*=\s*.*)$"),
                                     None)

_TERMINAL_TARGET                  = ("_TERMINAL_TARGET",
                                     TARGET,
                                     "a target statement",
                                     get_flags(),
                                     get_regexp_obj("^\s*(target)(\s*=\s*.*)$"),
                                     None)

# Added to support new commands in patch 3.3
# See comments for _RULE_TARGET_GETS
_TERMINAL_TARGET_ALIAS            = ("_TERMINAL_TARGET",
                                     TARGET,
                                     "a target @alias",
                                     get_flags(),
                                     get_regexp_obj("^\s*(@)(\s*.*)$"),
                                     None)

# Non item-id arameters in secure commands can't have special characters [, ], ;
# They must also start with a non-space.
_TERMINAL_SECURE_PARAMETER        = ("_TERMINAL_SECURE_PARAMETER",
                                     PARAMETER,
                                     "a parameter",
                                     get_flags(add_space_after=True),
                                     get_regexp_obj("^\s*([A-Za-z1-9]*[^\[\];]*)(.*)$"),
                                     None)

_TERMINAL_SECURE_ITEM_ID          = ("_TERMINAL_SECURE_ITEM_ID",
                                     PARAMETER,
                                     "a parameter",
                                     get_flags(add_space_after=True),
                                     get_regexp_obj("^\s*((?:item:)\d+)()$"),
                                     None)

# Disallow commas for multi-params.
# This will cause some problems since a few params have commas,
# but handles most cases
_TERMINAL_SECURE_MULTI_PARAMETER  = ("_TERMINAL_SECURE_MULTI_PARAMETER",
                                     PARAMETER,
                                     "a parameter",
                                     get_flags(),
                                     get_regexp_obj("^\s*([A-Za-z1-9]*[^\[\],;]*)(.*)$"),
                                     None)
_TERMINAL_SECURE_MULTI_EMPTY      = ("_TERMINAL_SECURE_MULTI_EMPTY",
                                     PARAMETER,
                                     "an empty parameter",
                                     get_flags(can_take_empty=True),
                                     get_regexp_obj("^\s*()(.*)$"),
                                     None)

# Special parameter that is alphanumeric, but ends with a number.
_TERMINAL_SECURE_ALPHA_PARAMETER  = ("_TERMINAL_SECURE_ALPHA_PARAMETER",
                                     PARAMETER,
                                     "a parameter",
                                     get_flags(),
                                     get_regexp_obj("^\s*([A-Za-z]+?)(\d+\W*)$"),
                                     None)

_TERMINAL_SECURE_INT_PARAMETER    = ("_TERMINAL_SECURE_INT_PARAMETER",
                                     PARAMETER,
                                     "a numeric parameter",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*(\d+(?! Pound)(?! Stone))([^\d].*|.{0})$"),
                                     None)

# Insecure params can have anything
_TERMINAL_PARAMETER               = ("_TERMINAL_PARAMETER",
                                     PARAMETER,
                                     "a parameter",
                                     get_flags(add_space_after=True),
                                     get_regexp_obj("^\s*(\S.*)(.*)$"),
                                     None)

_TERMINAL_IF                      = ("_TERMINAL_IF",
                                     IF,
                                     "the start of a condition",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\[)(.*)$"),
                                     None)

_TERMINAL_ENDIF                   = ("_TERMINAL_ENDIF",
                                     ENDIF,
                                     "the end of a conditional",
                                     get_flags(space_after=False, add_space_after=True),
                                     get_regexp_obj("^\s*(\])(.*)$"),
                                     None)

_TERMINAL_AND                     = ("_TERMINAL_AND",
                                     AND,
                                     "an 'and' (,)",
                                     get_flags(add_space_after=True),
                                     get_regexp_obj("^\s*(\,)(.*)$"),
                                     None)

_TERMINAL_ELSE                    = ("_TERMINAL_ELSE",
                                     ELSE,
                                     "an 'else' (;)", 
                                     get_flags(add_space_after=True),
                                     get_regexp_obj("^\s*(\;)(.*)$"),
                                     None)
                                     
_TERMINAL_NOT                     = ("_TERMINAL_NOT",
                                     NOT,
                                     "a 'not' (no)",
                                     get_flags(),
                                     get_regexp_obj("^\s*(no)(.*)$"),
                                     None)

_TERMINAL_TOGGLE                  = ("_TERMINAL_TOGGLE",
                                     TOGGLE,
                                     "a 'toggle' (!)",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\!)(.*)$"),
                                     None)

_TERMINAL_OPTION_WORD             = ("_TERMINAL_OPTION_WORD",
                                     OPTION_WORD,
                                     "a known option",
                                     get_flags(),
                                     get_regexp_obj("^\s*("+ _KNOWN_OPTION_WORD_REGEXP +")(.*)$"),
                                     None)

_TERMINAL_GETS                    = ("_TERMINAL_GETS",
                                     GETS,
                                     "a 'gets' (=)",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\=)(.*)$"),
                                     None)

_TERMINAL_IS                      = ("_TERMINAL_IS",
                                     IS,
                                     "a 'is' (:)",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\:)(.*)$"),
                                     None)

_TERMINAL_OR                      = ("_TERMINAL_OR",
                                     OR,
                                     "an 'or' (/)",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\/)(.*)$"),
                                     None)

_TERMINAL_OPTION_ARG              = ("_TERMINAL_OPTION_ARG",
                                     OPTION_ARG,
                                     "an option argument",
                                     get_flags(),
                                     get_regexp_obj("^\s*([A-Za-z0-9 -&\(\)\']+)(.*)$"),
                                     None)

_TERMINAL_MOD_OPTION_ARG          = ("_TERMINAL_MOD_OPTION_ARG",
                                     OPTION_ARG,
                                     "a modifier argument",
                                     get_flags(),
                                     get_regexp_obj("^\s*([A-Za-z0-9 -&]+)(\/.*)$"),
                                     None)

_TERMINAL_MOD_OPTION_ARG_LAST     = ("_TERMINAL_MOD_OPTION_ARG_LAST",
                                     OPTION_ARG,
                                     "a modifier argument",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*([A-Za-z0-9 -&]+)()$"),
                                     None)

_TERMINAL_NUMERIC_OPTION_ARG      = ("_TERMINAL_NUMERIC_OPTION_ARG",
                                     OPTION_ARG,
                                     "a numeric argument",
                                     get_flags(),
                                     get_regexp_obj("^\s*(\d+)(.*)$"),
                                     None)

_TERMINAL_NUMERIC_CMD_OPTION_ARG  = ("_TERMINAL_NUMERIC_CMD_OPTION_ARG",
                                     OPTION_ARG,
                                     "a numeric argument",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*(\d+)(.*)$"),
                                     None)

_TERMINAL_TARGET_OBJ              = ("_TERMINAL_TARGET_OBJ",
                                     TARGET_OBJ,
                                     "a target unit",
                                     get_flags(),
                                     get_regexp_obj("^\s*([^\s-]+-?)(.*)$"),
                                     None)

_TERMINAL_TARGET_KNOWN_OBJ        = ("_TERMINAL_TARGET_KNOWN_OBJ",
                                     TARGET_OBJ,
                                     "a target unit",
                                     get_flags(),
                                     get_regexp_obj("^\s*(-?(?:"+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: not t.needs_dash, boundries=False) +"-?))(.*)$"),
                                     None)

_TERMINAL_TARGET_REQ_ARGS         = ("_TERMINAL_TARGET_REQ_ARGS",
                                     TARGET_OBJ,
                                     "a target unit",
                                     get_flags(),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: t.req_num_arg, boundries=False) +")(\d+)$"),
                                     None)
                                     
_TERMINAL_INSEC_ALPHA_TARGET_OBJ  = ("_TERMINAL_INSEC_ALPHA_TARGET_OBJ",
                                     TARGET_OBJ,
                                     "a target unit",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*([A-Za-z]+)(.*)$"),
                                     None)

_TERMINAL_CURRENT_TARGET          = ("_TERMINAL_CURRENT_TARGET",
                                     TARGET_OBJ,
                                     "your current_target",
                                     get_flags(space_after=True),
                                     get_regexp_obj("^\s*(\%[tT])(.*)$"),
                                     None)


''' These rules each have at least one subrule.  Some of the subrules
    include rules with other subrules.  These are essentially the
    roots of the parse DAG.  '''

# Helper ruleset: or'd list of args
_RULE_COMMAND_MODIFIER_OR_LIST    = ("_RULE_COMMAND_MODIFIER_OR_LIST",
                                     None,
                                     "a list of arguments for a command verb modifier",
                                     get_flags(space_after=True, match_repeat=True),
                                     get_regexp_obj("^\s*([\w\/]+)(.*)$"),
                                     (_TERMINAL_MOD_OPTION_ARG,
                                      _TERMINAL_OR,
                                      _TERMINAL_MOD_OPTION_ARG_LAST,))


# Modifier, i.e. reset=
# Modifier can also just be a numeric argument, i.e. with equipslot.
_RULE_COMMAND_MODIFIER            = ("_RULE_COMMAND_MODIFIER",
                                     None,
                                     "a command verb modifier",
                                     get_flags(),
                                     get_regexp_obj("^\s*((?:reset\s*=\s*\S+))(.*)$"),
                                     (_TERMINAL_MODIFIER,
                                      _TERMINAL_GETS,
                                      _RULE_COMMAND_MODIFIER_OR_LIST,))
                            

# Handle (target)* and (target-)*, which can be tacked on at the end
# of any target specifier.
_RULE_TARGET_TARGET               = ("_RULE_TARGET_TARGET",
                                     None,
                                     "a target",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(-?(?:"+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: t.follow, boundries=False) +"-?)+)(.*)$"),
                                     (_TERMINAL_TARGET_KNOWN_OBJ,))


# Target + numeric argument
# The list of targets that can take arguments is defined
# by the language model.
_RULE_TARGET_OBJ_AND_ARG          = ("_RULE_TARGET_OBJ_AND_ARG",
                                     None,
                                     "a party or raid target",
                                     get_flags(),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: t.req_num_arg, boundries=False) +"\d+)(.*)$"),
                                     (_TERMINAL_TARGET_REQ_ARGS,
                                      _TERMINAL_TARGET_REQ_ARGS,
                                      _TERMINAL_NUMERIC_OPTION_ARG,))


# ^(target) + target
# Takes special target words that do not require a dash followed by target+.
_RULE_TARGET_BEFORE_TARGETS       = ("_RULE_TARGET_BEFORE_TARGETS",
                                     None,
                                     "a known target word",
                                     get_flags(),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: not t.needs_dash, boundries=False) +")("+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: t.follow, boundries=False) +".*)$"),
                                     (_TERMINAL_TARGET_KNOWN_OBJ,))


# ^(target)- + target
# Takes off anything that requires a dash followed by target+.
_RULE_TARGET_BEFORE_TARGETS_DASH  = ("_RULE_TARGET_BEFORE_TARGETS_DASH",
                                     None,
                                     "a valid unit-target specififer",
                                     get_flags(),
                                     get_regexp_obj("^\s*([^-]\S+?-)("+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: t.follow, boundries=False) +".*)$"),
                                     (_TERMINAL_TARGET_OBJ,))


# Get a target unit only
_RULE_TARGET_UNIT                 = ("_RULE_TARGET_UNIT",
                                     None,
                                     "the end of a target chain or a target unit",
                                     get_flags(),
                                     get_regexp_obj("^\s*((?!"+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: not t.needs_dash, boundries=False, end=True) +")\S+)()$"),
                                     (_TERMINAL_TARGET_OBJ,))

# Get only a non-unit target
_RULE_TARGET                      = ("_RULE_TARGET",
                                     None,
                                     "recognized target word",
                                     get_flags(),
                                     get_regexp_obj("^\s*(-?"+ gen_regexp_from_map(target.TARGET_MAP, filter=lambda t: not t.needs_dash, boundries=False, end=True) +")()"),
                                     (_TERMINAL_TARGET_KNOWN_OBJ,))

# As of patch 3.3, we now can handle "@" as an alias for "target=" in
# conditions, i.e. "@focus" instead of "target=focus".  To accomodate
# this, split out the TERMINAL_TARGET and TERMINAL_GETS acquisition
# into seperate subrules.
_RULE_TARGET_GETS                 = ("_RULE_TARGET_GETS",
                                     None,
                                     "a target assignment",
                                     get_flags(),
                                     get_regexp_obj("^\s*(target\s*=\s*)(.*)$"),
                                     (_TERMINAL_TARGET,
                                      _TERMINAL_GETS,))
_RULE_TARGET_GETS_ALIAS           = ("_RULE_TARGET_GETS_ALIAS",
                                     None,
                                     "a target assignment via alias",
                                     get_flags(),
                                     get_regexp_obj("^\s*(@\s*)(.*)$"),
                                     (_TERMINAL_TARGET_ALIAS,))

# Target, i.e. target=X.  Make sure to handle targets with numeric
# arguments.
_RULE_TARGET_MODIFIER             = ("_RULE_TARGET_MODIFIER",
                                     None,
                                     "a target assignment",
                                     get_flags(),
                                     get_regexp_obj("^\s*((?:target\s*=\s*|@)[^,\]]+)(.*)$"),
                                     (_RULE_TARGET_GETS_ALIAS,
                                      _RULE_TARGET_GETS,
                                      _RULE_TARGET_OBJ_AND_ARG,
                                      _RULE_TARGET_BEFORE_TARGETS,
                                      _RULE_TARGET_BEFORE_TARGETS_DASH,
                                      _RULE_TARGET_TARGET,
                                      _RULE_TARGET,
                                      _RULE_TARGET_UNIT,))

# Match an option WITH arguments
_RULE_OPTION_W_ARGS               = ("_RULE_OPTION_W_ARGS",
                                     None,
                                     "a conditional option statement with arguments",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*((?:no)?\s*"+ _KNOWN_OPTION_WORD_REGEXP +"\s*:.+)()$"),
                                     (_TERMINAL_NOT,
                                      _TERMINAL_OPTION_WORD,
                                      _TERMINAL_IS,
                                      _TERMINAL_OPTION_ARG,
                                      _TERMINAL_OR,))


# Handle an option without arguments.
_RULE_OPTION_NO_ARGS              = ("_RULE_OPTION_NO_ARGS",
                                     None,
                                     "a conditional option statement with no arguments",
                                     get_flags(match_only_once=True),
                                     get_regexp_obj("^\s*((?:no)?\s*"+ _KNOWN_OPTION_WORD_REGEXP +")()$"),
                                     (_TERMINAL_NOT,
                                      _TERMINAL_OPTION_WORD,))

# Handle options.
_RULE_OPTION                      = ("_RULE_OPTION",
                                     None,
                                     "a recognized option or target",
                                     get_flags(match_only_once=True),
                                     get_regexp_obj("^\s*([^,\]]+)(.*)$"),
                                     (_RULE_OPTION_NO_ARGS,
                                      _RULE_OPTION_W_ARGS,))

# Condition, [..]. . . Can be repeated.
_RULE_CONDITIONS                  = ("_RULE_CONDITIONS",
                                     None,
                                     "a valid condition",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(\[.*?\])(.*)$"),
                                     (_TERMINAL_IF,
                                      _TERMINAL_ENDIF,
                                      _RULE_TARGET_MODIFIER,
                                      _RULE_OPTION,
                                      _TERMINAL_AND,))


# Parameter rules
# Click commands can parameters in a specific form.
_RULE_SECURE_CLICK_PARAM_PHRASE   = ("_RULE_SECURE_CLICK_PARAM_PHRASE",
                                     None,
                                     "a /click-specific parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(parameter.PARAM_MAP, boundries=False) +"\d+)(.*)$"),
                                     (_TERMINAL_SECURE_ALPHA_PARAMETER,
                                      _TERMINAL_SECURE_INT_PARAMETER,
                                      _TERMINAL_SECURE_ITEM_ID,
                                      _TERMINAL_SECURE_PARAMETER,))

_RULE_SECURE_PARAMETER_PHRASE     = ("_RULE_SECURE_PARAMETER_PHRASE",
                                     None,
                                     "a complete command parameter",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*([^;\[\]\/\=]*,?\s*)(.*)$"),
                                     (_RULE_SECURE_CLICK_PARAM_PHRASE,
                                      _TERMINAL_TOGGLE,
                                      _TERMINAL_SECURE_ITEM_ID,
                                      _TERMINAL_SECURE_PARAMETER,
                                      _TERMINAL_AND,))

_RULE_SECURE_INT_PARAMETER_PHRASE = ("_RULE_SECURE_INT_PARAMETER_PHRASE",
                                     None,
                                     "a complete command parameter",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(,?\s*[^;\[\]\/\=]*)(.*)$"),
                                     (_TERMINAL_AND,
                                      _TERMINAL_SECURE_INT_PARAMETER,
                                      _TERMINAL_SECURE_INT_PARAMETER,
                                      _TERMINAL_SECURE_ITEM_ID,
                                      _TERMINAL_SECURE_PARAMETER,))


# Handle <NOP>,<NOP>
_RULE_SECURE_MULTI_EMPTY          = ("_RULE_SECURE_MULTI_EMPTY",
                                     None,
                                     "an empty parameter followed by a comma and another empty parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*(,\s*)()$"),
                                     (_TERMINAL_SECURE_MULTI_EMPTY,
                                      _TERMINAL_AND,
                                      _TERMINAL_SECURE_MULTI_EMPTY,))

# Handle <NOP>,param
_RULE_SECURE_MULTI_EMPTY_PARAM    = ("_RULE_SECURE_MULTI_EMPTY_PARAM",
                                     None,
                                     "an empty parameter followed by a comma and a non-empty command parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*(,\s*)(.*\S.*)$"),
                                     (_TERMINAL_SECURE_MULTI_EMPTY,
                                      _TERMINAL_AND,))

# Handle param,<NOP>
_RULE_SECURE_MULTI_PARAM_EMPTY   = ("_RULE_SECURE_MULTI_PARAM_EMPTY",
                                     None,
                                     "a command parameter followed by a comma and an empty parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*([^,]+\s*,\s*)()$"),
                                     (_TERMINAL_TOGGLE,
                                      _TERMINAL_SECURE_MULTI_PARAMETER,
                                      _TERMINAL_AND,
                                      _TERMINAL_SECURE_MULTI_EMPTY,))

# Handle param,... (not empty)
_RULE_SECURE_MULTI_PARAM_PARAM   = ("_RULE_SECURE_MULTI_PARAM_PARAM",
                                     None,
                                     "a command parameter followed by a comma and another non-empty parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*([^,]+\s*,)(.*\S.*)$"),
                                     (_TERMINAL_TOGGLE,
                                      _TERMINAL_SECURE_MULTI_PARAMETER,
                                      _TERMINAL_AND))

# Last param -- nothing after
_RULE_SECURE_MULTI_PARAM         = ("_RULE_SECURE_MULTI_PARAM",
                                     None,
                                     "a complete command parameter",
                                     get_flags(match_repeat=False),
                                     get_regexp_obj("^\s*([^,]+)()$"),
                                     (_TERMINAL_TOGGLE,
                                      _TERMINAL_SECURE_MULTI_PARAMETER,))

# Handle a set of toggled parameters
_RULE_SECURE_MULTI_PARAM_PHRASE   = ("_RULE_SECURE_MULTI_PARAM_PHRASE",
                                     None,
                                     "a complete command parameter phrase",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*([^;\[\]\/\=]+)(.*)$"),
                                     (_RULE_SECURE_MULTI_EMPTY,
                                      _RULE_SECURE_MULTI_EMPTY_PARAM,
                                      _RULE_SECURE_MULTI_PARAM_EMPTY,
                                      _RULE_SECURE_MULTI_PARAM_PARAM,
                                      _RULE_SECURE_MULTI_PARAM,))


# Command objects; repeat this over all input.
# command-object={ condition } parameters
_RULE_COMMAND_OBJECT              = ("_RULE_COMMAND_OBJECT",
                                     None,
                                     "a valid condition or parameter",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(.+)(.*)$"),
                                     (_RULE_CONDITIONS,
                                      _RULE_COMMAND_MODIFIER,
                                      _RULE_SECURE_PARAMETER_PHRASE,
                                      _TERMINAL_ELSE,
                                      _TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,))

_RULE_COMMAND_INT_PARAM_OBJECT    = ("_RULE_COMMAND_INT_PARAM_OBJECT",
                                     None,
                                     "a valid condition or parameter",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(.+)(.*)$"),
                                     (_RULE_CONDITIONS,
                                      _RULE_SECURE_INT_PARAMETER_PHRASE,
                                      _TERMINAL_ELSE,
                                      _TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,))

_RULE_COMMAND_MULTI_PARAM_OBJECT  = ("_RULE_COMMAND_MULTI_PARAM_OBJECT",
                                     None,
                                     "a valid condition or parameter",
                                     get_flags(match_repeat=True),
                                     get_regexp_obj("^\s*(.+)(.*)$"),
                                     (_RULE_CONDITIONS,
                                      _RULE_COMMAND_MODIFIER,
                                      _RULE_SECURE_MULTI_PARAM_PHRASE,
                                      _TERMINAL_ELSE,
                                      _TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,))

# Matches only once.  Required.
_RULE_SECURE_COMMAND              = ("_RULE_SECURE_COMMAND",
                                     None,
                                     "a valid macro command",
                                     get_flags(match_only_once=True),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(verb.VERB_MAP, filter=lambda v: v.secure) +".*)(.*)$"),
                                     (_TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,
                                      _RULE_COMMAND_OBJECT,))

# Commands that could take int params need to be treated a bit differently.
_RULE_SECURE_INT_COMMAND          = ("_RULE_SECURE_INT_COMMAND",
                                     None,
                                     "a valid macro command",
                                     get_flags(match_only_once=True),
                                     get_regexp_obj("^\s*("+ gen_regexp_from_map(verb.VERB_MAP, filter=lambda v: v.takes_int) +".*)(.*)$"),
                                     (_TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,
                                      _RULE_COMMAND_INT_PARAM_OBJECT,))

# Commands that could take multi params also need to be treated a bit differently.
_RULE_SECURE_MULTI_COMMAND        = ("_RULE_SECURE_MULTI_COMMAND",
                                     None,
                                     "a valid macro command",
                                     get_flags(match_only_once=True),
                                     get_regexp_obj("^\s*("+gen_regexp_from_map(verb.VERB_MAP, filter=lambda v: v.takes_list)+".*)(.*)$"),
                                     (_TERMINAL_META_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,
                                      _RULE_COMMAND_MULTI_PARAM_OBJECT,))

# Insecure targeted command=/verb Target
# Matches only once.  Everything after the command is a target.
_RULE_INSECURE_COMMAND_VERB_TARGET = ("_RULE_INSECURE_COMMAND_VERB_TARGET",
                                      None,
                                      "a valid target",
                                      get_flags(match_only_once=True),
                                      get_regexp_obj("^\s*("+ gen_regexp_from_map(verb.VERB_MAP, filter=lambda v: not v.secure and v.takes_units) +"\s+\S+\s*)(.*)$"),
                                      (_TERMINAL_INSECURE_COMMAND_VERB,
                                       _TERMINAL_INSEC_ALPHA_TARGET_OBJ,
                                       _TERMINAL_CURRENT_TARGET,))

# Insecure command=/verb params
# Matches only once.  Required.  Everything after the command is a
# parameter. If we're here, we must match, or fail.
_RULE_INSECURE_COMMAND            = ("_RULE_INSECURE_COMMAND",
                                     None,
                                     "a valid macro verb",
                                     get_flags(match_only_once=True, match_required=True),
                                     get_regexp_obj("^\s*(\/\w+.*)(.*)$"),
                                     (_RULE_INSECURE_COMMAND_VERB_TARGET,
                                      _TERMINAL_INSECURE_COMMAND_VERB,
                                      _TERMINAL_COMMAND_VERB,
                                      _TERMINAL_PARAMETER,))


''' Root rule. Applied in order to parse the macro. '''
LEX_RULE_ROOT                     = ("ROOT",
                                     None,
                                     "a valid macro command",
                                     get_flags(match_only_once=True, match_required=True),
                                     get_regexp_obj("^\s*(.+)(.*)$"),
                                     (_TERMINAL_COMMENTED_LINE,
                                      _RULE_SECURE_INT_COMMAND,
                                      _RULE_SECURE_MULTI_COMMAND,
                                      _RULE_SECURE_COMMAND,
                                      _RULE_INSECURE_COMMAND,
                                      _TERMINAL_PARAMETER,))

