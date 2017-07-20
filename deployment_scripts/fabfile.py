"""

Available commands:
    create_instance           Creates a new EC2 instance
    deploy                    Deploy the scrapy server to EC2 instances
    file_transfer             Transfer files from local machine to remote EC2 instances
    install_dependencies      Downloads and configures all dependencies
    get_hosts                 Gets the list of all available hosts dynamically
    kill_scrapyd              Kills the scrapy server
    production                Set up the production env
    local                     Set up the local env
    start_scrapyd             Starts the scrapy server


Examples:
    - fab production create_instance
        - Creates a new EC2 instance form a blank AMI image.

    - fab production get_hosts deploy
        - Deploy the scrapy server to EC2 instances

"""
import config
import time

from fabric.contrib.files import exists
from fabric.api import *

from aws import AWS
from notifications import Notification

GITHUB_URL = 'https://github.com/'
GITHUB_USER = 'pvt88/'
GITHUB_REPO = 'scrapy-cloud'
TEMP_SLEEP = 15


def create_instance(num_instances=1):
    """
    Creates an EC2 instance from an AMI and configures it based on config.py.
    """
    env.host_string = _create_instance(num_instances)


@parallel
def deploy():
    """
    Public function that deploys a fresh scrapy server to an EC2 instance.
    """
    env.release_stamp = time.strftime('%Y%m%d%H%M%S')
    install_dependencies()

    # Clone the repo from github and install the required packages
    _init_git()
    _install_requirements()

    # Transfer the local resource files to the remote machines
    local = '~/scrapy-cloud/cobweb/resources/'
    remote = 'scrapy-cloud/cobweb'
    file_transfer(localpath=local, remotepath=remote)

    # Start the scrapyd
    start_scrapyd()
    # Deploy the target
    scrapyd_deploy()


def file_transfer(localpath, remotepath):
    """
    Transfer files from local machine to remote EC2 instances
    """
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


def re_deploy():
    """
    Public function that re deploys the scrapy server to EC2 instances.
    """
    env.release_stamp = time.strftime('%Y%m%d%H%M%S')
    _update_git()
    _install_requirements()

    kill_scrapyd()
    time.sleep(10)
    start_scrapyd()
    scrapyd_deploy()


def get_hosts():
    """
    Get the list of running EC2 instances from AWS
    """
    env.hosts = _get_all_instances()


def start_scrapyd():
    """
    Public function that start a scrapy server
    """
    with cd(GITHUB_REPO):
        _runbg('scrapyd')

    Notification('Successfully launch a scrapy server at {}:6800'.format(env.host_string)).info()

def scrapyd_deploy():
    """
    Public function that start a scrapy server
    """
    with cd(GITHUB_REPO):
        run('scrapyd-deploy local-target')

    Notification('Successfully launch a scrapy server at {}:6800'.format(env.host_string)).info()

def scrapyd_deploy():
    """
    Public function that start a scrapy server
    """
    with cd(GITHUB_REPO):
        run('scrapyd-deploy local-target')

    Notification('Successfully deploy the target!').info()


def kill_scrapyd():
    """
    Public function that kill a scrapy server
    """
    with settings(warn_only=True):
        if env.environment == 'development':
            local('sudo kill `sudo lsof -t -i:6800`')
        else:
            run('sudo kill `sudo lsof -t -i:6800`', env.hosts)

        Notification('Successfully kill a scrapy server!').info()


def deploy_local_scrapyd():
    with cd(GITHUB_REPO):
        with prefix('. /usr/local/bin/virtualenvwrapper.sh; workon scrapy'):
            _runbg('scrapyd')
            Notification('Successfully launch a local scrapy server!').info()
            local('scrapyd-deploy local-target')

    Notification('Sleeping for {} seconds before attempting to deploy spider...'.format(TEMP_SLEEP)).info()
    time.sleep(TEMP_SLEEP)


def deploy_local_spider():
    with lcd('~/' + GITHUB_REPO + '/cobweb'):
        for spider_config in env.spider_configs:
            for type, urls in spider_config['crawl_urls'].items():
                for url in urls:
                    response = _curl(spider_config['spider'],
                                     spider_config['max_depth'],
                                     spider_config['vendor'],
                                     type,
                                     url,
                                     spider_config['start_index'])
                    Notification('Deploy spider with response={}'.format(response)).info()
                    time.sleep(5)

def production():
    _base_environment_settings()
    env.branch = "master"
    env.environment = 'production'


def development():
    _base_environment_settings()
    env.environment = 'development'

    env.spider_configs = config.SPIDER_CONFIGS


def _curl(spider, max_depth, vendor, type, crawl_url, start_index):
    return local('curl http://localhost:6800/schedule.json \
                        -d project=cobweb \
                        -d spider={} \
                        -d max_depth={} \
                        -d vendor={} \
                        -d type={} \
                        -d crawl_url={} \
                        -d start_index={}'.format(spider, max_depth, vendor, type, crawl_url, start_index)
                 , capture=True)


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


def _create_instance(num_instances=1):
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

    BUILD_SERVER = dict(image_id=aws_ami,
                        instance_type=aws_instance_type,
                        security_groups=[aws_security_groups],
                        key_name=aws_instance_key_name)

    Notification('Spinning up the instances...').info()

    # Create new instance using boto.
    for _ in range(int(num_instances)):
        reservation = connection.run_instances(**BUILD_SERVER)
        instance = reservation.instances[0]
        time.sleep(5)
        while instance.state != 'running':
            time.sleep(5)
            instance.update()
            Notification('-Instance {} is {}'.format(instance.id, instance.state)).info()

    # A new instance take a little while to allow connections so sleep for x seconds.
    Notification('Sleeping for {} seconds before attempting to connect...'.format(TEMP_SLEEP)).info()
    time.sleep(TEMP_SLEEP)

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

    Notification('Got {} instances:\n{}'.format(len(instances), "\n".join(instances))).info()

    return instances


def _install_requirements():
    with cd(GITHUB_REPO):
        run('sudo pip install --force-reinstall -q -r requirements.txt', env.hosts)


def _init_git():
    repo = GITHUB_URL + GITHUB_USER + GITHUB_REPO + '.git'
    if not exists(GITHUB_REPO):
        Notification('Cloning the project from {}'.format(repo)).info()
        run('git clone -q ' + repo, env.hosts)



def _update_git():
    with cd(GITHUB_REPO):
        current_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
        current_commit = local("git log -n 1 --format=%H", capture=True)

    Notification('Pulling commit {} from the branch {} !'.format(current_commit, current_branch)).info()

    with cd(GITHUB_REPO):
        run('git checkout {}'.format(current_branch), env.hosts)
        run('git pull', env.hosts)
        run('git reset --hard {}'.format(current_commit), env.hosts)


def _runbg(cmd):
    if env.environment == 'development':
        return local('dtach -n `mktemp -u /tmp/dtach.XXXX` %s' % cmd, capture=True)
    else:
        return run('dtach -n `mktemp -u /tmp/dtach.XXXX` %s' % cmd, env.hosts)

