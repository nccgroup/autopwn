#!/usr/bin/python2

import sys
import re
import os
import threading
import time
import yaml
from collections import OrderedDict
from time import gmtime, strftime

# Aidan Marlin @ NCC Group
# Project born 201502

class executeToolThread (threading.Thread):
   def __init__(self, thread_ID, tool_name, tool_binary_location, tool_arguments):
      threading.Thread.__init__(self)
      self.thread_ID = thread_ID
      self.tool_name = tool_name
      self.tool_binary_location = tool_binary_location
      self.tool_arguments = tool_arguments
        
   def run(self):
      print "[+] Launching " + self.tool_name
      executeTool(self.thread_ID, self.tool_name, self.tool_binary_location, self.tool_arguments)
      print "[-] " + self.tool_name + " is done.."
      logAutopwn(self.tool_name + " has finished")

#executeToolThread(1, tool[0], tool[1], tool[2])
def executeTool(thread_ID, tool_name, tool_binary_location, tool_arguments):
   os.system(tool_binary_location + " " + tool_arguments)

def showHelp():
   print "autopwn v0.3"
   print "By Aidan Marlin (email: aidan [dot] marlin [at] nccgroup [dot] com)."
   print
   print "autopwn expects one argument, the name of the file containing"
   print "targets to be pwned. Format of file should be"
   print "<ip>#<domain name>#[port-for-dirb]#[ssl-for-dirb] where"
   print "[ssl-for-dirb] would be 'http' or 'https'."
   print
   print "If target does not have a domain name, specify IP in both fields.."
   print "This might be fixed later.."
   print
   print "Examples:"
   print "195.95.131.71#nccgroup.com#443#https"
   print "216.58.208.78#google.com#80#http"
   print
   print "autopwn uses the tools/ directory located where this script is"
   print "to load tool definitions, which are yaml files. You can find"
   print "some examples in the directory already. If you think one is"
   print "missing, mention it on GitHub or email me and I might add it."
   print
   print "autopwn also uses assessments/ for assessment definitions."
   print "Before you would have to specify which menu a tool should appear in"
   print "in the tool configuration's file - this was a bad approach. Now,"
   print "the tools are decoupled and you can specify them in multiple"
   print "places via the assessments configuration files (examples of"
   print "which are provided)."
   print
   print "Have fun!"
   print "Legal purposes only.."
   print

def getTargets(target):
   fileTargets = ''

   if len(sys.argv) != 2:
      showHelp()
      sys.exit(1)
   else:
      fileTargets = sys.argv[1];

   if fileTargets == '':
      print "You need to specify a targets file"
      sys.exit(1)

   fdTargets = open(fileTargets, 'r')
   lines = fdTargets.read().split('\n')

   for x in lines:
      target.append(re.split(r'#',x))
      # print len(x) TODO DETERMINE ALL OPTIONS SPECIFIED HERE

   # Remove empty elements from list, could probably improve this
   for x in target:
      if x[0] == '':
         target.remove(x)

   return target

def determineAssessment(config_tools, menu_items):
   print "What assessment do you want to run?"
   for index, item in enumerate(menu_items):
      if item != 0:
         print str(index) + ") " + str(item)

   try:
      as_type = raw_input('Choose > ')
   except (KeyboardInterrupt, SystemExit):
      print
      print "Abandon ship!"
      sys.exit(1)
   if as_type == '':
      print config_tools
      print menu_items
      sys.exit(1)
   else:
      as_type_chosen = int(as_type)

   return as_type_chosen

def determineTools(config_tools, config_assessments, as_type, menu_items):
   tool_subset = []

   for tool in config_tools:
      if tool[0] in config_assessments[as_type][1]:
         tool_subset.append(tool)

   return tool_subset

def checkToolExists(tool):
   #                                      Don't judge me
   if 0 != os.system("which " + tool[1] + " >/dev/null 2>&1"):
      if 0 != os.system("ls " + tool[1] + " >/dev/null 2>&1"):
         print tool[1] + " was not found. Quitting.."
         sys.exit(1)

def logAutopwn(log_string):
   date =  strftime("%Y%m%d")
   date_time =  strftime("%Y%m%d %H:%M:%S")
   log_file = open(date + "_autopwn_commands.log","a")
   log_file.write("# " + date_time + "\n")
   log_file.write(log_string + "\n")
   log_file.close()

def runTools(tools, config_assessments, target):
   thread = []
   index = 0
   tool_string = ""

   # Check all the tools exist
   for tool in tools:
      checkToolExists(tool)

   for host in target:
      for tool in tools:
         # Variable declaration for placeholder replacements
         date =  strftime("%Y%m%d_%H%M%S")
         target_ip = host[0]
         target_domain_name = host[1]
         port_number = host[2]
         target_protocol = host[3]

         # Let's do it
         tool[2] = tool[2].format(target_domain_name=target_domain_name, target_ip=target_ip, date=date, port_number=port_number, target_protocol=target_protocol)
         # Log tool run
         tool_string = tool[1] + " " + tool[2]
         logAutopwn(tool_string)

         time.sleep (50.0 / 1000.0);
         #                           Thread ID  Name     Bin loc  args
         thread.append(executeToolThread(index, tool[0], tool[1], tool[2]))
         # If main process dies, everything else will as well
         thread[index].daemon = True
         # Start threads
         thread[index].start()

         # Parallel or singular?
         if config_assessments[3] != 1:
            thread[index].join()

         index = index + 1

   if config_assessments[3] == 1:
      for tid in thread:
         tid.join()

def getCurrentUser():
   if 0 != os.getuid():
      print "nmap requires uid 0 (root)"
      sys.exit(1)

def getConfig(config_tools,config_assessments,menu_items):
   i = 0
   pathname = ""
   tools_dir = ""
   assessment_dir = ""

   pathname = os.path.dirname(sys.argv[0])
   tools_dir = os.path.abspath(pathname) + "/tools/"
   assessments_dir = os.path.abspath(pathname) + "/assessments/"

   # Pull tool configs
   for file in os.listdir(tools_dir):
      if file.endswith(".apc"):
         stream = open(tools_dir + file, 'r')
         objects = yaml.load(stream)

         k = 0
         config_tools[i][k] = objects['name']
         k = k + 1
         config_tools[i][k] = objects['binary_location']
         k = k + 1
         config_tools[i][k] = objects['arguments']

      i = i + 1

   #Reset
   i = 0
   # Pull assessment configs
   for file in os.listdir(assessments_dir):
      if file.endswith(".apc"):
         stream = open(assessments_dir + file, 'r')
         objects = yaml.load(stream)

         k = 0
         config_assessments[i][k] = objects['name']
         k = k + 1
         config_assessments[i][k] = objects['tools']
         k = k + 1
         config_assessments[i][k] = objects['menu_name']
         k = k + 1
         config_assessments[i][k] = objects['parallel']

      i = i + 1

   for config_assessment_menu_item in config_assessments:
      menu_items.append(config_assessment_menu_item[2])

def fixMenuItems(menu_items):
   # TODO Find and remove 0
   # Remove dupes and sort
   return list(OrderedDict.fromkeys(menu_items))

def showTools(tools,target):
   for tool in tools:
      print tool[1] + " " + tool[2]

def main():
   # Variable declarations
   target = []
   tools = []
   config_tools = [[0 for x in range(16)] for x in range(256)] 
   config_assessments = [[0 for x in range(16)] for x in range(256)] 
   as_type = 0
   menu_items = []

   # Function calls
   getTargets(target)

   # Get config_toolss
   getConfig(config_tools,config_assessments,menu_items)
   # Remove dupes and sort menu
   menu_items = fixMenuItems(menu_items)

   as_type = determineAssessment(config_tools,menu_items)
   tools = determineTools(config_tools,config_assessments,as_type,menu_items)

   # Tools to be run
   showTools(tools,target)
   run_tools = raw_input('Run tools? [Ny] ')

   if run_tools.lower() == "y":
      dry_run = 0
      runTools(tools,config_assessments[as_type],target)
      sys.exit(0)
   else:
      print "Alright, I quit.."
      sys.exit(1)

if __name__ == "__main__":
   main()
