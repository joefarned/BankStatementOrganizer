# -*- coding: utf-8 -*-

"""
Handles deploying the website to production server.
"""

import datetime

from fabric.api import local, cd, sudo
from fabric.colors import green, red
from fabric.operations import put, prompt
from contextlib import contextmanager

# Import project settings
try:
    from fabconfig import *
except ImportError:
    import sys
    print "You need to define a fabconfig.py file with your project settings"
    sys.exit()


@contextmanager
def shell_env(**env_vars):
    orig_shell = env['shell']
    env_vars_str = ' '.join('{0}={1}'.format(key, value) for key, value in env_vars.items())
    env['shell'] = '{0} {1}'.format(env_vars_str, orig_shell)
    yield
    env['shell'] = orig_shell


def input_with_default(prompt, default, pwd=False):
    if pwd:
        x = getpass.getpass("%s (%s): " % (prompt, default))
    else:
        x = raw_input("%s (%s): " % (prompt, default))
    if not x:
        return default
    return x


def _get_commit_id():
    """
    Return the commit ID for the branch about to be deployed
    """
    return local('git rev-parse HEAD', capture=True)[:20]


def notify(msg):
    bar = '+' + '-' * (len(msg) + 2) + '+'
    print green('')
    print green(bar)
    print green("| %s |" % msg)
    print green(bar)
    print green('')


# Setup tasks


def config():
    project_domain = input_with_default("Project Domain", "localhost")
    project_server_auth = input_with_default("Project Server/Auth", "root@localhost")

    with open('fabconfig.py', 'r+') as f:
        new_fabconfig = f.read().replace('[[ PROJECT_DOMAIN ]]', project_domain).replace('[[ PROJECT_SERVER_AUTH ]]', project_server_auth)
        f.seek(0)
        f.write(new_fabconfig)
        f.truncate()

    with open('pava/deploy/nginx.conf', 'r+') as f:
        new_nginx = f.read().replace('[[ PROJECT_DOMAIN ]]', project_domain)
        f.seek(0)
        f.write(new_nginx)
        f.truncate()

    with open('pava/settings.py', 'r+') as f:
        new_default_conf = f.read().replace('[[ PROJECT_DOMAIN ]]', project_domain)
        f.seek(0)
        f.write(new_default_conf)
        f.truncate()

    print green("All set up!")


# Deployment tasks


def deploy():
    notify('Deploying to %s' % env.hosts)
    current = _get_commit_id()[0:7]
    env.version = prompt(red('Choose tag/commit to build from (%s): ' % current))
    if env.version is '':
        env.version = current

    pack()
    deploy_code(env.build_file)

    update_virtualenv()
    migrate()
    compress_files()
    install_cron()
    deploy_nginx_config()

    switch_symlink()

    reload()
    delete_old_builds()


def deploy_lite():
    notify('Deploying to %s' % env.hosts)
    env.version = _get_commit_id()[0:7]
    pack()
    deploy_code(env.build_file)
    migrate()
    compress_files()

    switch_symlink()
    reload_lite()
    delete_old_builds()


def reload():
    reload_python_code()
    reload_nginx()
    enable()


def reload_lite():
    sudo('touch %(enabled_wsgi)s' % env)


# Deployment subtasks


def pack():
    notify("Building from refspec %s" % env.version)
    env.build_file = '/tmp/build-%s.tar.gz' % str(env.version)
    local('git archive --format tar %s requirements.txt manage.py Procfile %s | gzip > %s' % (env.version, env.web_dir, env.build_file))

    now = datetime.datetime.now()
    env.build_dir = '%s-%s' % (env.build, now.strftime('%Y-%m-%d-%H-%M'))
    env.code_dir = '%s/%s' % (env.builds_dir, env.build_dir)


def upload(local_path, remote_path=None):
    """
    Uploads a file
    """
    if not remote_path:
        remote_path = local_path
    notify("Uploading %s to %s" % (local_path, remote_path))
    put(local_path, remote_path)


def unpack(archive_path):
    notify('Unpacking files')
    sudo('mkdir -p %(builds_dir)s' % env)
    with cd(env.builds_dir):
        # Create new build folder
        sudo('if [ -d "%(build_dir)s" ]; then rm -rf "%(build_dir)s"; fi' % env)
        sudo('mkdir -p %(build_dir)s' % env)
        sudo('tar xzf %s -C %s' % (archive_path, env.build_dir))

        # Add file indicating Git commit
        sudo('echo -e "refspec: %s\nuser: %s" > %s/build-info' % (env.version, env.user, env.build_dir))

        # Remove archive
        sudo('rm %s' % archive_path)


def deploy_code(archive_file):
    upload(archive_file)
    unpack(archive_file)


def create_virtualenv():
    """
    create venv if it doesn't exist
    """
    notify('Creating venv')

    sudo('mkdir -p %(builds_dir)s' % env)
    with cd(env.project_dir):
        sudo('/usr/bin/virtualenv --no-site-packages --distribute venv')


def update_virtualenv():
    """
    Install the dependencies in the requirements file
    """
    notify('Updating venv')

    with cd(env.code_dir):
        sudo('source %s/bin/activate && pip install -r requirements.txt' % env.virtualenv)


def migrate():
    """
    Apply any schema alterations
    """
    notify("Applying database migrations")
    with cd(env.code_dir):
        with shell_env(DJANGO_CONFIGURATION='Prod'):
            sudo('source %s/bin/activate && ./manage.py migrate --noinput > /dev/null' % env.virtualenv)


def compress_files():
    """
    run compressor
    """
    notify("compressing files")
    with cd(env.code_dir):
        with shell_env(DJANGO_CONFIGURATION='Prod'):
            sudo('source %s/bin/activate && ./manage.py compress --force' % env.virtualenv)


def install_cron():
    with cd(env.code_dir):
        sudo('%s/deploy/cron.d/install.sh' % env.project_code)


def switch_symlink():
    notify("Switching symlinks")
    with cd(env.project_dir):
        # Create new symlink for build folder
        sudo('if [ -h current ]; then unlink current; fi' % env)
        sudo('ln -s %(builds_dir)s/%(build_dir)s current' % env)


def deploy_nginx_config():
    notify('Moving nginx config into place')
    with cd(env.code_dir):
        sudo('mv %(nginx_conf)s /data/etc/nginx/conf.d/%(project_code)s.conf' % env)


def reload_python_code():
    notify('Touching WSGI file to reload python code')
    with cd(env.builds_dir):
        sudo('if [ -h %(available_wsgi)s ]; then unlink %(available_wsgi)s; fi' % env)
        sudo('ln -s %(project_dir)s/current/%(wsgi)s %(available_wsgi)s' % env)
        sudo('touch %(available_wsgi)s' % env)


def reload_nginx():
    notify('Reloading nginx configuration')
    sudo('service nginx force-reload')


def delete_old_builds():
    notify('Deleting old builds')
    with cd(env.builds_dir):
        sudo('find . -maxdepth 1 -type d -name "%(build)s*" | sort -r | sed "1,9d" | xargs rm -rf' % env)


def enable():
    """
    gets uwsgi to reload python code
    """
    notify('Enabling app')
    sudo('if [ ! -f %(enabled_wsgi)s ]; then ln -s %(available_wsgi)s %(enabled_wsgi)s; fi' % env)
    sudo('touch %(enabled_wsgi)s' % env)
