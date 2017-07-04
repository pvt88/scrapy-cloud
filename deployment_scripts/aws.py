from boto import ec2

from notifications import Notification


class AWS(object):
    def __init__(self, access_key=None, secret_key=None, region=None):
        self.aws_connection = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = ec2.get_region(region)

    def connect(self):
        """
        Establishes a connection to AWS.
        """
        Notification('Attempting to establish a connection to AWS').info()
        self.ec2conn = ec2.connection.EC2Connection(aws_access_key_id=self.access_key,
                                                    aws_secret_access_key=self.secret_key,
                                                    region=self.region)

        Notification('Successfully connected to AWS in {}'.format(self.ec2conn.region)).info()

        return self.ec2conn
