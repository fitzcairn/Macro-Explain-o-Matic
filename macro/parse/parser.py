'''
Class for transforming a lexed list of tokens into a parse tree
for a WoW macro.
'''

import re
import sys
from sys import exit

# Macro modules
from macro.exceptions       import *
from macro.logger           import logger
from macro.util             import clean_macro
from macro.lex.lexer        import GLOBAL_MACRO_TOKENIZER, MacroCommandTokenizer
from macro.lex.token        import MacroToken
from macro.lex.ids          import *



# The parser class.  Evaluates the tokens parsed out of a macro to
# form a parse tree.
class MacroParser:
    '''MacroParser

    Simple parser for the wow macro langage.  Uses recursive
    forward-looking parsing.

    Here is the EBNF definition (although Im pretty sure this is
    incomplete):
    
    command = "/", command-verb, [ {command-object, ";" } command-object] ]
    command-verb = ? any secure command word ?
    command-object = { condition } parameters
    parameters = ? anything which may be passed to the command word ?
    condition = "[" condition-phrase { "," condition-phrase } "]"
    condition-phrase = [ "no" ], option-word, [ ":" option-argument { "/" option-argument } ]
    option-argument = ? any one-word option, such as "shift, "ctrl", "target", "1", "2" ?
    '''

    # Constructor.
    def __init__(self, lexer_obj=None, macro=None, debug=False):
        ''' Constructor '''
        self.DEBUG = debug
        
        # Save the lexer object
        if lexer_obj is None:
            self.__tokenizer = GLOBAL_MACRO_TOKENIZER
            self.__tokenizer.DEBUG = debug
        elif isinstance(lexer_obj, MacroCommandTokenizer): 
            self.__tokenizer = lexer_obj
        else:
            raise ConfigError("Requires a valid lexer object!")

        # The current token.
        self.__current_token = None

        # Parse the macro if we got one.
        if macro is not None: self.lex_and_parse_macro(macro)

    # Lex the macro with the global lexer instance.
    # This is just a shortcut method.
    def lex_macro(self, macro_input_line, index):
        self.macro_line = clean_macro(macro_input_line)
        if self.macro_line is None or self.macro_line.isspace() or len(self.macro_line) < 1:
            raise UserInputError("Macro input blank.  Require valid macro.")

        if self.DEBUG: logger.debug("About to lex: %s" % (self.macro_line))
        self.__tokenizer.reset(self.macro_line, index)
        if self.DEBUG: logger.debug("Tokens:\n%s" % str(self.__tokenizer))


    # Kick off into recursive top-down parser for a SINGLE MACRO
    # COMMAND.  For a given macro line, gets the first token, and then
    # calls into the recursive parser.  This is the public interface
    # for the parser.
    def parse_macro(self):
        if not self.__tokenizer.ready:
            raise ConfigError("Parser called without lexer ready.")

        if self.DEBUG: logger.debug("About to parse: %s" % (self.macro_line))

        # Advance to the first token
        self.__current_token = self.__tokenizer.next()
            
        # Kick off the recursive top-down descent.
        return self.__handle_command()


    # One-stop parsing solution
    def lex_and_parse_macro(self, macro_input_line, index=0):
        self.lex_macro(macro_input_line, index)
        return self.parse_macro()


    # Accessors to the tokenizer.
    def mark_token_error(self, id, index=NULL_TOKEN_ID):
        self.__tokenizer[id].error_index = index
    def mark_tokens_useless(self, start, end=-1, tok_type=None):
        # Define helper to remove repeated code.
        # If tok_type filter is specified, check it.
        def mark_toks(t, t_f=None):
            if t_f:
                if t.is_type(t_f):
                    t.strike = True
                    t.js     = False
            else:
                t.strike = True
                t.js     = False                                
        # If end is < 0 we mark everything from start on.
        if end < 0:
            for t in self.__tokenizer[start:]:
                mark_toks(t, tok_type)
        else:
            for t in self.__tokenizer[start:end]:
                mark_toks(t, tok_type)
                    
    def get_command_html(self):
        if self.__tokenizer.ready:
            return self.__tokenizer.get_command_html()
        return ''
    def get_command_str(self):
        if self.__tokenizer.ready:
            return self.__tokenizer.get_command_str()
        return ''
    def get_useless_tokens(self):
        if self.__tokenizer.ready:
            return self.__tokenizer.get_useless_tokens()
        return ''
    def get_tokens(self):
        return self.__tokenizer.get_tokens()


    # Convienience method to get a default target object. If no target
    # was specified, save a "fake" target that just refers to the
    # current target.  This makes interpretation MUCH easier later.
    def get_default_target(self, target):
        ''' Create a target tuple from a string target name. '''
        result = self.__tokenizer.get_default_target(target)
        if not result:
            return (None, None, [])
        # Mark that these tokens were created while
        # parsing, and did not come from the original
        # lexed set.
        for r in result:
            r.added = True
            r.js = False
        return (result[0], result[1], result[2:])


    # Given a parameter structure, create and return a target
    # structure.  Input is a list if (toggle, param) tuples.
    # Only the first tuple in the list is considered.
    def get_target_from_param(self, param):
        ''' Create a target tuple from a param list. '''
        if not param: return None,None,None,
        t,p = param[0]
        # [target, gets, tar, [args], [targetof...]]
        result = self.__tokenizer.get_default_target(p.data)

        # If the target command requires an argument, check for it.
        if result[2].attrs.req_num_arg and len(result) < 4:
            raise ParseErrorUnexpectedToken(None,
                                            MacroToken(TARGET_OBJ),
                                            result[2])
        # Adjust the positions and ids of the targets
        tgt_list = []
        for tgt in result[2:]:
            tgt.start = tgt.start + p.start
            tgt.end   = tgt.end   + p.end
            tgt.token_id = p.token_id
            tgt_list.append(tgt)

        # Return target tuple
        return (result[0], result[1], tgt_list)


    # Use a parameter as a target unit.  Check for
    # any illegal targeting (right now, just totems)
    # Returns a list of tokens for rendering.  Raises
    # an exception on error.
    def use_param_as_target(self, verb, param):
        if not param: return []
        for t,p in param:
            words = p.data.split()
            if len(words) > 1 and any([w.lower() == 'totem' for w in words]):
                raise ParseErrorTargetTotem(verb,
                                            p)
        return verb.attrs.param_function(param)


    #
    # Private Methods
    #

    # Advance token stream.
    def __consume_token(self, expected_type, exception=True):
        '''
        Check the current token and consume if it is the type
        requested.  Tosses an exception if there is no match
        unless exception is set to False.
        '''
        # Get the next token.
        if (self.__current_token is None) or \
           (not self.__current_token.is_type(expected_type)):
            # If we're not silent, throw an exception
            if exception:
                err = "Expected: %s, received: %s" % (expected_type,
                                                      self.__current_token.token_type)
                if self.DEBUG: logger.debug(err)
                raise ParseErrorUnexpectedToken(None,
                                                err,
                                                self.__current_token)
            else:
                return None
        # Consume the token by setting the current_token to the next one.
        consumed_token     = self.__current_token
        if len(self.__tokenizer) > 0:
            self.__current_token = self.__tokenizer.next()
        else:
            # If we're at the end of a macro, assign a null token.
            self.__current_token = MacroToken(END_OF_COMMAND)
        if self.DEBUG: logger.debug("Popping token: %s" % (consumed_token))
        if self.DEBUG: logger.debug("Current token: %s" % (self.__current_token))
        return consumed_token

        
    # command = "/", command-verb, [ {command-object, ";" } command-object] ]
    def __handle_command(self):
        '''
        Handles a complete macro command.
        Returns:
          (command_verb, [command_objects])
        '''
        if self.DEBUG: logger.debug("  self.__handle_command")

        # The command must start with a command verb.
        command_verb = self.__handle_command_verb()

        # Next come any number of command objects.
        # This is really what a macro command is: a list of objects.
        # Every command object gets its own copy of the command,
        # as every command object contains different param
        objects = [self.__handle_command_object(command_verb)]
        while self.__current_token.is_type(ELSE):
            objects.append(self.__handle_command_object(command_verb,
                                                        self.__consume_token(ELSE)))
        return (command_verb, objects)

    
    # command-object = { condition } parameters
    def __handle_command_object(self, command_verb, else_token=None):
        '''
        Handles a command object, which is the parameter and any
        conditions pertaining to it being passed to the verb.

        Because the target for the command is set in the conditions,
        each condition is grouped with a target.
        
        Returns:
          (else_token, [(target, condition)..], modifier, parameter)

        Where else_token is a token or None, target and parameter are
        lists or None, and condition is a tuple of (if, [phrases],
        endif) or None.

        '''
        if self.DEBUG: logger.debug("  self.__handle_command_object")
        
        # If the command is not secure (doesn't accept options), then
        # everything is a parameter.
        if command_verb.attrs.secure:
            target_and_condition_tuples = []

            # Apparently its legal to repeat the verb before
            # every command object--this worked in my tests.
            # So, attempt to consume another set of verb, modifer(=None).
            same_verb = self.__handle_command_verb(req=False)
            if same_verb is not None:
                if same_verb.data != command_verb.data:
                    # Verb must be the same as the original verb, or this
                    # macro fails.
                    raise ParseErrorMultipleVerbs(command_verb,
                                                  same_verb)
                # Flag the extra verb as meaningless.
                same_verb.strike = True

            # If there are no conditions, then a modifier can follow
            # the command.  Attempt to parse it here so we can throw
            # an accurate exception if its put before conditions.
            modifier = None
            if self.__current_token.is_type(MODIFIER):
                modifier = self.__handle_command_modifer(command_verb)
                
            # Empty command objects are still valid command objects.
            if self.__current_token.is_type(IF):
                # If we have a modifier already, oops.
                if modifier:
                    raise ParseErrorResetBeforeConditions(command_verb,
                                                          modifier[0],
                                                          None)

                # If there is a condition, take care of it.  There can
                # be multiple conditions.  Multiple conditions are
                # intrinisically an OR.
                while self.__current_token.is_type(IF):
                    # Each condition can specify both a conjunction
                    # of tests AND set the target the tests are run
                    # against.  Further, that target is passed to
                    # the command along with the parameters if
                    # the test passes.  Thus handle_condition returns
                    # a tuple of target and conditions.
                    target_and_condition_tuples.append(
                        self.__handle_condition(command_verb))
            else:
                # No target set, and no conditions.  Set
                # the list of target and condition tuples to None.
                target_and_condition_tuples = None

            # After conditions come the modifier.  If there is one,
            # parse it.  Should never have two.
            if self.__current_token.is_type(MODIFIER):
                modifier = self.__handle_command_modifer(command_verb)

            # After modifier come the parameter.  If there is one,
            # handle it.  There is one set of params (opt) per
            # command-object.  Not all commands require a paramter.
            parameter = self.__handle_parameters(command_verb, else_token)

            # Check the next token--if there is one, better be an else.
            if not(self.__current_token.is_type(ELSE) or \
                   self.__current_token.is_type(END_OF_COMMAND)):
                raise ParseErrorMalformedCommand(command_verb,
                                                 self.__current_token)

            # Return the tuple described in the docstring.
            return (else_token, target_and_condition_tuples, modifier, parameter,)

        # If this is not a secure command.  Parse accordingly.
        else:
            if self.DEBUG: logger.debug("  %s is an INSECURE COMMAND!" % (command_verb))
            target_condition = None
            
            # Does this verb accept targets?
            if command_verb.attrs.takes_units:
                tar_tok_list = []
                if self.__current_token.is_type(TARGET_OBJ):
                    tar_token = self.__consume_token(TARGET_OBJ)
                    # Check if %t or alpha, throw exception if
                    # the verb can't accept this target
                    if tar_token.attrs.perc_target and \
                       not command_verb.attrs.takes_perc_target:
                        # Throw exception.
                        raise ParseErrorInsecureVerbNoCurrentTarget(command_verb,
                                                                    tar_token)
                    tar_tok_list = [tar_token]

                # Does this insecure verb require a target?
                elif command_verb.attrs.req_target:
                    # throw exception.
                    raise ParseErrorInsecureVerbReqTgt(command_verb)

                # See __handle_condition and
                #__handle_target_specifier for format
                target_condition = [((None, None, tar_tok_list), None)]
                
            if self.__current_token.is_type(PARAMETER):
                return (None, target_condition, None, [(None, self.__consume_token(PARAMETER))])
            else:
                # Does it require a parameter?
                if command_verb.attrs.param_req:
                    raise ParseErrorParamRequired(command_verb)
                return (None, target_condition, None, None)


    # command-verb = ? any secure command word ?
    # Note: not entirely correct.  It should look more like this:
    # command-verb = ? verb ? {reset=option-argument}
    # However, the reset is only valid for some commands.
    def __handle_command_verb(self, req=True):
        '''
        Switch between a verb and a metaverb (i.e. #show), and handles
        any modifiers.  Optional argument to control exceptions if no
        verb token found.

        Returns:
          command_verb

        '''
        if self.DEBUG: logger.debug("  self.__handle_command_verb")
        command_verb = None

        # Consume either a meta command or a command verb
        if self.__current_token.is_type(COMMAND_VERB):
            command_verb = self.__consume_token(COMMAND_VERB, req)
        elif self.__current_token.is_type(META_COMMAND_VERB):
            command_verb = self.__consume_token(META_COMMAND_VERB, req)
        else:
            command_verb = self.__consume_token(COMMENTED_LINE, req)
        return command_verb


    # {reset=option-argument/option-argument/...}
    # (Above not really correct, fix?)
    def __handle_command_modifer(self, command_verb):
        '''
        Handle a command modifier, i.e. reset=arg/arg/arg.
        This just like a single condition phrase.

        Returns:
          (reset_token, gets_token, [option_arg_tuples])
        '''
        if self.DEBUG: logger.debug("  self.__handle_command_modifier")

        # Make sure this command TAKES a modifier.
        if not command_verb.attrs.allow_reset:
            raise ParseErrorNoResetAllowed(command_verb,
                                           self.__current_token,
                                           None)
        return (self.__consume_token(MODIFIER),
                self.__consume_token(GETS),
                self.__handle_option_arguments())


    # condition = "[" condition-phrase { "," condition-phrase } "]"
    def __handle_condition(self, command_verb):
        '''
        Handle all the options and any targets set in a single condition
        statement, i.e. [target=mouseover, combat, exists].

        Returns:
          (target, condition)
        Where target is a list or None if not specified, and condition
        is a tuple of (if, [phrases], endif)
        '''
        if self.DEBUG: logger.debug("  self.__handle_condition")

        # The condition is a flat list of tests (condition-phrases).
        # We continue to parse the condition until we reach an
        # ENDIF. Each condition can set a target at any point in the
        # condition list.  The conditions all apply to the target.  If
        # they evaluate to true, the target is passed to the
        # command-verb for action on.  NOTE: The target can be set
        # anywhere in a valid condition.  This is handled in
        # __handle_condition_phrase().
        phrases = []
        target  = []
        while not self.__current_token.is_type(ENDIF):
            # First token must be an if.
            if_token = self.__consume_token(IF)

            # Get and append the phrase
            self.__handle_condition_phrase(command_verb, target, phrases)

            # If there are more phrases, continue to append them
            while self.__consume_token(AND, False) is not None:
                self.__handle_condition_phrase(command_verb, target, phrases)

        if len(target) == 1:
            target = target[0]
        # If we got more than one target, possible parse
        # exception.
        elif len(target) > 1:
            # Did we get multiple target= or @target commands,
            # or did we get a target a different way?

            # TODO: if we have multiple targets, a couple things can happen.
            #  a) FOCUSCAST + target= command -> VALID! target= command is used, warning on focuscast
            #  b) FOCUSCAST + SELFCAST -> VALID, but use new target.
            #  c) target= + target= -> INVALID
            added_target = {}
            reg_target   = None
            for t in target:
                # Handle case c)
                if not t[0].added:
                    if reg_target:
                        raise ParseErrorMultiTargetCondition(command_verb,
                                                             t[0],
                                                             None)
                    reg_target = t
                else:
                    added_target[t[-1][-1].data] = t

            # Handle case b)
            # HACK HACK HACK HACK
            added_target = added_target.values()
            if len(added_target) > 1 and not reg_target:
                # In this case, the target of the macro depends
                # on the modifier key used.  This leads to one confusing
                # macro.  Change the target text and add a warning to it.
                target_txt = ", ".join([t[-1][-1].data for t in added_target[:-1]]) + \
                             " or " + added_target[-1][-1][-1].data + \
                             ", depending on which key was down when the macro was activated."
                target = self.get_default_target("target")
                target[-1][-1].render_desc = target_txt
                target[-1][-1].warn = ("""This macro will use different targets depending on what keys are down when activated.  Is this your intended effect?""",)
                target[-1][-1].js = False
            # Handle case a)
            elif added_target and reg_target:
                # If here, we've in a case a).  Add warning to overriding
                # regular target.
                reg_target[0].warn = ("""Setting the target to %s overrides the target set by your modifier key ('%s').""",
                                      reg_target[-1],
                                      added_target[-1][-1])
                target = reg_target

        # If we didn't get any phrases/targets, ret None in the tuple.
        if len(phrases) == 0: phrases = None
        if len(target)  == 0: target  = None

        # Finish by consuming endif, return.
        endif_token = self.__consume_token(ENDIF)
        return (target, (if_token, phrases, endif_token))
    

    # target = target {target}
    def __handle_target_specifier(self, command_verb):
        '''
        Handle target specification.
        
        Target specifications are unique in that they contain several
        actionable commands all mushed together.  For example,
        
           playertargettargettarget

        Means "target of the target of the target of the player".  In
        order to parse thois correctly, need to tokenize the target
        specifier into several tokens and handle it accordingly.

        Returns:
          (target, gets, [target_tokens])
        '''
        if self.DEBUG: logger.debug("  self.__handle_target_specifier")
        word = self.__consume_token(TARGET)

        # Patch 3.3 introduced @target alias commands.  If the target=
        # word is "target", require a gets.  Else pass.
        op = None if word.data == '@' else self.__consume_token(GETS)

        # Handle all target tokens.  First MUST be a target token
        init_target = self.__consume_token(TARGET_OBJ)
        target_list = [init_target]

        # If this target object requires a numeric arg, parse that.
        if target_list[0].attrs.req_num_arg:
            target_list.append(self.__consume_token(OPTION_ARG))

        # While we continue to get target objects, parse them.
        while self.__current_token.is_type(TARGET_OBJ):
            next_target = self.__consume_token(TARGET_OBJ)
            # Make sure this is a valid follow-on target
            if not next_target.attrs.follow:
                raise ParseErrorInvalidTargetToken(next_target)
            target_list.append(next_target)

        # Test initial target token to ensure we're not
        # totem-stomping, illegal as of 3.2.  Only viable for single-token
        # targets.
        if len(target_list) == 1:
            if any([w.lower() == 'totem' for w in init_target.data.split()]):
                raise ParseErrorTargetTotem(command_verb,
                                            init_target)
        return (word, op, target_list)

    
    # condition-phrase = [ "no" ], option-word, [ ":" option-argument { "/" option-argument } ]
    # (Note: the above is incorrect/incomplete, as it does not account for
    # target= conditions--which aren't really conditions, and are treated
    # as if they are a seperate rule.)
    def __handle_condition_phrase(self, command_verb, target_list, phrase_list):
        '''
        Handle a phrase in a condition.

        Returns: None, modifies references in place.  A target tuple
        (target, gets, [target_tokens]) is added to target_list if a
        target statement is found, and a (not, word, operator, [arg_list])
        tuple is added to phrase_list if found.
        '''
        if self.DEBUG: logger.debug("  self.__handle_condition_phrase")

        # Do we have a target assignment?  If so, handle.
        if self.__current_token.is_type(TARGET):
            target_list.append(self.__handle_target_specifier(command_verb))
            return

        # If there's a NOT, append that first.
        neg  = None
        if self.__current_token.is_type(NOT):
            neg = self.__consume_token(NOT)

        # Go in EBNF order: word, is, args.
        if self.__current_token.is_type(OPTION_WORD):
            word = self.__consume_token(OPTION_WORD)
            if self.__current_token.is_type(IS):
                # Does this option take arguments?
                if word.attrs.no_args:
                    raise ParseErrorNoArgsForOption(command_verb,
                                                    word,
                                                    self.__current_token)
                phrase_list.append((neg,
                                    word,
                                    self.__consume_token(IS),
                                    self.__handle_option_arguments(word, neg, target_list)))

            else:
                # Did this option require arguments?
                if word.attrs.req_args:
                    raise ParseErrorReqArgsForOption(command_verb,
                                                     word)
                phrase_list.append((neg, word, None, None))
        # Empty conditions are allowed, nothing is push
        return


    # option-argument { "/" option-argument }
    def __handle_option_arguments(self, word=None, neg=None, target_list=[]):
        '''

        Handle a list of arguments.  These arguments are an "OR"--no
        need to save the operator.

        If an argument drives a target acquisition, such as FOCUSCAST,
        modifies the target_list reference to add the new target.

        Returns:
          [args]
        '''
        if self.DEBUG: logger.debug("  self.__handle_option_arguments")
        new_arg = self.__consume_token(OPTION_ARG)
        arg = [new_arg]

        # Does this argument add a target, such as special
        # FOCUSCAST key checks?
        if new_arg.attrs.new_target:
            # Add the target specified by the use of the
            # modifier arg to the list.
            target_list.append(self.get_default_target(new_arg.attrs.new_target))


        # Loop and consume all or'd option-arguments
        while self.__current_token.is_type(OR):
            or_tok = self.__consume_token(OR)
            or_tok.js = False

            # If we have the form word:opt/word:opt/word:opt, handle.
            if word and \
                   (self.__current_token.is_type(NOT) or \
                    self.__current_token.is_type(OPTION_WORD)):
                # If we have a not, better match what is passed in.
                if self.__current_token.is_type(NOT):
                    repeat_neg = self.__consume_token(NOT)
                    if not neg:
                        raise ParseErrorNonMatchingNegs(neg, repeat_neg)
                repeat_word = self.__consume_token(OPTION_WORD)
                # If the repeated word doesn't match, oops.
                if repeat_word.data != word.data:
                    raise ParseErrorNonMatchingOptionWords(word, repeat_word)
                self.__consume_token(IS)

            # Handle the arg.
            new_arg = self.__consume_token(OPTION_ARG)
            arg.append(new_arg)

            # Does this argument add a target, such as special
            # FOCUSCAST key checks?
            if new_arg.attrs.new_target:
                target_list.append(self.get_default_target(new_arg.attrs.new_target))

        return arg


    # parameters = {!}parameter { "," {!}parameter } 
    # parameter = ? anything which may be passed to the command word ?
    def __handle_parameters(self, command_verb, else_token=None):
        '''
        Handles parameters, along with error checking.  If this is not
        a secure command, then only one parameter is expected.
        Otherwise, parameters can be a list, can have toggles, and
        have different types (i.e. numeric).

        Returns:
          [(toggle, parameter)...] or []
        '''
        if self.DEBUG: logger.debug("  self.__handle_parameters")
        param_list = []

        # Loop, accounting for toggleable commands.
        done = False
        while not done:
            toggle = None
            param  = None
            if self.__current_token.is_type(TOGGLE):
                toggle = self.__consume_token(TOGGLE)
                # Check if toggles are allowed.
                if not command_verb.attrs.allow_toggle:
                    raise ParseErrorNoTogglesAllowed(command_verb,
                                                     toggle)
            if self.__current_token.is_type(PARAMETER):
                param = self.__consume_token(PARAMETER)
                param_list.append((toggle, param))
                # If there are more params, there'll be an AND--consume it.
                if self.__current_token.is_type(AND):
                    self.__consume_token(AND)
            else:
                done = True

        # Error checking.
        # 0. Did the verb require a parameter without being able to
        # list its param types (i.e. targeting commands), have no
        # default param, and not get one?

        # Note: disabled to allow people to clear their targets
        # legitimately.

        #if command_verb.attrs.param_req         and \
        #   not command_verb.attrs.def_target    and \
        #   not param_list:
        #    raise ParseErrorParamRequired(command_verb)

        # 1. If the command required a parameter, did it get one?
        #    Note that if else token is not none, we can assume
        #    we got one in a previous object, therefore this command
        #    has SOMETHING to do.  If params are optional, None will
        #    be in the set of params possible for a verb.
        if command_verb.attrs.param           and \
           not command_verb.attrs.takes_units   and \
           None not in command_verb.attrs.param and \
           not else_token                       and \
           not param_list:
            raise ParseErrorParamRequired(command_verb, None, None)

        # 2. If the command required a specific parameter pattern, did
        #    we get it?
        elif command_verb.attrs.param and param_list:
            param_types = [p.data_type for (t,p) in param_list]
            last_pos = param_list[0][1].end
            if self.DEBUG: logger.debug("Command takes: %s.  Found: %s" \
                                        % (command_verb.attrs.param,
                                           param_types))
            
            # 2.1 If this command takes a list, check that all the types
            # in the list are as expected.
            if command_verb.attrs.takes_list:
                for t in param_types:
                    if tuple([t]) not in command_verb.attrs.param:
                        raise ParseErrorWrongParams(command_verb,
                                                    param_types,
                                                    last_pos)

            # 2.2 Otherwise, make sure the param pattern we got is an
            # accepted one.
            elif tuple(param_types) not in command_verb.attrs.param:
                raise ParseErrorWrongParams(command_verb,
                                            param_types,
                                            last_pos)

        # Return the parameter list or None
        if len(param_list) > 0: return param_list
        return None
