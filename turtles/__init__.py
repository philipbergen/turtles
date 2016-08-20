import os
import attr


def em(*names, cache={}):
    """ :return: String of emojis from named emojis in names.
    """
    if not cache:
        import ujson
        import sys
        with open([p for p in sys.path[::-1] if p.endswith('/site-packages')][0] + '/em/emojis.json') as fin:
            cache.update(ujson.load(fin))
    return ''.join([cache[name]['char'] for name in names])


class StageFailed(Exception):
    """ Raised to indicate that a stage did not set success = true.
    """


class MaxRecursion(Exception):
    """ Raised when recursion level passes a preset threshold.
    """


@attr.s(slots=True)
class TurtleNeck(object):
    """ Holds all the stage parameters
    """
    indir = attr.ib()
    outdir = attr.ib(default=None)
    image = attr.ib(default=None)
    stage = attr.ib(default=None)
    result = attr.ib(default=attr.Factory(dict))
    recurse = attr.ib(default=0)

    def ensure(self):
        if not self.result:
            import ujson
            try:
                with open(os.path.join(self.indir, 'result.json')) as fin:
                    self.result = ujson.load(fin)
            except FileNotFoundError:
                pass
        if not self.stage:
            self.stage = self.result.get('next', None)
        self.image = self.result.get('image', self.image)
        print(em('point_right'), "Ensured", self)
        return self

    @property
    def input_dir(self):
        return os.path.abspath(self.indir)

    @property
    def output_dir(self):
        if self.outdir:
            return os.path.join(os.path.abspath(self.outdir), self.stage)
        return os.path.abspath(os.path.join(self.input_dir, '..', self.stage))

    @property
    def input_volume(self):
        return self.input_dir + ':/input:ro'

    @property
    def output_volume(self):
        return self.output_dir + ':/output:rw'


def stage(neck):
    """ Runs a stage with docker.
        :param neck: TurtleNeck input for the stage.
        :return: New turtle neck if call successful, else raise CalledProcessError
    """
    from subprocess import run, STDOUT
    os.makedirs(neck.output_dir, exist_ok=False)
    cmd = ["docker", 'run', '--rm', '-v', neck.input_volume, '-v', neck.output_volume, neck.image, neck.stage]
    print(em('whale'), cmd)
    with open(os.path.join(neck.output_dir, 'log.txt'), 'w') as fout:
        print(em('scroll'), "Output logged in", fout.name)
        try:
            run(cmd, stderr=STDOUT, stdout=fout, check=True, timeout=neck.result.get('timeout', 100))
        except Exception as e:
            import traceback
            fout.write("EXCEPTION: ")
            fout.write(repr(e))
            fout.write('\n')
            fout.write(traceback.format_exc())
            print(em('boom'), 'Stage crashed (%s), see log for details:' % e, fout.name)
            raise

    res = TurtleNeck(neck.output_dir, neck.outdir, neck.image, recurse=neck.recurse + 1).ensure()
    if not res.result.get('success', None):
        print(em('-1'), "Stage failed", neck)
        raise StageFailed(neck)
    print(em('+1'), "Stage successful", neck)
    return res

