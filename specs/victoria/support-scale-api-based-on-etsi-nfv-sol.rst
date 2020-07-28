..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


======================================================================
Support scaling operations for VNF based on ETSI NFV-SOL specification
======================================================================

https://blueprints.launchpad.net/tacker/+spec/support-etsi-nfv-specs

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on of the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================

In the current Tacker implementation based on ETSI NFV-SOL,
Tacker uses its own API which describes scaling operations
which is Ability to dynamically extend/reduce resources granted
to the Virtual Network Function (VNF) as needed.

However, these operations are not aligned with the current ETSI NFV
data-model. As a result, there might be lack of compatibility with `3rd
party VNFs` [#etsi_plugtest2]_, as they are developed according to ETSI
NFV specifications.  Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into Telecom production
networks and also will simplify further development and support of future
standards.

Proposed change
===============

Introduce a new interface to invoke VNF lifecycle management operations of VNF
instances towards the VNFM.
The operation provided through this interface is:

* Scale VNF

1) Flow of Scale Out of a VNF instance
--------------------------------------

Precondition: VNF instance in INSTANTIATED state.

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    Client -> "tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/scale"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-server" -> "tacker-conductor"
      [label = "trriger asynchronous task"];
    Client <- "tacker-conductor" [label = "POST /grants"];
    Client --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "resourse signal"];
    "openstackDriver" -> "heat" [label = "update stack"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "MgmtDriver" [label = "execute MgmtDriver"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "tacker-conductor" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


The procedure consists of the following steps as illustrated in above sequence:

#. Client sends a POST request to the Scale VNF Instance resource.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM and Client exchange granting information.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. OpenstackDriver sends resource-signal request to Heat to scale out the
   resource. The number of VMs to scale out is calculated by multiplying
   "number_of_steps" contained in Scale VNF request and "number_of_instances"
   contained in VNFD.
#. OpenstackDriver sends request to Heat to update the stack, and the
   "desired_capacity", contained in HOT of the target VM, is incremented.
   As a Heat specification, "desired_capacity" is referenced during
   UpdateStack, this process is performed so as to prevent returning to
   the previous number of VMs at the time of the next UpdateStack.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state to indicate the completion
   occurrence of the lifecycle management operation.

When scaling multiple VMs, resource-signal and Update Stack are repeated as
a set for each VM.

Postcondition: VNF instance is still in INSTANTIATED state and VNF has been
scaled.


2) Flow of Scale in of a VNF instance
-------------------------------------

Precondition: VNF instance in INSTANTIATED state.

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    Client -> "tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/scale"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-server" -> "tacker-conductor"
      [label = "trriger asynchronous task"];
    Client <- "tacker-conductor" [label = "POST /grants"];
    Client --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "MgmtDriver" [label = "execute MgmtDriver"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
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
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


The procedure consists of the following steps as illustrated in above sequence:

#. Client sends a POST request to the Scale VNF Instance resource.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM and Client exchange granting information.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. OpenstackDriver sends resource-signal request to Heat to scale in the
   resource. The number of VMs to scale in is calculated by multiplying
   "number_of_steps" contained in Scale VNF request and "number_of_instances"
   contained in VNFD.
#. OpenstackDriver sends request to Heat to update the stack, and the
   "desired_capacity", contained in HOT of the target VM, is decremented.
   As a Heat specification, "desired_capacity" is referenced during
   UpdateStack, this process is performed so as to prevent returning to the
   previous number of VMs at the time of the next UpdateStack.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state to indicate the completion
   occurence of the lifecycle management operation.

When scaling multiple VMs, resource-signal and Update Stack are repeated as
a set for each VM.

When scale-in (resource-signal) is executed using Heat, Heat operates to
delete the VM which was created at first. Depending on the VNF, it may be
necessary to delete the VM that is last created . Therefore, it is
possible to select the order of VM removal in 'additionalParams' as
scaling request parameter. If isReverse in 'additionalParams' is True,
delete from the last registered VM. If not, delete from first registered
VM. If 'additionalParams' is not set, the behavior is the same as False.

Postcondition: VNF instance still in INSTANTIATED state and VNF has been
scaled.

Alternatives
------------

None

Data model impact
-----------------

Modify following tables in current Tacker database. The corresponding
schemas are detailed below:-

vnf_instantiated_info::
    scale_status scale_status json

vnf_lcm_op_occs::
    operation_params operation_params json

"operation_parames" stores additionalParams attribute of ScaleVNF Request.
It is used for getting operation status from NFVO.

REST API impact
---------------

The following restFul API will be added. This restFul API will be based on
ETSI NFV SOL002 [#NFV-SOL002]_ and SOL003 [#NFV-SOL003]_.

* | **Name**: Scale VNF Instances
  | **Description**: Scale by add/remove VNF instance resources
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}/scale
  | **Request**: Resource URI variables for this resource

  +---------------+------------------------------------------------------+
  | Name          | Description                                          |
  +===============+======================================================+
  | vnfInstanceId | The identifier of the VNF instance to be scaled.     |
  +---------------+------------------------------------------------------+

  | **Request**:

  +------------------+-------------+-----------------------------------------+
  | Data type        | Cardinality | Description                             |
  +==================+======+======+=========================================+
  | ScaleVnfRequest  | 1           | Parameters for the Scale VNF operation. |
  +------------------+-------------+-----------------------------------------+

  +---------------------+-------------------+-------------+------------------+
  | Attribute name      | Data type         | Cardinality | Supported in (V) |
  +=====================+===================+=============+==================+
  | type                | Enum(inlined)     | 1           |    Yes           |
  +---------------------+-------------------+-------------+------------------+
  | aspectId            | IdentifierInVnfd  | 1           |    Yes           |
  +---------------------+-------------------+-------------+------------------+
  | numberOfSteps       | Integer           | 0..1        |    Yes           |
  +---------------------+-------------------+-------------+------------------+
  | additionalParams    | KeyValuePairs     | 0..1        |    Yes           |
  +---------------------+-------------------+-------------+------------------+


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
       - The request was accepted for processing, but the processing has not
         been completed.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

Add new OSC commands in python-tackerclient to invoke scaling operations of
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

* Add new REST API endpoints to Tacker-server for scaling operations
  of VNF instances.
* Make changes in python-tackerclient to add new OSC commands for calling
  scaling operations of VNF instances restFul APIs.
* Add new unit and functional tests.
* Change API Tacker documentation.

Dependencies
============

None

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
