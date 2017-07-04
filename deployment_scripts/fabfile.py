"""

Available commands:
    create_instance           Creates a new EC2 instance
    deploy                    Deploy the scrapy server to EC2 instances
    file_transfer             Transfer files from local machine to remote EC2 instances
    install_dependencies      Downloads and configures all dependencies
    set_hosts                 Gets the list of all available hosts
    setup_git_repo            Clones the repo from github and installs the required package
    start_scrapyd             Starts the scrapy server
    production                Set up the production env


Examples:
    - fab production instance
        - Creates a new EC2 instance form a blank AMI image.

    - fab production deploy
        - Deploy the scrapy server to EC2 instances

"""
import config
import time

from fabric.api import env, run, cd, put, abort, prompt

from aws import AWS
from notifications import Notification


def create_instance():
    """
    Creates an EC2 instance from an AMI and configures it based on config.py.
    """
    env.host_string = _create_instance()


def deploy():
    """
    Public function that deploys a fresh scrapy server to an EC2 instance.
    """
    env.release_stamp = time.strftime('%Y%m%d%H%M%S')
    set_hosts()
    install_dependencies()
    setup_git_repo()
    start_scrapyd()


def file_transfer(localpath, remotepath):
    put(localpath, remotepath, use_sudo=True)
    Notification('Successfully transferring configs file from local to remote machines').info()



def install_dependencies():
    """
    Public function that install all dependencies
    """
    Notification('Installing dependencies').info()
    run('sudo apt-get -yqq update', env.hosts)
    run('sudo apt-get -yqq install git dtach python-pip  \
        libpq-dev python-dev libxml2-dev libxslt1-dev  \
        libldap2-dev libsasl2-dev libffi-dev', env.hosts)


def set_hosts():
    """
    Get the list of running EC2 instances from AWS
    """
    env.hosts = _get_all_instances()


def setup_git_repo():
    """
    Public function that clones the project from git, installs all requirements.txt
    and transfer the config files from local machine over to host machines
    """
    # Clone the repo from github and install the required packages
    repo = 'https://github.com/pvt88/scrapy-cloud.git'
    Notification('Cloning the project from {}'.format(repo)).info()
    run('git clone ' + repo, env.hosts)
    run('sudo pip install -q -r scrapy-cloud/requirements.txt', env.hosts)

    # Transfer the local resource files to the remote machines
    local = '~/scrapy-cloud/cobweb/resources/'
    remote = 'scrapy-cloud/cobweb'
    file_transfer(localpath=local, remotepath=remote)


def start_scrapyd():
    """
    Public function that start a scrapy server
    """
    with cd('scrapy-cloud'):
        _runbg('scrapyd')

    Notification('Successfully launch a scrapy server at {}:6800'.format(env.host_string)).info()


def production():
    _base_environment_settings()
    env.branch = "master"
    env.environment = 'production'


def _base_environment_settings():
    """
    Common environment variables.
    """
    env.release_stamp = time.strftime('%Y%m%d%H%M%S')
    env.connection_attempts = 3

    env.ec2_region = config.EC2_REGION
    env.ec2_ami = config.EC2_AMI
    env.ec2_instance = config.EC2_INSTANCE
    env.ec2_security_group = config.EC2_SECURITY_GROUP

    env.user = config.USER
    env.aws_key_name = config.KEY_NAME
    env.key_filename = config.KEY_PATH
    env.aws_access_key = config.EC2_AWS_ACCESS_KEY
    env.aws_secret_key = config.EC2_AWS_SECRET_KEY


def _create_instance():
    """
    Creates a new EC2 Instance using boto.
    """
    try:
        connection = AWS(access_key=env.aws_access_key, secret_key=env.aws_secret_key, region=env.ec2_region).connect()
    except Exception:
        Notification("Could not connect to AWS").error()
        abort("Exited!")

    aws_ami = prompt("Hit enter to use the default Ubuntu AMI or enter one:", default=env.ec2_ami)
    aws_security_groups = prompt("Enter the security group (must already exist)?", default=env.ec2_security_group)
    aws_instance_type = prompt("What instance type do you want to create? ", default=env.ec2_instance)
    aws_instance_key_name = prompt("Enter your key pair name (don't include .pem extension)", default=env.aws_key_name)

    BUILD_SERVER = {
        'image_id': aws_ami,
        'instance_type': aws_instance_type,
        'security_groups': [aws_security_groups],
        'key_name': aws_instance_key_name
    }

    Notification('Spinning up the instance...').info()

    # Create new instance using boto.
    reservation = connection.run_instances(**BUILD_SERVER)
    instance = reservation.instances[0]
    time.sleep(5)
    while instance.state != 'running':
        time.sleep(5)
        instance.update()
        Notification('-Instance state: %s' % instance.state).info()

    Notification('Instance %s was created successfully' % instance.id).info()
    # A new instance take a little while to allow connections so sleep for x seconds.
    Notification('Sleeping for %s seconds before attempting to connect...' % 30).info()
    time.sleep(30)

    return instance.public_dns_name

def _get_all_instances():
    try:
        connection = AWS(access_key=env.aws_access_key, secret_key=env.aws_secret_key, region=env.ec2_region).connect()
    except Exception:
        Notification("Could not connect to AWS").error()
        abort("Exited!")

    instances = []
    for reservation in connection.get_all_instances(
            filters={'key-name': env.aws_key_name, 'instance-state-name': 'running'}):
        for host in reservation.instances:
            # build the user@hostname string for ssh to be used later
            instances.append('ubuntu@' + str(host.public_dns_name))

    Notification('Getting {} instances:\n{}'.format(len(instances), "\n".join(instances))).info()

    return instances

def _runbg(cmd):
    return run('dtach -n `mktemp -u /tmp/dtach.XXXX` %s' % (cmd), env.hosts)