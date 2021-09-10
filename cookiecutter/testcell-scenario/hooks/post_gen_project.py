import os
import sys
import re
import glob

# Find build playbook(s) in use.
keep = []
with open('molecule/playbooks/converge.yml') as f:
    for line in f.readlines():
        m = re.match(r'- import_playbook:\s*(.*build.*)\s*', line)
        if m:
            keep.append(m.group(1))

# Remove the unused build playbooks.
for path in glob.glob('molecule/playbooks/*build*'):
    playbook = os.path.basename(path)
    if playbook not in keep:
        os.unlink(path)

# Unfortunately, Cookiecutter does not clean up rendered hook scripts. As a
# workaround, remove myself to avoid cluttering /tmp with a large number of
# small files called /tmp/tmp*.py.
if sys.argv[0].startswith('/tmp/tmp'):
    os.unlink(sys.argv[0])
