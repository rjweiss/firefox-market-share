#! /usr/bin/env python
# XXX Need countries and operating systems
import requests
import logging
import datetime
import time
import sys
import os
import csv
import json
import simplejson
import StringIO
import io
import itertools
from collections import OrderedDict
from ConfigParser import SafeConfigParser
from isoweek import Week
from requests import *
from dateutil.rrule import *
from itertools import *


class NetMarketShareDownloadJob(object):
    def __init__(self, jobfilter, regionfilter, timefilter, logger=None):
        parser = SafeConfigParser()
        parser.read('config.cfg')
        self.logger = logger or logging.getLogger(__name__)
        self.baseurl = parser.get('netmarketshare', 'baseurl')
        self.loginurl = parser.get('netmarketshare', 'loginurl')
        self.output_dir = parser.get('netmarketshare', 'output_dir')
        self.account = parser.get('netmarketshare', 'account')
        self.passwd = parser.get('netmarketshare', 'passwd')
        self.ua = parser.get('netmarketshare', 'ua')
        self.session = None
        self.query_params = None
        self.jobfilter = jobfilter
        self.regionfilter = regionfilter
        self.timefilter = timefilter

    def initialize(self):
        try:
            self.get_session()
        except Exception as e:
            sys.exit(e)

        self.get_query_params()

    def get_all_months(self, start_month):
        start = datetime.datetime(2009, 1, 1)
        end = datetime.datetime.now()
        months = rrule(MONTHLY, dtstart=start, until=end)
        return [str(i + start_month) for i in range(months.count())]

    def get_all_weeks(self, start_week):
        start = datetime.datetime(2009, 1, 1)
        end = datetime.datetime.now()
        weeks = rrule(WEEKLY, dtstart=start, until=end)
        return [str(i + start_week) for i in range(weeks.count())]

    def get_session(self):
        self.logger.debug('Initiating new NetMarketShare session')
        session = Session()
        session.mount("http://", requests.adapters.HTTPAdapter(max_retries=1))
        session.mount("https://", requests.adapters.HTTPAdapter(max_retries=1))
        headers = {'User-Agent': self.ua}
        payload = {'login_acct_page': self.account,
                   'login_pwd_page': self.passwd}
        rs = session.post(self.loginurl, data=payload)

        if rs.ok:
            self.session = session
        else:
            raise Exception("Failed to create session.")

    def get_query_params(self):
        resource = ['0']
        device = ['0','1','2']
        # os = ['','*1','*2','*3','*8','*9','*10','*11','*12','*13','*14','*15','*16','3211','238','8489','44072644','1244','7584','3512','83','3241','3378','251','2936','117','11','600','3236']
        os = ['']
        span = ['1']
        json = ['22']
        country = [''] # Worldwide totals

        if self.jobfilter == 'complete':
            if self.timefilter == 'monthly':
                interval = ['M']
                timeunit = self.get_all_months(120) # January 1 2009 in months
            elif self.timefilter == 'weekly':
                interval = ['W']
                timeunit = self.get_all_weeks(519) # January 1 2009 in weeks
        elif self.jobfilter == 'update':
            if self.timefilter == 'monthly':
                interval = ['M']
                timeunit = [self.get_all_months(120)[-1]]
                # timeunit = [self.get_all_months(120)]
            elif self.timefilter == 'weekly':
                interval = ['W']
                timeunit = [self.get_all_weeks(519)[-1]]
                # timeunit = [self.get_all_weeks(519)]

        if self.regionfilter == 'countries':
            countries = ['ZW','ZM','ZA','YU','YT','YE','XK','WS','WF','VU','VN','VI','VG','VE','VC','VA','UZ','UY','US','UM','UK','UG','UA','TZ','TW','TV','TT','TR','TL','TP','TO','TN','TM','TK','TJ','TH','TG','TF','TD','TC','SZ','SY','SV','SU','ST','SS','SR','SO','SN','SM','SL','SK','SJ','SI','SH','SG','SE','SD','SC','SB','SA','RW','RU','RO','RS','RE','QA','PY','PW','PT','PS','PR','PN','PM','PL','PK','PH','PG','PF','PE','PA','OM','NZ','NU','NT','NR','NP','NO','NL','NI','NG','NF','NE','NC','NA','MZ','MY','MX','MW','MV','MU','MT','MS','MR','MQ','MP','MO','MN','MM','ML','MK','MH','MG','MF','ME','MD','MC','MA','LY','LV','LU','LT','LS','LR','LK','LI','LC','LB','LA','KZ','KY','KW','KR','KP','KN','KM','KI','KH','KG','KE','JP','JO','JM','JE','IT','IS','IR','IG','IO','IN','IM','IL','IE','ID','HU','HT','HR','HN','HM','HK','GY','GW','GU','GT','GS','GR','GQ','GP','GN','GM','GL','GI','GH','GG','GF','GE','GD','GB','GA','FX','FR','FO','FM','FK','FJ','FI','EU','ET','ES','ER','EH','EG','EE','EC','DZ','DO','DM','DK','DJ','DE','CZ','CY','CX','CV','CU','CS','CR','CO','CN','CM','CL','CK','CI','CH','CG','CF','ZR','CD','CC','CA','BZ','BY','BW','BV','BT','BS','BR','BO','BN','BM','BJ','BI','BH','BG','BF','BE','BD','BB','BA','AZ','AX','AW','AU','AT','AS','AR','AQ','AO','AN','AM','AL','AI','AG','AF','AE','AD','AC']
            countries = ['-000%09101%09{0}%0D'.format(el) for el in countries] # Weird NMS country formatting
            country.extend(countries) # For world totals

        self.query_params = itertools.product(*[resource, device, os, interval, timeunit, span, country, json])

    def build_query_string(self, qp):
        current_query = zip(params.values(), qp)
        query = '&'.join(['='.join(el) for el in current_query])
        return self.baseurl + query, current_query

    def request_data(self, url):
        self.logger.debug("Trying " + url)
        try:
            r = self.session.get(url, timeout=180)
        except requests.exceptions.RequestException as e:
            logging.critical(e)
            sys.exit()
        return r

    def write_data(self, payload, query):
        fname_params = dict((k, query[v]) for (k, v) in params.iteritems())
        fname = '_'.join(['-'.join(el) for el in list(fname_params.iteritems())]) + '.json'
        fname = fname.replace('*', 'A') # Windows-friendly filename
        fname = os.path.join(self.output_dir, fname)
        self.logger.debug("Saving as " + fname)

        with io.open(fname, 'w', encoding='utf-8') as f:
            f.write(unicode(json.dumps(payload, ensure_ascii=False)))
        return True

    def run(self):
        global params
        params = OrderedDict()
        params['resource'] = 'qprid'
        params['device'] = 'qpcustomd'
        params['os'] = 'qpcustomb'
        params['interval'] = 'qptimeframe'
        params['timeunit'] = 'qpsp'
        params['range'] = 'qpnp'
        params['country'] = 'qpaf'
        params['json'] = 'qpf'

        self.logger.debug('Now attempting to download {0} NetMarketShare data.'.format(
                          self.timefilter))

        if self.query_params:
            for qp in self.query_params:
                url, current_query = self.build_query_string(qp)
                rs = self.request_data(url)
                current_payload = dict(current_query)
                current_payload.update(rs.json())
                current_payload['queryurl'] = url
                self.write_data(current_payload, dict(current_query))
            return True
        else:
            return False

class StatCounterDownloadJob(object):

    def __init__(self, jobfilter, regionfilter, timefilter, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        parser = SafeConfigParser()
        parser.read('config.cfg')
        self.baseurl = parser.get('statcounter', 'baseurl')
        self.output_dir = parser.get('statcounter', 'output_dir')
        self.timefilter = timefilter
        self.jobfilter = jobfilter
        self.regionfilter = regionfilter

    def get_all_months(self):
        start = datetime.datetime(2009,1,1)
        end = datetime.datetime.now()
        return (el for el in rrule(MONTHLY, dtstart=start, until=end))

    def get_all_weeks(self):
        start = datetime.datetime(2009,1,1)
        end = datetime.datetime.now()
        return (el for el in rrule(WEEKLY, dtstart=start, until=end))

    def get_all_days(self):
        start = datetime.datetime(2009,1,1)
        end = datetime.datetime.now()
        return (el for el in rrule(DAILY, dtstart=start, until=end))

    def get_query_params(self):
        bar = ['1']
        stattype = ['browser']
        device = ['desktop', 'mobile%2Btablet', 'console']
        region = ['ww']
        granularity = [self.timefilter]

        if self.jobfilter == 'complete':
            if self.timefilter == 'monthly':
                dates = [d for d in list(self.get_all_months())]
                dates.pop()
            if self.timefilter == 'weekly':
                dates = [d for d in list(self.get_all_weeks())]
                dates.pop()
        elif self.jobfilter == 'update':
            if self.timefilter == 'monthly':
                dates = [d for d in list(self.get_all_months())]
                dates.pop()
                dates = [dates[-1]]
            if self.timefilter == 'weekly':
                datelist = [d for d in list(self.get_all_weeks())]
                datelist.pop()
                dates = [datelist[-1]]
        return itertools.product(*[bar, device, stattype, region, granularity, dates])

    def build_query_string(self, qp):
        params = list(qp)
        date = params.pop()
        if self.timefilter == 'monthly':
            date_params = [date.strftime('%Y%m'), date.strftime('%Y%m'),
                           date.strftime('%Y-%m'), date.strftime('%Y-%m'),
                           '1', # for csv
                           'true'] # for multi-device
            params.extend(date_params)
            current_query = zip(params_monthly, params)

        elif self.timefilter == 'weekly':
            date_params = [date.strftime('%Y') + str(date.isocalendar()[1]),
                           date.strftime('%Y') + str(date.isocalendar()[1]),
                           date.strftime('%Y-') + str(date.isocalendar()[1]),
                           date.strftime('%Y-') + str(date.isocalendar()[1]),
                           '1', # for csv
                           'true'] # for multi-device
            params.extend(date_params)
            current_query = zip(params_weekly, params)

        query = '&'.join(['='.join(el) for el in current_query])
        return self.baseurl + query, current_query

    def request_data(self, url):
        self.logger.debug("Trying " + url)
        try:
            r = requests.get(url, timeout=180)
        except requests.exceptions.RequestException as e:
            sys.exit(e)

        f = StringIO.StringIO(r.content)
        f.readline()
        reader = csv.reader(f, delimiter=',')
        return reader

    def write_data(self, payload, query):
        if payload['granularity'] == 'monthly':
            payload['date'] = payload['fromMonthYear']
        elif payload['granularity'] == 'weekly':
            dates = payload['fromWeekYear'].split('-')
            payload['date'] = str(Week(int(dates[0]), int(dates[1])).day(0))

        fname_params = list(query.iteritems())
        fname_params.pop()

        fname = '_'.join(['-'.join(el) for el in fname_params]) + '.json'
        fname = os.path.join(self.output_dir, fname)
        self.logger.debug("Saving as " + fname)

        with io.open(fname, 'w', encoding='utf-8') as f:
            f.write(unicode(json.dumps(payload, ensure_ascii=False)))
        return True

    def run(self):
        global params_monthly
        global params_weekly

        params_monthly = ('bar', 'device_hidden', 'statType_hidden',
                          'region_hidden', 'granularity', 'fromInt', 'toInt',
                          'fromMonthYear', 'toMonthYear', 'csv',
                          'multi-device')
        params_weekly = ('bar', 'device_hidden', 'statType_hidden',
                         'region_hidden', 'granularity', 'fromInt', 'toInt',
                         'fromWeekYear', 'toWeekYear', 'csv', 'multi-device')

        self.logger.info('Now attempting to download {0} StatCounter data.'.format(
                          self.timefilter))
        self.query_params = self.get_query_params()

        if self.query_params:
            for qp in self.query_params:
                url, query = self.build_query_string(qp)
                rs = self.request_data(url)
                payload = dict(query)
                payload['rows'] = [{'browser': row[0],
                                    'value': float(row[1])/100} for row in rs]
                payload['queryurl'] = url
                payload['os'] = 'all'
                self.write_data(payload, dict(query))
            return True
        else:
            return False
