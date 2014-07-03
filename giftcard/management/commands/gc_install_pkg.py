from ..base_command import GiftcardCommand, CommandError
import fabric.api

class Command(GiftcardCommand):
    def handle(self, *args, **kwargs):
        for host in self.hosts(args):
            with fabric.api.settings(host_string=host):
                self._upgrade()
                self._install_packages()

    def _upgrade(self):
        '''Install any pending updates (we assume that some cron
        job is doing "apt-get update" once in a while).
        '''
        fabric.api.sudo('apt-get dist-upgrade -y')

    def _install_packages(self):
        host_config = self.host_config()
        fabric.api.sudo('apt-get install -y ' + ' '.join(host_config['apt_packages']))
        fabric.api.sudo('python -m easy_install ' + ' '.join(host_config['pip_packages']))
