#!/usr/bin/python

# add this to install script                                                                        # insert this where startup-script is set

import os                                                                                           # adds access to os.system

import subprocess                                                                                   # allows cpu spawn new processes, connect to their input/output/error pipes, and obtain their return codes

import re



print ('********** Setting up user django**********')                                               # log messaging
os.system ('adduser -M django' + \
    '&& usermod -L django' + \
    '&& chown - R django')                                                                          # add django as apache user and set permissions



def local_repo():
    repo="""[local-epel]

name=NTI300 EPEL
baseurl=http://35.193.67.158/epel/
gpgcheck=0
enabled=1"""

    os.system('for file in $( ls /etc/yum.repos.d/ ); do mv /etc/yum.repos.d/$file /etc/yum.repos.d/$file.bak; done')
    print(repo)
    with open("/etc/yum.repos.d/local-repo.repo","w+") as f:
      f.write(repo)
    f.close()
    
local_repo()

def setup_install():

    print ('********** installing pip & virtualenv so we can give django its own ver of python**********')    # log messaging

    os.system('yum -y install python-pip httpd mod_wsgi && pip install --upgrade pip')              # install python httpd mod_wsgi and then upgrade python to latest version
    os.system('pip install virtualenv')                                                             # install virual environemtn manager
    os.chdir('/opt')                                                                                # change to the directory created during install
    os.mkdir('/opt/django')                                                                         # create a directory for django virtualenv
    os.chdir('/opt/django')                                                                         # change to that directory
    os.system('virtualenv django-env')                                                              # set-up the virutal environment
    os.system('chown -R django /opt/django')                                                        # set the owner/permissions for the directory of the django ve

    

def django_install():

    print ('********** activating virtualenv & django **********')            # log messaging
    os.system('source /opt/django/django-env/bin/activate ' + \
        '&& pip install django')                                                          # activate virtual environment and install django
    os.chdir('/opt/django')                                                              # change to the djangodirectory
    os.system('source /opt/django/django-env/bin/activate ' + \
        '&& django-admin --version ' + \
        '&& django-admin startproject project1')                                       # activate, log version of django, set-up new project, "project1"



def django_start():

    print('**********starting django**********')                                           # log messaging
    os.system('chown -R django /opt/django')                                               # set ownership/permissions for directories and sub directories
    os.chdir('/opt/django/project1')                                                       # change to the proejct directory
    os.system('source /opt/django/django-env/bin/activate ' + \
        '&& python manage.py migrate')                                                    # activate pythone and migrate to the project
    os.system('source /opt/django/django-env/bin/activate ' + \
        '&& echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\'admin\', \'admin@newproject.com\', \'pw123456\')" | python manage.py shell')

                                                                                        # this line sets-up admin user

    outputwithnewline = subprocess.check_output('curl -s checkip.dyndns.org | sed -e \'s/.*Current IP Address: //\' -e \'s/<.*$//\'',shell=True)

                                                                                      # capture IP Address in a string var

    print('**********project1/settings.py **********')
    print outputwithnewline                                                                    
    output = outputwithnewline.replace("\n", "")                             
    old_string = "ALLOWED_HOSTS = []"                                                         # set var with old value of allowed hosts line
    new_string = 'ALLOWED_HOSTS = [\'{}\']'.format(output)                                    # set var with new value of allowed hosts line
    print (new_string)                                                                         # log the new string value
    print (old_string)                                                                         # log the old stringvalue

    

    with open('project1/settings.py') as f:
        newText=f.read().replace(old_string, new_string)                                            # open settings.py and replace the old value with the new value
    with open('project1/settings.py', "w") as f:
        f.write(newText)                                                                            # write the updated settings.py file
    with open('project1/settings.py') as f:
        f.close()                                                                                   # close the settings.py file

    os.system('sudo -u django sh -c "source /opt/django/django-env/bin/activate && python manage.py runserver 0.0.0.0:8000&"')

                                                                                                    # activate and start pytho
def setup_mod_wsgi():

    os.chdir('/opt/django/project1')                                                   # change into the project1 directory
    # update settings.py
    new_string = 'STATIC_ROOT = os.path.join(BASE_DIR, "static/")' + '\n'                           # define the new line
    print (new_string)                                                                              # log to the new value



    with open('project1/settings.py', "a") as f:                                                    # open file for append
        f.write(new_string)                                                                         # append the new line
    with open('project1/settings.py') as f:                                                         # close the file
        f.close()

    print('********** settings.py updated**********')
    # updates the django.conf file for httpd
    # defines django.conf file content as an array
    django_config_file = [

        'Alias /static /opt/django/project1/static/',
        '<Directory /opt/django/project1/static/>',
        '    Require all granted',
        '</Directory>',
        '<Directory /opt/django/project1/project1>',
        '    <Files wsgi.py>',
        '        Require all granted',
        '    </Files>',
        '</Directory>',
        'WSGIDaemonProcess project1 python-path=/opt/django/project1:/opt/django/django-env/lib/python2.7/site-packages/',
        'WSGIProcessGroup project1',
        'WSGIScriptAlias / /opt/django/project1/project1/wsgi.py'
        ]

    f = open('/etc/httpd/conf.d/django.conf',"w+")                                            # Create it if it does not exist
    i = 0                                                                                     # set i to zero to start the while loop at the begining of the content array
    while i < len(django_config_file):                                                        # do while until the array is fully processed
        newLine = django_config_file[i] + '\n'                                                # assign new line the value of the current array item and add eol indicator
        with open('/etc/httpd/conf.d/django.conf', "a") as f:                                 # open & append the file to 
                f.write(newLine)                                                              # write new line
        with open('/etc/httpd/conf.d/django.conf') as f:                                      # close the file
                f.close()
        i += 1                                                                             # start toincrement the loop counter

    print('********** django.conf updated**********')
    os.system('usermod -a -G django apache')                                                  # setup the django group
    os.system('chmod 710 /opt/django')
    os.system('chmod 664 /opt/django/project1/db.sqlite3')
    os.system('chown :apache /opt/django/project1/db.sqlite3')
    os.system('chown :apache /opt/django')
    os.system('systemctl start httpd')
    os.system('systemctl enable httpd')                                                       # start & enable HTTPD services





# run the install and start functions

setup_install()
django_install()
django_start()    
setup_mod_wsgi()

print ('********** django.py cloud install complete**********')                          # log completion of install
