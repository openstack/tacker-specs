..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


========================================
Affinity/Anti-affinity policies for VDUs
========================================

https://blueprints.launchpad.net/tacker/+spec/vdu-affinity-policy

This proposal describes the plan to introduce Affinity/Anti-affinity
policies for VDUs into VNFD template. The Tacker administrator enables
the Affinity policy to place VDUs into the same Compute node and enables
Anti-affinity policy to force-place VDUs into different Compute nodes.

Problem description
===================

Deployers sometimes want to control the placement of instances. For
example, they want to place the instances into the same compute node in
order to reduce communication overhead and traffics between instances,
e.g. a web server and a database. They may also wants to ensure that the
instances are deployed into different compute nodes to avoid failure at
the same time by a hardware fault. Especially, it's important to achive
severe SLA such that requires 99.999% availability.

Currently, the only way to control the placement is using availability
zone. But, creating availability zones requires admin priviledge and it
has no flexibility.

For example, considering this scenario, when there is a need to place
VDUs into the same compute node using availability zones. An
administrator creates availability zones for each compute node. An
operator finds appropriate compute node and specify corresponding
availability zone for each deployment. It has no merit of the cloud and
to make matters worse, operators have to recover VDUs manually if the
deployed compute node fails.

Dispersing VDUs into different compute nodes also has concerns. The
availability zones need to split into the maximum number of VDUs in
expected VNFs. It decreases utilization efficiency and there are some
cases that are unable to split, e.g. the operators use an infrastructure
provided by other organization, a split of availability zones violates
an infrastructure design policy and so on.

Proposed change
===============

Introduce a new policy ``tosca.policies.tacker.Placement`` into VNFD.
It provides affinity/anti-affinity placement for the target VDUs.

This feature is designed to satisfy a requirement defined in ETSI GS
NFV-IFA 011 [#f1]_.

An example VNFD assuming Active/Standby is shown below. This example
defines anti-affinity placement to primary VDU and secondary VDU.

.. code-block:: yaml

  :caption: Example VNFD
  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
  description: placement policy for VDUs
  topology_templete:
    node_templates:
      VDU_Primary:
        type: tosca.nodes.nfv.VDU.Tacker
  # ...snip...
      VDU_Secondary:
        type: tosca.nodes.nfv.VDU.Tacker
  # ....snip...
  policies:
    - anti_affinity_placement_policy
        type: tosca.policies.tacker.Placement
        properties:
          policy: anti-affinity
          strict: true
        targets: [ VDU_Primary, VDU_Secondary ]

This placement policy supports "affinity", "anti-affinity",
"soft-affinity", "soft-anti-affinity" in terms of Nova ServerGroup.

Mapping these ServerGroup policies to our placement policy type,
``policy`` property specifies "affinity" or "anti-affinity" as a
fundamental policy and ``strict`` property controls "soft-" prefix.

The base policy ``tosca.policies.Placement`` is already implemented on
tosca-parser [#f2]_. Current heat-translator implements the placement
policy using ``OS::Nova::ServerGroup`` resource which supports both of
affinity and anti-affinity but current heat-translator always specifies
"affinity" as the policy parameter of the resource.

This feature extends ``tosca.policies.Placement`` in heat-translator to
support additional properties. This plan follows other existing node
types. For example, when heat-translator translates
``tosca.policies.tacker.Scaling`` derived from
``tosca.policies.Scaling``, it uses the translator for
``tosca.policies.Scaling``, but heat-translator has an issue which is
policies derived from tosca.policies.Placement are not
translated [#f3]_. The issue must be solved before
we implement the feature.

Tacker itself needs no change excepting for the policy definition. The
policy will be defined in ``tacker_defs.yaml``.

This feature doesn't support Kubernetes until Node affinity becomes
stable. According to Kubernetes Configuration / Node affinity [#f4]_, it
was marked as beta at the time Rocky PTG was held.

Alternatives
------------

Implementing this feature has another option.

**Implement as a policy described in NSD**

This feature can also be modeled with a policy in NSD.

Example NSD including policies are shown below.

.. code-block:: yaml

  :caption: Example NSD

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
  description: placement policy for VNFs
  imports:
    - VNFD_Primary
    - VNFD_Secondary
  topology_template:
    node_templates:
      VNF_Primary:
        type: tosca.nodes.nfv.VNF_Primary
      VNF_Secondary:
        type: tosca.nodes.nfv.VNF_Secondary

  policies:
    - anti_affinity_policy:
        type: tosca.policies.tacker.Placement
        description: Apply my placement policy to my application servers
        targets: [ VNF_Primary, VNF_Secondary ]
        properties:
          policy: anti-affinity
          strict: true

With the above example, VNF_Primary and VNF_Secondary will be placed
into different compute nodes.

This model respects to ETSI GS NFV-IFA 014 [#f5]_, the policy corresponds to
NsDf.affinityOrAntiAffinityGroup.

Adopting this model requires a large scope of changes. It is due to
calling Tacker APIs from a Mitral workflow to create VNF instances that
constitute a NS instance. To implement this model, the following
changes will be required.

* Changes to NS feature

  * Add a support for policies section of NSD to "NS Create API".

    * Add a policy processor which understand the policies and reflect
      the policy to generated workflow.

      * The workflow needs to create a ServerGroup and pass the created
        resource to each VNF creation task. And the workflow need to
        return the resource as a part of its result.

      * VNF creation
        tasks need to generate and pass policies to "VNF Creation" API.

    * The policy processors should be isolated for each policy type

      * It seems to be hard to design a module that can be applied to
        general cases.

  * Save and use additional resource information

    * When Tacker creates NS, Tacker saves additional resources'
      information generated by a mistral workflow

      * The policies also need to be saved if we give policies as an API
        parameter.

    * When Tacker deletes NS, Tacker deletes additional resources' bound
      to the NS.

    * When Tacker updates NS, Tacker might take into account policies
      and additional resources.

* Changes to VNF feature

  * Add API parameter "policies" that allows users to add or override the policies.

    * Given policies have to be saved with other VNF attributes

  * Implement "tosca.policies.tacker.Placement.ServerGroup" which put
    all VDUs contained in the VNF to a specified ServerGroup.

TOSCA parser impact
-------------------

This feature needs to add a policy type named
``tosca.policies.tacker.Placement``.

.. csv-table:: tosca.policies.tacker.Placement (derived from tosca.policies.Placement)
    :header: Property Name,Type,Required,Default,Constraints,Description

    policy,string,false,'affinity',"'affinity',
    'anti-affinity'",Placement policy for target VDUs
    strict,boolean,false,'false',"'true', 'false'","If the policy is not
    strict, it is allowed to continue even if the scheduler fails to
    assign hosts under the policy."

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

VDU deployment time will be a little bit longer since Nova filters
applicable compute nodes for given VDUs.

Other deployer impact
---------------------

This feature requires heat-translator which supports
`tosca.policies.tacker.Placement` type.

Developer impact
----------------

This feature depends on a change of heat-translator which is developed
by other project. We need to discuss with heat-translator guys and to
contribute their project.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Dinesh Bhor <dinesh.bhor@nttdata.com>

Other contributors:
  Hiroyuki Jo <jo.hiroyuki@lab.ntt.co.jp>

  Masataka Saito <saitomst@intellilink.co.jp>

  Tushar Patil <tushar.vitthal.patil@gmail.com>

  Nitesh Vanarase <nitesh.vanarase@nttdata.com>

Work Items
----------

* Contribute to Heat-translator on `tosca.policies.Placement`
* Add TOSCA type definitions
* Unit Tests
* Functional Tests
* Feature documentation in doc/source/user/placement_usage_guide.rst

Dependencies
============

This feature depends on next items.

* VDU Level recovery

  * Current Tacker respawns the whole the VNF when it detects a failure
    on a VDU

  * If a user wants to use this feature to improve availability of his
    VNF which has redundant architecture, Tacker needs to support VDU
    level respawn action.

  * This issue should be solved in another blueprint.

* Improvement of Placement policy on Heat-translator

  * Current implementation only supports affinity policy.

  * We need to add support for the properties defined above.

* `Policies derived from tosca.policies.Placement are not translated <https://bugs.launchpad.net/heat-translator/+bug/1755433>`_

Testing
=======

add unit test

Documentation Impact
====================

* update VNFD template guide, adding a guide of
  tosca.policies.tacker.Placement

References
==========

.. [#f1] http://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/010/02.01.01_60/gs_NFV-IFA011v020101p.pdf
.. [#f2] https://github.com/openstack/tosca-parser/blob/f208175e69f05b5723c6cd2b0f56512b0bd3caa3/toscaparser/elements/TOSCA_definition_1_0.yaml#L931
.. [#f3] https://bugs.launchpad.net/heat-translator/+bug/1755433
.. [#f4] https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity
.. [#f5] http://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/014/02.04.01_60/gs_NFV-IFA014v020401p.pdf

