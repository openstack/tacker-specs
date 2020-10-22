..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===================================================
Support ETSI NFV-SOL based error-handling operation
===================================================

https://blueprints.launchpad.net/tacker/+spec/support-error-handling

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================

In the current Tacker implementation based on ETSI NFV-SOL,
Tacker executes its own error-handling operation which reacts to errors the
VNFM encounters.

However, those operations are not aligned with the current ETSI NFV
data-model. As a result, there might be a lack of compatibility with `3rd
party VNFs` [#etsi_plugtest2]_, as they are developed according to ETSI
NFV specifications.  Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into Telecom production
networks and also will simplify further development and support of future
standards.

Proposed change
===============

Adding new APIs to VNFM regarding error handling.
The operations provided through these APIs are:

* Retry operation task

  The client can use this API to initiate retrying a VNF
  lifecycle operation.

* Fail operation task

  The client can use this API to mark a VNF lifecycle
  management operation occurrence as "finally failed".
  Once the operation is marked as
  "finally failed", it cannot be retried or rolled back anymore.
  On the basis of the ETSI NFV specification,
  "FAILED" represents "finally failed".

1) Flow of Retry operation
-----------------------------

Precondition: VNF lifecycle management operation occurrence is
in FAILED_TEMP state.
LCM operation that can perform Retry operation are Instantiation,
Termination, Healing, Scaling, and ChangeExternalConnectivity.

.. seqdiag::

  seqdiag {
    Client -> "tacker-server"
      [label = "POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/retry"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "start retry procedure"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" ->> "tacker-conductor" [label = "end retry procedure"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }

#. The Client sends a POST request with an empty body to the "Retry operation task"
   resource.
#. VNFM sends the Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing occurrence
   of the lifecycle management operation.
#. On successful retry, VNFM sends the Client a VNF lifecycle management
   operation occurrence notification with the "COMPLETED" state to indicate
   successful completion of the operation.
#. On unsuccessful retry, VNFM sends the Client a VNF lifecycle management
   operation occurrence notification with the "FAILED_TEMP" state to indicate
   an intermediate error (retry failed) of the operation.

Postcondition: The VNF lifecycle management operation occurrence is in one of the following states:
FAILED_TEMP, COMPLETED.

2) Flow of Fail operation
----------------------------

Precondition: VNF lifecycle management operation occurrence is in
FAILED_TEMP state.
LCM operation that can perform Fail operation are Instantiation,
Termination, Healing, Scaling, and ChangeExternalConnectivity.

.. seqdiag::

  seqdiag {
    Client -> "tacker-server"
      [label = "POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/fail"];
    "tacker-server" -> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "mark operation as failed"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (FAILED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    Client <-- "tacker-server" [label = "Response 200 OK"];
  }

The procedure consists of the following steps as illustrated in above sequence:

#. The client sends a POST request with an empty body to the "Fail operation task"
   resource.
#. VNFM marks the operation as failed.
#. VNFM sends the Client a VNF lifecycle management operation occurrence
   notification with the "FAILED" state to indicate the final failure of the operation.

Postcondition: The VNF lifecycle management operation occurrence is FAILED state.

Alternatives
------------
None

Data model impact
-----------------
None

REST API impact
---------------

The following REST API will be added. This REST API will be based on
ETSI NFV SOL002 [#NFV-SOL002]_ and SOL003 [#NFV-SOL003]_.

* | **Name**: Retry VNF operation
  | **Description**: Request to retry VNF lifecycle operations
  | **Method type**: POST
  | **URL for the resource**:
      /vnflcm/v1/ vnf_lcm_op_occs/{vnfLcmOpOccId}/retry
  | **Request**: Resource URI variables for this resource

  +---------------+-----------------------------------------------------------------------------------------+
  | Name          | Description                                                                             |
  +===============+=========================================================================================+
  | vnfLcmOpOccId | Identifier of the related VNF lifecycle management operation occurrence to be retried.  |
  +---------------+-----------------------------------------------------------------------------------------+

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
       - Success 202
       - The request has been accepted for processing, but processing has
         not been completed.
     * - ProblemDetails
       - 0..1
       - Error 404
       - Error: The API producer did not find a current
         representation for the target resource or is not willing to
         disclose that one exists.
         The general cause for this error and
         its handling is specified in clause 6.4 of
         ETSI GS NFV-SOL 013 [#etsi_sol013]_, not been completed.
     * - ProblemDetails
       - 1
       - Error 409
       - Error: The operation cannot be executed currently, due
         to a conflict with the state of the VNF LCM operation occurrence resource.


* | **Name**: Fail VNF operation
  | **Description**: Request to mark VNF lifecycle operations as "FAILED".
  | **Method type**: POST
  | **URL for the resource**:
      /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/fail
  | **Request**: Resource URI variables for this resource

  +---------------+--------------------------------------------------------------------------------------------------+
  | Name          | Description                                                                                      |
  +===============+==================================================================================================+
  | vnfLcmOpOccId | Identifier of the related VNF lifecycle management operation occurrence to be marked as "failed".|
  +---------------+--------------------------------------------------------------------------------------------------+

  | **Response**:

  .. list-table::
     :widths: 10 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - VnfInstance
       - 0..N
       - | Success: 200
       - The state of the VNF lifecycle management operation occurrence
         has been changed successfully.
     * - ProblemDetails
       - 0..1
       - Error 404
       - Error: The API producer did not find a current
         representation for the target resource or is not willing to
         disclose that one exists.
         The general cause for this error and
         its handling is specified in clause 6.4 of
         ETSI GS NFV-SOL 013 [#etsi_sol013]_, not been completed.
     * - ProblemDetails
       - 1
       - Error 409
       - Error: The operation cannot be executed currently, due
         to a conflict with the state of the VNF LCM operation occurrence resource.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Support in Wallaby
     * - id
       - Identifier
       - 1
       - Yes
     * - operationState
       - LcmOperationStateType
       - 1
       - Yes
     * - stateEnteredTime
       - DateTime
       - 1
       - Yes
     * - startTime
       - DateTime
       - 1
       - Yes
     * - vnfInstanceId
       - Identifier
       - 1
       - Yes
     * - grantId
       - Identifier
       - 0..1
       - Yes
     * - operation
       - LcmOperationType
       - 1
       - Yes
     * - isAutomaticInvocation
       - Boolean
       - 1
       - Yes
     * - operationParams
       - Object
       - 0..1
       - Yes
     * - isCancelPending
       - Boolean
       - 1
       - Yes
     * - cancelMode
       - CancelModeType
       - 0..1
       - No
     * - error
       - ProblemDetails
       - 0..1
       - Yes
     * - >type
       - URI
       - 0..1
       - No
     * - >title
       - String
       - 0..1
       - Yes
     * - >status
       - Integer
       - 1
       - Yes
     * - >detail
       - String
       - 1
       - Yes
     * - >instance
       - URI
       - 0..N
       - No
     * - additional attributes
       - Not specified.
       - 0..1
       - Yes
     * - resourceChanges
       - Structure (inlined)
       - 0..1
       - Yes
     * - >affectedVnfcs
       - AffectedVnfc
       - 0..N
       - Yes
     * - >>id
       - IdentifierInVnf
       - 1
       - Yes
     * - >>vduId
       - IdentifierInVnfd
       - 1
       - Yes
     * - >>changeType
       - Enum (inlined)
       - 1
       - Yes
     * - >>computeResource
       - ResourceHandle
       - 1
       - Yes
     * - >>metadata
       - KeyValuePairs
       - 0..N
       - No
     * - >>affectedVnfcCPIds
       - IdentifierInVnf
       - 0..N
       - Yes
     * - >>addedStorageResourceIds
       - VnfVirtualLinkResourceInfo
       - 0..N
       - Yes
     * - >>removedStorageResourceIds
       - IdentifierInVnf
       - 0..N
       - Yes
     * - >>removedStorageResourceIds
       - IdentifierInVnf
       - 0..N
       - Yes
     * - >affectedVirtualLinks
       - AffectedVirtualLink
       - 0..N
       - Yes
     * - >>id
       - IdentifierInVnf
       - 1
       - Yes
     * - >>vnfVirtualLinkDescId
       - IdentifierInVnfd
       - 1
       - Yes
     * - >>changeType
       - Enum (inlined)
       - 1
       - Yes
     * - >>networkResource
       - resourceHandle
       - 1
       - Yes
     * - >>metadata
       - KeyValuePairs
       - 0..1
       - No
     * - >affectedVirtualStorages
       - AffectedVirtualStorage
       - 0..N
       - Yes
     * - >>id
       - IdentifierInVnf
       - 1
       - Yes
     * - >>VirtualStorageDescId
       - IdentifierInVnfd
       - 1
       - Yes
     * - >>changeType
       - Enum (inlined)
       - 1
       - Yes
     * - >>storageResource
       - resourceHandle
       - 1
       - Yes
     * - >>metadata
       - KeyValuePairs
       - 0..1
       - No
     * - changedInfo
       - VnfInfoModifications
       - 0..1
       - Yes
     * - >vnfInstanceName
       - String
       - 0..1
       - Yes
     * - >vnfInstanceDescription
       - String
       - 0..1
       - Yes
     * - >vnfConfigurableProperties
       - KeyValuePairs
       - 0..1
       - No
     * - >metadata
       - KeyValuePairs
       - 0..1
       - Yes
     * - >extensions
       - KeyValuePairs
       - 0..1
       - No
     * - >vimConnectionInfo
       - vimConnectionInfo
       - 0..N
       - Yes
     * - >>id
       - Identifier
       - 1
       - Yes
     * - >>vimId
       - Identifier
       - 0..1
       - Yes
     * - >>vimType
       - String
       - 1
       - Yes
     * - >>interfaceInfo
       - KeyValuePairs
       - 0..1
       - Yes
     * - >>accessInfo
       - KeyValuePairs
       - 0..1
       - Yes
     * - >>extra
       - KeyValuePairs
       - 0..1
       - No
     * - >vimConnectionInfoDeleteIds
       - Identifier
       - 0..N
       - No
     * - >vnfPkgId
       - Identifier
       - 0..1
       - Yes
     * - >vnfdid
       - Identifier
       - 0..1
       - Yes
     * - >vnfProvider
       - String
       - 0..1
       - Yes
     * - >vnfProductName
       - String
       - 0..1
       - Yes
     * - >vnfSotwareVersion
       - Version
       - 0..1
       - Yes
     * - >vnfdVersion
       - Version
       - 0..1
       - Yes
     * - changedExtConnectivity
       - ExtVirtualLinkInfo
       - 0..N
       - Yes
     * - >id
       - Identifier
       - 1
       - Yes
     * - >resourceHandle
       - ResourceHandle
       - 1
       - Yes
     * - >>vimConnectionId
       - Identifier
       - 0..1
       - Yes
     * - >>resourceProviderId
       - Identifier
       - 0..1
       - No
     * - >>resourceId
       - IdentifierInVim
       - 1
       - Yes
     * - >>vimLevelResourceType
       - String
       - 0..1
       - No
     * - >linkPorts/ extLinkPorts
       - ExtLinkPortInfo
       - 0..N
       - Yes
     * - >>id
       - Identifier
       - 1
       - Yes
     * - >>resourceHandle
       - ResourceHandle
       - 1
       - Yes
     * - >>cpInstanceId
       - IdentifierInVnf
       - 0..1
       - Yes
     * - _links
       - Structure (inlined)
       - 1
       - Yes
     * - >self
       - Link
       - 1
       - Yes
     * - >vnfInstance
       - Link
       - 1
       - Yes
     * - >grant
       - Link
       - 0..1
       - Yes
     * - >cancel
       - Link
       - 0..1
       - No
     * - >retry
       - Link
       - 0..1
       - Yes
     * - >rollback
       - Link
       - 0..1
       - Yes
     * - >fail
       - Link
       - 0..1
       - Yes

The following attributes of REST APIs will be added.
Details of APIs implemented in previous versions are
described in NFV Orchestration API v1.0 [#NFV_Orchestration_API_v1.0]_.

* | **Name**: Query VNF occurrence
  | **Description**: Request individual VNF lifecycle management operation occurrence by its id
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}
  | **Resource URI variables for this resource:**:

  +----------------+---------------------------------------------------------------+
  | Name           | Description                                                   |
  +================+===============================================================+
  | vnfLcmOpOccId  | Identifier of a VNF lifecycle management operation occurrence.|
  +----------------+---------------------------------------------------------------+

  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - VnfLcmOpOcc
       - 1
       - | Success 200
         | Error 4xx
       - The operation has completed successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - _links
       - Structure (inlined)
       - 1
       - Yes
     * - >retry
       - Link
       - 0..1
       - Yes
     * - >fail
       - Link
       - 0..1
       - Yes

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------
Add new OSC commands in python-tackerclient to invoke Retry VNF
operation and Fail VNF operation.

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
  Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>
Other contributors:
  Keiko Kuriu <keiko.kuriu.wa@hco.ntt.co.jp>

Work Items
----------

* Add new REST API endpoints to Tacker-server for LCM notifications interface
  of VNF instances.
* Make changes in python-tackerclient to add new OSC commands for calling
  APIs of Retry VNF operation and Fail VNF Operation.
* Add new unit and functional tests.
* Change API Tacker documentation.

Dependencies
============

To execute retry operation or fail operation, consumer should invoke subscription operation
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
.. [#etsi_plugtest2]
  https://portal.etsi.org/Portals/0/TBpages/CTI/Docs/2nd_ETSI_NFV_Plugtests_Report_v1.0.0.pdf
.. [#NFV-SOL002]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL003]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_sol013]
   https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/02.06.01_60/gs_nfv-sol013v020601p.pdf
   (Chapter 6: Error reporting)
.. [#subscription_spec] https://specs.openstack.org/openstack/tacker-specs/specs/victoria/support-notification-api-based-on-etsi-nfv-sol.html
.. [#NFV_Orchestration_API_v1.0]
   https://docs.openstack.org/api-ref/nfv-orchestration/v1/index.html#virtualized-network-function-lifecycle-management-interface-vnf-lcm

