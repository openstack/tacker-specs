..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


=====================================================================
Support ETSI NFV-SOL based change external VNF connectivity operation
=====================================================================

https://blueprints.launchpad.net/tacker/+spec/support-change-external-connectivity

This specification describes the interface of change external VNF connectivity
based on ETSI NFV-SOL specification.

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================

Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into telecom production
networks and also will simplify further development and support of future standards.
In the former release, Tacker has not supported interface of
change external VNF connectivity as defined in
ETSI NFV SOL 002 [#etsi_sol002]_ and SOL 003 [#etsi_sol003]_.
Tacker should support more APIs and attributes to compliant
ETSI NFV SOL specification and expand a wide range of use cases.

Examples of possible use cases are below.
 - switching the network caused by subscriber movement
 - switching the network on the EPC side caused
   by the introduction of new features
 - changing the network based on VIP changes for containers

Proposed change
===============

The operation provided through a new API in this specification is below.
 - support an additional API:
     - Change external VNF connectivity (POST)

Along with the addition of the Change external VNF connectivity API,
the existing LCM APIs also support new related attributes.

.. seqdiag::

  seqdiag {
    Client; NFVO; tacker-server; tacker-conductor;

    Client -> "tacker-server" [label = "Change external VNF connectivity"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-server" -> "tacker-conductor" [label = "trigger asynchronous task"];
    NFVO <- "tacker-conductor" [label = "POST /grants"];
    NFVO --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute MgmtDriver"];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor" [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }

This operation allows the client to change the external
connectivity of a VNF instance.

 - Disconnect the external CPs that are connected to a particular external VL,
   and connect them to a different external VL.
 - Change the connectivity parameters of the existing external CPs,
   including changing addresses.

On this specification, the cases below are supported.
 - change the port

     VNFM supports to change port/network.

 - change parameters

     VNFM also supports to change ip address/mac address/allowed_address_pair.

The cases if the ports are used as trunk-parent-port or trunk-sub-port are
unsupported(create/delete/connect/disconnect/change).

The operations provided through additional attributes
in this specification are below.

 - support additional attributes:
     - Grants (POST)

         As part of Change external VNF connectivity , VNFM sends Grant Request
         as part of this specification.
         When applicable, the NFVO can reserve resources based on the VNFM's
         virtualized resources request.

         For the above management Change external VNF connectivity
         supports the Granting interface.

     - VNF instances (GET)
     - Individual VNF instances (GET)

         As part of Change External VNF connectivity, these APIs set
         _link(changeExtConn) parameter.

     - Notification endpoint (POST)

         VNFM support to send Notification endpoint of Change External VNF
         Connectivity.

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

A) Support new APIs
~~~~~~~~~~~~~~~~~~~
The following REST API will be added. These attributes are based on
ETSI NFV SOL002 [#etsi_sol002]_ and SOL003 [#etsi_sol003]_.

* | **Name**: Change external VNF connectivity
  | **Description**: Change the external connectivity of a VNF instance
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}/change_ext_conn
  | **Request**:

  +----------------------------------+-------------+------------------------------------------------------+
  | Data type                        | Cardinality | Description                                          |
  +==================================+======+======+======================================================+
  | ChangeExtVnfConnectivityRequest  | 1           | Parameters for the Change external VNF connectivity. |
  +----------------------------------+-------------+------------------------------------------------------+

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - extVirtualLinks
       - ExtVirtualLinkData
       - 1..N
       - Yes
     * - >id
       - Identifier
       - 1
       - Yes
     * - >vimConnectionId
       - Identifier
       - 0..1
       - Yes
     * - >resourceProviderId
       - Identifier
       - 0..1
       - No
     * - >resourceId
       - IdentifierInVim
       - 1
       - Yes
     * - >extCps
       - VnfExtCpData
       - 1..N
       - Yes
     * - >extLinkPorts
       - ExtLinkPortData
       - 0..N
       - Yes
     * - vimConnectionInfo
       - VimConnectionInfo
       - 0..N
       - Yes
     * - >id
       - Identifier
       - 1
       - Yes
     * - >vimId
       - Identifier
       - 0..1
       - Yes
     * - >vimType
       - String
       - 1
       - Yes
     * - >interfaceInfo
       - KeyValuePairs
       - 0..1
       - Yes
     * - >accessInfo
       - KeyValuePairs
       - 0..1
       - Yes
     * - >extra
       - KeyValuePairs
       - 0..1
       - No
     * - additionalParams
       - KeyValuePairs
       - 0..1
       - Yes

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
       - The request has been accepted for processing.
     * - ProblemDetails
       - 1
       - Error 409
       - Error: The operation cannot be executed currently, due to
         a conflict with the state of the resource.
     * - ProblemDetails
       - See clause 6.4 of [#etsi_sol013]_
       - Error 4xx/5xx
       - Error: Any common error response code as defined in clause 6.4 of
         ETSI GS NFV-SOL 013 [#etsi_sol013]_ may be returned.

B) Support new attributes of implemented APIs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following attributes of REST APIs will be added. These attributes are
based on ETSI NFV SOL002 [#etsi_sol002]_ and SOL003 [#etsi_sol003]_.
Details of APIs implemented in previous versions are
described in NFV Orchestration API v1.0 [#NFV_Orchestration_API_v1.0]_.

* | **Name**: List VNF Instances
  | **Description**: Request list of all existing VNF instances
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_instances
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
         | Error: 401 403
       - Information about zero or more VNF instances was queried successfully.

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
     * - >changeExtConn
       - Link
       - 0..1
       - Yes

* | **Name**: Query VNF
  | **Description**: Request existing VNF instance resource by its id
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}
  | **Resource URI variables for this resource**:

  +---------------+---------------------------------+
  | Name          | Description                     |
  +===============+=================================+
  | vnfInstanceId | Identifier of the VNF instance. |
  +---------------+---------------------------------+

  | **Response**:

  .. list-table::
     :widths: 10 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - VnfInstance
       - 1
       - | Success: 200
         | Error: 401 403 404
       - Information about an individual VNF instance was queried successfully.

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
     * - >changeExtConn
       - Link
       - 0..1
       - Yes

* | **Name**: Query VNF occurrence
  | **Description**: Request individual VNF lifecycle
      management operation occurrence by its id
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
     * - changedExtConnectivity
       - ExtVirtualLinkInfo
       - 0..N
       - Yes

.. note:: VnfLcmOpOcc.changedExtConnectivity referred in
        　"Proposed change 2) Flow of VNF LCM operation occurrence (GET)" is
        　based on the spec of [#support-fundamental-vnf-lcm]_.

* | **Name**: Notification endpoint
  | **Description**: Send notifications related to VNF lifecycle changes
  | **Method type**: POST
  | **URL for the resource**: The resource URI is provided
      by the client when creating the subscription.
  | **Request**:

  .. list-table::
     :widths: 20 10 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Description
     * - VnfLcmOperationOccurrenceNotification
       - 1
       - A notification about lifecycle changes triggered by a VNF LCM
         operation occurrence.
     * - VnfIdentifierCreationNotification
       - 1
       - A notification about the creation of a VNF identifier and the
         related individual VNF instance resource.
     * - VnfIdentifierDeletionNotification
       - 1
       - A notification about the deletion of a VNF identifier and the
         related individual VNF instance resource.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - changedExtConnectivity
       - ExtVirtualLinkInfo
       - 0..N
       - Yes

Security impact
---------------

None

Notifications impact
--------------------

This specification enhances an API related to
notification for VNF lifecycle management.

Other end user impact
---------------------

Add a new OSC command in python-tackerclient to
invoke change external VNF connectivity.

Performance Impact
------------------

None

Other deployer impact
---------------------

The previously created VNFs will not be allowed to
be managed using the newly introduced APIs.

Developer impact
----------------

Tacker-VNFM calls the following API as a client.
The following attributes related to the Change external
VNF connectivity API will be added.
These attributes are based on ETSI NFV SOL003 [#etsi_sol003]_.
Details of APIs implemented in previous versions are
described in Tacker Victoria specifications [#Tacker_Victoria]_.

* | **Name**: Grants
  | **Description**: Obtain permission from the NFVO to perform
                     a particular VNF lifecycle operation
  | **Method type**: POST
  | **URL for the resource**: /grant/v1/grants
  | **Request**:

  +--------------------------+-------------+----------------------------------+
  | Data type                | Cardinality | Description                      |
  +==========================+======+======+==================================+
  | GrantRequest             | 1           | Parameters for the Grants.       |
  +--------------------------+-------------+----------------------------------+

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - instantiationLevelId
       - Identifier
       - 0..1
       - Yes
     * - updateResources
       - ResourceDefinition
       - 0..N
       - Yes
     * - >id
       - IdentifierLocal
       - 1
       - Yes
     * - >type
       - Enum (inlined)
       - 1
       - Yes
     * - >vduId
       - dentifierInVnfd
       - 0..1
       - Yes
     * - >resourceTemplateId
       - dentifierInVnfd
       - 1
       - Yes
     * - >resource
       - ResourceHandle
       - 0..1
       - Yes
     * - additionalParams
       - KeyValuePairs
       - 0..1
       - Yes

  | **Response**:

  .. list-table::
     :widths: 10 10 16 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description

     * - Grant
       - 1
       - Success 201
       - The grant has been created successfully (synchronous mode).
     * - n/a
       - n/a
       - Success 202
       - The request has been accepted for processing, and it is
         expected to take some time to create the grant (asynchronous mode).
     * - ProblemDetails
       - 1
       - Error 403
       - Error: The grant has been rejected.
     * - ProblemDetails
       - See clause 6.4 of [#etsi_sol013]_
       - Error 4xx/5xx
       - Error: Any common error response code as defined in clause 6.4 of
         ETSI GS NFV-SOL 013 [#etsi_sol013]_ may be returned.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - updateResources
       - GrantInfo
       - 0..N
       - Yes
     * - >resourceDefinitionId
       - IdentifierLocal
       - 1
       - Yes
     * - extVirtualLinks
       - ExtVirtualLinkData
       - 0..N
       - Yes
     * - >id
       - Identifier
       - 1
       - Yes
     * - >vimConnectionId
       - Identifier
       - 0..1
       - Yes
     * - >resourceId
       - IdentifierInVim
       - 1
       - Yes
     * - >extCps
       - VnfExtCpData
       - 1..N
       - Yes
     * - >extLinkPorts
       - ExtLinkPortData
       - 0..N
       - Yes
     * - extManagedVirtualLinks
       - ExtManagedVirtualLinkData
       - 0..N
       - Yes
     * - >id
       - Identifier
       - 1
       - Yes
     * - >virtualLinkDescId
       - IdentifierInVnfd
       - 1
       - Yes
     * - >vimConnectionId
       - Identifier
       - 0..1
       - Yes
     * - >resourceID
       - IdentifierInVim
       - 1
       - Yes

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Kentaro Ogawa <kentaro.ogawa.dr@hco.ntt.co.jp>
Other contributors:
  Makoto Hamada <makoto.hamada.xu@hco.ntt.co.jp>

Work Items
----------

* Add a new REST API and supported attributes to Tacker-server.
* Make changes in python-tackerclient to add new OSC commands for calling
  an API of change external VNF connectivity.
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
.. [#etsi_sol002]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_sol003]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_sol013]
   https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/02.06.01_60/gs_nfv-sol013v020601p.pdf
   (Chapter 6: Error reporting)
.. [#NFV_Orchestration_API_v1.0]
   https://docs.openstack.org/api-ref/nfv-orchestration/v1/index.html#virtualized-network-function-lifecycle-management-interface-vnf-lcm
.. [#Tacker_Victoria]
   https://specs.openstack.org/openstack/tacker-specs/specs/victoria/support-sol003-vnfm-operations.html
.. [#support-fundamental-vnf-lcm]
   https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/support-fundamental-vnf-lcm-based-on-ETSI-NFV.html
