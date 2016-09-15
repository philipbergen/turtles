"""
Usage:
    trtl [-p PIPELINE] [-w WORKSPACE_DIR] [-r RESULT_DIR] [-d IMAGE] [-s STAGE] [-t TIMEOUT]
         [-v VOLUME]... [--stop STOP] [--one] [--max-recurse MAX_RECURSE] [--verbose]
         [--home-dir=HOME_DIR] [--volume-prefix=VOL_PREFIX]

Options:
    -p PIPELINE    Path to a turtle pipeline script.

    -w WORKSPACE_DIR  The directory to mount as /workspace inside the container. Typically the root
                      of your source tree. If not specified CWD will be used.

    -r RESULT_DIR  Target directory base for output from this stage. If not specified
                   <WORKSPACE_DIR> is used.

    -d IMAGE       Docker image URL. If not specified, the image from <PIPELINE> is used.
                   Please note: ports exposed by an image are automatically detected and exposed.

    -s STAGE       Optionally specify the stage to run on the input. If not specified it will
                   be derived from <PIPELINE>.

    -t TIMEOUT     The timeout in seconds, only supported on python3.

    -v VOLUME      Extra volume mounts for the container. Same format as -v for docker.

    --one          Run just one stage, then stop.

    --stop STOP    Run until the next stage is <STOP>, then stop.

    --verbose      Verbose

    --max-recurse MAX_RECURSE   The maximum stages to allow trtl to recurse through [default: 100]

    --volume-prefix VOL_PREFIX  Use this to prefix relative volume mounts, not CWD. Can also be set
                                using env var TRTL_CWD.

    --home-dir HOME_DIR         Sets that path to use as "home" in paths [default: ~]

"""
from __future__ import absolute_import, print_function
import os
import json

import six


def main(opts):
    """ Acts on the options derived from the usage described in __doc__.
    """
    def abspath(path, prefix):
        if not path.startswith("/"):
            path = os.path.join(prefix, path)
        return os.path.abspath(path)

    def say(*args):
        if opts['--verbose']:
            print(*args)

    from . import load_pipeline, stage, StageFailed, MaxRecursion, em
    if opts['-r'] is not None:
        opts['-r'] = os.path.abspath(opts['-r'])
    settings = {k: v for k, v in six.iteritems(opts) if not k.startswith('--')}
    opts['--max-recurse'] = int(opts['--max-recurse'])
    if not opts['--volume-prefix']:
        opts['--volume-prefix'] = os.environ.get('TRTL_CWD', os.getcwd())
    say("OPTS", opts)

    if settings['-p']:
        for k, v in six.iteritems(load_pipeline(settings['-p']).stage(settings)):
            if k == '-v':
                settings['-v'].extend(v)
            elif settings.get(k, None) is None:
                settings[k] = v
    if not settings['-p'] and not settings['-w']:
        raise Exception("At least one of INPUT_DIR and PIPELINE must be set.")
    if not settings['-s']:
        raise Exception("STAGE must be set.")
    if not settings['-d']:
        raise Exception("IMAGE must be set.")

    if not settings['-w']:
        settings['-w'] = os.getcwd()
    if not settings['-r']:
        settings['-r'] = settings['-w']
    settings['-w'] = abspath(os.path.expanduser(settings['-w']), opts['--volume-prefix'])
    settings['-r'] = abspath(os.path.expanduser(settings['-r']), opts['--volume-prefix'])
    say("SETTINGS", settings)
    del settings['-p']

    for _ in range(opts['--max-recurse']):
        try:
            res_path = settings['-r'] + '/result.json'
            if os.path.exists(res_path):
                os.unlink(res_path)
            say(_, "SETTINGS", settings)
            stage(settings)
            print(em('+1'), "Stage successful:", settings['-s'])
            if not os.path.exists(res_path):
                say("MISSING", res_path)
                break
            with open(res_path) as fin:
                tmp = json.load(fin)
                if tmp.get('-s', None) is None or tmp['-s'] == settings['-s']:
                    break
                if '-r' in tmp:
                    tmp['-r'] = abspath(tmp['-r'], opts['--volume-prefix'])
                settings.update(tmp)
                if '-p' in settings:
                    settings.update(load_pipeline(tmp['-p']).stage(settings))
                    del settings['-p']
                print(em('fast_forward'), "Next stage is", settings['-s'])
            if opts['--one'] or opts['--stop'] == settings['-s']:
                print(em("no_entry"), "Not proceeding to next stage because --stop")
                break
        except StageFailed as e:
            print(em('x', 'boom'), "Failed", e)
            return False
    else:
        print(em('x', 'boom'), "Maximum recursion reached:", opts['--max-recurse'])
        raise MaxRecursion(settings)
    print(em('ok', 'tada'), "Final stage completed")
    return True


def cli():
    """ Wrapper for docopt parsing without dirtying the global namespace.
    """
    import docopt
    opts = docopt.docopt(__doc__)
    main(opts)


if __name__ == '__main__':
    cli()
