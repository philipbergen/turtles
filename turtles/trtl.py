"""
Usage:
    trtl [-p PIPELINE] [-i INPUT_DIR] [-o OUTPUT_DIR] [-d IMAGE] [-s STAGE] [-t TIMEOUT]
         [-v VOLUME]... [--stop STOP] [--one] [--max-recurse MAX_RECURSE] [--verbose]

Options:
    -p PIPELINE    Path to a turtle pipeline script.

    -i INPUT_DIR   The directory to mount as /input inside the container. Typically the root
                   of your source tree. If not
                   specified os.path.dirname(<SETTINGS_JSON>) will be used.

    -o OUTPUT_DIR  Target directory base for output from this stage. If not specified
                   <INPUT_DIR> will be used. Only if <OUTPUT_DIR> is set, the combined
                   <OUTPUT_DIR>/<STAGE> will be used.

    -d IMAGE       Docker image URL. If not specified, the path from <INPUT_DIR>/result.json
                   will be used.

    -s STAGE       Optionally specify the stage to run on the input. If not specified it will
                   be derived from <INPUT_DIR>/settings.json

    -t TIMEOUT     The timeout in seconds, only supported on python3.

    -v VOLUME      Extra volume mounts for the container. Same format as -v for docker.

    --one          Run just one stage, then stop.

    --stop STOP    Run until the next stage is <STOP>, then stop.

    --max-recurse MAX_RECURSE  The maximum stages to allow trtl to recurse through [default: 100]

    --verbose      Verbose

"""
from __future__ import absolute_import, print_function
import os
import json

import six


def main(opts):
    """ Acts on the options derived from the usage described in __doc__.
    """

    def say(*args):
        if opts['--verbose']:
            print(*args)

    from . import load_pipeline, stage, StageFailed, MaxRecursion, em
    o_outdir = opts['-o']
    if o_outdir is not None:
        o_outdir = os.path.abspath(o_outdir)
    settings = {k: v for k, v in six.iteritems(opts) if not k.startswith('--')}
    opts['--max-recurse'] = int(opts['--max-recurse'])
    say("OPTS", opts)

    if settings['-p']:
        for k, v in six.iteritems(load_pipeline(settings['-p']).stage(settings)):
            if k == '-v':
                settings['-v'].extend(v)
            elif settings.get(k, None) is None:
                settings[k] = v
    if not settings['-p'] and not settings['-i']:
        raise Exception("At least one of INPUT_DIR and PIPELINE must be set.")
    if not settings['-s']:
        raise Exception("STAGE must be set.")
    if not settings['-d']:
        raise Exception("IMAGE must be set.")

    if not settings['-i']:
        settings['-i'] = os.path.dirname(settings['-p'])
    if not settings['-o']:
        settings['-o'] = settings['-i']
    settings['-i'] = os.path.abspath(os.path.expanduser(settings['-i']))
    settings['-o'] = os.path.abspath(os.path.expanduser(settings['-o']))
    say("SETTINGS", settings)
    del settings['-p']

    for _ in range(opts['--max-recurse']):
        try:
            if o_outdir:
                print(em("point_right"), "Using", o_outdir, "as base, appending", settings['-s'],
                      "for OUTPUT_DIR")
                settings['-o'] = os.path.join(o_outdir, settings['-s'])
            res_path = settings['-o'] + '/result.json'
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
                if '-o' in tmp:
                    o_outdir = os.path.abspath(tmp['-o'])
                settings.update(tmp)
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
