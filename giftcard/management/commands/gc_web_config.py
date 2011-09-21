from ..base_command import GiftcardCommand, CommandError
from django.conf import settings
import fabric.api

class Command(GiftcardCommand):
    def handle(self, *args, **kwargs):
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                webserver_handler = self.webserver_handler()
                print '-' * 80
                print host
                print '-' * 80
                print webserver_handler.get_configuration_file(self.find_local_project_root(), self.host_config())
