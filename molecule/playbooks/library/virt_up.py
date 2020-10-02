#!/usr/bin/python

import logging
import os

from ansible.module_utils.basic import AnsibleModule
import virt_up

log = logging.getLogger(__name__)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['up', 'absent']),
            name=dict(type='str', required=True),
            template=dict(type='str'),
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
        tname = module.params.get('template', 'generic-centos-8')
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
