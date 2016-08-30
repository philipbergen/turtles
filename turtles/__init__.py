from __future__ import print_function
import os
import sys
import time
import attr
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
    if not __EM_CACHE:
        import json
        # TODO: What is the right way to do this?
        with open(os.path.join(os.path.dirname(__file__), 'emojis.json')) as fin:
            __EM_CACHE.update(json.load(fin))
    return ' '.join([__EM_CACHE[name]['char'] for name in names])


class PrepFailed(Exception):
    """ Raised to indicate that a prep for a stage terminated with non-zero exit code.
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


@attr.s
class TurtleNeck(object):
    """ opts are the options as given by the docstring in turtle.trtl
    """
    opts = attr.ib()

    # def __repr__(self):
    #     return "TurtleNeck(%r)" % self.opts
    #
    # def __str__(self):
    #     return "<TurtleNeck(%s)>" % ', '.join(["%s=%s" % (k, v) for k, v in six.iteritems(self.opts) and v is not None])

    @property
    def volumes(self):
        xtra = [os.path.abspath(v.split(":", 1)[0]) + ":" + v.split(":", 1)[1] for v in self.opts['-v']]
        return [self.opts['-i'] + ':/input:ro', self.opts['-o'] + ':/output:rw'] + xtra

    def __getattr__(self, item):
        return self.opts[("-" + item) if len(item) == 1 else ("--" + item.replace("_", '-'))]


def stage(neck):
    """ Runs a stage with docker.
        :param neck: TurtleNeck input for the stage.
        :raise: StageFailed if the docker command exits non-zero.
    """
    print(em('cinema'), "Starting stage", neck.s)
    try:
        os.makedirs(neck.o)
    except OSError:
        pass  # Ignore if directory exists already
    cmd = ["docker", 'run', '--rm']
    for vol in neck.volumes:
        cmd += ["-v", vol]
    cmd += [neck.d, neck.s]
    print(em('whale'), cmd)
    with open(os.path.join(neck.o, 'log.txt'), 'a') as fout:
        fout.write('Log started: %d-%.2d-%.2d %.2d:%.2d:%.2d\n' % time.localtime()[:6])
        print(em('scroll'), "Output logged in", fout.name)
        returncode, stdo, stde = sp_run(cmd, stderr=STDOUT, stdout=fout, check=True, timeout=neck.t)
        if stdo:
            fout.write(stdo)
        if stde:
            fout.write(stde)
        if returncode:
            if stdo:
                sys.stdout.write(stdo)
            if stde:
                sys.stderr.write(stde)
            raise StageFailed(neck)


def prep(settings):
    """ Runs prep script before the stage specified in settings runs.
        :param settings: The dictionary of settings that is going to be the input arg to TurtleNeck for the next stage.
    """
    cmd = [settings['-p'], '--prep']
    for k, v in sorted(six.iteritems(settings)):
        if k != '-p' and not k.startswith('--') and v is not None:
            if type(v) is list:
                for vv in v:
                    cmd.append(k)
                    cmd.append(vv)
            else:
                cmd.append(k)
                cmd.append(str(v))
    print(em('mortar_board'), cmd)
    with open(os.path.join(settings['-o'], 'log.txt'), 'a') as fout:
        fout.write('Log started: %d-%.2d-%.2d %.2d:%.2d:%.2d\n' % time.localtime()[:6])
        print(em('scroll'), "Output logged in", fout.name)
        returncode, stdo, stde = sp_run(cmd, stderr=STDOUT, stdout=fout, check=True, timeout=settings['-t'])
        if stdo:
            fout.write(stdo)
        if stde:
            fout.write(stde)
        if returncode:
            if stdo:
                sys.stdout.write(stdo)
            if stde:
                sys.stderr.write(stde)
            raise PrepFailed(settings)
