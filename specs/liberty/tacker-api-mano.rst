..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Implement Tacker API v1 based on NFV MANO
==========================================

https://blueprints.launchpad.net/tacker/+spec/tacker-api-mano

This spec describes the plan to introduce new Tacker REST API endpoints based
on ETSI NFV MANO standards [1]. The current REST API endpoints based on
'servicevm' standards will be retained for backward compatibility and support.


Problem description
===================

Tacker service currently implements REST API endpoints based on 'servicevm'
standards. However, Tacker is built on principles of an NFV orchestrator with
in-built VNF Manager as described in the ETSI NFV MANO architecture [1]. Tacker
should support and implement CRUD operations on VNF resources. Towards this,
REST API endpoints based on VNF has to be introduced which can then be invoked
by a user using an independent client or through the python-tackerclient
itself.


Proposed change
===============

The actual task of moving Tacker from 'servicevm' to NFV MANO standards in
entirety is complex and will be done in phases. As part of this spec, the task
concerning REST API endpoints based on NFV MANO will be introduced and
implemented. The proposed changes involve the following action items:

* Tacker REST API extension will be moved from 'servicevm' to 'vnfm'.
* Add two new REST API end points 'vnf' and 'vnfd' to describe VNF resources.
* The exiting resources 'device' and 'device_template' will be moved under the
  new 'vnfm' extension.
* The implementation of 'vnfm' REST API will be a wrapper around existing
  'servicevm' implementation.
* The 'vnfm' resource attributes will be the same as 'servicevm' resources
  except for 'services' attribute which is not being used in the project
  currently.

The new 'vnfm' extension will be integrated to Tacker v1 REST API. The current
implementation of 'servicevm' extension will be retained for backward
compatibility.

Alternatives
------------
Other solution is to integrate the Pecan framework in to Tacker. This involves
re-factoring the entire project in one phase to update to NFV MANO standards.
Currently, tacker is based on stable Kilo release branch and does not support
Pecan framework. This solution can only be implemented when Tacker moves to
master release for OpenStack services. The high-level tasks include:


* Modify plugin and database backend implementation to move from servicevm to
  NFV MANO standards.
* Move out of home grown REST framework and implement the Pecan framework to
  describe and implement CRUD operations on VNF resources.

Data model impact
-----------------
None

REST API impact
---------------

New extension 'vnfm' will be introduced in v1 which will implement REST API
end points as described below:

**/vnfd**

::

 +---------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description        |
 |Name          |       |        |Value     |Conversion  |                   |
 +---------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity           |
 |              |(UUID) |        |          |            |                   |
 +---------------------------------------------------------------------------+
 |name          |string |RW, All |''        |string      |human+readable     |
 |              |       |        |          |            |name               |
 +---------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of     |
 |              |       |        |          |            |template           |
 +---------------------------------------------------------------------------+
 |attributes    |dict   |RW, All |None      |dict        |TOSCA YAML file    |
 |              |       |        |          |            |                   |
 +---------------------------------------------------------------------------+
 |infra_driver  |string |RW, All |heat      |string      |driver to provision|
 |              |       |        |          |            |VNF                |
 +---------------------------------------------------------------------------+
 |mgmt_driver   |string |RW All  |noop      |string      |driver to configure|
 |              |       |        |          |            |VNF                |
 +---------------------------------------------------------------------------+
 |service_types |list   |RW, All |[]        |service_type|NFV service type   |
 |              |       |        |          |_list       |(VNF, NSD)         |
 +---------------------------------------------------------------------------+
 |tenant_id     |string |RO, All |N/A       |string      |project id to      |
 |              |       |        |          |            |launch VNF         |
 +--------------+-------+--------+----------+--------------------------------+


**/vnf**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RW, All |''        |string      |human+readable      |
 |              |       |        |          |            |name                |
 +----------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of      |
 |              |       |        |          |            |template            |
 +----------------------------------------------------------------------------+
 |attributes    |dict   |RW, All |None      |dict        |TOSCA YAML file     |
 |              |       |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |instance_id   |string |RO, All |generated |string      |identity of         |
 |              |       |        |          |            |VM instance         |
 +----------------------------------------------------------------------------+
 |mgmt_url      |string |RO, All |None      |string      |IP address of       |
 |              |       |        |          |            |VNF management net. |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RW, All |generated |string      |project id to       |
 |              |       |        |          |            |launch VNF          |
 +----------------------------------------------------------------------------+
 |template_id   |string |RW, All |None      |string      |VNFD id             |
 |              |       |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of VNF              |
 +--------------+-------+--------+----------+---------------------------------+
 |service_      |list   |RW, All |[]        |service_    |VNF role for a given|
 |contexts      |       |        |          |context_list|network             |
 +--------------+-------+--------+----------+---------------------------------+


Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

There will be no direct impact on python-tackerclient in the way the user
will interact with the client. With the current implementation, VNF resource
requests were internally forwarded to 'servicevm' resource requests. However,
with the new implementation, python-tackerclient will directly invoke the
'vnfm' REST API for VNF resource requests.

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
  sseetha

Other contributors:
  None

Work Items
----------

1. Add new extension 'vnfm' to tacker v1 and deprecate the existing 'servicevm'
   extension.
2. The new extension should internally call servicevm plugin base.
3. Modify VNFM API requests from tackerclient to reflect VNF resources in
   request body and remove the current wrapper implementation around
   'servicevm'.
4. Add unit tests for the new extension and contribute to existing API related
   test cases.
5. Add REST api doc file that will capture the 'vnfm' extension in detail.

Dependencies
============

None

Testing
=======

As of now, there are no tempest tests added to Tacker and will be tracked as a
separate activity.

Documentation Impact
====================

A documentation page capturing the new REST API VNF v1 resources will be added
in Tacker wiki link [2].


References
==========

[1] http://www.ietf.org/proceedings/88/slides/slides-88-opsawg-6.pdf
[2] https://wiki.openstack.org/wiki/Tacker/API
