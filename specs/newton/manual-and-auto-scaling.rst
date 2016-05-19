
===========================
VNF manual and Auto-scaling
===========================
https://blueprints.launchpad.net/tacker/+spec/vnf-scaling

Adds support to scale the deployed VNF manually and automatically.

Problem description
===================

Currently VNF resources in terms of CPU core and memory are hardcoded
in VNFD template through image flavor settings. This result in either
provisioning VNF for typical usage or for maximum usage. The former leads
to service disruption when load exceeds provisioned capacity. And the later
leads to underutilized resources and waste during normal system load. So
users would like to have a way to seamlessly scale the number of VNFs on
demand either manually or automatically.


Proposed change
===============
Following sections details the every aspect of scaling from TOSCA modeling
till the driver level.

1. TOSCA Scaling Policy Model

Assume the following sample template where 2 VDUs are connected to a network
using single connection for each.

.. code-block:: yaml

    topology_template:
      node_templates:
        vdu1:
          type: tosca.nodes.nfv.VDU.Tacker
        vdu2:
          type: tosca.nodes.nfv.VDU.Tacker

        # vdu1 - cp1 - vl

        cp1:
          type:tosca.nodes.nfv.CP.Tacker

        # vdu2 - cp2 - vl

        cp2:
          type:tosca.nodes.nfv.CP.Tacker
        vl:
          type: tosca.nodes.nfv.VL

When user deploys this VNF, assume that initially 2 instances of vdu1+cp1 to be
running, and when scaling scenario occurs for vdu1, it needs to scaled out/in
in the step of 1 count to max of 3 and min of 1 instance of vdu to be running.
To support this case, Scaling policy would be defined as below by referring [1]


**tosca.policies.tacker.Scaling:**

.. code-block:: yaml

  tosca.policies.tacker.Scaling:
    derived_from: tosca.policies.Scaling
    description: Defines policy for scaling the given targets.
    properties:
      increment:
        type: integer
        required: true
        description: Number of nodes to add or remove during the scale out/in.
      targets:
        type: list
        entry_schema:
          type: string
        required: true
        description: List of Scaling nodes.
      min_instances:
        type: integer
        required: true
        description: Minimum number of instances to scale in.
      max_instances:
        type: integer
        required: true
        description: Maximum number of instances to scale out.
      default_instances:
        type: integer
        required: true
        description: Initial number of instances.
      cooldown:
        type: integer
        required: false
        default: 120
        description: Wait time (in seconds) between consecutive scaling
        operations. During the cooldown period, scaling action will be ignored


And the example of these new elements are given below:

.. code-block:: yaml

     policies:

        sp1:

          type: tosca.policies.tacker.Scaling

          description: Simple VDU scaling

          properties:
             min_instances: 1

             max_instances: 3

             default_instances: 2

             increment: 1

             targets: [vdu1, vdu2]


Here, in case of scale-in, targets will be reduced by count given in
'increment', and for scale-out its vice-versa.

Assume that user wants to monitor vdu1+cp1 and vdu2+cp2 separately or
accumulative. To support either of these cases, scaling policy could be
defined inline with monitoring strategy and gives flexibility.

Below section defines the triggering mechanisms.

Once scaling is started, it will listen to the exposed heat events to track
the progress of the scaling and find out the new/deleted VDU details and it
will invoke the management drivers accordingly.

2. Trigger Scaling Policy using an API (Manual)
Tacker would be provided to enable the support for scaling on existing REST
API for VNFS, as mentioned in the below section `REST API Impact`_.

And corresponding CLI would look like below:

.. code-block::ini

**tacker vnf-scale --vnf-id <vnf-id>**
                  **--vnf-name <vnf name>**
                  **--scaling-policy-name <policy name>**
                  **--scaling-type <type>**

Here, scaling-policy-name and scaling-type are same as defined in the REST API.
And vnf-id or vnf-name is used to provide the VNF reference, while one of these
parameters are mandatory, if both are given, vnf-id will be used.

For example, to scale-out policy 'sp1' defined above, this cli could be used
as below:

.. code-block::ini

**tacker vnf-scale --vnf-name sample-vnf**
                  **--scaling-policy-name sp1**
                  **--scaling-type out**


3. Trigger Scaling Policy using Alarm / Monitoring Triggers

Alarm monitoring driver could make use of this scaling feature to trigger
scale-in scale-out automatically as mentioned below:

.. code-block:: yaml

        mp1:

          type: tosca.policies.Monitoring

          description: Simple VDU monitoring

          properties:

            # all monitoring related properties

            scale-[in|out]: sp1

            targets: [vdu1, vdu2]

NOTE:
Here, targets should match with corresponding scaling policy. Also the exact
schematic of this kind of monitoring policy is defined by the monitoring
`spec`_ .

.. _spec: https://review.openstack.org/306562

Alternatives
------------------

None

Data model impact
------------------

Once scaling operation is completed, the current state of the scale elements
would be captured in the deviceattributes table as set of key value pairs.


.. _REST API Impact:

REST API impact
---------------

**POST on v1.0/vnfs/<vnf-uuid>/scale**

with body

.. code-block::json

**{"scale": { "type": "<type>", "policy" : "<scaling-policy-name>"}}**

Here,

<scaling-policy-name> - Name of the scaling policy used in the VNFD, which
needs to be unique, similar to VDU naming.

For scaling there two kind of actions:

* **scale-in** - For Scaling in operation
* **scale-out** - For Scaling out operation

so <type> could be one of 'in' for scale-in or 'out' for scale-out.

Response http status codes:

* 202 - Accepted the request for doing the scaling operation
* 404 - Bad request, if given scaling-policy-name and type are invalid
* 500 - Internal server error, on scaling operation failed due to an error
* 401 - Unauthorized

During the scaling operation, the VNF will be moving in below state
transformations:

* **ACTIVE -> PENDING_SCALE_IN -> ACTIVE**
* **ACTIVE -> PENDING_SCALE_IN -> ERROR**
* **ACTIVE -> PENDING_SCALE_OUT -> ACTIVE**
* **ACTIVE -> PENDING_SCALE_OUT -> ERROR**

For each scaling action, the state transformation is captured via Events
supported by audit spec [5]


Security
------------------
It is allowed only for VNF owner and admin users.

so following policy will be defined for the new REST API defined above.

**"rule:admin_or_owner"**

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
------------------

None

Implementation
===============

How to form required heat scaling resource type in heat
-------------------------------------------------------
In OpenStack, heat does provide an feature to setup a scaling group, which can
be scaled in/out based on the pre-defined scaling policy. Here scaling group
can contain any OpenStack resource such as nova instance, cinder volume, etc,
whereas scaling policy helps to scale in/out in numbers, percentage, etc.
So this heat feature could be used to accomplish the scaling of VDU in
tacker as mentioned below:

1. Model the complete VNFD elements to be part of heat scaling group
OS::Heat::ScalingGroup. For example, consider a simple VNFD VDU.
Now we wanted this VDU to be scaled in/out between 2 to 5 counts with
initial setup with 3 elements. In this case, use the below heat template to
setup the scale group. while creating the group, use the min_instances,
max_instances and cooldown from the policies defined.

.. code-block:: yaml

    heat_template_version: 2016-04-08

    resources:
      G1_scaling_group:
         type: OS::Heat::ScalingGroup
            properties:
              min_size: 2
              max_size: 5
              desired_capacity:3
              cooldown: 120
              resource:

                 type: <vdu scale group custom type>


NOTE:

* here, custom type would capture the scale group as single heat HOT template
  and same would be used as a whole to scale in/out.
* Scale group could be modeled in TOSCA, and same needs to be
  supported in heat template-translator to convert it into heat scaling group.
* Make use of vnfd template parameterization to customize min_size, max_size,
  desired_capacity and flavor based on scaling need and same has to made as
  template parameters in above heat template.

Once scaling group is ready, scaling policy needs to be configured as below
one for scale-in and another for scale-out:

.. code-block:: yaml

    G1_scale_out_policy:

        type: OS::Heat::ScalingPolicy
        properties:

            adjustment_type: change_in_capacity
            cooldown: 120
            scaling_adjustment: 1

    G1_scale_in_policy:

        type: OS::Heat::ScalingPolicy
        properties:

            adjustment_type: change_in_capacity
            cooldown: 60
            scaling_adjustment: -1

NOTE:

* cooldown is the time-window in seconds of scale in/out event and this
  will be varying based on the VNF.
* Add the scale group reference id in both of these policies.
* To monitor the scale group using the alarm based monitoring driver,
  following setup to be made in scaling element:

In scaling VDU element, set the metadata as below with unique identifier per
scale group:

.. code-block:: yaml

    resources:

        G1_scaling_group:

            properties:

                resource:

                    metadata: {"metering.stack": <XXX>}


In alarm based monitoring driver, it's mandatory to set the matching metadata
with the same unique identifier as below. It helps ceilometer to aggregate the
metrics collected across all the groups defined in the targets and find out
whether the alarm criteria is met or not.

.. code-block:: yaml

    G1_scale_out_alarm:

        type: OS::Ceilometer::Alarm
        properties:

            matching_metadata: {'metadata.user_metadata.stack': <XXX>}


NOTE:

* When scaling is supported, it would mandates the Load-balancer among the VDU
  in scaling group. So it can to be added as part of scaling group resource
  element. This would help the user to have virtual IP for the set of VDUs in
  the scaling group. The scope of thise problem could be enabled as another
  Load balancer policy via separate blueprint/spec.


Assignee(s)
------------------

Primary assignee:
  Kanagaraj Manickam <mkr1481@gmail.com>

Work Items
------------------

#. Model scaling in vnfd with TOSCA format.
#. Leverage tosca-parser & heat-translator as appropriate for scaling.
#. Update heat infra driver to handle scaling.
#. Update the required REST API and enable the same in python-tackerclient.
#. Enhance the horizon to scale in/out the live VNF.
#. Create a sample TOSCA template with scaling requirements.
#. Update the user documents.
#. Add the required test cases.
#. Add devref for scaling.
#. Add release notes.
#. Add event support once spec [5] is implemented.

Dependencies
============
None


Reference
=========
1. http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html#_Toc445238236

2. http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.pdf

3. https://review.openstack.org/#/c/214297/4/specs/liberty/Auto-Scaling.rst

4. https://review.openstack.org/#/c/283163/1/specs/mitaka/manual-scaling.rst

5. https://review.openstack.org/321370