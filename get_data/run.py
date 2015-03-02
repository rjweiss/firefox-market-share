#! /usr/bin/env python
from download import NetMarketShareDownloadJob, StatCounterDownloadJob
from etl import NetMarketShareETLJob, StatCounterETLJob, DashboardETLJob
from datetime import datetime
from ConfigParser import SafeConfigParser
from logging import config
import logging
import argparse
import sys
import os
import json


__author__ = 'Rebecca Weiss'
__version__ = '0.1.0'
__date__ = 'Feb 25 2015'


def main(config, args):
    logger = logging.getLogger(__name__)
    logger.info(u'Begin marketshare data retrieval w/jobtype={a}, region={b}, interval={c})'.format(a=args.jobtype, b=args.region, c=args.interval))
    try:
        initialize()
    except Exception as e:
        logger.error(e)
        sys.exit()
    try:
        download_data(args)
    except Exception as e:
        logger.error(e)
        sys.exit()
    try:
        etl_data(config.get('settings', 'output_dir'), args)
    except Exception as e:
        logger.error(e)
        sys.exit()

    logger.info('Finished downloading and ETL market share data.')


def initialize():
    # XXX Needs to check if S3 flag is enabled, if so, write to S3 instead of local
    # see https://gist.github.com/SavvyGuard/6115006
    logger = logging.getLogger(__name__)
    logger.info('Initializing market share download and ETL jobs.')

    if not os.path.exists(config.get('netmarketshare', 'output_dir')):
        try:
            os.makedirs(config.get('netmarketshare', 'output_dir'))
        except OSError as e:
            if exception.errno != errno.EEXIST:
                raise

    if not os.path.exists(config.get('statcounter', 'output_dir')):
        try:
            os.makedirs(config.get('statcounter', 'output_dir'))
        except OSError as e:
            if exception.errno != errno.EEXIST:
                raise


def download_data(args):
    logger = logging.getLogger(__name__)
    logger.info('Attempting to download market share data.')
    nms_download_job = NetMarketShareDownloadJob(
                       args.jobtype, args.region, args.interval)
    sc_download_job = StatCounterDownloadJob(
                       args.jobtype, args.region, args.interval)
    nms_download_job.initialize()
    nms_data = nms_download_job.run()
    sc_data = sc_download_job.run()
    if not sc_data:
        raise Exception('Failed to download {} StatCounter data'.format(
                        args.interval))
    if not nms_data:
        raise Exception('Failed to download {} NetMarketShare data'.format(
                        args.interval))
    logger.info('Finished downloading market share data.')


def etl_data(output_dir, args):
    logger = logging.getLogger(__name__)
    logger.info('Attempting to ETL market share data.')
    sc_etl_job = StatCounterETLJob(args.interval)
    nms_etl_job = NetMarketShareETLJob(args.interval)
#    dash_etl_job = DashboardETLJob(args.interval)
    sc_data = sc_etl_job.run()
    nms_data = nms_etl_job.run()
    logging.info('here')
#    dash_etl_job.run() # For Firefox and Fennec dashboards

    if not sc_data:
        raise Exception('Failed to ETL StatCounter {} data'.format(
                        args.interval))
    if not nms_data:
        raise Exception('Failed to ETL NetMarketShare {} data'.format(
                        args.interval))

    dashboard_data = {
        'pageviews': sc_data,
        'users': nms_data
    }

    with open(os.path.join(output_dir, '{}_data.json'.format(args.interval)),
              'wb') as outfile:
        json.dump(dashboard_data, outfile)
    logger.info('Retrieved and added {a}/{b} new measurements to dashboard'.format(
                a=len(dashboard_data['pageviews']), b=len(dashboard_data['users'])))


if __name__ == '__main__':
    logging.config.fileConfig('config.cfg')
    config = SafeConfigParser()
    config.read('config.cfg')
    parser = argparse.ArgumentParser(description='Download and ETL browser market share data for dashboards.  Be sure config.cfg is correct.')
    settings = parser.add_argument_group('settings')
    settings.add_argument('interval', help='monthly or weekly')
    settings.add_argument('region', help='world or countries')
    settings.add_argument('jobtype', help='update or complete')
    # settings.add_argument('s3', help='true or false')
    args = parser.parse_args()
    main(config, args)

    meta = {
        'last_updated': str(datetime.now())
    }

    with open(os.path.join(config.get('settings', 'output_dir'), 'meta.json'),
              'w') as output:
        json.dump(meta, output)
