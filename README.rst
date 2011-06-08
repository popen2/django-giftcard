===============
Django giftcard
===============

What is it?
-----------
Django is an amazing framework for developing web sites, but it lacks proper deployment tools in a built-in manner.
Giftcard is a Django app containing commands for deployment and maintenance of web servers hosting Django a deployment.

Giftcard uses no databases, urls or views. Just commands and settings from your project.

Who is it good for? (and what's with the name?)
-------------------
Giftcard is good for deploying Django sites with no wrapping or packaging, directly from your source directory.
Let's assume you have a Git repo (or SVN, or something else) which contains all of your project files, including its dependencies.
Now, say that you want to deploy that Django project. You'd normally map your dependencies, make sure they're installed on the other side (your production server), and then pack your own project somehow (e.g. easy_install) and sent it over to the server.

This might be nice if you're developing some independent package like 'twisted', but it looks like a lot of work, considering the fact that you already have a local working copy of your site.

This assymetry is exactly what Giftcard comes to solve.

Installation
----------
For this tutorial, we'll assume working with Git, but Giftcard is independent of this.

First, create an empty file called `.giftcard-root` in your project root:

    touch .giftcard-root

Now, add django-giftcard as a submodule (or download and place in your source tree, if not using Git):

    git submodule add git://github.com/popen2/django-giftcard.git django-giftcard

Make sure you've added `$YOUR_PROJECT_ROOT/django-giftcard` to the `$PYTHONPATH` of your project.
The two most common approaches are through `settings.py` or through an entry script wrapping `manage.py`.

Finally, add `giftcard` to your `INSTALLED_APPS`:

    INSTALLED_APPS = [
        ...
        'giftcard',
    ]
