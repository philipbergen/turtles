def stage(settings):
    """ Creates a mvn image and pipeline.
    """
    import os
    import sys
    from subprocess import call, Popen, PIPE
    if not os.path.exists(os.path.expanduser("~/.m2")):
        sys.exit("Maven configuration in ~/.m2 is required")
    image = "turtle-mvn"
    pope = Popen(["docker", "images", "-q", image], stdout=PIPE)
    so, _ = pope.communicate()
    if not so.strip():
        here = os.getcwd()
        with open(os.path.join(here, "log.txt"), 'a') as fout:
            print("Preparing for pipeline, logging to", fout.name)
            try:
                os.chdir(os.path.dirname(settings['-p']))
                with open("Dockerfile", 'w') as df:
                    uidgid = "%d:%d" % (os.getuid(), os.getgid())
                    df.write(open("Dockerfile.in").read().replace("50657:50657", uidgid))
                res = call(["docker", "build", "-t", image, "."], stdout=fout)
                if res:
                    sys.exit("Docker build failed.")
            finally:
                os.chdir(here)
    if not os.path.exists("target"):
        os.mkdir("target")
    return {
        "-s": "compile",
        "-d": image,
        "-v": ["~/.m2:/home/turtle/.m2:rw", "target:/input/target:rw"],
    }
