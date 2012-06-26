===============
Django giftcard
===============

What is it?
-----------
Django is an amazing framework for developing web sites, but it lacks proper deployment tools in a built-in manner.
Giftcard is a Django app containing commands for deployment and maintenance of web servers hosting Django as a deployment.

Giftcard uses no databases, urls or views. Just commands and settings from your project.

Who is it good for? (and what's with the name?)
-----------------------------------------------
Giftcard is good for deploying Django sites with no wrapping or packaging required, directly from your source directory.

Let's assume you have a Git repo (or SVN, or something else) which contains all of your project files, including its dependencies.

Now, say that you want to deploy this Django project.
You'd normally map your dependencies, make sure they're installed on the other side (your production server),
and then pack your own project somehow (e.g. easy_install) and sent it over to the server.

This might be nice if you're developing some independent package like ``twisted``, but it looks like a lot of work, considering the fact that you already have a local working copy of your site.

This assymetry is exactly what Giftcard comes to solve.

Installation
------------
For this tutorial, we'll assume working with Git, but Giftcard is independent of this.

First, create an empty file called ``.giftcard-root`` in your project root::

    touch .giftcard-root

Now, add django-giftcard as a submodule (or download and place in your source tree, if not using Git)::

    git submodule add git://github.com/popen2/django-giftcard.git django-giftcard

Make sure you've added ``$YOUR_PROJECT_ROOT/django-giftcard`` to the ``$PYTHONPATH`` of your project.
The two most common approaches are through ``settings.py`` or through an entry script wrapping ``manage.py``.

Next, add ``giftcard`` to your ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        'giftcard',
    ]

Finally, make sure that you have ``fabric`` installed.
You can install it locally on the machine you're deploying from, or as a submodule in your Git repo.
Note that ``fabric`` depends on ``paramiko``, so when adding as a submodule, make sure you install ``paramiko`` as well.

Configuration
-------------
This was easy.
Now, we need to configure Giftcard to be able to work.

Currently Giftcard support installation on Ubuntu servers with Apache-2, but more environments can be easily added.

You can use the following bootstrap configuration by opening your ``settings.py`` file and adding::

    GIFTCARD_HOSTS = {
        'root@www.yourserver.com': {                             # Replace with the user@server of your deployment
            'web_server'      : 'apache2',                       # Currently, only apache2 is supported
            'remote_root'     : '/opt/PROJECT_NAME',             # This is where the project will be deployed

            'apt_packages'    : [                                # List the APT packages your want to install
                'apache2',
                'libapache2-mod-wsgi',
                'libpq-dev',
                'rsync',
                'python-dev',
                'python-pip',
            ],

            'pip_packages'    : [                                # Like apt_packages, but for easy_install
                'psycopg2',
            ],

            'web_server_config': {
                'unix_user': 'www-data',
                'fqdn': 'site.example.com',
                'bad_fqdns': (
                    r'^site$',
                    r'^site\.example$',
                    r'^old-name$',
                    r'^old-name\.old-example$',
                    r'^old-name\.old-example\.org$',
                ),
                'ban_msie_redirect': '/static/no-ie.html',
                'compression': True,
                'ssl' : {
                    'certificate_file': '/opt/ssl/server.crt',
                    'private_key_file': '/opt/ssl/server.key',
                },
                'static_paths': (
                    ('/static/admin', os.path.join('/opt', 'PROJECT_NAME', 'django/django/contrib/admin/static/admin')),
                    ('/static'      , os.path.join('/opt', 'PROJECT_NAME', 'static')),
                    ('/media'       , os.path.join('/opt', 'PROJECT_NAME', 'media')),
                ),
            },
        },
    }

As you can see, ``GIFTCARD_HOSTS`` is a regular dictionary that maps between SSH-like connection strings to their configurations.

``web_server``
    Currently can only be set to ``apache2``. In the future it will be possible to add ``nginx`` and ``lighttpd``.
``remote_root``
    The remote path in which the project will be deployed. Giftcard simply ``rsync``s the contents of the local project root to the remote side.
``apt_packages``
    List of packages passed directly to ``apt-get`` for installation.
    This configuration is used in the ``gc_install_pkg`` command.
``pip_packages``
    Exactly like ``apt_packages``, but for ``easy_install``.

``web_server_config`` holds the following:
    ``unix_user`` is the UNIX username that should own the web server.
    ``fqdn`` is the fully qualified domain name, in our example it is site.example.com .
    ``bad_fqdns`` is a list/tuple of all FQDN's we want to redirect to our actual FQDN. In our example, we ban site, site.example and some old URL's users have gotten used to, like old-name.old-example.org. This is useful after an FQDN change to help users get used to the new FQDN, or when users in the local network surf to URL's without their DNS suffix, and then copy-paste them to WAN users.
    ``ban_msie_redirect`` is a hook that allows blocking Microsoft Internet Explorer by redirecting any MSIE browsers to an explicit page, usually recommending the user to upgrade to a browser software, rather than MSIE which is not a browser.
    ``ssl``, when exists in the configuration, makes Giftcard generate appropriate configuration for listening on port 443 and respecting SSL.
    ``static_paths`` is the configuration for static files.

Apache configuration
--------------------
The configuration for the webserver is automatically generated.
At the moment it's not possible to manually extend the configuration. However, it is rather easy to add new configuration options in 'web_server_config' and respond to them for each web server.

Note that the generated configuration assumes to be running on the WSGI plugin, and that our project root contains a script named ``wsgi.py``.

Sample wsgi.py
--------------
To Complete Apache's configuration, we'll use this ``wsgi.py`` file::

    #!/usr/bin/env python2.7
    import os
    import sys
    
    HERE = os.path.dirname(__file__)
    
    for library in file(os.path.join(HERE, 'LIBS')).read().splitlines():
        sys.path.append(os.path.join(HERE, library))
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'
    
    import django.core.handlers.wsgi
    application = django.core.handlers.wsgi.WSGIHandler()

Executing it
------------
That's it.

Now we can finally use some commands::

    ./manage.py gc_web_config   # Show the configuration file to be generated for each server

    ./manage.py gc_install_pkg  # Goes into each server and verifies its packages

    ./manage.py gc_deploy       # Deploying our project, configuring & restarting Apache

How does Giftcard know the password to my servers?
--------------------------------------------------
It doesn't.

Giftcard assumes you store your SSH keys in your ``.ssh/config`` per-server.

Fabric uses your stored keys to access your servers. Giftcard doesn't manage your SSH keys because it's contained in your source control and this is rather unsafe.
