
===========================================
Add alarm-based monitoring driver to Tacker
===========================================
https://blueprints.launchpad.net/tacker/+spec/alarm-based-monitoring-driver

This spec describes an alarm-based monitoring driver in Tacker

Problem description
===================

ETSI MANO architecture describes to monitor the VNF to take appropriate action
such as fault management, performance management. Monitoring became an
important aspect in MANO architecture.
Currently, Tacker provides a very minimal support for checking the liveliness
of VNF elements by means of ping or curl which helps to recover the element
in case it is unreachable. But Tacker does not support monitoring of
the CPU/memory usage of VNF elements. Further, it is necessary for Tacker to monitor all
VNF resources as well. The reason is that the failure of VNFs happen too diversely.

Proposed change
===============

The scope of this spec focused on:

* designing a generic monitoring framework. Whereby, an alarm-based monitoring driver
  in Tacker is designed to collect alarms/events triggered by the low-level designs
  (Ceilometer, Monasca, custom driver). In this spec, the alarm-based monitoring
  driver can completely monitor any resources in OpenStack that Ceilometer can support.
  In real implementation, this spec aims to leverage Ceilometer to monitor CPU/memory
  usage inside VNF.

* defining Monitoring Policy using the TOSCA Policy format. The monitoring policy
  can apply to a single VDU or multiple VDUs.

* adding support for inserting Ceilometer Alarms into the HOT template to allow
  Ceilometer to trigger scaling in Heat resource groups.


::

    The alarm-based monitoring framework:
            +-----------------------------------+
            |                                   |
            |                                   |
            |      +-----------------+          |
            |      | VNFM / TOSCA    |          |
            |      |                 |          |
            |      +--------+--------+          |
            |               |                   |
            |      +--------v--------+          |
            |      |                 |          |
            |      | alarm-framework <-----+    |
            |      |                 +---+ |    |
            |      +-+-^-------+-^---+   | |    |
            |        | |       | |       | |    |
            | +------v-++  +---v-+-+  +--v-+-+  |
            | |         |  |       |  |      |  |
            | |         |  |       |  |      |  |
            | |Ceilometer  |Monasca|  |Custom|  |
            | |         |  |       |  |      |  |
            | |         |  |       |  |      |  |
            | |         |  |       |  |      |  |
            | +---------+  +-------+  +------+  |
            +-----------------------------------+

The TOSCA scheme could be defined as the following:

**tosca.policies.tacker.Monitoring**

.. code-block:: yaml

  tosca.policies.tacker.Monitoring:
    derived_from: tosca.policies.Monitoring
    targets:
      type: list
      entry_schema:
        type: string
        required: true
      description: List of monitored VDUs
    triggers:
      resize_compute:
        event_type:
          type: map
          entry_schema:
            type: string
          required: true
        metrics:
          type: string
          required: true
        condition:
          type: map
          entry_schema:
            type: string
          required: false
        action:
          type: map
          entry_schema:
            type: string
          required: true


TOSCA template referred to [1]_ could be modeled with the below details in term of auto-scaling:

.. code-block:: ini

 tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
 description: Demo example

 metadata:
 template_name: sample-tosca-vnfd

 topology_template:
 node_templates:
    vdu1:
      type: tosca.nodes.nfv.VDU.Tacker
      capabilities:
        nfv_compute:
          properties:
            disk_size: 1 GB
            mem_size: 512 MB
            num_cpus: 2
      properties:
        image: cirros-0.3.4-x86_64-uec
        mgmt_driver: noop
        availability_zone: nova

    vdu1_cpu_usage_monitoring_policy:
        type: tosca.policies.tacker.Monitoring
        targets: [vdu1]
        triggers:
            resize_compute:
                event_type:
                    type: tosca.events.resource.utilization
                    implementation: Ceilometer
                metrics: cpu_util
                condition: utilization greater_than 70%
                    threshold: 70
                    period: 60
                    evaluations: 1
                    method: average
                    comparison: gt
                action:
                    resize: vdu1_scaling_policy

In the above template, event type is described in [3]_ and used in [4]_.

alarm_url will be created by webhook in Tacker as the following:

.. code-block:: ini

    v1.0/vnfs/<vnf-uuid>/<monitoring-policy-name>/<action-name>/<params>

Where:
monitoring-policy is the name of monitoring policy which is described in VNFD.

action-name is the name of action which is described in VNFD as well. Multiple actions
could be supported in monitoring policy. By changing action-name, the appropriate action
will be invoked and then the alarm-based monitoring driver will process this action.
In above example, action-name is 'vdu1_scaling_policy'. Whereby, when the monitoring driver
receives triggers from Ceilometer, it will invoke scaling action and trigger scaling
automatically. The detailed scaling mechanism using the monitoring driver is defined by
the scaling spec [2]_.

params contains the information related to alarm-actions. For example,
it can be used for user authentication. Whereby, Webhook handler will generate
randomly a key. This helps to make sure that we have a unique url for each alarm.
Alarm url will be stored in Tacker db and only these unique callbacks will be
used. The expression showm below is an example of alarm url which contains user authentication

.. code-block:: ini

    v1.0/vnfs/<vnf-uuid>/<monitoring-policy-name>/<action-name>/2w3r40-34c2d2

Here, monitoring-policy-name is the name of  monitoring policy and threshold is a value
which user wants to update.

Based on the different types of callbacks, we have the appropriate actions as following:

#1. if action is "Log", the monitoring driver will restore alarms into database.
We have two options to display these information:

 * Use CLI. The status of alarm could be defined in the existing CLI as the following:

   tacker vnf-show [vnf-id]

 * Modify Tacker-Horizon. Add "Alarms" tab to tacker-horizon where user can know what
   is happening with VNF. This tab need to have some information like:
   [VDU-ID]-----[Alarms (CPU, MEMORY, PORT,...)]--- [Status (HIGH, LOW, DELETED,..)].

#2. If action is "Scaling", we can call API to trigger scaling. The detailed scaling
    mechanism could be found in scaling spec [2]_.

#3. If action is "respawn", this action is the same in case of ping driver.



In order to translate the monitoring policy into HOT template, we can use heat ceilometer
resource type. In this approach, Tacker will create OS::Ceilometer::Alarm resource by
making use of either the same template used for scale-group or separate template.

create a ceilometer resource as below with required alarm criteria:

.. code-block:: ini

    vdu_scale_up_alarm:

        type: OS::Ceilometer::Alarm
        properties:

          meter_name: cpu_util
          statistic: avg
          period: 60
          evaluation_periods: 1
          threshold: 50
          comparison_operator: gt
          action:
            - {get_attr: tacker_alarm_url}
    vdu_scale_down_alarm:

        type: OS::Ceilometer::Alarm
        properties:

          meter_name: cpu_util
          statistic: avg
          period: 600
          evaluation_periods: 1
          threshold: 15
          comparison_operator: lt
          action:
             - {get_attr: tacker_alarm_url}


Future considerations:
----------------------

1. Indeed, it is necessary so that the monitoring driver could monitor beyond VDU resources.
CP resources should be monitored as well. Especially, it is necessary when we have SFC
in the future. The reason is that each CP will need to assign to a Neutron port.
SFC is created based on the connection of Neutron ports, therefore port monitoring is
necessary for high availability in SFC. The below example show port monitoring which
could be done by the alarm-based monitoring driver:


.. code-block:: ini

    tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

    description: Demo example

    metadata:
    template_name: sample-tosca-vnfd

    topology_template:
    node_templates:
       VDU1:
         type: tosca.nodes.nfv.VDU.Tacker
         properties:
           image: cirros-0.3.4-x86_64-uec
           flavor: m1.tiny
           availability_zone: nova
           mgmt_driver: noop
           config: |
             param0: key1
             param1: key2

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
       CP_monitoring_policy:
         type: tosca.policies.tacker.Monitoring
         targets: [CP1]
          triggers:
            port_monitoring:
              event:
                type: tosca.events.resource.utilization
                implementation: Ceilometer
                metrics: port_bandwidth
                condition: load greater_than 80%
                period: 60
                evaluations: 1
                statistics: average
                action:
                 trigger: vnffg1-ha-policy

2. In the future, Tacker users could want to update monitoring parameters like threshold.
The problem is when VNF instances sustain heavy load and CPU usage reaches to the
pre-defined threshold value. Alarms will be triggered to Tacker, but actually it not really
necessary because the VNF instances still have the ability to work well. Tacker users now want
to increase the threshold value. This could be done as the following:

.. code-block:: ini

    tacker vnf-update --vnf-id <vnf-id> --monitoring-policy-name <monitoring policy>
                                        --threshold [threshold-value]

NOTE: The threshold need to be be parameterized in the template.

Alternatives
------------

None

Data model impact
------------------

None

REST API impact
------------------

**POST on  /v1.0/vnfs/<vnf-uuid>/<monitoring-policy>/<action-name>/<params>**


Security
------------------

Need security between OpenStack Ceilometer and Tacker [5]_.

Notifications impact
--------------------
Ceilometer triggers alarms to the alarm-based monitoring driver in Tacker.

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
------------------

None

Implementation
===============

Assignee(s)
------------------

Primary assignee:
  Tung Doan <tungdoan@dcn.ssu.ac.kr>

  Kanagaraj Manickam <mkr1481@gmail.com>

Work Items
------------------

#. Tosca monitoring elment model to Heat ceilometer monitoring element
   translation
#. Enable the new convention in vnfd for mentioning to the alarm based
   monitoring parameters
#. create a sample TOSCA template
#. Create a new monitoring driver for alarm based monitoring with configurable
   parameter to use either of the approach mentioned above.
#. Enable to log Ceilometer alarms and report to users.
#. Enhance the horizon to show the live monitoring parameters.


Dependencies
============
In case we use heat ceilometer to describe the monitoring policy, make sure
that monitoring strategy is supported by Ceilometer.
Testing
========

1. Monitoring in case of high CPU usage

- Create vnfd from the alarm-based VNFD template
- Create vnf from the vnfd
- Stress VM which VNF is running on. The purpose is to make CPU usage reach
  threshold.
- Use CLI/Horizon to show alarms/events related to VNF VM.


Reference
=========

.. [1] http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.pdf
.. [2] https://review.opendev.org/#/c/318577/
.. [3] https://www.oasis-open.org/committees/download.php/56812/2015-10-27%20OpenStack%20Tokyo%20-%20Senlin-TOSCA%20vBrownBag-final.pdf
.. [4] https://github.com/openstack/tosca-parser/blob/master/toscaparser/tests/data/policies/tosca_policy_template.yaml#L60
.. [5] https://github.com/openstack/ceilometer/blob/stable/liberty/ceilometer/alarm/notifier/rest.py#L84
