..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===========================================================
Support ETSI NFV SOL003 to interoperate with 3rd-party NFVO
===========================================================

https://blueprints.launchpad.net/tacker/+spec/support-vnfm-operations

Enables Tacker to operate as a VNFM that can interoperate with 3rd-party NFVO.
Therefore, support ETSI NFV SOL003 [#NFV-SOL003]_ Or-Vnfm specifications and
VNF lifecycle operations interoperating with NFVO.


Problem description
===================

In current Tacker implementation, functions of VNFM and NFVO are tightly coupled.

The reason for such an implementation is that users can easily build NFV
environment(VNFM + NFVO) to small start using Tacker. On the other hand,
it is also important for Tacker to cooperate with 3rd-party NFVO as VNFM when
considering the practical application of Tacker.
So, Tacker as VNFM will support VNF package and grant APIs based on ETSI NFV
SOL003 [#NFV-SOL003]_.



Proposed change
===============

This feature supports the functionality for Tacker to connect to NFVO as VNFM.
When Tacker connects to 3rd-party NFVO (as referred to NFVO) as VNFM,
Tacker(VNFM) needs the following information from NFVO, so the operations
to get them will be implemented.

- VNF package information
- Grant information

1) NFVO information management
------------------------------

1-1) Flow of Getting VNF package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When operating as VNFM connected to NFVO, Tacker-VNFM uses the following API
to get the VNF package information from NFVO when starting
lifecycle management(LCM) operation.
The following APIs sent from VNFM can be sent or suppressed by the Tacker
configuration.

VNF packages uses "vnf_packages" API.

Precondition: One or more "Individual VNF package" resources are created.

.. seqdiag::

  seqdiag {
    Client; NFVO; tacker-server; tacker-conductor;

    Client -> "tacker-server" [label = "POST /vnf_instances/"];
    "tacker-server" ->> "tacker-server"
      [label = "Create VNF instance resource"];
    "tacker-server" -> "tacker-conductor"
      [label = "execute vnf_package list process{filter}"];
    NFVO <- "tacker-conductor"
      [label = "GET /vnf_packages/ with attribute filter(vnfdId)"];
    NFVO --> "tacker-conductor" [label = "Response 200 OK with VnfPkgInfo"];
    "tacker-server" <<- "tacker-conductor" [label = "(VnfPkgInfo)"];
    "tacker-server" ->> "tacker-server"
      [label = "Update VNF instance resource(VnfPkgInfo)"];
    "tacker-server" -> "tacker-conductor"
      [label = "execute vnf_package content process{vnfPkgId}"];
    NFVO <- "tacker-conductor"
      [label = "GET /vnf_packages/{vnfPkgId}/package_content "];
    NFVO --> "tacker-conductor"
      [label = "Response 200 OK with VNF package file"];
    "tacker-server" <<- "tacker-conductor"
      [label = "(VNF package content file)"];
    "tacker-server" ->> "tacker-server"[label = "Store received package file"];
    "tacker-server" -> "tacker-conductor"
      [label = "execute vnf_package vnfd process{vnfPkgId}"];
    NFVO <- "tacker-conductor"
    [label =
    "GET /vnf_packages/{vnfPkgId}/vnfd with 'Accept' header contains 'text/plain'"];
    NFVO --> "tacker-conductor" [label = "Response 200 OK with VNFD contents"];
    "tacker-server" <<- "tacker-conductor" [label = "(VNFD)"];
    "tacker-server" ->> "tacker-server"
      [label = "Update VNF instance resource(VNFD)"];
    "tacker-server" -> "tacker-conductor"
      [label = "execute vnf_package artifact process{vnfPkgId}"];
    NFVO <- "tacker-conductor"
      [label = "GET /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}"];
    NFVO --> "tacker-conductor" [label = "Response 200 OK with artifact file"];
    "tacker-server" <<- "tacker-conductor" [label = "(artifact file)"];
    "tacker-server" ->> "tacker-server"
      [label = "Store received package file"];
    Client <-- "tacker-server" [label = " Response 201 Created"];
    "tacker-server" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI}"];
    Client --> "tacker-conductor" [label = "Response 204 No Content"];
  }


* VNF packages (GET)
    When VNFM receives Create VNF request, VNFM will request get
    vnfPkgInformation to NFVO.
    VNFM sets the attribute based filtering parameter to get vnfPkgId.
    NFVO sends http response with vnfPkgInfo that is based on the vnfPkgId.
    After http response is received, VNFM stores the received vnfPkgId.
* VNF package content (GET)
* VNFD in an individual VNF package (GET)
* Individual VNF package artifact (GET)
    VNFM requests to get information of content/VNFD/artifact.
    NFVO provides such information to VNFM.
    After http response is received, VNFM stores the contents received.
* Individual VNF package (GET)
    In a case of having vnfPkgId, VNFM can get only related vnfPkgInformation.
    ModifyVNF Information can send this API.

1-2) Flow of grant request with synchronous response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This operation allows the VNFM to request a grant for authorization of a VNF
LCM operation. This interface supports multiple use cases, such as:

* The NFVO can approve or reject a request based on policies (e.g. dependencies
  between VNFs) and available capacity.
* When applicable, the NFVO can reserve resources based on the VNFM's
  virtualised resources request.
* The NFVO can provide to the VNFM information about the VIM where cloud
  resources are allocated. This can include additional information such as
  the availability zone.

Grant API is sent in below sequences:
- Instantiation
- Healing
- Scaling
- Termination

.. seqdiag::

  seqdiag {
    Client; NFVO; tacker-server; tacker-conductor;

    Client -> "tacker-server" [label = "LCM Operation Request"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-server" -> "tacker-conductor"
      [label = "trriger asynchronous task"];
    NFVO <- "tacker-conductor" [label = "POST /grants"];
    NFVO --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute MgmtDriver"];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute VnfLcmDriver"];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (COMPLETED)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }


After receiving 201 created with body data, VNFM updates the grant information.

Postcondition: The grant information is available to the VNFM.

2) A judgement of NFVO operation condition
--------------------------------------------

Since API transmission is performed for connection with NFVO, communication
with NFVO is enabled by setting URI in the Tacker configuration.
If no URI is set, all API transmissions for NFVO will be suppressed.
The following APIs sent from VNFM can be sent or suppressed by the Tacker
configuration.

- VNF package information
- Grant information

3) Authorization of API requests and notifications
--------------------------------------------------

3-1) A support of OAuth2.0
~~~~~~~~~~~~~~~~~~~~~~~~~~

SOL013 [#NFV-SOL013]_ stipulates that ETSI NFV MANO API call uses
OAuth2 [#NFV-SOL013]_, and sending a notification uses OAuth2 or HTTP Basic
authentication.
Currently Tacker does not support the operation corresponding to OAuth2.
Tacker requires IETF RFC 6749 compliant authorization.

3-2) A support of TLS1.2
~~~~~~~~~~~~~~~~~~~~~~~~

Currently Tacker supports SSL. Transport security support is required to
prevent falsification of transmitted information and to secure a free
communication path.
SOL013 [#NFV-SOL013]_ recommends TLS1.2 (IETF RFC 5246). Tacker also needs to
be TLS1.2 compliant.

4) API enhancement of CreateVNF
-------------------------------

For enhancement of receiving VNF package metadata, VNFM support "metadata" parameter
on "Create VNF" request.
This parameter is stored in VNFM.
This parameter overwrites 6.2.35
tosca.datatypes.nfv.VnfInfoModifiableAttributesMetadata in SOL001
[#NFV-SOL001]_.
However, metadata does not affect lifecycle based on SOL003 [#NFV-SOL003]_
5.5.2.2 Type: VnfInstance. Therefore, Tacker just save metadata.


Alternatives
------------

None


Data model impact
-----------------

None



REST API impact
---------------

None



Security impact
---------------

All APIs are authenticated by OAuth2 and encrypted by TLS1.2.


Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

VNFM get pkg data/Image during Instantiation execute.
The process may take some time.


Other deployer impact
---------------------

None

Developer impact
----------------

Tacker-VNFM calls the following APIs as a client.
These attributes are based on ETSI NFV SOL003 [#NFV-SOL003]_.

* | **Name**: Grants
  | **Description**: Request a grant
  | **Method type**: POST
  | **URL for the resource**: /grant/v1/grants
  | **Request**:

  +--------------+-------------+--------------------------------------------+
  | Data type    | Cardinality | Description                                |
  +==============+=============+============================================+
  | GrantRequest | 1           | Parameters for requesting Grants resource. |
  +--------------+-------------+--------------------------------------------+

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Support
     * - vnfInstanceId
       - Identifier
       - 1
       - Yes
     * - vnfLcmOpOccId
       - Identifier
       - 1
       - Yes
     * - vnfdId
       - Identifier
       - 1
       - Yes
     * - flavourId
       - Identifier
       - 0..1
       - Yes
     * - operation
       - GrantedLcmOperationType
       - 1
       - Yes
     * - isAutomaticInvocation
       - Boolean
       - 1
       - Yes
     * - instantiationLevelId
       - Identifier
       - 0..1
       - No
     * - addResources
       - ResourceDefinition
       - 0..N
       - Yes
     * - tempResources
       - ResourceDefinition
       - 0..N
       - No
     * - removeResources
       - ResourceDefinition
       - 0..N
       - Yes
     * - updateResources
       - ResourceDefinition
       - 0..N
       - No
     * - placementConstraints
       - PlacementConstraint
       - 0..N
       - Yes
     * - vimConstraints
       - VimConstraint
       - 0..N
       - No
     * - additionalParams
       - KeyValuePairs
       - 0..1
       - No
     * - _links
       - Structure (inlined)
       - 1
       - Yes
     * - >vnfLcmOpOcc
       - Link
       - 1
       - Yes
     * - >vnfInstance
       - Link
       - 1
       - Yes

  | **Response**:

  .. list-table::
     :widths: 10 10 20 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - Grant
       - 1
       - | Success 201
         | Error 400 401 403
       - The grant has been created successfully (synchronous mode).

  .. list-table::
     :header-rows: 1

     * - Attributename
       - Datatype
       - Cardinality
       - Support
     * - id
       - Identifier
       - 1
       - Yes
     * - vnfInstanceId
       - Identifier
       - 1
       - Yes
     * - vnfLcmOpOccId
       - Identifier
       - 1
       - Yes
     * - vimConnections
       - VimConnectionInfo
       - 0..N
       - Yes
     * - zones
       - ZoneInfo
       - 0..N
       - Yes
     * - zoneGroups
       - ZoneGroupInfo
       - 0..N
       - No
     * - computeReservationId
       - IdentifierInVim
       - 0..1
       - No
     * - networkReservationId
       - IdentifierInVim
       - 0..1
       - No
     * - storageReservationId
       - IdentifierInVim
       - 0..1
       - No
     * - addResources
       - GrantInfo
       - 0..N
       - Yes
     * - tempResources
       - GrantInfo
       - 0..N
       - No
     * - removeResources
       - GrantInfo
       - 0..N
       - Yes
     * - updateResources
       - GrantInfo
       - 0..N
       - No
     * - vimAssets
       - Structure(inlined)
       - 0..1
       - Yes
     * - >computeResourceFlavours
       - VimComputeResourceFlavour
       - 0..N
       - Yes
     * - >softwareImages
       - VimSoftwareImage
       - 0..N
       - Yes
     * - extVirtualLinks
       - ExtVirtualLinkData
       - 0..N
       - No
     * - extManagedVirtualLinks
       - ExtManagedVirtualLinkData
       - 0..N
       - No
     * - additionalParams
       - KeyValuePairs
       - 0..1
       - Yes
     * - _links
       - Structure(inlined)
       - 1
       - Yes
     * - >self
       - Link
       - 1
       - Yes
     * - >vnfLcmOpOcc
       - Link
       - 1
       - Yes
     * - >vnfInstance
       - Link
       - 1
       - Yes


* | **Name**: VNF packages
  | **Description**: Query VNF packages information
  | **Method type**: GET
  | **URL for the resource**: /vnf_packages


* | **Name**: VNF package content
  | **Description**: Fetch an on-boarded VNF package
  | **Method type**: GET
  | **URL for the resource**: /vnf_packages/{vnfPkgId}/package_content


* | **Name**: VNFD of an individual VNF package
  | **Description**: Read VNFD of an onboarded VNF package
  | **Method type**: GET
  | **URL for the resource**: /vnf_packages/{vnfPkgId}/vnfd


* | **Name**: Individual VNF package artifact
  | **Description**: Fetch individual VNF package artifact
  | **Method type**: GET
  | **URL for the resource**: /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}


* | **Name**: Individual VNF package
  | **Description**: Read information about an individual VNF package
  | **Method type**: GET
  | **URL for the resource**: /vnf_packages/{vnfPkgId}

Implementation
==============

Assignee(s)
-----------

Primary assignee:
 Makoto Hamada <makoto.hamada.xu@hco.ntt.co.jp>


Work Items
----------

* Implement process of Getting VNF package and Grant.
* Add new config and change Tacker Config documentation.
* Support OAuth2.0 and TLS1.2
* Support API enhancement of CreateVNF.
* Add new unit and functional tests.


Dependencies
============

"Create VNF" referred in "Proposed change" is ETSI SOL based API proposed
in the spec [#enhance_spec]_.


Testing
=======

Unit and functional test cases will be added for VNF package and Grant.


Documentation Impact
====================

A new configuration options for connection of NFV will be added to
configuration reference.


References
==========

.. [#NFV-SOL001] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/02.06.01_60/gs_nfv-sol001v020601p.pdf
.. [#NFV-SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. [#NFV-SOL013] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/02.06.01_60/gs_nfv-sol013v020601p.pdf
.. [#enhance_spec] https://specs.openstack.org/openstack/tacker-specs/specs/victoria/enhancement_enhance-vnf-lcm-api-support.html
