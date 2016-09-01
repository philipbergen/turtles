def stage(settings):
    """ Creates a mvn image and pipeline.
    """
    import os
    import sys
    from subprocess import call
    from turtles import interpolate_file, docker_inspect, ImageMissing
    if not os.path.exists(os.path.expanduser("~/.m2")):
        sys.exit("Maven configuration in ~/.m2 is required")
    image = "turtle-mvn"
    try:
        docker_inspect(image)
    except ImageMissing:
        here = os.getcwd()
        with open(os.path.join(here, "log.txt"), 'a') as fout:
            print("Preparing for pipeline, logging to", fout.name)
            try:
                os.chdir(os.path.dirname(settings['-p']))
                interpolate_file("Dockerfile.in", "Dockerfile", log=fout.write)
                if call(["docker", "build", "-t", image, "."], stdout=fout):
                    sys.exit("Docker build failed.")
            finally:
                os.chdir(here)
    if not os.path.exists("target"):
        os.mkdir("target")
    return {
        "-s": "validate",
        "-d": image,
        "-v": ["~/.m2:/home/turtle/.m2:rw", "target:/workspace/target:rw"],
    }
