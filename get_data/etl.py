#! /usr/bin/env python
# XXX Need countries and operating systems
import os
import io
import dateutil
import json
import pprint
import logging
from dateutil.parser import *
from collections import defaultdict
from pprint import pprint
from ConfigParser import SafeConfigParser


class StatCounterETLJob(object):

    def __init__(self, interval, logger=None):
        parser = SafeConfigParser()
        parser.read('config.cfg')
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = parser.get('statcounter', 'output_dir')
        self.interval = interval
        self.output_dir = parser.get('settings', 'output_dir')

    def get_files(self):
        self.files = os.listdir(self.data_dir)

    def get_monthly_data(self):
        self.month_files = [f for f in self.files
                            if 'granularity-monthly' in f]

    def get_weekly_data(self):
        self.week_files = [f for f in self.files if 'granularity-weekly' in f]

    def _get_browser(self, x):
        return {
            'IE': 'IE',
            'Firefox': 'Firefox',
            'Safari': 'Safari',
            'Opera': 'Opera',
            'Opera Mini': 'Opera',
            'Opera Mobile': 'Opera',
            'Android': 'Android',
            'Playstation': 'Playstation',
            'Chrome': 'Chrome',
            'iPhone': 'Safari',
            'Sony PS4': 'Playstation',
            'Sony PS3': 'Playstation'
        }.get(x, 'Other')

    def transform(self, payload):
        # # XXX Valid browsers needs to be conditional on platform
        # valid_browsers = set([])
        # if payload['device_hidden'] == 'desktop':
        #     valid_browsers = set(['Firefox', 'Opera', 'Safari', 'Chrome', 'IE'])
        # elif payload['device_hidden'] == 'mobile':
        #     valid_browsers = set(['Firefox', 'Opera', 'Safari', 'Chrome', 'IE',
        #                           'Android', 'iPhone', 'UC Browser'])
        # elif payload['device_hidden'] == 'console':
        #     valid_browsers = set(['Opera', 'IE', 'Sony PS4', 'Sony PS3'])

        result = defaultdict(float)
        if self.interval == 'monthly':
            result['date'] = dateutil.parser.parse(payload['date']).date()
            result['date'] = str(result['date'].replace(day=1))
        else:
            result['date'] = str(dateutil.parser.parse(payload['date']).date())
        result['platform'] = payload['device_hidden']
        result['level'] = 'pageviews'
        result['os'] = 'all'
    #     result['country'] = payload['country']
        for row in payload['rows']:
            result[self._get_browser(row['browser'])] += row['value']
            # if row['browser'] in valid_browsers:
            #     result[row['browser']] = row['value']
            # else:
            #     result[u'Other'] += row['value']
        return result

    def extract(self):
        self.get_files()
        self.get_monthly_data()
        self.get_weekly_data()

        if self.interval == 'monthly':
            for month in self.month_files:
                self.logger.debug('Extracting ' + month)
                with open(os.path.join(self.data_dir, month), 'r') as infile:
                    data = json.load(infile)
                    yield dict(self.transform(data))
        if self.interval == 'weekly':
            for week in self.week_files:
                self.logger.debug('Extracting ' + week)
                with open(os.path.join(self.data_dir, week), 'r') as infile:
                    data = json.load(infile)
                    yield dict(self.transform(data))

    def run(self):
        return list(self.extract())


class NetMarketShareETLJob(object):

    def __init__(self, interval, logger=None):
        parser = SafeConfigParser()
        parser.read('config.cfg')
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = parser.get('netmarketshare', 'output_dir')
        self.interval = interval
        self.output_dir = parser.get('settings', 'output_dir')

    def get_files(self):
        self.files = os.listdir(self.data_dir)

    def get_all_months(start_month):
        start = datetime.datetime(2009, 1, 1)
        end = datetime.datetime.now()
        months = rrule.rrule(rrule.MONTHLY, dtstart=start, until=end)

        for i in range(months.count()):
            yield str(i + start_month)

    def get_all_weeks(start_week):
        start = datetime.datetime(2009, 1, 1)
        end = datetime.datetime.now()
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start, until=end)

        for i in range(weeks.count()):
            yield str(i + start_week)

    def get_monthly_data(self):
        self.month_files = [f for f in self.files if 'interval-M' in f]

    def get_weekly_data(self):
        self.week_files = [f for f in self.files if 'interval-W' in f]

    def _get_device(self, x):
        return {
            '0': 'desktop',
            '1': 'mobile_and_tablet',
            '2': 'console'
        }[x]

    def _get_os(self, x):
        return {
            '': 'all',
            '*1': 'windows',
            '*2': 'osx',
            '*3': 'linux',
        }.get(x, 'other')

    def _get_browser(self, x):
        return {
            'Microsoft Internet Explorer': 'IE',
            'Firefox': 'Firefox',
            'Safari': 'Safari',
            'Opera': 'Opera',
            'Opera Mini': 'Opera',
            'Opera Mobile': 'Opera',
            'Android Browser': 'Android',
            'Playstation': 'Playstation',
            'Chrome': 'Chrome'
        }.get(x, 'Other')

    def _get_float(self, value):
        return float(value.strip('%')) / 100

    def _collapse_browsers(self, d, platform):
        result = defaultdict(float)
        for browser in d.keys():
            result[self._get_browser(browser)] += d[browser]
        return dict(result)

    def transform(self, payload):
        result = {}
        for row in payload['rows']:
            result[row['ColumnName']] = self._get_float(row['UV'])
        result = self._collapse_browsers(result, payload['qpcustomd'])
        result['date'] = str(dateutil.parser.parse(payload['startTime'])
                             .date())
        # d['country'] = payload['qpaf']
        result['os'] = self._get_os(payload['qpcustomb'])
        result['platform'] = self._get_device(payload['qpcustomd'])
        result['level'] = u'users'
        return result

    def extract(self):
        self.get_files()
        self.get_monthly_data()
        self.get_weekly_data()

        if self.interval == 'monthly':
            for month in self.month_files:
                self.logger.debug('Extracting ' + month)
                with open(os.path.join(self.data_dir, month), 'r') as infile:
                    payload = json.load(infile)
                    yield self.transform(payload)
        if self.interval == 'weekly':
            for week in self.week_files:
                self.logger.debug('Extracting ' + week)
                with open(os.path.join(self.data_dir, week), 'r') as infile:
                    payload = json.load(infile)
                    yield self.transform(payload)

    def run(self):
        return list(self.extract())


class DashboardETLJob(object):

    def __init__(self, interval, logger=None):
        parser = SafeConfigParser()
        parser.read('config.cfg')
        self.logger = logger or logging.getLogger(__name__)
        self.interval = interval
        self.output_dir = parser.get('settings', 'output_dir')

    def get_files(self):
        self.files = os.listdir(self.output_dir)

    def get_date_and_Firefox(self, d):
        return dict((k, d[k]) for k in ['date', 'Firefox'] if k in foo)

    def extract(self):
        self.get_files()
        with open(os.path.join(self.output_dir, '{0}_data.json'.format(self.interval)), 'r') as infile:
            payload = json.load(infile)
            return payload

    def transform(self, payload):
        # XXX Yuck.
        pageviews = payload['pageviews']
        users = payload['users']
        fennec_pageviews = []
        firefox_pageviews = []
        fennec_users = []
        firefox_users = []

        for d in pageviews:
            if d['platform'] == 'desktop':
                if 'Firefox' in d.keys():
                    firefox_pageview = dict((k, d[k]) for k in ['date', 'Firefox'] if k in d)
                    firefox_pageviews.append(firefox_pageview)
            elif d['platform'] == 'mobile%2Btablet':
                if 'Firefox' in d.keys():
                    fennec_pageview = dict((k, d[k]) for k in ['date', 'Firefox'] if k in d)
                    fennec_pageviews.append(fennec_pageview)
            else:
                continue

        for d in users:
            if d['platform'] == 'desktop':
                if 'Firefox' in d.keys():
                    firefox_user = dict((k, d[k]) for k in ['date', 'Firefox'] if k in d)
                    firefox_users.append(firefox_user)
            elif d['platform'] == 'mobile_and_tablet':
                if 'Firefox' in d.keys():
                    fennec_user = dict((k, d[k]) for k in ['date', 'Firefox'] if k in d)
                    fennec_users.append(fennec_user)
            else:
                continue

        for d in fennec_pageviews:
            d['value'] = d.pop('Firefox')

        for d in firefox_pageviews:
            d['value'] = d.pop('Firefox')

        for d in fennec_users:
            d['value'] = d.pop('Firefox')

        for d in firefox_users:
            d['value'] = d.pop('Firefox')

        firefox = {
            u'pageviews': firefox_pageviews,
            u'users': firefox_users
        }

        fennec = {
            u'pageviews': fennec_pageviews,
            u'users': fennec_users
        }

        return firefox, fennec

    def run(self):
        payload = self.extract()
        firefox, fennec = self.transform(payload)

        with open(os.path.join(self.output_dir, 'firefox_marketshare_{0}.json'.format(self.interval)), 'w') as outfile:
            json.dump(firefox, outfile)

        with open(os.path.join(self.output_dir, 'fennec_marketshare_{0}.json'.format(self.interval)), 'w') as outfile:
            json.dump(fennec, outfile)
