def stage(settings):
    """ Creates a mvn image and pipeline.
    """
    import os
    import sys
    import shutil
    from subprocess import call, Popen, PIPE
    from turtles import interpolate_file, docker_inspect, ImageMissing
    shares = ['~/.ssh', '~/.m2']
    for share in shares:
        if not os.path.exists(os.path.expanduser(share)):
            sys.exit("For jenkins to work properly you need: " + share)
    image = "turtle-jenkins"
    try:
        docker_inspect(image)
    except ImageMissing:
        here = os.getcwd()
        with open(os.path.join(here, "log.txt"), 'a') as fout:
            print("Preparing for pipeline, logging to", fout.name)
            try:
                os.chdir(os.path.dirname(settings['-p']))
                if call(["git", "clone", "git@github.com:philipbergen/turtles.git"]):
                    sys.exit("Failed: git clone git@github.com:philipbergen/turtles.git")
                interpolate_file("Dockerfile.in", "Dockerfile", log=fout.write)
                if call(["docker", "build", "-t", image, "."], stdout=fout):
                    sys.exit("Docker build failed.")
            finally:
                shutil.rmtree("turtles")
                os.chdir(here)
    if not os.path.exists(".jenkins/plugins"):
        try:
            os.mkdir(".jenkins")
        except OSError:
            pass
        uidgid = "%d:%d" % (os.getuid(), os.getgid())
        print("Will now launch Jenkins, please press run the wizard and shut down jenkins after")
        cmd = ["docker", "run", "--user", uidgid, "-p", "8080:8080", "--rm", "-v",
               os.path.abspath(".jenkins") + ":/var/jenkins_home:rw",
               image]
        call(cmd)
    pope = Popen(["git", "remote", "get-url", "origin"], stdout=PIPE)
    giturl, _ = pope.communicate()
    if not type(giturl) == str:
        giturl = str(giturl, encoding='utf-8')
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
    if not os.path.exists(cfg_path):
        try:
            os.makedirs(os.path.dirname(cfg_path))
        except OSError:
            pass
        interpolate_file(os.path.join(os.path.dirname(settings['-p']), "config.xml"), cfg_path,
                         template)
    with open(".jenkins/cwd", 'w') as fout:
        fout.write(os.getcwd())
    return {
        "-s": '/usr/local/bin/jenkins.sh',
        "-d": image,
        "-v": ["/var/run/docker.sock:/var/run/docker.sock", ".jenkins:/var/jenkins_home:rw"] + [
            '%s:%s:rw' % (share, share.replace('~', '/var/jenkins_home')) for
            share in shares],
    }
