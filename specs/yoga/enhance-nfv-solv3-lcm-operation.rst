..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


================================
Enhance NFV SOL_v3 LCM operation
================================

.. Blueprints:

- https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-scale-vnf
- https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-heal-vnf
- https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-modify-vnf
- https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-change-external-connectivity

This specification supports a new version of VNF lifecycle management APIs
complying with ETSI NFV SOL v3.
It adds a new version of APIs involved in operating instantiated VNF instances
(scale, heal, modify, and change external vnf connectivity).

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
involved in getting information of lifecycle management operation.

* Scale VNF (POST /vnf_instances/{vnfInstanceId}/scale)
* Heal VNF (POST /vnf_instances/{vnfInstanceId}/heal)
* Modify VNF Information (PATCH /vnf_instances/{vnfInstanceId})
* Change External VNF Connectivity (POST /vnf_instances/{vnfInstanceId}/change_ext_conn)


1) Flow of Scale VNF
--------------------

.. seqdiag::

  seqdiag {
    node_width = 72;
    edge_length = 100;

    Client; NFVO; tacker-server; tacker-conductor; VnfLcmDriver; MgmtDriver; openstackDriver; heat; VNF;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/scale"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    NFVO <- "tacker-conductor" [label = "POST /grants"];
    NFVO --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute preamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute preamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" ->> "VnfLcmDriver" [label = "calculate the number of VMs to scale-out or scale-in"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "[only for scale-in] mark stack unhealthy (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id}/resources/{resource_name_or_physical_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "openstackDriver" -> "heat" [label = "update stack (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute postamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute postamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }

The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF instance in INSTANTIATED state.

#. Client sends VNFM a POST request for the Scale VNF Instance.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM and NFVO exchange granting information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. MgmtDriver executes preamble operation according to a MgmtDriver script.
#. The number of VMs to scale is calculated by multiplying
   "number_of_steps" contained in Scale VNF request and "number_of_instances"
   contained in VNFD.
#. Only for scale-in, OpenstackDriver sends Heat mark stack unhealthy request
   for the removed VM.
#. OpenstackDriver sends Heat stack-update request with the incremented
   or decremented "desired_capacity" of AutoScalingGroup for the target VM.
#. MgmtDriver executes postamble operation according to a MgmtDriver script.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state or "FAILED_TEMP" state
   to indicate the result of the lifecycle management operation.


Postcondition: VNF instance is still in INSTANTIATED state and VNF has been
scaled.

.. note:: Scale API version 1 supports *is_reverse* option.
  Scale-in operation with this option deletes VNF from the last registered VM.
  Scale API version 2 does not support this option
  because it deletes VM in this order by default.

.. note:: Tacker does not support *non-uniform deltas*
  defined in ETSI NFV SOL001 [#NFV-SOL001_331]_.
  Therefore, *uniform delta* corresponding to "number_of_instances" can be set
  and "number_of_instances" is the same regardless of scale_level.

2) Flow of Heal VNF
-------------------

The client can specify the target resources for healing
with two parameters in the API request.

- *vnfcInstanceId* is a list which indicates VNFC instances
  for which a healing action is requested.

- *all* indicates whether network resources and storage resources
  are included in the heal target. This is set in the attribute
  of *additionalParams*.

With the combination of these parameters,
Tacker supports the following patterns of healing.

- Pattern A. *vnfcInstanceId* is included in the request.
   - Pattern A-1. *all = False* is included in the request or *all* is not included in the request.
       - Only specified VNFC instances are healed.
   - Pattern A-2. *all = True* are included in the request.
       - Specified VNFC instances and storage resources are healed.
- Pattern B. *vnfcInstanceId* is not included in the request.
   - Pattern B-1. *all = False* is included in the request or *all* is not included in the request.
       - All VNFC instances included in the VNF instance are healed.
   - Pattern B-2. *all = True* are included in the request.
       - All resources included in the VNF instance are healed.
         It includes VNFC instances, network resources, and storage resources
         but not external virtual networks.

The heal operation of pattern B-2 can be implemented by
combining terminate vnf and instantiate vnf.

The following shows the sequence of patterns A-1, A-2, and B-1.

.. seqdiag::

  seqdiag {
    node_width = 72;
    edge_length = 100;

    Client; NFVO; tacker-server; tacker-conductor; VnfLcmDriver; MgmtDriver; openstackDriver; heat; VNF;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/heal"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "NFVO" <- "tacker-conductor" [label = "POST /grants"];
    "NFVO" --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute preamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute preamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "mark stack unhealthy (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id}/resources/{resource_name_or_physical_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "openstackDriver" -> "heat" [label = "update stack (PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute postamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute postamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }

The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF instance in INSTANTIATED state.

#. Client sends a POST request for the Heal VNF Instance.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM and NFVO exchange granting information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. MgmtDriver executes preamble operation according to a MgmtDriver script.
#. OpenstackDriver sends Heat mark stack unhealthy request for the target VM
   according to the heal request parameter.
#. OpenstackDriver sends Heat stack-update request to execute heal.
   When scaling multiple VMs, stack-update are repeated as a set for each VM.
#. MgmtDriver executes postamble operation according to a MgmtDriver script.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state or "FAILED_TEMP" state
   to indicate the result of the lifecycle management operation.

Postcondition: VNF instance in "INSTANTIATED" state, and healed.



3) Flow of the Modify VNF Information
-------------------------------------

.. seqdiag::

  seqdiag {
    node_width = 140;
    edge_length = 340;

    Client; tacker-server; tacker-conductor;

    Client -> "tacker-server" [label = "PATCH vnflcm/v2/vnf_instances/{vnfInstanceId}"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" -> "tacker-conductor" [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" ->> "tacker-conductor" [label = "VNF Modification"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


Precondition: The resource representing the VNF instance has been created.

#. Client sends VNFM a PATCH request for the Modify VNF instance's information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. VNFM modifies the VNF instance's information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state or "FAILED_TEMP" state
   to indicate the result of the lifecycle management operation.

Postcondition: After successful completion, information of the VNF instance
is updated.


4) Flow of Change external VNF connectivity
-------------------------------------------

.. seqdiag::

  seqdiag {
    node_width = 72;
    edge_length = 100;

    Client; NFVO; tacker-server; tacker-conductor; VnfLcmDriver; MgmtDriver; openstackDriver; heat; VNF;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_ext_conn"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "NFVO" <- "tacker-conductor" [label = "POST /grants"];
    "NFVO" --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute preamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute preamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" -> "openstackDriver" [label = "execute openstackDriver"];
    "openstackDriver" -> "heat" [label = "update stack (PUT /v1/{tenant_id}/stacks/{stack_name}/{stack_id})"];
    "openstackDriver" <-- "heat" [label = ""];
    "VnfLcmDriver" <-- "openstackDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute postamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute postamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF instance in INSTANTIATED state.

#. Client sends VNFM a POST request for the change external VNF connectivity.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM and NFVO exchange granting information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. MgmtDriver executes preamble operation according to a MgmtDriver script.
#. OpenstackDriver sends Heat stack-update request
   with the external Virtual Link (VL) and external Connection Point to change.
#. MgmtDriver executes postamble operation according to a MgmtDriver script.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state or "FAILED_TEMP" state
   to indicate the result of the lifecycle management operation.


Postcondition: VNF instance is still in INSTANTIATED state and the external
VNF connectivity has been changed.

This specification supports the following VL's changes.
 - port
 - network.
 - ip address/mac address/allowed_address_pair in VLs.

This specification does not support trunk-parent-port and trunk-sub-port.


Data model impact
-----------------

The change has no impact for data model.

Since Xena release has already supported all attributes defined
in SOL002 v3.3.1 [#NFV-SOL002_331]_ and SOL003 v3.3.1 [#NFV-SOL003_331]_,
data objects and database tables do not need to be changed.


REST API impact
---------------

All defined attributes should be supported in API validation.

* | **Name**: Scale a VNF instance
  | **Description**: Scale-in or scale-out for VNF instance.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v2/vnf_instances/{vnfInstanceId}/scale
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - ScaleVnfRequest
      - 1
      - Parameters for the scale VNF operation.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 10 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Supported in API v2
      - Supported in API v1
      - Description
    * - type
      - Enum
      - 1
      - Yes
      - Yes
      - | Indicates the type of the scale operation requested.
          Permitted values:
        | SCALE_OUT: adding additional VNFC instances to
          the VNF to increase capacity.
        | SCALE_IN: removing VNFC instances from the
          VNF in order to release unused capacity.
    * - aspectId
      - IdentifierInVnfd
      - 1
      - Yes
      - Yes
      -
    * - numberOfSteps
      - Integer
      - 0..1
      - Yes
      - Yes
      -
    * - additionalParams
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >is_reverse
      - Boolean
      - 0..1
      - No
      - Yes
      - Tacker original attribute

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 202
      - The request has been accepted for processing.
    * - ProblemDetails
      -  0..1
      -  Error: 404
      -  The API producer did not find a current representation
         for the target resource or is not willing to disclose
         that one exists.
    * - ProblemDetails
      -  1
      -  Error: 409
      -  The operation cannot be executed currently, due to a
         conflict with the state of the resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.


* | **Name**: Heal a VNF instance
  | **Description**: Heal for VNF instance.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v2/vnf_instances/{vnfInstanceId}/heal
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - HealVnfRequest
      - 1
      - Parameters for the heal VNF operation.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 10 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Supported in API v2
      - Supported in API v1
      - Description
    * - vnfcInstanceId
      - Identifier
      - 0..N
      - Yes
      - Yes
      - This attribute is defined in only SOL 002.
    * - cause
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - additionalParams
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - >all
      - Boolean
      - 0..1
      - Yes
      - No
      - Tacker original attribute
    * - healScript
      - String
      - 0..1
      - No
      - No
      - This attribute is defined in only SOL 002.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 202
      - The request has been accepted for processing.
    * - ProblemDetails
      -  0..1
      -  Error: 404
      -  The API producer did not find a current representation
         for the target resource or is not willing to disclose
         that one exists.
    * - ProblemDetails
      -  1
      -  Error: 409
      -  The operation cannot be executed currently, due to a
         conflict with the state of the resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.


* | **Name**: Modify VNF information
  | **Description**: Update information about a VNF instance.
  | **Method type**: PATCH
  | **URL for the resource**: vnflcm/v2/vnf_instances/{vnfInstanceId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - VnfInfoModificationRequest
      - 1
      - Parameters for the VNF modification.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 10 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Supported in API v2
      - Supported in API v1
      - Description
    * - vnfInstanceName
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - vnfInstanceDescription
      - String
      - 0..1
      - Yes
      - Yes
      -
    * - vnfPkgId
      - Identifier
      - 1
      - No
      - Yes
      - Although this attribute is not available in SOL 002/003 v2.6.1,
        Tacker support it in v1 API. See note.
    * - vnfdId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - vnfConfigurableProperties
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - metadata
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - extensions
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - vimConnectionInfo
      - map(VimConnectionInfo)
      - 0..N
      - Yes
      - Yes
      - This attribute is defined in only SOL 003.
    * - >vimId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >vimType
      - String
      - 1
      - Yes
      - Yes
      -
    * - >interfaceInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >accessInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >extra
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - vnfcInfoModifications
      - VnfcInfoModifications
      - 0..N
      - Yes
      - No
      - This attribute is defined in only SOL 002.
    * - >id
      - IdentifierInVnf
      - 1
      - Yes
      - No
      -
    * - >vnfcConfigurableProperties
      - KeyValuePairs
      - 1
      - Yes
      - No
      -

  .. note:: vnfPkgId is not available in SOL 002/003 v2.6.1.
    It is available in v2.4.1.
    However, Tacker have supported it for some NFV related equipment,
    utilizing v2.4.1 API.


  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 202
      - The request has been accepted for processing.
    * - ProblemDetails
      -  1
      -  Error: 409
      -  The operation cannot be executed currently, due to a
         conflict with the state of the resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Any common error response code as defined in clause 6.4
         of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. note:: Since current Tacker does not support *http Etag*,
            it does not support Error Code: 412 Precondition Failed.
            According to the ETSI NFV SOL document,
            there is no API request/response specification for Etag yet,
            and transactions using Etag are not defined by standardization.
            Tacker will support Etag after the ETSI NFV specification defines
            relevant transactions.

* | **Name**: Change external VNF connectivity
  | **Description**: Change the external connectivity of a VNF instance.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_ext_conn
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - ChangeExtVnfConnectivityRequest
      - 1
      - Parameters for the change external VNF connectivity.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 10 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Supported in API v2
      - Supported in API v1
      - Description
    * - extVirtualLinks
      - ExtVirtualLinkData
      - 1..N
      - Yes
      - Yes
      -
    * - >id
      - Identifier
      - 1
      - Yes
      - Yes
      -
    * - >vimConnectionId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >resourceProviderId
      - Identifier
      - 0..1
      - Yes
      - No
      -
    * - >resourceId
      - IdentifierInVim
      - 1
      - Yes
      - Yes
      -
    * - >extCps
      - VnfExtCpData
      - 1..N
      - Yes
      - Yes
      -
    * - >>cpdId
      - IdentifierInVnfd
      - 1
      - Yes
      - Yes
      -
    * - >>cpConfig
      - map(VnfExtCpConfig)
      - 1..N
      - Yes
      - Yes
      -
    * - >>>parentCpConfigId
      - IdentifierInVnf
      - 0..1
      - Yes
      - Yes
      -
    * - >>>linkPortId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >>>cpProtocolData
      - CpProtocolData
      - 0..N
      - Yes
      - Yes
      -
    * - >>>>layerProtocol
      - Enum
      - 1
      - Yes
      - Yes
      - Permitted values: IP_OVER_ETHERNET.
    * - >>>>ipOverEthernet
      - IpOverEthernetAddressData
      - 0..1
      - Yes
      - Yes
      -
    * - >>>>>macAddress
      - MacAddress
      - 0..1
      - Yes
      - Yes
      -
    * - >>>>>segmentationId
      - String
      - 0..1
      - Yes
      - not defined
      - New attribute in API v2.
    * - >>>>>ipAddresses
      - Structure
      - 0..N
      - Yes
      - Yes
      -
    * - >>>>>>type
      - Enum
      - 1
      - Yes
      - Yes
      - Permitted values: IPV4, IPV6.
    * - >>>>>>fixedAddresses
      - IpAddress
      - 0..N
      - Yes
      - Yes
      -
    * - >>>>>>numDynamicAddresses
      - Integer
      - 0..1
      - Yes
      - Yes
      -
    * - >>>>>>addressRange
      - Structure
      - 0..1
      - Yes
      - Yes
      -
    * - >>>>>>>minAddress
      - IpAddress
      - 1
      - Yes
      - Yes
      -
    * - >>>>>>>maxAddress
      - IpAddress
      - 1
      - Yes
      - Yes
      -
    * - >>>>>>subnetId
      - IdentifierInVim
      - 0..1
      - Yes
      - Yes
      -
    * - >extLinkPorts
      - ExtLinkPortData
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
      - Yes
      -
    * - vimConnectionInfo
      - map(VimConnectionInfo)
      - 0..N
      - Yes
      - Yes
      - This attribute is defined in only SOL 003.
    * - >vimId
      - Identifier
      - 0..1
      - Yes
      - Yes
      -
    * - >vimType
      - String
      - 1
      - Yes
      - Yes
      -
    * - >interfaceInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >accessInfo
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -
    * - >extra
      - KeyValuePairs
      - 0..1
      - Yes
      - No
      -
    * - additionalParams
      - KeyValuePairs
      - 0..1
      - Yes
      - Yes
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 202
      - The request has been accepted for processing.
    * - ProblemDetails
      -  1
      -  Error: 409
      -  The operation cannot be executed currently, due to a
         conflict with the state of the resource.
    * - ProblemDetails
      -  See clause 6.4 of [#NFV-SOL013_341]_
      -  Error: 4xx, 5xx
      -  Any common error response code as defined in clause 6.4
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

Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>


Work Items
----------

* Add new attributes supported by v2 API to python-tackerclient.
* Add new version API endpoints to Tacker-server.
* Implement new version API processings for Tacker-conductor.
* Add new unit and functional tests.
* Update the Tacker's API reference.


Dependencies
============

None

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
.. [#NFV-SOL001_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/011/03.03.01_60/gs_nfv-sol011v030301p.pdf
.. [#NFV-SOL013_341]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.04.01_60/gs_nfv-sol013v030401p.pdf
