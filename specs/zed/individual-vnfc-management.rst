..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===========================================
Support individual VNFC management via Heat
===========================================

.. Blueprints:

https://blueprints.launchpad.net/tacker/+spec/individual-vnfc-management

This specification proposes new functionality about
individual VNFC management via OpenStack Heat.
This proposal focuses on v2 VNF Lifecycle management (LCM) API
and adds new sample BaseHOT, corresponding UserData script,
and utility functions for UserData class [#Tacker-userdata_script]_.

Problem description
===================

ETSI NFV SOL002 v3.3.1 [#NFV-SOL002_331]_ and
SOL003 v3.3.1 [#NFV-SOL003_331]_
define an element called VNF Component (VNFC).
VNFC is a unit of a virtual computer such as VM and Pod,
and VNF is composed of one or more VNFC.
Tacker's VNF LCM API has supported
the VNF instances consisting of multiple VNFCs
by using the AutoScalingGroup [#OpenStack_Resource_Types_AutoScalingGroup]_
provided by OpenStack Heat.

Following shows the sample BaseHOT with AutoScalingGroup.

* top HOT

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: 'Simple Base HOT for Sample VNF'

    parameters:
      nfv:
        type: json

    resources:
      VDU1_scale_group:
        type: OS::Heat::AutoScalingGroup
        properties:
          min_size: 1
          max_size: 3
          desired_capacity: { get_param: [ nfv, VDU, VDU1, desired_capacity ] }
          resource:
            type: VDU1.yaml
            properties:
              name: {get_param: [ nfv, VDU, VDU1, computeName ] }
              flavor: { get_param: [ nfv, VDU, VDU1, computeFlavourId ] }
              image: { get_param: [ nfv, VDU, VDU1, vcImageId ] }
              zone: { get_param: [ nfv, VDU, VDU1, locationConstraints] }
              net: { get_param: [ nfv, CP, VDU1_CP1, network] }

* nested HOT (VDU1.yaml specified in above top HOT)

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: 'VDU1 HOT for Sample VNF'

    parameters:
      name:
        type: string
      flavor:
        type: string
      image:
        type: string
      zone:
        type: string
      net:
        type: string

    resources:
      VDU1:
        type: OS::Nova::Server
        properties:
          name: { get_param: name }
          flavor: { get_param: flavor }
          image: { get_param: image }
          networks:
          - port:
              get_resource: VDU1_CP1

          availability_zone: { get_param: zone }

      VDU1_CP1:
        type: OS::Neutron::Port
        properties:
          network: { get_param: net }


HEAT API (stack create, stack update, etc.) generates
as many resources (VNFCs) as the "desired_capacity".
Since properties are applied to all VNFCs uniformly,
individual settings and updates cannot be made to individual VNFC.

It causes following two problems.

1. Service interruption by re-creating all VNFCs
------------------------------------------------

AutoScalingGroup causes the service interruption in
"VNF software modification not assisted by NFV-MANO"
described in ETSI NFV IFA007 v3.6.1 B.2 [#NFV-IFA007_361]_.

In this scenario, after directly updating the VM's configuration
from a component outside MANO,
Modify operation updates the VNF Instance's information
in VNFM for subsequent LCM integrity.
Then subsequent Scale or Heal operation creates resources
with the new image and
re-create all VNFCs created by AutoScalingGroup simultaneously
even if they are not scale-out targets or heal targets.
This causes service interruption, which is unacceptable on commercial systems.
Details of this problem can be found in the Proposed change chapter.

.. note:: Tacker has supported
   "VNF software modification assisted by NFV MANO
   via change of current VNF Package"
   described in IFA007 v3.6.1 B.3 [#NFV-IFA007_361]_
   by the rolling update operation of ChangeCurrentVNFPackage API.

2. Restriction for anti-affinity between VNFCs
----------------------------------------------

When "ZONE" is specified as ``PlacementConstraint.scope``
and VNFM obtains the zone from NFVO,
AutoScalingGroup applies it to all VNFCs.
That is, all VNFCs are deployed on the same zone
even if anti-affinity is specified by VNFD or Grant.
This behavior violates the standard specification.

Proposed change
===============

change of the sequence
----------------------

This proposal changes the sequence of software update as follows.

Sequence before changing
^^^^^^^^^^^^^^^^^^^^^^^^

The following sequence omits the notification process.

.. seqdiag::

  seqdiag {
      node_width = 80;
      edge_length = 100;

    EM; Client; NFVO; "Tacker common process"; "Tacker UserData script";
    Heat; VDU1-VNFC1; VDU1-VNFC2;

    === Instantiate VNF ===

    "Client" -> "Tacker common process"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/instantiate"];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];
    "Tacker common process" ->> "Tacker common process"
      [label = "calculate the number of VMs"];
    "NFVO" <- "Tacker common process" [label = "POST /grants"];
    "NFVO" --> "Tacker common process"
      [label = "201 Created with OpenStack Glance imageid"];
    "Tacker common process" -> "Tacker UserData script"
      [label = "request, instance, grantRequest, grant, tmp_csar_dir"];
    "Tacker common process" <-- "Tacker UserData script"
      [label = "HOT and corresponding input-parameter including desired_capacity"];
    "Tacker common process" -> "Heat"
      [label = "POST /v1/{tenant_id}/stacks --parameter
       imageid=<original imageid>; desired_capacity=1"];
    "Heat" -> "VDU1-VNFC1" [label = "create VM"];
    "Heat" <-- "VDU1-VNFC1" [label = ""];
    "Tacker common process" <-- "Heat" [label = ""];

    === Update internal configuration on VNFC ===

    "EM" -> "VDU1-VNFC1" [label = "update the internal configuration"];
    "EM" <-- "VDU1-VNFC1" [label = ""];

    === Modify the VNF Instance's information in Tacker DB ===

    "Client" -> "Tacker common process"
     [label = "PATCH vnflcm/v2/vnf_instances/{vnfInstanceId}"];
    "Tacker common process" -> "Tacker common process"
      [label = "change vnfdid of the vnfInstance.
       new vnfd includes identifier of the new image."];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];

    === Scale-out the VNF ===

    "Client" -> "Tacker common process"
      [label = "/vnflcm/v2/vnf_instances/{vnfInstanceId}/scale"];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];
    "NFVO" <- "Tacker common process" [label = "POST /grants"];
    "NFVO" --> "Tacker common process"
      [label = "201 Created with new OpenStack Glance imageid"];
    "Tacker common process" -> "Tacker UserData script"
      [label = "request, instance, grantRequest, grant, tmp_csar_dir"];
    "Tacker UserData script" -> "Tacker UserData script"
      [label = "calculate the number of VMs"];
    "Tacker common process" <-- "Tacker UserData script"
      [label = "HOT and corresponding input-paramaeter including desired_capacity"];
    "Tacker common process" -> "Heat"
      [label = "PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id}
       --existing --parameter imageid=<new imageid>; desired_capacity=2"];
    "Heat" -> "VDU1-VNFC1" [label = "re-create VM"];
    "Heat" <--  "VDU1-VNFC1" [label = ""];
    "Heat" -> "VDU1-VNFC2" [label = "create VM"];
    "Heat" <-- "VDU1-VNFC2" [label = ""];
    "Tacker common process" <-- "Heat" [label = ""];
  }


The procedure consists of the following steps as illustrated in above sequence:

Instantiate VNF

#. Client sends Tacker common process a POST request
   for the Instantiate VNF Instance.
#. The number of VMs is calculated by multiplying
   "instantiationLevelId" described in InstantiateVnfRequest
   and "number_of_instances" described in the VNFD.
#. Tacker common process and NFVO exchange granting information.
#. Tacker UserData script makes HOT and corresponding input-parameters.
#. Tacker common process sends Heat stack-create request with
   the "Glance imageid" and "desired_capacity" of AutoScalingGroup.
#. Heat creates VNFC1 belonging to VDU1.

Update internal configuration on VNFC and
the VNF Instance's information in Tacker DB

#. Element Manager (EM) updates the internal configuration on VNFC1
   by accessing the guest OS.
#. Client sends Tacker common process a PATCH request
   for the Modify VNF Information.
#. Tacker common process updates vnfdid of the VNF Instance.
   The identifiers of the new software image
   having updated configuration are described in the new VNFD.

Scale-out the VNF

#. Client sends Tacker common process a POST request
   for the Scale-out VNF Instance.
#. The number of VMs is calculated by multiplying
   "number_of_steps" described in Scale VNF request
   and "number_of_instances" described in the VNFD.
#. Tacker common process and NFVO exchange granting information.
   Grant from NFVO contains the new Glance imageid for VNFC.
#. Tacker UserData script makes HOT and corresponding input-parameters.
#. Tacker common process sends Heat stack-update request with
   the "Glance imageid" and "desired_capacity" of AutoScalingGroup.
#. Heat re-creates VNFC1 using the new software image.
#. Heat creates VNFC2 using the new software image.


Sequence after changing
^^^^^^^^^^^^^^^^^^^^^^^

The following sequence omits the notification process.

Changes are highlighted in red boxes.

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    EM; Client; NFVO; "Tacker common process"; "Tacker UserData script";
    Heat; VDU1-VNFC1; VDU1-VNFC2;

    === Instantiate VNF ===

    "Client" -> "Tacker common process"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/instantiate"];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];
    "Tacker common process" ->> "Tacker common process"
      [label = "calculate the number of VMs"];
    "NFVO" <- "Tacker common process" [label = "POST /grants"];
    "NFVO" --> "Tacker common process"
      [label = "201 Created with OpenStack Glance imageid"];
    "Tacker common process" -> "Tacker UserData script"
      [label = "request, instance, grantRequest, grant, tmp_csar_dir"];
    "Tacker common process" <-- "Tacker UserData script"
      [label = "adjusted HOT and corresponding input-parameter",
       leftnote = "Tacker UserData script makes adjusted HOT"];
    "Tacker common process" -> "Heat"
      [label = "POST /v1/{tenant_id}/stacks --parameter imageid=<original imageid>"];
    "Heat" -> "VDU1-VNFC1" [label = "create VM"];
    "Heat" <-- "VDU1-VNFC1" [label = ""];
    "Tacker common process" <-- "Heat" [label = ""];

    === Update internal configuration on VNFC ===

    "EM" -> "VDU1-VNFC1" [label = "update the internal configuration"];
    "EM" <-- "VDU1-VNFC1" [label = ""];

    === Modify the VNF Instance's information in Tacker DB ===

    "Client" -> "Tacker common process"
     [label = "PATCH vnflcm/v2/vnf_instances/{vnfInstanceId}"];
    "Tacker common process" -> "Tacker common process"
      [label = "change vnfdid of the vnfInstance.
       new vnfd includes identifier of the new image."];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];

    === Scale-out the VNF ===

    "Client" -> "Tacker common process"
      [label = "/vnflcm/v2/vnf_instances/{vnfInstanceId}/scale"];
    "Client" <-- "Tacker common process" [label = "Response 202 Accepted"];
    "NFVO" <- "Tacker common process" [label = "POST /grants"];
    "NFVO" --> "Tacker common process"
      [label = "201 Created with new OpenStack Glance imageid"];
    "Tacker common process" -> "Tacker UserData script"
      [label = "request, instance, grantRequest, grant, tmp_csar_dir"];
    "Tacker UserData script" -> "Tacker UserData script"
      [label = "calculate the number of VMs"];
    "Tacker common process" <-- "Tacker UserData script"
      [label = "adjusted HOT and corresponding input-parameter",
       leftnote = "Tacker UserData script makes adjusted HOT"];
    "Tacker common process" -> "Heat"
      [label = "PATCH /v1/{tenant_id}/stacks/{stack_name}/{stack_id}
       --existing --parameter imageid=<new imageid>"];
    "Heat" -> "VDU1-VNFC2" [label = "create VM"];
    "Heat" <-- "VDU1-VNFC2" [label = ""];
    "Tacker common process" <-- "Heat" [label = ""];
  }


The procedure consists of the following steps as illustrated in above sequence:

Instantiate VNF

#. Client sends Tacker common process a POST request
   for the Instantiate VNF Instance.
#. The number of VMs is calculated by multiplying
   "instantiationLevelId" described in InstantiateVnfRequest
   and "number_of_instances" described in VNFD.
#. Tacker common process and NFVO exchange granting information.
#. Tacker UserData script makes adjusted HOT and corresponding input-parameters.
#. Tacker common process sends Heat stack-create request
   with the "Glance imageid".
#. Heat creates VNFC1 belonging to VDU1.

Update internal configuration on VNFC
and the VNF Instance's information in Tacker DB

#. Element Manager (EM) updates the internal configuration on VNFC1
   by accessing the guest OS.
#. Client sends Tacker common process a PATCH request for the Modify VNF Information.
#. Tacker common process updates vnfdid of the VNF Instance.
   The identifiers of the new software image
   having updated configuration are described in the new VNFD.

Scale-out the VNF

#. Client sends Tacker common process a POST request
   for the Scale-out VNF Instance.
#. The number of VMs is calculated by multiplying
   "number_of_steps" described in Scale VNF request
   and "number_of_instances" described in VNFD.
#. Tacker common process and NFVO exchange granting information.
   grant from NFVO contains new Glance imageid for VNFC.
#. Tacker UserData script makes adjusted HOT and
   corresponding input-parameters.
#. Tacker common process sends Heat stack-update request
   with the "Glance imageid" to target VNFC.
#. Heat creates VNFC2 belonging to VDU1.


Adjusted HOT
------------

Tacker's UserData script generates adjusted HOT from BaseHOT.
Individual VNFC definitions are described in adjusted HOT,
and individual input-parameters for them can be specified.
Therefore, Tacker can manage individual VNFC by using adjusted HOT.
For example, Tacker can change the software image of only heal target VNFC.
Also, Tacker can specify the different availability zone for each VNFC.

Since the proposed change does not affect Tacker-common process,
Tacker can support both BaseHOT with AutoScalingGroup
and BaseHOT without AutoScalingGroup.

BaseHOT
^^^^^^^

* top HOT

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
          name: { get_param: [ nfv, VDU, VDU1, computeName ] }
          flavor: { get_param: [ nfv, VDU, VDU1, computeFlavourId ] }
          image: { get_param: [ nfv, VDU, VDU1, vcImageId ] }
          zone: { get_param: [ nfv, VDU, VDU1, locationConstraints] }
          net: { get_param: [ nfv, CP, VDU1_CP1, network] }

* nested HOT (VDU1.yaml specified in above top HOT)

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: 'VDU1 HOT for Sample VNF'

    parameters:
      name:
        type: string
      flavor:
        type: string
      image:
        type: string
      zone:
        type: string
      net:
        type: string

    resources:
      VDU1:
        type: OS::Nova::Server
        properties:
          name: { get_param: name }
          flavor: { get_param: flavor }
          image: { get_param: image }
          networks:
          - port:
              get_resource: VDU1_CP1

          availability_zone: { get_param: zone }

      VDU1_CP1:
        type: OS::Neutron::Port
        properties:
          network: { get_param: net }

* Input-parameter

  .. code-block:: json

    "nfv": {
      "VDU": {
        "VDU1": {
          "computeName": "VDU1",
          "computeFlavourId": "m1.tiny",
          "vcImageId": "6b8a14f0-1b40-418a-b650-ae4a0378daa5",
          "locationConstraints": "zone-x"
        }
      },
      "CP": {
        "VDU1_CP1": {
          "network": "67c837dc-c247-4a3e-ac0f-5603bfef1ba3"
        }
      }
    }

Adjusted HOT
^^^^^^^^^^^^

* top HOT

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    description: Test Base HOT

    parameters:
      nfv:
        type: json

    resources:
      VDU1-0:
        type: VDU1.yaml
        properties:
          name: { get_param: [ nfv, VDU, VDU1-0, computeName ] }
          flavor: { get_param: [ nfv, VDU, VDU1-0, computeFlavourId ] }
          image: { get_param: [ nfv, VDU, VDU1-0, vcImageId ] }
          zone: { get_param: [ nfv, VDU, VDU1-0, locationConstraints ] }
          net: { get_param: [ nfv, CP, VDU1_CP1-0, network ] }
      VDU1-1:
        type: VDU1.yaml
        properties:
          name: { get_param: [ nfv, VDU, VDU1-1, computeName ] }
          flavor: { get_param: [ nfv, VDU,VDU1-1, computeFlavourId ] }
          image: { get_param: [ nfv, VDU,VDU1-1, vcImageId ] }
          zone: { get_param: [ nfv, VDU,VDU1-1, locationConstraints ] }
          net: { get_param: [ nfv, CP, VDU1_CP1-1,network ] }

* nested HOT

  Only the top HOT is changed to the adjusted HOT.
  Nested HOT is unchanged from BaseHOT.

* Input-parameter

  .. code-block:: json

    "nfv": {
      "VDU": {
        "VDU1-0": {
          "computeName": "VDU1-0",
          "computeFlavourId": "m1.tiny",
          "vcImageId": "6b8a14f0-1b40-418a-b650-ae4a0378daa5",
          "locationConstraints": "zone-x"
        },
        "VDU1-1": {
          "computeName": "VDU1-1",
          "computeFlavourId": "m1.large",
          "vcImageId": "0ef0597c-4aab-4235-8513-bf5d8304fe64",
          "locationConstraints": "zone-y"
        }
      },
      "CP": {
        "VDU1_CP1-0": {
          "network": "67c837dc-c247-4a3e-ac0f-5603bfef1ba3"
        },
        "VDU1_CP1-1": {
          "network": "4d8aa289-21eb-4997-86f2-49a884f78d0b"
        }
      }
    }

Following is the requirements of UserData script.

* UserData script calculates the number of VNFCs on the basis of
  the number of ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo``,
  ``Grant.addResources``, and ``Grant.removeResources``
  similar to the method of calculating desired_capacity.
  `get_param_capacity` [#userdata_get_param_capacity]_
  , which is one of utility functions
  for UserData class can be used to get the number of resources.

* UserData script describes the same number of resources
  as VNFC to adjusted HOT.

  * UserData scripts create the resource id of VNFC (e.g. VDU1-0, VDU-1-1).
  * Properties of resources are copied from BaseHOT.

* UserData script makes the input-parameter corresponding to Adjusted HOT.

.. note::
  There is a difference in scale-in operation with and without AutoScalingGroup.
  Basically, VNFCs are deleted in order from the latest in scale-in operation.
  In the case of using AutoScalingGroup, the latest resource is determined
  on the basis of the `creation_time` by OpenStack Nova.
  Since `creation_time` is updated by heal operation,
  the order of VNFCs is changed dynamically.
  On the other hand, in the case of the not using AutoScalingGroup,
  the latest resource is determined by the resource-id (e.g. VDU1-0, VDU1-1).
  Thus the order of the VNFc is not changed by heal operation when not using
  AutoScalingGroup.

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

* Add new VNF package containing new BaseHOT and new UserData scripts.
* Add new functional tests.
* Add new utility functions making adjusted HOT.


Dependencies
============

None

Testing
========

Functional test cases will be added for Instantiate and Scale VNF.


Documentation Impact
====================

New utility functions for UserData class will be described
in UserData script manual.

References
==========
.. [#Tacker-userdata_script]
  https://docs.openstack.org/tacker/latest/user/userdata_script.html
.. [#NFV-SOL002_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_nfv-sol002v030301p.pdf
.. [#NFV-SOL003_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
.. [#OpenStack_Resource_Types_AutoScalingGroup]
  https://docs.openstack.org/heat/latest/template_guide/openstack.html#OS::Heat::AutoScalingGroup
.. [#NFV-IFA007_361]
  https://docbox.etsi.org/ISG/NFV/Open/Publications_pdf/Specs-Reports/NFV-IFA%20007v3.6.1%20-%20GS%20-%20Or-Vnfm%20ref%20point%20Spec.pdf
.. [#userdata_get_param_capacity] https://docs.openstack.org/tacker/latest/user/userdata_script.html#def-get-param-capacity-vdu-name-inst-grant-req
