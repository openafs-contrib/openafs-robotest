import collections
import os
import pathlib
import pytest

from cookiecutter.main import cookiecutter
from contextlib import contextmanager

platforms = [
    'alma8',
    'debian11',
    'fedora35',
    'solaris114',
]

install_methods = ['managed', 'packages', 'bdist', 'sdist', 'source']
layout = [
    '1 host',
]

@contextmanager
def chdir(path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)

def params():
    p = []
    for x in platforms:
        for y in install_methods:
            if x.startswith('solaris') and y in ['managed', 'packages']:
                continue  # package installs not supported on solaris.
            p.append((x, y, 0))
    for hi, _ in enumerate(layout):
        if hi != 0:
            p.append((platforms[0], install_methods[0], hi))
    return p

def run_command(c):
    print('Running:', c)
    return os.system(c)

def get_str_option(name, default):
    return os.environ.get(name, default)

def get_bool_option(name, default):
    value = get_str_option(name, default)
    if value.lower() in ('1', 'y', 'yes', 'true', 'on'):
        return True
    if value.lower() in ('0', 'n', 'no', 'false', 'off'):
        return False
    raise ValueError('Invalid value %s: %s' % (name, value))

@pytest.mark.parametrize('platform,install_method,layout_index', params())
def test_template(tmpdir, install_method, platform, layout_index):

    print("\nRunning in directory %s" % tmpdir)

    # Test options.
    lint = get_bool_option('TCS_LINT', 'yes')
    run = get_bool_option('TCS_RUN', 'no')
    install_with_dkms = get_bool_option('TCS_ENABLE_DKMS', 'no')
    build_packages = get_bool_option('TCS_ENABLE_BUILDS', 'yes')
    do_build = (build_packages and install_method in ('packages', 'bdist', 'sdist'))

    # Render the template in the tmpdir. Raises an execption on error.
    testcell_name = '%s-%s-%d' % (platform, install_method, layout_index)
    template = pathlib.Path(__file__).parent.parent.parent
    cookiecutter(
        template=str(template),
        directory='cookiecutter/testcell-scenario',
        output_dir=str(tmpdir),
        no_input=True,
        extra_context={
            'testcell_name': testcell_name,
            'driver': 'vagrant/libvirt',
            'platform': platform,
            'install_method': install_method,
            'install_with_dkms': ('yes' if install_with_dkms else 'no'),
            'build_packages': ('yes' if build_packages else 'no'),
        },
    )
    print("\nCreated scenario in directory %s/%s" % (tmpdir, testcell_name))

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
    if do_build:
        assert 'afs_builders' in molecule_yml
    else:
        assert 'afs_builders' not in molecule_yml

    # Check the generated scenario file.
    prepare_yml = pathlib.Path(tmpdir / testcell_name / 'molecule' / \
                   'playbooks' / 'prepare.yml').read_text()
    if do_build:
        assert 'import_playbook: build' in prepare_yml

    # Optionally, check with yamllint and ansible-lint.
    if lint:
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

    # Optionally, run the generated scenario. This can take a long time.
    if run:
        with chdir(tmpdir / testcell_name):
            bcdir = pathlib.Path('~/.config/molecule').expanduser()
            bc = bcdir / 'platforms' / ('%s.yml' % platform)
            opt = (' --base-config=%s' % bc) if bc.exists() else ''
            rc = run_command('molecule%s test' % opt)
            assert rc == 0
            rc = run_command('molecule%s reset' % opt)
            assert rc == 0
