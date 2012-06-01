import logging
import json
import datetime
import time
import os
import functools
from collections import defaultdict
from django import http
from django.shortcuts import render

from funfactory.log import log_cef
from session_csrf import anonymous_csrf

from . import models
from . import forms
from . import utils


def plot_graph(start_date, end_date, adubyday, currentversions):
    throttled = {}
    for v in currentversions:
        if v['product'] == adubyday['product'] and v['featured']:
            throttled[v['version']] = float(v['throttle'])

    graph_data = {
        'startDate': adubyday['start_date'],
        'endDate': end_date.strftime('%Y-%m-%d'),
        'count': len(adubyday['versions']),
    }

    for i, version in enumerate(adubyday['versions'], start=1):
        graph_data['item%s' % i] = version['version']
        graph_data['ratio%s' % i] = []
        points = defaultdict(int)

        for s in version['statistics']:
            time = utils.unixtime(s['date'], millis=True)
            if time in points:
                (crashes, users) = points[time]
            else:
                crashes = users = 0
            users += s['users']
            crashes += s['crashes']
            points[time] = (crashes, users)

        for day in utils.daterange(start_date, end_date):
            time = utils.unixtime(day, millis=True)

            if time in points:
                (crashes, users) = points[time]
                t = throttled[version['version']]
                if t != 100:
                    t *= 100
                if users == 0:
                    logging.warning('no ADU data for %s' % day)
                    continue
                ratio = (float(crashes) / float(users) ) * t
            else:
                ratio = None

            graph_data['ratio%s' % i].append([int(time), ratio])

    return graph_data

# FIXME validate/scrub all info
# TODO would be better as a decorator
def _basedata(product=None, version=None):
    data = {}
    api = models.CurrentVersions()
    data['currentversions'] = api.get()
    for release in data['currentversions']:
        if product == release['product']:
            data['product'] = product
            break
    for release in data['currentversions']:
        if version == release['version']:
            data['version'] = version
            break
    return data


def products(request, product, versions=None):
    data = _basedata(product)

    # FIXME hardcoded default, find a better place for this to live
    os_names = ['Windows', 'Mac', 'Linux']

    duration = request.GET.get('duration')

    if duration is None or duration not in ['3','7','14']:
        duration = 7
    else:
       duration = int(duration)

    data['duration'] = duration

    if versions is None:
        versions = []
        for release in data['currentversions']:
            if release['product'] == product and release['featured']:
                versions.append(release['version'])
    else:
        versions = versions.split(';')

    if len(versions) == 1:
        data['version'] = versions[0]

    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=duration + 1)

    mware = models.ADUByDay()
    adubyday = mware.get(product, versions, os_names,
                         start_date, end_date)

    data['graph_data'] = json.dumps(plot_graph(start_date, end_date, adubyday, data['currentversions']))
    data['report'] = 'products'

    return render(request, 'crashstats/products.html', data)


@anonymous_csrf
def topcrasher(request, product=None, version=None, days=None, crash_type=None,
               os_name=None):

    data = _basedata(product, version)

    if days not in ['1', '3', '7', '14', '28']:
        days = 7
    days = int(days)
    data['days'] = days

    end_date = datetime.datetime.utcnow()

    if crash_type not in ['all', 'browser', 'plugin', 'content']:
        crash_type = 'browser'

    data['crash_type'] = crash_type

    if os_name not in ['Windows', 'Linux', 'Mac OS X']:
        os_name = None

    data['os_name'] = os_name

    api = models.TCBS()
    tcbs = api.get(product, version, crash_type, end_date,
                    duration=(days * 24), limit='300')

    signatures = [c['signature'] for c in tcbs['crashes']]

    bugs = {}
    api = models.Bugs()
    for b in api.get(signatures)['bug_associations']:
        bug_id = b['bug_id']
        signature = b['signature']
        if signature in bugs:
            bugs[signature].append(bug_id)
        else:
            bugs[signature] = [bug_id]

    for crash in tcbs['crashes']:
        sig = crash['signature']
        if sig in bugs:
            if 'bugs' in crash:
                crash['bugs'].extend(bugs[sig])
            else:
                crash['bugs'] = bugs[sig]

    data['tcbs'] = tcbs
    data['report'] = 'topcrasher'

    return render(request, 'crashstats/topcrasher.html', data)


def daily(request):
    data = _basedata()

    product = request.GET.get('p')
    if product is None:
        product = 'Firefox'
    data['product'] = product

    versions = []
    for release in data['currentversions']:
        if release['product'] == product and release['featured']:
            versions.append(release['version'])

    os_names = ['Windows', 'Mac', 'Linux']

    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=8)

    api = models.ADUByDay()
    adubyday = api.get(product, versions, os_names, start_date, end_date)

    data['graph_data'] = json.dumps(plot_graph(start_date, end_date, adubyday, data['currentversions']))
    data['report'] = 'daily'

    return render(request, 'crashstats/daily.html', data)


def builds(request, product=None):
    data = _basedata(product)

    data['report'] = 'builds'
    return render(request, 'crashstats/builds.html', data)

def hangreport(request, product=None, version=None, listsize=50):
    data = _basedata(product, version)

    page = request.GET.get('page')
    if page is None:
        page = 1
    data['page'] = int(page)

    duration = request.GET.get('duration')

    if duration is None or duration not in ['3','7','14']:
        duration = 7
    else:
       duration = int(duration)
    data['duration'] = duration

    end_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    hangreport = models.HangReport()
    data['hangreport'] = hangreport.get(product, version, end_date, duration,
                                        listsize, page)

    data['report'] = 'hangreport'
    return render(request, 'crashstats/hangreport.html', data)

def topchangers(request, product=None, versions=None):
    data = _basedata(product, versions)

    data['report'] = 'topchangers'
    return render(request, 'crashstats/topchangers.html', data)

def report_index(request, crash_id=None):
    data = _basedata()

    mware = SocorroMiddleware()
    data['report'] = mware.report_index(crash_id)

    return render(request, 'crashstats/report_index.html', data)

def report_list(request):
    data = _basedata()

    signature = request.GET.get('signature')
    product_version = request.GET.get('version')
    start_date = request.GET.get('date')
    result_number = 250

    mware = SocorroMiddleware()
    data['report_list'] = mware.report_list(signature, product_version,
                                            start_date, result_number)

    return render(request, 'crashstats/report_list.html', data)

def query(request):
    data = _basedata()

    api = models.Search()
    # XXX why on earth are these numbers hard-coded?
    data['query'] = api.get(product='Firefox',
        versions='13.0a1;14.0a2;13.0b2;12.0', os_names='Windows;Mac;Linux',
        start_date='2012-05-03', end_date='2012-05-10', limit='100')

    return render(request, 'crashstats/query.html', data)


def buginfo(request, signatures=None):
    data = _basedata()

    form = forms.BugInfoForm(request.GET)
    if not form.is_valid():
        return http.HttpResponseBadRequest(str(form.errors))

    bugs = form.cleaned_data['bug_ids']
    fields = form.cleaned_data['include_fields']

    bzapi = models.BugzillaBugInfo()
    data['bugs'] = json.dumps(bzapi.get(bugs, fields))

    return render(request, 'crashstats/buginfo.html', data)


@utils.json_view
def plot_signature(request, product, version, start_date, end_date, signature):
    data = _basedata(product, version)

    date_format = '%Y-%m-%d'
    try:
        start_date = datetime.datetime.strptime(start_date, date_format)
        end_date = datetime.datetime.strptime(end_date, date_format)
    except ValueError, msg:
        return http.HttpResponseBadRequest(str(msg))

    diff = end_date - start_date
    duration = diff.days * 24.0 + diff.seconds / 3600.0

    api = models.SignatureTrend()
    sigtrend = api.get(product, version, signature, end_date, duration)

    graph_data = {
        'startDate': sigtrend['start_date'],
        'signature': sigtrend['signature'],
        'endDate': sigtrend['end_date'],
        'counts': [],
        'percents': [],
    }

    for s in sigtrend['signatureHistory']:
        t = utils.unixtime(s['date'], millis=True)
        graph_data['counts'].append([t, s['count']])
        graph_data['percents'].append([t, (s['percentOfTotal'] * 100)])

    return graph_data


@utils.json_view
def signature_summary(request):
    data = _basedata()

    try:
        range_value = int(request.GET.get('range_value'))
    except ValueError, msg:
        return http.HttpResponseBadRequest(str(msg))

    range_unit = request.GET.get('range_unit')
    signature = request.GET.get('signature')
    product_version = request.GET.get('version')
    try:
        start_date = datetime.datetime.strptime(request.GET.get('date'), '%Y-%m-%d')
    except ValueError, msg:
        return http.HttpResponseBadRequest(str(msg))
    end_date = datetime.datetime.utcnow()

    report_types = {
        'architecture': 'architectures',
        'flash_version': 'flashVersions',
        'os': 'percentageByOs',
        'process_type': 'processTypes',
        'products': 'productVersions',
        'uptime': 'uptimeRange'
    }

    api = models.SignatureSummary()

    result = {}
    signature_summary = {}
    for r in report_types:
         name = report_types[r]
         result[name] = api.get(r, signature, start_date, end_date)
         signature_summary[name] = []

    # FIXME fix JS so it takes above format..
    for r in result['architectures']:
        signature_summary['architectures'].append({
            'architecture': r['category'],
            'percentage': (float(r['percentage']) * 100),
            'numberOfCrashes': r['report_count']})
    for r in result['percentageByOs']:
        signature_summary['percentageByOs'].append({
            'os': r['category'],
            'percentage': (float(r['percentage']) * 100),
            'numberOfCrashes': r['report_count']})
    for r in result['productVersions']:
        signature_summary['productVersions'].append({
            'product': r['product_name'],
            'version': r['version_string'],
            'percentage': r['percentage'],
            'numberOfCrashes': r['report_count']})
    for r in result['uptimeRange']:
        signature_summary['uptimeRange'].append({
            'range': r['category'],
            'percentage': (float(r['percentage']) * 100),
            'numberOfCrashes': r['report_count']})
    for r in result['processTypes']:
        signature_summary['processTypes'].append({
            'processType': r['category'],
            'percentage': (float(r['percentage']) * 100),
            'numberOfCrashes': r['report_count']})
    for r in result['flashVersions']:
        signature_summary['flashVersions'].append({
            'flashVersion': r['category'],
            'percentage': (float(r['percentage']) * 100),
            'numberOfCrashes': r['report_count']})

    return signature_summary
