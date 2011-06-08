from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import fabric.api
import os
import tempfile

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.project_root = self._find_project_root()
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                config_method = self._get_config_method()
                self._sync_project()
                config_method()

    def host_config(self):
        return settings.GIFTCARD_HOSTS[fabric.api.env.host_string]

    def _get_config_method(self):
        config_methods = dict(
            apache2 = self._configure_apache2,
        )

        web_server = self.host_config()['web_server']
        if web_server not in config_methods:
            raise CommandError('Unknown web_server value {0}. Available configurators are {1}'.format(web_server, config_methods.keys()))

        return config_methods[web_server]

    def _find_project_root(self):
        root = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(root, '.giftcard-root')):
            root = os.path.dirname(root)
            if root in ('', os.path.sep):
                raise CommandError('\n'.join([
                    'Could not find ".giftcard-root".',
                    'Please place this empty file in the project root,'
                    'so giftcard can know where the sync root is.']))
        return root

    def _sync_project(self):
        remote_root = self.host_config()['remote_root']
        fabric.api.local('rsync -avz --delete {0}/ {1}:{2}'.format(self.project_root, fabric.api.env.host_string, remote_root))

    def _configure_apache2(self):
        host_config = self.host_config()
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
