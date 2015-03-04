# autopwn
Specify targets and run sets of tools against them

By Aidan Marlin (email: aidan [dot] marlin [at] nccgroup [dot] com).

autopwn expects one argument, the name of the file containing
targets to be pwned. Format of file should be
<ip>#<domain name>#[port-for-dirb]#[ssl-for-dirb] where
[ssl-for-dirb] would be 'http' or 'https'.

If target does not have a domain name, specify IP in both fields..
This might be fixed later..

Examples:
195.95.131.71#nccgroup.com#443#https
216.58.208.78#google.com#80#http

autopwn uses the tools/ directory located where this script is
to load tool definitions, which are yaml files. You can find
some examples in the directory already. If you think one is
missing, mention it on GitHub or email me and I might add it.

Have fun!
Legal purposes only..
