''' Defines exceptions used to report errors in parsing and execution
of macros.
'''

import exceptions
from macro.interpret.txt_token import TxtToken
from macro.util                import NULL_POSITION, NULL_TOKEN_ID

# Base exception class with a shared rendering method.
class MacroError():
    ''' Base class for macro exceptions containing rendering
    methods.'''

    # To be overridden
    def set_render_list(self):
        self.render = [TxtToken("Unknown Exception")]        

    def get_render_list(self):
        ''' Get a list of the tokens to render for this
        exception. '''
        self.set_render_list()
        return self.render

    # Debug methods
    def get_debug_str(self):
        r_list = self.get_render_list()
        return ''.join(map(lambda t: t.get_render_desc() + ' ' \
                           if t.render_space_after             \
                           else t.get_render_desc(), r_list))
    def __str__(self):
        return self.get_debug_str()
    def __repr__(self):
        return self.get_debug_str()    


# Exception types
class OtherError(MacroError):
    ''' Non-lexing/parsing errors.'''


class InterpretError(MacroError):
    ''' Interpretation-specific errors.
    Attributes:
      cmd  -- Start of command causing interpretation problems.

      '''
    def __init__(self, cmd, data1=None):
        self.cmd   = cmd
        self.data1 = data1

    def get_token(self):
        ''' Get the token causing the error so we can give it
        a display popup.'''
        return self.cmd

class LexerError(MacroError):
    ''' Lexer errors.
    Attributes:
      data  -- Input causing error
      pos   -- Start index of input
      rule  -- Rules object we tried.
    '''
    def __init__(self, data, start, end, rule):
        self.start = start
        self.end   = end
        self.rule  = rule
        self.data  = data
    def get_start(self):
        return self.start
    def get_end(self):
        return self.end


class ParserError(MacroError):
    ''' Parser errors.
    Attributes:
      cmd    -- Verb MacroToken
      data1  -- Exception data field 1
      data2  -- Exception data field 2

    Note that these errors can be saved as popups
      '''
    def __init__(self, cmd, data1=None, data2=None):
        if cmd: cmd.render_space_after = True
        self.cmd   = cmd
        self.data1 = data1
        self.data2 = data2

    def get_token(self):
        ''' Get the token causing the error so we can give it
        a display popup.'''
        if self.data1 is not None and self.data1.token_id != NULL_TOKEN_ID:
            return self.data1
        if self.data2 is not None:
            return self.data2
        return None
    
    def get_pos(self):
        if self.data1 is not None and self.data1.start != NULL_POSITION:
            return self.data1.start
        if self.data2 is not None:
            return self.data2.start
        return NULL_POSITION


#
# UI Errors
#

# No input
class NoInputError(OtherError, BaseException):
    '''Handle configuration errors.'''

    def __init__(self, error="Unknown init error"):
        self.error = error
    def set_render_list(self):
        self.render = [TxtToken(self.error)]

# Init error
class InitError(OtherError, BaseException):
    '''Handle configuration errors.'''

    def __init__(self, error="Unknown init error"):
        self.error = error
    def set_render_list(self):
        self.render = [TxtToken(self.error)]

# Search error
class InvalidSearchError(OtherError, BaseException):
    '''Somebody is doing something funny with search.'''

    def __init__(self, error="Unknown search error"):
        self.error = error
    def set_render_list(self):
        self.render = [TxtToken(self.error)]


#
# Input/Config Errors
#

# Handle config problems
class ConfigError(OtherError, BaseException):
    '''Handle configuration errors.'''

    def __init__(self, error="Unknown init error"):
        self.error = error
    def set_render_list(self):
        self.render = [TxtToken("Configuration error: "),
                       TxtToken(error)]        
    

# Bad user input independant of parsing.
class UserInputError(OtherError, BaseException):
    '''Exception raised for errors in the input independant of
    parsing.
    '''
    def __init__(self, macro=''):
        self.error = macro
    def set_render_list(self):
        if len(self.error) == 0:
            self.render = [TxtToken("Please enter a macro to parse.")]
        else:
            self.render = [TxtToken("Bad user input: "),
                           TxtToken(self.error)]


# Too long
class MacroLenError(OtherError, BaseException):
    '''Macro too long.
    '''
    def __init__(self, err=''):
        self.error = err
    def set_render_list(self):
        self.render = [TxtToken(self.error)]


#
# Lexer Errors
#

# Error in lexing--couldn't lex input into tokens.
class LexErrorNoMatchingRules(LexerError, BaseException):
    '''Raised when we cant find a rule to lex some input.
    '''
    # Override the render list construction.
    def set_render_list(self):
        from macro.lex.rules import get_rule_desc
        # Give a bit of detail on what we failed
        desc = get_rule_desc(self.rule)
        self.render = [TxtToken("Expected %s, but got %s.  Is there a typo in your macro?" \
                                % (desc, self.data))]
        

# Error in lexing--required macro part not found.
class LexErrorRequiredMatchFailed(LexerError, BaseException):
    '''Raised when we expected a match for something, and didnt find
    one.  Example: /command-verb
    '''
    def set_render_list(self):
        from macro.lex.rules import get_rule_desc
        # Give a bit of detail on what we failed
        desc = get_rule_desc(self.rule)        
        self.render = [TxtToken("Could not find %s in %s." % (desc,
                                                                self.data))]
        

#
# Parsing Errors
#


# Error in parsing--invalid target token
class ParseErrorInvalidTargetToken(ParserError, BaseException):
    '''Was looking for one type of token, got another.
    In this exception, data1 is expected, data2 is recieved
    '''
    def set_render_list(self):
        self.render = [TxtToken("Target qualifier %s is either mispelled or in the wrong place." % self.cmd.data)]
    def get_pos(self):
        return self.cmd.start
    def get_token(self):
        return self.cmd

    
# Error in parsing--got unexpected token
class ParseErrorUnexpectedToken(ParserError, BaseException):
    '''Was looking for one type of token, got another.
    In this exception, data1 is expected, data2 is recieved
    '''
    def set_render_list(self):
        self.render = [TxtToken("Unexpected token found.  Do you have a typo in your macro?")]
    def get_pos(self):
        return self.data2.start
    def get_token(self):
        return self.data2


# Error in parsing--multiple targets in the same condition.
class ParseErrorMultiTargetCondition(ParserError, BaseException):
    '''Bad condition--has multiple targets.
    In this exception, data1 is current target, data2 the new target
    '''
    def set_render_list(self):
        self.render = [TxtToken("Can't assign multiple targets in the same condition.")]

# Error in parsing--no reset allowed for this command.
class ParseErrorNoResetAllowed(ParserError, BaseException):
    '''reset= given for a command that doesnt allow it..
    Field data1 is the reset param.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Macro command %s doesn't take reset options." % self.cmd.data)]

    def get_pos(self):
        return self.data1.start
    def get_token(self):
        return self.data1


# Error in parsing--reset in the wrong place
class ParseErrorResetBeforeConditions(ParserError, BaseException):
    '''reset= options must be given before conditions.
    Field data1 is the reset param.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Options for resetting a sequence must be placed after any macro conditions.  Example: %s [conditions] reset=..." % self.cmd.data)]

    def get_pos(self):
        return self.data1.start
    def get_token(self):
        return self.data1


# Error in parsing--toggles aren't allowed
class ParseErrorNoTogglesAllowed(ParserError, BaseException):
    '''Command doesnt take toggled arguments.
    data1 has the offending toggle, data2 the parameter.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Command %s doesn't allow toggled parameters." % self.cmd.data)]


# Error in parsing--parameter required to make a valid command.
class ParseErrorParamRequired(ParserError, BaseException):
    '''Command needs a parameter, and doesnt have one.
    No data for this error.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Command %s requires a valid parameter." % self.cmd.data)]

    def get_pos(self):
        return self.cmd.end
    def get_token(self):
        return self.cmd


# Error in parsing--did not find an acceptable param pattern.
class ParseErrorWrongParams(ParserError, BaseException):
    '''Command was not given an acceptable set of parameters.
    The command token has the pattern required.
    data1 has the parameter types, data2 the error position.
    '''
    def set_render_list(self):
        if self.cmd.attrs.error_msg:
            self.render = [TxtToken(self.cmd.attrs.error_msg)]
            return 
        req_pats = []
        got_pats = None
        for t in self.cmd.attrs.param:
            if not t:
                req_pats.append('no value, ')
            else:
                req_pats.append('(%s)' % \
                                (', '.join(["Item, Spell or known identifier" if i is str \
                                            else "Numeric Value"          \
                                            for i in t])))
        if len(self.data1) > 0:
            got_pats = ('(%s)' % \
                        (', '.join(["Item, Spell or known identifier" if i is str \
                                    else "Numeric Value"          \
                                    for i in self.data1])))
        else:
            got_pats = "nothing"
        self.render = [TxtToken("Command %s" % self.cmd.data),
                       TxtToken("takes"),
                       TxtToken(' or '.join(req_pats), render_space_after=False),
                       TxtToken(".  The parameter types given are"),
                       TxtToken(got_pats, render_space_after=False),
                       TxtToken(". Did you mispell or forget something?")]
        
    # Return the position
    def get_pos(self):
        return self.data2
    def get_token(self):
        return self.cmd

# Error in parsing--option does not allow arguments.
class ParseErrorNoArgsForOption(ParserError, BaseException):
    '''Option arguments are given for an option that does
    not allow them.  Example: exists:1/2/3
    data1 has the option, data2 operator token.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Option"),
                       self.data1,
                       TxtToken("doesn't take arguments.")]

    # Return the position of the op token.
    def get_pos(self):
        return self.data2.end
    def get_token(self):
        return self.data2    

# Error in parsing--option requires arguments, and we didn't get any.
class ParseErrorReqArgsForOption(ParserError, BaseException):
    '''
    Option arguments are omitted for an option that requires them.
    data1 has the option.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Option"),
                       self.data1,
                       TxtToken("requires option arguments.")]        

    # Return the position of the op token.
    def get_pos(self):
        return self.data1.end
    

# Error in parsing--non-matching negs in or list
class ParseErrorNonMatchingNegs(ParserError, BaseException):
    '''
    If we get word:arg/noword:arg form, error.
    data1 has the offending negative.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Can't mix negative and non-negatives options in the same argument list.  Break this into seperate options.")]

    # Return the position of the op token.
    def get_pos(self):
        return self.data1.end
    

# Error in parsing--non-matching option words in or list
class ParseErrorNonMatchingOptionWords(ParserError, BaseException):
    '''
    If we get word:arg/word:arg form, word had better match.
    cmd has the first option.
    data1 has the option that doesnt match.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Option"),
                       TxtToken("'%s'" % self.cmd.data),
                       TxtToken("does not match option"),
                       TxtToken("'%s'" % self.data1.data),
                       TxtToken("in your condition.  Break this list into seperate options."),
                       ]        

    # Return the position of the op token.
    def get_pos(self):
        return self.data1.end
    

# Error in parsing--malformed command
class ParseErrorMalformedCommand(ParserError, BaseException):
    '''Wrong formulation of command.
    data1 contains token causing the error.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Macro command %s is malformed at token %s" \
                                % (self.cmd.data,
                                   self.data1.data))]
    def get_pos(self):
        return self.data1.end
    

# Error in parsing--multiple DIFFERENT verbs in the command
class ParseErrorMultipleVerbs(ParserError, BaseException):
    '''Wrong formulation of command.
    data1 contains token causing
    the error.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Can't have multiple commands %s and %s in the same macro line." \
                                % (self.cmd.data,
                                   self.data1.data))]

    def get_pos(self):
        return self.data1.end


# Error in parsing--insecure verb can't take %t
class ParseErrorInsecureVerbNoCurrentTarget(ParserError, BaseException):
    ''' Verb doesnt recognize %t.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Command %s doesn't recognize %s as a target, causing this macro to not execute correctly." \
                                % (self.cmd.data,
                                   self.data1.data))]

    def get_pos(self):
        return self.data1.end


# Error in parsing--insecure verb requires a target
class ParseErrorInsecureVerbReqTgt(ParserError, BaseException):
    ''' Verb doesnt recognize %t.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Command %s requires a target unit to function correctly." % self.cmd.data)]

    def get_pos(self):
        return self.cmd.end
    def get_token(self):
        return self.cmd

    
# Error in parsing--Totem specified in target= command
class ParseErrorTargetTotem(ParserError, BaseException):
    '''Wrong formulation of command.
    data1 contains token causing
    the error.
    '''
    def set_render_list(self):
        self.render = [TxtToken("As of patch 3.2, totems can't be used as macro targets."),
                       self.data1,
                       TxtToken("is not a valid target for %s." % self.cmd.data)]
    
    def get_pos(self):
        return self.data1.end


# Error in interpreting--single-use command used multiple times.
class InterpetErrorSingleUseCommandViolated(InterpretError, BaseException):
    '''Some commands can only be used once per macro.  This exception
    is thrown when we see one of these commands multiple time in the
    same macro.
    '''
    def set_render_list(self):
        self.render = [TxtToken("Command %s can only be used once per macro." % self.cmd.data)]

    def get_pos(self):
        return self.cmd.end


# Error in interpreting--invalid option used in reset command.
class InterpetErrorInvalidResetOption(InterpretError, BaseException):
    '''Got an invalid reset option.  Overload self.cmd to contain
    the option.
    '''
    def set_render_list(self):
        desc = "'%s'" % self.cmd.data        
        self.render = [TxtToken("Option %s can't be used as a reset condition." % desc)]

    def get_pos(self):
        return self.cmd.end

# Error in interpreting--invalid arg used in option.
class InterpetErrorInvalidConditionArg(InterpretError, BaseException):
    '''Got an invalid condition arg.  Overload self.cmd to contain
    the option.
    '''
    def set_render_list(self):
        arg = "'%s'" % self.cmd.data
        word  = "'%s'" % self.data1.data        
        self.render = [TxtToken("Value %s is not a valid argument for the %s conditional." \
                                % (word, arg))]
    def get_pos(self):
        return self.data1.end
    def get_token(self):
        return self.data1
