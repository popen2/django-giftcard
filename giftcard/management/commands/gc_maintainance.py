from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import fabric.api
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                config_method = self._get_config_method()
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

    def _configure_apache2(self):
        fabric.api.sudo('touch ' + self.host_config()['maintenance_hook'])
        fabric.api.sudo('/etc/init.d/apache2 reload')
