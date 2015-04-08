#!/usr/bin/python2

import copy
import sys
import getopt
import re
import subprocess
import os
import shlex
import threading
import time
import yaml
from collections import OrderedDict
from screenutils import list_screens, Screen
from subprocess import Popen, PIPE
from time import gmtime, strftime

# Aidan Marlin @ NCC Group
# Project born 201502

class Log:
   def __init__(self, config, directory, log_filename, log_type, log_string):
      date = strftime("%Y%m%d")
      date_time = strftime("%Y%m%d %H:%M:%S") # TODO Offset time

      if log_type == 'tool_output':
         try:
            # log_filename is pikey, make it better
            log_file = open(directory + "/" + date + "_autopwn_" + log_filename + "_stdout.log","a")
         except OSError as e:
            print "[E] Error creating log file: " + e
            sys.exit(1)

         log_file.write(log_string)
         log_file.close()

      if log_type == 'tool_string':
         try:
            log_file = open(date + "_autopwn_commands.log","a")
         except OSError as e:
            print "[E] Error creating log file: " + e
            sys.exit(1)
         try:
            if config.log_started != True:
               log_file.write("## autopwn v0.9 command output\n")
               config.log_started = True
         except:
            pass
         log_file.write("# " + date_time + "\n")
         log_file.write(log_string + "\n")
         log_file.close()

      if log_type == 'individual_target':
         try:
            log_file = open(directory + "/target","w")
         except OSError as e:
            print "[E] Error creating log file: " + e
            sys.exit(1)
         log_file.write(log_string + "\n")
         log_file.close()

class Run:
   thread = []
   index = False

   def __init__(self, tool_subset, assessment_type, config):
      if config.dry_run == True:
         print "--------------------------------"
         print "The following tools will be run:"
         print "--------------------------------"
      for tool in tool_subset:
         # Run for real
         if config.dry_run != True:
            try:
               log = Log(config,os.getcwd(),False,'tool_string',"# Executing " + \
                     tool['name'] + " tool (" + tool['url'] + "):\n" + \
                     tool['execute_string'])
            except:
               log = Log(config,os.getcwd(),False,'tool_string',"# Executing " + \
                     tool['name'] + " tool:\n# " + \
                     tool['execute_string'])

            time.sleep (0.1);
            self.thread.append(RunThreads(self.index, tool))
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
            print tool['execute_string']
            pass

      if config.dry_run != True:
         if assessment_type['parallel'] == True:
            while threading.activeCount()>1:
               pass
            #for tid in self.thread:
            #   tid.join(1)

class RunThreads (threading.Thread):
   def __init__(self, thread_ID, tool):
      threading.Thread.__init__(self)
      self.kill_received = False
      self.thread_ID = thread_ID
      self.tool_name = tool['name']
      self.tool_execute_string = tool['execute_string']
      self.tool_output_dir = tool['output_dir']
      self.target_name = tool['host']['target_name']
      self.tool_stdout = ''
      self.tool_stderr = ''

   def execute_tool(self, thread_ID, tool_name,
                     tool_execute_string):
      # Always check any tools provided by
      # community members
      command_arguments = shlex.split(tool_execute_string)
      proc = Popen(command_arguments, stdout=PIPE, stderr=PIPE)

      self.tool_stdout, self.tool_stderr = proc.communicate()
      exitcode = proc.returncode

   def run(self):
      print "[+] Launching " + self.tool_name
      self.execute_tool(self.thread_ID, self.tool_name,
                        self.tool_execute_string)
      print "[-] " + self.tool_name + " is done.."
      log = Log(False, os.getcwd() + "/" + self.tool_output_dir,
            self.target_name + "_" + self.tool_name,
            'tool_output', self.tool_stdout)
      log = Log(False, os.getcwd(), False, 'tool_string', "# " + \
            self.tool_name + " has finished")

class Tools:
   def __init__(self, config, args, assessment):
      config.tool_subset = []
      for tool in config.tools_config:
         if tool['name'] in assessment['tools']:
            config.tool_subset.append(tool)

      print "autopwn v0.9 by Aidan Marlin"
      print "email: aidan [dot] marlin [at] nccgroup [dot] com"
      print

      self.replace_placeholders(config, assessment)
      self.check_exists(config, args, assessment)

      if args.argument['with_screen'] == True:
         self.prepend_tool(config, 'screen')

   def prepend_tool(self, config, prepend_tool):
      if prepend_tool == 'screen':
         index = False
         for host in config.target_list:
            for tool in config.tool_subset:
               config.tool_subset_evaluated[index]['execute_string'] = \
                  "screen -D -m -S autopwn_" + \
                  host['target_name'] + "_" + \
                  host['target_domain_name'] + "_" + host['target_ip'] + \
                  "_" + tool['name'] + " " + "/bin/bash -c '" + \
                  config.tool_subset_evaluated[index]['execute_string'] + \
                  "'"

               index = index + 1

   def check_exists(self, config, args, assessment):
      error_type = '[E]'

      for tool in config.tool_subset:
         if os.path.isfile(tool['binary_location']) == False:
            if args.argument['ignore_missing_binary'] == True:
               error_type = '[W]'

            print error_type + " Could not find binary for " + tool['name']

            if args.argument['ignore_missing_binary'] == False:
               sys.exit(1)

   def replace_placeholders(self, config, assessment):
      config.tool_subset_evaluated = []

      for host in config.target_list:
         for tool in config.tool_subset:
            config.tool_subset_evaluated.append(copy.deepcopy(tool))

            # Variable declaration for placeholder replacements
            date = strftime("%Y%m%d_%H%M%S")
            date_day = strftime("%Y%m%d")
            config.tool_subset_evaluated[-1]['output_dir'] = date_day + "_autopwn_" + host['target_ip'] + "_" + host['target_name']
            config.tool_subset_evaluated[-1]['host'] = host
            output_dir = config.tool_subset_evaluated[-1]['output_dir']

            # Create log directory in CWD
            if not os.path.exists(output_dir):
               try:
                  os.makedirs(output_dir)
               except OSError as e:
                  print "[E] Error creating output directory: " + e
                  sys.exit(1)

            # Create target file in new directory
            try:
               Log(config,output_dir,'individual_target',host['target_ip'] + '#' + \
                  host['target_domain_name'] + '#' + \
                  host['target_port_number'] + '#' + \
                  host['target_protocol'])
            except:
               # Not all target arguments specified
               Log(config,output_dir,False,'individual_target',host['target_ip'])

            # Replace placeholders for tool argument string
            tool_arguments_instance = config.tool_subset_evaluated[-1]['arguments'].format(
                                       target_domain_name=host['target_domain_name'],
                                       target_ip=host['target_ip'], date=date,
                                       target_port_number=host['target_port_number'],
                                       target_protocol=host['target_protocol'],
                                       target_url=host['target_url'],
                                       target_name=host['target_name'],
                                       output_dir=output_dir)

            config.tool_subset_evaluated[-1]['execute_string'] = config.tool_subset_evaluated[-1]['binary_location'] + " " + \
                                    tool_arguments_instance

            # Replace placeholders for pre tool command string
            if 'pre_tool_execution' in config.tool_subset_evaluated[-1]:
               config.tool_subset_evaluated[-1]['pre_tool_execution'] = config.tool_subset_evaluated[-1]['pre_tool_execution'].format(
                                       target_domain_name=host['target_domain_name'],
                                       target_ip=host['target_ip'], date=date,
                                       target_port_number=host['target_port_number'],
                                       target_protocol=host['target_protocol'],
                                       target_url=host['target_url'],
                                       target_name=host['target_name'],
                                       output_dir=output_dir)

            # Replace placeholders for post tool command string
            if 'post_tool_execution' in config.tool_subset_evaluated[-1]:
               config.tool_subset_evaluated[-1]['post_tool_execution'] = config.tool_subset_evaluated[-1]['post_tool_execution'].format(
                                       target_domain_name=host['target_domain_name'],
                                       target_ip=host['target_ip'], date=date,
                                       target_port_number=host['target_port_number'],
                                       target_protocol=host['target_protocol'],
                                       target_url=host['target_url'],
                                       target_name=host['target_name'],
                                       output_dir=output_dir)

class Menus:
   # Not 0 because this is a valid selection..
   item_selected = ''

   def __init__(self, menu_items, menu_name):
      if menu_name == 'assessment':
         self.display_assessment_menu(menu_items)

   def display_assessment_menu(self, menu_items):
      valid_option_index = False

      print "What assessment do you want to run?"
      for index, item in enumerate(menu_items):
         if item != '':
            print str(index) + ") " + str(item)
            valid_option_index = valid_option_index + 1

      try:
         self.item_selected = raw_input('Choose > ')
         print
      except (KeyboardInterrupt, SystemExit):
         print
         print "[E] Abandon ship!"
         sys.exit(1)
      if self.item_selected == '': # TODO - Review
         print "[E] No choice was made, quitting.."
         sys.exit(1)
      else:
         if int(self.item_selected) >= False and \
               int(self.item_selected) < valid_option_index:
            self.item_selected = int(self.item_selected)
         else:
            print "[E] Invalid option, quitting.."
            sys.exit(1)

class Assessments:
   assessment_type = ""

   def __init__(self, config, argument_assessment):
      # Shall we process assessment from command line
      # arguments or display menu?
      if argument_assessment != '':
         argument_assessment_found = False
         # Command line
         for assessment_type in config.assessments_config:
            if assessment_type['name'] == argument_assessment:
               self.assessment_type = assessment_type
               argument_assessment_found = True
         if argument_assessment_found != True:
            print "[E] Assessment name not found. Is it spelt correctly?"
            sys.exit(1)
      else:
         # Display menu
         config.dry_run = True
         menu = Menus(config.menu_items,'assessment')
         self.assessment_type = config.assessments_config[menu.item_selected]

      #print "self.assessment_type = " + str(self.assessment_type)
      #sys.exit(1)

class Print:
   def __init__(self, display_text, file_descriptor):
      if display_text == 'help':
         self.display_help(file_descriptor)

   def display_help(self, file_descriptor):
      # Not doing anything with file_descriptor yet
      print "autopwn v0.9"
      print "By Aidan Marlin"
      print "Email: aidan [dot] marlin [at] nccgroup [dot] com"
      print
      print "-t <target_file>       Required. The file containing the"
      print "                       targets"
      print "-a <assessment_type>   Optional. Specify assessment name"
      print "                       to run."
      print "                       Autopwn will not prompt to run"
      print "                       tools with this option"
      print "-i                     Optional. Ignore missing binary"
      print "                       conditions"
      print "-r                     Optional. Ignore tool rulesets"
      print "-s                     Optional. Launch tool with screen"
      print
      print "Format of the target file should be:"
      print
      print "targets:"
      print "   - target_name: <target-name>"
      print "     ip_address: <ip-address>"
      print "     domain: <domain>"
      print "     url: <url-path>"
      print "     port: <port-number>"
      print "     protocol: <protocol>"
      print "     mac_address: <mac_address>"
      print "   - target_name: <target-name-1>"
      print "     ..."
      print
      print "Only 'target_name' and 'ip_address' are compulsory options."
      print "Example file:"
      print
      print "targets:"
      print "   - target_name: test"
      print "     ip_address: 127.0.0.1"
      print "     domain: test.com"
      print "     url: /test"
      print "     port: 80"
      print "     protocol: https"
      print "   - target_name: test-1"
      print "     ip_address: 127.0.0.2"
      print
      print "autopwn uses the tools/ directory located where this"
      print "script is to load tool definitions, which are yaml"
      print "files. You can find some examples in the directory"
      print "already. If you think one is missing, mention it on"
      print "GitHub or email me and I might add it."
      print
      print "autopwn also uses assessments/ for assessment definitions."
      print "Instead of selecting which tools you would like to run,"
      print "you specify which assessment you would like to run."
      print "Assessment configuration files contain lists of tools"
      print "which will be run as a result."
      print
      print "Have fun!"
      print "Legal purposes only.."
      print
      sys.exit(1)

class Arguments:
   argument = {'assessment':'', 'target_file':'',
               'ignore_missing_binary':False, 'ignore_rules':False,
               'with_screen':False}

   def __init__(self, arguments):
      # If no arguments specified, dump autopwn help / description
      if len(sys.argv) == True:
         help = Print('help', 'stdout')

      try:
         opts, args = getopt.getopt(arguments,"irsa:t:",["assessment=","target="])
      except getopt.GetoptError:
         print "./autopwn.py [-irs] [-a <assessment_type>] -t <target_file>"
         sys.exit(1)

      for opt, arg in opts:
         if opt in ("-a", "--assessment"):
            # Assessment type
            self.argument['assessment'] = arg
         if opt in ("-t", "--target"):
            # Target file
            self.argument['target_file'] = arg
         if opt in ("-i", "--ignore-missing"):
            # Ignore missing binary files
            self.argument['ignore_missing_binary'] = True
         if opt in ("-r", "--ignore-rules"):
            # Ignore tool rule violations
            self.argument['ignore_rules'] = True
         if opt in ("-s", "--with-screen"):
            # Ignore tool rule violations
            self.argument['with_screen'] = True

      if self.argument['target_file'] == '':
         print "[E] Target file not specified"
         sys.exit(1)

# Configuration class loads all information from .apc files and target file
class Configuration:
   # Class vars
   log_started = False
   autopwn_config = {'parallel': False,
                     'parallel_override': False,
                     'scripts_directory':''}
   tools_config = []
   assessments_config = []
   menu_items = []
   target_list = []
   dry_run = False

   # This method will pull configuration and target file information
   # Will probably split into separate methods at some point
   def __init__(self, target_file):
      i = False

      pathname = os.path.dirname(sys.argv[0])
      tools_directory = os.path.abspath(pathname) + "/tools/"
      assessments_directory = os.path.abspath(pathname) + \
                              "/assessments/"

      # Pull global config
      autopwn_global_config_file = pathname + '/autopwn.apc'
      stream = open(autopwn_global_config_file, 'r')
      objects = yaml.load(stream)

      # Global parallel
      try:
         self.autopwn_config['parallel'] = objects['parallel']
         self.autopwn_config['parallel_override'] = True
      except:
         pass

      # Scripts directory
      try:
         self.autopwn_config['scripts_directory'] = objects['scripts_directory']
      except:
         print "[E] Missing option in autopwn configuration file: scripts_directory is mandatory"
         sys.exit(1)

      # Pull tool configs
      for file in os.listdir(tools_directory):
         if file.endswith(".apc"):
            stream = open(tools_directory + file, 'r')
            objects = yaml.load(stream)

            self.tools_config.append({'name':'',
                                       'binary_location':'',
                                       'arguments':''
                                       })

            self.tools_config[i]['name'] = objects['name']
            self.tools_config[i]['binary_location'] = objects['binary_location']
            self.tools_config[i]['arguments'] = objects['arguments']
            # The following options are not compulsory
            try:
               self.tools_config[i]['rules'] = objects['rules']
            except:
               pass
            try:
               self.tools_config[i]['pre_tool_execution'] = objects['pre_tool_execution']
            except:
               pass
            try:
               self.tools_config[i]['post_tool_execution'] = objects['post_tool_execution']
            except:
               pass
            try:
               self.tools_config[i]['url'] = objects['url']
            except:
               pass

            i = i + 1

      # Pull assessment configs
      i = False
      for file in os.listdir(assessments_directory):
         if file.endswith(".apc"):
            stream = open(assessments_directory + file, 'r')
            objects = yaml.load(stream)

            self.assessments_config.append({'name':'','tools':'',
                                             'menu_name':'',
                                             'parallel':''})
            self.assessments_config[i]['name'] = objects['name']
            self.assessments_config[i]['tools'] = objects['tools']
            self.assessments_config[i]['menu_name'] = objects['menu_name']
            if self.autopwn_config['parallel_override'] == True:
               self.assessments_config[i]['parallel'] = self.autopwn_config['parallel']
            else:
               self.assessments_config[i]['parallel'] = objects['parallel']

            i = i + 1

      # Assign menu_items
      for config_assessment_menu_item in self.assessments_config:
         self.menu_items.append(config_assessment_menu_item['menu_name'])

      ###
      # Get targets
      ###
      try:
         fd_targets = open(target_file, 'r')
         yaml_content = yaml.load(fd_targets)
         #for target in yaml_content['targets']:
         #   print target
         fd_targets.close()
      except IOError as e:
         print "[E] Error processing target file: {1}".format(e.errno,
                                                               e.strerror)
         sys.exit(1)

      # Process each target in target list
      target_name_matrix = []

      for target in yaml_content['targets']:
            # If attributes haven't been specified, set to False
            try:
               # Does this exist? It bloody well should
               target['target_name']
            except:
               print "[E] Target name missing: Target name must be specified"
               sys.exit(1)
            if target['target_name'] in target_name_matrix:
               print "[E] Duplicate target names identified"
               sys.exit(1)
            else:
               target_name_matrix.extend([target['target_name']])
               target_name = target['target_name']
            try:
               target_ip = target['ip_address']
            except:
               print "[E] Target file missing IP address(es)"
               sys.exit(1)
            try:
               target_domain_name = target['domain']
            except:
               target_domain_name = target_ip
            try:
               target_port_number = target['port']
            except:
               target_port_number = False
            try:
               target_protocol = target['protocol']
            except:
               target_protocol = False
            try:
               target_url = target['url']
               # Forward slash (/) SHOULD already be in tool argument string
               if target_url.startswith('/'):
                  target_url = target_url[1:]
            except:
               target_url = ''

            self.target_list.append({'target_ip':target_ip,
                                     'target_domain_name':target_domain_name,
                                     'target_port_number':target_port_number,
                                     'target_url':target_url,
                                     'target_name':target_name,
                                     'target_protocol':target_protocol})

class Prompt:
   def __init__(self, prompt, config, tools, assessment):
      if prompt == 'run_tools':
         self.show_post_commands(config,assessment)
         self.run_tools(config,tools,assessment)

   def show_post_commands(self, config, assessment):
      # Run post-tool execution commands
      # config.dry_run is assumed, but let's bail if
      # it's not set as expected
      if config.dry_run == True:
         Commands(config,assessment.assessment_type,'post')
      else:
         print "[E] Dry run variable not set as expected. " + \
               "You shouldn't see this error"
         sys.exit(1)

   def run_tools(self, config, tools, assessment):
      if config.autopwn_config['parallel_override'] == True:
         print "[I] Global parallel option set"
      run_tools = raw_input('Run tools? [Ny] ')

      if run_tools.lower() == "y":
         config.dry_run = False
         # Run pre-tool execution commands
         Commands(config,assessment.assessment_type,'pre')
         Run(config.tool_subset_evaluated,assessment.assessment_type,config)
         # Run post-tool execution commands
         Commands(config,assessment.assessment_type,'post')
         sys.exit(0)
      else:
         print "[E] Alright, I quit.."
         sys.exit(1)

class Rules:
   def __init__(self, args, config, tools):
      self.check(args, config, tools)

   def check(self, args, config, tools):
      # Hosts
      rule_violation = False
      for host_index, host in enumerate(config.target_list):
         # Tools
         for tool_config_index, tool_config in enumerate(config.tools_config):
            check_tool_rule = False
            for tool in config.tool_subset:
               #print tool_config['name']
               #print tool['name']
               if tool_config['name'] == tool['name']:
                  check_tool_rule = True

            if check_tool_rule != True:
               continue

            # Check
            try:
               for rule_type in tool_config['rules']:
                  if rule_type == 'target-parameter-exists':
                     #print "rule_type " + rule_type
                     for argument in tool_config['rules'][rule_type]:
                        #print "argument0 " + argument
                        rule_violation_tmp = self.check_comparison(host,tool_config,
                                           rule_type,argument,
                                           False)
                        rule_violation = rule_violation or rule_violation_tmp
                  else:
                     for argument in tool_config['rules'][rule_type]:
                        rule_violation_tmp = self.check_comparison(host,tool_config,
                                        rule_type,argument,
                                        tool_config['rules'][rule_type][argument])
                  rule_violation = rule_violation or rule_violation_tmp
            except:
               pass

      if rule_violation:
         error_type = '[E]'

         if args.argument['ignore_rules'] == True:
            error_type = '[W]'

         print error_type + " There were rule violations"

         if args.argument['ignore_rules'] == False:
            sys.exit(1)

   def check_comparison(self,host,tool_config,rule_type,argument,argument_value):
      error = False
      if rule_type == 'not-equals':
         if host[argument] == argument_value:
            print "[W] Rule violation in " + tool_config['name'] + \
                  " for host " + host['target_domain_name'] + \
                  ": '" + argument + "' must be '" + argument_value + "'"
            error = True
      elif rule_type == 'equals':
         if host[argument] != argument_value:
            print "[W] Rule violation in " + tool_config['name'] + \
                  " for host " + host['target_domain_name'] + \
                  ": '" + argument + "' must be '" + argument_value + "'"
            error = True
      elif rule_type == 'greater-than':
         if host[argument] > argument_value:
            print "[W] Rule violation in " + tool_config['name'] + \
                  " for host " + host['target_domain_name'] + \
                  ": '" + argument + "' must be greater than '" + argument_value + "'"
            error = True
      elif rule_type == 'less-than':
         if host[argument] < argument_value:
            print "[W] Rule violation in " + tool_config['name'] + \
                  " for host " + host['target_domain_name'] + \
                  ": '" + argument + "' must be less than '" + argument_value + "'"
            error = True
      elif rule_type == 'target-parameter-exists':
         if host[argument] == False:
            print "[W] Rule violation in " + tool_config['name'] + \
                  " for host " + host['target_domain_name'] + \
                  ": '" + argument + "' not specified in target"
            error = True

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
               print "The following pre-tool execution commands will be run:"
               print "--------------------------------"
               display_pre_command_banner = False

      for tool in config.tool_subset_evaluated:
         try:
            if config.dry_run == True:
               print tool['pre_tool_execution']
            else:
               if 'pre_tool_execution' in tool:
                  print "[+] Running pre-tool commands for " + tool['name']
                  subprocess.call(tool['pre_tool_execution'],shell = True)
                  print "[-] Pre-tool commands for " + tool['name'] + " have completed.."
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
               print "--------------------------------"
               print "The following post-tool execution commands will be run:"
               print "--------------------------------"
               display_post_command_banner = False
      for tool in config.tool_subset_evaluated:
         try:
            if config.dry_run == True:
               print tool['post_tool_execution']
            else:
               if 'post_tool_execution' in tool:
                  print "[+] Running post-tool commands for " + tool['name']
                  subprocess.call(tool['post_tool_execution'],shell = True)
                  print "[-] Post-tool commands for " + tool['name'] + " have completed.."
                  log = Log(config,os.getcwd(),False,'tool_string',
                        "# Post-tool commands for " + tool['name'] + \
                        " has finished")

         except:
            pass

class CleanUp:
   def __init__(self):
      for screen in list_screens():
         if screen.name.startswith("autopwn"):
            screen.kill()

def main():
   # Process arguments
   args = Arguments(sys.argv[1:])
   # Pull config
   config = Configuration(args.argument['target_file'])
   # Determine assessment
   assessment = Assessments(config,args.argument['assessment'])
   # Process tools
   tools = Tools(config,args,assessment.assessment_type)
   # Check rules
   Rules(args,config,tools)
   # Run pre-tool execution commands
   Commands(config,assessment.assessment_type,'pre')
   # Run tools
   execute = Run(config.tool_subset_evaluated,assessment.assessment_type,config)
   if config.dry_run == True:
      Prompt('run_tools',config,tools,assessment)
   # Run post-tool execution commands
   Commands(config,assessment.assessment_type,'post')

if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      CleanUp()
      print
      print "[E] Quitting!"
      sys.exit(1)
