from __future__ import print_function
import os
import sys
import time
from subprocess import STDOUT

import six


def sp_run(cmd, stderr=None, stdout=None, check=True, timeout=None):
    """ Python 2 compatibility means we can't use subprocess.run
    """
    from subprocess import Popen, CalledProcessError
    pope = Popen(cmd, stderr=stderr, stdout=stdout)
    try:
        stdo, stde = pope.communicate(timeout=timeout)
    except TypeError:
        stdo, stde = pope.communicate()  # Python 2
    return pope.returncode, stdo, stde


__EM_CACHE = {}


def em(*names):
    """ :return: String of emojis from named emojis in names.
    """
    if os.environ.get("JOB_NAME", None) is not None:
        return "=] "
    if not __EM_CACHE:
        import json
        with open(os.path.join(os.path.dirname(__file__), 'emojis.json')) as fin:
            __EM_CACHE.update(json.load(fin))
    return ' '.join([__EM_CACHE[name]['char'] for name in names])


class PrepFailed(Exception):
    """ Raised to indicate that a prep for a stage terminated with non-zero exit code.
    """


class ImageMissing(Exception):
    """ Raised when a docker image is addressed that does not exist.
    """


class StageFailed(Exception):
    """ Raised to indicate that a stage terminated with non-zero exit code.
    """


class MaxRecursion(Exception):
    """ Raised when recursion level passes a preset threshold.
    """


class InvalidPreconditions(Exception):
    """ Raised when the input settings are invalid.
    """


def load_pipeline(filename):
    """ Import the pipeline script. The script should have the method "stage(settings)",
        it will be called by trtl.
    """
    from types import ModuleType
    pipeline = ModuleType('turtle_pipeline')
    # pipeline.__file__ = filename
    exec(open(filename).read(), pipeline.__dict__)
    return pipeline


def docker_inspect(image):
    """ Returns the inspection structure (a list of dictionaries) from docker inspect.
        :param image: Name of image.
    """
    import json
    from subprocess import Popen, PIPE
    pope = Popen(["docker", "inspect", image], stdout=PIPE)
    so, _ = pope.communicate()
    if not type(so) == str:
        so = str(so, encoding='utf-8')
    if pope.returncode:
        raise ImageMissing(image)
    return json.loads(so)


def interpolate_file(input_path, output_path, kw={}, log=lambda x: None):
    """ Using a file formatted with python %(xyz)s as input, creates the output file.
        :param kw: Dictionary with key-val for interpolation, uid_gid is automatically
            added for convenience.
        :param log: Set to a function that is called with strings for logging, if desired
    """
    if 'uid_gid' not in kw:
        kw['uid_gid'] = "%d:%d" % (os.getuid(), os.getgid())
        log("Added uid_gid: " + kw['uid_gid'])
    with open(output_path, 'w') as fout, open(input_path) as fin:
        log("Extrapolating " + input_path + " to " + output_path)
        fout.write(fin.read() % kw)


def stage(settings, volume_prefix=None):
    """ Runs a stage with docker.
        :param settings: The settings dict.
        :param volume_prefix: The path to prefix relative paths with, if None, use CWD.
        :raise: StageFailed if the docker command exits non-zero.
    """

    def abspath(path, prefix):
        if not path.startswith("/"):
            path = os.path.join(prefix, path)
        return os.path.abspath(path)

    def volumes(settings, prefix):
        xtra = [
            abspath(os.path.expanduser(v.split(":", 1)[0]), prefix) + ":" + v.split(":", 1)[1]
            for v in settings['-v']]
        return [settings['-w'] + ':/workspace:rw', settings['-r'] + ':/result:rw'] + xtra

    def ports(image):
        try:
            di = docker_inspect(image)
            res = []
            for ep, _ in six.iteritems(di[-1]["Config"]["ExposedPorts"]):
                p, _ = (ep + '/').split('/', 1)
                res.append('-p')
                res.append(p + ":" + p)
            return res
        except (ImageMissing, IndexError, KeyError):
            return []

    volume_prefix = volume_prefix or os.getcwd()

    print(em('cinema'), "Starting stage", settings['-s'])
    try:
        os.makedirs(settings['-r'])
    except OSError:
        pass  # Ignore if directory exists already
    cmd = ["docker", 'run', '--rm', '-w', '/workspace']
    for vol in volumes(settings, volume_prefix):
        cmd += ["-v", vol]
    cmd += ports(settings['-d'])
    cmd += [settings['-d'], settings['-s']]
    print(em('whale'), cmd)
    with open(os.path.join(settings['-r'], 'log.txt'), 'a') as fout:
        fout.write('Log started: %d-%.2d-%.2d %.2d:%.2d:%.2d\n' % time.localtime()[:6])
        print(em('scroll'), "Output logged in", fout.name)
        returncode, stdo, stde = sp_run(cmd, stderr=STDOUT, stdout=fout, check=True,
                                        timeout=settings['-t'])
        if stdo:
            fout.write(stdo)
        if stde:
            fout.write(stde)
        if returncode:
            if stdo:
                sys.stdout.write(stdo)
            if stde:
                sys.stderr.write(stde)
            raise StageFailed(settings)
