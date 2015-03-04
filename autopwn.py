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
# Work started around 201502

# TODO
# 0 - What if the target doesn't have a domain name? Temp fix: IP in both fields (Y)
# 1 - Stop using os.system()
# 2 - Get shot down by 14 year old Python devs,
#     who've been coding for "over 20 years", on how I'm
#     doing everything wrong, like not just import'ing autopwn
# 3 - TDD? :\ :/ :( :X
# 4 - Configuration for individual tools? Hmmmm.
# 4a) Allow users to easily change the command
#     they want run
# 4b) Have online repo where users can share yaml
#     configs
# 5 - What if tool requires root? Make check for this

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

#executeToolThread(1, tool[0], tool[1], tool[3])
def executeTool(thread_ID, tool_name, tool_binary_location, tool_arguments):
   os.system(tool_binary_location + " " + tool_arguments)

def showHelp():
   print "autopwn v0.2"
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

def determineAssessment(config, menu_items):
   print "What kind of assessment is this?"
   for index, item in enumerate(menu_items):
      if item != 0:
         print str(index) + ") " + str(item)

   as_type = raw_input('Choose > ')
   if as_type == '':
      print config
      print menu_items
      sys.exit(1)
   else:
      as_type_chosen = int(as_type)

   return as_type_chosen

def chooseTools(config, as_type, menu_items):
   tool_subset = []
   tool_subset_chosen = []

   # We need to isolate the tools in the selected assessment type
   # otherwise we won't get consistent tool number increments
   for index, tool in enumerate(config):
      if tool[2] == menu_items[as_type]:
         tool_subset.append(tool)

   print "Which tools would you like to run for " + menu_items[as_type] + "?"
   for index, tool in enumerate(tool_subset):
      print str(index) + ") " + tool[0]

   print "You can choose more than one like (0,1,2,3)"
   tools_chosen_input = raw_input('Choose > ')

   # Split
   tools_chosen_input = re.split(',',tools_chosen_input)
   # Convert int
   tools_chosen_input = [int(a) for a in tools_chosen_input] 

   # Determine subset of tools which were chosen
   for index, tool in enumerate(tool_subset):
      if index in tools_chosen_input:
         tool_subset_chosen.append(tool)

   return tool_subset_chosen

def checkToolExists(tool):
   #                                      Don't judge me
   if 0 != os.system("which " + tool[1] + " 2>/dev/null"):
      if 0 != os.system("ls " + tool[1] + " 2>/dev/null"):
         print tool[1] + " was not found. Quitting.."
         sys.exit(1)

def runTools(tools, target):
   thread = []
   index = 0

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
         tool[3] = tool[3].format(target_domain_name=target_domain_name, target_ip=target_ip, date=date, port_number=port_number, target_protocol=target_protocol)

         #                           Thread ID  Name     Bin loc  args
         thread.append(executeToolThread(index, tool[0], tool[1], tool[3]))
         # Start threads
         thread[index].start()
         index = index + 1

def getCurrentUser():
   if 0 != os.getuid():
      print "nmap requires uid 0 (root)"
      sys.exit(1)

def getConfig(config, menu_items):
   i = 0
   pathname = ""
   tools_dir = ""

   pathname = os.path.dirname(sys.argv[0])
   tools_dir = os.path.abspath(pathname) + "/tools/"

   for file in os.listdir(tools_dir):
      if file.endswith(".apc"):
         stream = open(tools_dir + file, 'r')
         objects = yaml.load(stream)

         k = 0
         config[i][k] = objects['name']
         k = k + 1
         config[i][k] = objects['binary_location']
         k = k + 1
         config[i][k] = objects['menu']
         k = k + 1
         config[i][k] = objects['arguments']

      i = i + 1

   for tool_menu_owner in config:
      menu_items.append(tool_menu_owner[2])

def fixMenuItems(menu_items):
   # TODO Find and remove 0
   # Remove dupes and sort
   return list(OrderedDict.fromkeys(menu_items))

def showTools(tools,target):
   for tool in tools:
      print tool[1] + " " + tool[3]

def main():
   # Variable declarations
   target = []
   tools = []
   config = [[0 for x in range(16)] for x in range(256)] 
   as_type = 0
   menu_items = []

   # Function calls
   getTargets(target)

   # Get configs
   getConfig(config,menu_items)
   # Remove dupes and sort menu
   menu_items = fixMenuItems(menu_items)

   as_type = determineAssessment(config,menu_items)
   tools = chooseTools(config,as_type,menu_items)

   # Tools to be run
   showTools(tools,target)
   run_tools = raw_input('Run tools? [Ny] ')

   if run_tools.lower() == "y":
      dry_run = 0
      runTools(tools,target)
      sys.exit(0)
   else:
      print "Alright, I quit.."
      sys.exit(1)

if __name__ == "__main__":
   main()
