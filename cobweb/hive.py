import sys
import time

from datetime import datetime

import resources.configs as configs

from notifications import Notification
from overseer import Overseer

def main(argv=None):

    # Set up variables
    overseers = []
    total_spiders = 0
    start_time = datetime.utcnow()
    remote_hosts = configs.OVERLORD_SCRAPYD_HOSTS
    max_parallel_spiders = configs.OVERLORD_MAX_PARALLEL_SPIDERS
    sleep_window = configs.OVERLORD_SLEEP_WINDOW

    tasks = configs.OVERSEER_CONFIGS

    # Some helper methods
    def _spawn_overseers(hosts, spider_name):
        for host in hosts:
            overseer = Overseer(name='cobweb', spider_name=spider_name, host=host,
                                mongodb_credentials=configs.MONGODB_CREDENTIALS)
            overseers.append(overseer)

    def _days_hours_minutes(td):
        return td.days, td.seconds // 3600, (td.seconds // 60) % 60

    for task in tasks:
        spider_name = task['spider']
        vendor = task['vendor']
        types = task['types']

        # Create overseer to manage remote scrapyd server
        _spawn_overseers(remote_hosts, spider_name)

        while overseers:
            try:
                for idx, overseer in enumerate(overseers):

                    # Remove any dead overseer
                    if not overseer.heartbeat():
                        overseers.remove(overseer)
                        continue

                    if not types:
                        name = overseer.kill()
                        Notification('{} - [Master]: Killing Overseer {}'.format(datetime.utcnow(), name)).warning()
                        continue

                    # If there is still capacity in the overseer, spawn more spiders
                    running_spiders, _, _ = overseer.get_status()
                    if running_spiders < max_parallel_spiders:
                        num_new_spiders = max_parallel_spiders - running_spiders
                        total_spiders += num_new_spiders
                        try:
                            type = types[0]
                            overseer.spawn_spiders(num_new_spiders, type=type, vendor=vendor)
                        except ValueError:
                            types.remove(type)
                            Notification('{} - [Master]: Out of {} property to crawl'.format(datetime.utcnow(), type)).warning()

                day, hour, minute = _days_hours_minutes(datetime.utcnow() - start_time)
                Notification('{} - [Master]: Alive Overseers = {}, Spawn Spiders = {}, Time = {} days {} hours {} minutes'
                             .format(datetime.utcnow(),
                                     len(overseers),
                                     total_spiders,
                                     day,
                                     hour,
                                     minute
                                     )
                             ).warning()

            except Exception as e:
                Notification('{} - [Exception]: {}'.format(datetime.utcnow(), e)).error()
                time.sleep(4*sleep_window)
                pass

            Notification('{} - [Master]: Finished vendor={}'
                         .format(datetime.utcnow(),
                                 vendor
                                 )
                         ).warning()
            time.sleep(sleep_window)


if __name__ == "__main__":
    sys.exit(main())


