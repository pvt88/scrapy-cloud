import pymongo
import sys
import time

from datetime import datetime

from scrapyd_api import ScrapydAPI
from scrapy.conf import settings

import cobweb.resources.configs as configs

from deployment_scripts.notifications import Notification

scrapyds = [ScrapydAPI(server) for server in configs.OVERLORD_SCRAPYD_URIS]


def deploy(max_items, server_id=0):
    mongodb_credentials = settings.get('MONGODB_CREDENTIALS')

    connection = pymongo.MongoClient(
        mongodb_credentials['server'],
        mongodb_credentials['port']
    )
    db = connection[mongodb_credentials['database']]
    collection = db['property_list']
    cursor = collection.find({"last_crawled_date": None, "type": "rent"}).sort("created_date", pymongo.ASCENDING)[:max_items]

    ids = [(item['link'], item['property_id'], item['vendor'], item['type']) for item in cursor]
    links, property_ids, vendors, _ = zip(*ids)

    job_id = scrapyds[server_id].schedule('cobweb', 'real_estate_spider', vendor=vendors[0], crawl_url=','.join(links))

    Notification('{} - [Server {}]: Launch job={}'
                 .format(datetime.utcnow(),
                         server_id,
                         job_id)
                 ).success()

    collection.update({"vendor": vendors[0],
                       "property_id": {"$in": property_ids},
                       "type": "rent"},
                      {"$set": {"last_crawled_date": datetime.utcnow()
                               },
                      },
                      multi=True,
                      upsert=False)


def launch_spiders(num_spiders, server_id=0):
    count = 0
    while count < num_spiders:
        count += 1
        deploy(configs.OVERLORD_ITEMS_PER_SPIDER, server_id)
        time.sleep(3)


def main(argv=None):
    total_spiders = 0
    start_time = datetime.utcnow()
    while total_spiders < configs.OVERLORD_TOTAL_SPIDERS:
        try:
            for server_id, _ in enumerate(scrapyds):
                running_spiders, finished_spiders = get_running_spiders(server_id)
                Notification('{} - [Server {}]: Running Spiders {}  Finished Spiders {}'
                             .format(datetime.utcnow(),
                                     server_id,
                                     len(running_spiders),
                                     len(finished_spiders)
                                     )
                             ).info()
                if len(running_spiders) < configs.OVERLORD_MAX_PARALLEL_SPIDERS:
                    spiders_launching = configs.OVERLORD_MAX_PARALLEL_SPIDERS - len(running_spiders)
                    total_spiders = total_spiders + spiders_launching
                    launch_spiders(spiders_launching, server_id)


            day, hour, minute = days_hours_minutes(datetime.utcnow() - start_time)
            Notification('{} - [Master-{}%]: Total Spiders {} in {} days, {} hours, {} minutes'
                         .format(datetime.utcnow(),
                                 int(100.0 * total_spiders / configs.OVERLORD_TOTAL_SPIDERS),
                                 total_spiders,
                                 day,
                                 hour,
                                 minute
                                 )
                         ).warning()


        except Exception as e:
            Notification('{} - [Exception]: {}'
                         .format(datetime.utcnow(),
                                 e)
                         ).error()

            time.sleep(3*60)
            pass

        time.sleep(configs.OVERLORD_SLEEP_WINDOW)


def get_running_spiders(server_id=0):
    status = scrapyds[server_id].list_jobs('cobweb')
    running = status['running']
    finished = status['finished']
    return running, finished


def days_hours_minutes(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60

if __name__ == "__main__":
    sys.exit(main())


