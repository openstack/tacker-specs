..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


=========================================
Support multi artifacts of ansible driver
=========================================

https://blueprints.launchpad.net/tacker/+spec/add-ansible-mgmt-driver-sample

We'll be able to use the configuration of multi deployment patterns.

Problem description
===================

The Ansible Driver has only one configuration information for the VDU.
This configuration information is defined in the ``implementation`` key.

.. note::

  ``implementation`` key is defined in TOSCA Simple Profile 3.6.14 [#f1]_.

This parameter cannot have multiple values, it has a single value.
It is executed according to this definition at the start and end of each
VNF lifecycle.

.. code-block:: yaml

  node_templates:
    VNF:
      type: SAMPLE.VNF
      properties:
        flavour_description: 'n-vnf'
        vnfm_info:
          - Tacker
      interfaces:
        Vnflcm:
          instantiate: []
          instantiate_start: []
          instantiate_end:
            implementation: ansible_driver
      ...
      artifacts:
        ansible_driver:
          description: Management driver plugin
          type: tosca.artifacts.Implementation.Python
          file: /opt/stack/tacker/tacker/vnfm/mgmt_drivers/ansible/ansible.py

If we want the different configurations for VNFD of different deployment
flavor, we need to implement the conditional branch within a Driver or
provide the another Driver.
However, these methods increase the specificity of the Driver.

We think of ways to ensure the versatility of Driver and propose the following
change.

Proposed change
===============

The proposed change is to implement the ``primary`` and ``dependencies`` keys
defined by TOSCA.

``primary`` can define the primary script.

``dependencies`` can define a secondary script that it's referenced by the
primary script.

If you implemented this dependency, you would define it as follows :

.. code-block:: yaml

  node_templates:
    VNF:
      type: SAMPLE.VNF
      properties:
        flavour_description: 'n-vnf'
        vnfm_info:
          - Tacker
      interfaces:
        Vnflcm:
          instantiate: []
          instantiate_start:
            implementation:
              primary: ansible_driver
              dependencies:
                - mgmt-drivers-ansible-config-start
          instantiate_end:
            implementation:
              primary: ansible_driver
              dependencies:
                - mgmt-drivers-ansible-config-end
      ...
      artifacts:
        ansible_driver:
          description: Management driver plugin
          type: tosca.artifacts.Implementation.Python
          file: /opt/stack/tacker/tacker/vnfm/mgmt_drivers/ansible/ansible.py
        mgmt-drivers-ansible-config-start:
          description: Management driver config_start.yaml
          type: tosca.artifacts.Implementation.Yaml
          file: ../ScriptAnsible/config_start.yaml
        mgmt-drivers-ansible-config-end:
          description: Management driver config_end.yaml
          type: tosca.artifacts.Implementation.Yaml
          file: ../ScriptAnsible/config_end.yaml

``primary`` defines the script that has run management capabilities,
and ``dependencies`` defines the script that performs the actual injection.
These definitions allow for flexible configuration by the user.

.. note::

  This spec also keep supporting the backward compatibility that single artifact
  format currently used by VNFD.

How to use
----------

The Ansible Driver uses a yaml file.
However, the yaml definition isn't defined in OASIS and cannot be used as it is
by Tacker that refer to definition file of OASIS.
To use the yaml file, we create the following definition file.

example: additional_type.yaml

.. code-block:: yaml

  tosca_definitions_version: tosca_simple_yaml_1_2
  description: yaml types definitions version 0.0.1

  metadata:
    template_name: additional_type
    template_author: ---
    template_version: 0.0.1

  artifact_types:
    tosca.artifacts.Implementation.Yaml:
      derived_from: tosca.artifacts.Implementation
      description: artifacts for Yaml
      mime_type: application/x-yaml
      file_ext: [yaml]

After creation of this file, we put the this file in the ``Definitions`` folder
of VNF Package.

example

.. code-block:: shell

  VNF Package
  |
  +--TOSCA-Metadata
  |  +--TOSCA.meta
  |
  +--Definitions
  |  +--etsi_nfv_sol001_common_types.yaml
  |  +--etsi_nfv_sol001_vnfd_types.yaml
  |  +--helloworld3_df_simple.yaml
  |  +--helloworld3_top.vnfd.yaml
  |  +--helloworld3_types.yaml
  |  +--additional_type.yaml               <<< add file
  |
  +--Files
  |  +--images
  |     +--cirros-0.5.2-x86_64-disk.img
  |
  +--Drivers
  |  +--vnflcm_noop.py
  |
  +--UserData
     +--__init__.py
     +--lcm_user_data.py

The VNFD imports this definition file at imports section.

Also, the VNFD cannot read this definition file simply by storing it.
To be able to read this definition file, we add the following configuration
to the VNFD.

.. code-block:: yaml

  tosca_definitions_version: tosca_simple_yaml_1_2

  description: Simple deployment flavour for Sample VNF

  imports:
    - etsi_nfv_sol001_common_types.yaml
    - etsi_nfv_sol001_vnfd_types.yaml
    - helloworld3_types.yaml
    - additional_type.yaml                  <<< import file

After the bellow settings, you can perform the VNF LCM.

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

Primary assignee:
  Wataru Juso <w-juso@nec.com>

Other contributors:
  Aldinson C. Esto <esto.aln@nec.com>

  Pooja Singla <pooja.singla@india.nec.com>

Work Items
----------
* Enable understanding of primary and dependencies at tosca-parser
* Enable understanding of primary and dependencies at schema of tacker
* Extend method that get implementation information

Dependencies
============
None

Testing
=======
None

Documentation Impact
====================

* Modifying User Documentation of Ansible Driver

References
==========
.. [#f1] https://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.2/os/TOSCA-Simple-Profile-YAML-v1.2-os.html
