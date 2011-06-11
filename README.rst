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
            'maintenance_hook': '/opt/PROJECT_NAME-maintenance', # More on this later...

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
        },
    }

As you can see, ``GIFTCARD_HOSTS`` is a regular dictionary that maps between SSH-like connection strings to their configurations.

``web_server``
    Currently can only be set to ``apache2``. In the future it will be possible to add ``nginx`` and ``lighttpd``.
``remote_root``
    The remote path in which the project will be deployed. Giftcard simply ``rsync``s the contents of the local project root to the remote side.
``maintenance_hook``
    This file is created when launching the ``gc_maintenance`` command and deleted every time the site is deployed.
    When we program our site (or maybe Apache configuration file) to respond to this path, we can have each web server enter maintenance mode before upgrading it, to avoid messy error-500 pages during the upgrade.
``apt_packages``
    List of packages passed directly to ``apt-get`` for installation.
    This configuration is used in the ``gc_install_pkg`` command.
``pip_packages``
    Exactly like ``apt_packages``, but for ``easy_install``.

Apache configuration
--------------------
Giftcard looks for a file named ``apache2.conf`` in the project root (where we placed the ``.giftcard-root`` file.)

This isn't an ordinary Apache configuration file, but a template which required one parameter -- the remote project root.

An example for an Apache configuration file (not the ``{0}`` inside the file, which is where Giftcard will plant the remote project root)::

    <VirtualHost *:80>
      ServerAdmin example
      ServerAlias example.com
    
      DocumentRoot {0}/static
    
      LogLevel warn
    
      WSGIDaemonProcess www-data processes=4 maximum-requests=1024 threads=1
      WSGIProcessGroup www-data
    
      WSGIScriptAlias / {0}/wsgi.py
    
      # Insert filter
      SetOutputFilter DEFLATE
    
      # Netscape 4.x has some problems...
      BrowserMatch ^Mozilla/4 gzip-only-text/html
    
      # Netscape 4.06-4.08 have some more problems
      BrowserMatch ^Mozilla/4\.0[678] no-gzip
    
      # MSIE masquerades as Netscape, but it is fine
      # BrowserMatch \bMSIE !no-gzip !gzip-only-text/html
    
      # NOTE: Due to a bug in mod_setenvif up to Apache 2.0.48
      # the above regex won't work. You can use the following
      # workaround to get the desired effect:
      BrowserMatch \bMSI[E] !no-gzip !gzip-only-text/html
    
      # Don't compress images
      SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$ no-gzip dont-vary
    
      Alias /static/admin "{0}/django/django/contrib/admin/media"
      <Location "/static/admin">
        SetHandler None
      </Location>
    
      Alias /static "{0}/static"
      <Location "/static">
        SetHandler None
      </Location>
    
      Alias /media "{0}/media"
      <Location "/media">
        SetHandler None
      </Location>
    </VirtualHost>

Note that this Apache configuration implies the following:

- Django is contained in our project as a subdirectory (or perhaps a Git submodule).
  This allows us to use different Django versions on the same server, and even change Django and upload it to the production server without packing and distributing anything.
- Our project root contains a script named ``wsgi.py`` which is used by Apache's WSGI module.

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

    ./manage.py gc_install_pkg  # Goes into each server and verifies its packages

    ./manage.py gc_deploy       # Deploying our project, configuring & restarting Apache

    ./manage.py gc_maintenance  # Enter maintenance mode
    # work work work...
    ./manage.py gc_deploy       # Deploy the new site and exit maintenance mode

How does Giftcard know the password to my servers?
--------------------------------------------------
It doesn't.

Giftcard assumes you store your SSH keys in your ``.ssh/config`` per-server.

Fabric uses your stored keys to access your servers. Giftcard doesn't manage your SSH keys because it's contained in your source control and this is rather unsafe.
