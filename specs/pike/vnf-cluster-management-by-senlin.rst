..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


===========================================
Autoscaling-management-with-senlin-resource
===========================================

The URL of the launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/autoscaling-management-with-senlin-resource

This spec introduces a new way of managing VDU auto-scaling function.

Problem description
===================

Tacker provides feasible functions of managing VNF which include
auto-scaling. Currently auto-scaling function is provided by Heat
AutoScalingGroup. But Heat AutoScalingGroup is not support a feasible enough
feature for VDU auto-scaling. That is because Heat can only make the
instruction of auto-scaling to VDU clusters but is lack of ability of managing
the VDU cluster. For example, when VDU auto-scaling failed or VDU went to ERROR
status, the only way to recover it is using Heat stack-update, but stack-update
usually has a low possibility to recover the stack.
Senlin[1] is an OpenStack project which provides clustering service.
It defines the concepts of Profile, Cluster, Node, Policy, Receiver, etc. which
is fit for the use case of VDU cluster management in Tacker. For example when
auto-scaling failed user can use Senlin commands to delete the failed nodes
directly. Senlin provides powerful policies(placement policy, deletion policy,
etc.) which can be used to make VDU auto-scaling much more intelligent than
Heat autoscaling group. If user wants to scale in a cluster, senlin deletion
policy(which can added to tacker later) can decide which nodes should be deleted
firstly(the elder ones or the young ones) and the nodes which are in ERROR
status will always be deleted at first. For alarming management, Senlin does
not only support Ceilometer, but also message service(Zaqar), and even some
other monitoring tools defined by user himself, as long as those tools support
webhook.
Besides scaling function, Senlin also provides HA policy(will be introduced to
Tacker in future) which can be used to support HA function for VDUs. By using
senlin to manage the VDU cluster, the VDU cluster's health status are always
checked by senlin, if the cluster is not healthy, for example, some nodes go
to error status, senlin will send an event to notify user. After all it is
reasonable to integrate Senlin into Tacker to manage VDU cluster.

Proposed changes
================

To use Senlin, necessary Senlin entities like Profile, Cluster, Policies,
etc. should be created by Heat first. All the Senlin resources have been
defined in HOT template already. By integrating Senlin with tacker, after all
the Tacker resources translated into a HOT template file, the HOT file will be
stored in Senlin profile, then Senlin will pass this template to Heat to create
VDU, CP VL, etc.
The whole workflow is like:

::

                                                    +-----------------+
    +-----------------+                             |   HOT template  |
    | TOSCA template  |                             | Senlin resource |
    | Senlin scaling  |                             +-----------------+
    | policy resource |     +-----------------+
    |  + other Tacker | --> | Heat translator | -->          +            -->
    |   resource      |     +-----------------+     +-----------------+      |
    +-----------------+                             |   HOT template  |      |
                                                    | Tacker resource |      |
                                                    +-----------------+      |
          +----------------+                        +----------------------+ |
          | Senlin Cluster |           +------+     |    HOT Senlin        | |
          +----------------+      <--  | Heat | <-- | profile: Tacker.yaml | |
                  ^                    +------+     +------------^---------+ |
                  |                                              |       <---+
            +-------------+                         +-----------------+
            | Senlin node |                         |   HOT template  |
            |   VDU       |                         | Tacker resource |
            +-------------+                         +-----------------+

Because Tacker supports TOSCA format template, it is necessary to define all
the resources(both Tacker and Senlin resources)in one TOSCA template. Then the
TOSCA template will be translated by tosca-parser and heat-translator to HOT
template which will be used to deploy VDU cluster. Heat-translator has already
supported most of the resources translation for Tacker and Senlin, So what is
needed to be done is TOSCA template integration for Tacker and Senlin, and
adding translation support for some resources in heat-translator.
And in Tacker additional jobs like parsing the monitoring property of VDU
needs to be done.


TOSCA template example for VDU auto-scaling management

.. code-block:: yaml

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
          metadata: {metering.vnf: SG1}
          monitoring_policy:
            name: ping
            parameters:
              monitoring_delay: 45
              count: 3
              interval: 1
              timeout: 2
            actions:
              failure: respawn

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
          network_name: net1
          vendor: Tacker

    policies:
      - cluster_scaling:
        type: tosca.policies.Tacker.Scaling
        description: Cluster node autoscaling
        driver: Senlin(Or some name else to distinguish Heat driver)
        targets: [VDU1]
        properties:
          min_instances: 2
          max_instances: 10
          default_instances: 3
          increment: 1

      - vdu_cpu_usage_monitoring_policy:
            type: tosca.policies.tacker.Alarming
            triggers:
                vdu_hcpu_usage_scaling_out:
                    event_type:
                        type: tosca.events.resource.cpu.utilization
                        implementation: Ceilometer
                    metrics: cpu_util
                    condition:
                        threshold: 50
                        constraint: utilization greater_than 50%
                        period: 60
                        evaluations: 1
                        method: avg
                        comparison_operator: gt
                    metadata: SG1
                    actions: [cluster_scaling]

The TOSCA template above does not introduce new resource type, only some
attributes of the policies resource are different from the existing scaling
policy supported by Tacker now. The 'driver' attribute is added to distinguish
the Heat-autoscaling-group driver and Senlin driver. User can switch the
auto-scaling backend by configuring different drivers.
This TOSCA template will be translated to HOT template. There will be two HOT
template created after the translation. One contains all the resources related
to VDU which is like what is done in Tacker now. This HOT template will be
referenced by Senlin profile when Senlin resources are created by Heat.
Another HOT template only contains senlin related resources which will be
passed to Heat for resource creation first. After Senlin resources 'profile'
and 'cluster' are created, three senlin node(the number of nodes depends on the
desired_capacity of cluster property in line 196) will be created according to
the senlin profile. The senlin node actually is the VDU, it will be created
during the node creation. After that the VDU nodes belong to a cluster. There
is a receiver which is a webhook pointing to the cluster, if the resource usage
triggers the alarm limit, the webhook will be executed to start scaling the
VDU cluster. The scaling obeys the scale-in and scale-out policies attached to
the cluster.

HOT template for Senlin resources

.. code-block:: yaml

  heat_template_version: 2016-04-08

  description: >
    This template demonstrates creation of senlin resources for vm auto-scaling

  resources:
    Senlin:
      type: OS::Senlin::Profile
      properties:
        type: os.nova.server-1.0
        properties:
          template: tacker.yaml

    Senlin_cluster:
      type: OS::Senlin::Cluster
      properties:
        desired_capacity: 3
        min_size: 2
        max_size: 10
        profile: {get_resource: Senlin}

    Senlin_scale_out_receiver:
      type: OS::Senlin::Receiver
      properties:
        action: CLUSTER_SCALE_OUT
        type: webhook
        cluster: {get_resource: Senlin_cluster}

    cluster_scaling_scale_out:
      type: OS::Senlin::Policy
      properties:
        type: senlin.policy.scaling-1.0
        bindings:
          - cluster: {get_resource: Senlin_cluster}
        properties:
          event: CLUSTER_SCALE_OUT
          adjustment:
            type: CHANGE_IN_CAPACITY
            number: 1

    scale_out_alarm:
      type: OS::Aodh::Alarm
      properties:
        meter_name: cpu_util
        statistic: avg
        period: 60
        evaluation_periods: 1
        threshold: 50
        repeat_actions: True
        alarm_actions:
          - {get_attr: [Senlin_scale_out_receiver, channel, alarm_url]}
        comparison_operator: gt

    Senlin_scale_in_receiver:
      type: OS::Senlin::Receiver
      properties:
        action: CLUSTER_SCALE_IN
        type: webhook
        cluster: {get_resource: Senlin_cluster}

    cluster_scaling_scale_in:
      type: OS::Senlin::Policy
      properties:
        type: senlin.policy.scaling-1.0
        bindings:
          - cluster: {get_resource: Senlin_cluster}
        properties:
          event: CLUSTER_SCALE_IN
          adjustment:
            type: CHANGE_IN_CAPACITY
            number: 1

    scale_in_alarm:
      type: OS::Aodh::Alarm
      properties:
        meter_name: cpu_util
        statistic: avg
        period: 60
        evaluation_periods: 1
        threshold: 50
        repeat_actions: True
        alarm_actions:
          - {get_attr: [Senlin_scale_in_receiver, channel, alarm_url]}
        comparison_operator: lt

HOT template for VDU

.. code-block:: yaml

  heat_template_version: 2016-04-08

  description: >
    This template demonstrates a template for VDU

  resources:
    VDU:
      type: OS::Nova::Server
      properties:
        image: cirros-0.3.4-x86_64-uec
        flavor: m1.tiny
        availability_zone: nova
        networks:
          - network: net1

Then how does the scaling feature work?
Take this template for example, after all the Senlin resources(a cluster with
three VDUs created on it, a receiver and scaling policy attached to the
cluster, and also an alarm) are deployed by Heat, the scaling management can
be left to Senlin completely. VDUs can be created and deleted automaticaly
under the rules of the scaling policy according to the resource consumption.
If users don't want to scale in/out VDUs automatically, they can also use
'tacker vnf-scale' command to control the scalability manually. The request
will trigger senlin backend to execute the scale in/out actions.
If user wants to auto-scale selective VDUs, they can simply add these VDUs
information into the template, Senlin will adopt the nodes into Senlin's
cluster and then control the scalability. This feature[2] is under
implementation by Senlin team now.

API impact
==========

This feature has no impact to the existing feature of Tacker. The existing
way of managing VDU scalibility can be used as usual. This feature only
adds a new option for VDU auto-scaling.

Dependency required
===================

Senlin should be installed to make this feature work, so it is necessary
to update the tacker's Devstack installation procedure in the script and
the manual installation guideline.
Because Senlin resources are deployed by Heat using senlinclient and
user may also want to use senlin command to do scaling manually, senlinclient
is required. And senlinclient talks to other clients(Novaclient, Heatclient)
by openstackSDK, openstackSDK is also required to be installed.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  xuhaiwei<hai-xu@xr.jp.nec.com>
  xuan0802<thespring1989@gmail.com>
  Xinhui Li<lxinhui@vmware.com>

Working Items
-------------

* Implement Senlin scaling policy for VDU in TOSCA template.
* Update Devstack installation procedure and manual installation guideline.
* Add unit test and function test for scaling feature.
* Add guideline for how to use Senlin scaling feature.

Testing
=======

* Add function test for vnf auto-scaling.
* Add tosca template sample for Senlin based auto-scaling.

Documentation Impact
====================

Update documentation for vnf auto-scaling and add new documentation.

References
==========

..[1] https://wiki.openstack.org/wiki/Senlin
..[2] https://blueprints.launchpad.net/senlin/+spec/senlin-adopt-function
