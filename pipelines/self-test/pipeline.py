def stage(settings):
    """ Creates a self-test image and pipeline.
    """
    import os
    import sys
    from subprocess import call
    from turtles import interpolate_file, docker_inspect, ImageMissing
    image = "turtle-selftest"
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
    return {
        "-s": "test",
        "-d": image,
    }
