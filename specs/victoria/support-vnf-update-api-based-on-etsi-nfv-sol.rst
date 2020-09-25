..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


=================================================================
Support VNF update operations based on ETSI NFV-SOL specification
=================================================================

https://blueprints.launchpad.net/tacker/+spec/support-etsi-nfv-specs

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on of the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================

In the current Tacker implementation based on ETSI NFV-SOL,
Tacker uses its own API which describes VNF update operations
which is Ability to execute a VNF application software modification.

However, these operations are not aligned with the current ETSI NFV
data-model. As a result, there might be lack of compatibility with `3rd
party VNFs` [#etsi_plugtest2]_, as they are developed according to ETSI
NFV specifications.  Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into Telecom production
networks and also will simplify further development and support of future
standards.

Proposed change
===============

Introduce a new interface for updating information about a VNF instance.

The operation provided through this interface is:
* Modify VNF

The following items can be updated by this operation.:
- vnfInstanceName
- vnfInstanceDescription
- vnfdId
- metadata
- vimConnectionInfo

1) Flow of the Modify VNF Information operation (change vnfdId)
---------------------------------------------------------------

Precondition: The resource representing the VNF instance has been created.
The VNF Package used for "Modify VNF" has been onboarded in NFVO.

.. seqdiag::

  seqdiag {
    Client; NFVO; tacker-server; tacker-conductor;

    Client -> "tacker-server" [label = "PATCH /vnf_instances/{vnfInstanceId}"];
    "tacker-server" -> "tacker-conductor" [label = "execute vnf_package list process{filter}"];
    NFVO <- "tacker-conductor" [label = "GET /vnf_packages/ with attribute filter(vnfdId)"];
    NFVO --> "tacker-conductor" [label = "Response 200 OK with VnfPkgInfo"];
    "tacker-server" <<- "tacker-conductor" [label = "(VnfPkgInfo)"];
    "tacker-server" ->> "tacker-server" [label = "Update VNF instance resource(VnfPkgInfo)"];
    "tacker-server" -> "tacker-conductor" [label = "execute vnf_package content process{vnfPkgId}"];
    NFVO <- "tacker-conductor" [label = "GET /vnf_packages/{vnfPkgId}/package_content "];
    NFVO --> "tacker-conductor" [label = "Response 200 OK with VNF package file"];
    "tacker-server" <<- "tacker-conductor" [label = "(VNF package content file)"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor" [label = "trriger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" ->> "tacker-conductor" [label = "VNF Modification"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


The procedure consists of the following steps as illustrated in above sequence:

#. The Client sends a PATCH request to the "Individual VNF instance" resource.
#. If VNFM does not have target VNF Package, VNFM gets it from NFVO.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. The VNFM has finished the modification operation.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification  with the "COMPLETED" state to indicate the completion
   occurrence of the lifecycle management operation.

Postcondition: After successful completion, information of the VNF
instance is updated.

2) Flow of the Modify VNF Information operation (Other changes)
------------------------------------------------------------------

Precondition: The resource representing the VNF instance has been created.

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = "PATCH /vnf_instances/{vnfInstanceId}"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor" [label = "trriger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" ->> "tacker-conductor" [label = "VNF Modification"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


#. The Client sends a PATCH request to the "Individual VNF instance" resource.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. The VNFM has finished the modification operation.
#. VNFM sends to the Client a VNF lifecycle management operation occurrence
   notification  with the "COMPLETED" state to indicate the completion
   occurrence of the lifecycle management operation.

Postcondition: After successful completion, information of the VNF instance
is updated.

Alternatives
------------

None

Data model impact
-----------------

Modify following tables in current ‘tacker’ database. The corresponding
schemas are detailed below:-

vnf_instances::
    vnf_metadata vnf_metadata json

REST API impact
---------------

The following restFul API will be added. This restFul API will be based on
ETSI NFV SOL002 [#NFV-SOL002]_ and SOL003 [#NFV-SOL003]_.

* | **Name**: Modify VNF Instances
  | **Description**: Modify an Individual VNF instance resource.
  | **Method type**: PATCH
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}
  | **Request**: Resource URI variables for this resource

  +------------------------+------------------------------------------------+
  | Name                   | Description                                    |
  +========================+================================================+
  | VnfModificationRequest | Identifier of the VNF instance to be modified. |
  +------------------------+------------------------------------------------+

  | **Request**:

  .. list-table::
     :header-rows: 1
     :widths: 18 10 50

     * - Data type
       - Cardinality
       - Description
     * - VnfModificationRequest
       - 1
       - Parameters for the Scale VNF operation.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in (V)
     * - vnfInstanceName
       - String
       - 0..1
       - Yes
     * - vnfInstanceDescription
       - String
       - 0..1
       - Yes
     * - vnfPkgId
       - Identifier
       - 1
       - Yes
     * - vnfdId
       - Identifier
       - 1
       - Yes
     * - vnfConfigurableProperties
       - KeyValuePairs
       - 0..1
       - No
     * - vimConnectionInfo
       - VimConnectionInfo
       - 0..N -> 0..1
       - Yes
     * - metadata
       - KeyValuePairs
       - 0..1
       - Yes
     * - extensions
       - KeyValuePairs
       - 0..1
       - No
     * - vnfcInfoModifications
       - VnfcInfoModificartions
       - 0..1
       - No
     * - vnfcInfoModificationsDeleteIds
       - Identifier
       - 0..N
       - No
     * - vimConnectionInfoDeleteIds
       - Identifier
       - 0..N
       - No

  .. note::
      vnfPkgId is not available in SOL 002 /003 v2.6.1 but in v2.4.1. However,
      most NFV related equipment, such as NFVO, still utilize v2.4.1 API
      and this attribute is mondatory for executing VNF update operation.
      So, Tacker will support vnfPkgId in Victoria release. Whether or not
      continue to support v2.4.1 API and attributes for the future release
      will be decided based on the requirements of service providers and the
      situation of NFV product.

  .. note::
      vimConnectionInfo shows multiple VIMs per VNF. However due to the
      partial support of this feature in the ETSI present release, the number
      of entries in the VIMs attribute is not greater than 1.

  | **Response**:

  .. list-table::
     :widths: 10 10 20 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - n/a
       - n/a
       - | Success 202
         | Error 409
       - The request was accepted for processing, but the processing has not
         been completed.

  .. note::
      According to the ETSI NFV SOL document, there is no API request/response
      specification for Etag yet, and transactions using Etag are not defined
      by standardization. Therefore, the Victoria release does not support
      `Error Code: 412 Precondition Failed`. Once a standard specification
      for this is established, it will be installed on the tacker.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

Add new OSC commands in python-tackerclient to invoke VNF update operations
of VNF instances API.

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

* Add new REST API endpoints to Tacker-server for VNF update operations
  of VNF instances.
* Make changes in python-tackerclient to add new OSC commands for calling
  updating operations of VNF instances restFul APIs.
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
