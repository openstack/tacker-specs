..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


=========================================
Support ETSI NFV-SOL based error-handling
=========================================

https://blueprints.launchpad.net/tacker/+spec/support-etsi-nfv-specs

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on of the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================

In the current Tacker implementation based on ETSI NFV-SOL,
Tacker executes its own error-handling operation which reacts to errors the
VNFM encounters.

However, those operations are not aligned with the current ETSI NFV
data-model. As a result, there might be lack of compatibility with `3rd
party VNFs` [#etsi_plugtest2]_, as they are developed according to ETSI
NFV specifications.  Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into Telecom production
networks and also will simplify further development and support of future
standards.

Proposed change
===============

Introduces a new interface to VNFM for reverting VNF lifecycle management
operations for VNF instances.
The operation provided through this interface is:

* Rollback

1) Flow of Rollback of LCM resource
-----------------------------------

Precondition: The operation state should be set in "FAILED_TEMP" state.
Moreover, ongoing lifecycle management operation should be either VNF
instantiation or Scaling-out.

The procedure consists of the following steps as illustrated in each
sections.

1-1) Sending of Notification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* VNFM holds the Callback URL sent by consumer via "Subscription API" in
  advance.
* Depending on the progress status of the lifecycle management operations,
  send API notification (Notify) to notify the status change and update
  the internal operation_status.
* The node that received the notification returns 204 NO CONTENT indicating
  success and grasps the sequence status of VNFM.

The states that VNFM notifies with VNF Rollback are as follows:

- ROLLING_BACK
- ROLLED_BACK

Postcondition:
When the rollback operation is completed successfully, the operation state
will be changed in "ROLLEDBACK" state.

1-2) Rollback LCM operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a Rollback request is received, VNFM operates to stop the lifecycle
operation normally while it is terminated.
When the rollback operation is executed during VNF instantiation, VNFM
removes all VMs and resources.

.. seqdiag::

  seqdiag {
    node_width = 105;
    edge_length = 130;

    Client -> "tacker-server"
      [label = "POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor"
      [label = "trriger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
     [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "delete stack"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


When the rollback operation is executed for Scale-out, VNFM deletes all VMs
and resources specified in the middle of Scale-out operation.

.. seqdiag::

  seqdiag {
    node_width = 72;
    edge_length = 100;

    Client -> "tacker-server"
      [label = "POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor"
      [label = "trriger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "MgmtDriver" [label = "execute MgmtDriver"];
    "MgmtDriver" -> vnf [label = "VNF Configuration"];
    "MgmtDriver" <-- vnf [label = ""];
    "tacker-conductor" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "resourse signal"];
    "openstackDriver" -> "heat" [label = "update stack"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


User needs to separately implement Rollback sub-operation by VNF Configuration.
In case of Scale-out, VNFM starts VNF Configuration for rollbacking.
Instantiation does not launch VNF Configutration.

Postcondition: When Rollback is successfully completed,  the instantiation
state has transited to NOT_INSTANTIATED state only for "Instantiate VNF".

Alternatives
------------
None

Data model impact
-----------------
None

REST API impact
---------------

The following RESTful API will be added. This RESTful API will be based on
ETSI NFV SOL002 and SOL003 [#NFV-SOL003]_.

* | **Name**: Rollback VNF oepration
  | **Description**: Request to rollback VNF lifecycle operations
  | **Method type**: POST
  | **URL for the resource**:
      /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback
  | **Request**: Resource URI variables for this resource

  +---------------+---------------------------------------------------------------------------+
  | Name          | Description                                                               |
  +===============+===========================================================================+
  | vnfLcmOpOccId | Identifier of the related VNF lifecycle management operation occurrence.  |
  +---------------+---------------------------------------------------------------------------+

  | **Response**:

  .. list-table::
     :widths: 10 10 16 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description

     * - n/a
       - n/a
       - | Success 202
         | Error 404 409
       - The request has been accepted for processing, but processing has
         not been completed.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------
Add new OSC commands in python-tackerclient to invoke rollback operation of
VNF instances API.

Performance Impact
------------------

None

Other deployer impact
---------------------

The previously created VNFs will not be allowed to be managed using the newly
introduced APIs.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Keiko Kuriu <keiko.kuriu.wa@hco.ntt.co.jp>

Work Items
----------

* Add new REST API endpoints to Tacker-server for LCM notifications interface
  of VNF instances.
* Make changes in python-tackerclient to add new OSC commands for calling
  rollback operation of VNF instances RESTful APIs.
* Add features which Tacker consumes Rest API for Notifications
* Add new unit and functional tests.
* Change API Tacker documentation.

Dependencies
============

To execute rollback operations, consumer should invoke subscription operaiton
[#subscription_spec]_ in advance in order to get "vnfLcmOpOccId" related to
the target LCM operation.

Testing
========

Unit and functional test cases will be added for VNF lifecycle management
of VNF instances.

Documentation Impact
====================

Complete user guide will be added to explain how to invoke VNF lifecycle
management of VNF instances with examples.

References
==========

.. [#etsi_nfv] https://www.etsi.org/technologies-clusters/technologies/NFV
.. [#NFV-SOL002]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL003]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_plugtest2]
  https://portal.etsi.org/Portals/0/TBpages/CTI/Docs/2nd_ETSI_NFV_Plugtests_Report_v1.0.0.pdf
.. [#subscription_spec] https://review.opendev.org/#/c/731718/
