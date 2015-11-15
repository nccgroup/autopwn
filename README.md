# autopwn

[![Build Status](https://travis-ci.org/nccgroup/autopwn.svg)](https://travis-ci.org/nccgroup/autopwn)

Specify targets and run sets of tools against them

autopwn is designed to make a pentester's life easier and more consistent
by allowing them to specify tools they would like to run against targets,
without having to type them in a shell or write a script. This tool will
probably be useful during certain exams as well..

## Installation

It is recommended that you use the docker image while exposing TCP 5000
for autopwn clients to connect to. This is because the autopwn docker
image is already setup (tools are installed and in the right place).

Only allow this package to listen on a loopback IP address. If you have
this package listen on a public IP, you're allowing arbitrary users to
execute commands as root on your server. Eventually, HTTPS and credentials
will be required, but for now, don't be a moron.

#### From Docker

TODO - pull docker image, execute while exposing TCP 5000

1. Execute ``docker pull rascal999/autopwn``
2. Run ``docker run -i -t -p 127.0.0.1:5000:5000 rascal999/autopwn /usr/sbin/autopwn``
3. Run autopwn client

#### From the Python Package Index

1. Execute ``pip install autopwn``

#### From this repository

1. Clone the Git repository
2. Change into the newly created directory
3. Execute ``pip install .``

## Usage

Running autopwn will start the web server.

## Sample output

```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
127.0.0.1 - - [15/Nov/2015 11:04:41] "GET /ping HTTP/1.1" 200 -
127.0.0.1 - - [15/Nov/2015 11:04:41] "GET /favicon.ico HTTP/1.1" 404 -
```

In order to interface with autopwn you should use autopwn-cli
(available at https://github.com/rascal999/autopwn-cli). If you're
interested in the API, you can also do stuff in the browser.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Credits

Developed by Aidan Marlin (aidan [dot] marlin [at] nccgroup [dot] com)
while working at NCC Group.

I'd like to thank the following contributors for
their work on previous autopwn versions:

- Selfegris
- 0xsauby
- [berdario](https://github.com/berdario/)
