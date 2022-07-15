..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===================================
Enhance ChangeCurrentVNFPackage API
===================================

Blueprints: https://blueprints.launchpad.net/tacker/+spec/enhance-change-package

This specification enhances the ChangeCurrentVNFPackage API.

Problem description
===================

The ChangeCurrentVNFPackage API is defined in ETSI NFV-SOL003
v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_, according to the VNF software modification
procedure in ETSI NFV-IFA007 v3.3.1 [#ETSI-NFV-IFA007-v3.3.1]_.
Tacker supports the ChangeCurrentVNFPackage operation in Yoga release,
but Tacker has supported software image update case only and
lacks some parameters.
The following cases will be supported.

#. Change OpenStack flavor
#. Change external/internal Virtual Links(VL) and Connection Points(CP)
#. Add other ChangeCurrentVNFPackage API parameters

.. note::

  Yoga release only supports `RollingUpdate` process [#SPEC-Upgrade-Vnf-Pkg]_.
  This spec does not target the update process enhancement.

Proposed change
===============

(1) Add a function and VNF package samples to change OpenStack flavor
---------------------------------------------------------------------
This function can change the OpenStack flavor and provide the vertical
scaling of resources such as vMemory and vCPU in ChangeCurrentVNFPackage API.
This function will be implemented by using different HEAT input-parameters
in User Data [#Tacker_User_Data]_. We also aim to add these samples to
tacker documents. See the below.

.. note::

  ``computeFlavourId`` such as "m1.tiny" in HEAT input-parameters is
  set by VNFDs (``requested_additional_capability_name``) or Grant
  response. The information about flavor is managed in OpenStack Nova.

* BaseHOT

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: Test Base HOT

    parameters:
      nfv:
        type: json

    resources:
      VDU1:
        type: VDU1.yaml
        properties:
          flavor: { get_param: [ nfv, VDU, VDU1, computeFlavourId ] }
          image: { get_param: [ nfv, VDU, VDU1, vcImageId] }
          name: VDU1
          availability_zone: { get_param: [ nfv, VDU, VDU1, locationConstraints ] }

      VDU2:
        type: VDU2.yaml
        properties:
          flavor: { get_param: [ nfv, VDU, VDU2, computeFlavourId ] }
          image: { get_param: [ nfv, VDU, VDU2, vcImageId] }
          name: VDU2
          availability_zone: { get_param: [ nfv, VDU, VDU2, locationConstraints ] }


* Before: `input_params.yaml`

  "computeFlavourId" parameters of VDU1 and VDU2 are "m1.tiny".

  .. code-block:: json

    {
      "VDU": {
        {
          "VDU1": {
            "computeFlavourId": "m1.tiny",
            "locationConstraints": "nova"
          },
          "VDU1-VirtualStorage": {
            "vcImageId": "56c7b026-a23e-49e5-96c6-05ab90186965"
          },
          "VDU2": {
            "computeFlavourId": "m1.tiny",
            "locationConstraints": "nova"
          },
          "VDU2-VirtualStorage": {
            "vcImageId": "6b8a14f0-1b40-418a-b650-ae4a0378daa5"
          }
        }
      }
    }

* After: `scale_up_input_params.yaml`

  VDU2 will change new OpenStack flavor for scale-up ("m1.tiny"->"m1.small").

  .. code-block:: json

    {
      "VDU": {
        {
          "VDU1": {
            "computeFlavourId": "m1.tiny",
            "locationConstraints": "nova"
          },
          "VDU1-VirtualStorage": {
            "vcImageId": "56c7b026-a23e-49e5-96c6-05ab90186965"
          },
          "VDU2": {
            "computeFlavourId": "m1.small",
            "locationConstraints": "nova"
          },
          "VDU2-VirtualStorage": {
            "vcImageId": "6b8a14f0-1b40-418a-b650-ae4a0378daa5"
          }
        }
      }
    }

(2) Add a function to change external/internal Network
------------------------------------------------------
The following operations will be supported by using additional
ChangeCurrentVNFPackage API parameters
(``extVirtualLinks``, ``extManagedVirtualLinks``),
modified HOT input-parameters or BaseHOT templates.

.. note::

  In NFV SOL, an external NW is defined as being created or deleted
  without VNF LCM operations.Therefore, ChangeCurrentVNFPackage API
  will operate modification/additions/deletion of External CPs only.


* Change external CP

  * Modify external CP
  * Add external CP
  * Delete external CP

.. note::

  If ``extVirtualLinks -> extLinkPorts`` is present,
  "Add and Delete" means "Connect and Disconnect" external CP.
  Because in this case, externally provided link ports are
  used to connect/disconnect external CPs to the external VL.

* Change internal VL

  * Modify internal VL
  * Add internal VL
  * Delete internal VL

* Change internal CP

  * Modify internal CP
  * Add internal CP
  * Delete internal CP

There are several ways to change networks.
An example to modify external CP is described below.

* BaseHOT

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: Test Base HOT

    parameters:
      nfv:
        type: json

    resources:
      VDU1:
        type: OS::Nova::Server
        properties:
          networks:
          - port: { get_param: [ nfv, CP, VDU1_CP1, port ]  }

* Before: `VnfInstance`

  `VDU1_CP1` is connected to the external VL
  "67c837dc-c247-4a3e-ac0f-5603bfef1ba3".

  .. code-block:: json

    "instantiatedVnfInfo": {
      "extVirtualLinkInfo": [
        {
          "currentVnfExtCpData": [
            {
              "cpConfig": {
                "VDU1_CP1": {
                  "cpProtocolData": [
                    {
                      "ipOverEthernet": {
                        "ipAddresses": [
                          {
                            "numDynamicAddresses": 1,
                            "subnetId": "0cc4d7e2-37c5-49f0-98d2-da945b5841e5",
                            "type": "IPV4"
                          }
                        ]
                      },
                    "layerProtocol": "IP_OVER_ETHERNET"
                    }
                  ],
                  "linkPortId": "1f330fd3-b037-4d42-993f-8df45b0efa99",
                  "parentCpConfigId": "a0eab66b-e82f-4a42-a2e5-57d0b02abab3"
                }
              },
              "cpdId": "VDU1_CP1"
            }
          ],
          "extLinkPorts": [
            {
              "cpInstanceId": "cp-req-1f330fd3-b037-4d42-993f-8df45b0efa99",
              "id": "1f330fd3-b037-4d42-993f-8df45b0efa99",
              "resourceHandle": {
                "resourceId": "04ab6361-7e6c-4255-a10c-2ab1a6daa4c2"
              }
            }
          ],
          "id": "3d0d9c9b-dbbc-41d6-84ef-1bf2529753d5",
          "resourceHandle": {
            "resourceId": "67c837dc-c247-4a3e-ac0f-5603bfef1ba3",
            "resourceProviderId": "Company",
            "vimConnectionId": "02ef2cca-d853-4e90-950a-a6d0ce86ec3a"
          }
        }
      ]
    }

* After: `extVirtualLinks` in the "ChangeCurrentVnfPkgRequest"

  `VDU1_CP1` is disconnected and reconnected to
  the external VL "d703f250-7d54-45b3-b29e-2ef8a5e5f6a1".

  .. code-block:: json

    "extVirtualLinks": [
      {
        "id": "3d0d9c9b-dbbc-41d6-84ef-1bf2529753d5",
        "vimConnectionId": "02ef2cca-d853-4e90-950a-a6d0ce86ec3a",
        "resourceProviderId": "Company",
        "resourceId": "d703f250-7d54-45b3-b29e-2ef8a5e5f6a1",
        "extCps": [
          {
            "cpdId": "VDU1_CP1",
            "cpConfig": {
              "VDU1_CP1": {
                "parentCpConfigId": "2254b5d5-35f7-4d7e-b467-0ef17866ef1d",
                "linkPortId": "5353df3d-16de-4789-8a57-0623b5c83700",
                "cpProtocolData": [
                  {
                    "layerProtocol": "IP_OVER_ETHERNET",
                    "ipOverEthernet": {
                      "ipAddresses": [
                        {
                          "type": "IPV4",
                          "numDynamicAddresses": 1,
                          "subnetId": "5156e206-c513-41ff-a6e6-b45516046188"
                        }
                      ]
                    }
                  }
                ]
              }
            }
          }
        ],
        "extLinkPorts": [
          {
            "id": "5353df3d-16de-4789-8a57-0623b5c83700",
            "resourceHandle": {
              "resourceId": "0ec87b04-c441-4859-8a44-53e28f685ea2"
            }
          }
        ]
      }
    ]

.. note::

  ``extVirtualLinks`` might be omitted if the entries in the list are unchanged.


(3) Add ChangeCurrentVNFPackage API parameters
----------------------------------------------

ChangeCurrentVNFPackage API parameters that are not
implemented by Tacker will be supported.

* ChangeCurrentVnfPkgRequest

  .. list-table::
      :widths: 15 10 30 30
      :header-rows: 1

      * - Attribute name
        - Data type
        - Cardinality
        - Description
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
        - "vimConnectionInfo" attribute array in "VnfInstance".
      * - extensions
        - KeyValuePairs
        - 0..1
        - "extensions" attribute in "VnfInstance".
      * - vnfConfigurableProperties
        - KeyValuePairs
        - 0..1
        - "vnfConfigurableProperties" attribute in "VnfInstance".

.. note::

  Tacker applies the ``vimConnectionInfo``, ``extensions``
  and ``vnfConfigurableProperties`` attributes in the
  "ChangeCurrentVnfPkgRequest" data structure in the payload body
  to the existing attributes from the "VnfInstance" data structure
  according to the rules of JSON Merge Patch(IETF RFC 7396 [#IETF-RFC-7396]_).
  Tacker also needs to unify the implemented merge policies of
  "VnfInfoModificationRequest" to the above policy.

Data model impact
-----------------

None


REST API impact
---------------

The following RESTful API will be updated.
This RESTful API will be based on ETSI NFV-SOL003
v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_.

* | **Name**: change current VNF Package
  | **Description**: Request to change current VNF package by vnfd ID.
  | **Method type**: POST
  | **URL**: /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg
  | **Request**:

  .. list-table::
      :widths: 15 10 30
      :header-rows: 1

      * - Data type
        - Cardinality
        - Description
      * - ChangeCurrentVnfPkgRequest
        - 1
        - Parameters for the change current VNF package.

  .. list-table::
      :widths: 15 15 10 30 10 10
      :header-rows: 1

      * - Attribute name
        - Data type
        - Cardinality
        - Parameter description
        - Supported in (Y)
        - Supported in (Z)
      * - vnfdId
        - Identifier
        - 1
        - Identifier of the VNFD which defines the destination VNF Package
          for the change.
        - Yes
        - Yes
      * - extVirtualLinks
        - ExtVirtualLinkData
        - 0..N
        - Information about external VLs to connect the VNF to.
        - No
        - Yes
      * - extManagedVirtualLinks
        - ExtManagedVirtualLinkData
        - 0..N
        - Information about internal VLs that are managed by the NFVO.
        - No
        - Yes
      * - vimConnectionInfo
        - map (VimConnectionInfo)
        - 0..N
        - "vimConnectionInfo" attribute array in "VnfInstance".
        - No
        - Yes
      * - additionalParams
        - KeyValuePairs
        - 0..1
        - Additional parameters passed by the NFVO as input to the process.
        - Yes
        - Yes
      * - extensions
        - KeyValuePairs
        - 0..1
        - "extensions" attribute in "VnfInstance".
        - No
        - Yes
      * - vnfConfigurableProperties
        - KeyValuePairs
        - 0..1
        - "vnfConfigurableProperties" attribute in "VnfInstance".
        - No
        - Yes

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
  Yuta Kazato <yuta.kazato.nw@hco.ntt.co.jp>

  Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>

Other contributors:
  Hiroo Kitamura <hiroo.kitamura@ntt-at.co.jp>

Work Items
----------

* Implement additional ChangeCurrentVNFPackage API parameters
  in tacker-server and tacker-conductor.
* Implement additional functions of upgrade VNF operations.
* Add and update unit and functional tests.
* Add and update sample vnf packages.
* Update the Tacker User Guide: ChangeCurrentVNFPackage API.

Dependencies
============

* Change current VNF package (/vnf_instances/{vnfInstanceId}/
  change_vnfpkg POST) [#ETSI-NFV-SOL003-v3.3.1]_

* Tacker SPEC: Support ChangeCurrentVNFPackage for
  VNF software modification [#SPEC-Upgrade-Vnf-Pkg]_

Testing
=======

Unit and functional test cases will be added and
updated for the ChangeCurrentVNFPackage API.

Documentation Impact
====================

Description about additional upgrade VNF operations
and ChangeCurrentVNFPackage API parameters will be added to
the Tacker User Guide.

References
==========

.. [#ETSI-NFV-SOL003-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
.. [#ETSI-NFV-IFA007-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/007/03.03.01_60/gs_nfv-ifa007v030301p.pdf
.. [#Tacker_User_Data] https://docs.openstack.org/tacker/latest/user/userdata_script.html
.. [#IETF-RFC-7396]  https://tools.ietf.org/html/rfc7396
.. [#SPEC-Upgrade-Vnf-Pkg] https://specs.openstack.org/openstack/tacker-specs/specs/yoga/upgrade-vnf-package.html
