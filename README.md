# autopwn

[![Build Status](https://travis-ci.org/nccgroup/autopwn.svg)](https://travis-ci.org/nccgroup/autopwn)

Specify targets and run sets of tools against them

autopwn is designed to make a pentester's life easier and more consistent
by allowing them to specify tools they would like to run against targets,
without having to type them in a shell or write a script. This tool will
probably be useful during certain exams as well..

## Installation

#### From the Python Package Index

1. Execute ``pip install autopwn``

#### From this repository

1. Clone the Git repository
2. Change into the newly created directory
3. Execute ``pip install .``

### From Docker (work in progress)

1. Execute ``docker pull rascal999/autopwn``
2. Run ``docker run -i -t rascal999/autopwn /bin/bash``
3. In the container run ``autopwn``

## Usage

autopwn supports a number of options, including:

```
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        The file containing the targets
  -m MODULE, --module MODULE
                        Specify module (tool or assessment) to run. Autopwn
                        will not drop to shell if this option is specified
  -d ASSESSMENT_DIRECTORY, --assessment_directory ASSESSMENT_DIRECTORY
                        Specify assessment directory
  -s, --with_screen     Run tools in screen session
  -p, --parallel        Run tools in parallel regardless of assessment or
                        global parallel option
```

## Sample output

```
autopwn v0.17.0 shell. Type help or ? to list commands.

autopwn > search
Assessment                     Description
----------------------------------------------------------------

assessment/nmap-common-ports   Run nmap scanner against common TCP ports of target.
assessment/nmap                Run nmap scanner against all TCP ports on target.
assessment/drupal              Run CMSmap Drupal scans against target.
assessment/dir-brute           Brute force web application files.
assessment/webapp              Run web application specific tools against target
assessment/udp-scan            Run UDP scans against target.
assessment/windows-audit       Run Windows auditing tools against target
assessment/ssl-audit           Run SSL auditing tools against target.

Tool                           Description
----------------------------------------------------------------

tool/nmap-common-ports         Nmap ("Network Mapper") is a free and open source (license) utility for network discovery and security auditing.
tool/dirb                      URL Bruteforcer - DIRB is a Web Content Scanner. It looks for hidden Web Objects.
tool/nmap                      Nmap ("Network Mapper") is a free and open source (license) utility for network discovery and security auditing.
tool/udp-proto-scanner         udp-proto-scanner is a perl script which discovers UDP services by sending triggers to a list of hosts.
tool/enum4linux                Enum4linux is a tool for enumerating information from Windows and Samba systems.
tool/testsslserver             TestSSLServer is a simple command-line tool which contacts a SSL/TLS server (name and port are given as parameters) and obtains some information from it.
tool/httrack                   HTTrack is a free (GPL, libre/free software) and easy-to-use offline browser utility. It allows you to download a World Wide Web site from the Internet
tool/sslscan                   sslscan tests SSL/TLS enabled services to discover supported cipher suites.
tool/cmsmap-drupal             CMSmap - Drupal instance.
tool/nbtscan                   NBTScan is a program for scanning IP networks for NetBIOS name information (similar to what the Windows nbtstat tool provides against single hosts).
tool/sslyze                    Fast and full-featured SSL scanner.
tool/arachni                   Arachni is a Free/Open-Source Web Application Security Scanner aimed towards helping users evaluate the security of web applications.
tool/nikto                     Nikto is an Open Source (GPL) web server scanner which performs comprehensive tests against web servers for multiple items.
tool/skipfish                  Skipfish is an active web application security reconnaissance tool.

autopwn > use assessment/webapp
Name: webapp
Long name: Web Application
Description: Run web application specific tools against target

The follwing tools are used in this assessment:
- dirb
- httrack
- cmsmap-drupal
- arachni
- nikto
- skipfish

The following options are required for this assessment:
    - target_name
    - target
    - port_number
    - protocol

autopwn (assessment/webapp) > show options
Options for tool/assessment.

        Option                         Value
        ------------------------------------------------
        target_name                   
        target                        
        port_number                   
        protocol                      

autopwn (assessment/webapp) > set target_name test
target_name = test
autopwn (assessment/webapp) > set target 127.0.0.1
target = 127.0.0.1
autopwn (assessment/webapp) > set port_number 80
port_number = 80
autopwn (assessment/webapp) > set protocol http
protocol = http
autopwn (assessment/webapp) > save
There are 6 jobs in the queue
autopwn (assessment/webapp) > run
[+] Launching dirb
[-] dirb is done..
[+] Launching httrack
[-] httrack is done..
[+] Launching cmsmap-drupal
[-] cmsmap-drupal is done..
[+] Launching arachni
[-] arachni is done..
[+] Launching nikto
[-] nikto is done..
[+] Launching skipfish
[-] skipfish is done..
autopwn (assessment/webapp) > 
```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Credits

Developed by Aidan Marlin (aidan [dot] marlin [at] nccgroup [dot] com)
while working at NCC Group. I'd like to thank the following contributors for
their pull requests:

- Selfegris
- 0xsauby
- [berdario](https://github.com/berdario/)
