# autopwn

Specify targets and run sets of tools against them

autopwn is designed to make a pentester's life easier and more consistent
by allowing them to specify tools they would like to run against targets,
without having to type them in a shell or write a script. This tool will
probably be useful during certain exams as well..

## Running

To use autopwn, simply fork the GitHub repository and run autopwn.py

## Usage

autopwn supports a number of options, including:

```-t <target_file>          Required. The file containing the
                          targets
-a <assessment_type>      Optional. Specify assessment name
                          to run. Autopwn will not prompt to
                          run tools with this option
-d <assessment_directory> Optional. Specify assessment directory
-i                        Deprecated (and buggy). Optional. Ignore
                          missing binary conditions
-r                        Optional. Ignore tool rulesets
-s                        Optional. Run tools in screen session```

## Sample output

```# ./autopwn.py -t target
What assessment do you want to run?
0) Nmap Scan (Common TCP Ports)
1) Nmap Scan (All TCP Ports)
2) Drupal Scans (Parallel)
3) HTTrack (Mirror website)
4) Directory Brute Forcing
5) Web Application
6) Web Application (Parallel)
7) UDP Scanning
8) Windows Audit
9) SSL Audit
Choose > 8

autopwn v0.9.3 by Aidan Marlin
email: aidan [dot] marlin [at] nccgroup [dot] com

--------------------------------
The following tools will be run:
--------------------------------
/usr/bin/enum4linux -av 127.0.0.1 > 20150415_autopwn_127.0.0.1_test/20150415_130834+0100_test_enum4linux_127.0.0.1
/usr/bin/nbtscan -v 127.0.0.1 > 20150415_autopwn_127.0.0.1_test/20150415_130834+0100_test_nbtscan_127.0.0.1
[I] Global parallel option set
Run tools? [Ny] y
[+] Launching enum4linux
[+] Launching nbtscan
[-] nbtscan is done..
[-] enum4linux is done..
# tree
.
├── 20150415_autopwn_127.0.0.1_test
│   ├── 20150415_130834+0100_test_enum4linux_127.0.0.1
│   ├── 20150415_130834+0100_test_nbtscan_127.0.0.1
│   └── target
├── 20150415_autopwn_commands.log
└── target

1 directory, 6 files```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Credits

Developed by Aidan Marlin (aidan [dot] marlin [at] nccgroup [dot] com)
while working at NCC Group.

## License

autopwn - Specify targets and run sets of tools against them
Copyright (C) 2015 Aidan Marlin (aidan [dot] marlin [at] nccgroup [dot] com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
