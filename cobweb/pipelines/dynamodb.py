import datetime
import boto3
from decimal import Decimal
from cobweb.items import HouseItem
import logging

log = logging.getLogger('cobweb.scrapy.pipeline.dynamodb')

class DynamoDBPipeline(object):

    def _default_encoder(value):
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, datetime.time):
            return value.strftime('%H:%M:%S')
        elif isinstance(value, float):
            return Decimal(str(value)) # This is to work around boto/DynamoDB restriction on Float
        elif isinstance(value, str):
            if value == "" or value == u'':
                return " "
            else:
                return value
        else:
            return value

    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name,
                 table_name, encoder=_default_encoder):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.table_name = table_name
        self.encoder = encoder
        self.table = None

    @classmethod
    def from_crawler(cls, crawler):
        aws_access_key_id = crawler.settings['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = crawler.settings['AWS_SECRET_ACCESS_KEY']
        region_name = crawler.settings['DYNAMODB_PIPELINE_REGION_NAME']
        table_name = crawler.settings['DYNAMODB_PIPELINE_TABLE_NAME']
        return cls(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            table_name=table_name
        )

    def open_spider(self, spider):
        db = boto3.resource(
            'dynamodb',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )
        self.table = db.Table(self.table_name)

    def close_spider(self, spider):
        self.table = None

    def process_item(self, item, spider):
        if isinstance(item, HouseItem):
            self.table.put_item(
                TableName=self.table_name,
                Item={k: self.encoder(v) for k, v in item.items()},
            )
            return item