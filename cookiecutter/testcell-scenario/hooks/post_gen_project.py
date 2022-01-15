import os
import sys
import re
import glob

# Find build playbook(s) in use.
keep = []
with open('molecule/playbooks/prepare.yml') as f:
    for line in f.readlines():
        m = re.match(r'- import_playbook: build/(.*)', line)
        if m:
            keep.append(m.group(1))

# Remove the unused build playbooks.
for path in glob.glob('molecule/playbooks/build/*'):
    playbook = os.path.basename(path)
    if playbook not in keep:
        os.unlink(path)

# Create an initial .gitignore file. We do this with the hook to
# avoid a .gitignore file in the template repo.
if not os.path.exists('.gitignore'):
    with open('.gitignore', 'w') as f:
        for i in ('.*', '*.pyc', '*.pyo', 'venv/', 'builds/', 'reports/'):
            f.write('%s\n' % i)

# Unfortunately, Cookiecutter does not clean up rendered hook scripts. As a
# workaround, remove myself to avoid cluttering /tmp with a large number of
# small files called /tmp/tmp*.py.
if sys.argv[0].startswith('/tmp/tmp'):
    os.unlink(sys.argv[0])
