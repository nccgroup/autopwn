#!/usr/bin/env python3

import cmd
import json
import os
import random
import sys
import re
import readline
import requests

from collections import OrderedDict, defaultdict

# Aidan Marlin @ NCC Group
# Project born 201502 (oh god, hardcoded tools)
# Project reborn 201505 (eh, logic and views)
# Project re-reborn 201511 (JSON server and clients, yay!)

# TODO Default options need to be known/set
#      Option required local knowledge should be improved?
#      Run command
#      Assessments

class Configuration:
    def __init__(self):
        self.state = {}
        self.state['assessments'] = {}
        self.state['tools'] = {}
        self.state['options'] = {}
        self.state['jobs'] = {}
        self.state['updated'] = False
        self.state['selected_resource'] = {}
        self.state['selected_resource']['option'] = defaultdict(lambda : '')
        self.state['selected_resource']['name'] = None
        self.state['resource_options'] = None
        self.state['job'] = None

        self.config = {}
        self.config['server'] = 'http://127.0.0.1:5000'
        self.config['connected'] = False

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

class Search:
    def __init__(self, glob, search_string):
        self.search(glob, "Assessment", "/assessments", "assessments", search_string)
        self.search(glob, "Tool", "/tools", "tools", search_string)

    def search(self, glob, result_text, url, arg, search_string):
        # Submit search (let's completely ignore the local cache of results here)
        try:
            data = requests.get(glob.config['server'] + url + '?search=' + search_string)
            if data.status_code == 200:
                json_response = json.loads(data.content.decode('utf8'))
                print('{0:30} {1}'.format(result_text, "Description"))
                print("-"*64)
                for row in json_response['result']:
                    print('{0:30} {1}'.format(row['name'], row['description']))
        except requests.exceptions.RequestException as e:
            print("Fail! Service still up?")
        print()

class Use:
    def __init__(self, glob, arg):
        # Set selected resource and selected resource id
        try:
            asset = ((item for item in glob.state['tools'] if item["name"] == arg).__next__())
            glob.state['selected_resource']['name'] = arg
            for tool in glob.state['tools']:
                if tool['name'] == glob.state['selected_resource']['name']:
                    glob.state['selected_resource']['id'] = tool['id']
        except:
            # Reset
            glob.state['selected_resource']['name'] = None
            glob.state['job'] = None
            print("Not a valid tool or assessment")
            return
        # Fetch options for tool id
        try:
            data = requests.get(glob.config['server'] + '/options/' + str(glob.state['selected_resource']['id']))
            if data.status_code == 200:
                glob.state['resource_options'] = json.loads(data.content.decode('utf8'))
        except requests.exceptions.RequestException as e:
            print("Fail! Service still up?")

class Ping:
    def __init__(self, glob):
        if re.match("^http://127.0.0.1[:/].*$", glob.config['server']) == None:
            print("[WARNING] Um, you're not using this over the net are you? That's a very stupid idea. autopwn doesn't use authentication or encryption yet. If you're on IPv6 I'm sorry I couldn't be bothered to regex kthxbai\n")
        try:
            r = requests.get(glob.config['server'] + '/ping')
            json_response = json.loads(r.content.decode('utf8'))
            if json_response['message'] == 'pong':
                glob.config['connected'] = True
            print("Connected!")
        except requests.exceptions.RequestException as e:
            print("Not connected!")
            pass

class Update:
    def __init__(self, glob):
        self.fetch(glob, "/tools", "tools")
        self.fetch(glob, "/assessments", "assessments")
        self.fetch(glob, "/jobs", "jobs")
        self.fetch(glob, "/options", "options")

    def fetch(self, glob, url, arg):
        # Tools, assessments and jobs
        print("Updating " + arg + "...",end='')
        try:
            data = requests.get(glob.config['server'] + url)
            if data.status_code == 200:
                glob.state[arg] = json.loads(data.content.decode('utf8'))['result']
                glob.state['updated'] = True
                print("Done!")
            else:
                print("Fail!")
        except requests.exceptions.RequestException as e:
            print("Fail! Server might be down!")
            return

class Show:
    def __init__(self, glob, arg):
        if arg == 'options':
            self.show_options(glob)
        elif arg == 'jobs':
            self.show_jobs(glob)
        elif arg == 'config':
            self.show_config(glob)
        else:
            self.show_help(glob)

    def show_options(self, glob):
        if glob.state['selected_resource']['name'] != None:
            print(glob.state['selected_resource']['name'])
            resource = ((item for item in glob.state['tools'] if item["name"] == glob.state['selected_resource']['name']).__next__())
            # Determine what options are needed for tool(s)
            print("Options for tool/assessment.")
            print()
            print("        {0:16} {1:16} {2:32} {3}".format("Option", "Value", "Example Values", "Required"))
            print("        "+"-"*96)
            for tool_option in glob.state['resource_options']['result']:
                for option in glob.state['options']:
                    option_required = False
                    if option['id'] == tool_option['option']:
                        if tool_option['required'] == 1:
                            option_required = True
                        print("        {0:16} {1:16} {2:32} {3}".format(option['option_name'], \
                                glob.state['selected_resource']['option'][option['option_name']], \
                                option['option_example'], option_required))
            print()
        else:
            print("No tool or assessment selected")

    def show_jobs(self, glob):
        print("1. Swap bits")
        print("2. Periodically switch on Caps Lock")
        print("3. Send scan results home")
        print("4. ...")
        print("5. Fragment drive")
        print("6. Emulate single blown pixel")
        print("7. Recommend Windows to the user")

class Set:
    def __init__(self, glob, arg):
        if len(arg.split(' ')) != 2:
            print("Incorrect number of arguments")
            return
        option_name = arg.split(' ')[0]
        option_value = arg.split(' ')[1]
        glob.state['selected_resource']['option'][option_name] = option_value

class Save:
    def __init__(self, glob):
        if glob.state['selected_resource']['name'] != None:
            # TODO Add tool options
            post_data = {}
            post_data['tool'] = glob.state['selected_resource']['id']
            post_data['target'] = glob.state['selected_resource']['option']['target']
            post_data['target_name'] = glob.state['selected_resource']['option']['target_name']
            post_data['protocol'] = glob.state['selected_resource']['option']['protocol']
            post_data['port_number'] = glob.state['selected_resource']['option']['port_number']
            post_data['user'] = glob.state['selected_resource']['option']['user']
            post_data['password'] = glob.state['selected_resource']['option']['password']
            post_data['user_file'] = glob.state['selected_resource']['option']['user_file']
            post_data['password_file'] = glob.state['selected_resource']['option']['password_file']
            data = requests.post(glob.config['server'] + '/jobs', data = post_data)
            glob.state['job'] = json.loads(data.content.decode('utf8'))
            print("Saved.")
        else:
            print("You need to 'use' a tool first")

class Run:
    def __init__(self, glob):
        if glob.state['job'] != None:
            data = requests.post(glob.config['server'] + '/jobs/execute', \
                   data = glob.state['job'])
            if data.status_code == 201:
                print("Command executed")
            else:
                print("Error indicated by server")
        else:
            print("Save a tool with options first")

class Shell(cmd.Cmd):
    glob = Configuration()

    # Test connectivity
    Ping(glob)

    # Fetch tools and assesments
    Update(glob)

    prompt = 'autopwn > '

    def cmdloop(self, intro=None):
        try:
            cmd.Cmd.cmdloop(self, intro)
        except KeyboardInterrupt as e:
            print()
            print("Type 'quit' to exit autopwn shell")
            self.cmdloop()

    def emptyline(self):
        'Update assets from service'
        Update(self.glob)
        pass

    def do_shell(self, arg):
        'Execute shell commands'
        os.system(arg)
    def do_search(self, arg):
        'Search for a tool or assessment'
        Search(self.glob, arg)
    def do_use(self, arg):
        'Select a tool or assessment to use'
        Use(self.glob, arg)
        # Set autopwn prompt if tool found (or if not)
        if self.glob.state['selected_resource']['name'] != None:
            if (sys.stdout.isatty()) == True:
                arg = '\x1b[%sm%s\x1b[0m' % \
                    (';'.join(['31']), arg)
            self.prompt = 'autopwn (' + arg + ') > '
        else:
            self.prompt = 'autopwn > '
    def do_set(self, arg):
        'Set resource options'
        Set(self.glob, arg)
    def do_show(self, arg):
        'Show options'
        Show(self.glob, arg)
    def do_save(self, arg):
        'Create new job on service using options'
        Save(self.glob)

    def complete_set(self, text, line, begin, end):
        completions = ''
        if not text:
            completions = [ option['option_name']
                            for option in self.glob.state['options']
                          ]
        else:
            # TODO Fix this (not all options should be selectable)
            completions = [ option['option_name']
                            for option in self.glob.state['options']
                                if line.split(' ')[1] in option['option_name']
                          ]
        return completions

    def complete_use(self, text, line, begin, end):
        completions = ''
        if not text:
            # Add assessments
            completions = [ assessment['name']
                            for assessment in self.glob.state['assessments']
                          ]
            # Add tools
            completions = completions + [ tool['name']
                            for tool in self.glob.state['tools']
                          ]
        else:
            # Add assessments which match
            completions = [ assessment['name']
                            for assessment in self.glob.state['assessments']
                                if line.split(' ')[1] in assessment['name']
                          ]

            # Add tools which match
            completions = completions + [ tool['name']
                            for tool in self.glob.state['tools']
                                if line.split(' ')[1] in tool['name']
                          ]
        return completions

    def do_reload(self, arg):
        'Update assets from service'
        Update(self.glob)
    def do_bye(self, arg):
        'Quit autopwn'
        self.terminate()
    def do_ping(self, arg):
        'Test connectivity'
        Ping(self.glob)
    def do_run(self, arg):
        'Execute job list on server'
        Run(self.glob)
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
        quote.append("Fuck it, we'll do it in production.")
        quote.append("Programmers are tools for converting caffeine into code.")
        quote.append("Those who can't write programs, write help files.")
        quote.append("Should array indices start at 0 or 1? My compromise of 0.5 was rejected without, I thought, proper consideration.")
        quote.append("Fifty years of programming language research, and we end up with C++?")
        quote.append("Software is like sex: It’s better when it’s free.")
        quote.append("If debugging is the process of removing bugs, then programming must be the process of putting them in.")
        quote.append("Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live.")
        quote.append("C programmers never die. They are just cast into void.")
        quote.append("19 Jan 2038 at 3:14:07 AM")
        quote.append("If Python is executable pseudocode, then perl is executable line noise.")
        quote.append("The only difference between a bug and a feature is the documentation.")
        print(random.choice(quote))
        sys.exit(0)

def _main(arglist):
    # Load configuration (Only 127.0.0.1 should be used right now)
    #pathname = os.path.abspath(config.find_path(__file__) or config.find_path(sys.argv[0]))
    #autopwn_config_file = os.path.abspath(pathname) + "/autopwn.apc"
    #config_objects = open(autopwn_config_file, 'r')
    #config = yaml.load(config_objects)

    # Process command line arguments
    if len(sys.argv) > 1:
        Arguments(sys.argv[1:]).parser
    else:
        # Drop user to shell
        Shell().cmdloop("autopwn 1.0.0 shell. Type help or ? to list commands.\n")

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
