..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


============================================
TOSCA Parser and Heat Translator Integration
============================================

https://blueprints.launchpad.net/tacker/+spec/tosca-parser-integration


Problem description
===================

Tacker uses a private YAML format for VNFD templates that bears a passing
resemblance to TOSCA but has custom tags and far fewer capabilities. Tacker
also does it's own translation of the VNFD into a Heat template, which
requires maintenance and has far fewer capabilities than other existing
projects.

This spec documents the changes required in Tacker to support using
tosca-parser and heat-translator instead of the existing YAML format
and custom Heat template generator. Tacker will use heat-translator to
create the base HOT template, and will make whatever modifications are
needed to support the rapidly-evolving NFV profile.

Proposed change
===============

There tosca-parser [#]_ and heat-translator [#]_ projects have been updated to
support the TOSCA NFV Profile [#]_. The tosca-parser project has also accepted
a patch to allow it to be used by a server providing a pre-formatted YAML
dictionary instead of a file or URL containing the template.

This spec proposes to add support for TOSCA templates by using the tosca-parser
and heat-translator projects to eventually replace the custom YAML template
and HOT template generation used by Tacker today.

The initial implementation will coexist with the existing Tacker YAML format,
and the interfaces will remain the same. Future work will be required
to separate the TOSCA template processing from the Heat driver and
remove the existing template processing.

Parameters will be handled as they are today. Both tosca-parser and
heat-translator accept parameter inputs to be applied to the resulting
template.

Tacker will support both the tosca_simple_yaml_1_0 and
tosca_simple_profile_for_nfv_1_0_0 profiles in the version field.

Tacker-specific data such as management drivers and monitoring drivers
will be added to the existing NFV object definitions for use in the TOSCA
template. All Tacker extensions will need to be removed from the
translated ToscaTemplate before it is passed to the ToscaTranslator for
conversion to HOT.

The tacker_defs.yaml file will define Tacker-specific types that are
not specific to NFV profile types. The tacker_nfv_defs.yaml file will
define Tacker-specific NFV types. These files will be
automatically added as an import to all VNFDs when they are created, based
on the version of the template. The imports must be added by the Tacker
server in order to be able to specify the full path to the import file.


Sample tacker_defs.yaml
-----------------------
::

  data_types:
    tosca.datatypes.tacker.Monitoring.ActionMap:
      properties:
        trigger:
          type: string
          required: true
        action:
          type: string
          required: true
        params:
          type: map
          entry_schema:
            type: string

    tosca.datatypes.tacker.Monitoring.Mechanism:
      properties:
        name:
          type: string
          required: true
        actions:
          type: list
          entry_schema:
            type: tosca.datatypes.tacker.ActionMap
        parameters:
          type: map
          entry_schema:
            type: string

  policy_types:
    tosca.policies.tacker.Placement:
      derived_from: tosca.policies.Root

    tosca.policies.tacker.Monitoring:
      derived_from: tosca.policies.Root
      monitoring_params:
        type: map
        entry_schema:
          type: string

    tosca.policies.tacker.Monitoring.Failure:
      derived_from: tosca.policies.tacker.Monitoring
      action:
        type: string

    tosca.policies.tacker.Monitoring.Failure.Respawn:
      derived_from: tosca.policies.tacker.Monitoring.Failure
      action: respawn

    tosca.policies.tacker.Monitoring.Failure.Terminate:
      derived_from: tosca.policies.tacker.Monitoring.Failure
      action: log_and_kill

    tosca.policies.tacker.Monitoring.Failure.Log:
      derived_from: tosca.policies.tacker.Monitoring.Failure
      action: log

    tosca.policies.tacker.Monitoring.NoOp:
      derived_from: tosca.policies.tacker.Monitoring

    tosca.policies.tacker.Monitoring.Ping:
      derived_from: tosca.policies.tacker.Monitoring
      monitoring_params:
        count: 3
        interval: 5

    tosca.policies.tacker.Monitoring.HttpPing:
      derived_from: tosca.policies.tacker.Monitoring.Ping

  group_types:
    tosca.groups.tacker.VDU:
      derived_from: tosca.groups.Root

Sample tacker_nfv_defs.yaml
---------------------------
::

  node_types:
    tosca.nodes.nfv.VDU.Tacker:
      derived_from: tosca.nodes.nfv.VDU
      properties:
        image:
          type: string
        flavor:
          type: string
        availability_zone:
          type: string
        metadata:
          type: map
          entry_schema:
            type: string
        config_drive:
          type: boolean
          default: false

        placement_policy:
          type: string

        monitoring_policy:
          type: tosca.datatypes.tacker.MonitoringMechanism

        config:
          type: string

        mgmt_driver:
          type: string

        service_type:
          type: string

    tosca.nodes.nfv.CP.Tacker:
      derived_from: tosca.nodes.nfv.CP
      properties:
        management:
          type: boolean
          required: false
          default: false
        anti_spoofing_protection:
          type: boolean
          required: false

Alternatives
------------

Tacker could continue to maintain it's own YAML format and HOT template
generation but this will put significant limitations on future capabilities.

Data model impact
-----------------

Initial support for tosca-parser/heat-translator will have no data model
impact. Future changes may be required to add the ability to specify
multiple different management drivers for different VDUs, and to handle
CSAR files.

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

User will need to use TOSCA templates to take advantage of this capability

Performance Impact
------------------

Using tosca-parser and heat-translator will use more cycles than the
home-grown solution, but the additional capabilities provided more
than make up for the small increase in processing time.

Other deployer impact
---------------------

The plan is to support the existing YAML format and TOSCA together through
the Mitaka cycle. The existing YAML format will be deprecated in Mitaka
and removed in Newton.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  bob-haddleton

Work Items
----------

- Develop tacker_defs.yaml file to extend the existing TOSCA NFV node
  definitions with the properties required by Tacker. File to be stored
  in tacker/vm/tosca/lib

- Create module tacker.vm.tosca.utils to provide utility methods to manipulate
  the TOSCA template as needed

- Modify the existing heat driver create_device_template_pre() method to
  detect a TOSCA template and invoke tosca-parser (ToscaTemplate) to
  pre-process the template for any syntax errors and store the resulting
  data in the database.

- Modify the existing heat driver create() method to detect a TOSCA template
  and invoke tosca-parser (ToscaTemplate) and heat-translator (TOSCATranslator)
  to generate the HOT template. The generated ToscaTemplate will need to be
  processed to remove the Tacker-specific nodes and properties before it
  can be processed by TOSCATranslator to generate the HOT template.


Dependencies
============

- tosca-parser 0.4.0 release is required for this feature

- heat-translator 0.4.0 release is required for this feature

Testing
=======

Existing tests for the heat driver will be expanded to include support for
testing the create_device_template_pre() method and the create() method
with TOSCA template inputs to ensure that the feature works as expected.

Documentation Impact
====================

Documentation of the Tacker-specific extensions to the NFV Profile as defined
by tacker_defs.yaml will be needed, and sample TOSCA templates will need to be
provided. Devstack sample templates will also be needed.

References
==========
.. [#] https://blueprints.launchpad.net/tosca-parser/+spec/tosca-nfv-support
.. [#] https://blueprints.launchpad.net/heat-translator/+spec/tosca-nfv-support
.. [#] TOSCA Simple Profile for Network Functions - http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.html
