..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode

=============================================
Enhance Heat input on the basis of NFV SOL014
=============================================

https://blueprints.launchpad.net/tacker/+spec/support-hot-according-to-nfv-sol014

This specification enhances the Tacker's supported parameters mapped
to the OpenStack's Heat Orchestration Template (HOT) [#Heat_API]_.
The specification adds supported parameters and focuses
on how they can be mapped onto the HOT to instantiate the VNF.

Problem description
===================
ETSI NFV SOL014 [#ETSI_SOL014]_  specified a set of data models for
information exchanged over the virtualised resource management.
It also focused on implementation examples of the
data models defined for the various interfaces using the HOT.

Though Tacker has already been implemented LCM operations
using HOT [#Userdata]_ , its supported parameters were limited.

The further support of the parameters in HOT with SOL014 makes
Tacker more flexible and powerful as Generic-VNFM.

Proposed change
===============
This specification enables Tacker to support more parameters in the input
data for Heat. To instantiate VNF, Tacker will generate the input data for
Heat in accordance with VNF Descriptor (VNFD), information in InstantiateVnfRequest
operation, and Grant operation defined in SOL001 [#ETSI_SOL001]_ and SOL003 [#ETSI_SOL003]_ .

Following parameters will be supported.

.. list-table::
    :header-rows: 1
    :widths: 2 ,2 ,2 ,2 ,2 ,2 ,2

    * -  category
      -  parameter
      -  VNFD
      -  API - InstantiateVnfRequest
      -  API - Grant
      -  Heat
      -  Supported in (W)
    * -  Compute
      -  name
      -  tosca.nodes.nfv.Vdu.Compute
      -  N/A
      -  N/A
      -  OS::Nova::Server > properties > name
      -  NO
    * -  Compute
      -  flavour
      -  tosca.nodes.nfv.Vdu.Compute
      -  N/A
      -  vimAssets
      -  OS::Nova::Server > properties > flavor
      -  YES
    * -  Compute
      -  image
      -  tosca.artifacts.nfv.SwImage
      -  N/A
      -  vimAssets
      -  OS::Nova::Server > properties > image
      -  YES
    * -  Compute
      -  desired\_capacity
      -  tosca.policies.nfv.InstantiationLevels,  tosca.policies.nfv.VduScalingAspectDeltas,  tosca.policies.nfv.VduInitialDelta
      -  N/A
      -  N/A
      -  OS::Heat::AutoScalingGroup > properties > desired\_capacity
      -  NO
    * -  Compute
      -  max\_size
      -  tosca.nodes.nfv.Vdu.Compute
      -  N/A
      -  N/A
      -  OS::Heat::AutoScalingGroup > properties > max\_size
      -  NO
    * -  Compute
      -  min\_size
      -  tosca.nodes.nfv.Vdu.Compute
      -  N/A
      -  N/A
      -  OS::Heat::AutoScalingGroup > properties > min\_size
      -  NO
    * -  Compute
      -  scaling\_adjustment
      -  N/A
      -  addtionalParams
      -  addtionalParams
      -  OS::Heat::ScalingPolicy > properties > scaling\_adjustment
      -  NO
    * -  Network
      -  ext\_network
      -  N/A
      -  extVirtualLinks
      -  extVirtualLinks
      -  OS::Neutron::Port > properties > network
      -  YES
    * -  Network
      -  ext\_subnet
      -  N/A
      -  extVirtualLinks
      -  extVirtualLinks
      -  OS::Neutron::Subnet > properties > name
      -  YES
    * -  Network
      -  ext\_ip\_address
      -  N/A
      -  extVirtualLinks
      -  extVirtualLinks
      -  OS::Neutron::Port > properties > fixed\_ips > ip\_address
      -  YES
    * -  Network
      -  ext\_managed\_network
      -  tosca.nodes.nfv.VnfVirtualLink
      -  extManagedVirtualLinks
      -  extManagedVirtualLinks
      -  OS::Neutron::Port > properties > network
      -  NO
    * -  Network
      -  ext\_managed\_subnet
      -  N/A
      -  addtionalParams
      -  addtionalParams
      -  OS::Neutron::Subnet > properties > name
      -  NO
    * -  Network
      -  ip\_address
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::Port > properties > fixed\_ips > ip\_address
      -  NO
    * -  Network
      -  gateway\_ip
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::Subnet > properties > gateway\_ip
      -  NO
    * -  Network
      -  enable\_dhcp
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::Subnet > properties > enable\_dhcp
      -  NO
    * -  Network
      -  mac\_address
      -  N/A
      -  extVirtualLinks
      -  extVirtualLinks
      -  OS::Neutron::Port > properties > mac\_address
      -  NO
    * -  Network
      -  port\_id
      -  tosca.nodes.nfv.VduCp
      -  extVirtualLinks,  extManagedVirtualLinks
      -  extVirtualLinks,  extManagedVirtualLinks
      -  OS::Neutron::FloatingIP > properties > port\_id
      -  NO
    * -  Network
      -  network\_type
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::ProviderNet > propterties > network\_type,  OS::Neutron::Segment > propterties > network\_type
      -  NO
    * -  Network
      -  binding:vnic\_type
      -  tosca.nodes.nfv.VduCp
      -  N/A
      -  N/A
      -  OS::Neutron::Port > properties > binding:vnic\_type
      -  NO
    * -  Network
      -  max\_kbps
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::QoSBandwidthLimitRule > properties > max\_kbps
      -  NO
    * -  Network
      -  min\_kbps
      -  tosca.nodes.nfv.VnfVirtualLink
      -  N/A
      -  N/A
      -  OS::Neutron::QoSMinimumBandwidthRule > properties > min\_kbps
      -  NO
    * -  Storage
      -  volume\_type
      -  N/A
      -  addtionalParams
      -  addtionalParams
      -  OS::Cinder::Volume > properties > volume\_type
      -  NO
    * -  Storage
      -  volume\_size
      -  tosca.nodes.nfv.Vdu.VirtualBlockStorage
      -  N/A
      -  N/A
      -  OS::Nova::Server > properties > block\_device\_mapping > volume\_size
      -  NO
    * -  placement
      -  server\_availability\_zone
      -  N/A
      -  N/A
      -  zones
      -  OS::Nova::Server > properties > availability\_zone
      -  YES
    * -  placement
      -  volume\_availability\_zone
      -  N/A
      -  addtionalParams
      -  addtionalParams
      -  OS::Cinder::Volume > properties > availability\_zone
      -  NO
    * -  placement
      -  ServerGroup
      -  tosca.policies.nfv.AffinityRule,  tosca.policies.nfv.AntiAffinityRule
      -  N/A
      -  N/A
      -  OS::Nova::ServerGroup > properties > policies
      -  NO
    * -  other parameter
      -
      -  N/A
      -  addtionalParams
      -  N/A
      -  other parameter
      -  NO



To support arbitrary data type, which is not specified in standard VNF Instantiation operation,
Tacker will provide several operations using the additionalParams in InstantiateVnfRequest.

The following describes the example of the input data including additionalParams.

.. note::

   Tacker has already supported additionalParams in InstantiateVnfRequest.
   However, additinalParamas was only used as a flag regarding LCM operation user data.
   This specification will expand the use of additionalParams by allowing setting
   any data defined by consumers.


.. code-block:: json-object

   {
     "flavourId": "flavour_id",
     "instantiationLevelId": "instantiation_level_id",
     "extVirtualLinks": [
       {
         "resourceId": "a77119b7-fcaa-47e5-955d-29f37d5603d4",
         "id": "dc144409-bc93-48b9-be0a-7d737c01a88b",
         "extCps": [
           {
             "cpdId": "CP_0",
             "cpConfig": [
               {
                 "cpProtocolData": [
                   {
                     "layerProtocol": "IP_OVER_ETHERNET",
                     "ipOverEthernet": {
                       "ipAddresses": [
                         {
                           "type": "IPV4",
                           "macAddress": "fa:16:3e:aa:bb:cc",
                           "fixedAddresses": [
                             "192.168.1.1"
                           ]
                         }
                       ]
                     }
                   }
                 ]
               }
             ]
           }
         ]
       }
     ],
     "additionalParams": {
       "lcm-operation-user-data": "./UserData/lcm_user_data.py",
       "lcm-operation-user-data-class": "SampleUserData",
       "Cp1Network": "452e9c2f-a0b4-401e-bdea-5007ce1dfd2b",
       "Cp1IpAddress": "192.168.10.1",
       "Cp1MacAddress": "fa:16:3e:aa:bb:dd"
     }
   }


Tacker will generate the input data mapped to HOT when it calls
create-stack API in Heat.
To address various consumers’ requirements, Tacker will provide three
options to describe HOT and set corresponding additionalParams.
The following data model shows sample HOT and additionalParams for each option.


* Set parameters obtained from additionalParams within the nfv data structure.

  HOT:

  .. code-block:: yaml

   resources:
     VDU_0:
       type: OS::Nova::Server
       properties:
         name: VDU_0
         flavor: { get_param: [ nfv, VDU, VDU_0, flavor ] }
         block_device_mapping_v2: [{ device_name: "vda", volume_id : { get_resource : VDU_0_Storage } }]
         availability_zone: nova
         networks:
           - port: { get_resource: CP_0 }
           - port: { get_resource: CP_1 }

     CP_0:
       type: OS::Neutron::Port
       properties:
         network: { get_param: [ nfv, CP, CP_0, network ] }
         fixed_ips:
           - ip_address: [ nfv, CP, CP_0, fixed_ips, ip_address, 0 ]
         mac_address: { get_param: [ nfv, CP, CP_0, mac_address ] }

     CP_1:
       type: OS::Neutron::Port
       properties:
         network: { get_param : [ nfv, Cp1Network ] }
         fixed_ips:
           - ip_address: { get_param: [ nfv, Cp1IPAddress ] }
         mac_address: { get_param: [ nfv, Cp1MacAddress ] }

     VDU_0_Storage:
       type: OS::Cinder::Volume
       deletion_policy: Delete
       properties:
         name: VDU_0_Storage
         image: { get_param: [ nfv, VDU, VDU_0_Storage, image ] }
         size: 30


  parameters:

  .. code-block:: json-object

   {
     "parameters": {
       "nfv": {
         "VDU": {
           "VDU_0": {"flavor": "VDU_Flavor"},
           "VDU_0_Storage": {"image": "VDU_image"}
         },
         "CP": {
           "CP_0": {
             "network": "a77119b7-fcaa-47e5-955d-29f37d5603d4",
             "mac_address": "fa:16:3e:aa:bb:cc",
             "fixed_ips": [
               {
                 "ip_address": "192.168.1.1"
               }
             ]
           }
         },
         "Cp1Network" : "452e9c2f-a0b4-401e-bdea-5007ce1dfd2b",
         "Cp1IPAddress": "192.168.10.1",
         "Cp1MacAddress": "fa:16:3e:aa:bb:dd"
       }
     }
   }


* Set parameters obtained from additionalParams outside the nfv data structure.

  HOT:

  .. code-block:: yaml

   resources:
     VDU_0:
       type: OS::Nova::Server
       properties:
         name: VDU_0
         flavor: { get_param: [ nfv, VDU, VDU_0, flavor ] }
         block_device_mapping_v2: [{ device_name: "vda", volume_id : { get_resource : VDU_0_Storage } }]
         availability_zone: nova
         networks:
           - port: { get_resource: CP_0 }
           - port: { get_resource: CP_1 }

     CP_0:
       type: OS::Neutron::Port
       properties:
         network: { get_param: [ nfv, CP, CP_0, network ] }
         fixed_ips:
           - ip_address: [ nfv, CP, CP_0, fixed_ips, ip_address, 0 ]
         mac_address: { get_param: [ nfv, CP, CP_0, mac_address ] }

     CP_1:
       type: OS::Neutron::Port
       properties:
         network: { get_param : Cp1Network }
         fixed_ips:
           - ip_address: { get_param: Cp1IPAddress }
         mac_address: { get_param: Cp1MacAddress }

     VDU_0_Storage:
       type: OS::Cinder::Volume
       deletion_policy: Delete
       properties:
         name: VDU_0_Storage
         image: { get_param: [ nfv, VDU, VDU_0_Storage, image ] }
         size: 30


  parameters:

  .. code-block:: json-object

   {
     "parameters": {
       "nfv": {
         "VDU": {
           "VDU_0": {"flavor": "VDU_Flavor"},
           "VDU_0_Storage": {"image": "VDU_image"}
         },
         "CP": {
           "CP_0": {
             "network": "a77119b7-fcaa-47e5-955d-29f37d5603d4",
             "mac_address": "fa:16:3e:aa:bb:cc",
             "fixed_ips": [
               {
                 "ip_address": "192.168.1.1"
               }
             ]
           }
         }
       }
       "Cp1Network" : "452e9c2f-a0b4-401e-bdea-5007ce1dfd2b",
       "Cp1IPAddress": "192.168.10.1",
       "Cp1MacAddress": "fa:16:3e:aa:bb:dd"
     }
   }


* Set all parameters outside the nfv data structure.

  .. note::

      In this option, the nfv data structure is not mandatory for HOT and the input data.


  HOT:

  .. code-block:: yaml

   resources:
     VDU_0:
       type: OS::Nova::Server
       properties:
         name: VDU_0
         flavor: { get_param: nfv_VDU_VDU_0_flavor }
         block_device_mapping_v2: [{ device_name: "vda", volume_id : { get_resource : VDU_0_Storage } }]
         availability_zone: nova
         networks:
           - port: { get_resource: CP_0 }
           - port: { get_resource: CP_1 }

     CP_0:
       type: OS::Neutron::Port
       properties:
         network: { get_param : nfv_CP_CP_0_network }
         fixed_ips:
           - ip_address: { get_param : nfv_CP_CP_0_fixed_ips_ip_address_0 }
         mac_address: { get_param : nfv_CP_CP_0_fixed_ips_ip_mac_address }

     CP_1:
       type: OS::Neutron::Port
       properties:
         network: { get_param : Cp1Network }
         fixed_ips:
           - ip_address: { get_param: Cp1IPAddress }
         mac_address: { get_param: Cp1MacAddress }

     VDU_0_Storage:
       type: OS::Cinder::Volume
       deletion_policy: Delete
       properties:
         name: VDU_0_Storage
         image: { get_param: nfv_VDU_VOU_0_Storage_image }
         size: 30


  parameters:

  .. code-block:: json-object

   {
     "parameters": {
       "nfv_VDU_VDU_0_flavor": "VDU_Flavor",
       "nfv_VDU_VOU_0_Storage_image": "VDU_image",
       "nfv_CP_CP_0_network" : "a77119b7-fcaa-47e5-955d-29f37d5603d4",
       "nfv_CP_CP_0_fixed_ips_ip_address_0": "192.168.1.1",
       "nfv_CP_CP_0_fixed_ips_ip_mac_address": "fa:16:3e:aa:bb:cc",
       "Cp1Network" : "452e9c2f-a0b4-401e-bdea-5007ce1dfd2b",
       "Cp1IPAddress": "192.168.10.1",
       "Cp1MacAddress": "fa:16:3e:aa:bb:dd"
     }
   }


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

* Add new unit and functional tests.
* Add new documents describing SOL014 based VNF package.
* Enhance implementation to support SOL014 based parameters and
  additionalParams in LCM operation user data.


Dependencies
============

None

Testing
========

Unit and functional test cases will be added for VNF Lifecycle Management.

Documentation Impact
====================

New documents describing SOL014 based VNF package
will be added to Tacker User Guide.

References
==========
.. [#Heat_API]
  https://docs.openstack.org/heat/latest/template_guide/openstack.html

.. [#ETSI_SOL014]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/014/03.05.01_60/gs_nfv-sol014v030501p.pdf

.. [#userdata]
  https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/lcm-operation-with-lcm-operation-user-data.html

.. [#ETSI_SOL001]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/03.03.01_60/gs_nfv-sol001v030301p.pdf

.. [#ETSI_SOL003]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf


