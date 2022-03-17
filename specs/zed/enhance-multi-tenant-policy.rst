..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


=======================================================
Enhance Multi-tenant policy in VNF Lifecycle Management
=======================================================
https://blueprints.launchpad.net/tacker/+spec/enhance-multi-tenant-policy

This specification discusses the enhancement of multi-tenant policy in the
VNF lifecycle management.

Discussion to enable a non-admin role user to instantiate VNF, tenancy
isolation between admin and the non-admin role users.

Problem description
===================

In tacker, a non-admin role user is able to get resource information
for VNF, but fails to perform certain VNF LCM operations such as VNF
instantiation.

Second, need to implement negative functional test cases for VNF LCM
operations and validate notification is received by the tenant specified
in the subscription sequence.

Proposed change
===============

1. Allow non admin role user to instantiate VNF
-----------------------------------------------

In OpenStack Heat Orchestration Template (HOT) enables the creation of most
OpenStack resource types, such as instances, floating IP addresses, volumes,
security groups and users, collectively known as the stack creation process.

.. note:: By default admin role user is allowed to create an OpenStack stack.

To allow non-admin role users to create VNFs, the OpenStack resource policies
must be changed.

Below mention policies require necessitates change:

#. Heat Policies

   * resource_types:OS::Nova::Flavor
   * resource_types:OS::Cinder::VolumeType
   * resource_types:OS::Neutron::QoSPolicy
   * resource_types:OS::Neutron::QoSBandwidthLimitRule

#. Nova Policies

   * os_compute_api:os-flavor-manage
   * os_compute_api:os-flavor-manage:create
   * os_compute_api:os-flavor-manage:delete

#. Neutron Policies

   * create_policy
   * create_policy_bandwidth_limit_rule

.. note:: As per the investigation, OpenStack allows admin role users to create
   stack, creation process involves different OpenStack services (such as Heat,
   Nova, Glance, etc.).

   To enable a non-admin role user requires the above mention policy changes
   as well as code level changes in desired OpenStack services as well.

   Adjourning investigation for this cycle, in future we can resume.

2. Design for negative functional test cases
--------------------------------------------

The functional test case architecture for a multi-tenant environment,
as described in spec [#ADD-MTPOLICY]_, dedicates a subscription notification
server for each tenant. Validates that these servers only receive alerts
of VNF package or LCM operations conducted by their respective tenants.

To address the design requirement, multiple instances of a fake HTTP server
was created, one for each tenant, to function as notification servers.
In Zuul, the fake HTTP server class instances run on the same test node
(controller-tacker).
In single tenancy, the desired HTTP requests and responses are fabricated(mock)
in functional test cases.
Similarly in a multi-tenant environment, mock HTTP requests and responses for
notification servers, with additional validation of tenant details present in
notification.

Alternatives
------------

An alternate approach to designing a negative functional test case in Zuul,
where two distinct nodes are needed to construct notification servers.

This approach has the following design/implementation challenges:

* Adding two new Zuul nodes with a specific port open (opening a port in Zuul
  may necessitate a special request).

* On the new nodes, use ansible-playbook or similar to set up an HTTP server.

* A network issue may cause the actual HTTP request to timeout.

Data model impact
-----------------

None

REST API impact
---------------

None

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

None

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Manpreet Kaur <kaurmanpreet2620@gmail.com>

Work Items
----------

* Identify and enable the OpenStack policies that allow non admin role
  users to create VNF.
* Add negative functional test cases for VNF LCM operations and validate
  notification is received by the tenant specified in the subscription
  sequence.

Dependencies
============

None

Testing
=======

Functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

None

References
==========

.. [#ADD-MTPOLICY] https://specs.openstack.org/openstack/tacker-specs/specs/yoga/multi-tenant-policy.html
