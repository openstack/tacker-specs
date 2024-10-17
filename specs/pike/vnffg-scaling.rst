
=================================
Enable scaling function for VNFFG
=================================

https://blueprints.launchpad.net/tacker/+spec/vnffg-scaling

This proposal aims to provide scaling function for VNFFG based on the existing
policy actions in VNFM.
The spec is referred to Network service fault management in ETSI standard [#first]_.

Problem description
===================

Currently, Tacker has already supported scaling function for
individual VNFs by using alarm driver. However, when doing
scaling in or out, the new-added or deleted instances' CP
cannot be added or removed to/from Neutron SFC port-pair group [#second]_.

This spec is supposed to provide scaling for VNFFG in single site,
multi-sites support will be taken into account in the future. In addtition,
Tacker had plan to add VNFFG to Network Service (NS), therefore this spec also
considers extending scope to support VNFFG inside NSs.

Proposed change
===============

Introduce a vnffg-ha engine in Tacker NFVO

.. code-block:: console


  +---------------------------------+
  |          Tacker_NFVO            |
  |      +------------------+       |
  |      |                  |       |
  |      |  NFVO API/TOSCA  |       |               +-----------------------+
  |      |                  |       |               |                       |
  |      +---------+--------+       |               |      Tacker_VNFM      |
  |                |                |               | +-------------------+ |
  |                |                |               | |  VNFM API/TOSCA   | |
  |                |                |               | |                   | |
  |                |                |               | +---------+---------+ |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |          +-----v-----+          |               |    +------v------+    |
  |          |NFVO Plugin|          |               |    | VNFM Plugin |    |
  |          |           |          |               |    |             |    |
  |          +-----+-----+          |               |    +------+------+    |
  |                |                |               |           |           |
  |  +-------------v--------------+ |               |           |           |
  |  |      vnffg-ha engine       | |               |   +-------v--------+  |
  |  |                            <-----conductor-------+ policy actions |  |
  |  |                            | |               |   +----------------+  |
  |  +----------------------------+ |               +-----------------------+
  |                                 |
  +---------------------------------+


*Component*

vnffg-ha engine: When vnffg-ha receives a trigger from policy actions in VNFM:
  1. Firstly, it finds which VNFFG VNF belongs to.
  2. Then it makes changes in VNFFG corresponding to VNF policy action.

Scaling support for VNFFG in Neutron SFC [#fourth]_:


.. code-block:: console

              +--------------------------------------------------+
              |     +---------------+  Neutron SFC               |
              |     |  +---------+  |             +---------+    |
     +-----------------+         +----------------+         |    |
     |        |     |  | VM 11   |  |             | VM 2    |    |
 +---+----+   |     |  +---------+  |             +-----+---+    |
 |Endpoint|   |     |               |                   |        |
 |        |   |     |  +---------+  |                   |        |
 +--------+   |     |  |         |  |                   |        |
     +-----------------+ VM 12   +----------------------+        |
              |     |  +---------+  |                            |
              |     +---------------+                            |
              +--------------------------------------------------+

In the above figure, VM11 is launched by VNF1, VM12 is scaled out from VM11.
VM2 is launched by VNF2.

Currently, Tacker leverages networking-sfc project [#third]_ to deploy
SFC based on Neutron ports. One of good points is that networking-sfc
enables multiple port pairs inside a port-pair group [#fourth]_ so that
load-balancing could be applied.

By using port pair group update we can modify the lists of port pairs
including **add**, **remove**, or even change the new set of port pairs.
This feature in networking-sfc is feasible to do auto-scaling for VNFFG.


*Load-balancing*

There are several cases to process:
1. load-balancing between VNFs.
2. load-balancing between VDUs

In the scope of this spec, we deal with load-balancing between VDUs to
achieve scaling vnffg.

In Neutron-SFC, a logical port-pair-group can contain one or more logical
port-pairs and is used to load balance traffic across the Service Functions
(logical port-pairs) [#sixth]_. We will use this spec to perform scale-out
or scale-in operations by adding or removing port-pairs on a port-pair-group
for VNFFG [#seventh]_.

For example, insert port-pair (PP2) of VM12 to existing port-pair-group that
contain port-pair (PP1) of VM11 to perform scale-out.

.. code-block:: console

   $ neutron port-pair-group-update --port-pair PP1 --port-pair PP2 PPG1

In the same way, we can update port-pair-group to perform scale-in by removing
one or more port-pairs from the port-pair-group.

Proposed change
---------------

AutoScalingRPC call

.. code-block:: python

 class AutoScalingRPC(object):

    target = oslo_messaging.Target(
        exchange='vnffg-scaling',
        topic=topics.TOPIC_CONDUCTOR,
        fanout=False,
        version='1.0')

    def vnf_scaling_event(self, context, **kwargs):
        pass


Tosca template:

.. code-block:: ini

    tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
    description: Demo example

    metadata:
      template_name: sample-tosca-vnfd1

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU.Tacker
          capabilities:
            nfv_compute:
              properties:
                 num_cpus: 1
                 mem_size: 512 MB
                 disk_size: 1 GB
      properties:
        image: cirros-0.3.5-x86_64-disk
        availability_zone: nova
        mgmt_driver: noop
        config: |
          param0: key1
          param1: key2
        metadata: {metering.vnf: VDU1}

    CP11:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        management: true
        order: 0
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL11
        - virtualBinding:
            node: VDU1

    CP12:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        order: 1
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL12
        - virtualBinding:
            node: VDU1

    CP13:
      type: tosca.nodes.nfv.CP.Tacker
      properties:
        order: 2
        anti_spoofing_protection: false
      requirements:
        - virtualLink:
            node: VL13
        - virtualBinding:
            node: VDU1

    VL11:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net_mgmt
        vendor: Tacker

    VL12:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net0
        vendor: Tacker

    VL13:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net1
        vendor: Tacker

    policies:
    - vdu1_cpu_usage_monitoring_policy:
        type: tosca.policies.tacker.Alarming
        triggers:
            vdu_hcpu_usage_respawning:
                event_type:
                    type: tosca.events.resource.utilization
                    implementation: ceilometer
                metrics: cpu_util
                condition:
                    threshold: 50
                    constraint: utilization greater_than 50%
                    period: 600
                    evaluations: 1
                    method: avg
                    comparison_operator: gt
                metadata: VDU1
                action: [respawn, notify]


In the above template, actions include **respawn ** and **notify**.
Accordingly, **respawn** action indicates the healing function.
Meanwhile, **notify** action indicates events which are triggered to
NFVO layer.

*Response to scaling action*

For scaling in, we need to remove the terminated instance's CP
from current sfc port-pair group ASAP, to avoid data lose.

But for scaling out, the new instantiated instance may need some
configuration before we add it's CP into sfc port-pair group.
This also aims to avoid traffic lose.
How to make sure VM is ready to work is a question.

Use cases
---------
1. Scaling-out

VNFM triggers the scaling out based on policies in VNFD. In VNFM layer, new VNF will be
scaled out with the same VNFD like the old one. In NFVO layer, we have 2 options. The first
option, after launching new VNF, for auto-scaling VNFFG we will wait and update new VNF's
port-pair to existing port-pair-group, it can take long time to reach normal state due to
VM-based VNF. The second option, we can use a algorithm to find the best matched VNF, that
have the same VNFD, tenant id and low resource usage and then add its port-pair to existing
port-pair-group. The second choice can give lower latency.
Scaling-out refers to vertical scale-out use case in [#fifth]_ IETF draft.

2. Scaling-in

For scaling-in, first port-pair of VNF will be remove from port-pair-group, then tacker will
invoke the scale-in policy to shutdown VNF.


Security impact
---------------

Notifications impact
--------------------

Because the failure of VNFs happened in VNFM layer, VNFFGs is orchestrated in NFVO layer.
A broken VNF could make one or several VNFFGs fail. Therefore, we need to have a method to
inform VNFFGs about their VNFs. In short term, tacker conductor will be used to emit events
from VNFM to NFVO. The future consideration is to use event/auditing functions.


Other end user impact
---------------------

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
  Tung Doan <doantungbk.203@gmail.com>

Other contributors:
  Yan Xing an<yanxingan@cmss.chinamobile>

  Phuoc Hoang <hoangphuocbk2.07@gmail.com>

Work Items
----------

 * Implement vnffg-ha engine in NFVO
 * Add API for triggering services in NFVO
 * Modify the existing VNFFG implementation in NFVO plugin
 * Add event/auditing function for vnffg-scaling
 * Add unit and functional tests for vnffg-scaling



Dependencies
============

None

References
==========
.. [#first] http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf
.. [#second] https://github.com/openstack/tacker/blob/master/tacker/db/nfvo/vnffg_db.py#L405&L431
.. [#third] https://wiki.openstack.org/wiki/Neutron/ServiceInsertionAndChaining
.. [#fourth] https://docs.openstack.org/developer/networking-sfc/api.html
.. [#fifth] https://www.ietf.org/id/draft-ao-sfc-scalability-analysis-02.txt
.. [#sixth] https://github.com/openstack/networking-sfc/blob/master/doc/source/contributor/sfc_ovn_driver.rst
.. [#seventh] https://docs.openstack.org/ocata/networking-guide/config-sfc.html
