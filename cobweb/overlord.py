import pymongo
import sys
import time

from datetime import datetime

from scrapyd_api import ScrapydAPI
from scrapy.conf import settings

import cobweb.resources.configs as configs

scrapyd = ScrapydAPI(configs.OVERLORD_SCRAPYD_URI)
scrapyd_1 = ScrapydAPI(configs.OVERLORD_SCRAPYD_URI_1)


def deploy(max_items, scrapyd_id=0):
    mongodb_credentials = settings.get('MONGODB_CREDENTIALS')

    connection = pymongo.MongoClient(
        mongodb_credentials['server'],
        mongodb_credentials['port']
    )
    db = connection[mongodb_credentials['database']]
    collection = db['property_list']
    cursor = collection.find({"last_crawled_date": None, "type": "sell"}).sort("created_date", pymongo.ASCENDING)[:max_items]

    ids = [(item['link'], item['property_id'], item['vendor'], item['type']) for item in cursor]
    links, property_ids, vendors, _ = zip(*ids)

    if scrapyd_id == 0:
        job_id = scrapyd.schedule('cobweb', 'real_estate_spider', vendor=vendors[0], crawl_url=','.join(links))
        print('Launched job={} on scrapyd={} : vendor={} : id={}'.format(job_id, configs.OVERLORD_SCRAPYD_URI, vendors[0], ','.join(property_ids)))
    elif scrapyd_id == 1:
        job_id = scrapyd_1.schedule('cobweb', 'real_estate_spider', vendor=vendors[0], crawl_url=','.join(links))
        print('Launched job={} on scrapyd={} : vendor={} : id={}'.format(job_id, configs.OVERLORD_SCRAPYD_URI_1, vendors[0], ','.join(property_ids)))

    collection.update({"vendor": vendors[0],
                       "property_id": {"$in": property_ids},
                       "type": "sell"},
                      {"$set": {"last_crawled_date": datetime.utcnow()
                               },
                      },
                      multi=True,
                      upsert=False)


def launch_spiders(num_spiders, scrapyd_id=0):
    count = 0
    while count < num_spiders:
        count += 1
        deploy(configs.OVERLORD_ITEMS_PER_SPIDER, scrapyd_id)
        time.sleep(7)


def main(argv=None):
    total_spiders = 0
    while total_spiders < configs.OVERLORD_TOTAL_SPIDERS:
        for idx in range(2):
            running_spiders, finished_spiders = get_running_spiders(idx)
            print('On server {}, there are {} spiders running and {} spiders finished so far!'.format(idx, len(running_spiders),
                                                                                        len(finished_spiders)))
            if len(running_spiders) < configs.OVERLORD_MAX_PARALLEL_SPIDERS:
                spiders_launching = configs.OVERLORD_MAX_PARALLEL_SPIDERS - len(running_spiders)
                total_spiders = total_spiders + spiders_launching
                launch_spiders(spiders_launching, idx)

        time.sleep(configs.OVERLORD_SLEEP_WINDOW)

    print('Completed {} spiders!'.format(total_spiders))


def get_running_spiders(scrapyd_id=0):
    if scrapyd_id == 0:
        status = scrapyd.list_jobs('cobweb')
        running = status['running']
        finished = status['finished']
    elif scrapyd_id == 1:
        status = scrapyd_1.list_jobs('cobweb')
        running = status['running']
        finished = status['finished']

    return running, finished


if __name__ == "__main__":
    sys.exit(main())


