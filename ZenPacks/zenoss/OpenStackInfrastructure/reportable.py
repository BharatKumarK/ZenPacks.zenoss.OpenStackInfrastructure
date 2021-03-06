##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import basereportable
from ZenPacks.zenoss.OpenStackInfrastructure.SoftwareComponent import SoftwareComponent
from Products.Zuul.interfaces import IReportable
from ZenPacks.zenoss.ZenETL.reportable import MARKER_LENGTH, DEFAULT_STRING_LENGTH


class BaseReportable(basereportable.BaseReportable):

    @classmethod
    def entity_class_for_class(cls, object_class):
        entity_class = super(BaseReportable, cls).entity_class_for_class(object_class)
        return entity_class.replace("open_stack", "openstack")

    @property
    def export_as_bases(self):
        bases = super(BaseReportable, self).export_as_bases

        # Anything that is a softwarecomponent subclass, also export
        # as a softwarecomponent.
        if isinstance(self.context, SoftwareComponent):
            bases.append(SoftwareComponent)

        return bases


class BaseReportableFactory(basereportable.BaseReportableFactory):
    pass


class AvailabilityZoneReportable(BaseReportable):

    def reportProperties(self):
        # allow table join between avalability zone and region.
        for prop in super(AvailabilityZoneReportable, self).reportProperties():
            yield prop

        yield ('openstack_infrastructure_region_key',
               'reference',
               IReportable(self.context.device().getDeviceComponents(
                   type='OpenStackInfrastructureRegion')[0]).sid,
               MARKER_LENGTH)

class HostReportable(BaseReportable):

    # add a reference to the host device, in addition to the normal
    # exported references and properties.
    def reportProperties(self):
        for prop in super(HostReportable, self).reportProperties():
            yield prop

        hostDevice = self.context.proxy_device()
        if hostDevice:
            yield ('openstack_infrastructure_host_host_device_key',
                   'reference',
                   IReportable(hostDevice).sid,
                   MARKER_LENGTH)
        else:
            yield ('openstack_infrastructure_host_host_device_key',
                   'reference',
                   None,
                   MARKER_LENGTH)


class InstanceReportable(BaseReportable):

    # add a reference to the guest device, in addition to the normal
    # exported references and properties.
    def reportProperties(self):
        for prop in super(InstanceReportable, self).reportProperties():
            yield prop

        guestDevice = self.context.guestDevice()
        if guestDevice:
            yield ('openstack_infrastructure_instance_guest_device_key',
                   'reference',
                   IReportable(guestDevice).sid,
                   MARKER_LENGTH)
        else:
            yield ('openstack_infrastructure_instance_guest_device_key',
                   'reference',
                   None,
                   MARKER_LENGTH)


class RegionReportable(BaseReportable):

    def reportProperties(self):
        for prop in super(RegionReportable, self).reportProperties():
            yield prop
        region = self.context

        yield ('openstack_infrastructure_region_parent_org',
               'string',
               str(len(region.parentOrg())) if region.parentOrg() else None,
               DEFAULT_STRING_LENGTH)

        yield ('openstack_infrastructure_region_child_orgs',
               'string',
               str(len(region.childOrgs())),
               DEFAULT_STRING_LENGTH)
