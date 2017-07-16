import time
import numpy as np
import pymongo

from datetime import datetime
from dateutil import parser
from scrapyd_api import ScrapydAPI

from notifications import Notification


class Overseer(object):
    """
    Overseer facilitate the deployment process of local spiders to a remote scrapyd server

    Available methods:
        spawn_spiders           Create spider and deploy them to remote scrapyd server
        get_status              Report the current status of the remote scrapyd server

    """

    DEFAULT_TYPE = 'sell'
    DEFAULT_VENDOR = 'None'

    def __init__(self, name, spider_name, host, mongodb_credentials):
        self.server = ScrapydAPI(host)
        self.host_name = self._strip_host_name(host)
        self.birth_date = datetime.utcnow()
        self.name = name
        self.spider_name = spider_name
        self.alive = True
        client = pymongo.MongoClient(mongodb_credentials['server'],
                                     mongodb_credentials['port'],
                                     connectTimeoutMS=30000,
                                     socketTimeoutMS=None,
                                     socketKeepAlive=True)

        db = client[mongodb_credentials['database']]
        self.collection = db[mongodb_credentials['collection']]

    def kill(self):
        self.alive = False
        return self.host_name

    def heartbeat(self):
        return self.alive

    def spawn_spiders(self, num_spiders=5, items_per_spider=100, **kwargs):
        type = kwargs.get('type', self.DEFAULT_TYPE)
        vendor = kwargs.get('vendor', self.DEFAULT_VENDOR)

        count = 0
        while count < num_spiders:
            count += 1
            self._spawn(vendor, type, items_per_spider)
            time.sleep(3)

    def get_status(self):
        """
         Return:
             the number of running spiders
             the number of finished spiders
             the average time for one spider to finish
        """
        status = self.server.list_jobs(self.name)
        running = status['running']
        finished = status['finished']
        finished_times = [self._time_diff_in_minute(job['end_time'], job['start_time']) for job in finished]
        avg_time = np.average(finished_times)

        Notification('{} - [{}] \t Running Spiders = {}, Finished Spiders = {}, Average Runtime = {}'
                     .format(datetime.utcnow(),
                             self.host_name,
                             len(running),
                             len(finished),
                             avg_time
                             )
                     .expandtabs(3)
                     ).info()

        return len(running), len(finished), avg_time

    def _spawn(self, vendor, type, items_per_spider=100):
        # Get the tasks from the database
        tasks = self._get_tasks_from_database(vendor, type, items_per_spider)
        if not tasks:
            raise ValueError('There is no more task from the database!')

        links, property_ids = zip(*tasks)

        # Schedule the tasks with the remote scrapyd server
        job_id = self.server.schedule(self.name, self.spider_name, vendor=vendor, crawl_url=','.join(links))

        Notification('{} - [{}] \t Launch spider {}'
                     .format(datetime.utcnow(),
                             self.host_name,
                             job_id)
                     .expandtabs(3)
                     ).success()

        # Clear the tasks from the database
        self._clear_tasks_from_database(vendor, type, property_ids)

    def _get_tasks_from_database(self, vendor, type, items_per_spider):
        cursor = self.collection \
                     .find({"last_crawled_date": None, "type": type, "vendor": vendor}) \
                     .sort("created_date", pymongo.ASCENDING) \
                     .limit(items_per_spider)

        tasks = [(item['link'], item['property_id']) for item in cursor]

        return tasks

    def _clear_tasks_from_database(self, vendor, type, property_ids):
        self.collection.update({"vendor": vendor, "type": type, "property_id": {"$in": property_ids}},
                               {"$set": {"last_crawled_date": datetime.utcnow()}},
                               multi=True,
                               upsert=False)

    @staticmethod
    def _time_diff_in_minute(current, previous):
        return ((parser.parse(current) - parser.parse(previous)).seconds // 60) % 60

    @staticmethod
    def _strip_host_name(host):
        return host.replace('http://', '').replace('.compute.amazonaws.com:6800', '')

