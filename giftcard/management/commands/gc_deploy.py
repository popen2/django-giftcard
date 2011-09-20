from ...webservers import apache2
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import fabric.api
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.project_root = self._find_project_root()
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                webserver_config_method = self._get_webserver_config_method()
                self._sync_project()
                webserver_config_method(self.project_root, self.host_config())

    def host_config(self):
        return settings.GIFTCARD_HOSTS[fabric.api.env.host_string]

    def _get_webserver_config_method(self):
        webserver_config_methods = dict(
            apache2 = apache2.configure,
        )

        web_server = self.host_config()['web_server']
        if web_server not in webserver_config_methods:
            raise CommandError('Unknown web_server value {0}. Available configurators are {1}'.format(web_server, webserver_config_methods.keys()))

        return webserver_config_methods[web_server]

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
