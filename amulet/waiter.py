
import os
import sys
import yaml
import subprocess
import helpers

from helpers import JUJU_VERSION, TimeoutError

_success_states = ['started']

# Move these to another module?
def _get_gojuju_status(environment=None):
    return _get_pyjuju_status(environment)


# Move these to another module?
def _get_pyjuju_status(environment=None):
    cmd = ['juju', 'status']
    if environment:
        cmd.extend(['-e', environment])

    try:
        status_yml = subprocess.check_output(cmd)
    except TimeoutError:
        raise
    except:
        raise Exception('Unable to query status for %s' % environment)

    return yaml.safe_load(status_yml)


def _parse_unit_state(data):
    states = ['life', 'relations-error', 'agent-state']
    for state_key in states:
        if state_key in data:
            return data[state_key]


def status(*args, **kwargs):
    status = {}

    if not 'juju_env' in kwargs:
        raise KeyError('No juju_env set')

    juju_env = kwargs['juju_env']

    try:
        if JUJU_VERSION.major == 0:
            juju_status = _get_pyjuju_status(juju_env)
        else:
            juju_status = _get_gojuju_status(juju_env)
    except TimeoutError:
        raise
    except Exception as e:
        print e
        return status

    if not args:
        args = [service for service in juju_status['services']]

    for arg in args:
        service, unit = arg.split('/') if '/' in arg else [arg, None]
        if not service in juju_status['services']:
            raise ValueError('%s is not in the deployment yet' % arg)

        if not service in status:
            status[service] = {}

        # Use potential recurive + mergedicts?
        # http://stackoverflow.com/a/7205672/196832
        units = juju_status['services'][service]['units']
        if unit:
            state = _parse_unit_state(units['/'.join([service, unit])])
            status[service][unit] = state
        else:
            for unit_name in units:
                unit = unit_name.split('/')[1]
                state = _parse_unit_state(units['/'.join([service, unit])])
                status[service][unit] = state

    return status

def setup_parser(parent):
    from . import wait

    def wait_cmd(args):
        try:
            wait(*args.services, **vars(args))
        except TimeoutError:
            print >> sys.stderr, 'Timeout criteria was met'
            sys.exit(124)
        except:
            print >> sys.stderr, 'Unexpected error occurred'
            raise

        sys.exit(0)

    parser = parent.add_parser('wait', help="Wait until criteria is met")
    parser.add_argument('-e', '--environment', dest='juju_env',
                        help="Juju environment")
    parser.add_argument('-t', '--timeout', help="Timeout in seconds", type=int)
    parser.add_argument('services', nargs='*',
                        help="What services or units to wait on")
    parser.set_defaults(func=wait_cmd)

