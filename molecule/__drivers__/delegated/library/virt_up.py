#!/usr/bin/python

# Copyright (c) 2020, Sine Nomine Associates
# BSD 2-Clause License

ANSIBLE_METADATA = {
    'metadata_version': '1.1.',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = r"""
---
module: virt_up

short_description: Create instances on local libvirt hypervisor

description:
  - Create instances with virt-builder, virt-sysprep, and virt-install

requirements:
  - python virt-up
  - python libvirt
  - libguestfs tools
  - qemu-img

options:
  state:
    description:
      - C(up) Create and instance if it does not exist. Creates a template if needed.
      - C(absent) Delete the instance if it exists.
    type: str
    default: up
    choices:
      - up
      - absent

  name:
    description: The instance name.
    required: true
    type: str

  template:
    description: The os template name. See C(virt-up --list-templates). Required for state C(up).
    type: str

  sshdir:
    description:
      - Local destination for ssh key files. This path will be used to
        set the results for the molecule instance configuration.
    type: path

  logfile:
    description: Log file destination on hypervisor.
    type: path
    default: $HOME/.cache/virt-up/virt-up.log

author:
  - Michael Meffie (@meffie)
"""

EXAMPLES = r"""
- name: Create instance(s).
  virt_up:
    state: up
    name: myinst
    template: generic-centos-8
    sshdir: "{{ molecule_ephemeral_directory }}"
  register: virt_up
"""

RETURN = r"""
server:
  description: Molecule instance configuration for delegated drivers.
  type: dict
  sample:
    instance: instance.name
    address: internet address
    user: login username
    port: ssh port
    identity_file: fully qualified ssh key file destination path

remote_identity_file:
  description: fully qualified path of the generated key on the hypervisor
  type: path
"""

import logging
import os
import pprint

from ansible.module_utils.basic import AnsibleModule
import virt_up

log = logging.getLogger(__name__)
loglevels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'warn': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['up', 'absent'], default='up'),
            name=dict(type='str', required=True),
            template=dict(type='str'),
            size=dict(type='str', default=None),
            memory=dict(type='int', default=None),
            cpus=dict(type='int', default=1),
            sshdir=dict(type='path', default=''),
            logfile=dict(type='path', default='~/.cache/virt-up/virt-up.log'),
            loglevel=dict(type='str', choices=loglevels.keys(), default='info'),
        ),
        supports_check_mode=False,
    )
    result = dict(
        changed=False,
        server=dict(),
    )

    logfile = os.path.expanduser(module.params['logfile'])
    if not os.path.exists(os.path.dirname(logfile)):
        os.makedirs(os.path.dirname(logfile))
    logging.basicConfig(
        filename=logfile,
        level=loglevels[module.params['loglevel']],
        format='%(asctime)s %(levelname)s %(message)s')
    log.info("Starting virt_up: version='%s', state='%s', name='%s', template='%s'",
        virt_up.__version__,
        module.params['state'], module.params['name'], module.params['template'])

    name = module.params['name']
    if module.params['state'] == 'up' and not virt_up.Instance.exists(name):
        if not 'template' in module.params:
            raise ValueError("template parameter is required for state 'up'.")

        template = virt_up.Instance.build(
            module.params['template'],
            template=module.params['template'],
            prefix='TEMPLATE-',
            size=module.params['size'],
            memory=module.params['memory'],
            vcpus=module.params['cpus'])

        instance = template.clone(
          name,
          memory=module.params['memory'],
          vcpus=module.params['cpus'])
        instance.start()
        instance.wait_for_port(22) # Wait for boot to complete.
        log.info("Instance '%s' is up.", instance.name)

        ssh_identity = instance.meta['user']['ssh_identity']
        identity_file = os.path.join(module.params['sshdir'], os.path.basename(ssh_identity))
        result['changed'] = True
        result['remote_identity_file'] = ssh_identity
        result['server'] = {
            'instance': instance.name,
            'address': instance.address(),
            'user': instance.meta['user']['username'],
            'port': '22',
            'identity_file': identity_file,
        }

    if module.params['state'] == 'absent' and virt_up.Instance.exists(name):
        instance = virt_up.Instance(name)
        ssh_identity = instance.meta['user']['ssh_identity']
        instance.delete()
        log.info("Instance '%s' was deleted.", name)
        result['changed'] = True
        result['server'] = {
            'identity_file': os.path.join(module.params['sshdir'], os.path.basename(ssh_identity)),
        }

    log.debug('result=%s', pprint.pformat(result))
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
