def stage(settings):
    """ Creates a mvn image and pipeline.
    """
    import os
    import sys
    import shutil
    from subprocess import call, Popen, PIPE
    shares = ['~/.ssh', '~/.m2']
    for share in shares:
        if not os.path.exists(os.path.expanduser(share)):
            sys.exit("For jenkins to work properly you need: " + share)
    pope = Popen(["git", "remote", "get-url", "origin"], stdout=PIPE)
    giturl, _ = pope.communicate()
    giturl = giturl.strip()  # git@github.com:philipbergen/turtles.git
    user, ghurl = giturl.split('@', 1)  # git, github.com:philipbergen/turtles.git
    ghurl, ghrepo = ghurl.split(':', 1)  # github.com, philipbergen/turtles.git
    org, name = ghrepo.rsplit('/', 1)  # philipbergen, turtles.git
    name, _ = name.split(".", 1)  # turtles, _
    template = {
        "name": name,
        "user": user,
        "github_org": org,
        "github_url": "https://%s/%s/%s" % (ghurl, org, name),
        "git_url": giturl,
    }
    cfg_path = ".jenkins/jobs/%(name)s/config.xml" % template
    if not os.path.exists(".jenkins") or not os.path.exists(cfg_path):
        try:
            os.makedirs(".jenkins/jobs/%(name)s" % template)
        except OSError:
            pass
        with open(cfg_path, 'w') as fout:
            cfg_xml = open(os.path.join(os.path.dirname(settings['-p']), "config.xml")).read()
            fout.write(cfg_xml % template)
    image = "turtle-jenkins"
    pope = Popen(["docker", "images", "-q", image], stdout=PIPE)
    so, _ = pope.communicate()
    if not so.strip():
        here = os.getcwd()
        with open(os.path.join(here, "log.txt"), 'a') as fout:
            print("Preparing for pipeline, logging to", fout.name)
            try:
                os.chdir(os.path.dirname(settings['-p']))
                call(["git", "clone", "git@github.com:philipbergen/turtles.git"])
                res = call(["docker", "build", "-t", image, "."], stdout=fout)
                if res:
                    sys.exit("Docker build failed.")
            finally:
                shutil.rmtree("turtles")
                os.chdir(here)
    return {
        "-s": '/usr/local/bin/jenkins.sh',
        "-d": image,
        "-v": ["/var/run/docker.sock:/var/run/docker.sock", ".jenkins:/var/jenkins_home:rw"] + [
            '%s:%s:rw' % (share, share.replace('~', '/var/jenkins_home')) for
            share in shares],
    }
