from ..base_command import GiftcardCommand, CommandError
import fabric.api

class Command(GiftcardCommand):
    def handle(self, *args, **kwargs):
        from django.conf import settings
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                webserver_handler = self.webserver_handler()
                webserver_handler.enter_maintenance(self.find_local_project_root(), self.host_config())
