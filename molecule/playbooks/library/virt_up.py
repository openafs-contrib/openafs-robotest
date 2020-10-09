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
    description: The os template name. See C(virt-up --list-templates).
    required: true
    type: str

  sshdir:
    description:
      - Local destination for ssh key files. This path will be used to
        set the results for the molecule instance configuration.
    type: path

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

from ansible.module_utils.basic import AnsibleModule
import virt_up

log = logging.getLogger(__name__)

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['up', 'absent'], default='up'),
            name=dict(type='str', required=True),
            template=dict(type='str', required=True),
            sshdir=dict(type='path', default='')
        ),
        supports_check_mode=False,
    )
    result = dict(
        changed=False,
        server=dict(),
    )

    logging.basicConfig(level=logging.INFO, filename='/tmp/virt_up.log')
    log.info("Staring virt_up: version='%s', state='%s', name='%s', template='%s'",
        virt_up.__version__,
        module.params['state'], module.params['name'], module.params['template'])

    if module.params['state'] == 'up':
        name = module.params['name']
        tname = module.params['template']
        template = virt_up.Instance.build(tname, template=tname, prefix='TEMPLATE-')
        instance = template.clone(name)
        instance.start()
        address = instance.address() # Wait for address to be assigned.

        ssh_identity = instance.meta['user']['ssh_identity']
        result['changed'] = True
        result['server'] = {
            'instance': instance.name,
            'address': address,
            'user': instance.meta['user']['username'],
            'port': '22',
            'identity_file': os.path.join(module.params['sshdir'], os.path.basename(ssh_identity)),
        }
        result['remote_identity_file'] = ssh_identity
    elif module.params['state'] == 'absent':
        name = module.params['name']
        if virt_up.Instance.exists(name):
            instance = virt_up.Instance(name)
            ssh_identity = instance.meta['user']['ssh_identity']
            instance.delete()
            result['changed'] = True
            result['server'] = {
                'identity_file': os.path.join(module.params['sshdir'], os.path.basename(ssh_identity)),
            }
    else:
        raise ValueError('Invalid state parameter.')

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
