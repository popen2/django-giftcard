from ..base_command import GiftcardCommand, CommandError
import fabric.api

class Command(GiftcardCommand):
    def handle(self, *args, **kwargs):
        from django.conf import settings
        local_project_root = self.find_local_project_root()
        for host in settings.GIFTCARD_HOSTS:
            with fabric.api.settings(host_string=host):
                webserver_handler = self.webserver_handler()
                self._sync_project(local_project_root)
                if webserver_handler:
                    webserver_handler.configure(local_project_root, self.host_config())

    def _sync_project(self, local_project_root):
        remote_root = self.host_config()['remote_root']
        fabric.api.local('rsync -avz --delete {0}/ {1}:{2}'.format(local_project_root, fabric.api.env.host_string, remote_root))
