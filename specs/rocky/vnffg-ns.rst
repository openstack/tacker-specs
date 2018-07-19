..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================================
VNF Forwarding Graph support in Network Service Descriptor
==========================================================

https://blueprints.launchpad.net/tacker/+spec/vnffg-ns

This spec describes the plan to add support for VNF Forwarding Graphs (VNFFG)
into Tacker Network Service Orchestration (NSO). In its current state Tacker
contains an NSO feature which can deploy a set of VNFs in one shot using NSD
[#f1]_. Tacker also supports VNFFG, but it is used as a separate VNFFGD
template schema and cannot launch VNFs. The purpose of this spec is to add
support for traffic flow, and VNFFGs via NSD.

Problem description
===================

::

               +-----------------------------------------------------+
               |            +----------------------------+           |
               |            |            VNFFG           |           |
               |            | +--------+      +--------+ |           |
      +-------+|            |/| VNF 2A |      | VNF 2B |\|           |
     / End   / |            / +--------+      +--------+ \           |
    / Point / \|           /|       \            /       |\          |
   +-------+   \          / |        \          /        | \         |
               |\ +-------+ |         \        /         | +-------+ |
               | \| VNF 1 | |         +--------+         | | VNF 3 | |
               |  +-------+ |         | VNF 2C |         | +-------+ |
               |            |         +--------+         |           |
               |            +----------------------------+           |
               +-----------------------------------------------------+


This is a desire by NFV community to be able to orchestrate and manage
network traffic by using NSD templates. Adding support of VNFFGs is an
essential part of network service which describes a graph of inter-connected
VNFs. The traffic flow through a VNFFG is controlled by a Forwarding Path
element, which also include policy for which traffic may traverse a
Forwarding Path of connected VNFs in the graph. An NSD contains a description
of all VNFs within the network service, how those VNFs are connected via
Virtual Link (VL) elements (Layer 2 connection), and a VNFFG which describe
how the traffic should flow.

In order to achieve full NSO driven by a single NSD, this spec intends to
address gaps of missing NSO functionality by integrating VNFFGs into NSO.

**Notes:**

* This spec focus on integrating VNFFG into NS and in the current
  implementation of VNFFG, there's only one path supported.

* The future works on VNFFG will add support for multiple paths.
  Then NS will be able to contain multiple paths through the graph
  depending on the desired traffic flow.

Background Knowledge
====================

How VNF is supported in NS
--------------------------
Firstly we need to onboard the VNFDs, then import the onboarded VNFDs in NSD.

Basic sample tosca template for VNF with NSD:

.. code-block:: yaml

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0

  description: Import VNFDs(already on-boarded)
  imports:
    - VNFD1
    - VNFD2
  topology_template:
    node_templates:
      VNF1:
        type: tosca.nodes.nfv.VNF1

      VNF2:
        type: tosca.nodes.nfv.VNF2

..

When instantiating this NSD, nfvo_plugin retrieves these VNFDs from DB,
generates mistral workflows, and then execute these workflows.

Next, mistral invokes tacker's API to instantiate VNF according to the
workflows [#f2]_.

Proposed changes
================

Introduce a new template for network service which topology contains VNFs,
connection points, virtual links, a forwarding path, and a VNF forwarding
graph. The future work will add support for multiple forwarding paths
and the groups property will contains a set of VNFFGs.

::

                       TOSCA                                        NFV
      +------------------------------------------+         +--------------------+
      |                                          |         |                    |
      |           Service Template  <------------------------+ Network Service  |
      |                                          |         |   Descriptor (NSD) |
      | +-------------------+                    |         |                    |
      | | Topology template |   +-------------+  |         |     +----------+   |
      | |  +---------+      |   | Node types  <------------------+   VNFD   |   |
      | |  |  Node   <----------+substitutable|  |         |     +----------+   |
      | |  | Template|      |   +-------------+  |         |                    |
      | |  +---------+      |                    |         |     +----------+   |
      | |  +---------+      |   +-------------+  |      +--------+   VLD    |   |
      | |  |  Node   <----------+ Node types  <---------+  |     +----------+   |
      | |  | Template|      |   +-------------+  |         |                    |
      | |  +---------+      |                    |         |     +----------+   |
      | |  +---------+      |   +-------------+  |      +--------+  VNFFGD  |   |
      | |  |  Node   <----------+ Group types <---------+  |     +----------+   |
      | |  | Template|      |   +-------------+  |         |                    |
      | |  +---------+      |                    |         |     +----------+   |
      | |  +---------+      |                    |      +--------+   PNFD   |   |
      | |  |  Node   |      |   +-------------+  |      |  |     +----------+   |
      | |  | Template<----------+ Node types  <---------+  |                    |
      | |  +---------+      |   +-------------+  |         +--------------------+
      | |                   |                    |
      | +-------------------+                    |
      |                                          |
      +------------------------------------------+


Multiple changes will be required, which includes changes to tacker Client,
Horizon, and Server.

::

   +--------------------------------------------+
   |     +------------------+                   |
   |     |Client Application|                   |
   |     +--------+---------+                   |
   |              |                             |
   |       +------v-----+                       |
   |       |  NFVO NS   +----------------+      |
   | +-----+    API     |                |      |
   | |     +------+-----+             +--v---+  |
   | |            |                   | VNFM |  |
   | |            |                   +---+--+  |
   | |            |                       |     |
   | | +----------v---------------+   +---v--+  |
   | | |Network Service Descriptor|   | VNFs |  |
   | | +--------------------------+   +------+  |
   | +-------------+                            |
   |               |                            |
   |       +-------v--------+                   |
   |       |     VNFFGs     |                   |
   |       +----------------+                   |
   +--------------------------------------------+


VNF-Mapping
-----------

The VNF-mapping feature was introduced in VNFFG. This feature allows the
operator to decide which specific VNF instances to use when instantiating a
VNFFG. VNF-mapping is an orchestrator choice. The default mapping of VNFs will
be based on random selection.

In NSO, VNFs are instantiated by NSO so we can use the new-created VNFs for
VNFFG.

VNFFGD Changes
--------------

**VNFFG creation**

The proposed way to support VNFFGD in NS is to define the VNFFGD in NSD:

Proposed sample Tosca template for VNFFG with NSD:

.. code-block:: yaml

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

  description: Import VNFDs(already on-boarded) with input parameters
  imports:
      - sample-vnfd1
      - sample-vnfd2

  topology_template:
    inputs:
      vl1_name:
        type: string
        description: name of VL1 virtuallink
        default: net_mgmt
      vl2_name:
        type: string
        description: name of VL2 virtuallink
        default: net0
      net_src_port_id:
        type: string
        description: neutron port id of source port
      ip_dest_prefix:
        type: string
        description: IP prefix of destination port

    node_templates:
      VNF1:
        type: tosca.nodes.nfv.VNF1
        requirements:
          - virtualLink1: VL1

      VNF2:
        type: tosca.nodes.nfv.VNF2

      VL1:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: {get_input: vl1_name}
          vendor: tacker

      VL2:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: {get_input: vl2_name}
          vendor: tacker

      Forwarding_path1:
        type: tosca.nodes.nfv.FP.TackerV2
        description: creates path inside ns (src_port->CP12->CP22->dst_port)
        properties:
          id: 51
          policy:
            type: ACL
            criteria:
              - name: block_tcp
                classifier:
                  network_src_port_id: {get_input: net_src_port_id}
                  destination_port_range: 80-1024
                  ip_proto: 6
                  ip_dst_prefix: {get_input: ip_dest_prefix}
          path:
            - forwarder: sample-vnfd1
              capability: CP12
            - forwarder: sample-vnfd2
              capability: CP22

      Forwarding_path2:
        type: tosca.nodes.nfv.FP.TackerV2
        description: creates path inside ns (src_port->CP12->dst_port)
        properties:
          id: 52
          policy:
            type: ACL
            criteria:
              - name: block_tcp
                classifier:
                  network_src_port_id: {get_input: net_src_port_id}
                  destination_port_range: 8080-8080
                  ip_proto: 6
                  ip_dst_prefix: {get_input: ip_dest_prefix}
          path:
            - forwarder: sample-vnfd1
              capability: CP12

    groups:

      VNFFG1:
        type: tosca.groups.nfv.VNFFG
        description: HTTP to Corporate Net
        properties:
          vendor: tacker
          version: 1.0
          number_of_endpoints: 2
          dependent_virtual_link: [VL1, VL2]
          connection_point: [CP12, CP22]
          constituent_vnfs: [sample-vnfd1, sample-vnfd2]
        members: [Forwarding_path1]

      VNFFG2:
        type: tosca.groups.nfv.VNFFG
        description: HTTP to Corporate Net
        properties:
          vendor: tacker
          version: 1.0
          number_of_endpoints: 1
          dependent_virtual_link: [VL1]
          connection_point: [CP12]
          constituent_vnfs: [sample-vnfd1]
        members: [Forwarding_path2]

..

To instantiate NS from this NSD, nfvo_plugin extracts the VNFGD from the
NSD, generates mistral workflows, and then execute these workflows.


**VNFFG listing**

The VNFFG created via NSD then will be available in the results of the
following command.

.. code-block:: console

  openstack vnf graph list

..


**VNFFG updating**

We can update the VNFFG created via NSD using NSD updates.

NSO changes
-----------

Current implementation of Tacker lacks of the ability to update NS. Updating
feature will be supported in the future.

.. code-block:: console

  openstack ns update --nsd-template <NSD template to update NS> <NS name or id>

..

Like mentioned above, the VNFFG can be updated via this method.

Due to the limitation of networking-sfc which does not support NSH
(Network Service Header), the neutron port-ids information needs to be
available before we can create the flow classifiers for VNFFGs [#f3]_. That
will add complexity to the networks and VNFFGs creation via NSD implementation.
Therefore, in this spec we will only focus on the VNFFG creation via NSD and
requires all the networks available beforehand. Future works will add
support for networks creation via NSD.


Alternatives
------------

None

Data model impact
-----------------

* The data model for NS will need to be updated to include a list of VNFFGs
  it contains.

* The VNFFG data model already exists, and can track the Forwarding Path and
  VNFs which belong to each VNFFG. A new column names ns_id will be added to
  keep track of the NS in which that VNFFG belongs. If that VNFFG does not
  belong to any NS, the ns_id column's value of that VNFFG will be blank.

* For VNFFGD, a new column names nsd_id will be added too to identify the NSD
  it belongs.

REST API impact
---------------

The current REST API includes functionality to query VNFFG objects and its
sub-components. Changes to the REST API for NS will include returning the
associated VNFFGs for that NS instance.

**JSON Request and Response Sample:**

GET /v1.0/nss/{ns_id}

Show ns - Show information for a specified ns id.

* show_res:

.. code-block:: console

    {
        "ns": {
            "name": "NS_vnffg_demo"
            "description": "ns vnffg demo",
            "status": "ACTIVE",
            "created_at": "2018-07-19 01:28:36",
            "tenant_id": "a7f7c7a319ab4b6bb5217712e8e62c38",
            "vim_id": "8010ece7-0e9a-420f-8ec9-08d87304f7fd",
            "updated_at": "2018-07-19 01:30:23",
            "mgmt_urls": "{'VNF2': {'VDU1': '192.168.120.7'},
                           'VNF1': {'VDU1': '192.168.120.3'}}",
            "vnf_ids": "{'VNF2': '28f957ea-4cdb-4611-9b3d-25f5711d88b6',
                         'VNF1': '287a0084-7ddf-4682-b286-20304a143078'}",
            "error_reason": null,
            "vnffg_ids": "{'VNFFG2': '23268756-ea57-4958-aa19-493c8d697bbf',
                           'VNFFG1': '69683863-d3da-4ff1-badc-f16ca36b40e5'}",
            "nsd_id": "2ab5c205-e526-4176-a22e-219242346dab",
            "id": "26257a53-e0c2-423f-9385-0ff5ccc02839",
        }
    }

..

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

No impact on end user side. Behaviour will be the same as earlier ns
operations. Support for vnffg will be supported inside ns.
As per the earlier ns CRUD operation behaviour, first we need to create
vnfd and mention the vnfd name in nsd template.
Example CLI calls:

First create required VNFDs:

.. code-block:: console

  openstack vnf descriptor create --vnfd-file <tosca vnf1 yaml file> VNFD1

  openstack vnf descriptor create --vnfd-file <tosca vnf2 yaml file> VNFD2

  openstack vnf descriptor create --vnfd-file <tosca vnf3 yaml file> VNFD3

..

Mention the vnfd name in nsd template:

.. code-block:: yaml

  imports:
      - VNFD1
      - VNFD2
      - VNFD3

..

To create NSD:

.. code-block:: console

  openstack ns descriptor create --nsd-file samples/nsd/tosca-vnffg-nsd.yaml NSD1

..

To create NS

.. code-block:: console

  openstack ns create --nsd-name NSD1 --param-file <PARAM-FILE> NS1

..

Performance impact
------------------

None

Developer impact
----------------

Mistral will be used to generate VNFFG from NS follow these steps:

1. Getting the vnf-mapping parameter from the imported VNFs or the VNF created
through NSD and use it as the parameter for the VNFFG creation function.

2. Extracting nested VNFFGs template from NS template (similar to nested Heat
template, we can extract groups attribute and its forwarding path in members).

3. Using Mistral workflow to create VNFFG directly from VNFFG template above
(don't need to create VNFFGD).

::

   +---------------------------------------------+
   |     +------------------+                    |
   |     |Client Application|                    |
   |     +--------+---------+                    |
   |              |              +-------------+ |
   |        +-----v----+         |  Workflow   | |
   |        | NFVO:NSD +--------->  Generator  | |
   |        +-----+----+         +---------+---+ |
   |              |                        |     |
   |              |                        |     |
   |              |                        |     |
   | +------------v-------------+     +----v---+ |
   | |Network Service Descriptor|     | Mistral| |
   | +--------------------------+   +-+----+---+ |
   |                                |      |     |
   |                    +--------+  |  +---v--+  |
   |                    | VNFFGs <--+  | VNFs |  |
   |                    +--------+     +------+  |
   +---------------------------------------------+

Network Service creation procedure is showed as below diagram

::

                 +------------------------+
                 |                        |
                 |      NSD template      |
                 |                        |
                 |                        |
                 +------------------------+
                             | extract templates
         +-------------------v---------------+
         |                                   |
    +----v------------+            +---------v------+
    |                 |            |                |
    | VNFFGD templates|            |      VNFDs     |
    |                 |            |                |
    +----+------------+            +---------+------+
         |                                   |    create VNFs
         |                +-----------+------+-----------------+
         |                |           |                        |
         |                |           |                        |
         |           +----v---+   +---v----+              +----v---+
         |           |  VNF1  |   |  VNF2  |              |  VNFn  |
         |           +----+---+   +---+----+              +----+---+
         |                |           |                        |
         |                | +---------+                        |
         |                | | +--------------------------------+
         |                | | |
         |                | | |on-success
         |                | | |
         |            +---v-v-v---------+
         |            |      VNFFGs     |
         +------------>    (optional)   |
        create VNFFGs |                 |
                      +-----------------+


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Cong Phuoc Hoang <hoangphuocbk2.07@gmail.com>

Other contributors:
  Tim Rozet <trozet@redhat.com>

  Yan Xing an<yanxingan@cmss.chinamobile.com>

  Dharmendra Kushwaha <dharmendra.kushwaha@india.nec.com>

  Trinh Nguyen <dangtrinhnt@gmail.com>

Work Items
----------

1. Changes in NS to add support for 'vnffg'.
2. CLI changes in tackerclient
3. Add unit tests.
4. User guide docs for vnffg-ns.
5. Add devref to document how VNFFG in NSD works

Dependencies
============

None

Testing
=======

None

Documentation Impact
====================

Devref guide will be added to describe the vnffg support in NSD features,
operations with samples.

References
==========

.. [#f1] https://docs.openstack.org/tacker/latest/user/nsd_usage_guide.html
.. [#f2] https://docs.openstack.org/tacker/latest/reference/mistral_workflows_usage_guide.html
.. [#f3] https://docs.openstack.org/tacker/latest/user/vnffg_usage_guide.html#known-issues-and-limitations
