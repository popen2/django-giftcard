import fabric.api
import tempfile
import os

from django.conf import settings

def _ban_msie(protocol, local_project_root, remote_project_root, web_server_config):
    if not web_server_config.get('ban_msie_redirect', None):
        return ''
    return '\n'.join([
        '  if ($http_user_agent ~ MSIE) {',
        '    rewrite ^ {}://{}{} break;'.format(protocol, web_server_config['fqdn'], web_server_config['ban_msie_redirect']),
        '  }',
    ])

# this needs to go at the base level in nginx.conf, not inside the main server
def _fqdn_redirections(protocol, local_project_root, remote_project_root, web_server_config):
    bad_fqdns = web_server_config.get('bad_fqdns', [])
    if not bad_fqdns:
        return ''

    return '\n'.join([
        '\n'.join([
            'server {',
            '  listen 80;',
            '  server_name {};'.format(bad_fqdn),
            '  return 301 {}://{}$request_uri;'.format(protocol, web_server_config['fqdn']),
            '}',
        ])
        for bad_fqdn in bad_fqdns
    ])

def _django_upstream():
    return '\n'.join([
        'upstream django {',
        '  server unix:/tmp/__django.sock;',
        '}',
    ])


def _favicon_redirect(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  location = /favicon.ico {',
        '    access_log off;',
        '    log_not_found off;',
        '    return 301 {}://{}/static/icons/favicon.png;'.format(protocol, web_server_config['fqdn']),
        '  }',
    ])

def _compression(protocol, local_project_root, remote_project_root, web_server_config):
    if not web_server_config.get('compression', False):
        return ''
    return '\n'.join([
        '  gzip on;',
        '  gzip_disable "MSIE[1-6]\.(?!.*SV1)";',
        '  gzip_types text/plain [s]text/html[/s] text/css application/x-javascript text/xml application/xml application/xml+rss text/javascript application/javascript text/x-js;',
    ])

# This needs to go in the supervisor's uwsgi process's environment
def _global_wsgi_configuration(local_project_root, remote_project_root, web_server_config):
    processes = web_server_config['process_number'] if 'process_number' in web_server_config else '4'
    threads = web_server_config['thread_number'] if 'thread_number' in web_server_config else '1'
    return ' '.join([
        '/usr/bin/uwsgi',
        '--socket /tmp/__infinilab.sock',
        '--wsgi-file {}/wsgi.py'.format(remote_project_root),
        '--chmod-socket=666',
        '--processes {}'.format(processes),
        '-T --threads {}'.format(threads),
    ])

def _supervisor_configuration(local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '[program:uwsgi]',
        'autorestart=true',
        'command={}'.format(_global_wsgi_configuration(local_project_root, remote_project_root, web_server_config)),
        'directory={}'.format(remote_project_root),
        'redirect_stderr=true',
        'user=root',
    ])

def _wsgi_configuration(protocol, local_project_root, remote_project_root, web_server_config):
    # all uwsgi configuration done in the supervisor uswgi config file
    return ''

def _static_paths(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '\n'.join([
            '  location {} {{'.format(url),
            '    root {};'.format(abs_path),
            '  }',
            '',
        ])
        for url, abs_path in web_server_config.get('static_paths', [])
    ])

def _virtual_server_prolougue(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  server_name {};'.format(web_server_config['fqdn']),
        '  charset utf-8;',
    ])

def _uwsgi_server(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  location / {',
        '    include     /etc/nginx/uwsgi_params;',
        '    uwsgi_param X-Real-IP $remote_addr;',
        '    uwsgi_param Host $http_host;',
        '    uwsgi_pass  django;',
        '  }',
    ])

def _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        _virtual_server_prolougue(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _ban_msie(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _compression(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _favicon_redirect(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _static_paths(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _uwsgi_server(protocol, local_project_root, remote_project_root, web_server_config),
    ])

def _openssl_config(protocol, local_project_root, remote_project_root, web_server_config):
    def _require_certificate_paths(protocol, local_project_root, remote_project_root, web_server_config):
        # nginx doesn't support location-based HTTPS traffic (see ticket #317)
        return ''

    ssl_config = web_server_config.get('ssl', None)
    if not ssl_config:
        return ''

    lines =  [
      '  ssl on;',
      '  ssl_certificate {};'.format(ssl_config['certificate_file']),
      '  ssl_certificate_key {};'.format(ssl_config['private_key_file']),
      '  ssl_session_timeout  30m;',
    ]

    # There is no certificate chain file in nginx;
    # instead, the certificate chain file should be appended to the ssl_certificate file

    if 'allowed_cas' in ssl_config:
        lines.append('  ssl_client_certificate {};'.format(ssl_config['allowed_cas']))

    lines.append(_require_certificate_paths(protocol, local_project_root, remote_project_root, web_server_config))
    return '\n'.join(lines)

def _gnutls_config(protocol, local_project_root, remote_project_root, web_server_config):
    # nginx doesn't support GnuTLS
    return ''

def _virtual_server_that_redirects(protocol, target_protocol, local_project_root, remote_project_root, web_server_config):
    return '  return 301 {}://{}$request_uri;'.format(target_protocol, web_server_config['fqdn'])

def _virtual_server(protocol, local_project_root, remote_project_root, web_server_config):
    return dict(
        http = '\n'.join([
            'server {',
            '  listen 80;',
            '',
            (_virtual_server_that_redirects(protocol, 'https', local_project_root, remote_project_root, web_server_config)
             if web_server_config.get('ssl', {}).get('only', False) else
             _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config)),
            '}',
        ]),
        https = '\n'.join([
            'server {',
            '  listen 443;',
            '',
            _openssl_config(protocol, local_project_root, remote_project_root, web_server_config),
            '',
            _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config),
            '}',
        ]),
    )[protocol] + '\n'

def _nginx_configuration(local_project_root, remote_project_root, web_server_config):
    configuration_file = '\n'.join([
        _django_upstream(),
        _fqdn_redirections('https', local_project_root, remote_project_root, web_server_config),
        _virtual_server('http', local_project_root, remote_project_root, web_server_config),
        _virtual_server('https', local_project_root, remote_project_root, web_server_config) if web_server_config.get('ssl', None) else '',
    ])

    return configuration_file

def get_configuration_file(local_project_root, host_config):
    web_server_config = host_config['web_server_config']
    remote_project_root = host_config['remote_root']
    configuration_file = '\n'.join([
        '#' * 80,
        '# Supervisor config: /etc/supervisor/conf.d/uwsgi.conf',
        '#' * 80,
        _supervisor_configuration(local_project_root, remote_project_root, web_server_config),
        '#' * 80,
        '# Nginx config: /etc/nginx/sites-enabled/giftcard',
        '#' * 80,
        _nginx_configuration(local_project_root, remote_project_root, web_server_config),
    ])

    return configuration_file

def _update(config_path, config_file):
    our_config_filename = 'giftcard'
    with fabric.api.cd(config_path):
        current_config_files = set(fabric.api.run('ls -1').splitlines())
        current_config_files.discard(our_config_filename)
        if current_config_files:
            fabric.api.sudo('rm -f ' + ' '.join(current_config_files))
        with tempfile.NamedTemporaryFile() as local_conf:
            local_conf.write(config_file)
            local_conf.flush()
            fabric.api.put(local_conf.name, our_config_filename)

def configure(local_project_root, host_config):
    web_server_config = host_config['web_server_config']
    remote_project_root = host_config['remote_root']
    _update('/etc/nginx/sites-enabled',
            _nginx_configuration(local_project_root, remote_project_root, web_server_config))
    _update('/etc/supervisor/conf.d/',
            _supervisor_configuration(local_project_root, remote_project_root, web_server_config))
    fabric.api.sudo('/usr/bin/supervisorctl restart uwsgi')
    fabric.api.sudo('/usr/sbin/nginx -s reload')
