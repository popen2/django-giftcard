from django.core.management.base import BaseCommand, CommandError
import fabric.api
import os

class GiftcardCommand(BaseCommand):
    def host_config(self):
        from django.conf import settings
        return settings.GIFTCARD_HOSTS[fabric.api.env.host_string]

    def webserver_handler(self):
        from ..webservers import apache2

        webserver_handlers = dict(
            apache2 = apache2,
        )

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
