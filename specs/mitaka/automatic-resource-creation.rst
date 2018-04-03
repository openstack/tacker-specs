..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================================================
Automatic openstack resource creation based on VNFD template
============================================================

https://blueprints.launchpad.net/tacker/+spec/automatic-resource-creation

Creating the custom openstack resources like flavors/networks/image is one
of the requirement from the VNF vendors. This blueprint proposes to add the
support for automatic resource creation while onboarding the VNFD/ creating
the VNF in tacker.

Problem description
===================

With the current version of tacker, telco operators have to create the openstack
resources before creating VNF. And VNF vendors cannot add the VDU details in the
VNFD. For example VNF vendors cannot specify:

1)The VM details of the VDU like cpu, memory and disk etc.,
2)The network details for the VDU like cidr, network_type etc.,
3)The image details which is not present in glance.

Proposed Change
===============

Introducing new host properties in VNFD template will give an initial pointer
to provide the solution for the tacker. This spec will address the automatic
creation of flavor, network and image.

Automatic Flavor Creation
--------------------------

Template Changes
~~~~~~~~~~~~~~~~

.. code-block:: ini

  topology_template:
     node_templates:
         my_server:
             type: tosca.nodes.Compute
              capabilities:
                 host:
                     properties:
                         num_cpus: 2
                         disk_size: 10 GB
                         mem_size: 512 MB

When the user give host properties, Tacker will create a new flavor with those
details by adding those details in heat template. Tacker will handle three
minimum host properties like 'disk_size' and 'num_cpus' and 'mem_size'.
To refer the other properties, refer [#]_.

Tacker will fetch the properties from TOSCA template and add them to HOT
as below:

.. code-block:: ini

    heat_template_version: 2015-04-30
     resources:
         my_server_flavor_<UUID>:
             type: OS::Nova::Flavor
              properties:
                 disk: 10
                 ram: 512
                 vcpus: 2

As 'vcpus' and 'ram' are required parameters in HOT, so if the template doesn't have
those details, Tacker will provide default values(vcpus=1 and ram=512).


Automatic Image Creation
------------------------

Template Changes
~~~~~~~~~~~~~~~~

.. code-block:: ini

  vdu1:
    artifacts:
     vm_image:
        type: tosca.artifacts.Deployment.Image.VM
        file: http://URL/vRouterVNF.qcow2

In the modified template, users can either specify the URL for the VM image or
glance image name in `file` type. Tacker will create the image if URL is specified
in the `file` parameter.

In this case, we can have three options to automatically create and upload the image:

1). Specify the image URI in the template and no parameterization

If we choose this option, we can't parameterize the `vm_image`. And tackers upload the image
while onboarding the VNFD using glance client. It is one step process. With this option,
we have to maintain the state of the VNFD based on image creation.

2). Provide the image in CSAR Zip.

Using this option, we have to ship the bundle with image needed for that VNFD. So Tacker will
upload the image at onboarding time. With this option, we have to maintain the state
of the VNFD based on image creation.

3). Provide parameterization and upload images at the time of VNF creation.

Here we can parameterize the `vm_image` attribute. With this option Tacker will upload the image into
glance at VNF deployment time using HOT template.

Let's take an example of how TOSCA image artifact can be converted to HOT image resource.

TOSCA:

.. code-block:: ini

    artifacts:
      vm_image:
        type: tosca.artifacts.Deployment.Image.VM.qcow2
        file: http://filer/vnfimages/vrouter.qcow2

Heat:

.. code-block:: ini

  image:
    type: OS::Glance::Image
     properties:
      container_format: bare
      disk_format: qcow2
      location: http://filer/vnfimages/vrouter.qcow2

We can remove statefulness of VNFD with this option.

In this spec, we prefer the third option.

Automatic Network Creation
--------------------------

Template Changes
~~~~~~~~~~~~~~~~

.. code-block:: ini

    internal_datapath:
        type: tosca.nodes.nfv.VL.ELAN
        network_name: net_internal_dp
        ip_version: 4
        cidr: '192.168.0.0/24'
        start_ip: '192.168.0.50'
        end_ip: '192.168.0.200'
        gateway_ip: '192.168.0.1'

In this modified template, users can specify the CIDR of the network, they want
to deploy VNF. If the user specify the CIDR and not the network_id, tacker will
automatically create network and corresponding subnet. Refer [#]_ for the
properties the tacker will support in network_interfaces. For the networks, tacker
will create the network resources at VNF creation time using heat code. So we are not
storing the network details as network resources are associated with heat stack details.

Let's see how the above TOSCA template can be converted to HOT network resource.

.. code-block:: ini

    net_internal_dp:
            type: OS::Neutron::Net
            properties:
              name: net_internal_dp

    net_internal_dp_subnet:
            type: OS::Neutron::Subnet
            properties:
              network_id: { get_resource: private_net }
              cidr: 192.168.0.0/24
              gateway_ip: 192.168.0.1
              allocation_pools: [{"end": "192.168.0.200", "start": "192.168.0.50"}]

Data model impact
-----------------

Flavors, networks and images will be created while deploying VNF, and will be removed automatically
by heat at the deletion VNF. So there won't be any change in data model.

REST API impact
---------------

None

Other end user impact
---------------------

User can use TOSCA templates in addition to Tacker defined templates after this spec.

Note:
Auto image upload is not suitable for VNFs that would get instantiated multiple times.
It will cause the same glance image to be uploaded multiple times.

Implementation
==============

Assignee(s)
-----------

Primary assignee:

- Bharath Thiruveedula (bharath-ves)

Other contributors:
  None

Work Items
----------

* Modify the calls of VNF create, so that VNF operations will be handled by
  plugin.

Dependencies
============

None

Testing
=======

This Blueprint provides unit test cases for each of the deliverables.

Documentation Impact
====================

devref will be modified by providing the instructions on how to adapt the new
template changes.


References
==========

.. [#] `<http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/TOSCA-Simple-Profile-YAML-v1.0.html>`_
.. [#] `<http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd01/TOSCA-Simple-Profile-YAML-v1.0-csprd01.html#_Toc430015804>`_
