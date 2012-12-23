'''
Lexer (Tokenizer) for the WoW macro language.
'''

import re

# Our modules
from macro.exceptions     import *
from macro.lex.ids        import *
from macro.lex            import rules
from macro.logger         import logger
from macro.lex.token      import create_token
from macro.util           import clean_macro


# The tokenizer class
class MacroCommandTokenizer:
    """MacroCommandTokenizer

    This class handles the tokeniziation of a macro string.  Here is
    the EBNF definition (although I'm pretty sure this is incomplete:)

    command = "/", command-verb, [ {command-object, ";" } command-object] ]
    command-verb = ? any secure command word ?
    command-object = { condition } parameters
    parameters = ? anything which may be passed to the command word ?
    condition = "[" condition-phrase { "," condition-phrase } "]"
    condition-phrase = [ "no" ], option-word, [ ":" option-argument { "/" option-argument } ]
    option-argument = ? any one-word option, such as 'shift, 'ctrl', 'target', '1', '2' ?

    Parse the macro by first splitting it into commands (one per line),
    and then using top-down recursive descent parsing.  We can only do
    this because the grammer defined by the EBNF above is not
    left-recursive, direct or indirect.

    A MacroCommandTokenizer is iterable over the set of tokens in a given
    macro command.  MacroTokens are returned.  See the definition of
    that class for more details.
    """

    # Constructor
    def __init__(self, macro_command=None, debug=False):
        """ __init__()
        """
        self.DEBUG = debug
        self.ready = False

        # The macro command currently being parsed.
        self.current_command = None

        # A token queue for when we are forced to use look-ahead parsing,
        # i.e. match a large chunk of something and then break it up into
        # tokens.
        self.current_token_queue = []

        # Symboltable for variables settable in macro--i.e. focus, target, etc.
        self.symbol_to_value_table = {}
        self.value_to_symbol       = {}
        self.symbol_count_table    = {}

        # Character counter--there is a limit to how long macros can be!
        self.macro_char_counter = 0

        # Save a reference to the root rule
        self.parse_root = rules.LEX_RULE_ROOT
        if macro_command is not None: self.reset(macro_command)


    # Reset tokenizer for a new command.
    def reset(self, macro_command, command_index=0):
        """ reset()
        Resets the tokenizer to start parsing a new command.
        """
        self.iter_index          = 0
        self.current_token_queue = []
        self.current_command     = macro_command
        self.__macro_html        = ''
        self.command_index       = command_index

        # Call the parser to parse the macro into tokens.
        self.__lex()

        # Set a flag.
        self.ready = True


    # Get a list of all useless tokens
    def get_useless_tokens(self):
        return [t for t in self.current_token_queue \
                if t.strike]

    # Get a list of the tokens
    def get_tokens(self):
        return self.current_token_queue


    # Get the clean command that we tokenized
    # The html version includes useless tokens and spaces
    # to allow for wrapping.
    def get_command_html(self):
        # By default, return command html with useless tokens
        # intact for display.
        return ''.join([t.get_raw_html(show_errors=True,
                                       js=True, strike_useless=True) \
                        for t in self.current_token_queue])
    def get_command_str(self):
        return ''.join([t.get_reconstructed_token_str() \
                        for t in self.current_token_queue \
                        if not t.strike])
    

    # A special interface into the lexer to get a default
    # target token.
    def get_default_target(self, target):
        ret_list = []
        if not target: target = ''
        self.__apply_rule_set(ret_list,
                              rules.get_target_parse_rule(),
                              "target=" + target,
                              save_pos_and_id=False)
        return ret_list


    #
    # Iterator interface
    #

    # Iterator interface.
    def next(self):
        ''' Get next token in queue. '''
        if self.iter_index == len(self.current_token_queue):
            self.ready = False
            raise StopIteration
        else:
            item = self.current_token_queue[self.iter_index]
            self.iter_index += 1
            return item

    # Not standard iterator interface, but useful.
    def prev(self):
        ''' Get the previous token in the the queue.
        If the iterator is at the begining of the queue,
        the first item is returned.'''
        item = None
        if self.iter_index == 0:
            item = self.current_token_queue[self.iter_index]
        else:
            item = self.current_token_queue[(self.iter_index - 1)]
        return item

    # Get an iterator over this class
    def __iter__(self):
        return self

    # Make the length builtin work for this class.
    # Define length as the number of tokens left in the queue.
    def __len__(self):
        return len(self.current_token_queue) - self.iter_index

    # Make the [] accessor work.
    def __getitem__(self, key):
        return self.current_token_queue[key]

    # For debug only
    def __str__(self):
        return "\n".join(map(str, self.current_token_queue))


    #
    # Private Methods
    #

    # Parse the macro into tokens using recursive look-ahead parsing.
    # This is a basically a header function to kick off a recursion.
    #
    # A token is defined loosely as terminals in the macro language,
    # i.e. [ is the start of an if, where as mounted is an
    # option-word.  The macro language is somewhat loosely defined
    # (and the EBNF above is incomplete), so the set of terminals is a
    # bit larger than the one in the EBNF.  See the parsing rules for
    # details.
    def __lex(self):
        # If we don't have a macro, raise an exception.
        if self.current_command is None or self.current_command is '':
            raise UserInputError("Require macro command string to parse.")

        if self.DEBUG: logger.debug("About to parse: " + self.current_command)

        # First normalize all spaces in the macro
        self.current_command = clean_macro(self.current_command, debug=self.DEBUG)

        # Clear the global parse state.
        self.current_token_queue = []
        rules.clear_rule_match()
        
        # Kick off the recursion.
        (rem, idx) = self.__apply_rule_set(self.current_token_queue,
                                           self.parse_root,
                                           self.current_command)

        # If we didn't consume all the input, we have a parse error.
        if (rem != ''):
            raise LexErrorNoMatchingRules(rem, idx, idx+str(rem),
                                          self.parse_root)

        # Make sure we don't add a space after the last token.
        self.current_token_queue[-1].space_after=False
        

    # Simple tokenizer that applies a parse rule set.  Recursive
    # private method that does a depth-first descent of the parse
    # rules on the input.
    def __apply_rule_set(self, queue, parse_rule, input, curr_index=0, space='', save_pos_and_id=True):
        # Decompose rule
        (name, token_type, desc, flags, re_obj, subrules) = rules.decompose_rule(parse_rule)
        
        if self.DEBUG: logger.debug("%sUsing rule: %s" % (space, name))
        if self.DEBUG: logger.debug("%sInput: |%s| index: %s" % (space, input, curr_index))
        end = 0

        # If there's nothing to do here, return.
        if len(input) == 0 and \
               not rules.rule_takes_empty(parse_rule):
            return (input, curr_index)

        # First, apply the rule.  If we miss, return.
        curr_match, rem_input, match_start, match_end = \
                    rules.apply_rule(parse_rule, input, curr_index)
        if curr_match is None:
            if self.DEBUG: logger.debug("%sNO MATCH.  Returning input: |%s|  index: %s" % (space, input, curr_index))
            return (input, curr_index)

        # Update the current index to be the start of the match--any
        # chars between curr_index and match_start are space chars.
        curr_index = match_start
        if self.DEBUG: logger.debug("%sFOUND: |%s| REM: |%s| RULE: %s START: %s, END: %s" % (space, curr_match, rem_input, name, curr_index, match_end))

        # If this rule has subrules, recurse on them. The current
        # index passed in the recursive call is the start of the
        # region where the match occurred in the original input.
        if subrules:
            done = False
            while not done:
                prev_curr_match = curr_match
                for rule_obj in subrules:
                    # Update the remainder of the match and the index with each application.
                    if self.DEBUG: logger.debug("%sRECURSING on curr_match: |%s| index: %s rule: %s" % (space, curr_match, curr_index, rule_obj))
                    (curr_match, curr_index) = self.__apply_rule_set(queue,
                                                                     rule_obj,
                                                                     curr_match,
                                                                     curr_index,
                                                                     space + "  ",
                                                                     save_pos_and_id)
                    
                # Input left over/not parsed?
                if len(curr_match) > 0 and not curr_match.isspace():
                    # If this rule isn't meant to be repeated,
                    # exception.
                    if not rules.match_repeat(flags):
                        raise LexErrorNoMatchingRules(curr_match, curr_index,
                                                      curr_index+len(curr_match), parse_rule)
                    # Did we make any progress in the last iteration?
                    # If not, exception.
                    elif prev_curr_match == curr_match:
                        raise LexErrorNoMatchingRules(curr_match, curr_index,
                                                      curr_index+len(curr_match), parse_rule)
                # Everything is consumed--we're done here.
                else:
                    done = True

        # If this rule has no subrules, then we have found an actual
        # token.  Save.
        else:
            if self.DEBUG: logger.debug("%sAdding [%s] to stack as %s" % (space, curr_match, name))
            if save_pos_and_id:
                queue.append(create_token(token_type,
                                          len(queue),
                                          curr_match,
                                          match_start,
                                          match_end,
                                          rules.space_after(flags),
                                          rules.add_space_after(flags),
                                          self.command_index))
            else:
                if self.DEBUG: logger.debug("DROPPING POSITIONS")
                queue.append(create_token(token_type,
                                          NULL_TOKEN_ID,
                                          curr_match,
                                          NULL_POSITION,
                                          NULL_POSITION,
                                          rules.space_after(flags),
                                          rules.add_space_after(flags),
                                          self.command_index))
        return (rem_input, match_end)


# Create a global tokenizer that can be used in multiple places.
GLOBAL_MACRO_TOKENIZER = MacroCommandTokenizer()


