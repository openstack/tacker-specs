..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


================================================
Support ETSI NFV-SOL_v3 error-handling operation
================================================
https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-error-handling

This specification supports a new version of VNF lifecycle management APIs
complying with ETSI NFV SOL v3.
It adds a new version of APIs involved in error handling operations
(retry, fail, rollback).

Problem description
===================
ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Support of key ETSI NFV specifications will significantly reduce efforts
for Tacker integration into Telecom production networks and also will
simplify further development and support of future standards.
To integrate Tacker into a wide variety of products,
it should comply with multiple versions of ETSI NFV SOL specifications.
Tacker has already supported VNF lifecycle management operations
defined in ETSI NFV SOL002 v2.6.1 [#NFV-SOL002_261]_ and
SOL003 v2.6.1 [#NFV-SOL003_261]_.
Furthermore, Xena release supported a part of VNF lifecycle management operations
defined in ETSI NFV SOL002 v3.3.1 [#NFV-SOL002_331]_ and SOL003 v3.3.1 [#NFV-SOL003_331]_.
The details of supported APIs are described in Tacker Xena Specifications
[#SOL_v3_starting_and_terminating]_ [#SOL_v3_getting_LCM_information]_.
Tacker should support more VNF lifecycle management operations
defined in ETSI NFV SOL002/003 v3.3.1.


Proposed change
===============
Since the VNF lifecycle management interface version specified in ETSI NFV SOL v3
is "2.0.0", the API major version included in the URI shall be set
to "v2". Supporting v2 APIs involves changing the data type of some attributes and adding
or removing attributes.
To avoid impact on the existing implementation, APIs corresponding to "v2"
should be implemented as a process independent of that of "v1".

This interface supports the following APIs
involved in error handling of lifecycle management operation.

* Retry operation (POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/retry)
* Fail operation (POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/fail)
* Rollback operation (POST /vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback)


1) Flow of Retry operation
-----------------------------

LCM operations that can perform Retry operation are Instantiation,
Termination, Healing, Scaling, Modify and ChangeExternalConnectivity.

.. seqdiag::

  seqdiag {
    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/retry"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
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

The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF lifecycle management operation occurrence is
in FAILED_TEMP state.

#. The Client sends a POST request with an empty body to the "Retry operation"
   resource.
#. VNFM sends endpoints such as Client a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing occurrence
   of the lifecycle management operation.
#. On successful retry, VNFM sends endpoints such as Client a VNF lifecycle management
   operation occurrence notification with the "COMPLETED" state to indicate
   successful completion of the operation.
#. On unsuccessful retry, VNFM sends endpoints such as Client a VNF lifecycle management
   operation occurrence notification with the "FAILED_TEMP" state to indicate
   an intermediate error (retry failed) of the operation.

Postcondition: The VNF lifecycle management operation occurrence is in one of the following states:
FAILED_TEMP, COMPLETED.

.. note:: For details on the retry procedure, refer
  to the specifications [#SOL_v3_starting_and_terminating]_ [#SOL_v3_enhance_LCM_operation]_
  for each VNF lifecycle management operation.

2) Flow of Fail operation
----------------------------

LCM operations that can perform Fail operation are Instantiation,
Termination, Healing, Scaling, Modify and ChangeExternalConnectivity.

.. seqdiag::

  seqdiag {
    Client; tacker-server; tacker-conductor; tacker-database;
    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/fail"];
    "tacker-server" -> "tacker-database"
      [label = "mark operation as failed"];
    "tacker-server" <-- "tacker-database"
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (FAILED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    Client <-- "tacker-server" [label = "Response 200 OK"];
  }

The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF lifecycle management operation occurrence is in
FAILED_TEMP state.

#. The client sends a POST request with an empty body to the "Fail operation"
   resource.
#. VNFM marks the operation as failed.
#. VNFM sends endpoints such as Client a VNF lifecycle management operation occurrence
   notification with the "FAILED" state to indicate the final failure of the operation.

Postcondition: The VNF lifecycle management operation occurrence is FAILED state.


3) Flow of Rollback operation
------------------------------

LCM operations that can perform Rollback operation are Instantiation, Scale-out, Modify, and ChangeExternalConnectivity.

When a Rollback request is received, VNFM operates to stop the lifecycle
operation normally while it is terminated.
As shown in the below, there are differences in
flow of rollback for each VNF lifecycle management operation.

When the rollback operation is executed during VNF instantiation, VNFM
removes all VMs and resources.

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 130;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLING_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
     [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "delete stack if exists"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLED_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


When the rollback operation is executed for scale-out VNF operation, VNFM reverts changes of VMs
and resources specified in the middle of scale-out operation.

.. seqdiag::

  seqdiag {
    node_width = 75;
    edge_length = 100;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLING_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "mark stack unhealthy (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id}/resources/{resource_name_or_physical_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "openstackDriver" -> "heat" [label = "update stack (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLED_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


When the rollback operation is executed during modifying VNF Information, VNFM
simply updates the state of operation.

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 130;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLING_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
     [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLED_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


When the rollback operation is executed during changing external VNF connectivity, VNFM
reverts changes of the external connectivity for VNF instances.

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 130;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLING_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
     [label = "POST {callback URI} (ROLLING_BACK)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" ->> "VnfLcmDriver" [label = "recreated stack parameters using instantiatedVnfInfo"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "update stack (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "tacker-database"
      [label = "mark operation as ROLLED_BACK"];
    "tacker-conductor" <-- "tacker-database"
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (ROLLED_BACK or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


The procedure consists of the following steps as illustrated in above sequences:

Precondition: VNF lifecycle management operation occurrence is
in FAILED_TEMP state.

#. The Client sends a POST request with an empty body to the "Rollback operation"
   resource.
#. VNFM sends endpoints such as Client a VNF lifecycle management operation occurrence
   notification with the "ROLLING_BACK" state to indicate the processing occurrence
   of the lifecycle management operation.
#. On successful rollback, VNFM sends endpoints such as Client a VNF lifecycle management
   operation occurrence notification with the "ROLLED_BACK" state to indicate
   successful completion of the operation.
#. On unsuccessful rollback, VNFM sends endpoints such as Client a VNF lifecycle management
   operation occurrence notification with the "FAILED_TEMP" state to indicate
   an intermediate error (rollback failed) of the operation.

Postcondition: The VNF lifecycle management operation occurrence is in one of the following states:
FAILED_TEMP, ROLLED_BACK.

.. note:: API v1 supports rollback operation for Instantiation and Scale-out.
          API v1 does not support rollback operation for Modify and ChangeExternalConnectivity.


Data model impact
-----------------
The change has no impact for data model.
Since Xena release has already supported all attributes defined
in SOL002 v3.3.1 [#NFV-SOL002_331]_ and SOL003 v3.3.1 [#NFV-SOL003_331]_,
Data objects and Database tables do not need to be changed.


REST API impact
---------------
All defined attributes should be supported in API validation.

* | **Name**: Retry a VNF LCM operation occurrence
  | **Description**: Request to retry a VNF LCM operation occurrence
  | **Method type**: POST
  | **URL for the resource**:
      /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/retry
  | **Request**: Resource URI variables for this resource

  .. list-table::
    :header-rows: 1
    :widths: 2 2

    * - Name
      - Description
    * - vnfLcmOpOccId
      - Identifier of a VNF lifecycle management operation occurrence to be retried.

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
      - Success: 202
      - The request has been accepted for processing, but processing has
        not been completed.
    * - ProblemDetails
      - 0..1
      - Error: 404
      - Error: The API producer did not find a current
        representation for the target resource or is not willing to
        disclose that one exists.
        The general cause for this error and
        its handling is specified in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_, not been completed.
    * - ProblemDetails
      - 1
      - Error: 409
      - Error: The operation cannot be executed currently, due
        to a conflict with the state of the VNF LCM operation occurrence resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Error: Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.




* | **Name**: Fail a VNF LCM operation occurrence
  | **Description**: Request to mark a VNF LCM operation occurrence as "FAILED".
  | **Method type**: POST
  | **URL for the resource**:
      /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/fail
  | **Request**: Resource URI variables for this resource

  .. list-table::
    :header-rows: 1
    :widths: 2 2

    * - Name
      - Description
    * - vnfLcmOpOccId
      - Identifier of the related VNF lifecycle management operation occurrence to be marked as "failed".

  | **Response**:

  .. list-table::
    :widths: 10 10 16 50
    :header-rows: 1

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - VnfLcmOpOcc
      - 1
      - Success: 200
      - The state of the VNF lifecycle management operation occurrence
        has been changed successfully.
    * - ProblemDetails
      - 0..1
      - Error: 404
      - Error: The API producer did not find a current
        representation for the target resource or is not willing to
        disclose that one exists.
        The general cause for this error and
        its handling is specified in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_, not been completed.
    * - ProblemDetails
      - 1
      - Error: 409
      - Error: The operation cannot be executed currently, due
        to a conflict with the state of the VNF LCM operation occurrence resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Error: Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.



  .. list-table::
    :header-rows: 1

    * - Attribute name
      - Data type
      - Cardinality
      - Supported in API v2
      - Supported in API v1
      - Description
    * - id
      - Identifier
      - 1
      - Yes
      - Yes
      -
    * - operationState
      - LcmOperationStateType
      - 1
      - Yes
      - Yes
      -
    * - stateEnteredTime
      - DateTime
      - 1
      - Yes
      - Yes
      -
    * - startTime
      - DateTime
      - 1
      - Yes
      - Yes
      -
    * - vnfInstanceId
      - Identifier
      - 1
      - Yes
      - Yes
      -
    * - grantId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - operation
      - LcmOperationType
      - 1
      - Yes
      - Yes
      - In SOL 002/003, 11 types of values ​​are defined. See note.
    * - isAutomaticInvocation
      - Boolean
      - 1
      - Yes
      - Yes
      -
    * - operationParams
      - Object
      - 0..1
      - Yes
      - Yes
      -
    * - isCancelPending
      - Boolean
      - 1
      - Yes
      - Yes
      -
    * - cancelMode
      - CancelModeType
      - 0..1
      - Yes
      - No
      - In SOL 002/003, 2 types of values ​​are defined: FORCEFUL, GRACEFUL
    * - error
      - ProblemDetails
      - 0..1
      - Yes
      - Yes
      -
    * - >type
      - URI
      - 0..1
      - Yes
      - No
      -
    * - >title
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - >status
      - Integer
      - 1
      - Yes
      - Yes
      -
    * - >detail
      - String
      - 1
      - Yes
      - Yes
      -
    * - >instance
      - URI
      - 0..N
      - Yes
      - No
      -
    * - >additional attributes
      - Not specified.
      - 0..N
      - No
      - No
      -
    * - resourceChanges
      - Structure (inlined)
      - 0..1
      - Yes
      - Yes
      -
    * - >affectedVnfcs
      - AffectedVnfc
      - 0..N
      - Yes
      - Yes
      -
    * - >>id
      - IdentifierInVnf
      - 1
      - Yes
      - Yes
      -
    * - >>vduId
      - IdentifierInVnfd
      - 1
      - Yes
      - Yes
      -
    * - >>vnfdId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>changeType
      - Enum (inlined)
      - 1
      - Yes
      - Yes
      - Permitted values: ADDED, REMOVED, MODIFIED, TEMPORARY
    * - >>computeResource
      - ResourceHandle
      - 1
      - Yes
      - Yes
      -
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - No
      -
    * - >>resourceDefinitionId
      - IdentifierLocal
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>zoneId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - >>affectedVnfcCPIds
      - IdentifierInVnf
      - 0..N
      - Yes
      - Yes
      -
    * - >>addedStorageResourceIds
      - VnfVirtualLinkResourceInfo
      - 0..N
      - Yes
      - Yes
      -
    * - >>removedStorageResourceIds
      - IdentifierInVnf
      - 0..N
      - Yes
      - Yes
      -
    * - >affectedVirtualLinks
      - AffectedVirtualLink
      - 0..N
      - Yes
      - Yes
      -
    * - >>id
      - IdentifierInVnf
      - 1
      - Yes
      - Yes
      -
    * - >>vnfVirtualLinkDescId
      - IdentifierInVnfd
      - 1
      - Yes
      - Yes
      -
    * - >>vnfdId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>changeType
      - Enum (inlined)
      - 1
      - Yes
      - Yes
      - Permitted values: ADDED, REMOVED, MODIFIED, TEMPORARY, LINK_PORT_ADDED, LINK_PORT_REMOVED
    * - >>networkResource
      - resourceHandle
      - 1
      - Yes
      - Yes
      -
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - No
      -
    * - >>vnfLinkPortIds
      - IdentifierInVnf
      - 0..N
      - Yes
      - Yes
      -
    * - >>resourceDefinitionId
      - IdentifierLocal
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>zoneId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - >affectedExtLinkPorts
      - AffectedExtLinkPort
      - 0..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>id
      - IdentifierInVnf
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>changeType
      - Enum (inlined)
      - 1
      - Yes
      - Not defined
      - | Permitted values: ADD, REMOVED
        | New attribute in API v2.
    * - >>extCpInstanceId
      - IdentifierInVnf
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>resourceHandle
      - ResourceHandle
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>resourceDefinitionId
      - IdentifierLocal
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >affectedVirtualStorages
      - AffectedVirtualStorage
      - 0..N
      - Yes
      - Yes
      -
    * - >>id
      - IdentifierInVnf
      - 1
      - Yes
      - Yes
      -
    * - >>VirtualStorageDescId
      - IdentifierInVnfd
      - 1
      - Yes
      - Yes
      -
    * - >>vnfdId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>changeType
      - Enum (inlined)
      - 1
      - Yes
      - Yes
      - Permitted values: ADDED, REMOVED, MODIFIED, TEMPORARY
    * - >>storageResource
      - resourceHandle
      - 1
      - Yes
      - Yes
      -
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - No
      -
    * - >>resourceDefinitionId
      - IdentifierLocal
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>zoneId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 003.
        | New attribute in API v2.
    * - >>metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - changedInfo
      - VnfInfoModifications
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfInstanceName
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfInstanceDescription
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfConfigurableProperties
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - >metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >extensions
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - >vimConnectionInfo
      - map(vimConnectionInfo)
      - 0..N
      - Yes
      - Yes
      - This attribute is defined only in SOL 003.
    * - >>vimId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>vimType
      - String
      - 1
      - Yes
      - Yes
      -
    * - >>interfaceInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >>accessInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >>extra
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfdId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfProvider
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfProductName
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfSoftwareVersion
      - Version
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfdVersion
      - Version
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfcInfoModifications
      - VnfcInfoModifications
      - 0..N
      - Yes
      - Not defined
      - | This attribute is defined in only SOL 002.
        | New attribute in API v2.
    * - >>id
      - IdentifierInVnf
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>vnfcConfigurableProperties
      - KeyValuePairs
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - changedExtConnectivity
      - ExtVirtualLinkInfo
      - 0..N
      - Yes
      - Yes
      -
    * - >id
      - Identifier
      - 1
      - Yes
      - Yes
      -
    * - >resourceHandle
      - ResourceHandle
      - 1
      - Yes
      - Yes
      -
    * - >>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - No
      -
    * - >extLinkPorts
      - ExtLinkPortInfo
      - 0..N
      - Yes
      - Yes
      -
    * - >>id
      - Identifier
      - 1
      - Yes
      - Yes
      -
    * - >>resourceHandle
      - ResourceHandle
      - 1
      - Yes
      - Yes
      -
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Yes
      - No
      -
    * - >>cpInstanceId
      - IdentifierInVnf
      - 0..1
      - Yes
      - Yes
      -
    * - >currentVnfExtCpData
      - VnfExtCpData
      - 1..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>cpdId
      - IdentifierInVnfd
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>cpConfig
      - map(VnfExtCpConfig)
      - 1..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>parentCpConfigId
      - IdentifierInVnf
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>linkPortId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>cpProtocolData
      - CpProtocolData
      - 0..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>layerProtocol
      - Enum (inlined)
      - 1
      - Yes
      - Not defined
      - | Permitted values: IP_OVER_ETHERNET
        | New attribute in API v2.
    * - >>>>ipOverEthernet
      - IpOverEthernetAddressData
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>macAddress
      - MacAddress
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>segmentationId
      - String
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>ipAddresses
      - Structure (inlined)
      - 0..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>type
      - Enum (inlined)
      - 1
      - Yes
      - Not defined
      - | Permitted values: IPV4, IPV6
        | New attribute in API v2.
    * - >>>>>>fixedAddresses
      - IpAddress
      - 0..N
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>numDynamicAddresses
      - Integer
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>addressRange
      - Structure (inlined)
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>>minAddress
      - IpAddress
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>>maxAddress
      - IpAddress
      - 1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >>>>>>subnetId
      - IdentifierInVim
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - modificationsTriggeredByVnfPkgChange
      - ModificationsTriggeredByVnfPkgChange
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfConfigurableProperties
      - KeyValuePairs
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >extensions
      - KeyValuePairs
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfdId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfProvider
      - String
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfProductName
      - String
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfSoftwareVersion
      - Version
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - >vnfdVersion
      - Version
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - vnfSnapshotInfoId
      - Identifier
      - 0..1
      - Yes
      - Not defined
      - New attribute in API v2.
    * - _links
      - Structure (inlined)
      - 1
      - Yes
      - Yes
      -
    * - >self
      - Link
      - 1
      - Yes
      - Yes
      -
    * - >vnfInstance
      - Link
      - 1
      - Yes
      - Yes
      -
    * - >grant
      - Link
      - 0..1
      - Yes
      - Yes
      -
    * - >cancel
      - Link
      - 0..1
      - No
      - No
      -
    * - >retry
      - Link
      - 0..1
      - Yes
      - Yes
      -
    * - >rollback
      - Link
      - 0..1
      - Yes
      - Yes
      -
    * - >fail
      - Link
      - 0..1
      - Yes
      - Yes
      -
    * - >vnfSnapshot
      - Link
      - 0..1
      - No
      - Not defined
      - New attribute in API v2.

  .. note:: LcmOperationType defines the permitted values to
            represent VNF lifecycle operation types in VNF
            lifecycle management operation occurrence resources
            and VNF lifecycle management operation occurrence
            notifications.
            It shall comply with the provisions defined in following table.

  .. list-table::
    :widths: 10 50
    :header-rows: 1

    * - Value
      - Description
    * - INSTANTIATE
      - Represents the "Instantiate VNF" LCM operation.
    * - SCALE
      - Represents the "Scale VNF" LCM operation.
    * - SCALE_TO_LEVEL
      - Represents the "Scale VNF to Level" LCM operation.
    * - CHANGE_FLAVOUR
      - Represents the "Change VNF Flavour" LCM operation.
    * - TERMINATE
      - Represents the "Terminate VNF" LCM operation.
    * - HEAL
      - Represents the "Heal VNF" LCM operation.
    * - OPERATE
      - Represents the "Operate VNF" LCM operation.
    * - CHANGE_EXT_CONN
      - Represents the "Change external VNF connectivity" LCM operation.
    * - MODIFY_INFO
      - Represents the "Modify VNF Information" LCM operation.
    * - CREATE_SNAPSHOT
      - Represents the "Create VNF Snapshot" LCM operation.
    * - REVERT_TO_SNAPSHOT
      - Represents the "Revert To VNF Snapshot" LCM operation.
    * - CHANGE_VNFPKG
      - Represents the "Change current VNF package" LCM operation.


* | **Name**: Rollback a VNF LCM operation occurrence
  | **Description**: Request to rollback a VNF LCM operation occurrence
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback
  | **Resource URI variables for this resource:**:


  .. list-table::
    :header-rows: 1
    :widths: 2 2

    * - Name
      - Description
    * - vnfLcmOpOccId
      - Identifier of a VNF lifecycle management operation occurrence to be rolled back.

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
      - Success: 202
      - The request has been accepted for processing, but processing has
        not been completed.
    * - ProblemDetails
      - 0..1
      - Error: 404
      - Error: The API producer did not find a current
        representation for the target resource or is not willing to
        disclose that one exists.
        The general cause for this error and
        its handling is specified in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_, not been completed.
    * - ProblemDetails
      - 1
      - Error: 409
      - Error: The operation cannot be executed currently, due
        to a conflict with the state of the VNF LCM operation occurrence resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Error: Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.


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
  Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>


Work Items
----------
* Add new version API endpoints to Tacker-server.
* Implement new version API processings for Tacker-conductor.
* Add new unit and functional tests.
* Update the Tacker's API reference.


Dependencies
============

* Instantiate/Terminate operation

  Depends on spec "Support NFV SOL_v3 starting and terminating"
  [#SOL_v3_starting_and_terminating]_.

* Scale/Heal/Modify/Change external vnf connectivity operation

  Depends on spec "Enhance NFV SOL_v3 LCM operation"
  [#SOL_v3_enhance_LCM_operation]_.


Testing
=======
Unit and functional test cases will be added for VNF lifecycle management
of VNF instances.


Documentation Impact
====================

New supported APIs need to be added into Tacker API reference.


References
==========

.. [#etsi_nfv] https://www.etsi.org/technologies-clusters/technologies/NFV
.. [#NFV-SOL002_261]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL003_261]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL002_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_nfv-sol002v030301p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL003_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#SOL_v3_starting_and_terminating]
  https://specs.openstack.org/openstack/tacker-specs/specs/xena/support-nfv-solv3-start-and-terminate-vnf.html
.. [#SOL_v3_getting_LCM_information]
  https://specs.openstack.org/openstack/tacker-specs/specs/xena/support-nfv-solv3-get-information.html
.. [#SOL_v3_enhance_LCM_operation]
  https://specs.openstack.org/openstack/tacker-specs/specs/yoga/enhance-nfv-solv3-lcm-operation.html
.. [#NFV-SOL013_341]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.04.01_60/gs_nfv-sol013v030401p.pdf
