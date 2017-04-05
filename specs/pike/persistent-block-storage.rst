..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


================================================
Support persistent block storage in Tacker TOSCA
================================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/persistent-block-storage

This spec is to describe a TOSCA template for Cinder volume, and map the
new TOSCA attributes to Heat's Cinder volume.


Problem description
===================

Currently Tacker doesn't have many storage related attributes exposed
in its TOSCA template. VDU disk_size is probably the only thing. We
don't have support for attaching a persistent virtual storage (like
Cinder volume) to Tacker VDU. Sometimes, VDU also needs 'boot from
volume' feature.


Background technology
======================
Now in TOSCA template, it supports creating VDU only with volume size,
not supports booting from volume and specifying whether to delete the
created volumesif the VDU is deleted.

Heat introduction
-----------------
Heat now supports block storage. The usage is below:

1. Create a new block storage volume

.. code-block:: yaml

    resources:
      my_new_volume:
        type: OS::Cinder::Volume
        properties:
          size: 10

2. Create a bootable volume from an existing image

.. code-block:: yaml

    resources:
      my_new_bootable_volume:
        type: OS::Cinder::Volume
        properties:
          size: 10
          image: ubuntu-trusty-x86_64

3. Create new volumes from another existing volume

.. code-block:: yaml

    resources:
      another_volume:
        type: OS::Cinder::Volume
        properties:
          source_volid: 2fff50ab-1a9c-4d45-ae60-1d054d6bc868

4. Create a new volume from another existing volume snapshot

.. code-block:: yaml

    resources:
      another_volume:
        type: OS::Cinder::Volume
        properties:
          snapshot_id: 2fff50ab-1a9c-4d45-ae60-1d054d6bc868

5. Create a new volume from another existing volume backup

.. code-block:: yaml

    resources:
      another_volume:
        type: OS::Cinder::Volume
        properties:
          backup_id: 2fff50ab-1a9c-4d45-ae60-1d054d6bc868

6. Create a new volume, and create an instance with this volume attached

.. code-block:: yaml

    resources:
      new_volume:
        type: OS::Cinder::Volume
        properties:
          size: 1

      new_instance:
        type: OS::Nova::Server
        properties:
          flavor: m1.small
          image: ubuntu-trusty-x86_64

      volume_attachment:
        type: OS::Cinder::VolumeAttachment
        properties:
          volume_id: { get_resource: new_volume }
          instance_uuid: { get_resource: new_instance }

7. Boot an instance from a volume and specify whether to delete the
volume when the instance is deleted

.. code-block:: yaml

    resources:
      bootable_volume:
        type: OS::Cinder::Volume
        properties:
          size: 10
          image: ubuntu-trusty-x86_64

      instance:
        type: OS::Nova::Server
        properties:
          flavor: m1.small
          networks:
            - network: private
          block_device_mapping:
            - device_name: vda
              volume_id: { get_resource: bootable_volume }
              delete_on_termination: false


Proposed change
===============


1. Attaching a volume in TOSCA template
In this case, the instance boot from an image, with a new
created volume attached.

We introduce two new nodes, named VB and CB.
VB defines a block storage, while CB describes the relationship
between VDU and VB. VB will be deleted when the VDU is removed.
One TOSCA template can support multiple VBs and CBs.

.. code-block:: yaml

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU.Tacker
	      properties:
	        image: centos
	        flavor: centos

        CP1:
          type: tosca.nodes.nfv.CP.Tacker
          requirements:
            - virtualLink:
                node: VL1
            - virtualBinding:
                node: VDU1

        VL1:
          type: tosca.nodes.nfv.VL

        VB1:
          type: tosca.nodes.BlockStorage
          properties:
            size: 10 GB

        CB1:
          type: tosca.nodes.BlockStorageAttachment
          properties:
            location: /dev/vdb
          requirements:
            - virtualBinding:
                node: VDU1
            - virtualAttachment:
                node: VB1

2. TOSCA for boot from volume
In this case, the instance boot from a volume.
The volume can be created from many different material, e.g. from a image.

Same with 1, we introduce a node named VB to define a block storage.
In the requirement section of VDU node, we use local_storage to
define the boot volume.
'delete_on_termination' can be configured to determine whether to delete
the volume when VDU deleting.

.. code-block:: yaml

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU.Tacker
	      properties:
	        flavor: centos
          requirements:
            - local_storage:
                node: VB1
                relationship:
                  type: tosca.relationships.AttachesTo
                  location: /dev/vdb
                  delete_on_termination: false

        CP1:
          type: tosca.nodes.nfv.CP.Tacker
          requirements:
            - virtualLink:
                node: VL1
            - virtualBinding:
                node: VDU1

        VL1:
          type: tosca.nodes.nfv.VL

        VB1:
          type: tosca.nodes.BlockStorage
          properties:
            size: 10 GB
            image: ubuntu-trusty-x86_64

3. VDU scaling scenario
A volume can only be attached to one instance in current nova/cinder realization.
In tacker vnf scaling scenario, a VDU may have many instantiated instances.
So in heat, we need create multiple volumes for each instances.
Unfortunately, heat does not support it.

So we should verify the tosca template have no scaling policies when block storage
exists.


Alternatives
------------
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
Primary assignee:
  Zhou Zhihong<zhouzhihong@cmss.chinamobile.com>

Other contributors:
  Yan Xing an<yanxingan@cmss.chinamobile.com>

Work Items
----------
1. Add tosca template samples for block storage
2. Add codes to translate tosca template to HOT
3. UT testcase
4. FT testcase
5. devref doc

Dependencies
============

None

Testing
=======
None


Documentation Impact
====================
None


References
==========

.. [1] http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd01/TOSCA-Simple-Profile-YAML-v1.0-csprd01.html#_Toc430015836
