#
# POC molecule-robotframework verify.
#
# Read the molecule managed connection information to run
# robot over ssh on the test instance and show live output.
#

import pathlib
import sh
import click
import yaml
from pprint import pprint as pp

CACHEDIR = pathlib.Path('~/.cache/molecule/openafs-robotest').expanduser()

def load_config(scenario_name, instance):
    config = {}
    yml = CACHEDIR / scenario_name / 'instance_config.yml'
    for i in yaml.safe_load(yml.read_text()):
        if i['instance'] == instance:
           return i
    return None

@click.command()
@click.option('-s', '--scenario-name', default='default')
@click.option('-i', '--instance', default='m-server-01')
@click.option('-t', '--test-suite', default='tests')
def main(scenario_name, instance, test_suite):
    config = load_config(scenario_name, instance)
    #pp(config)
    args = [
        '-p', config['port'],
        '-i', config['identity_file'],
        '-o', 'PasswordAuthentication=no',
        '-o', 'CheckHostIP=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'LogLevel=ERROR',
        '%s@%s' % (config['user'], config['address']),
    ]
    ssh = sh.Command('ssh').bake(args)
    cmd = [
        'robot',
        '-A', '.openafs-robotest/robotrc',
        'openafs-robotest/%s' % test_suite,
    ]
    for line in ssh(*cmd, _iter=True, _err_to_out=True):
        click.echo(line, nl=False)

if __name__ == '__main__':
    main()
