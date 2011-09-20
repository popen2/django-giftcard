import fabric.api
import tempfile
import os

def configure(project_root, host_config):
    remote_root = host_config['remote_root']
    our_config_filename = 'giftcard'
    with fabric.api.cd('/etc/apache2/sites-enabled'):
        current_config_files = set(fabric.api.run('ls -1').splitlines())
        current_config_files.discard(our_config_filename)
        if current_config_files:
            fabric.api.sudo('rm -f ' + ' '.join(current_config_files))
        with tempfile.NamedTemporaryFile() as local_conf:
            local_conf.write(file(os.path.join(project_root, 'apache2.conf')).read().format(remote_root))
            local_conf.flush()
            fabric.api.put(local_conf.name, our_config_filename)
    fabric.api.sudo('rm -f ' + host_config['maintenance_hook'])
    fabric.api.sudo('/etc/init.d/apache2 reload')
