#!/usr/bin/python2

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
from time import gmtime, strftime

# Aidan Marlin @ NCC Group
# Project born 201502

class Log:
   def __init__(self, log_type, log_string):
      if log_type == 'tool_string':
         date =  strftime("%Y%m%d")
         date_time =  strftime("%Y%m%d %H:%M:%S")
         log_file = open(date + "_autopwn_commands.log","a")
         log_file.write("# " + date_time + "\n")
         log_file.write(log_string + "\n")
         log_file.close()

class Run:
   thread = []
   index = 0

   def __init__(self, tools_subset, assessment_type, target_list, dry_run):
      for host in target_list:
         for tool in tools_subset:
            # Variable declaration for placeholder replacements
            date =  strftime("%Y%m%d_%H%M%S")
            target_ip = host[0]
            target_domain_name = host[1]
            port_number = host[2]
            target_protocol = host[3]

            # Let's do it
            tool_arguments_instance = tool['arguments'].format(target_domain_name=target_domain_name, target_ip=target_ip, date=date, port_number=port_number, target_protocol=target_protocol)

            tool_string = tool['binary_location'] + " " + tool_arguments_instance

            # Run for real
            if dry_run != 1:
               log = Log('tool_string',tool_string)

               time.sleep (50.0 / 1000.0);
               #                                  Thread ID  Name     Bin loc  args
               self.thread.append(RunThreads(self.index, tool['name'], tool['binary_location'], tool_arguments_instance))
               # If main process dies, everything else will as well
               self.thread[self.index].daemon = True
               # Start threads
               self.thread[self.index].start()

               # Parallel or singular?
               if assessment_type['parallel'] != 1:
                  while threading.activeCount()>1:
                     pass

               self.index = self.index + 1
            else:
               print tool_string

      if dry_run != 1:
         if assessment_type['parallel'] == 1:
            while threading.activeCount()>1:
               pass
            #for tid in self.thread:
            #   tid.join(1)

class RunThreads (threading.Thread):
   def __init__(self, thread_ID, tool_name, tool_binary_location, tool_arguments):
      threading.Thread.__init__(self)
      self.kill_received = False
      self.thread_ID = thread_ID
      self.tool_name = tool_name
      self.tool_binary_location = tool_binary_location
      self.tool_arguments = tool_arguments

   #executeToolThread(1, tool[0], tool[1], tool[2])
   def executeTool(self, thread_ID, tool_name, tool_binary_location, tool_arguments):
      #os.system(tool_binary_location + " " + tool_arguments)
      # Using shell = True can be a security risk,
      # and this will be fixed at some point. For now
      # (and always), check any tools provided by
      # community members
      subprocess.call(tool_binary_location + " " + tool_arguments,shell = True)
      #print tool_binary_location + " " + tool_arguments

   def run(self):
      print "[+] Launching " + self.tool_name
      self.executeTool(self.thread_ID, self.tool_name, self.tool_binary_location, self.tool_arguments)
      print "[-] " + self.tool_name + " is done.."
      log = Log('tool_string',"# " + self.tool_name + " has finished")

class Tools:
   tool_subset = []

   def __init__(self, tools, assessment):
      for tool in tools:
         if tool['name'] in assessment['tools']:
            self.tool_subset.append(tool)

class Menus:
   # Not 0 because this is a valid selection..
   item_selected = ''

   def __init__(self, menu_items, menu_name):
      if menu_name == 'assessment':
         self.displayAssessmentMenu(menu_items)

   def displayAssessmentMenu(self, menu_items):
      valid_option_index = 0

      print "What assessment do you want to run?"
      for index, item in enumerate(menu_items):
         if item != '':
            print str(index) + ") " + str(item)
            valid_option_index = valid_option_index + 1

      try:
         self.item_selected = raw_input('Choose > ')
      except (KeyboardInterrupt, SystemExit):
         print
         print "[E] Abandon ship!"
         sys.exit(1)
      if self.item_selected == '': # TODO - Review
         print "[E] No choice was made, quitting.."
         sys.exit(1)
      else:
         print self.item_selected
         if int(self.item_selected) >= 0 and int(self.item_selected) < valid_option_index:
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
         argument_assessment_found = 0
         # Command line
         for assessment_type in config.assessments_config:
            if assessment_type['name'] == argument_assessment:
               self.assessment_type = assessment_type
               argument_assessment_found = 1
         if argument_assessment_found != 1:
            print "[E] Assessment name not found. Is it spelt correctly?"
            sys.exit(1)
      else:
         # Display menu
         config.dry_run = 1
         menu = Menus(config.menu_items,'assessment')
         self.assessment_type = config.assessments_config[menu.item_selected]

class Print:
   def __init__(self, display_text, file_descriptor):
      if display_text == 'help':
         self.displayHelp(file_descriptor)

   def displayHelp(self, file_descriptor):
      # Not doing anything with file_descriptor yet
      print "autopwn v0.5"
      print "By Aidan Marlin (email: aidan [dot] marlin [at] nccgroup [dot] com)."
      print
      print "-t <target_file>       Required. The file containing the targets"
      print "-a <assessment_type>   Optional. Specify assessment name to run."
      print "                       Autopwn will not prompt to run tools with"
      print "                       this option"
      print
      print "Format of the target file should be:"
      print "<ip>#[domain name]#<port>#<ssl> where"
      print "<ssl> would be 'http' or 'https'."
      print
      print "Examples:"
      print "195.95.131.71#nccgroup.com#443#https"
      print "216.58.208.78#80#http"
      print
      print "autopwn uses the tools/ directory located where this script is"
      print "to load tool definitions, which are yaml files. You can find"
      print "some examples in the directory already. If you think one is"
      print "missing, mention it on GitHub or email me and I might add it."
      print
      print "autopwn also uses assessments/ for assessment definitions."
      print "Instead of selecting which tools you would like to run, you"
      print "specify which assessment you would like to run. Assessment"
      print "configuration files contain lists of tools which will be run"
      print "as a result."
      print
      print "Have fun!"
      print "Legal purposes only.."
      print
      sys.exit(1)

class Arguments:
   argument = {'assessment':'', 'target_file':''}

   def __init__(self, arguments):
      # If no arguments specified, dump autopwn help / description
      if len(sys.argv) == 1:
         help = Print('help', 'stdout')

      try:
         opts, args = getopt.getopt(arguments,"a:t:",["assessment=","target="])
      except getopt.GetoptError:
         print "./autopwn.py [-a <assessment_type>] -t <target_file>"
         sys.exit(2)

      for opt, arg in opts:
         if opt in ("-a", "--assessment"):
            # Assessment type
            self.argument['assessment'] = arg
         if opt in ("-t", "--target"):
            # Target file
            self.argument['target_file'] = arg

      if self.argument['target_file'] == '':
         print "[E] Target file not specified"
         sys.exit(1)

# Configuration class loads all information from .apc files and target file
class Configuration:
   # Class vars
   tools_config = [{'name':'','binary_location':'','arguments':''} for x in range(256)]
   assessments_config = [{'name':'','tools':'','menu_name':'','parallel':''} for x in range(128)]
   menu_items = []
   target_list = []
   dry_run = 0

   # This method will pull configuration and target file information
   # Will probably split into separate methods at some point
   def __init__(self, target_file):
      i = 0

      pathname = os.path.dirname(sys.argv[0])
      tools_directory = os.path.abspath(pathname) + "/tools/"
      assessments_directory = os.path.abspath(pathname) + "/assessments/"

      # Pull tool configs
      for file in os.listdir(tools_directory):
         if file.endswith(".apc"):
            stream = open(tools_directory + file, 'r')
            objects = yaml.load(stream)

            self.tools_config[i]['name'] = objects['name']
            self.tools_config[i]['binary_location'] = objects['binary_location']
            self.tools_config[i]['arguments'] = objects['arguments']

         i = i + 1

      # Pull assessment configs
      i = 0
      for file in os.listdir(assessments_directory):
         if file.endswith(".apc"):
            stream = open(assessments_directory + file, 'r')
            objects = yaml.load(stream)

            self.assessments_config[i]['name'] = objects['name']
            self.assessments_config[i]['tools'] = objects['tools']
            self.assessments_config[i]['menu_name'] = objects['menu_name']
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
         lines = fd_targets.read().split('\n')
         fd_targets.close()
      except IOError as e:
         print "[E] Error processing target file: {1}".format(e.errno, e.strerror)
         sys.exit(1)

      for x in lines:
         tmp = x.split("#")
         if len(tmp) == 3:
            tmp.insert(1, tmp[0])
            self.target_list.append(tmp)
         else:
            self.target_list.append(tmp)

      # Remove empty elements from list, could probably improve this
      for x in self.target_list:
         if x[0] == '':
            self.target_list.remove(x)

class Prompt:
   def __init__(self, prompt, config, tools, assessment):
      if prompt == 'run_tools':
         self.runTools(config,tools,assessment)

   def runTools(self, config, tools, assessment):
      run_tools = raw_input('Run tools? [Ny] ')

      if run_tools.lower() == "y":
         config.dry_run = 0
         Run(tools.tool_subset,assessment.assessment_type,config.target_list,config.dry_run)
         sys.exit(0)
      else:
         print "[E] Alright, I quit.."
         sys.exit(1)

def main():
   # Process arguments
   args = Arguments(sys.argv[1:])
   # Pull config
   config = Configuration(args.argument['target_file'])
   # Determine assessment
   assessment = Assessments(config,args.argument['assessment'])
   # Process tools
   tools = Tools(config.tools_config,assessment.assessment_type)
   # Run tools
   execute = Run(tools.tool_subset,assessment.assessment_type,config.target_list,config.dry_run)
   if config.dry_run == 1:
      prompt = Prompt('run_tools',config,tools,assessment)

if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      print
      print "[E] Quitting!"
      sys.exit(1)
