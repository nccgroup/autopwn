#!/usr/bin/env python3

import cmd
import json
import os
import random
import sys
import re
import readline
import requests

# Aidan Marlin @ NCC Group
# Project born 201502 (oh god, hardcoded tools)
# Project reborn 201505 (eh, logic and views)
# Project re-reborn 201511 (JSON server and clients, yay!)

class Configuration:
    def __init__(self):
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
        self.search(glob, "/assessments", search_string)
        self.search(glob, "/tools", search_string)

    def search(self, glob, url, search_string):
        r = requests.get(glob.config['server'] + url + '?search=' + search_string)
        # TODO Finish JSON
        json_response = json.loads(r.content.decode('utf8'))
        print(json_response)
        print('{0:30} {1}'.format(item_type_string, "Description"))
        print("-"*64)
        print()

class Ping:
    def __init__(self, glob):
        if re.match("^http://127.0.0.1[:/].*$", glob.config['server']) == None:
            print("[WARNING] Um, you're not using this over the net are you? That's a very stupid idea. autopwn doesn't use authentication or encryption yet. If you're on IPv6 I'm sorry I couldn't be bothered to regex kthxbai\n")
        try:
            r = requests.get(glob.config['server'] + '/ping')
            json_response = json.loads(r.content.decode('utf8'))
            if json_response['message'] == 'pong':
                glob.config['connected'] = True
        except requests.exceptions.RequestException as e:
            pass

class Shell(cmd.Cmd):
    glob = Configuration()
    # Test connectivity
    Ping(glob)
    if glob.config['connected'] == False:
        print("Not connected to an autopwn node!\n")
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
    def do_search(self, arg):
        Search(self.glob, arg)
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
