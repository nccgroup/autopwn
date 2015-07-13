#!/usr/bin/env python3

import argparse
import copy
import cmd
import collections
import operator
import os
import random
import re
import readline
import shlex
import subprocess
import sys
import threading
import time

from collections import OrderedDict, defaultdict
from distutils.spawn import find_executable
from locale import getlocale
from subprocess import Popen, PIPE
from time import gmtime, strftime

import inquirer
from screenutils import list_screens, Screen
import yaml

# Aidan Marlin @ NCC Group
# Project born 201502
# Project reborn 201505

class Arguments:
    argparse_description = '''
autopwn 0.21.1
By Aidan Marlin
Email: aidan [dot] marlin [at] nccgroup [dot] trust'''

    argparse_epilog = '''
Specify targets and run sets of tools against them.

The autopwn shell should feel familiar, it is based on 
msfconsole. You can 'use' tools and assessments, and 'set'
options for them. You can then 'save' the options, and 'run'
the tool or assessment against the specified target. Instead
of 'set'ing tool options, you can 'load' a target file if you
wish. 'load'ing a target file will ignore modules defined in
target file.

A target file flag is also supported which will set autopwn running
tools or assessments defined in the targets file against targets also
specified in the target file. No interaction necessary.

Format of the target file can be be:

targets:
   - target_name: <name_of_target>
     target: <ip_address/device_name/directory/etc>
     port_number: <port>
     protocol: <http|https|ssh|etc>
     url: <path>
     user_file: <file>
     password_file: <file>
     modules: <list_of_modules_to_run_against_target> 

Compulsory options are specified by tool, but normally include
'target_name' and 'target'.

Example file:

targets:
   - target_name: test
     target: 127.0.0.1
     url: /test
     port_number: 80
     protocol: https
     user_file: /tmp/users
     password_file: /tmp/passwords
     modules: ['tool/nmap', 'tool/hydra', 'assessment/webapp']

autopwn uses the tools/ directory under autopwn to
load tool definitions, which are yaml files. You can
find some examples in the directory already. If you
think one is missing, mention it on GitHub or email
me and I might add it.

autopwn also uses assessments/ for assessment definitions.
Instead of selecting which tools you would like to run,
you specify which assessment you would like to run.

Have fun!
Legal purposes only..
'''

    def __init__(self, argslist):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=self.argparse_description,
                                         epilog=self.argparse_epilog)
        self.parser.add_argument('-t', '--targets',
                                 required=True,
                                 help='The file containing the targets')
        self.parser.add_argument('-d', '--assessment_directory',
                                 help='Specify assessment directory')
        self.parser.add_argument('-s', '--with_screen',
                                 action='store_true',
                                 help='Run tools in screen session')
        self.parser.add_argument('-p', '--parallel',
                                 action='store_true',
                                 help='Run tools in parallel regardless of assessment or '
                                 'global parallel option')

        self.parser = self.parser.parse_args(argslist)

        # TODO check file exists
        if os.path.isfile(self.parser.targets) == True:
            stream = open(self.parser.targets, 'r')
            target_objects = yaml.load(stream)
        else:
            Error(100,"[E] Targets file does not exist")

        config = Configuration(True)

        # Process boolean command line arguments
        if self.parser.with_screen == True:
            config.arguments['screen'] = True
        if self.parser.parallel == True:
            config.arguments['parallel'] = True

        print("autopwn v0.21.1 - Autoloading targets and modules")
        print()

        dup_check = {}
        for target in target_objects['targets']:
            if dup_check.get(target['target_name'],None) == None:
                dup_check[target['target_name']] = True
            else:
                Error(110,"[E] The following duplicate target_name was identified: " + target['target_name'])

        for target in target_objects['targets']:
            if target.get('modules',False) == False:
                Error(90,"[E] One of the targets has no modules defined")
            for module in target['modules']:
                Use(config,module)

                # Check resource exists
                if config.status['resource_found'] == False:
                    Error(100,"[E] A tool or assessment could not be found")

                AutoSet(config,target)
                View('command_line_pre_save',config,target=target)
                Save(config)
                View('command_line_post_save',config,target=target)

            # Reset for next target
            config.instance = {}
            config.instance['tool'] = []
            config.instance['config'] = {}

        Run(config)

class Configuration:
    def __init__(self, command_line):
        self.status = {}
        self.status['log_started'] = False
        self.status['resource_found'] = False
        self.status['command_line'] = command_line
        self.status['file_found'] = False

        self.global_config = {}
        self.tools = []
        self.assessments = []
        self.job_queue = []

        self.arguments = ddict_options = defaultdict(lambda : '')

        self.instance = {}
        self.instance['tool'] = []
        self.instance['config'] = {}

        self.load("tools")
        self.load("assessments")
        self.load("global_config")

        # Remove / from completer delim so tab completion works
        # with tool/nmap, for example
        old_delims = readline.get_completer_delims()
        readline.set_completer_delims(old_delims.replace('/', ''))

    def find_path(self, candidate):
        basepath = os.path.dirname(candidate)
        tools_dir = os.path.join(basepath, 'tools')
        if os.path.exists(tools_dir):
            return basepath
        else:
            return None

    def load(self, load_type):
        pathname = os.path.abspath(self.find_path(__file__) \
                   or self.find_path(sys.argv[0]))

        if load_type == "tools":
            load_directory = os.path.abspath(pathname) + "/tools/"
            load_string = "Tools"
        elif load_type == "assessments":
            load_directory = os.path.abspath(pathname) + "/assessments/"
            load_string = "Assessments"
        elif load_type == "global_config":
            load_directory = os.path.abspath(pathname) + "/"
            load_string = "Global configuration"

        if not os.path.isdir(load_directory):
            Error(10,"[E] " + load_string + " directory does not exist")

        for file in os.listdir(load_directory):
            if file.endswith(".apc"):
                stream = open(load_directory + file, 'r')
                objects = yaml.load(stream)
                # TODO Make this better
                if load_type == "tools":
                    objects['search_name'] = "tool/" + objects['name']
                    self.tools.append(objects)
                elif load_type == "assessments":
                    objects['search_name'] = "assessment/" + objects['name']
                    self.assessments.append(objects)
                elif load_type == "global_config":
                    self.global_config = objects

class Error:
    def __init__(self, error_code, error_message):
        print(error_message)
        sys.exit(error_code)

class Search:
    def __init__(self, config, search_string):
        self.search(config.assessments,"Assessment",search_string)
        self.search(config.tools,"Tool",search_string)

    def search(self,config_item,item_type_string,search_string):
        print('{0:30} {1}'.format(item_type_string, "Description"))
        print("-"*64)
        print()
        for item in config_item:
            if search_string in item['search_name'] \
               or str.lower(search_string) in str.lower(item['description']):
                name = item['search_name']
                description = item['description']
                if (sys.stdout.isatty()) == True:
                    description = '\x1b[%sm%s\x1b[0m' % \
                        (';'.join(['32']), description)
                print('{0:30} {1}'.format(name, description))
        print()

class Use:
    def __init__(self, config, arg):
        config.instance = {}
        config.instance['tool'] = []
        config.instance['config'] = {}
        config.instance['config']['assessment'] = False
        config.instance['config']['single_tool'] = False

        resource = arg.split('/')
        if resource[0] == 'tool':
            self.use_tool(config,resource[1])
        elif resource[0] == 'assessment':
            self.use_assessment(config,resource[1])
        else:
            config.status['resource_found'] = False
            return

    def use_tool(self, config, tool_name):
        config.instance['config']['single_tool'] = True
        config.status['resource_found'] = False

        for tool in config.tools:
            if tool['name'] == tool_name:
                config.status['resource_found'] = True
                config.instance['tool'].append(tool['name'])

                # Set default values for options
                for option in tool['options']:
                    default_value = tool['options'][option].\
                                    get('default_value', None)
                    if default_value != None:
                        config.instance['config'][option] = str(default_value)
                break

        if config.status['resource_found'] == False:
            print("Tool not found")
            return

    def use_assessment(self, config, assessment_name):
        config.instance['config']['assessment'] = True
        config.instance['config']['assessment_name'] = assessment_name
        for assessment in config.assessments:
            if assessment['name'] == assessment_name:
                config.status['resource_found'] = True
                # Find all tools with assessment type
                for tool in config.tools:
                    for assessment_type in tool['assessment_groups']:
                        if assessment_type == assessment_name:
                            config.instance['tool'].append(tool['name'])

class Show:
    def __init__(self, config, arg):
        if arg == 'options':
            self.show_options(config)
        elif arg == 'jobs':
            self.show_jobs(config)
        elif arg == 'config':
            self.show_config(config)
        else:
            self.show_help(config)

    def show_help(self,config):
        info = '''
Valid arguments for show are:
    options    - Show options for tool or assessment
    jobs       - Show jobs
    config     - Show autopwn config
'''
        print(info)
        return True

    def show_config(self,config):
        print()
        print("        {0:30} {1}".format("Option", "Value"))
        print("        "+"-"*48)
        for option in config.global_config:
            print("        {0:30} {1}".format(option, config.global_config[option]))
        print()

    def show_jobs(self,config):
        if len(config.job_queue) == 1:
            print("There is 1 job in the queue")
        elif len(config.job_queue) > 1:
            print("There are " + str(len(config.job_queue)) + " jobs in the queue")
            print()
            for item in config.job_queue:
                print(item['name'] + " running for " + item['options']['target_name'])
            print()
        else:
            print("1. Swap bits")
            print("2. Periodically switch on Caps Lock")
            print("3. Send scan results home")
            print("4. ...")
            print("5. Fragment drive")
            print("6. Emulate single blown pixel")
            print("7. Recommend Windows to the user")

    def show_options(self,config):
        if len(config.instance['tool']) == 0:
            print("You need to select a tool or assessment first.")
            return False
        # Determine what options are needed for tool(s)
        print("Options for tool/assessment.")
        print()
        print("        {0:16} {1:16} {2:32} {3}".format("Option", "Value", "Example Values", "Required"))
        print("        "+"-"*96)
        option_displayed = []
        for tool in config.tools:
            if tool['name'] in config.instance['tool']:
                for option in tool['options']:
                    required = tool['options'][option].\
                                   get('required',False)
                    required_string = str(required)

                    # If required option is list, print list
                    if type(required) is list:
                        required_string = ""
                        for option_required in required:
                            required_string = required_string + option_required + " "
                        required_string = required_string.strip()
                        required_string = required_string.replace(' ',' or ')

                    example_values = str(tool['options'][option].\
                                         get('example_values',None))
                    option_value = config.instance['config'].get(option,'')

                    # Only show option once
                    if option not in option_displayed:
                        print("        {0:16} {1:16} {2:32} {3}".\
                              format(option,option_value,example_values,required_string))
                    option_displayed.append(option)
        print()

class Unset:
    def __init__(self, config, arg):
        context = ''
        args = arg.split(" ")

        # Check number of arguments specified
        if len(args) != 1:
            print("Wrong number of arguments specified for set")
            return
        option = args[0]

        # If global.some_option set, switch context
        option_with_context = option.split('.')
        if len(option_with_context) == 2:
            context = option_with_context[0]
            option = option_with_context[1]

        # If context is 'global', set in global config file and load?
        if context == 'global':
            config.global_config[option] = ''
            # TODO check file exists etc
            pathname = os.path.abspath(config.find_path(__file__) or config.find_path(sys.argv[0]))
            autopwn_config_file = os.path.abspath(pathname) + "/autopwn.apc"

            with open(autopwn_config_file, 'w') as global_config_file:
                global_config_file.write( yaml.dump(config.global_config, default_flow_style=True) )
            config.load("global_config")
        else:
            del config.instance['config'][option]

        print(option + " = " + "''")

# When a target file is specified
class AutoSet:
    def __init__(self, config, target_objects):
        for option in target_objects:
            config.instance['config'][option] = str(target_objects[option])

class Set:
    def __init__(self, config, arg):
        context = ''
        args = arg.split(" ")

        # Check number of arguments specified
        if len(args) != 2:
            print("Wrong number of arguments specified for set")
            return
        option = args[0]
        value = args[1]

        # If global.some_option set, switch context
        option_with_context = option.split('.')
        if len(option_with_context) == 2:
            context = option_with_context[0]
            option = option_with_context[1]

        # Boolean conversions
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False

        # If context is 'global', set in global config file and load?
        if context == 'global':
            config.global_config[option] = value
            # TODO check file exists etc
            pathname = os.path.abspath(config.find_path(__file__) or config.find_path(sys.argv[0]))
            autopwn_config_file = os.path.abspath(pathname) + "/autopwn.apc"

            with open(autopwn_config_file, 'w') as global_config_file:
                global_config_file.write( yaml.dump(config.global_config, default_flow_style=True) )
            config.load("global_config")
        else:
            config.instance['config'][option] = value

        print(option + " = " + str(value))

class Process:
    def __init__(self, config):
        info = {}

        if len(config.job_queue) == 0:
            print("No jobs to run")
            return

        for instance in config.job_queue:
            instance['parallel'] = config.arguments['parallel'] or config.global_config['parallel']
            instance['options']['date'] = strftime("%Y%m%d_%H%M%S%z")
            instance['options']['date_day'] = strftime("%Y%m%d")
            instance['options']['output_dir'] = instance['options']['date_day'] + \
                                "_autopwn_" + \
                                instance['options']['target_name']

            if hasattr(instance,'binary_prepend') == True:
                if self.binary_exists(instance['binary_prepend']) != True:
                    print("[I] Missing binary/script - " + instance['binary_prepend'])
                    #return debug:
            if self.binary_exists(instance['binary_name']) != True:
                # Error(50,"[E] Missing binary/script - " + instance['binary_name'])
                print("[I] Missing binary/script - " + instance['binary_name'])
                #return debug:

            if hasattr(instance,'binary_prepend') == True:
                instance['execute_string'] = instance['binary_prepend'] + " " + instance['binary_name'] + " " + instance['arguments']
            else:
                instance['execute_string'] = instance['binary_name'] + " " + instance['arguments']

            if config.arguments['screen'] == True:
                if self.binary_exists('screen') != True and self.binary_exists('bash') != True:
                    Error(50,"[E] Missing binary - screen or bash")
                instance['screen_name'] = "autopwn_" + \
                        instance['options']['target_name'] + "_" + \
                        instance['options']['target'] + "_" + \
                        instance['name']
                instance['execute_string'] = "screen -D -m -S " + \
                instance['screen_name'] + " " + "bash -c '" + \
                        instance['execute_string'] + \
                        "'"
            ddict_options = defaultdict(lambda : '')
            for option in instance['options']:
                ddict_options[option] = instance['options'][option]

            # Option replacements
            instance['execute_string'] = instance['execute_string'].format(**ddict_options)

        # Run jobs
        Execute(config)

    def binary_exists(self, binary_string):
        try:
            which_return_code = subprocess.call(["which",binary_string],stdout=open(os.devnull,'wb'),stderr=open(os.devnull,'wb'))
            if which_return_code == 0:
                return True
            else:
                return False
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                Error(55,"[E] 'which' binary couldn't be found")
            else:
                # Not sure what's happening at this point
                raise

# Load target files
class Load:
    def __init__(self, config, arg):
        # TODO check file exists
        if os.path.isfile(arg) == True:
            stream = open(arg, 'r')
            target_objects = yaml.load(stream)
            config.status['file_found'] = True
        else:
            config.status['file_found'] = False
            print("[I] Targets file not found")
            return

        for target in target_objects['targets']:
            AutoSet(config,target)

class Save:
    def __init__(self, config):
        if len(config.instance['tool']) == 0:
            print("No tool options to save")
            return
        for imported_tool in config.tools:
            for selected_tool in config.instance['tool']:
                if selected_tool == imported_tool['name']:
                    config.job_queue.append(copy.deepcopy(imported_tool))
                    config.job_queue_add_success = True
                    config.job_queue[-1]['options'] = {}
                    for option in config.instance['config']:
                        config.job_queue[-1]['options'][option] = \
                            config.instance['config'][option]

                    # Check all required parameters exist before save
                    for option in imported_tool['options']:
                        parameter_found = False
                        tool_option = imported_tool['options'][option]\
                                        .get('required', False)

                        if type(tool_option) == list:
                            ### Check that at least one exists
                            for required_option in tool_option:
                                parameter_found = parameter_found or \
                                                  self.check_required_exists\
                                                  (config,required_option)
                        if tool_option == True:
                            parameter_found = self.check_required_exists\
                                              (config,option)

                        if parameter_found == False and tool_option == True:
                            #print("debug: remove_instance to be called due to parameter_found == false and tool_option == true")
                            self.remove_instance(config)
                            return

                    # Set default option values for options
                    # (An option value becomes another option value)
                    for option in imported_tool['options']:
                        #print("debug: option == " + option)
                        default_option_value = imported_tool['options'][option].\
                                        get('default_option_value', None)
                        # Is there a default option
                        if default_option_value != None:
                            #print("debug: config.instance = " + str(config.instance['config']))
                            config.instance['config'][option] = \
                                str(config.instance['config'][option][default_option_value])
                        #else:
                        #    print("debug config.instance = " + str(config.instance['config']))
                        #    print("debug: remove_instance to be called due to default_option set to none")
                        #    self.remove_instance(config)
                        #    return

        if config.status['command_line'] != True:
            if len(config.job_queue) == 1:
                print("There is 1 job in the queue")
            else:
                print("There are " + str(len(config.job_queue)) + \
                      " jobs in the queue")

    def remove_instance(self, config):
        # TODO Check this actually works 
        # now that assessments are in
        #print("debug: remove_instance trigger!")
        config.job_queue.pop()
        config.job_queue_add_success = False

        if config.status['command_line'] != True:
            print("Some required parameters have not been set")

    def check_required_exists(self, config, option):
        parameter_found = False

        for tool in config.tools:
            if config.job_queue[-1]['name'] == tool['name']:
                instance_tool = tool
                break

        if option in config.job_queue[-1]['options'] or \
           instance_tool['options'][option]\
           .get('default_option_value', None) != None:
            parameter_found = True
        return parameter_found

class Execute:
    thread = []
    index = 0

    def __init__(self, config):
        for instance in config.job_queue:
            # Create log directory in CWD
            if not os.path.exists(instance['options']['output_dir']):
                try:
                    os.makedirs(instance['options']['output_dir'])
                except OSError as e:
                    Error(20,"[E] Error creating output directory: " + e)

            if 'url' in instance:
                log = Log(config, os.getcwd(), False, 'tool_string',"# Executing " + \
                          instance['name'] + " tool (" + instance['url'] + ") for " + \
                          instance['options']['target_name'] + ":\n" + \
                          instance['execute_string'])
            else:
                log = Log(config, os.getcwd(), False, 'tool_string',"# Executing " + \
                          instance['name'] + " tool:\n# " + \
                          instance['execute_string'])

            time.sleep (0.1);
            self.thread.append(RunThreads(config,instance))
            # If main process dies, everything else *SHOULD* as well
            self.thread[-1].daemon = True
            # Start threads
            self.thread[-1].start()

            # Parallel or singular?
            if instance['parallel'] != True:
                while threading.activeCount()>1:
                    pass

                self.index = self.index + 1
            else:
                print(instance['execute_string'])
                pass

        if instance['parallel'] == True:
            while threading.activeCount()>1:
                pass
            #for tid in self.thread:
            #    tid.join(1)

class RunThreads (threading.Thread):
    def __init__(self, config, instance):
        threading.Thread.__init__(self)
        self.tool_stdout = ''
        self.tool_sterr = ''
        self.instance = instance
        self.config = config

    def execute_tool(self):
        # Always check any tools provided by
        # community members
        # Bad bug using this and no shell for Popen,
        # will come back to this
        #command_arguments = shlex.split(tool_execute_string)
        proc = Popen(self.instance['execute_string'], stdout=PIPE, stderr=PIPE, shell=True)

        decode_locale = lambda s: s.decode(getlocale()[1])
        self.tool_stdout, self.tool_stderr = map(decode_locale, proc.communicate())

        exitcode = proc.returncode

    def run(self):
        print("[+] Launching " + self.instance['name'] + \
              " for " + self.instance['options']['target_name'])
        self.execute_tool()
        print("[-] " + self.instance['name'] + " for " + \
              self.instance['options']['target_name'] + " is done..")
        # Should we create a stdout log for this tool?
        stdout_boolean = self.instance['stdout']
        if stdout_boolean == True:
            log = Log(self.config, os.getcwd() + "/" + self.instance['options']['output_dir'],
                      self.instance['options']['target_name'] + "_" + self.instance['name'],
                      'tool_output', self.tool_stdout)
        log = Log(self.config, os.getcwd(), False, 'tool_string', "# " + \
                  self.instance['name'] + " for " + \
                  self.instance['options']['target_name'] + " has finished")

class Log:
    def __init__(self, config, directory, log_filename, log_type, log_string):
        date = strftime("%Y%m%d")
        date_time = strftime("%Y%m%d %H:%M:%S %z")
        date_time_filename = strftime("%Y%m%d_%H%M%S%z")

        if log_type == 'tool_output':
            try:
                # log_filename is pikey, make it better
                log_file = open(directory + "/" + date_time_filename + \
                                "_" + log_filename + "_stdout.log","a")
            except OSError as e:
                Error(30,"[E] Error creating log file: " + e)

            log_file.write(log_string)
            log_file.close()

        if log_type == 'tool_string':
            try:
                log_file = open(date + "_autopwn_commands.log","a")
            except OSError as e:
                Error(30,"[E] Error creating log file: " + e)
            if config.status['log_started'] != True:
                log_file.write("## autopwn 0.21.1 command output\n")
                log_file.write("## Started logging at " + date_time + "...\n")
                config.status['log_started'] = True

            log_file.write("# " + date_time + "\n")
            log_file.write(log_string + "\n")
            log_file.close()

        if log_type == 'individual_target':
            try:
                log_file = open(directory + "/target","w")
            except OSError as e:
                Error(30,"[E] Error creating log file: " + e)
            log_file.write(log_string + "\n")
            log_file.close()

class Run:
    def __init__(self, config):
        # Process job queue (replace placeholders)
        Process(config)

class Debug:
    def __init__(self, config, arg):
        import IPython; IPython.embed()

class Clear:
    def __init__(self, config, arg):
        config.job_queue = []
        print("Job queue cleared")

class View:
    def __init__(self, view, config, **kwargs):
        if kwargs is None:
            kwargs = defaultdict(lambda : '')

        if view == 'load':
            if config.status['file_found'] == True:
                print("Loaded target file")
        if view == 'clear':
            pass
        if view == 'command_line_pre_save':
            for key, value in kwargs.items():
                print("Loading " + value['target_name'] + " with " + config.instance['tool'][-1] + "...",end="")
        if view == 'command_line_post_save':
            for key, value in kwargs.items():
                if  config.job_queue_add_success == True:
                    print("Done!")
                else:
                    print("Failed!")
        if view == 'use':
            option_displayed = []
            # Show assessment info
            if config.instance['config']['assessment'] == True:
                for assessment in config.assessments:
                    if assessment['name'] == \
                       config.instance['config']['assessment_name']:
                        print('Name: ' + assessment['name'])
                        print('Long name: ' + assessment['long_name'])
                        print('Description: ' + assessment['description'])
                        print()
                        print('The follwing tools are used in this assessment:')
                        for tool in config.tools:
                            if assessment['name'] in tool['assessment_groups']:
                                print("- " + tool['name'])
                        print()

            if config.instance['config']['single_tool'] == True:
                if config.status['resource_found'] == False:
                    print("Please specify a valid tool or assessment")
                else:
                    for tool in config.tools:
                        if tool['name'] == config.instance['tool'][0]:
                            print('Name: ' + tool['name'])
                            print('Description: ' + tool['description'])
                            print('URL: ' + tool['url'])
                            print()

class CleanUp:
    def __init__(self):
        # Kill screen sessions. Needs improvement
        for screen in list_screens():
            if screen.name.startswith("autopwn"):
                screen.kill()

class Shell(cmd.Cmd):
    config = Configuration(False)
    prompt = 'autopwn > '

    def cmdloop(self, intro=None):
        try:
            cmd.Cmd.cmdloop(self, intro)
        except KeyboardInterrupt as e:
            print()
            print("Type 'quit' to exit autopwn shell")
            self.cmdloop()

    def emptyline(self):
        pass

    def do_shell(self, arg):
        'Execute shell commands'
        os.system(arg)

    def do_clear(self, arg):
        'Clear job queue'
        Clear(self.config,arg)
        View('clear',self.config)

    def do_search(self, arg):
        'Search function'
        Search(self.config,arg)
        View('search',self.config)

    def do_debug(self, arg):
        'Drop to IPython shell'
        Debug(self.config,arg)
        View('debug',self.config)

    def do_show(self, arg):
        'Show information'
        Show(self.config,arg)
        View('show',self.config)

    def complete_show(self, text, line, begin, end):
        operations = ['options','jobs','config']

        if not text:
            completions = operations
        else:
            completions = [ operation
                            for operation in operations
                                if text in operation
                          ]
        return completions

    def do_load(self, arg):
        'Load target file'
        Load(self.config,arg)
        View('load',self.config)

    def do_save(self, arg):
        'Save instance settings'
        Save(self.config)
        View('save',self.config)

    def do_run(self, arg):
        'Run job queue'
        Run(self.config)
        View('run',self.config)

    def do_use(self, arg):
        'Setup a tool or assessment'
        Use(self.config,arg)
        View('use',self.config,target=self.config.instance)
        if self.config.status['resource_found'] == True:
            if (sys.stdout.isatty()) == True:
                arg = '\x1b[%sm%s\x1b[0m' % \
                    (';'.join(['31']), arg)
            self.prompt = 'autopwn (' + arg + ') > '

    def complete_use(self, text, line, begin, end):
        completions = ''
        if not text:
            # Add assessments
            completions = [ assessment['search_name']
                            for assessment in self.config.assessments
                          ]
            # Add tools
            completions = completions + [ tool['search_name']
                            for tool in self.config.tools
                          ]
        else:
            # Add assessments which match
            completions = [ assessment['search_name']
                            for assessment in self.config.assessments
                                if line.split(' ')[1] in assessment['search_name']
                          ]

            # Add tools which match
            completions = completions + [ tool['search_name']
                            for tool in self.config.tools
                                if line.split(' ')[1] in tool['search_name']
                          ]
        return completions

    def do_set(self, arg):
        'Set configuration option'
        Set(self.config,arg)
        View('set',self.config)

    def complete_set(self, text, line, begin, end):
        for tool in self.config.tools:
            if tool['name'] in self.config.instance['tool']:
                completions = tool['options']
        if text != None:
            completions = [ parameter
                            for parameter in completions
                                if text in parameter
                          ]
        return completions

    def do_unset(self, arg):
        'Clear configuration option'
        Unset(self.config,arg)
        View('unset',self.config)

    def complete_unset(self, text, line, begin, end):
        for tool in self.config.tools:
            if tool['name'] in self.config.instance['tool']:
                completions = tool['options']
        if text != None:
            completions = [ parameter
                            for parameter in completions
                                if text in parameter
                          ]
        return completions

    def do_bye(self, arg):
        'Quit autopwn'
        self.terminate()

    def do_exit(self, arg):
        'Quit autopwn'
        self.terminate()

    def do_quit(self, arg):
        'Quit autopwn'
        self.terminate()

    def terminate(self):
        'Exit Autopwn'
        quote = []
        quote.append("Never underestimate the determination of a kid who is time-rich and cash-poor.")
        quote.append("There are few sources of energy so powerful as a procrastinating college student.")
        quote.append("I/O, I/O, It's off to disk I go. A bit or byte to read or write, I/O, I/O, I/O...")
        quote.append("SUPERCOMPUTER: what it sounded like before you bought it.")
        quote.append("Is reading in the bathroom considered Multi-Tasking?")
        quote.append("Premature optimisation is the root of all evil.")
        quote.append("The first rule of optimisation is: Don't do it. The second rule of optimisation is: Don't do it yet.")
        quote.append("Q: How many software engineers does it take to change a lightbulb? A: It can't be done; it's a hardware problem.")
        quote.append("Hackers are not crackers.")
        quote.append("Behind every successful Coder there an even more successful De-coder ")
        quote.append("If at first you don't succeed; call it version 1.0.")
        quote.append("F*ck it, we'll do it in production.")
        quote.append("Programmers are tools for converting caffeine into code.")
        quote.append("Those who can't write programs, write help files.")
        print(random.choice(quote))
        CleanUp()
        sys.exit(0)

def _main(arglist):
    # Process command line arguments
    if len(sys.argv) > 1:
        Arguments(sys.argv[1:]).parser
    else:
        # Drop user to shell
        Shell().cmdloop("autopwn 0.21.1 shell. Type help or ? to list commands.\n")

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
