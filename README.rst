Turtles - The flexible lightweight pipeline
===========================================

A docker based CI tool that works in the command line as well as inside CI services such as Jenkins.

* Docker based for trivial environment configuration
* Simple reproducability, no more testing inside Jenkins
* Tools that are parts of everyday work not just your CI suite
* Coexists with Jenkins


What turtles is
===============

One or more docker images support the tasks in your pipeline. For instance: sync, build, isolation
test, integration test, deploy.

The image's `entrypoint <https://docs.docker.com/engine/reference/builder/#/entrypoint>`_ points to
a script that implements the stages the image supports.

Because *you* create the image and write the script you have full control over each part and each
stage. The framework is very lightweight and will not be in the way.

Setup
=====

First create a docker image. A sample ``Dockerfile`` for a maven project could look something like
this:

::

    FROM maven:3.3-jdk-8-alpine
    ENTRYPOINT ["/input/stage"]

Note: This ignores the problems with users and access rights in docker. See code examples in
``pipelines`` for complete examples.

Build the image and tag it usefully:

::

    docker build --tag my-maven-project .


Create the ``stage`` script in your source folder, simplified:

::

    #!/bin/bash
    set -eu
    cd /input
    # Do the actual work of the stage
    mvn "$1"
    # Determine what the next stage should be
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
    [ -z "$next" ] && exit 0
    # Generate the result.json
    echo "{\"-s\":\"$next\"}" > /output/result.json


Note: The return code of the stage is *really* important. If it's zero it means the stage completed
successfully and that everything is ready to move to the next stage. If there test failures should
abort the pipeline, then test failures must be detected by the stage script and it should exit
non-zero.

To test run:

::

    trtl -d my-maven-project -i . -s compile

Once that completes, a result.json file is generated with next stage (``-s``) set to ``test`` (for
details see the ``stage`` script above). ``trtl`` will pick that up and run again, and again, until
the ``result.json`` no longer has a ``-s`` in it.

Each ``result.json`` has the power to change the docker image and that means that you have complete
control over environment, entrypoint, and execution for each stage in the pipeline.

result.json
-----------

The file is just a dictionary of the CLI parameters (see ``trtl -h`` for details):

::

    {
        "-d": "my-maven-project",
        "-s": "compile",
        "-t": 120
    }

Any of the parameters can be overridden in each stage's output ``result.json``. This allows the
pipeline to switch the image before the next stage. It is also a required mechanism for specifying
the next stage.

To specify parameters that can be set multiple times, such as ``-v``, use an array:

::

    {
        "-v": ["target:/input/target:rw", "~/.m2/settings.xml:/home/turtle/.m2/settings.xml"]
    }


Pipelines
---------
To avoid specifying all the parameters for launching a pipeline, write a pipeline script:

::

    def stage(settings):
        return {
            "-s": "build",
            "-d": "my-demo-image",
        }

And invoke it with ``trtl -i. -p pipeline.py``.

More advanced pipelines may create docker images and install keys and certificates before letting
the stage begin. See ``pipelines/mvn/pipeline.py`` for example.


MIT License
===========

Copyright (c) 2016 Philip Bergen

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
