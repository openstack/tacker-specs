..
   This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

====================================================================
Support event trigger alarm and vdu_autoheal by alarming type policy
====================================================================

This proposal aims at supporting vdu_autoheal by VDU state change event.

Problem description
===================

Currently Tacker support vdu_autoheal triggered by monitoring such as ping.
However, there are some systems which require healing triggered by events
such as resource's state change.
One use case is healing due to a hardware fault, and fault management
scenarios are discussed in NFV.
(example:OPNFV doctor's Fault management scenario [#f1]_)

In this case, healing should be triggered by VDU status change,
but it cannot be achieved with current Tacker.

Proposed change
===============

Our plan is to add a new policy ``tosca.policies.tacker.EventAlarming``
and enable vdu_autoheal by event alarming trigger.
New policy define monitoring resource state to evaluate the resource's event
and call action.

The overall workflow is as follow:

::

 +----------------------------+                      +---------------------------------------+
 |            Aodh            |                      | Tosca_alarm_template.yaml             |
 |                            |                      | (tosca.policies.tacker.EventAlarming) |
 |    +------------------+    | (Create              +--------------+------------------------+
 |    |                  |    |  EvantAlarm)                        |
 |    |    Alarm API     |<---|------------+                        |
 |    |                  |    |            |  +---------------------v-------------------------+
 |    +------------------+    |            |  |                    Tacker                     |
 |                            |            |  |                                               |
 |                            |            |  |   +---------------------------------------+   |
 |    +------------------+    |            |  |   |                   VNFM                |   |
 |    |                  |    |            |  |   |                                       |   |
 |    |    Alarm         |    |            |  |   |            +---------------+          |   |
 |    |    Evaluator     |    |            +--|---|------------|               |          |   |
 |    |    / Notifier    |    |               |   |            | Alarm Monitor |          |   |
 |    |                  |----|---------------|---|----------->|               |          |   |
 |    +------^-^----^----+    |               |   |            +---------------+          |   |
 |           | |    |         |               |   |                                       |   |
 |           | |    |         |               |   |                                       |   |
 |           | |    |         |               |   +---------------------------------------+   |
 +----------------------------+               +-----------------------------------------------+
             | |    |
             | |    |
 +------------------------------------------------+
 |     Notification bus                           |
 +------------------------------------------------+
             | |    |
             | |    | (Event Norification)
             | |    |
 +------------------------------------------------+
 |     OpenStack Services                         |
 |     (Nova, Neutron, Cinder, ...)               |
 |                                                |
 +-----------^-^----^-----------------------------+
             | |    |
             | |    |
             | |    |
             | |    +-----------------------------------+
             | +-------------------+                    |
             |                     |                    |
             |                     |                    |
 +-----------v------------------------------------------------------------------------------+
 |                                 |            NFVI    |                                   |
 | +--------------------------------------------------------------------------------------+ |
 | |                               |            VNF     |                                 | |
 | | +-----------------------------v---------+  +-------v-------------------------------+ | |
 | | |                VDU                    |  |                    VDU                | | |
 | | |                                       |  |                                       | | |
 | | +---------------------------------------+  +---------------------------------------+ | |
 | +--------------------------------------------------------------------------------------+ |
 +------------------------------------------------------------------------------------------+


1. Add policy ``tosca.policies.tacker.EventAlarming``

Add a new alarm monitoring policy ``tosca.policies.tacker.EventAlarming``
into VNFD definition.
This policy is translated to event alarm definition which monitor resource's event
and trigger actions in HOT.

The TOSCA scheme could be defined as the following:

tosca.policies.tacker.EventAlarming

.. code-block:: yaml

  tosca.policies.tacker.EventAlarming:
    derived_from: tosca.policies.Monitoring
    triggers:
      aodh_event:
        event_type:
          type: map
          entry_schema:
            type: string
          required: true
        condition:
          type: map
          entry_schema:
            type: string
          required: false
        action:
          type: list
          entry_schema:
            type: string
          required: true
        metadata:
          type: string
          required: true


and sample TOSCA template policy

.. code-block:: yaml

  description: Demo example

  metadata:
   template_name: sample-tosca-vnfd

  topology_template:
    node_templates:
      VDU1:
        type: tosca.nodes.nfv.VDU.Tacker
        capabilities:
          nfv_compute:
            properties:
              disk_size: 1 GB
              mem_size: 256 MB
              num_cpus: 1
        properties:
          image: cirros-0.4.0-x86_64-disk
          mgmt_driver: noop
          availability_zone: nova
          metadata: {metering.server_group: VDU1}

      CP1:
        type: tosca.nodes.nfv.CP.Tacker
        properties:
          management: true
          anti_spoofing_protection: false
        requirements:
          - virtualLink:
              node: VL1
          - virtualBinding:
              node: VDU1

      VL1:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: net_mgmt
          vendor: Tacker

    policies:
      - vdu1_event_monitoring_policy:
          type: tosca.policies.tacker.EventAlarming
          triggers:
              vdu1_event_healing:
                  description: VM delete
                  event_type:
                      type: compute.instance.delete.end
                      implementation: ceilometer
                  condition:
                      resource_type: instance
                  metadata: VDU1
                  action: [vdu_autoheal]

HOT template for Event Alarm monitoring resource:

.. code-block:: yaml

  description: 'Demo example'
  heat_template_version: '2013-05-23'
  outputs:
    mgmt_ip-VDU1:
      value:
        get_attr:
        - CP1
        - fixed_ips
        - 0
        - ip_address
  parameters: {}
  resources:
    CP1:
      properties:
        network: net_mgmt
        port_security_enabled: false
      type: OS::Neutron::Port
    VDU1:
      properties:
        availability_zone: nova
        config_drive: false
        flavor:
          get_resource: VDU1_flavor
        image: cirros-0.4.0-x86_64-disk
        metadata:
          metering.server_group: VDU1-08aa3827-0
        networks:
        - port:
            get_resource: CP1
        user_data_format: SOFTWARE_CONFIG
      type: OS::Nova::Server
    vdu1_event_healing:
      properties:
        alarm_actions:
        - http://{tacker domain url}:9890/v1.0/vnfs/{vnf id}/vdu1_event_healing/vdu_autoheal/hc4vg2c0
        description: VM delete
        event_type: compute.instance.delete.end
        query:
        - field: traits.instance_id
          op: eq
          value:
            get_resource: VDU1
        repeat_actions: true
      type: OS::Aodh::EventAlarm


Also, only when event_type is compute.instance.update, state of condition can be
defined on TOSCA Template.

This is part of sample TOSCA Template when event_type is compute.instance.update
and state is defined.

.. code-block:: yaml

  policies:
    - vdu1_event_monitoring_policy:
        type: tosca.policies.tacker.EventAlarming
        triggers:
            vdu1_event_error_healing:
                description: VM state is updated to error
                event_type:
                    type: compute.instance.update
                    implementation: ceilometer
                condition:
                    resource_type: instance
                    state: error
                metadata: VDU1
                action: [vdu_autoheal]


This TOSCA Template is changed to following HOT:

.. code-block:: yaml

  vdu1_event_error_healing:
    properties:
      alarm_actions:
      - http://{tacker domain url}:9890/v1.0/vnfs/{vnf id}/vdu1_event_error_healing/vdu_autoheal/hc4vg2c0
      description: VM state is updated to error
      event_type: compute.instance.update
      query:
      - field: traits.instance_id
        op: eq
        value:
          get_resource: VDU1
      - field: traits.state
        op: eq
        value: error
      repeat_actions: true
    type: OS::Aodh::EventAlarm

2. Enable vdu_autoheal by alarm monitoring and event monitoring

Enable vdu_autoheal by alarm monitoring and event alarm monitoring.
This plan adds vdu_autoheal in default alarm action.
The action vdu_autoheal needs healing target's name (e.g. VDU1).
Healing target is got by trigger's metadata [#f2]_ of alarm monitoring policy.

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

Work Items
----------

* Tosca element model monitoring event  to Heat ceilometer monitoring element translation
* Create a sample TOSCA template
* Add `tosca.policies.tacker.EventAlarming` policy to monitor specific event.
* Add vdu_autohealing in default alarm monitor action
* get vdu name from tosca template to use vdu_autoheal
* Unit Tests
* Functional Tests
* Update documentation

Dependencies
============

None

Testing
=======

Unit and functional tests are sufficient to test ``tosca.policies.tacker.EventAlarming``
policy.

Unit and functional tests are sufficient to test ``vdu_autohealing``
action by alarm monitoring policy.


Documentation Impact
====================

* Add VNFD tosca-template under samples to show how to configure
  ``tosca.policies.tacker.EventAlarming`` policy.
* Add a new policy ``tosca.policies.tacker.EventAlarming`` in Tacker
  Alarm Monitoring Framework [#f3]_.

References
==========
.. [#f1] https://docs.opnfv.org/en/stable-fraser/submodules/doctor/docs/development/requirements/05-implementation.html#figure8
.. [#f2] https://specs.openstack.org/openstack/tacker-specs/specs/stein/vdu-auto-healing.html#proposed-change
.. [#f3] https://docs.openstack.org/tacker/latest/user/alarm_monitoring_usage_guide.html
