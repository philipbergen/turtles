Turtles - The flexible lightweight pipeline
===========================================

A docker based CI tool that works in the command line as well as inside 
CI services such as Jenkins.

* Docker based for trivial environment configuration
* Simple reproducability, no more testing inside Jenkins
* Tools that are parts of everyday work not just your CI suite
* Coexists with Jenkins


What turtles is
===============

One or more docker images support the tasks in your pipeline. For instance:
sync, build, isolation test, integration test, deploy.

The image's `entrypoint <https://docs.docker.com/engine/reference/builder/#/entrypoint>`_ 
points to a script that implements the stages the image supports.

Because *you* create the image and write the script you have full control over
each part and each stage. The framework is very lightweight and will not be
in the way.

Setup
=====

First create a docker image. A sample ``Dockerfile`` for a maven project
could look something like this:

::

    FROM maven:3.3-jdk-8-alpine
    ENTRYPOINT ["/input/stage"]

Build the image and tag it usefully:

::
    docker build --tag my-maven-project .

Create the ``stage`` script in your source folder, simplified:

::

    #!/bin/bash
    set -eu
    case "$1" in
    compile)
        next=test
        ;;
    test)
        next=package
        ;;
    package)
        next=
        ;;
    *)
        echo "Stage $1; UNSUPPORTED"
        exit 1
        ;;
    esac
    cd /input
    mvn "$1"
    [ -n "$next" ] && next=", \"next_stage\":\"$next\""
    echo "{\"success\":true$next}" > /output/result.json

Finally a ``settings.json`` to get the whole thing started. Notice
the docker image name and the starting stage.

::

    {
        "image": "my-maven-project",
        "stage": "compile",
        "timeout": 120
    }

To test run:

::

    trtl settings.json

Once that completes, a result.json file is generated with ``next_stage``
set to ``test`` (for details see the ``stage`` script above). ``trtl`` 
will pick that up and run again, and again, until the ``result.json``
no longer has a ``next_stage`` in it.

Each ``result.json`` has the power to change the docker image and that
means that you have complete control over environment, entrypoint, and
execution for each stage in the pipeline.


MIT License
===========

Copyright (c) 2016 Philip Bergen


Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
