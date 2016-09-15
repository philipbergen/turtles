def stage(settings):
    """ Creates a git-client image, then returns a stage that will interact with the user to
        determine the git URL. The URL is then cloned into CWD.
    """
    import os
    import sys
    import shutil
    from subprocess import call, Popen, PIPE
    from turtles import docker_inspect, ImageMissing, interpolate_file
    if not os.path.exists("git-url.txt"):
        try:
            giturl = raw_input("Please enter git URL: ")
        except NameError:
            giturl = input("Please enter git URL: ")
        with open("git-url.txt", "w") as fout:
            fout.write(giturl)
    image = "turtle-git"
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
        "-s": "setup",  # Ignored by repo_setup
        "-d": image,
        "-v": [".:/cwd:rw", "~/.ssh:/home/turtle/.ssh:rw"],
    }
