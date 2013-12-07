from fabric.api import *
from fabric.contrib.files import upload_template, append

import config

@task
def setup_agep_vm():
    """Setup a new agep VM [$AG:NeedKomUser][$AG:NeedSudo]"""
    execute(install_apache)
    execute(install_php)
    execute(create_folders)
    execute(upload_default_page)
    execute(set_user_rights)
    execute(configure_apache)
    execute(add_mysql_host)
    execute(configure_logrotate)
    execute(restart_apache)

    if hasattr(env, 'fab_addsudo') and env.fab_addsudo == 'True':
        execute(allow_sudo_user)


@task
def install_apache():
    """Install apache"""
    sudo('apt-get install -y apache2')


@task
def install_php():
    """Install php"""
    sudo('apt-get install -y php5 libapache2-mod-php5 php5-cli php5-curl php5-dev php5-gd php5-ldap php5-mcrypt php5-mysql php5-odbc php5-pgsql')


@task
def restart_apache():
    """Restart apache"""
    sudo('service apache2 restart')


@task
def configure_apache():
    """Configure apache  [$AG:NeedKomUser]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    # Disable default site
    sudo('a2dissite 000-default')

    # Copy config
    upload_template('files/agep/apache.conf', '/etc/apache2/sites-available/apache.conf',  {'user': env.fab_komuser})

    # Enable config
    sudo('a2ensite apache.conf', pty=True)

    sudo('a2enmod rewrite')


@task
def configure_logrotate():
    """Configure logrotate to rotate apachelogs"""
    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    sudo('echo -e "/home/' + env.fab_komuser + '/logs/*.log $(cat /etc/logrotate.d/apache2)" > /etc/logrotate.d/apache2')


@task
def allow_sudo_user():
    """Allow kom user to use sudo [$AG:NeedKomUser]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return
    
    sudo('adduser ' + env.fab_komuser + ' sudo')


@task
def upload_default_page():
    """Upload the default webpage. [$AG:NeedKomUser]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    upload_template('files/agep/index.html', '/home/' + env.fab_komuser + '/public_html/index.html', {
            'vm_name':  env.fab_komuser + '.agepoly.ch',
        }, use_sudo=True)


@task
def create_folders():
    """Create folders [$AG:NeedKomUser]"""
    
    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    sudo('mkdir /home/' + env.fab_komuser + '/public_html/')
    sudo('mkdir /home/' + env.fab_komuser + '/logs/')


@task
def add_mysql_host():
    """Add the mysql host"""
    append('/etc/hosts', config.MYSQL_HOST + ' mysql')

@task
def set_user_rights():
    """Set user rights to access everything he needs [$AG:NeedKomUser]"""
    
    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    sudo('chown -R ' + env.fab_komuser + ':www-data /home/' + env.fab_komuser + '/public_html/')
    sudo('chown -R ' + env.fab_komuser + ':www-data /home/' + env.fab_komuser + '/logs/')


@task
def setup_mysql():
    """Setup the mysql database and user [$AG:NeedKomUser][$AG:NeedMysqlPassword][$AG:NeedSrvIp]"""
    with hide('running'):
        execute(create_mysql_database)
        execute(add_mysql_user)
        execute(add_mysql_rights)
        execute(reload_mysql_rights)


def mysql_execute(sql):
    """Executes passed sql command using mysql shell."""

    sql = sql.replace('"', r'\"')
    return run('echo "%s" | mysql --user="%s" --password="%s"' % (sql, config.MYSQL_USER, config.MYSQL_PASSWORD))

@task
def create_mysql_database():
    """Create a new mysql database [$AG:NeedKomUser]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return
    
    mysql_execute("CREATE DATABASE %s DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;" % (env.fab_komuser,))

@task
def add_mysql_user():
    """Add mysql user [$AG:NeedKomUser][$AG:NeedMysqlPassword][$AG:NeedSrvIp]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    if not hasattr(env, 'fab_mysqlpassword') or env.fab_mysqlpassword == '':
        return

    if not hasattr(env, 'fab_srvip') or env.fab_srvip == '':
        return
    
    mysql_execute("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" % (env.fab_komuser, env.fab_srvip, env.fab_mysqlpassword))

@task
def add_mysql_rights():
    """Add mysql rights [$AG:NeedKomUser][$AG:NeedSrvIp]"""

    if not hasattr(env, 'fab_komuser') or env.fab_komuser == '':
        return

    if not hasattr(env, 'fab_srvip') or env.fab_srvip == '':
        return
    
    mysql_execute("GRANT ALL ON %s.* TO '%s'@'%s';" % (env.fab_komuser, env.fab_komuser, env.fab_srvip))

@task
def reload_mysql_rights():
    """Reload mysql rights"""
    
    mysql_execute("FLUSH PRIVILEGES;")