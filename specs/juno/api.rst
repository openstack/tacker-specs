..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Example Spec - The title of your blueprint
==========================================

https://blueprints.launchpad.net/neutron/+spec/adv-services-in-vms




Problem description
===================

(Background: this project is spin-out project from Neutron)

It is a quite common requirement to run services in virtual
machines aka ServiceVM. So far each OpenStack
service(Especially Neutron case) implemented their own life
cycle management of ServiceVMs/services and
hardware. Preparing/pooling/scheduling VMs/services and so on.
It resulted in duplicated work and rises the bar for appliance
provide to integrate appliances with OpenStack.

This project introduces a new service for managing
servicevm/device. Its responsibility is to:

* manage VMs/devices/services
* control the allocation of processing capacity in such devices As
  such the servicevm/device manager mainly serves other
  projects. Another natural responsibility of this service would be to
  keep track of and store the physical topology that the devices are
  part of.
* pluggable for each VMs/physical devices/services


As ETSI NFV is an important use case, NFV conformance is in the scope
of this project.  This project services as some components of NFV MANO
architecture.
http://www.ietf.org/proceedings/89/slides/slides-89-opsawg-7.pdf

* corresponding component:
  * VNFM(VNF Manager)
* corresponding interfaces:
  * VNF lifecycle management interface
  * VNF lifecycle changes notifications interface
  * VNF configuration interface


The relationship of NFV team and this project:

This project serves as (sub)component(s) necessary for NFV in
openstack. The team will cooperate with NFV team.


Proposed change
===============

Create API and consolidate the existing multiple implmementations


Alternatives
------------

None

Data model impact
-----------------

.. code-block:: python


   class DeviceTemplate(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
       """Represents template to create hosting device
       """
       # Descriptive name
       name = sa.Column(sa.String(255))
       description = sa.Column(sa.String(255))
   
       # service type that this service vm provides.
       # At first phase, this includes only single service
       # In future, single service VM may accomodate multiple services.
       service_types = orm.relationship('ServiceType', backref='template')
   
       # driver to create hosting device. e.g. noop, nova, heat, etc...
       device_driver = sa.Column(sa.String(255))
   
       # mgmt driver to communicate with hosting device.
       # e.g. noop, OpenStack MGMT, OpenStack notification, netconf, snmp,
       #      ssh, etc...
       mgmt_driver = sa.Column(sa.String(255))
   
       # (key, value) pair to spin up
       attributes = orm.relationship('DeviceTemplateAttribute',
                                     backref='template')
   
   
   class ServiceType(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
       """Represents service type which hosting device provides.
       Since a device may provide many services, This is one-to-many
       relationship.
       """
       template_id = sa.Column(sa.String(36), sa.ForeignKey('devicetemplates.id'),
                               nullable=False)
       service_type = sa.Column(sa.String(255), nullable=False)
   
   
   class DeviceTemplateAttribute(model_base.BASE, models_v1.HasId):
       """Represents attributes necessary for spinning up VM in (key, value) pair
       key value pair is adopted for being agnostic to actuall manager of VMs
       like nova, heat or others. e.g. image-id, flavor-id for Nova.
       The interpretation is up to actual driver of hosting device.
       """
       template_id = sa.Column(sa.String(36), sa.ForeignKey('devicetemplates.id'),
                               nullable=False)
       key = sa.Column(sa.String(255), nullable=False)
       value = sa.Column(sa.String(255), nullable=True)
   
   
   class Device(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
       """Represents devices that hosts services.
       Here the term, 'VM', is intentionally avoided because it can be
       VM or other container.
       """
       template_id = sa.Column(sa.String(36), sa.ForeignKey('devicetemplates.id'))
       template = orm.relationship('DeviceTemplate')
   
       # sufficient information to uniquely identify hosting device.
       # In case of service VM, it's UUID of nova VM.
       instance_id = sa.Column(sa.String(255), nullable=True)
   
       # For a management tool to talk to manage this hosting device.
       # opaque string. mgmt_driver interprets it.
       # e.g. (driver, mgmt_address) = (ssh, ip address), ...
       mgmt_address = sa.Column(sa.String(255), nullable=True)
   
       service_context = orm.relationship('DeviceServiceContext')
       services = orm.relationship('ServiceDeviceBinding', backref='device')
   
       status = sa.Column(sa.String(255), nullable=False)
   
   
   class DeviceArg(model_base.BASE, models_v1.HasId):
       """Represents kwargs necessary for spinning up VM in (key, value) pair
       key value pair is adopted for being agnostic to actuall manager of VMs
       like nova, heat or others. e.g. image-id, flavor-id for Nova.
       The interpretation is up to actual driver of hosting device.
       """
       device_id = sa.Column(sa.String(36), sa.ForeignKey('devices.id'),
                             nullable=False)
       device = orm.relationship('Device', backref='kwargs')
       key = sa.Column(sa.String(255), nullable=False)
       # json encoded value. example
       # "nic": [{"net-id": <net-uuid>}, {"port-id": <port-uuid>}]
       value = sa.Column(sa.String(4096), nullable=True)
   
   
   # This is tentative.
   # In the future, this will be replaced with db models of
   # service insertion/chain.
   # Since such models are under discussion/development as of
   # this time, this models is just for lbaas driver of hosting
   # device
   # This corresponds to the instantiation of DP_IF_Types
   class DeviceServiceContext(model_base.BASE, models_v1.HasId):
       """Represents service context of Device for scheduler.
       This represents service insertion/chainging of a given device.
       """
       device_id = sa.Column(sa.String(36), sa.ForeignKey('devices.id'))
       network_id = sa.Column(sa.String(36), nullable=True)
       subnet_id = sa.Column(sa.String(36), nullable=True)
       port_id = sa.Column(sa.String(36), nullable=True)
       router_id = sa.Column(sa.String(36), nullable=True)
   
       role = sa.Column(sa.String(255), nullable=True)
       # disambiguation between same roles
       index = sa.Column(sa.Integer, nullable=True)
   
   
   # this table corresponds to ServiceInstance of the original spec
   class ServiceInstance(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
       """Represents logical service instance
       This table is only to tell what logical service instances exists.
       There will be service specific tables for each service types which holds
       actuall parameters necessary for specific service type.
       For example, tables for "Routers", "LBaaS", "FW", tables. which table
       is implicitly determined by service_type_id.
       """
       name = sa.Column(sa.String(255), nullable=True)
       service_type_id = sa.Column(sa.String(36),
                                   sa.ForeignKey('servicetypes.id'))
       service_type = orm.relationship('ServiceType')
       # points to row in service specific table if any.
       service_table_id = sa.Column(sa.String(36), nullable=True)
   
       # True: This service is managed by user so that user is able to
       #       change its configurations
       # False: This service is manged by other tacker service like lbaas
       #        so that user can't change the configuration directly via
       #        servicevm API, but via API for the service.
       managed_by_user = sa.Column(sa.Boolean(), default=False)
   
       # mgmt driver to communicate with logical service instance in
       # hosting device.
       # e.g. noop, OpenStack MGMT, OpenStack notification, netconf, snmp,
       #      ssh, etc...
       mgmt_driver = sa.Column(sa.String(255))
   
       # For a management tool to talk to manage this service instance.
       # opaque string. mgmt_driver interprets it.
       mgmt_address = sa.Column(sa.String(255), nullable=True)
   
       service_context = orm.relationship('ServiceContext')
       devices = orm.relationship('ServiceDeviceBinding')
   
       status = sa.Column(sa.String(255), nullable=False)
   
   
   # This is tentative.
   # In the future, this will be replaced with db models of
   # service insertion/chain.
   # Since such models are under discussion/development as of
   # this time, this models is just for lbaas driver of hosting
   # device
   # This corresponds to networks of Logical Service Instance in the origianl spec
   class ServiceContext(model_base.BASE, models_v1.HasId):
       """Represents service context of logical service instance.
       This represents service insertion/chainging of a given device.
       This is equal or subset of DeviceServiceContext of the
       corresponding Device.
       """
       service_instance_id = sa.Column(sa.String(36),
                                       sa.ForeignKey('serviceinstances.id'))
       network_id = sa.Column(sa.String(36), nullable=True)
       subnet_id = sa.Column(sa.String(36), nullable=True)
       port_id = sa.Column(sa.String(36), nullable=True)
       router_id = sa.Column(sa.String(36), nullable=True)
   
       role = sa.Column(sa.String(255), nullable=True)
       index = sa.Column(sa.Integer, nullable=True)        # disambiguation
   
   
   class ServiceDeviceBinding(model_base.BASE):
       """Represents binding with Device and LogicalResource.
       Since Device can accomodate multiple services, it's many-to-one
       relationship.
       """
       service_instance_id = sa.Column(
           sa.String(36), sa.ForeignKey('serviceinstances.id'), primary_key=True)
       device_id = sa.Column(sa.String(36), sa.ForeignKey('devices.id'),
                             primary_key=True)
   
   

REST API impact
---------------

.. code-block:: python

   RESOURCE_ATTRIBUTE_MAP = {
   
       'device_templates': {
           'id': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True,
           },
           'tenant_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'required_by_policy': True,
               'is_visible': True,
           },
           'name': {
               'allow_post': True,
               'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True,
               'default': '',
           },
           'description': {
               'allow_post': True,
               'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True,
               'default': '',
           },
           'service_types': {
               'allow_post': True,
               'allow_put': False,
               'convert_to': attr.convert_to_list,
               'validate': {'type:service_type_list': None},
               'is_visible': True,
               'default': attr.ATTR_NOT_SPECIFIED,
           },
           'device_driver': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
               'default': attr.ATTR_NOT_SPECIFIED,
           },
           'mgmt_driver': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
               'default': attr.ATTR_NOT_SPECIFIED,
           },
           'attributes': {
               'allow_post': True,
               'allow_put': False,
               'convert_to': attr.convert_none_to_empty_dict,
               'validate': {'type:dict_or_nodata': None},
               'is_visible': True,
               'default': None,
           },
       },
   
       'devices': {
           'id': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True
           },
           'tenant_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'required_by_policy': True,
               'is_visible': True
           },
           'template_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
           },
           'instance_id': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'mgmt_address': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'kwargs': {
               'allow_post': True,
               'allow_put': True,
               'validate': {'type:dict_or_none': None},
               'is_visible': True,
               'default': {},
           },
           'service_contexts': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:service_context_list': None},
               'is_visible': True,
           },
           'services': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
           },
           'status': {
               'allow_post': False,
               'allow_put': False,
               'is_visible': True,
           },
       },
   
       'service_instances': {
           'id': {
               'allow_post': False,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True
           },
           'tenant_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'required_by_policy': True,
               'is_visible': True
           },
           'name': {
               'allow_post': True,
               'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'service_type_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
           },
           'service_table_id': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'mgmt_driver': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'mgmt_address': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': True,
           },
           'service_contexts': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:service_context_list': None},
               'is_visible': True,
           },
           'devices': {
               'allow_post': True,
               'allow_put': False,
               'validate': {'type:uuid_list': None},
               'convert_to': attr.convert_to_list,
               'is_visible': True,
           },
           'status': {
               'allow_post': False,
               'allow_put': False,
               'is_visible': True,
           },
           'kwargs': {
               'allow_post': True,
               'allow_put': True,
               'validate': {'type:dict_or_none': None},
               'is_visible': True,
            'default': {},
           },
       },
   }


Security impact
---------------

None

Notifications impact
--------------------

None


Other end user impact
---------------------

None


Performance Impact
------------------

None


Other deployer impact
---------------------

TBD


Developer impact
----------------

Some Neutron driver needs to be aware of this project.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  yamahata
  bob-melander 
  balaji
  to be added

Other contributors:
  To be added

Work Items
----------

* API: define API which consolidates existing implementations
* db model
* make implmentation working
* start incubation process
* testing
* documentation


Dependencies
============

* nova client
* neutron driver needs to be written to use this project
* glance?


Testing
=======

* unit test
* devstack
* tempest


Documentation Impact
====================

all kind of documentations needs to be written


References
==========

* https://wiki.openstack.org/wiki/ServiceVM
* links to NFV team
  * https://wiki.openstack.org/wiki/Meetings/NFV
  * https://etherpad.openstack.org/p/juno-nfv-bof
