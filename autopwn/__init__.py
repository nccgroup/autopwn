#!/usr/bin/env /usr/bin/python

import argparse
import copy
import operator
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from distutils.spawn import find_executable
from locale import getlocale
from subprocess import Popen, PIPE
from time import gmtime, strftime

import inquirer
from screenutils import list_screens, Screen
import yaml

# Aidan Marlin @ NCC Group
# Project born 201502

class Log:
    def __init__(self, config, directory, log_filename, log_type, log_string):
        date = strftime("%Y%m%d")
        date_time = strftime("%Y%m%d %H:%M:%S %z")

        if log_type == 'tool_output':
            try:
                # log_filename is pikey, make it better
                log_file = open(directory + "/" + date + "_autopwn_" + \
                                log_filename + "_stdout.log","a")
            except OSError as e:
                print("[E] Error creating log file: " + e)
                sys.exit(1)

            log_file.write(log_string)
            log_file.close()

        if log_type == 'tool_string':
            try:
                log_file = open(date + "_autopwn_commands.log","a")
            except OSError as e:
                print("[E] Error creating log file: " + e)
                sys.exit(1)
            if config.log_started != True:
                log_file.write("## autopwn v0.16.0 command output\n")
                log_file.write("## Started logging at " + date_time + "...\n")
                config.log_started = True

            log_file.write("# " + date_time + "\n")
            log_file.write(log_string + "\n")
            log_file.close()

        if log_type == 'individual_target':
            try:
                log_file = open(directory + "/target","w")
            except OSError as e:
                print("[E] Error creating log file: " + e)
                sys.exit(1)
            log_file.write(log_string + "\n")
            log_file.close()

class Run:
    thread = []
    index = False

    def __init__(self, tool_subset, assessment_type, config):
        if config.dry_run == True:
            print("--------------------------------")
            print("The following tools will be run:")
            print("--------------------------------")
        for tool in tool_subset:
            # Run for real
            if config.dry_run != True:
                if 'url' in tool:
                    log = Log(config,os.getcwd(),False,'tool_string',"# Executing " + \
                              tool['name'] + " tool (" + tool['url'] + "):\n" + \
                              tool['execute_string'])
                else:
                    log = Log(config,os.getcwd(),False,'tool_string',"# Executing " + \
                              tool['name'] + " tool:\n# " + \
                              tool['execute_string'])

                time.sleep (0.1);
                self.thread.append(RunThreads(config, tool))
                # If main process dies, everything else *SHOULD* as well
                self.thread[self.index].daemon = True
                # Start threads
                self.thread[self.index].start()

                # Parallel or singular?
                if assessment_type['parallel'] != True:
                    while threading.activeCount()>1:
                        pass

                self.index = self.index + 1
            else:
                print(tool['execute_string'])
                pass

        if config.dry_run != True:
            if assessment_type['parallel'] == True:
                while threading.activeCount()>1:
                    pass
                #for tid in self.thread:
                #    tid.join(1)

class RunThreads (threading.Thread):
    def __init__(self, config, tool):
        threading.Thread.__init__(self)
        self.kill_received = False
        self.tool_name = tool['name']
        self.tool_execute_string = tool['execute_string']
        self.tool_output_dir = tool['output_dir']
        self.tool_stdout_boolean = tool['stdout']
        self.target_name = tool['target']['name']
        self.tool_stdout = ''
        self.tool_stderr = ''
        self.config = config

    def execute_tool(self, tool_name,
                            tool_execute_string):
        # Always check any tools provided by
        # community members
        # Bad bug using this and no shell for Popen,
        # will come back to this
        #command_arguments = shlex.split(tool_execute_string)
        proc = Popen(tool_execute_string, stdout=PIPE, stderr=PIPE, shell=True)

        decode_locale = lambda s: s.decode(getlocale()[1])
        self.tool_stdout, self.tool_stderr = map(decode_locale, proc.communicate())

        exitcode = proc.returncode

    def run(self):
        print("[+] Launching " + self.tool_name)
        self.execute_tool(self.tool_name,
                          self.tool_execute_string)
        print("[-] " + self.tool_name + " is done..")
        # Should we create a stdout log for this tool?
        if self.tool_stdout_boolean == True:
            log = Log(self.config, os.getcwd() + "/" + self.tool_output_dir,
                      self.target_name + "_" + self.tool_name,
                      'tool_output', self.tool_stdout)
        log = Log(self.config, os.getcwd(), False, 'tool_string', "# " + \
                  self.tool_name + " has finished")

class Tools:
    def __init__(self, config, args, assessment):
        config.tool_subset = []
        for tool in config.tools_config:
            if tool['name'] in assessment['tools']:
                config.tool_subset.append(tool)

        print("autopwn v0.16.0 by Aidan Marlin")
        print("email: aidan [dot] marlin [at] nccgroup [dot] com")
        print()

        self.replace_placeholders(config, assessment)
        for tool in config.tool_subset:
            self.check_tool_exists(tool['binary_location'], args)

        if args.with_screen == True:
            self.prepend_tool(config, 'screen', args)

    def prepend_tool(self, config, prepend_tool, args):
        if prepend_tool == 'screen':
            bash_binary = self.check_tool_exists('bash', args)
            screen_binary = self.check_tool_exists('screen', args)
            index = False
            for target in config.target_list:
                for tool in config.tool_subset:
                    config.tool_subset_evaluated[index]['execute_string'] = \
                        screen_binary + " -D -m -S autopwn_" + \
                        target['name'] + "_" + \
                        target['domain_name'] + "_" + target['ip'] + \
                        "_" + tool['name'] + " " + bash_binary + " -c '" + \
                        config.tool_subset_evaluated[index]['execute_string'] + \
                        "'"

                    index = index + 1

    def check_tool_exists(self, tool, args):
        error_type = '[E]'

        if os.path.isfile(tool) == False:
            tool_location = find_executable(tool)
            if tool_location == None:
                if args.ignore_missing_binary == True:
                    error_type = '[W]'

                print(error_type + " Could not find binary for " + tool)

                if args.ignore_missing_binary == False:
                    sys.exit(1)
            else:
                return tool_location

    def replace_placeholders(self, config, assessment):
        config.tool_subset_evaluated = []

        for target in config.target_list:
            for tool in config.tool_subset:
                config.tool_subset_evaluated.append(copy.deepcopy(tool))
                target_string = ''

                if target['ip'] != None:
                    target_string = target['ip']
                elif target['ip_address_list'] != None:
                    target_string = target['ip_address_list']
                else:
                    print("[E] You shouldn't see this error")
                    sys.exit(1)

                # Variable declaration for placeholder replacements
                date = strftime("%Y%m%d_%H%M%S%z")
                date_day = strftime("%Y%m%d")
                config.tool_subset_evaluated[-1]['output_dir'] = date_day + \
                                                                 "_autopwn_" + \
                                                                 target_string + \
                                                                 "_" + target['name']
                config.tool_subset_evaluated[-1]['target'] = target
                output_dir = config.tool_subset_evaluated[-1]['output_dir']

                # Create log directory in CWD
                if not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                    except OSError as e:
                        print("[E] Error creating output directory: " + e)
                        sys.exit(1)

                # Create target file in new directory
                Log(config,output_dir,False,
                    'individual_target',target_string)

                option_format_string = {}
                # Option string processing
                argument_prepend_option = False
                argument_separator = ''
                argument_encapsulation = ''
                if 'option-formats' in tool:
                    for option_format_instance in tool['option-formats']:
                        individual_option_set = tool['option-formats'][option_format_instance]

                        option = individual_option_set['option']
                        option_separator = individual_option_set['option-separator']
                        substitution_format = individual_option_set['substitution']

                        if 'argument-prepend-option' in tool['option-formats'][option_format_instance]:
                            argument_prepend_option = tool['option-formats'][option_format_instance]['argument-prepend-option']
                        else:
                            argument_prepend_option = False
                        if 'argument-separator' in tool['option-formats'][option_format_instance]:
                            argument_separator = tool['option-formats'][option_format_instance]['argument-separator']
                        else:
                            argument_separator = ''
                        if 'argument-encapsulation' in tool['option-formats'][option_format_instance]:
                            argument_encapsulation = tool['option-formats'][option_format_instance]['argument-encapsulation']
                        else:
                            argument_encapsulation = ''

                        option_placeholder = individual_option_set['option-placeholder']
                        if target[option_placeholder] == None:
                            continue

                        option_format_string[option_placeholder] = [ option + option_separator + argument_encapsulation ]
                        option_format_string_index = 1

                        # Argument stuff
                        if isinstance(target[option_placeholder], str):
                            option_format_string[option_placeholder][0] = \
                                                                          option_format_string[option_placeholder][0] + \
                                                                          ''.join(substitution_format.format(
                                                                          target[option_placeholder]))
                        else:
                            for item in target[option_placeholder]:
                                if option_format_string_index == 1:
                                    option_format_string[option_placeholder][0] = \
                                                                                  option_format_string[option_placeholder][0] + \
                                                                                  ''.join(substitution_format.format(
                                                                                  item,target[option_placeholder][item]))
                                    option_format_string_index = option_format_string_index + 1
                                else:
                                    option_format_string[option_placeholder].append(''.join(substitution_format.format(
                                                                                    item,target[option_placeholder][item])))

                # Some of the target variables might be None,
                # so these will need blanking
                domain_name_string = target['domain_name']
                ip_string = target['ip']
                port_number_string = target['port_number']
                protocol_string = target['protocol']
                url_string = target['url']
                name_string = target['name']

                if domain_name_string == None:
                    domain_name_string = ''
                if port_number_string == None:
                    port_number_string = ''
                if protocol_string == None:
                    protocol_string = ''
                if url_string == None:
                    url_string = ''
                if name_string == None:
                    name_string = ''

                if 'ip_address_list' not in option_format_string:
                    option_format_ip_address_list = ''
                else:
                    option_format_ip_address_list = option_format_string['ip_address_list'][0]
   
                # Cookies string stuff 
                option_format_cookies = ''
                if 'cookies' not in option_format_string:
                    if 'cookies_file' not in option_format_string:
                        option_format_cookies = ''
                    else:
                        option_format_cookies = option_format_string['cookies_file'][0]
                else:
                    first_option = True
                    for individual_option in option_format_string['cookies']:
                        # TODO Review space
                        if argument_prepend_option == True:
                            if first_option == True:
                                option_format_cookies = option_format_cookies + ' ' + individual_option
                                first_option = False
                            else:
                                option_format_cookies = option_format_cookies + ' ' + option + option_separator + individual_option
                        else:
                            option_format_cookies = option_format_cookies + individual_option + argument_separator
                option_format_cookies = option_format_cookies + argument_encapsulation


                # Replace placeholders for tool argument string
                tool_arguments_instance = config.tool_subset_evaluated[-1]['arguments'].format(
                                          domain_name=domain_name_string,
                                          ip=ip_string, date=date,
                                          port_number=port_number_string,
                                          protocol=protocol_string,
                                          url=url_string,
                                          name=name_string,
                                          ip_address_list=option_format_ip_address_list,
                                          cookie_arguments=option_format_cookies,
                                          output_dir=output_dir)

                config.tool_subset_evaluated[-1]['execute_string'] = config.tool_subset_evaluated[-1]['binary_location'] + " " + \
                                                                     tool_arguments_instance

                # Replace placeholders for pre tool command string
                if 'pre_tool_execution' in config.tool_subset_evaluated[-1]:
                    config.tool_subset_evaluated[-1]['pre_tool_execution'] = config.tool_subset_evaluated[-1]['pre_tool_execution'].format(
                                                                             domain_name=domain_name_string,
                                                                             ip=ip_string, date=date,
                                                                             port_number=port_number_string,
                                                                             protocol=protocol_string,
                                                                             url=url_string,
                                                                             name=name_string,
                                                                             output_dir=output_dir)

                # Replace placeholders for post tool command string
                if 'post_tool_execution' in config.tool_subset_evaluated[-1]:
                    config.tool_subset_evaluated[-1]['post_tool_execution'] = config.tool_subset_evaluated[-1]['post_tool_execution'].format(
                                                                              domain_name=domain_name_string,
                                                                              ip=ip_string, date=date,
                                                                              port_number=port_number_string,
                                                                              protocol=protocol_string,
                                                                              url=url_string,
                                                                              name=name_string,
                                                                              output_dir=output_dir)

class Menus:
    # Not 0 because this is a valid selection..
    item_selected = ''

    def __init__(self, menu_items, menu_name):
        if menu_name == 'assessment':
            self.display_assessment_menu(menu_items)

    def display_assessment_menu(self, menu_items):
        question = inquirer.List('item',
                                 message='What assessment do you want to run?',
                                 choices=menu_items)
        choice = inquirer.prompt([question])
        if choice is not None:
            self.item_selected = menu_items.index(choice['item'])
        else:
            sys.exit(1)

class Assessments:
    assessment_type = ""

    def __init__(self, config, argument_assessment):
        # Shall we process assessment from command line
        # arguments or display menu?
        if argument_assessment != None:
            # Set variable
            argument_assessment_found = False
            # Command line
            for assessment_type in config.assessments_config:
                if assessment_type['name'] == argument_assessment:
                    self.assessment_type = assessment_type
                    argument_assessment_found = True
            if argument_assessment_found == False:
                print("[E] Assessment name not found. Is it spelt correctly?")
                sys.exit(1)
        else:
            # Display menu
            config.dry_run = True
            menu = Menus(config.menu_items,'assessment')
            self.assessment_type = config.assessments_config[menu.item_selected]



# Configuration class loads all information from .apc files and target file
class Configuration:
    # Class vars
    autopwn_config = {'parallel':False,
                      'parallel_override':False,
                      'scripts_directory':''}
    log_started = False
    tools_config = []
    assessments_config = []
    menu_items = []
    target_list = []
    dry_run = False

    # This method will pull configuration and target file information
    # Will probably split into separate methods at some point
    def __init__(self, args):
        index = 0
        target_file = args.target

        def find_path(candidate):
             basepath = os.path.dirname(candidate)
             tools_dir = os.path.join(basepath, 'tools')
             if os.path.exists(tools_dir):
                 return basepath

        pathname = os.path.abspath(find_path(__file__) or find_path(sys.argv[0]))
        tools_directory = os.path.abspath(pathname) + "/tools/"

        # Command line parallel option 
        self.autopwn_config['parallel_command_line_option'] = args.parallel

        if args.assessment_directory == None:
            assessments_directory = os.path.abspath(pathname) + \
                                            "/assessments/"
        else:
            assessments_directory = args.assessment_directory

        # Pull global config
        autopwn_global_config_file = pathname + '/autopwn.apc'
        stream = open(autopwn_global_config_file, 'r')
        objects = yaml.load(stream)

        # Parallel APC config override option
        self.autopwn_config['parallel_global_override_option'] = False
        try:
            self.autopwn_config['parallel_global_option'] = objects['parallel']
            self.autopwn_config['parallel_global_override_option'] = True
        except:
            pass

        # Scripts directory
        try:
            self.autopwn_config['scripts_directory'] = objects['scripts_directory']
        except:
            print("[E] Missing option in autopwn configuration file: scripts_directory is mandatory")
            sys.exit(1)

        # Pull tool configs
        for file in os.listdir(tools_directory):
            if file.endswith(".apc"):
                stream = open(tools_directory + file, 'r')
                objects = yaml.load(stream)

                self.tools_config.append(objects)
                index = index + 1

        # Pull assessment configs
        index = 0
        # Check assessments directory exists
        if not os.path.isdir(assessments_directory):
            print("[E] Assessments directory does not exist")
            sys.exit(1)

        for file in os.listdir(assessments_directory):
            if file.endswith(".apc"):
                stream = open(assessments_directory + file, 'r')
                objects = yaml.load(stream)

                self.assessments_config.append(objects)

                if self.autopwn_config['parallel_command_line_option'] == False:
                    if self.autopwn_config['parallel_global_override_option'] == False:
                        self.assessments_config[index]['parallel'] = objects['parallel']
                    else: 
                        self.assessments_config[index]['parallel'] = self.autopwn_config['parallel_global_option']
                else:
                    self.assessments_config[index]['parallel'] = True
                    
                index = index + 1

        # Assign menu_items
        for config_assessment_menu_item in self.assessments_config:
            self.menu_items.append(config_assessment_menu_item['menu_name'])

        ###
        # Get targets
        ###
        try:
            fd_targets = open(target_file, 'r')
            yaml_content = yaml.load(fd_targets)
            fd_targets.close()
        except IOError as e:
            print("[E] Error processing target file: {1}".format(e.errno,
                                                                 e.strerror))
            sys.exit(1)

        # Process each target in target list
        target_name_matrix = []

        for target in yaml_content['targets']:
            # If attributes haven't been specified, set to False
            try:
                # Does this exist? It bloody well should
                target['name']
            except:
                print("[E] Target name missing: Target name must be specified")
                sys.exit(1)
            if target['name'] in target_name_matrix:
                print("[E] Duplicate target names identified")
                sys.exit(1)
            else:
                target_name_matrix.extend([target['name']])
                target_name = target['name']
            try:
                target_ip = target['ip_address']
                target_ip_address_list = None
            except:
                try:
                    target_ip_address_list = target['ip_address_list']
                    target_ip = None
                except:
                    print("[E] Target file missing IP address target or file")
                    sys.exit(1)
            try:
                target_domain_name = target['domain']
            except:
                target_domain_name = target_ip
            try:
                target_port_number = target['port']
            except:
                target_port_number = None
            try:
                target_protocol = target['protocol']
            except:
                target_protocol = None
            try:
                target_cookies = target['cookies']
            except:
                target_cookies = None
            try:
                target_cookies_file = target['cookies_file']
            except:
                target_cookies_file = None
            try:
                target_url = target['url']
                # Forward slash (/) SHOULD already be in tool argument string
                if target_url.startswith('/'):
                    target_url = target_url[1:]
            except:
                target_url = ''

            self.target_list.append({'ip':target_ip,
                                     'ip_address_list':target_ip_address_list,
                                     'domain_name':target_domain_name,
                                     'port_number':target_port_number,
                                     'url':target_url,
                                     'name':target_name,
                                     'protocol':target_protocol,
                                     'cookies':target_cookies,
                                     'cookies_file':target_cookies_file})

class Prompt:
    def __init__(self, prompt, config, args, tools, assessment):
        if prompt == 'run_tools':
            self.show_post_commands(config,assessment)
            self.run_tools(config,args,tools,assessment)

    def show_post_commands(self, config, assessment):
        # Run post-tool execution commands
        # config.dry_run is assumed, but let's bail if
        # it's not set as expected
        if config.dry_run == True:
            Commands(config,assessment.assessment_type,'post')
        else:
            print("[E] Dry run variable not set as expected. " + \
                    "You shouldn't see this error")
            sys.exit(1)

    def run_tools(self, config, args, tools, assessment):
        if config.autopwn_config['parallel_command_line_option'] == True:
            print("[I] Parallel option set on command line")
        if config.autopwn_config['parallel_global_override_option'] == True:
            print("[I] Parallel option set in global options file")
        run_tools = input('Run tools? [Ny] ')

        if run_tools.lower() == "y":
            config.dry_run = False
            # Run pre-tool execution commands
            Commands(config,assessment.assessment_type,'pre')
            Run(config.tool_subset_evaluated,assessment.assessment_type,config)
            # Run post-tool execution commands
            Commands(config,assessment.assessment_type,'post')
        else:
            print("[E] Alright, I quit..")
            sys.exit(1)

class Rules:
    def __init__(self, args, config, tools):
        self.check(args, config, tools)

    def check(self, args, config, tools):
        # Hosts
        rule_violation = False
        for target_index, target in enumerate(config.target_list):
            # Tools
            for tool_config_index, tool_config in enumerate(config.tools_config):
                check_tool_rule = False
                for tool in config.tool_subset:
                    if tool_config['name'] == tool['name']:
                        check_tool_rule = True

                if check_tool_rule != True:
                    continue

                # Check
                try:
                    for rule_type in tool_config['rules']:
                        if rule_type == 'target-parameter-exists':
                            for argument in tool_config['rules'][rule_type]:
                                rule_violation_tmp = self.check_comparison(target,tool_config,
                                                                           rule_type,argument,
                                                                           None)
                                rule_violation = rule_violation or rule_violation_tmp
                        else:
                            for argument in tool_config['rules'][rule_type]:
                                rule_violation_tmp = self.check_comparison(target,tool_config,
                                                                           rule_type,argument,
                                                                           tool_config['rules'][rule_type][argument])
                                rule_violation = rule_violation or rule_violation_tmp
                except:
                    #raise
                    pass

        if rule_violation:
            error_type = '[E]'

            if args.ignore_rules == True:
                error_type = '[W]'

            print(error_type + " There were rule violations")

            if args.ignore_rules == False:
                sys.exit(1)

    def check_comparison(self,target,tool_config,rule_type,argument,argument_value):
        error = False
        if rule_type == 'target-parameter-exists':
            # If list then make sure at least one of the items exists.
            # This is essentially 'or' functionality
            if type(argument) is list:
                parameter_found = False
                for parameter in argument:
                    if target[parameter] != None:
                        parameter_found = True
                        break
                # Was the parameter found?
                if parameter_found != True:
                    print("[W] Rule violation in " + tool_config['name'] + \
                          " for target " + target['name'] + \
                          ": One of the arguments was not specified")
                    error = True
            else:
                if target[argument] == None:
                    print("[W] Rule violation in " + tool_config['name'] + \
                          " for target " + target['name'] + \
                          ": '" + argument + "' not specified in target")
                    error = True
        else:
            ops = {"not-equals": operator.eq,
                   "equals": operator.ne,
                   "greater-than": operator.lt,
                   "less-than": operator.gt}

            violation = {"not-equals": \
                                       "[W] Rule violation in " + \
                                       tool_config['name'] + \
                                       " for target " + target['name'] + \
                                       ": '" + argument + "' must be '" + \
                                       str(argument_value) + "'",
                         "equals": \
                                   "[W] Rule violation in " + \
                                   tool_config['name'] + \
                                   " for target " + target['name'] + \
                                   ": '" + argument + "' must be '" + \
                                   str(argument_value) + "'",
                         "greater-than": \
                                         "[W] Rule violation in " + \
                                         tool_config['name'] + \
                                         " for target " + target['name'] + \
                                         ": '" + argument + "' must be '" + \
                                         str(argument_value) + "'",
                        "less-than": \
                                     "[W] Rule violation in " + \
                                     tool_config['name'] + \
                                     " for target " + target['name'] + \
                                     ": '" + argument + "' must be '" + \
                                     str(argument_value) + "'"}

            try:
                check_type = ops[rule_type]
                violation_type = violation[rule_type]
                if check_type(target[argument], argument_value):
                    print(violation_type)
                    error = True
            except:
                #raise
                pass
        return error

class Commands:
    def __init__(self, config, assessment_type, position):
        if position == 'pre':
            self.pre_command(config,assessment_type)
        elif position == 'post':
            self.post_command(config,assessment_type)

    def pre_command(self, config, assessment_type):
        if config.dry_run == True:
            display_pre_command_banner = True

            for tool in config.tool_subset_evaluated:
                if 'pre_tool_execution' in tool and \
                        display_pre_command_banner == True:
                    print("The following pre-tool execution commands will be run:")
                    print("--------------------------------")
                    display_pre_command_banner = False

        for tool in config.tool_subset_evaluated:
            try:
                if config.dry_run == True:
                    print(tool['pre_tool_execution'])
                else:
                    if 'pre_tool_execution' in tool:
                        print("[+] Running pre-tool commands for " + tool['name'])
                        subprocess.call(tool['pre_tool_execution'],shell = True)
                        print("[-] Pre-tool commands for " + tool['name'] + " have completed..")
                        log = Log(config,os.getcwd(),False,'tool_string',
                                  "# Pre-tool commands for " + tool['name'] + \
                                  " have finished")

            except:
                pass

    def post_command(self, config, assessment_type):
        display_post_command_banner = True
        if config.dry_run == True:
            for tool in config.tool_subset_evaluated:
                if 'post_tool_execution' in tool and \
                        display_post_command_banner == True:
                    print("--------------------------------")
                    print("The following post-tool execution commands will be run:")
                    print("--------------------------------")
                    display_post_command_banner = False
        for tool in config.tool_subset_evaluated:
            try:
                if config.dry_run == True:
                    print(tool['post_tool_execution'])
                else:
                    if 'post_tool_execution' in tool:
                        print("[+] Running post-tool commands for " + tool['name'])
                        subprocess.call(tool['post_tool_execution'],shell = True)
                        print("[-] Post-tool commands for " + tool['name'] + \
                              " have completed..")
                        log = Log(config,os.getcwd(),False,'tool_string',
                                  "# Post-tool commands for " + tool['name'] + \
                                  " have finished")

            except:
                pass

class CleanUp:
    def __init__(self):
        # Kill screen sessions. Needs improvement
        for screen in list_screens():
            if screen.name.startswith("autopwn"):
                screen.kill()

class Sanitise:
    def __init__(self, config):
        for tool in config.tool_subset_evaluated:
            tool['execute_string'] = ' '.join(tool['execute_string'].split())

class Arguments:
    argparse_description = '''
autopwn v0.16.0
By Aidan Marlin
Email: aidan [dot] marlin [at] nccgroup [dot] com'''

    argparse_epilog = '''
Format of the target file should be:

targets:
    - name: <target-name>
      ip_address: <ip-address>
      domain: <domain>
      url: <url-path>
      port: <port-number>
      protocol: <protocol>
      mac_address: <mac_address>
    - name: <target-name-1>
      ip_address_list: <ip-address-list>
      ...

Only 'name' and 'ip_address' are compulsory options.
Example file:

targets:
    - name: test
      ip_address: 127.0.0.1
      domain: test.com
      url: /test
      port: 80
      protocol: https
      mac_address: ff:ff:ff:ff:ff:ff
      cookies:
        some-cookie-name: some-cookie-value
        some-cookie-name1: some-cookie-value1
    - name: test-1
      ip_address_list: ip_list.txt
      cookies_file: cookies.txt

autopwn uses the tools/ directory located where this
script is to load tool definitions, which are yaml
files. You can find some examples in the directory
already. If you think one is missing, mention it on
GitHub or email me and I might add it.

autopwn also uses assessments/ for assessment definitions.
Instead of selecting which tools you would like to run,
you specify which assessment you would like to run.
Assessment configuration files contain lists of tools
which will be run as a result.

Have fun!
Legal purposes only..
'''

    def __init__(self, argslist):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=self.argparse_description,
                                         epilog=self.argparse_epilog)
        self.parser.add_argument('-t', '--target',
                                 required=True,
                                 help='The file containing the targets')
        self.parser.add_argument('-a', '--assessment',
                                 help='Specify assessment name to run. Autopwn will not '
                                'prompt to run tools with this option')
        self.parser.add_argument('-d', '--assessment_directory',
                                 help='Specify assessment directory')
        self.parser.add_argument('-i', '--ignore_missing_binary',
                                 action='store_true',
                                 help='Deprecated (and buggy)\nIgnore missing binary conditions')
        self.parser.add_argument('-r', '--ignore_rules',
                                 action='store_true',
                                 help='Deprecated (and buggy)\nIgnore tool rulesets')
        self.parser.add_argument('-s', '--with_screen',
                                 action='store_true',
                                 help='Run tools in screen session')
        self.parser.add_argument('-p', '--parallel',
                                 action='store_true',
                                 help='Run tools in parallel regardless of assessment or '
                                 'global parallel option')

        self.parser = self.parser.parse_args(argslist)

def _main(argslist):
    # Process arguments
    args = Arguments(argslist).parser
    # Pull config
    config = Configuration(args)
    # Determine assessment
    assessment = Assessments(config,args.assessment)
    # Process tools
    tools = Tools(config,args,assessment.assessment_type)
    # Check rules
    Rules(args,config,tools)
    # Run pre-tool execution commands
    Commands(config,assessment.assessment_type,'pre')
    # Sanitise command line strings (remove extra whitespace)
    Sanitise(config)
    # Run tools
    execute = Run(config.tool_subset_evaluated,assessment.assessment_type,config)
    if config.dry_run == True:
        Prompt('run_tools',config,args,tools,assessment)
    # Run post-tool execution commands
    Commands(config,assessment.assessment_type,'post')

def main():
    try:
        _main(sys.argv[1:])
    except KeyboardInterrupt:
        CleanUp()
        print()
        print("[E] Quitting!")
        sys.exit(1)

if __name__ == "__main__":
    main()
