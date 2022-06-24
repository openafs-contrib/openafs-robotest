import json
import itertools
import os
import pathlib
import pytest

from cookiecutter.main import cookiecutter
from contextlib import contextmanager

DRIVER = os.environ.get('MOLECULE_DRIVER_NAME', 'vagrant/libvirt')

cluster_types = {
    '1host': "one instance",
    '2hosts': "one client instance, one server instance",
    '9hosts': "three client instances, three database instances, three fileserver instances",
}


def is_valid(mode, row):
    d, c, p, i = row
    if mode == 'run' and d != DRIVER:
        return False
    if p.startswith('solaris') and i in ('managed', 'packages'):
        return False
    return True


def params(mode):
    cookiecutter_json = pathlib.Path(__file__).parent.parent / 'testcell-scenario' / 'cookiecutter.json'
    with open(cookiecutter_json) as f:
        c = json.load(f)
    for row in itertools.product(c['driver'], cluster_types.keys(), c['platform'], c['install_method']):
        if is_valid(mode, row):
            yield(row)


@contextmanager
def chdir(path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def run_command(c):
    print('Running:', c)
    return os.system(c)


def render(tmpdir, driver,cluster, platform, install_method):
    """
    Render the template in the tmpdir.
    Raises an execption on error.
    """
    testcell_name = '%s-%s-%s' % (platform, install_method, cluster)
    template = pathlib.Path(__file__).parent.parent.parent
    cookiecutter(
        template=str(template),
        directory='cookiecutter/testcell-scenario',
        output_dir=str(tmpdir),
        no_input=True,
        extra_context={
            'testcell_name': testcell_name,
            'driver': driver,
            'cluster': cluster_types[cluster],
            'platform': platform,
            'install_method': install_method,
            'install_with_dkms': 'yes',
            'build_packages': 'yes',
        },
    )
    print("\nCreated scenario in directory %s/%s" % (tmpdir, testcell_name))
    return testcell_name


@pytest.mark.parametrize('driver,cluster,platform,install_method', params('render'))
def test_render(tmpdir, driver,cluster, platform, install_method):
    testcell_name = render(tmpdir, driver,cluster, platform, install_method)

    # Check generated files (except optional build tasks).
    files = [
        'molecule',
        'molecule/default',
        'molecule/default/collections.yml',
        'molecule/default/molecule.yml',
        'molecule/playbooks',
        'molecule/playbooks/converge_cell.yml',
        'molecule/playbooks/converge_realm.yml',
        'molecule/playbooks/converge.yml',
        'molecule/playbooks/prepare.yml',
        'molecule/templates',
        'molecule/templates/openafs-robotest.yml.j2'
    ]
    for f in files:
        filename = tmpdir / testcell_name / f
        assert filename.exists()

    # Spot check the generated molecule file.
    molecule_yml = pathlib.Path(tmpdir / testcell_name / 'molecule' / \
                   'default' / 'molecule.yml').read_text()
    assert platform in molecule_yml
    assert install_method in molecule_yml
    if install_method in ('packages', 'bdist', 'sdist'):
        assert 'afs_builders' in molecule_yml
    else:
        assert 'afs_builders' not in molecule_yml

    # Check the generated scenario file.
    prepare_yml = pathlib.Path(tmpdir / testcell_name / 'molecule' / \
                   'playbooks' / 'prepare.yml').read_text()
    if install_method in ('packages', 'bdist', 'sdist'):
        assert 'import_playbook: build' in prepare_yml

    # Check with yamllint and ansible-lint.
    with chdir(tmpdir / testcell_name):
        rc = run_command('yamllint .')
    assert rc == 0

    # Get our required collection.
    with chdir(tmpdir / testcell_name):
        rc = run_command('molecule dependency')
    assert rc == 0
    path = pathlib.Path.home() / '.cache' / 'molecule' / \
           testcell_name / 'default' / 'collections'
    cmd = 'ANSIBLE_COLLECTIONS_PATHS=%s ansible-lint' % (path)
    with chdir(tmpdir / testcell_name):
        rc = run_command(cmd)
    assert rc == 0


@pytest.mark.parametrize('driver,cluster,platform,install_method', params('run'))
def test_run(tmpdir, driver,cluster, platform, install_method):
    testcell_name = render(tmpdir, driver,cluster, platform, install_method)
    with chdir(tmpdir / testcell_name):
         bcdir = pathlib.Path('~/.config/molecule').expanduser()
         bc = bcdir / 'platforms' / ('%s.yml' % platform)
         opt = (' --base-config=%s' % bc) if bc.exists() else ''
         rc = run_command('molecule%s test' % opt)
         assert rc == 0
         rc = run_command('molecule%s reset' % opt)
         assert rc == 0
