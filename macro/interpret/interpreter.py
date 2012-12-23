'''
The interpreter.

Class that contains methods to traverse a macro tree and construct
natural language output.
'''

import re

from macro.lex.token           import create_token
from macro.lex.ids             import TARGET_OBJ, OR
from macro.logger              import logger
from macro.exceptions          import *
from macro.util                import NULL_TOKEN, valid
from macro.parse.parser        import MacroParser
from macro.interpret.obj       import InterpretedMacro,InterpretedMacroCommand
from macro.interpret.txt_token import TxtToken
from macro.interpret.errors    import *
from macro.data.wow            import *

''' What external data source to use when interpreting.
This source is used to look up parameter data and some
option arguments. '''
DATA_SOURCE = SOURCE_DATASTORE


# Small helper function for testing.
def get_test_mi(debug=True, test=True, lookup=False):
    global DATA_SOURCE
    if not lookup:
        DATA_SOURCE = SOURCE_TEST
    return MacroInterpreter(debug, test)


class MacroInterpreter:
    '''MacroInterpreter

    Given a macro, break it down into commands, parse them, and then
    traverse the parse trees to construct a natural-langauge
    interpretation of the command.  The commands are then saved along
    with errors, warnings, etc, for output.

    This class creates instances of commmand.InterpretedMacro.  Each
    instance defines iterator interface is defined over the commands
    in the macro.

    Each iteration over an InterpretedMacro returns an
    InterpretedMacroCommand object, which itself iterates over
    (if_condition, do_cmd) tuples.

    Each if_condition/do_cmd is a tuple of InterpretedTokens making
    up this command.
    '''
    # Create an interpeter object.
    def __init__(self, DEBUG=False, TEST=False):
        ''' Constructor '''
        self.DEBUG = DEBUG
        self.TEST  = TEST
        self.setup()


    # Init the interpreter to parse a macro.
    def setup(self):
        # Handle to InterpretedMacro objects.
        self.__int_macro = None

        # GCD flag tracker 
        self.__gcd_map = {}

        # Not recognized tracker
        self.__unrec_map = {}

        # Ref to macro obj.
        self.__int_macro = None

        # Track the number of commands in the macro we've recieved.
        self.__num_macro_commands = 0

        # Some commands can only be used once per macro.  Track this.
        self.__single_use_cmd_seen = {}

        # Some verbs have related sets where only one in the set
        # can be used.  Track this.
        self.__related_use_cmd_seen = {}

        # Init the param cache
        self.__param_cache         = {}


    # Entry point for processing a macro.
    def interpret_macro(self, macro='', parser=None):
        '''
        Takes in a macro, splits it into commands, and interprets each
        command, storing interpretation state in this object.
        
        Returns:
        Ref to InterpretedMacro object.
        '''
        # Set up to parse a new macro.
        self.setup()
        self.curr_macro            = macro
        self.__int_macro           = InterpretedMacro(macro)
        
        # Get a parser object
        self.parser = parser or MacroParser(debug=self.DEBUG)

        # Make sure we have input--this should be done above this level.
        if not valid(macro):
            raise InitError("No valid macro input.")

        # Split up the macro for parsing.
        macro_lines = re.compile("\r*\n+").split(macro)
        cmd_len = len('\n'.join(macro_lines))
    
        # Iterate and clean out spaces, getting an accurate count
        # of the lines.
        valid_macro_lines = []
        for macro_line in macro_lines:
            # Get rid of empty lines--and remember that we "changed" the macro
            # by dropping them.
            if len(macro_line) == 0 or macro_line.isspace():
                self.__int_macro.macro_changed = True
                continue
            valid_macro_lines.append(macro_line)
            self.__num_macro_commands = len(valid_macro_lines)

        # Iterate and interpret macro, splitting on /r and /n
        for i, macro_line in enumerate(valid_macro_lines):
            # Make sure that the macro is less than the supported limit.
            # If its more, throw an exception.
            if cmd_len > MAX_LEN_ALLOWED:
                raise MacroLenError(MACRO_LEN_ERROR % (cmd_len, MAX_LEN_ALLOWED))

            # Get rid of empty lines--and remember that we "changed" the macro
            # by dropping them.
            if len(macro_line) == 0 or macro_line.isspace():
                self.__int_macro.macro_changed = True
                continue

            # Init for a new macro command.
            self.__init_new_command(macro_line)
    
            # Lex and parse the macro line.
            # Then inteperet the resulting parse tree.
            try:
                parse_tree = self.parser.lex_and_parse_macro(macro_line, i)
                self.interpret_macro_command(parse_tree)

                # Lexer error
            except LexerError, instance:
                start = instance.get_start()
                end   = instance.get_end()
                msg   = "%s" % instance
                
                # Generate some fake tokens so we can show the error at the
                # correct location.
                beg_tok  = create_token(token_type=NULL_TOKEN, data=macro_line[:start],    token_id=0, index=i)
                prob_tok = create_token(token_type=NULL_TOKEN, data=macro_line[start:end], token_id=1, index=i)
                end_tok  = create_token(token_type=NULL_TOKEN, data=macro_line[end:],      token_id=2, index=i)

                # Save lexer error at the problem input
                prob_tok.error = (msg,)

                # Turn on errors/js/highlighting for the error tok.
                prob_tok.js = True
                prob_tok.highlight = True
                
                # Save the command for display.
                self.__save_command([beg_tok, prob_tok, end_tok])
                
                # Report error on interpretation side.
                self.__save_interpret([TxtToken(txt=LEXER_ERROR)])
                
                # Save the raw command as the "clean" one since we
                # have no idea what to do with it.
                self.__save_clean_raw_command(macro_line)
                
                # Mark that this macro has issues
                self.__int_macro.macro_good = False
                self.__new_cmd.error = True

                if self.TEST: raise
                continue

            # Critical error.  Return. 
            except OtherError, instance:
                raise InitError("Error executing lexing engine.  Valid input?")

            # Error parsing or interpreting the macro command
            except (ParserError, InterpretError), instance:
                cmd   = instance.cmd
                token = instance.get_token()
                msg   = instance
                if token: token.error = ("%s", instance.get_render_list())

                # Since the command lexed, we can save it out properly for display.
                self.__save_command(self.parser.get_tokens())
                
                # Report error on interpretation side.
                self.__save_interpret([TxtToken(txt=PARSER_ERROR)])
                
                # Save the lexed, cleaned command
                self.__save_clean_raw_command(self.parser.get_command_str(), macro_line)
        
                # Mark that this macro has issues
                self.__int_macro.macro_good = False
                self.__new_cmd.error = True
                if self.TEST: raise
                continue

            # Save the lexed tokens for rendering.
            self.__save_command(self.parser.get_tokens())
            
            # Save cleaned raw command, and whether we cleaned anything.
            clean_cmd_str = self.parser.get_command_str()
            self.__save_clean_raw_command(clean_cmd_str, macro_line)
            
        # Add in the newlines to the macro length so that it is reported
        # correctly.
        self.__int_macro.macro_len += self.__num_macro_commands - 1
            
        # Done, return macro object.
        return self.__int_macro


    # Entry point for interpreting a command.  This takes a parse tree
    # for a single command and interprets it.
    def interpret_macro_command(self, command_obj):
        '''
        Takes the parse tree for a single command and interprets it,
        saving the results internally.
        
        Functions down the chain can throw exceptions.
        '''
        # A command is a tuple of (verb, [objects])
        verb, objects = command_obj

        # If this is a single-use verb (i.e. targetenemy), have we already
        # seen it previously in a macro?
        if verb.attrs.only_usable_once:
            if verb.data in self.__single_use_cmd_seen:
                # Whoops, yup.
                raise InterpetErrorSingleUseCommandViolated(verb)
            self.__single_use_cmd_seen[verb.data] = True

        # If this is part of a group where only one can be used.
        # check.
        if verb.attrs.related:
            for v in verb.attrs.related:
                if v in self.__related_use_cmd_seen:
                    # Whoops, yup. Mark this command as useless.
                    verb.error = (WARN_RELATED_COMMAND, [verb], [TxtToken(v)])
                    self.parser.mark_tokens_useless(verb.token_id)
                    return
            self.__related_use_cmd_seen[verb.data] = True

        # Need to go through each of the objects and interpret each one,
        # applying the verb and modifier to each set of parameters.
        prev_evals_to_true = False
        for i, obj in enumerate(objects):

            # Eval the object, all objects after the first one get "else"
            # prepended to conditions.
            evals_to_true = self.__interpret_cmd_object(obj, verb, (i > 0))
            if self.DEBUG: logger.debug("evals: %s, i: %s, prev_evals: %s" \
                                        % (evals_to_true, i, prev_evals_to_true))

            # Check for problem patterns if there is more than one object.
            if len(objects) > 1:
                # Command object: (else, [conditions], parameter)
                else_token, conditions, mod, param = obj

                # If this object is always true, warn that all other command
                # objs are a waste of space and return.
                if evals_to_true and i < (len(objects) - 1):
                    next_else_token, next_conds, next_mod, next_param = \
                                     objects[i + 1]
                    # Mark the tokens as useless from the else on.
                    self.parser.mark_tokens_useless(next_else_token.token_id)

                    # Go through the token queue for this command and
                    # add a warning for all useless characters.  Right
                    # now this only works for extra verb commands, but
                    # could be expanded.  Note: I'm sure there's a
                    # cleaner way to rewrite the below.
                    useless_groups = []
                    accum = []
                    for t in self.parser.get_tokens():
                        if t.strike: accum.append(t)
                        elif len(accum) > 0:
                            useless_groups.append(accum)
                            accum = []
                    if len(accum) > 0: useless_groups.append(accum)
                    for group in useless_groups:
                        for t in group:
                            t.js = False
                            t.wowhead = False
                        group[-1].error = (WARN_UNUSED_TOKENS, group)
                    return

                # If this is the last object and the previous object did NOT
                # automatically evaluate to true, then this command may have
                # unintended effects.    Warn if there are no parameters!
                if not prev_evals_to_true and i == (len(objects) - 1) \
                             and param is None:
                    else_token.warn = (WARN_UNINTENDED_ELSE, [else_token], [else_token], [verb])
            prev_evals_to_true = evals_to_true



    #
    # Internal Methods
    #
    
    def __init_new_command(self, macro, interpret=None):
        ''' Add a record for a new command. '''

        # Clear interpretation maps
        self.__gcd_map     = {}
        self.__unrec_map = {}

        # Insert a new command structure
        self.__new_cmd = InterpretedMacroCommand(cmd=macro,
                                                 index=len(self.__int_macro))
        self.__int_macro.add_cmd(self.__new_cmd)

    def __save_interpret(self, do_list, if_list=[]):
        ''' Save an interpretation for this macro in (if,do) tuples,
        where if and do are lists of tokens for rendering.'''
        self.__new_cmd.interpret.append((if_list, do_list))

    def __save_command(self, tok_list):
        ''' Save a macro command as a tuple of tokens to be rendered. '''
        self.__new_cmd.cmd_list = tok_list

    def __save_clean_raw_command(self, cmd_str, orig_raw_cmd=None):
        ''' Save a macro command string.  Also save whether a macro
        command changed or not.  Add to the macro len, considering
        only the cleaned version and a newline character.'''
        self.__new_cmd.cmd_str = cmd_str
        if orig_raw_cmd and cmd_str != orig_raw_cmd:
            self.__int_macro.macro_changed = True
        self.__int_macro.macro_len += (len(cmd_str) + 1)

    # For testing only
    def __str__(self):
        ret = ['\n']
        # Add any init errors.
        for cmd in self.__int_macro:
            cmd_ret = ['\n']
            cmd_ret.append("COMMAND:\n%s\n" % cmd.cmd)
            cmd_ret.append("INTERPRETATION:\n%s\n" % ', '.join(map(str, cmd.interpret)))
            ret.append('\n'.join(cmd_ret))
        return ''.join(ret)


    #
    # Interpretation Methods (Internal)
    #

    # Handle a command object.
    def __interpret_cmd_object(self, obj, verb, add_else=False):
        '''
        Consumes a command object from the parse tree.    Adds output to
        internal state.    Returns True if there were no conditions
        or if the condition was empty, False otherwise.
        '''
        # Command object: (else, [conditions], parameter)
        else_token, conditions, mod, param = obj

        # If we have no conditions, just interpret the verb.
        if conditions is None:
            render_list = self.__interpret_verb(verb, mod, param, target=None)
            if add_else:
                else_token.render_desc = "Otherwise:"
                else_token.render_space_after = False
                self.__save_interpret(render_list, [else_token])
            else:
                self.__save_interpret(render_list)
            return True
        
        # Each condition really drives what gets passed to the command
        # verb.  Go through the list and interpret.
        condition_map = {}
        for i,cond in enumerate(conditions):
            # The last condition gets an else in its interpretation if there
            # was more than one condition in the command.
            if len(conditions) > 1 and i > 0:
                add_else = True

            if self.DEBUG: logger.debug("len: %s, i: %s, else: %s" % (len(conditions), i, add_else))

            # If we hit an empty condition and there are still more
            # conditions to process, we're done--the other conditions
            # will never be executed. Add a warning.
            # interpret_condition returns the endif token if the condition
            # was empty so that we can assign an error to it if nec.
            endif_token = \
                self.__interpret_condition(cond, verb, mod, param, condition_map, add_else)
            if endif_token is not None:
                # We have an empty condition.  If there are any other
                # conditions, they should not be here.
                if i < (len(conditions) - 1):
                    # Mark the extra conditions as useless, starting from the first if
                    # and ending including the last endif
                    start = self.__unpack_condition(conditions[i + 1])[1]
                    end     = self.__unpack_condition(conditions[-1])[3]
                    self.parser.mark_tokens_useless(start.token_id, end.token_id+1)
                    endif_token.warn = (WARN_UNUSED_CONDITIONS, [verb])
                return True
        return False
    
        
    # Handle a conditional
    def __interpret_condition(self, cond, verb, mod, param, condition_map, add_else=False):
        '''
        Consume a condition, adding output from its interprtaion to
        internal state.    Returns None if the condition had phrases,
        the end_if token iff the condition was empty.
        '''
        target, if_token, phrases, endif_token = self.__unpack_condition(cond)

        if self.DEBUG: logger.debug("TARGET: %s COND: %s" % (target, cond))

        # Get the command verb output for this condition.
        verb_render_list = self.__interpret_verb(verb, mod, param, target)

        # If there's no condition to evaluate, save the verb
        # interpretation and return.
        if not if_token:
            self.__save_interpret(verb_render_list)
            return None

        # Evaluate the phrases in the condition and save.
        if_render_list = []
        if if_token:
            phrase_render_list = []
            # Special case: no options!    This condition defaults to true.
            # Don't even bother with the if-statement.
            if phrases is None:
                if add_else:
                    if_token.render_desc = "Otherwise:"
                    self.__save_interpret(verb_render_list,
                                          [if_token])
                else:
                    self.__save_interpret(verb_render_list)
            else:
                endif_token.render_desc = "then:"
                endif_token.render_space_after = False
                if self.DEBUG: logger.debug("About to interpret phrases.")
                phrase_render_list = self.__interpret_phrases(verb, phrases, target) + [endif_token]
                if add_else:
                    if_token.render_desc = "if"
                    if_render_list = [TxtToken(txt="Else,"), if_token] + phrase_render_list
                else:
                    if_token.render_desc = "If"
                    if_render_list = [if_token] + phrase_render_list

            # If this is a repeat condition in this command, remove it
            # instead out outputting it.  We check repeats using a
            # map passed in by reference.
            condition_key = [t.get_render_desc() for t in phrase_render_list]
            condition_key.sort()
            condition_key = ''.join(condition_key)
            if condition_key in condition_map:
                # Oops.  Repeat condition.  Cut out extra tokens and
                # add error.
                self.parser.mark_tokens_useless(start=if_token.token_id,
                                                end=endif_token.token_id+1)
                endif_token.warn = (WARN_REPEATED_CONDITION,)
                return
            condition_map[condition_key] = True

        # Only save if there were phrases to save.
        if phrases is not None:
            self.__save_interpret(verb_render_list, if_render_list)
            return None
        # Otherwise, return the endif for error assignment.
        else:
            return endif_token


    # Command verb
    def __interpret_verb(self, verb, mod, param, target):
        '''
        Interpret a command verb, including its modifier, target,
        and parameter.    Returns a string interpretation.
        '''
        if self.DEBUG: logger.debug("params: v: %s m: %s p: %s t: %s" % (verb, mod, param, target))

        #
        # Parameter
        #

        # Next process the parameter, if there is one.
        param_render_list = []
        if verb.attrs.secure and param and not verb.attrs.takes_units:
            # Look up parameters based on what the verb takes.
            for t,p in param:
                if p.data_type is int: continue # Only look up str
                p_obj = None
                if verb.attrs.takes_item:
                    p_obj = get_wow_object(p.data, is_item=True, src=DATA_SOURCE, cache=self.__param_cache)
                if not p_obj and verb.attrs.takes_spell:
                    p_obj = get_wow_object(p.data, src=DATA_SOURCE, cache=self.__param_cache)
                if p_obj:
                    p.attrs.param_data_obj = p_obj
                    p.render_desc = p_obj.get_name()
                    p.wowhead = True
                    
            # Add any GCD warnings and interpret
            self.__add_gcd_warnings(verb, param)
            param_render_list = verb.attrs.param_function(param)
        elif not verb.attrs.secure and param:
            # Interpret parameters for insecure verbs
            param_render_list = verb.attrs.param_function(param)
        elif verb.attrs.param_req and not verb.attrs.takes_units:
            # Some verbs make no sense without SOMETHING for the
            # parameters.
            req_param = param
            if not req_param:
                # The parser takes care of illegal verb
                # forms for us, so this is in the case of a trailing
                # ";".
                req_param = [(None, TxtToken("nothing"))]
            param_render_list = verb.attrs.param_function(req_param)


        #
        # Target
        #

        # If the command sets targets, use the parameter as the
        # target.  In this case we will only need a target string,
        # so we do not create a parameter string.
        target_render_list = []
        if verb.attrs.secure and verb.attrs.takes_units:
            # Check if a target was set in the conditional that is the
            # key unit for this command. If this is true or if there
            # is no target set, the parameters are used as the target.
            if not target or self.__target_is_key_unit(verb, target):
                # If we have a parameter, set the param as the
                # target of this command.
                if param:
                    # If the verb recognizes target mofidiers, render
                    # the param as a target.
                    if verb.attrs.interp_target:
                        target_render_list = \
                          self.__interpret_param_as_target(verb, param)
                    else:
                        # Take the first parameter verbatim
                        target_render_list = [param[0][1]]
                # Otherwise get the default target
                else:
                    target_render_list = \
                        self.__interpret_target(self.parser.get_default_target(verb.attrs.def_target),
                                                verb, js=False)
            elif target:
                # Otherwise, the unit in the parameters is ignored.
                # Render and add a warning if there's a param.
                target_render_list = self.__interpret_target(target, verb, js=False)
                if param:
                    target[0].warn = (WARN_NOT_KEY_UNIT,
                                      verb.attrs.param_function(param),
                                      [TxtToken(verb.attrs.key_unit)],
                                      verb.attrs.param_function(param),
                                      [TxtToken(verb.attrs.key_unit)])
        # If we're incorporating the target into the verb string,
        # don't include highlights
        elif verb.attrs.alt_desc and target:
            target_render_list = self.__interpret_target(target, verb, js=False)
        # If this is a list verb that requires an external target, assign a
        # target per parameter and re-render the target list in the
        # parameter function
        elif param and verb.attrs.takes_ext_target and verb.attrs.takes_list:
            targets = []
            for t,p in param:
                if p.attrs.self_only or (p.found() and p.attrs.param_data_obj.self_only()):
                    targets.append([TxtToken(txt="yourself")])
                else:
                    targets.append(self.__interpret_target(target, verb))
            param_render_list = verb.attrs.param_function(param, targets)
        # Otherwise, just render the target as-is.
        elif verb.attrs.req_target:
            # Does the parameter influence the target?  I.e. some spells
            # are self-cast only. If so get a default "player" target.
            # Note that we're sure this is not a list param here.
            if param:
                t,p = param[0]
                if p.attrs.self_only or (p.found() and p.attrs.param_data_obj.self_only()):
                    target_render_list = [TxtToken(txt="yourself")]
            if not target_render_list:
                target_render_list = self.__interpret_target(target, verb)


        if self.DEBUG: logger.debug("target_render_list: %s" % target_render_list)
        if self.DEBUG: logger.debug("Param Obj: %s" % param)
        if self.DEBUG: logger.debug("Param: %s" % param_render_list)
        if self.DEBUG: logger.debug("Target Obj: %s" % str(target))
        if self.DEBUG: logger.debug("Target: %s" % str(target_render_list))


        # Handle modifier if there is one
        mod_render_list = []
        if mod is not None:
            # (reset_token, gets_token, [option_arg_tuples])
            reset_tok, gets_token, mod_args = mod

            # Piece together the args.    Unfortunately, this is a bit
            # different than handling an options list.
            for mod_arg in mod_args:
                if mod_arg.data_type is int:
                    mod_arg.render_desc = "after %s seconds" % mod_arg.data
                    mod_render_list.append([mod_arg])
                elif mod_arg.attrs.is_reset_arg:
                    if mod_arg.attrs.is_key:
                        mod_arg.render_desc = "this macro is activated with the %s down" % mod_arg.data
                        mod_render_list.append([mod_arg])                    
                    else:
                        mod_render_list.append([TxtToken("if"), mod_arg])
                else:
                    # Oops, invalid argument.  Interpret error!
                    raise InterpetErrorInvalidResetOption(mod_arg)
            mod_render_list = self.__interleave_join(mod_render_list, last_delim=", or", flatten=True)

            # Prepend the reset the command
            reset_tok.render_desc = "resetting the sequence"
            mod_render_list = [reset_tok] + mod_render_list

        if self.DEBUG: logger.debug("target_render_list later in function: %s" % target_render_list)

        # Construct the command description, and punctuation.
        final_render_list = verb.attrs.assemble_function(verb,
                                                         param_render_list,
                                                         mod_render_list,
                                                         target_render_list)
        return final_render_list


    # Phrases
    def __interpret_phrases(self, verb, phrases, target):
        '''
        Helper to handle phrase output for conditionals
        Returns a list of renderable tokens.
    
        Phrases is a list of phrases, where each element is a tuple:
        (not, word, operator, [arg_list])
        '''
        # Since a list of phrases is a conjunction, all must be true
        # in order for the condition to be true.    Therefore they are ALL
        # evaluated.
        #
        # Note that it is entirely possible for a given condition to have
        # phrases referring to self AND a target ([combat, harm] for
        # example).
        #
        # To make the condition easier to understand, we will group phrases
        # by the targets they refer to.    For example, instead of:
        #
        # If target is in combat and target exists and target is an enemy...
        #
        # We want:
        #
        # If target is in combat, exists, and is an enemy...
        #
        # To do this we'll attach each condition phrase to the target
        # it refers to.    We do this via a map.
        tgt_to_phrase = {}
        tgt_order_list = []

        # Break down each phrase and interpret.
        condense_map = {}
        phrase_map = {}
        target_self = self.__target_self(target)
        refers_only_to_self = True
        for phrase in phrases:
            negate, word, operator, args = phrase

            # If we have a not, mark it up.
            if negate:
                negate.render_desc = "not"
            else:
                negate = None

            # If this is a metaverb and this option requires an
            # action, add a warning.
            if word.attrs.action and verb.attrs.meta:
                word.warn = (WARN_ACTION_OPTION_IN_META, [word], [verb])

            # Set a target, and get the join word.
            tgt = ()
            tgt_join = []
            if not word.attrs.ext_target:
                # Option refers to self only, get default target of "you"
                tgt = tuple(self.__interpret_target())
                if word.attrs.req_join: tgt_join = [TxtToken(txt="are")]
            else:
                refers_only_to_self = False
                # Tgt needs to be a tuple in order to use a map.
                if self.DEBUG: logger.debug(" --> getting default target.")
                if self.DEBUG: logger.debug(" --> tar: %s verb: %s word: %s" % (target, verb, word))
                tgt = tuple(self.__interpret_target(target, verb, word))
                if word.attrs.req_join: tgt_join = self.__get_target_join(target, verb)
                if self.DEBUG: logger.debug(" ----> tgt_join: [%s]" % (tgt_join))
            
            # Make sure we have a list init'd for this target, and
            # save the order in which we saw targets
            tgt_key = ''.join([t.get_str() for t in tgt])
            if self.DEBUG: logger.debug(" ----> tgt_key: [%s]" % (tgt_key))
            if tgt_key not in tgt_to_phrase:
                tgt_order_list.append((tgt,tgt_key))
                tgt_to_phrase[tgt_key] = []

            # Handle argument list and construct the phrase
            arg_list = []
            if args:
                agg_args = {}
                for arg in args:
                    # Repeated argument?  Nuke.
                    if arg.data in agg_args:
                        # Turn off rendering for both the arg
                        # and the or behind it, if there was one.
                        self.parser.mark_tokens_useless(start=arg.token_id-1,
                                                        end=arg.token_id,
                                                        tok_type=OR)
                        self.parser.mark_tokens_useless(start=arg.token_id,
                                                        end=arg.token_id+1)
                        arg.warn   = (WARN_UNUSED_REPEATED_ARGS, [arg])
                    else:
                        agg_args[arg.data] = arg
                        # If there are default warnings, add them.
                        if arg.attrs.warn:
                            arg.warn = (arg.attrs.warn,)
                        # If the word takes params, look them up.
                        if word.attrs.can_take_spell:
                            arg.attrs.param_data_obj = get_wow_object(arg.data, src=DATA_SOURCE, cache=self.__param_cache)
                        # Is this a valid option arg?
                        if not arg.attrs.is_option_arg:
                            raise InterpetErrorInvalidConditionArg(word,arg)
                args = agg_args.values()
                if len(args) == 1:
                    arg_list = args
                elif len(args) < 3:
                    arg_list = self.__interleave_join(args, delim=" or")
                elif len(args) >= 3:
                    arg_list = self.__interleave_join(args, delim=",", last_delim=", or")
                
            # Check: Do we see duplicates of the same phrase in the
            # condition.  We do this AFTER we check for duplicate
            # arguments in case removing dup arguments creates a dup
            # phrase.  We use the tuple elements instead of phrase
            # since arg could have been updated.
            phrase_key = ''.join(map(lambda p: p.data if (p and type(p) is not list) else ''.join([i.data for i in p]) if p and type(p) is list else '', (negate, word, operator, args)))
            if phrase_key in phrase_map:
                # Repeated phrase detected.  Remove it.
                first_tok = negate if negate else word
                last_tok = args[-1] if args else word

                # Add a note.
                last_tok.warn = (WARN_REPEATED_PHRASE,)

                # Note we start at the AND token prior to the word.
                self.parser.mark_tokens_useless(start=first_tok.token_id-1,
                                                end=last_tok.token_id+1)
                continue
            phrase_map[phrase_key] = True

            # Check to see if we can condense arguments to save space.
            if word.data in condense_map:
                # Woops, yeah can condense.  For now just trigger error.
                word.warn = (WARN_REPEATED_OPTION_WORD,)
            condense_map[word.data] = True

            # Save the option interpretation, and attach to this target.
            if tgt_join:
                tgt_to_phrase[tgt_key].append(tgt_join + word.attrs.assemble_function(word, negate, arg_list, target_self))
            else:
                tgt_to_phrase[tgt_key].append(word.attrs.assemble_function(word, negate, arg_list, target_self))
        if self.DEBUG: logger.debug("tgt_to_phrase: " + str(tgt_to_phrase))

        # If the entire condition refers only to the player and the
        # user specified an external target in this condition, then
        # the target is ignored.
        if refers_only_to_self and target and not target_self and not verb.attrs.takes_ext_target:
            target[0].warn = (WARN_CONDITIONS_PLAYER, [verb])

        # If the user specified target=player, all other conditions
        # only check self, and the verb doesn't take external targets,
        # the target can be removed.
        if target_self and phrases and refers_only_to_self and not verb.attrs.takes_ext_target:
            target[0].warn = (WARN_TARGET_USELESS_SELF, [verb])
            
        # If the user targets self with phrases and not all conditions are
        # self-only, this could be a problem.
        if target_self and phrases and not refers_only_to_self:
            target[0].warn = (WARN_TARGET_SELF,)

        # Output each phrase list along with the target it refers to.
        phrase_list = []
        for idx,t_tuple in enumerate(tgt_order_list):
            (obj, t) = t_tuple
            tgt_list = list(obj)
            # If there's just one phrase for the target, not a list.
            to_add = []
            if len(tgt_to_phrase[t]) == 1:
                to_add = tgt_to_phrase[t][0]
            if len(tgt_to_phrase[t]) == 2:
                to_add = self.__interleave_join(tgt_to_phrase[t], space_before=True, delim="and", flatten=True)
            else:
                to_add = self.__interleave_join(tgt_to_phrase[t], last_delim=", and", flatten=True)
            phrase_list += tgt_list + to_add
            # Add a interpret conjunction across targets
            if (idx + 1) < len(tgt_to_phrase):
                phrase_list.append(TxtToken("and"))
        return phrase_list

    
    # Helper to get the join string for a target.
    def __get_target_join(self, target, verb):
        '''
        Get a target join string to the condition examining it.    Returns
        the empty string for any error, or if no join string needed.
        '''
        if self.DEBUG: logger.debug("Getting target join for target: %s verb: %s" % (target, verb))
        # If we don't have a target, get the default from the parser.
        if target is None:
            if verb is not None and verb.attrs.def_target:
                target = self.parser.get_default_target(verb.attrs.def_target)
            elif verb is not None and verb.attrs.takes_ext_target:
                target = self.parser.get_default_target("target")
            else:
                target = self.parser.get_default_target("player")
        # (target, gets, [target_tokens])
        tar_tok, eq_tok, tgt_args = target
        # If its a target, return the join.
        if tgt_args[-1].token_type == "TARGET_OBJ":
            if tgt_args[-1].attrs.use_are:
                return [TxtToken(txt="are")]
        return [TxtToken(txt="is")]

        
    # Helper to assemble a target string.
    def __interpret_target(self, target=None, verb=None, word=None, js=True, was_param=False):
        '''
        Intepret a target.  Returns a list of renderables.
        '''
        if self.DEBUG: logger.debug("TARGET: %s, VERB: %s" % (target, verb))

        # If we don't have a target, get the default from the parser.
        if not target:
            if verb and verb.attrs.def_target:
                target = self.parser.get_default_target(verb.attrs.def_target)
            elif word and word.attrs.def_target:
                if self.DEBUG: logger.debug("  -> Getting default for: %s" % word.attrs.def_target)
                target = self.parser.get_default_target(word.attrs.def_target)
            else:
                target = self.parser.get_default_target("player")
            # For the default target, turn off highlighting.
            js = False

        # (target, gets, [target_tokens])
        tar_tok, eq_tok, tgt_args = target

        render_list = []
        for tgt_arg in tgt_args:
            # If JS for this target is already off, respect that.
            tgt_arg.js = (tgt_arg.js and js)

            if tgt_arg.is_type(TARGET_OBJ):
                # Warn on unit name targets
                if not tgt_arg.attrs.recognized and len(tgt_args) > 1 and not was_param:
                    tgt_arg.warn = (WARN_TARGET_PARTY_OR_SELF, [TxtToken(tgt_arg.render_desc)], [TxtToken(tgt_arg.render_desc)])
                # Modify target for readibility.
                if len(render_list) == 0:
                    if tgt_arg.attrs.inc_the:
                        render_list.extend([TxtToken("the"), tgt_arg])
                    # Do we need to prepend "your"?
                    elif tgt_arg.attrs.use_your:
                        render_list.extend([TxtToken("your"), tgt_arg])
                    # If 'player' and part of a chain, then you -> your
                    elif tgt_arg.data == 'player' and len(tgt_args) > 1:
                        tgt_arg.render_desc  = "your"
                        render_list.append(tgt_arg)
                    else:
                        render_list.append(tgt_arg)
                else:
                    last = render_list[-1]
                    # If nec, make possessive of the last token, get
                    # rid of space.
                    if not last.is_type(TARGET_OBJ) or last.attrs.use_ap_s:
                        last.render_space_after = False
                        render_list.extend([TxtToken("'s"), tgt_arg])
                    else:
                        render_list.append(tgt_arg)                        
            else:
                render_list.append(tgt_arg)

        if self.DEBUG: logger.debug("target render_list: %s" % render_list)
        return render_list
    
    
    # Helper to assemble a target string from a parameter list.
    def __interpret_param_as_target(self, verb, param):
        '''
        Intepret a parameter object as a target.  Returns
        target_render_list.
        '''
        if param is None: return []

        # If this verb doesn't accept unit ids, then there is no reason
        # to try and convert the param into a target and look it up in
        # the unitid table.
        if not verb.attrs.takes_units:
            return []
    
        # Convert [(toggle, parameter)...] to (target, gets, [target tokens])
        try:
            new_target = self.parser.get_target_from_param(param)
            return self.__interpret_target(new_target, was_param=True)
        except:
            pass

        # Otherwise, return rendered param string.
        return self.parser.use_param_as_target(verb, param)

    
    # Helper
    def __target_is_key_unit(self, verb, target):
        '''
        Helper to determine if a target object contains the verb
        key unit.    Returns True/False.
        '''
        if verb is None: return False

        # All insecure verbs do not have key units.
        if not verb.attrs.secure: return False

        # Does this command even have a key unit?    Not all targeting
        # commands do.    Honor the parameter regardless if so.
        if not verb.attrs.key_unit: return True
    
        # If no target was set in a condition, then the effect
        # is the same as if the target was the key unit--the
        # parameter will be honored.
        if target is None: return True
             
        # (target, gets, [target_tokens])
        tar_tok, eq_tok, tgt_args = target
    
        # If we got a compound unit, join the data together before
        # checking.
        test_target = ''
        if (len(tgt_args) > 1):
            test_target = ''.join([t.data for t in tgt_args])
        else:
            test_target = tgt_args[0].data

        # Test to see if the target is the key unit
        if test_target != verb.attrs.key_unit: return False
        return True

    
    # Helper to see if we're targeting ourself.
    def __target_self(self, target):
        '''
        Given a target parse tree, check to see if the player
        has targeted themselves.
        '''
        if not target: return False
        tar_tok, eq_tok, tgt_args = target
        return (len(tgt_args) == 1 and tgt_args[0].data == 'player')


    # Helper for GCD warnings
    def __add_gcd_warnings(self, verb, param):
        '''
        Helper to add warnings for potential GCD problems
        from parameters.    Returns nothing.
        '''
        if verb is None or param is None: return

        # Does the verb itself cost GCD by default?
        if verb.attrs.gcd and (self.__new_cmd.index + 1) < self.__num_macro_commands:
            verb.warn = (WARN_VERB_GCD, [verb])

        # Otherwise, go through params and add warnings for GCD.
        for tog, p in param:
            if p is None: continue

            # If this command expects a spell ONLY
            if verb.attrs.takes_spell and not verb.attrs.takes_item:
                # Did we recognize this spell?
                if not p.attrs.param_data_obj and not p.attrs.is_empty and p not in self.__unrec_map:
                    p.warn = (WARN_UNKNOWN_SPELL,)
                    self.__unrec_map[p] = True
                # Did we find an item instead of a spell?
                elif p.attrs.is_item_id_param or \
                     (p.attrs.param_data_obj and p.attrs.param_data_obj.is_item() and p not in self.__unrec_map):
                    p.warn = (WARN_ITEM_INSTEAD_OF_SPELL, [verb], [p])
                else:
                    # Does this command trip the GCD?
                    # Only really relevant if this isnt the last command.
                    if p.attrs.param_data_obj and p.attrs.param_data_obj.trips_gcd() and \
                           (self.__new_cmd.index + 1) < self.__num_macro_commands and \
                           p not in self.__gcd_map:
                        p.warn = (WARN_SPELL_GCD, [p])
                        self.__gcd_map[p] = True

            # . . .or uses an item ONLY . . .
            elif verb.attrs.takes_item and not verb.attrs.takes_spell \
                     and not p.data_type is int:
                # Did we recognize an item
                if not p.attrs.param_data_obj and p not in self.__unrec_map:
                    p.warn = (WARN_UNKNOWN_ITEM,)
                    self.__unrec_map[p] = True
                # Is this as spell?
                elif p.attrs.param_data_obj and p.attrs.param_data_obj.is_spell():
                    p.warn = (WARN_SPELL_INSTEAD_OF_ITEM, [verb], [p])
                # If found, GCD warning (if this isnt the last command)
                elif p.attrs.param_data_obj and p.attrs.param_data_obj.trips_gcd() and p not in self.__gcd_map and \
                     (self.__new_cmd.index + 1) < self.__num_macro_commands:
                    p.warn = (WARN_ITEM_GCD, [verb], [p])
                    self.__gcd_map[p] = True


    # Simple helper to unpack a conditional
    def __unpack_condition(self, cond):
        '''
        Unpack a condition and return it as a flat list.
        '''
        # A condition is a tuple of (target, condition), and a condition
        # is a tuple if (if, [phrases], endif)
        target, condition = cond
    
        # If the condition is not none, unpack it.
        # Otherwise this is a target for an insecure verb.
        if condition:
            if_token, phrases, endif_token = condition
            return (target, if_token, phrases, endif_token)
        return (target, None, None, None)

  
    # Simple helper to interleave list with a delimiter text token.
    # Last delimiter is only used on lists with length > 2
    def __interleave_join(self, token_list, delim=",", last_delim=None, space_before=False, flatten=False):
        ret_list = []
        if not token_list: return ret_list
        for i,e in enumerate(token_list):
            if i > 0:
                if last_delim and i + 1 == len(token_list) and len(token_list) > 2:
                    ret_list.append(TxtToken(txt=last_delim))
                else:
                    ret_list.append(TxtToken(txt=delim))
            if not space_before and i + 1 < len(token_list):
                if flatten:
                    e[-1].render_space_after = False
                else:
                    e.render_space_after = False
            if flatten:
                ret_list.extend(e)                
            else:
                ret_list.append(e)
        return ret_list
