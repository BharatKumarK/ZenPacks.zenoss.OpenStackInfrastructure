##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenStack.NovaServiceStatus')

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from zope.component import adapts
from zope.interface import implements

from Products.ZenEvents import ZenEventClasses

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSource, PythonDataSourcePlugin, PythonDataSourceInfo,
    IPythonDataSourceInfo)

from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.OpenStack.utils import result_errmsg, add_local_lib_path
add_local_lib_path()

from novaclient import client as novaclient


class NovaServiceStatusDataSource(PythonDataSource):
    '''
    Datasource used to check the status of nova services via the nova API
    '''

    ZENPACKID = 'ZenPacks.zenoss.OpenStack'

    sourcetypes = ('OpenStack Nova Service Status',)
    sourcetype = sourcetypes[0]

    # RRDDataSource
    component = '${here/id}'
    cycletime = 30

    # PythonDataSource
    plugin_classname = 'ZenPacks.zenoss.OpenStack.datasources.'\
        'NovaServiceStatusDataSource.NovaServiceStatusDataSourcePlugin'

    # NovaServiceStatusDataSource

    _properties = PythonDataSource._properties + ( )


class INovaServiceStatusDataSourceInfo(IPythonDataSourceInfo):
    '''
    API Info interface for INovaServiceStatusDataSource.
    '''

    pass


class NovaServiceStatusDataSourceInfo(PythonDataSourceInfo):
    '''
    API Info adapter factory for NovaServiceStatusDataSource.
    '''

    implements(INovaServiceStatusDataSourceInfo)
    adapts(NovaServiceStatusDataSource)

    testable = False


class NovaServiceStatusDataSourcePlugin(PythonDataSourcePlugin):
    proxy_attributes = (
        'zOpenStackRegionName',
        'zCommandUsername',
        'zCommandPassword',
        'zOpenStackProjectId',
        'zOpenStackAuthUrl',
    )

    @classmethod
    def config_key(cls, datasource, context):
        """
        Return list that is used to split configurations at the collector.

        This is a classmethod that is executed in zenhub. The datasource and
        context parameters are the full objects.
        """
        return (
            context.device().id,
            datasource.getCycleTime(context),
            datasource.plugin_classname,
        )

    @classmethod
    def params(cls, datasource, context):
        return {}

    @inlineCallbacks
    def collect(self, config):
        log.debug("Collect for OpenStack Nova Service Status (%s)" % config.id)
        ds0 = config.datasources[0]

        if (log.isEnabledFor(logging.DEBUG)):
            http_log_debug = True
            logging.getLogger('novaclient.client').setLevel(logging.DEBUG)
        else:
            http_log_debug = False

        client = novaclient.Client(
            2,  # API version 2
            ds0.zCommandUsername,
            ds0.zCommandPassword,
            ds0.zOpenStackProjectId,
            ds0.zOpenStackAuthUrl,
            region_name=ds0.zOpenStackRegionName,
            http_log_debug=http_log_debug
        )

        results = {}

        log.info('Requesting services')
        results['services'] = client.services.list()

        defer.returnValue(results)
        yield None

    def onSuccess(self, result, config):
        data = self.new_data()

        for service in result['services']:
            service_id = prepId('service-{0}-{1}-{2}'.format(service.binary, service.host, service.zone))

            if service.status == 'disabled':
                data['events'].append({
                    'device': config.id,
                    'component': service_id,
                    'summary': 'Service %s on host %s (Availabilty Zone %s) is now DISABLED' % (service.binary, service.host, service.zone),
                    'severity': ZenEventClasses.Clear,
                    'eventClassKey': 'OpenStackNovaServiceStatus',
                    })

            elif service.state == 'up':
                data['events'].append({
                    'device': config.id,
                    'component': service_id,
                    'summary': 'Service %s on host %s (Availabilty Zone %s) is now UP' % (service.binary, service.host, service.zone),
                    'severity': ZenEventClasses.Clear,
                    'eventClassKey': 'OpenStackNovaServiceStatus',
                    })
            else:

                data['events'].append({
                    'device': config.id,
                    'component': service_id,
                    'summary': 'Service %s on host %s (Availabilty Zone %s) is now DOWN' % (service.binary, service.host, service.zone),
                    'severity': ZenEventClasses.Error,
                    'eventClassKey': 'OpenStackNovaServiceStatus',
                    })

        # Note: Technically, this event could be related to the nova-api component(s)
        # for this region
        data['events'].append({
            'device': config.id,
            'summary': 'Nova Status Collector: successful collection',
            'severity': ZenEventClasses.Clear,
            'eventKey': 'NovaServiceStatusCollection',
            'eventClassKey': 'EventsSuccess',
            })

        return data

    def onError(self, result, config):
        errmsg = 'Nova Status Collector: %s' % result_errmsg(result)
        log.error('%s: %s', config.id, errmsg)

        data = self.new_data()

        # Note: Technically, this event could be related to the nova-api component(s)
        # for this region
        data['events'].append({
            'device': config.id,
            'summary': errmsg,
            'severity': ZenEventClasses.Error,
            'eventKey': 'NovaServiceStatusCollection',
            'eventClassKey': 'EventsFailure',
            })

        return data
