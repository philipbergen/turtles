def stage(settings):
    """ Creates a git-client image, then returns a stage that will interact with the user to determine the
        git URL. The URL is then cloned into CWD. """
    import os
    import sys
    import shutil
    from subprocess import call, Popen, PIPE
    if not os.path.exists("git-url.txt"):
        try:
            giturl = raw_input("Please enter git URL: ")
        except NameError:
            giturl = input("Please enter git URL: ")
        with open("git-url.txt", "w") as fout:
            fout.write(giturl)
    image = "turtle-git"
    pope = Popen(["docker", "images", "-q", image], stdout=PIPE)
    so, _ = pope.communicate()
    if not so.strip():
        here = os.getcwd()
        with open(os.path.join(here, "log.txt"), 'a') as fout:
            print("Preparing for pipeline, logging to", fout.name)
            try:
                os.chdir(os.path.dirname(settings['-p']))
                if not os.path.exists('.ssh'):
                    shutil.copytree(os.path.expanduser("~/.ssh"), ".ssh")
                res = call(["docker", "build", "-t", image, "."], stdout=fout)
                if res:
                    sys.exit("Docker build failed.")
            finally:
                shutil.rmtree(".ssh")
                os.chdir(here)
    return {
        "-s": "setup",  # Ignored by repo_setup
        "-d": image,
        "-v": [".:/cwd:rw"],
    }
