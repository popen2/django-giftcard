# the skeleton for web server support
# used only when no web server is configured in a host

def _ban_msie(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _fqdn_redirections(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _favicon_redirect(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _compression(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _static_paths(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _virtual_server_prolougue(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _virtual_server_config(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _openssl_config(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _virtual_server_that_redirects(protocol, target_protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def _virtual_server(protocol, local_project_root, remote_project_root, web_server_config):
    return ''

def get_configuration_file(local_project_root, host_config):
    return ''

def configure(local_project_root, host_config):
    pass
