..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


====================================================
REST API for VNF based on ETSI NFV-SOL specification
====================================================

https://blueprints.launchpad.net/tacker/+spec/support-etsi-nfv-specs

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on of the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.


Problem description
===================

At the moment, Tacker uses its own API which describes CRUD operations
with components based on ETSI NFV MANO standards.

However, these operations are not aligned with the current ETSI NFV
data-model. As a result, there might be lack of compatibility with `3rd
party VNFs` [#etsi_plugtest2]_, as they are developed according to ETSI
NFV specifications.  In addition, the mismatch with the generally
accepted specifications brings additional complexity for integrations
with 3rd party ETSI-compliant systems thereby increasing time and
efforts for brownfield deployments.  ETSI NVF specifications describe
not just internal logic of MANO, but it also interacts with 3rd party
systems as VIM, SDN Controllers, VNFs, EMSs and OSS and are actively
used by multiple vendors in the market. Support of key ETSI NFV
specifications will significantly reduce efforts for Tacker integration
into Telecom production networks and also will simplify further
development and support of future standards.


Proposed change
===============

Introduce a new interface to invoke VNF lifecycle management operations
of VNF instances towards the VNFM.

The operations provided through this interface are:

* Create VNF Identifier
* Query VNF
* List VNF Identifier
* Delete VNF Identifier
* Instantiate VNF
* Heal VNF
* Terminate VNF

1) Flow of creation of a VNF instance resource
----------------------------------------------

.. seqdiag::

  seqdiag {
    Consumer -> VNFM [label = "1. POST .../vnf_instances"];
    VNFM -->> VNFM [label = "2. Create VNF instance resource"];
    Consumer <- VNFM [label = "3. 201 Created"];
  }

The procedure consists of the following steps as illustrated in above sequence:

* The Consumer sends a POST request to the "VNF Instances" resource
  including in the payload body a data structure of type
  "CreateVnfRequest".
* The VNFM creates a new VNF instance resource in NOT_INSTANTIATED
  state, and the associated VNF instance identifier. Some attribute in a
  VNF instance resource come from VNF package given in
  "CreateVnfRequest".
* The VNFM returns a 201 Created response containing a representation of
  the VNF instance resource just created by the VNFM, and provides the
  URI of the newly-created resource in the "Location" HTTP header.

.. note:: VNF instance resource requires VNF package registerd in
          advance. And also VNFD in VNF package must comply to
          `NFV-SOL001`_.

Postcondition: Upon successful completion, the VNF instance resource has
been created in "NOT_INSTANTIATED" state.


2) Flow of Instantiation of a VNF instance
------------------------------------------

.. seqdiag::

  seqdiag {
    Client -> WSGIMiddleware [label = "instantiate VNF"];
    WSGIMiddleware -->> WSGIMiddleware [label = "request validation"];
    Client <-- WSGIMiddleware [label = "202 Accepted"];
    WSGIMiddleware -> TackerConductor [label = "Trigger asynchronous task"];
    TackerConductor --> VnfLcmDriver [label = "instantiate_vnf(vnf_instance,
        instantiate_vnf_request)"];
    VnfLcmDriver --> ToscaParser [label = "read csar"];
    VnfLcmDriver <-- ToscaParser [label = "tosca object"];
    VnfLcmDriver -->> VnfLcmDriver [label = "get VNFD, prepare resource request"];
    VnfLcmDriver --> OpenstackDriver [label = "1. pre_instantiate_vnf(resources)"];
    OpenstackDriver --> Glance [label = "createImage"]
    OpenstackDriver <-- Glance [label = "image created"]
    VnfLcmDriver <-- OpenstackDriver [label = " resource  created"];
    VnfLcmDriver --> OpenstackDriver [label = "instantiate_vnf(vnf_instance,
        instantiate_vnf_request, vnfd_dict, resource_list)"];
    OpenstackDriver --> HeatClient [label = "create Heat Client"];
    OpenstackDriver <-- HeatClient [label = "Heat Client"];

    OpenstackDriver --> TranslateTemplate [label = "convert Tosca to HOT"];
    TranslateTemplate --> ToscaParser [label = "get tosca template"];
    TranslateTemplate <-- ToscaParser [label = "tosca template"];
    TranslateTemplate --> HeatTranslator [label = "Tosca to HOT"];
    TranslateTemplate <-- HeatTranslator [label = "HOT"];
    TranslateTemplate --> ToscaUtil [label = "post processing HOT using
        resource info and instantiateVnf request"];
    TranslateTemplate <-- ToscaUtil [label = "HOT"];
    OpenstackDriver <-- TranslateTemplate [label = "HOT"];
    OpenstackDriver --> Heat [label = "2. create stack"];
    OpenstackDriver <-- Heat [label = "stack created"];
    VnfLcmDriver <-- OpenstackDriver [label = "return stack id"];
    VnfLcmDriver -->> VnfLcmDriver [label = "3 update DB"];
    TackerConductor <-- VnfLcmDriver [label = "instantiation completed"];
  }

The procedure consists of the following steps as illustrated in above sequence:

#. During the pre instantiation process of VNF, VNFM will create images as
   described in the VNFD of the given deployment flavor using Glance client.
   According to ETSI NFV documents, NFVO should hold image information and
   register images to VIM directly, then, NFVO should provide image ids to
   VNFM with Grant API, but in ``U`` release, VNFM will register images
   directly to VIM.
#. Openstack driver will create stack using Heat and wait till it's status
   become `CREATE_COMPLETE`.
#. VnfLcmDriver will update DB for instantiatedState as ``INSTANTIATED``,
   vnf_state as ``STARTED`` and vnf package usage_state as ``IN_USE``
   accordingly.

.. note:: External network such as extVirtualLinks, extLinkPorts and
          extManagedVirtualLinks are assumed to be created by customer.
          According to ETSI NFV documents, these networks should be
          created by NFVO, however, functions related to NFVO will be
          future work. So, Tacker will not create external networks.

3) Flow of Heal of a VNF instance
---------------------------------

Precondition: VNF instance in "INSTANTIATED" state.

.. seqdiag::

  seqdiag {
    Client -> WSGIMiddleware [label = "1. HEAL VNF"];
    WSGIMiddleware -->> WSGIMiddleware [label = "request validation"];
    Client <-- WSGIMiddleware [label = "202 Accepted"];
    WSGIMiddleware -> TackerConductor [label = "Trigger asynchronous task"];
    TackerConductor --> VnfLcmDriver [label = "heal_vnf(vnf_instance, heal_vnf_request)"];
    VnfLcmDriver --> OpenstackDriver [label = "heal_vnf(vnf_instance, vim_connection_info,heal_vnf_request)"];
    OpenstackDriver --> Heat [label = "2. Mark resource unhealthy"];
    OpenstackDriver <-- Heat;
    OpenstackDriver --> Heat [label = "3. update stack"];
    OpenstackDriver <-- Heat [label = "stack updated"];
    VnfLcmDriver <-- OpenstackDriver;
    VnfLcmDriver --> OpenstackDriver [label = "post_heal_vnf(vnf_instance, vim_connection_info,heal_vnf_request)"];
    OpenstackDriver --> Heat [label = "4. get updated resource data"];
    OpenstackDriver <-- Heat [label = "resources"];
    VnfLcmDriver <-- OpenstackDriver;
    VnfLcmDriver -->> VnfLcmDriver [label = "5. update DB"];
    TackerConductor <-- VnfLcmDriver [label = "request successfully completed"];

  }

The procedure consists of the following steps as illustrated in above sequence:

#. Consumer sends a POST request to the "HEAL VNF Instance" resource.
#. OpenstackDriver will send request to HEAT to mark resource unhealthy based on HEAL Request.
#. OpenstackDriver will send request to HEAT to update the stack.
#. OpenstackDriver will send request to HEAT to get the updated resource data of the stack.
#. VnfLcmDriver will update the details of updated resource in DB.


Postcondition: VNF instance in "INSTANTIATED" state, and healed.

4) Flow of Termination of a VNF instance
----------------------------------------

.. seqdiag::

  seqdiag {
    Client -> WSGIMiddleware [label = "Terminate VNF"];
    WSGIMiddleware -->> WSGIMiddleware [label = "request validation"];
    Client <-- WSGIMiddleware [label = "202 Accepted"];
    WSGIMiddleware -> TackerConductor [label = "Trigger asynchronous task"];
    TackerConductor --> VnfLcmDriver [label = "terminate_vnf(vnf_instance, terminate_vnf_request)"];
    VnfLcmDriver --> OpenstackDriver [label = "terminate_vnf(vnf_instance, terminate_vnf_request, resource_list)"];
    OpenstackDriver --> Heat [label = "1. delete stack"];
    OpenstackDriver <-- Heat [label = "stack deleted"];
    OpenstackDriver --> Glance [label = "2. delete images"]
    OpenstackDriver <-- Glance [label = "images deleted"]
    VnfLcmDriver <-- OpenstackDriver [label = "resources removed"];
    TackerConductor <-- VnfLcmDriver [label = "request successfully completed"];
    TackerConductor -->> TackerConductor [label = "update DB"];
  }

The procedure consists of the following steps as illustrated in above sequence:

#. Consumer sends a POST request to the "Terminate VNF Instance" resource.
#. OpenstackDriver will delete the stack using Heat.
#. The image created during instantiation will be deleted.

Postcondition: "instantiationState" should be set to "NOT_INSTANTIATED".


5) Flow of deletion of a VNF instance resource
----------------------------------------------

Precondition: VNF instance in NOT_INSTANTIATED state.

.. seqdiag::

  seqdiag {
    Consumer -> VNFM [label = "1.DELETE .../vnf_instances/{vnfInstanceId}"];
    VNFM -->> VNFM [label = "2. Delete VNF instance resource"];
    Consumer <- VNFM [label = "3. 204 No content"];
    }

The procedure consists of the following steps as illustrated in above sequence:

#. Consumer sends a DELETE request to the "Individual VNF Instance" resource.
#. The VNFM deletes the VNF instance resource and the associated VNF instance
   identifier.
#. The VNFM returns a "204 No Content" response with an empty payload body.

Postcondition: VNF instance resource removed.

Error handling: If the "Individual VNF instance" resource is not in
                NOT_INSTANTIATED state, the VNFM rejects the
                deletion request.


Support subset of SOL001 VNFD TOSCA service template
----------------------------------------------------

We are planning to provide limited support of VNFD TOSCA service
template defined in `NFV-SOL001`_

Supported Data Types
~~~~~~~~~~~~~~~~~~~~

#. tosca.datatypes.nfv.ConnectivityType
#. tosca.datatypes.nfv.VirtualMemory
#. tosca.datatypes.nfv.VirtualCpu
#. tosca.datatypes.nfv.VduProfile
#. tosca.datatypes.nfv.VlProfile
#. tosca.datatypes.nfv.InstantiationLevel
#. tosca.datatypes.nfv.VduLevel
#. tosca.datatypes.nfv.ScaleInfo
#. tosca.datatypes.nfv.ScalingAspect
#. tosca.datatypes.nfv.LinkBitrateRequirements
#. tosca.datatypes.nfv.VnfAdditionalConfigurableProperties
#. tosca.datatypes.nfv.SwImageData
#. tosca.datatypes.nfv.VirtualBlockStorageData
#. tosca.datatypes.nfv.VirtualLinkBitrateLevel
#. tosca.datatypes.nfv.ChecksumData

Supported Artifact Types
~~~~~~~~~~~~~~~~~~~~~~~~

#. tosca.artifacts.nfv.SwImage

Supported Capability Types
~~~~~~~~~~~~~~~~~~~~~~~~~~

#. tosca.capabilities.nfv.VirtualBindable
#. tosca.capabilities.nfv.VirtualLinkable
#. tosca.capabilities.nfv.VirtualCompute
#. tosca.capabilities.nfv.VirtualStorage

Supported Interface Types
~~~~~~~~~~~~~~~~~~~~~~~~~

#. tosca.interfaces.nfv.Vnflcm

Supported Node Types
~~~~~~~~~~~~~~~~~~~~

#. tosca.nodes.nfv.VNF
#. tosca.nodes.nfv.Vdu.Compute
#. tosca.nodes.nfv.Vdu.VirtualBlockStorage
#. tosca.nodes.nfv.VduCp
#. tosca.nodes.nfv.VnfVirtualLink

Supported Policy Types
~~~~~~~~~~~~~~~~~~~~~~

#. tosca.policies.nfv.InstantiationLevels
#. tosca.policies.nfv.VduInstantiationLevels
#. tosca.policies.nfv.VirtualLinkInstantiationLevels
#. tosca.policies.nfv.ScalingAspects
#. tosca.policies.nfv.VduScalingAspectsDeltas
#. tosca.policies.nfv.VduInitialDelta


Alternatives
------------

None



Data model impact
-----------------

Add below new tables in 'tacker' database. The corresponding schemas are
detailed below:-

vnf_instances::
    `id` uuid

    `vnfd_id` uuid

    `vnf_instance_name` varchar(255) NULL

    `vnf_instance_description` varchar(1024) NULL

    `vnf_provider` varchar(255) NOT NULL

    `vnf_product_name` varchar(255) NOT NULL

    `vnf_software_version` varchar(255) NOT NULL

    `vnfd_version` varchar(255) NOT NULL

    `instantiation_state` varchar(255) NOT NULL

    `vim_connection_info` json NULL

    `tenant_id` varchar(64) NOT NULL

    `created_at` datetime NOT NULL

    `updated_at` datetime NULL

    `deleted_at` datetime NULL

    `deleted` tinyint(1) NULL

This table will have `id` as primary key. `vnfd_id` will be foreign key
of `vnf_package_vnfd`.`vnfd_id`.


vnf_instantiated_info::
    `id` int(11)

    `vnf_instance_id` uuid

    `flavour_id` varchar(255) NOT NULL

    `ext_cp_info` json NOT NULL

    `ext_virtual_link_info` json NULL

    `ext_managed_virtual_link_info` json NULL

    `vnfc_resource_info` json NULL

    `vnf_virtual_link_resource_info` json NULL

    `virtual_storage_resource_info` json NULL

    `vnf_state` varchar(255) NOT NULL

    `instance_id` varchar(255) NOT NULL

    `created_at` datetime NOT NULL

    `updated_at` datetime NULL

    `deleted_at` datetime NULL

    `deleted` tinyint(1) NULL

This table will have `id` as primary key. `vnf_instance_id` will be foreign
key of `vnf_instances`.`id`. `flavour_Id` will be foreign key of
`vnf_deployment_flavours`.`flavour_id`.


vnf_resources::
    `id` uuid

    `vnf_instance_id` uuid

    `resource_name` varchar(255) NULL

    `resource_type` Integer NOT NULL

    `resource_identifier` text NOT NULL

    `resource_status` text NOT NULL

    `created_at` datetime NOT NULL

    `updated_at` datetime NULL

    `deleted_at` datetime NULL

    `deleted` tinyint(1) NULL

This table will have `id` as primary key. `vnf_instance_Id` will be foreign
key of `vnf_instances`.`id`.

.. note:: The `json` data types for columns `vim_connection_info`,
          `ext_cp_info`, `ext_virtual_link_info`,
          `ext_managed_virtual_link_info`, `vnfc_resource_info`,
          `vnf_virtual_link_resource_info`,
          `virtual_storage_resource_info` will contain json data.
          While saving the data in DB, The version object will be serialized
          and stored as json and during retrieving it from DB, The
          json data will be deserialized to create the version object.

REST API impact
---------------

The following restFul APIs will be added:

* | **Name**: Create VNF Identifier
  | **Description**: Creates a new VNF instance resource
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances
  | **Request**:

  +------------------+-------------+------------------------------+
  | Data type        | Cardinality | Description                  |
  +==================+======+======+==============================+
  | CreateVnfRequest | 1           | The VNF creation parameters. |
  +------------------+-------------+------------------------------+

  +----------------------------+------------------------------+-------------+------------------+
  | Attribute name             | Data type                    | Cardinality | Supported in (U) |
  +============================+==============================+=============+==================+
  | vnfdId                     | Identifier                   | 1           |    Yes           |
  +----------------------------+------------------------------+-------------+------------------+
  | vnfInstanceName            | String                       | 0..1        |    Yes           |
  +----------------------------+------------------------------+-------------+------------------+
  | vnfInstanceDescription     | String                       | 0..1        |    Yes           |
  +----------------------------+------------------------------+-------------+------------------+
  | metadata                   | KeyValuePairs                | 0..1        |    No            |
  +----------------------------+------------------------------+-------------+------------------+


  | **Response**:

  +-------------+-------------+------------------+-----------------------------------------------------+
  | Data type   | Cardinality | Response Codes   | Description                                         |
  +=============+=============+==================+=====================================================+
  | VnfInstance | 1           | Success 201      | A VNF Instance identifier was created successfully. |
  |             |             | Error 400 401    |                                                     |
  |             |             | 403              |                                                     |
  +-------------+-------------+------------------+-----------------------------------------------------+

* | **Name**: Query VNF
  | **Description**: Request to existing VNF instance resource by its id
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}
  | **Resource URI variables for this resource**:

  +---------------+---------------------------------+
  | Name          | Description                     |
  +===============+=================================+
  | vnfInstanceId | Identifier of the VNF instance. |
  +---------------+---------------------------------+

  | **Response**:

  +-------------+-------------+-----------------+------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes  | Description                                                            |
  +=============+=============+=================+========================================================================+
  | VnfInstance | 1           | Success: 200    |                                                                        |
  |             |             | Error: 401, 403 | Information about an individual VNF instance was queried successfully. |
  |             |             | 404             |                                                                        |
  +-------------+-------------+-----------------+------------------------------------------------------------------------+

* | **Name**: List VNF Instances
  | **Description**: Request to list all existing VNF instances
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_instances
  | **Response**:

  +-------------+-------------+-----------------+------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes  | Description                                                            |
  +=============+=============+=================+========================================================================+
  | VnfInstance | 0..N        | Success: 200    | Information about zero or more VNF instances was queried successfully. |
  |             |             | Error: 401, 403 |                                                                        |
  +-------------+-------------+-----------------+------------------------------------------------------------------------+

  +----------------------------+------------------------------+-------------+-----------------+
  | Attribute name             | Data type                    | Cardinality | Supported in (U)|
  +============================+==============================+=============+=================+
  | id                         | Identifier                   | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfInstanceName            | String                       | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfInstanceDescription     | String                       | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfdId                     | Identifier                   | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfProvider                | String                       | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfProductName             | String                       | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfSoftwareVersion         | Version                      | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfdVersion                | Version                      | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | vnfConfigurableProperties  | KeyValuePairs                | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | vimConnectionInfo          | VimConnectionInfo            | 0..N -> 0..1| Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | instantiationState         | Enum                         | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | instantiatedVnfInfo        | Structure                    | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >flavourId                 | IdentifierInVnfd             | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >vnfState                  | VnfOperationalStateType      | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >scaleStatus               | ScaleInfo                    | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >extCpInfo                 | VnfExtCpInfo                 | 1..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >extVirtualLinkInfo        | ExtVirtualLinkInfo           | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >extManagedVirtualLinkInfo | ExtManagedVirtualLinkInfo    | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >monitoringParameters      | MonitoringParameter          | 0..N        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >localizationLanguage      | String                       | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >vnfcResourceInfo          | VnfcResourceInfo             | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >vnfVirtualLinkResourceInfo| VnfVirtualLinkResourceInfo   | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >virtualStorageResourceInfo| VirtualStorageResourceInfo   | 0..N        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | metadata                   | KeyValuePairs                | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | extensions                 | KeyValuePairs                | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | _links                     | Structure                    | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >self                      | Link                         | 1           | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >indicators                | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >instantiate               | Link                         | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >terminate                 | Link                         | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >scale                     | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >scaleToLevel              | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >changeFlavour             | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >heal                      | Link                         | 0..1        | Yes             |
  +----------------------------+------------------------------+-------------+-----------------+
  | >operate                   | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+
  | >changeExtConn             | Link                         | 0..1        | No              |
  +----------------------------+------------------------------+-------------+-----------------+

* | **Name**: Delete VNF Instance
  | **Description**: Request to delete VNF instance resource by its id
  | **Method type**: DELETE
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}
  | **Resource URI variables for this resource**:

  +---------------+---------------------------------+
  | Name          | Description                     |
  +===============+=================================+
  | vnfInstanceId | Identifier of the VNF instance. |
  +---------------+---------------------------------+

  | **Response**:

  +-------------+-------------+-----------------+----------------------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes  | Description                                                                            |
  +=============+=============+=================+========================================================================================+
  | n/a         |             | Success: 204    |                                                                                        |
  |             |             | Error: 401, 403 | The VNF instance resource and the associated VNF identifier were deleted successfully. |
  |             |             | 404             |                                                                                        |
  +-------------+-------------+-----------------+----------------------------------------------------------------------------------------+

* | **Name**: Instantiate VNF task
  | **Description**: This task resource represents the "Instantiate VNF"
    operation. The client can use this resource to instantiate a VNF instance.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}/instantiate
  | **Resource URI variables for this resource**:

  +---------------+--------------------------------------------------------+
  | Name          | Definition                                             |
  +===============+========================================================+
  | vnfInstanceId | The identifier of the VNF instance to be instantiated. |
  +---------------+--------------------------------------------------------+

  | **Request**:

  +-------------------------+-------------+-----------------------------------------+
  | Data type               | Cardinality | Description                             |
  +=========================+=======================================================+
  | InstantiateVnfRequest   |     1       | Parameters passed to instantiate task.  |
  +-------------------------+-------------+-----------------------------------------+

  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | Attribute name            | Data type                 | Cardinality | Supported in (U) | Description                                                                                        |
  +===========================+===========================+=============+==================+====================================================================================================+
  | flavourId                 | IdentifierInVnfd          | 1           | Yes              | Identifier of the VNF deployment flavour to be instantiated.                                       |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | instantiationLevelId      | IdentifierInVnfd          | 0..1        | Yes              | Identifier of the instantiation level of the deployment flavour to be instantiated.                |
  |                           |                           |             |                  | If not present, the default instantiation level as declared in the VNFD is instantiated.           |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | extVirtualLinks           | ExtVirtualLinkData        | 0..N        | Yes              | Information about external VLs to connect the VNF to.                                              |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | vimConnectionInfo         | VimConnectionInfo         | 0..N -> 0..1| Yes              | Information about VIM connections to be used for managing the resources for the VNF instance.      |
  |                           |                           |             |                  | In U release, only 0..1 VIMConnectionInfo will be accepted.                                        |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | additionalParams          | KeyValuePairs             | 0..1        | Yes              | Additional input parameters for the instantiation process, specific to the VNF being instantiated. |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | extManagedVirtualLinks    | ExtManagedVirtualLinkData | 0..N        | Yes              |                                                                                                    |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | localizationLanguage      | String                    | 0..1        | No               |                                                                                                    |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+
  | extensions                | KeyValuePairs             | 0..1        | No               |                                                                                                    |
  +---------------------------+---------------------------+-------------+------------------+----------------------------------------------------------------------------------------------------+

  | **Response**:

  +-------------+-------------+------------------+-------------------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes   | Description                                                                         |
  +=============+=============+==================+=====================================================================================+
  | n/a         |             | Success: 202     |                                                                                     |
  |             |             | Error: 400, 401  | The request was accepted for processing, but the processing has not been completed. |
  |             |             | 403, 404, 409    |                                                                                     |
  +-------------+-------------+------------------+-------------------------------------------------------------------------------------+

* | **Name**: Heal VNF task
  | **Description**: Request for healing a VNF instance
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}/heal
  | **Resource URI variables for this resource**:

  +---------------+------------------------------------------------------+
  | Name          | Description                                          |
  +===============+======================================================+
  | vnfInstanceId | The identifier of the VNF instance to be healed.     |
  +---------------+------------------------------------------------------+

  | **Request**:

  +----------------------------+-------------+-----------------------------------------+
  | Data type                  | Cardinality | Description                             |
  +============================+=============+=========================================+
  | HealVnfRequest             |     1       | Parameters for the Heal VNF operation.  |
  +----------------------------+-------------+-----------------------------------------+

  +----------------------------+------------------------------+-------------+------------------+--------------------------+
  | Attribute name             | Data type                    | Cardinality | Supported in (U) |  Description             |
  +============================+==============================+=============+==================+==========================+
  | vnfcInstanceId             | Identifier                   | 0..N        | Yes              |                          |
  +----------------------------+------------------------------+-------------+------------------+--------------------------+
  | cause                      | String                       | 0..1        | Yes              |                          |
  +----------------------------+------------------------------+-------------+------------------+--------------------------+
  | additionalParams           | KeyValuePairs                | 0..1        | No               |                          |
  +----------------------------+------------------------------+-------------+------------------+--------------------------+


  | **Response**:

  +-------------+-------------+-----------------+-------------------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes  | Description                                                                         |
  +=============+=============+=================+=====================================================================================+
  | n/a         | n/a         | Success: 202    |                                                                                     |
  |             |             | Error: 401, 403 |  The request was accepted for processing, but the processing has not been completed.|
  |             |             | 404, 409        |                                                                                     |
  +-------------+-------------+-----------------+-------------------------------------------------------------------------------------+

* | **Name**: Terminate VNF task
  | **Description**: This task resource represents the "Terminate VNF"
    operation. The client can use this resource to terminate a VNF instance.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/vnf_instances/{vnfInstanceId}/terminate
  | **Resource URI variables for this resource**:

  +---------------+------------------------------------------------------+
  | Name          | Description                                          |
  +===============+======================================================+
  | vnfInstanceId | The identifier of the VNF instance to be terminated. |
  +---------------+------------------------------------------------------+

  | **Request**:

  +-------------------------+-------------+-----------------------------------------+
  | Data type               | Cardinality | Description                             |
  +=========================+=======================================================+
  | TerminateVnfRequest   |     1       | Parameters passed to Terminate VNF task.  |
  +-------------------------+-------------+-----------------------------------------+

  +----------------------------+----------------+-----------------+-------------+-------------+-----------------------------------------------------------------------------------------+
  | Attribute name             | Data type      | Possible values | Cardinality | Support     | Description                                                                             |
  +============================+================+=================+=============+=============+=========================================================================================+
  | terminationType            | Enum (inlined) | FORCEFUL        | 1           | Yes         | Indicates whether forceful or graceful termination is requested.                        |
  |                            |                |                 |             |             | At first, only forceful termination will be supported.                                  |
  +----------------------------+----------------+-----------------+-------------+-------------+-----------------------------------------------------------------------------------------+
  | additionalParams           | KeyValuePairs  |                 | 0..1        | No          | Additional parameters to the termination process, specific to the VNF being terminated. |
  +----------------------------+----------------+-----------------+-------------+-------------+-----------------------------------------------------------------------------------------+
  | gracefulTerminationTimeout | Integer        |                 | 0..1        | Yes         | This attribute is only applicable in case of graceful termination.                      |
  |                            |                |                 |             |             | It defines the time to wait for the VNF to be taken out of service before shutting      |
  |                            |                |                 |             |             | down the VNF and releasing the resources.                                               |
  |                            |                |                 |             |             | The unit is seconds.                                                                    |
  +----------------------------+----------------+-----------------+-------------+-------------+-----------------------------------------------------------------------------------------+

  | **Response**:

  +-------------+-------------+------------------+-------------------------------------------------------------------------------------+
  | Data type   | Cardinality | Response Codes   | Description                                                                         |
  +=============+=============+==================+=====================================================================================+
  | n/a         |             | Success: 202     |                                                                                     |
  |             |             | Error: 400, 401  | The request was accepted for processing, but the processing has not been completed. |
  |             |             | 403, 404, 409    |                                                                                     |
  +-------------+-------------+------------------+-------------------------------------------------------------------------------------+

* Future work

  #. Scale VNF task
  #. Operate VNF task
  #. VNF LCM operation occurrences
  #. Individual VNF LCM operation occurrence


Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

Add new OSC commands in python-tackerclient to invoke VNF lifecycle management of VNF instances APIs.

+-----------------------+---------+------------------------------------------------------+-------------------+
| Name                  | Method  | URI                                                  | CLI Openstack     |
+=======================+=========+======================================================+===================+
| List vnf instances    | GET     | /vnflcm/v1/vnf_instances                             | vnflcm list       |
+-----------------------+---------+------------------------------------------------------+-------------------+
| Create vnf instance   | POST    | /vnflcm/v1/vnf_instances | vnflcm list               | vnflcm create     |
+-----------------------+---------+------------------------------------------------------+-------------------+
| Get vnf instance      | GET     | /vnflcm/v1/vnf_instances/{vnfInstanceID}             | vnflcm show       |
+-----------------------+---------+------------------------------------------------------+-------------------+
| Delete vnf instance   | DELETE  | /vnflcm/v1/vnf_instances/{vnfInstanceID}             | vnflcm delete     |
+-----------------------+---------+------------------------------------------------------+-------------------+
| Instantiate vnf task  | POST    | /vnflcm/v1/vnf_instances/{vnfInstanceID}/instantiate | vnflcm instantiate|
+-----------------------+---------+------------------------------------------------------+-------------------+
| Heal vnf task         | POST    | /vnflcm/v1/vnf_instances/{vnfInstanceID}/heal        | vnflcm heal       |
+-----------------------+---------+------------------------------------------------------+-------------------+
| Terminate vnf task    | POST    | /vnflcm/v1/vnf_instances/{vnfInstanceID}/terminate   | vnflcm terminate  |
+-----------------------+---------+------------------------------------------------------+-------------------+

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

Other contributors:
  Hiroyuki Jo <hiroyuki.jo.mt@hco.ntt.co.jp>

  Tushar Patil <tushar.vitthal.patil@gmail.com>

  Nitin Uikey <nitin.uikey@nttdata.com>

  Ajay Parja <Ajay.Parja@nttdata.com>

  Shubham Potale <Shubham.Potale@nttdata.com>

Work Items
----------

* Add new REST API endpoints to Tacker-server for VNF lifecycle management
  of VNF instances.
* Make changes in Heat-translator to translate new node types introduced in
  Tosca template version 1.2.
* Make changes in python-tackerclient to add new OSC commands for calling
  VNF lifecycle management of VNF instances restFul APIs.
* Add post processing to extract information regarding API request body.
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
.. _NFV-SOL001 : https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/02.06.01_60/gs_NFV-SOL001v020601p.pdf
.. _NFV-SOL002 : https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf (Chapter 5: VNF Lifecycle Management interface)
.. _NFV-SOL003 : https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_plugtest2] https://portal.etsi.org/Portals/0/TBpages/CTI/Docs/2nd_ETSI_NFV_Plugtests_Report_v1.0.0.pdf
