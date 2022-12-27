..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===================================================
Add sample coordinateVNF script for coordination IF
===================================================

.. Blueprints:

https://blueprints.launchpad.net/tacker/+spec/add-sample-coordinate-script

This specification proposes a sample coordinateVNF script
for rolling update with external management systems
(e.g., Operations Support Systems (OSS)/Element Manager (EM)).
This specification focuses on only VNF update by the ChangeCurrentVNFPackage API.

Problem description
===================

Tacker has supported rolling update by the ChangeCurrentVNFPackage API.
In some telecom systems, rolling update scenarios may require
coordination with external components
(e.g., changing load balancer settings from external components for authorization reasons).
To address such scenarios, ETSI NFV SOL002 v3.5.1 [#NFV-SOL002_351]_ defines
the VNF LCM Coordination interface.
However, the current Tacker does not support this API nor have other explicit functions
for coordination with external components.

Proposed change
===============

This specification proposes implementing the client function of Coordination API
in the Coordinate VNF script [#Coordinate-script]_,
which can be customized by the user without affecting common implementation.
Formally, coordination action and execution timing during LCM
are specified by VNFD according to ETSI NFV SOL001 [#NFV-SOL001_351]_.
However, there are few products that act as the Coordination API server
because this interface is not yet mature.
Therefore, formal support of this API is excessive now and
Tacker should focus on rolling update which has specific requirements.
For the same reason,
this specification targets only the ChangeCurrentVNFPackage API for VNF.
The support of other APIs and CNF is future work.

Support VNF LCM Coordination interface
--------------------------------------

The following shows the VNF LCM Coordination interface defined in SOL002 v3.5.1.
VNFM acts as a client and the external component acts as a server.

* | **Name**: Coordinate an LCM operation
  | **Description**: Request a VNF LCM Coordination
  | **Method type**: POST
  | **URL for the resource**: /lcmcoord/v1/coordinations
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - LcmCoordRequest
      - 1
      - Parameters for the coordination action.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Description
    * - vnfInstanceId
      - Identifier
      - 1
      - Identifier of the VNF instance which this
        coordination request is related to.
    * - vnfLcmOpOccId
      - Identifier
      - 1
      - The identifier of the VNF lifecycle management operation occurrence
        related to the coordination.
    * - lcmOperationType
      - LcmOperationForCoordType
      - 1
      - The type of the LCM operation with which coordination is requested.
    * - coordinationActionName
      - IdentifierInVnfd
      - 1
      - Indicates the LCM coordination action.
    * - inputParams
      - KeyValuePairs
      - 0..1
      - Additional parameters passed as input to
        the coordination action.
    * - _links
      - Structure
      - 1
      - Links to resources related to this request.
    * - >vnfLcmOpOcc
      - Link
      - 1
      - Related lifecycle management operation occurrence.
    * - >vnfInstance
      - Link
      - 1
      - Related VNF instance.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - LcmCoord
      - 1
      - Success: 201
      - Shall be returned to indicate a finished coordination
        action when the API producer has chosen the
        synchronous mode, which may be selected for
        coordination actions that finish within the time frame
        in which an HTTP response is expected.
    * - n/a
      -
      - Success: 202
      - Shall be returned when the API producer has chosen
        the asynchronous mode and the request has been
        accepted for processing.
        Further, the HTTP response may include a "RetryAfter"
        HTTP header that indicates the time to wait
        before sending the next GET request to the
        "individual coordination" resource indicated in the
        "Location" header. If the header is provided, the
        VNFM shall record the signalled delay value in the
        "delay" attribute of the applicable entry in the
        "lcmCoordinations" array in the "VnfLcmOpOcc" structure.
    * - ProblemDetails
      - 1
      - Error: 403
      - The starting of the coordination operation has been
        rejected. No "individual coordination action"
        resource shall be created.
    * - ProblemDetails
      - 1
      - Error: 409
      - The operation cannot be executed currently, due to a
        conflict with the state of the "Coordinations" resource.
    * - ProblemDetails
      - 1
      - Error: 503
      - The API producer has chosen the synchronous mode and
        cannot perform the requested coordination currently,
        but expects to be able to perform it sometime in the future.
        The HTTP response shall include a "Retry-After"
        HTTP header that indicates the delay after which it is
        suggested to repeat the coordination request with the
        same set of parameters. The VNFM shall record the
        signalled delay value in the "delay" attribute of the
        applicable entry in the "rejectedLcmCoordinations"
        array in the "VnfLcmOpOcc" structure.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx, 5xx
      - Any common error response code as defined in clause 6.4
        of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this coordination result
    * - coordinationResult
      - LcmCoordResultType
      - 1
      - The result of executing the coordination
        action which also implies the action to be
        performed by the VNFM as the result of this coordination.
    * - vnfInstanceId
      - Identifier
      - 1
      - Identifier of the VNF instance which this
        coordination request is related to.
    * - vnfLcmOpOccId
      - Identifier
      - 1
      - The identifier of the VNF lifecycle management operation occurrence
        related to the coordination.
    * - lcmOperationType
      - LcmOperationForCoordType
      - 1
      - The type of the LCM operation with which coordination is requested.
    * - coordinationActionName
      - String
      - 1
      - Indicates the LCM coordination action.
    * - outputParams
      - KeyValuePairs
      - 0..1
      - Additional parameters returned by the coordination action.
    * - warnings
      - String
      - 0..N
      - Warning messages that were generated while the operation was executing.
    * - error
      - ProblemDetails
      - 0..1
      - Error information related to the coordination.
    * - _links
      - Structure
      - 1
      - Links to resources related to this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >vnfLcmOpOcc
      - Link
      - 1
      - Related lifecycle management operation occurrence.
    * - >vnfInstance
      - Link
      - 1
      - Related VNF instance.

* | **Name**: Show Individual coordination action
  | **Description**: Query individual Coordination action
  | **Method type**: GET
  | **URL for the resource**: /lcmcoord/v1/coordinations/{coordinationId}
  | **Request**:
  | **Resource URI variables for this resource**:

  .. list-table::
    :header-rows: 1
    :widths: 2 ,2

    * - Name
      - Description
    * - coordinationId
      - Identifier of the LCM Coordination.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - LcmCoord
      - 1
      - Success: 200
      - Shall be returned when the coordination is finished
        and the coordination result has been read
        successfully.
    * - n/a
      -
      - Success: 202
      - Shall be returned when the management operation
        with which coordination is requested is still ongoing or
        in the process of being cancelled, i.e. no coordination
        result is available yet.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx, 5xx
      - Any common error response code as defined in clause 6.4
        of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this coordination result
    * - coordinationResult
      - LcmCoordResultType
      - 1
      - The result of executing the coordination
        action which also implies the action to be
        performed by the VNFM as the result of this coordination.
    * - vnfInstanceId
      - Identifier
      - 1
      - Identifier of the VNF instance which this
        coordination request is related to.
    * - vnfLcmOpOccId
      - Identifier
      - 1
      - The identifier of the VNF lifecycle management operation occurrence
        related to the coordination.
    * - lcmOperationType
      - LcmOperationForCoordType
      - 1
      - The type of the LCM operation with which coordination is requested.
    * - coordinationActionName
      - String
      - 1
      - Indicates the LCM coordination action.
    * - outputParams
      - KeyValuePairs
      - 0..1
      - Additional parameters returned by the coordination action.
    * - warnings
      - String
      - 0..N
      - Warning messages that were generated while the operation was executing.
    * - error
      - ProblemDetails
      - 0..1
      - Error information related to the coordination.
    * - _links
      - Structure
      - 1
      - Links to resources related to this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >vnfLcmOpOcc
      - Link
      - 1
      - Related lifecycle management operation occurrence.
    * - >vnfInstance
      - Link
      - 1
      - Related VNF instance.

Flow of VNF update
------------------

The following diagram shows the rolling update using coordinateVNF script.

.. code-block::


                                                             +---------+
                                                             |  VNFD   |
                                                             |         |
                                                             +----+----+
                                                                  |
                                        (Script is included       v       +-------------------+
                +--------------------+  in the package)     +----------+  | Change current    |
  +------------>| CoordinateVNF      +--------------------->|          |  | VNF Package       |
  |             | script             |                      |   CSAR   |  | Request with      |
  |   +---------+                    |                      |          |  | Additional Params |
  |   |         +-------+------------+                      +-----+----+  +--+----------------+
  |   |                 |    ^                                    |          | 1. Change current VNF Package
  |   |                 |    |                              +-----v----------v------------------------------+
  |   |  8. Coordination|    | Coordination                 |  +-----------------------+              VNFM  |
  |   |     request     |    | Result                       |  |   Tacker-server       |                    |
  |   |                 |    |                              |  +--+--------------------+                    |
  |   |                 v    |                              |     |  2. Change current VNF Package request  |
  |   |         +------------+-------+                      |     v                                         |
  |   |         |                    |                      |  +-----------------------------------------+  |
  |   |         |         EM         |                      |  |                                         |  |
  |   |         |                    |                      |  |   +-------------------+                 |  |
  |   |         +--------------------+                      |  |   | VnfLcmDriver      |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |  7. Coordinate                                      |  |   +-+-----------------+                 |  |
  |   |     resource                                        |  |     | 3. change_vnfpkg_process          |  |
  |   |         +--------------------+                      |  |     v                                   |  |
  |   |         |                    | 4. Get stack resource|  |   +-------------------+                 |  |
  |   |         |  +--------------+  |    to update         |  |   | InfraDriver       | 9. Repeat steps |  |
  |   |         |  | Resource     |<-+----------------------+--+---+                   |    5 through 8  |  |
  |   +---------+->|              |  | 5. Update VNFC       |  |   |                   |    for each VNFC|  |
  |             |  |              |<-+----------------------+--+---+                   +--------+        |  |
  |             |  +--------------+  |                      |  |   |                   |        |        |  |
  |             | VNF                |                      |  |   |                   |<-------+        |  |
  |             +--------------------+                      |  |   |                   |                 |  |
  |                        6. Execute CoordinateVNF script  |  |   |                   |                 |  |
  +---------------------------------------------------------+--+---+                   |                 |  |
                                                            |  |   +-------------------+                 |  |
                                                            |  |    Tacker-conductor                     |  |
                +--------------------+                      |  +-----------------------------------------+  |
                | Hardware Resources |                      |                                               |
                +--------------------+                      +-----------------------------------------------+

Sequence for Rolling update operation

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver"
    "CoordinateVNF script"
    "VIM (OpenStack)"
    "VNF"
    "EM"

    "Client" -> "Tacker-server"
      [label = "1. POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg"];
    "Client" <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. ChangeCurrentVNFPackage"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "change_vnfpkg"];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "3. change_vnfpkg_process"];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "4. Get stack resource to update"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "5. update_stack"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "InfraDriver" -> "CoordinateVNF script"
      [label = "6. CoordinateVNF"];
    "CoordinateVNF script" -> "VNF"
      [label = "7. Coordinate resource"];
    "CoordinateVNF script" <-- "VNF"
      [label = ""];
    "CoordinateVNF script" -> "EM"
      [label = "8. Coordination request"];
    "CoordinateVNF script" <-- "EM"
      [label = "Coordination result"];
    "InfraDriver" <-- "CoordinateVNF script"
      [label = ""];
    "InfraDriver" -> "InfraDriver"
      [label = "9. Repeat steps 5 through 8 for each VNFC"];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }


#. The Client sends a ChangeCurrentVNFPackage request to the "Individual VNF instance" resource.
#. Tacker-server calls Tacker-conductor,
   then Tacker-conductor fetches an on-boarded VNF package and calls VnfLcmDriver.
#. VnfLcmDriver sends a request to the InfraDriver to change vnfpkg process.
#. InfraDriver sends a request to the VIM to get stack resource to update.
#. InfraDriver sends a request to the VIM to update stack.
#. InfraDriver runs CoordinateVNF script.
#. CoordinateVNF script sends a request to the VNF to Coordinate VNF.
#. CoordinateVNF script sends a Coordination request to the external component.
   The endpoint URL of the external component is obtained from the ChangeCurrentVNFPackage request.
   The target VNFC obtained from Tacker is specified as inputParams in the LcmCoordRequest.
   (e.g. it is specified by vnfcInstanceId).
   The process after receiving Coordination response diverges
   depending on whether the Synchronous or Asynchronous mode. See note below.
#. Repeat steps 5 through 8 for each VNFC.

.. note::
  | According to SOL002, the Coordination interface supports Synchronous mode and Asynchronous modes.
    API server decides the mode, and API client can know it by the API response.
    Thus, since VNFM cannot control the mode, Tacker will support both modes.
    The following shows the Coordination processes of VNFM.
  |
  | Synchronous mode: The EM returns to the Tacker a "201 Created" response
    with a "LcmCoord" data structure in the body
    and then VNFM continues the process on the basis of the result.
    Alternatively, EM returns a "503 Service unavailable" response with
    a "ProblemDetails" data structure in the body and a "Retry-After"
    HTTP header that indicates the length of a delay after which a retry
    of the coordination is suggested.
    After the delay interval has passed, the VNFM sends coordination request again.
  |
  | Asynchronous mode: The EM returns to the Tacker a "202 Accepted" response
    with an empty body and a "Location" HTTP header that indicates
    the URI of the "Individual coordination action" resource.
    Tacker waits for a certain time interval
    (as indicated in the Retry-After header of the previous 202 response if signalled,
    or determined by other means otherwise) before the next iteration of the loop.
    Tacker polls the status of the coordination by sending a GET request to the EM,
    using the URI that was returned in the "Location" header.
    After obtaining the coordination result, Tacker continues the process on the basis of it.

Data model impact
-----------------

None

REST API impact
---------------

To enable users to specify the information
of the external coordination server,
``coordination_server_param`` in the ChangeCurrentVnfPkgRequest
will be supported.
This parameter must be set when using the coordinateVNF script
which calls Coordination API.

* ChangeCurrentVnfPkgRequest

  .. list-table::
      :widths: 15 10 30 30
      :header-rows: 1

      * - Attribute name
        - Data type
        - Cardinality
        - Description
      * - vnfdId
        - Identifier
        - 1
        - Identifier of the VNFD which defines the
          destination VNF Package for the change.
      * - extVirtualLinks
        - ExtVirtualLinkData
        - 0..N
        - Information about external VLs to connect the VNF to.
      * - extManagedVirtualLinks
        - ExtManagedVirtualLinkData
        - 0..N
        - Information about internal VLs that are managed by the NFVO.
      * - vimConnectionInfo
        - map (VimConnectionInfo)
        - 0..N
        - Information about VIM connections to be used for
          managing the resources for the VNF instance, or refer
          to external/externally-managed virtual links.
      * - additionalParams
        - KeyValuePairs
        - 0..1
        - Additional parameters passed by the EM as input to the process.
      * - extensions
        - KeyValuePairs
        - 0..1
        - "extensions" attribute in "VnfInstance".
      * - vnfConfigurableProperties
        - KeyValuePairs
        - 0..1
        - "vnfConfigurableProperties" attribute in "VnfInstance".


User can set following parameter in additionalParams.

* additionalParams

  .. list-table::
    :widths: 15 10 30
    :header-rows: 1

    * - Attribute name
      - Cardinality
      - Parameter description
    * - upgrade_type
      - 1
      - Type of file update operation method. Specify Blue-Green or Rolling update.
    * - lcm-operation-coordinate-old-vnf
      - 1
      - The file path of the script that simulates the behavior of CoordinateVNF for old VNF.
    * - lcm-operation-coordinate-new-vnf
      - 1
      - The file path of the script that simulates the behavior of CoordinateVNF for new VNF.
    * - vdu_params
      - 0..N
      - VDU information of target VDU to update.
        Specifying a vdu_params is required for OpenStack VIM and not required for Kubernetes VIM.
    * - > vdu_id
      - 1
      - VDU name of target VDU to update.
    * - > old_vnfc_param
      - 0..1
      - Old VNFC connection information.
        Required for ssh connection in CoordinateVNF operation for application configuration to VNFC.
    * - >> cp_name
      - 1
      - Connection point name of old VNFC to update.
    * - >> username
      - 1
      - User name of old VNFC to update.
    * - >> password
      - 1
      - Password of old VNFC to update.
    * - >> coordination_server_param
      - 0..1
      - Information to access coordination server.
        It is required when using coordinateVNF script which calling Coordination API.
    * - \>>> endpoint
      - 1
      - Endpoint URL of coordination server.
    * - \>>> access_info
      - 1
      - Profile required for access coordination server
        (e.g. User name and password).
    * - > new_vnfc_param
      - 0..1
      - New VNFC connection information.
        Required for ssh connection in CoordinateVNF operation for application configuration to VNFC.
    * - >> cp_name
      - 1
      - Connection point name of new VNFC to update.
    * - >> username
      - 1
      - User name of new VNFC to update.
    * - >> password
      - 1
      - Password of new VNFC to update.
    * - >> coordination_server_param
      - 0..1
      - Information to access coordination server.
        It is required when using coordinateVNF script which calling Coordination API.
    * - \>>> endpoint
      - 1
      - Endpoint URL of coordination server.
    * - \>>> access_info
      - 1
      - Profile required for access coordination server
        (e.g. User name and password).
    * - external_lb_param
      - 0..1
      - Load balancer information that requires configuration changes.
        Required only for the Blue-Green deployment process of OpenStack VIM.
    * - > ip_address
      - 1
      - IP address of load balancer server.
    * - > username
      - 1
      - User name of load balancer server.
    * - > password
      - 1
      - Password of load balancer server.

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

* Add new sample VNF packages containing new coordinate VNF scripts.
* Add new functional tests.
* Add new utility functions to act as a coordination client.

Dependencies
============

None

Testing
========

Functional test cases will be added for rolling update
with the new sample coordinateVNF script.

Documentation Impact
====================

New utility functions to act as a coordination client
will be described in user manual.

References
==========
.. [#NFV-SOL002_351]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.05.01_60/gs_NFV-SOL002v030501p.pdf
.. [#Coordinate-script]
  https://specs.openstack.org/openstack/tacker-specs/specs/yoga/upgrade-vnf-package.html
.. [#NFV-SOL001_351]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/03.05.01_60/gs_NFV-SOL001v030501p.pdf
.. [#NFV-SOL013_341]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.04.01_60/gs_NFV-SOL013v030401p.pdf
