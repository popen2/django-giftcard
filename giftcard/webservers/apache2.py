import fabric.api
import tempfile
import os

from django.conf import settings

def _ban_msie(protocol, local_project_root, remote_project_root, web_server_config):
    if not web_server_config.get('ban_msie_redirect', None):
        return ''
    return '\n'.join([
        '  RewriteCond %{HTTP_USER_AGENT} (MSIE)',
        '  RewriteCond %{REQUEST_URI}     !/static',
        '  RewriteRule ^.*$     {}://{}{} [R]'.format(protocol, web_server_config['fqdn'], web_server_config['ban_msie_redirect']),
    ])

def _fqdn_redirections(protocol, local_project_root, remote_project_root, web_server_config):
    bad_fqdns = web_server_config.get('bad_fqdns', [])
    if not bad_fqdns:
        return ''

    return '\n'.join([
        '  RewriteEngine On',
        ' [OR]\n'.join(['  RewriteCond ${{HTTP_HOST}} {}'.format(bad_fqdn)
                        for bad_fqdn in bad_fqdns]),
        '  RewriteRule ^.*$ {}://{}%{{REQUEST_URI}} [R]'.format(protocol, web_server_config['fqdn']),
    ])

def _favicon_redirect(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  RewriteCond %{REQUEST_URI}     ^/favicon.ico$',
        '  RewriteRule ^.*$     {}://{}/static/icons/favicon.png'.format(protocol, web_server_config['fqdn']),
    ])

def _compression(protocol, local_project_root, remote_project_root, web_server_config):
    if not web_server_config.get('compression', False):
        return ''
    return '\n'.join([
        '  SetOutputFilter DEFLATE',
        '  BrowserMatch ^Mozilla/4 gzip-only-text/html',
        '  BrowserMatch ^Mozilla/4\.0[678] no-gzip',
        '  BrowserMatch \bMSI[E] !no-gzip !gzip-only-text/html',
        '  SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$ no-gzip dont-vary',
    ])

def _global_wsgi_configuration(local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        'WSGIDaemonProcess {} processes=4 maximum-requests=1024 threads=1'.format(web_server_config['unix_user']),
        'WSGIProcessGroup ' + web_server_config['unix_user'],
    ])

def _wsgi_configuration(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  WSGIScriptAlias / {}/wsgi.py'.format(remote_project_root),
    ])

def _static_paths(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '\n'.join([
            '  Alias {} "{}"'.format(url, abs_path),
            '  <Location "{}">'.format(url),
            '    SetHandler None',
            '  </Location>',
        ])
        for url, abs_path in web_server_config.get('static_paths', [])
    ])

def _virtual_server_prolougue(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        '  ServerAdmin ' + settings.ADMINS[0][1],
        '  ServerName ' + web_server_config['fqdn'],
        '  LogLevel warn',
    ])

def _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config):
    return '\n'.join([
        _virtual_server_prolougue(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _ban_msie(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _fqdn_redirections(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _favicon_redirect(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _wsgi_configuration(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _compression(protocol, local_project_root, remote_project_root, web_server_config),
        '',
        _static_paths(protocol, local_project_root, remote_project_root, web_server_config),
    ])

def _require_certificate_paths(protocol, local_project_root, remote_project_root, web_server_config):
    ssl_config = web_server_config.get('ssl', None)
    assert ssl_config # Called from within an SSL context
    return '\n'.join([
        '\n'.join([
            '  <Location "{}">'.format(url),
            '    SSLVerifyClient require',
            '  </Location>',
            ])
        for url in ssl_config.get('require_certificate_paths', [])
    ])

def _ssl_config(protocol, local_project_root, remote_project_root, web_server_config):
    ssl_config = web_server_config.get('ssl', None)
    if not ssl_config:
        return ''
    return '\n'.join([
        '  SSLEngine on',
        '  SSLOptions +StdEnvVars +ExportCertData',
        '  SSLUserName SSL_CLIENT_S_DN',
        '  SSLCertificateFile '      + ssl_config['certificate_file'],
        '  SSLCertificateKeyFile '   + ssl_config['private_key_file'],
        '  SSLCertificateChainFile ' + ssl_config['certificate_chain_file'],
        _require_certificate_paths(protocol, local_project_root, remote_project_root, web_server_config),
    ])

def _virtual_server_that_redirects(protocol, target_protocol, local_project_root, remote_project_root, web_server_config):
    return '   Redirect permanent / {}://{}/'.format(target_protocol, web_server_config['fqdn'])

def _virtual_server(protocol, local_project_root, remote_project_root, web_server_config):
    print web_server_config.get('https_only', None)
    return dict(
        http = '\n'.join([
            '<VirtualHost *:80>',
            (_virtual_server_that_redirects(protocol, 'https', local_project_root, remote_project_root, web_server_config)
             if web_server_config.get('ssl', {}).get('only', False) else
             _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config)),
            '</VirtualHost>',
        ]),
        https = '\n'.join([
            '<VirtualHost *:443>',
            _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config),
            '',
            _ssl_config(protocol, local_project_root, remote_project_root, web_server_config),
            '</VirtualHost>',
        ]),
    )[protocol] + '\n'

def get_configuration_file(local_project_root, host_config):
    web_server_config = host_config['web_server_config']

    remote_project_root = host_config['remote_root']
    configuration_file = '\n'.join([
        _global_wsgi_configuration(local_project_root, remote_project_root, web_server_config),
        _virtual_server('http', local_project_root, remote_project_root, web_server_config),
        _virtual_server('https', local_project_root, remote_project_root, web_server_config) if web_server_config.get('ssl', None) else '',
    ])

    return configuration_file

def enter_maintenance(local_project_root, host_config):
    fabric.api.sudo('touch ' + host_config['maintenance_hook'])
    fabric.api.sudo('/etc/init.d/apache2 reload')

def configure(local_project_root, host_config):
    remote_root = host_config['remote_root']
    our_config_filename = 'giftcard'
    with fabric.api.cd('/etc/apache2/sites-enabled'):
        current_config_files = set(fabric.api.run('ls -1').splitlines())
        current_config_files.discard(our_config_filename)
        if current_config_files:
            fabric.api.sudo('rm -f ' + ' '.join(current_config_files))
        with tempfile.NamedTemporaryFile() as local_conf:
            local_conf.write(get_configuration_file(local_project_root, host_config))
            local_conf.flush()
            fabric.api.put(local_conf.name, our_config_filename)
    fabric.api.sudo('rm -f ' + host_config['maintenance_hook'])
    fabric.api.sudo('/etc/init.d/apache2 reload')
