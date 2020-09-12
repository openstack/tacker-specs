..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Implement VNF Components Support in Tacker
==========================================

https://blueprints.launchpad.net/tacker/+spec/vnf-components-support

VNF Component (VNFC) is network function software that runs within a virtual
runtime defined in a Virtual Deployment Unit (VDU).

This spec describes the plan to introduce VNF Components (VNFC) capability into Tacker.
In its current state, Tacker requires glance images or image location which has preinstalled
network function to instantiate VDU. But this spec provides the plan to specify VNFC
in VNF descriptors.

Problem description
-------------------

Most of the operators have their own installation procedures to create the VDU.
But when they try to use Tacker as NFV orchestration solution, they have to build
the image first and upload it to glance or provide image location in VNFD.

To address this problem in this spec, we introduce the new feature VNF Component
in tacker.

The benefits of using VNFC are as follows:

* To use vendor specific installation procedures to build network function.
* Loose coupling between image and network function which avoids dependency on the
  underlying image.
* Ability to standardize a minimal, base image (CentOS, Ubuntu) hardened with
  security fixes.
* Easy to update and configure the VDU.


Proposed change
---------------

We have a couple of methods to implement this feature. If we use `heat` as
`vnfc_driver`, then we have a couple of options to opt:

 * Use Cloud-Init option to install software component in VDU. The example
   provided in `Data Model impact` section uses this option. The advantage
   of using this option is, most of the cloud images have cloud-init installed
   But the drawback with this option is upgrade of software component will
   be difficult.

 * Use SoftwareDeployment option to install the software component. But the
   image must have heat agents installed.Refer [1] to see how to install heat
   agents. These agents will invoke heat-api to send the result of software
   deployment.The main advantage of using this option is, we can easily
   upgrade the software component at any point in future.


Alternatives
------------

The other alternative option is using `ssh` as `vnfc_driver`. Using this driver,
tacker will have whole control of managing the software component. But in this
blueprint we implement 'heat' as 'vnfc_driver' and also also discuss how we can
use 'ssh' as vnfc driver.

Using SSH like driver, Tacker has whole control of managing the flow. But the
major concern of using SSH driver is storing the passwords. So to address this
issue, we need to integrate OpenStack Barbican with Tacker.

The limitations of this approach is SSH driver completely relies on network
health and tacker has to depend on barbican for storing passwords for security.


Data model impact
-----------------

None

TOSCA Schema impact
-------------------

In VNFM, the VNFD template will be added with the following TOSCA properties:

.. code-block:: yaml

  firewall_vnfc:
    type: tosca.nodes.nfv.VNFC.Tacker
    properties:
      vnfc_driver: heat
    requirements:
      host: VDU1
    interfaces:
      Standard:
        create: {get_input:file}
        inputs:
              ip_address: { get_attribute: [ HOST, private_address ] }

  VDU1:
    type: tosca.nodes.nfv.VDU.Tacker
    properties:
      image: fedora
      flavor: m1.tiny
      availability_zone: nova
      mgmt_driver: noop

The definition of tosca.nodes.nfv.VNFC.Tacker is defined in the
tacker_nfv_defs.yaml as follows:

.. code-block:: yaml

  tosca.nodes.nfv.VNFC.Tacker:
    derived_from: tosca.nodes.SoftwareComponent
    properties:
       vnfc_driver:
         type: string
         required: true
    requirements:
      - host:
         node: tosca.nodes.nfv.VDU.Tacker
         relationship: tosca.relationships.HostedOn

The above VNFD will convert to the below heat template

.. code-block:: yaml

  VDU1:
    type: OS::Nova::Server
    properties:
      availability_zone: nova
      flavor: m1.tiny
      image: fedora
      user_data_format: SOFTWARE_CONFIG

  firewall_vnfc_config:
    type: OS::Heat::SoftwareConfig
    properties:
      group: script
      config:
        ...(contents of path/vfw_sw/installer/install.sh)
  firewall_vnfc_sw_deployment:
    type: OS::Heat::SoftwareDeployment
    properties:
      config: {get_resource: firewall_vnfc_config}
      server: {get_resource: VDU1}


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


Performance impact
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

This feature will include changes to Tacker server only.

Changes include:

* New definition for VNFC in `tacker_nfv_defs.yaml` to support validation
  of VNFC syntax in tosca-parser.

Assignee(s)
-----------

Primary assignee:
  Bharath Thiruveedula <bharath_ves@hotmail.com>

Other contributors:
  Manikantha Srinivas Tadi <manikantha.tadi@gmail.com>

Work Items
----------

1. Add VNFC definition to `tacker_nfv_defs.yaml`
2. Add parsing logic for VNFC
3. Add unit tests for VNFC template parsing.
4. Add functional test cases.
5. Introduce priority order for the VNFC node in tosca-parser and heat-translator
6. Add devref to document how VNFC works


Dependencies
============

None

Testing
=======

Add functional and unit tests for this functionality.


Documentation Impact
====================

Tacker VNFC user-guide will be provided.

References
==========

[1] https://docs.openstack.org/heat-agents/latest/install/building_image.html
