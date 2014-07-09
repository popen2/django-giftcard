from django.core.management.base import BaseCommand, CommandError
import fabric.api
import os

class GiftcardCommand(BaseCommand):
    args = '<hosts environments ...>'

    def hosts(self, args):
        from django.conf import settings
        all_hosts = settings.GIFTCARD_HOSTS
        if not args:
            return all_hosts
        hosts = []
        try:
            for env in args:
                if env in settings.GIFTCARD_ENVS:
                    for host in settings.GIFTCARD_ENVS[env]:
                        if host in all_hosts and host not in hosts:
                            hosts.append(host)
        except:
            # no environments
            pass
        for host in args:
            if host in all_hosts and host not in hosts:
                hosts.append(host)
        return hosts

    def host_config(self):
        from django.conf import settings
        return settings.GIFTCARD_HOSTS[fabric.api.env.host_string]

    def webserver_handler(self):
        from ..webservers import apache2, nginx, default

        webserver_handlers = dict(
            nginx = nginx,
            apache2 = apache2,
        )

        if 'web_server' not in self.host_config():
            return default
        web_server = self.host_config()['web_server']
        if web_server not in webserver_handlers:
            raise CommandError('Unknown web_server value {0}. Available configurators are {1}'.format(web_server, webserver_handlers.keys()))

        return webserver_handlers[web_server]

    def find_local_project_root(self):
        root = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(root, '.giftcard-root')):
            root = os.path.dirname(root)
            if root in ('', os.path.sep):
                raise CommandError('\n'.join([
                    'Could not find ".giftcard-root".',
                    'Please place this empty file in the project root,'
                    'so giftcard can know where the sync root is.']))
        return root
