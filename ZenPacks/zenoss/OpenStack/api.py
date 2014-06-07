##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
API interfaces and default implementations.
'''

import logging
log = logging.getLogger('zen.OpenStackAPI')

from urlparse import urlparse

from zope.event import notify
from zope.interface import implements
from ZODB.transact import transact

from Products.ZenUtils.Ext import DirectRouter, DirectResponse
from Products import Zuul
from Products.Zuul.catalog.events import IndexingEvent
from Products.Zuul.facades import ZuulFacade
from Products.Zuul.interfaces import IFacade
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.zenoss.OpenStack.utils import add_local_lib_path
add_local_lib_path()

OPENSTACK_DEVICE_PATH = "/Devices/OpenStack"


class IOpenStackFacade(IFacade):
    def addOpenStack(self, device_name, username, api_key, project_id, auth_url,
                     region_name=None, collector='localhost'):
        """Add OpenStack Endpoint."""

    def getRegions(self, username, api_key, project_id, auth_url):
        """Get a list of available regions, given a keystone endpoint and credentials."""


class OpenStackFacade(ZuulFacade):
    implements(IOpenStackFacade)

    def addOpenStack(self, device_name, username, api_key, project_id, auth_url,
                     region_name, collector='localhost'):
        """Add a new OpenStack endpoint to the system."""
        parsed_url = urlparse(auth_url)

        if parsed_url.scheme == "" or parsed_url.hostname is None:
            return False, _t("'%s' is not a valid URL." % auth_url)

        # Verify that this device does not already exist.
        deviceRoot = self._dmd.getDmdRoot("Devices")
        device = deviceRoot.findDeviceByIdExact(device_name)
        if device:
            return False, _t("A device named %s already exists." % device_name)

        zProperties = {
            'zCommandUsername': username,
            'zCommandPassword': api_key,
            'zOpenStackProjectId': project_id,
            'zOpenStackAuthUrl': auth_url,
            'zOpenStackRegionName': region_name
            }

        @transact
        def create_device():
            dc = self._dmd.Devices.getOrganizer(OPENSTACK_DEVICE_PATH)

            device = dc.createInstance(device_name)
            device.setPerformanceMonitor(collector)

            for prop, val in zProperties.items():
                device.setZenProperty(prop, val)

            device.index_object()
            notify(IndexingEvent(device))

        # This must be committed before the following model can be
        # scheduled.
        create_device()

        # Schedule a modeling job for the new device.
        device = deviceRoot.findDeviceByIdExact(device_name)
        device.collectDevice(setlog=False, background=True)

        return True, 'Device addition scheduled'

    def getRegions(self, username, api_key, project_id, auth_url):
        """Get a list of available regions, given a keystone endpoint and credentials."""

        from keystoneclient.v2_0.client import Client as keystoneclient

        client = keystoneclient(
            username=username,
            password=api_key,
            tenant_name=project_id,
            auth_url=auth_url,
        )

        regions = set()
        endpoints = client.service_catalog.get_endpoints()
        for (service, service_endpoints) in endpoints.iteritems():
            for endpoint in service_endpoints:
                regions.add(endpoint['region'])

        return [{'key': c, 'label': c} for c in sorted(regions)]


class OpenStackRouter(DirectRouter):
    def _getFacade(self):
        return Zuul.getFacade('openstack', self.context)

    def addOpenStack(self, device_name, username, api_key, project_id, auth_url,
                     region_name, collector='localhost'):

        facade = self._getFacade()
        success, message = facade.addOpenStack(
            device_name, username, api_key, project_id, auth_url,
            region_name=region_name, collector=collector)

        if success:
            return DirectResponse.succeed(jobId=message)
        else:
            return DirectResponse.fail(message)

    def getRegions(self, username, api_key, project_id, auth_url):
        facade = self._getFacade()

        data = facade.getRegions(username, api_key, project_id, auth_url)
        return DirectResponse(success=True, data=data)
