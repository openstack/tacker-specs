==================================
Network Service Descriptor support
==================================

https://blueprints.launchpad.net/tacker/+spec/nsd-support

This proposal describes the plan to add Network Service Descriptor(NSD) support
in Tacker. To enable dynamic composition of network services, NFV introduces
Network Service Descriptors (NSDs) that specify the network service to be
created.

::

         TOSCA                                NFV

 +-----------------------------------+    +----------------+
 |         Service Template          |    | Network Service|
 | +-------------------+             |    |    Descriptor  |
 | | Topology Template |             |    |                |
 | |    +---------+    | +----------+|    |    +-----+     |
 | |    |  Node   | <--+-| NodeTypes|<----+----| VNFD|     |
 | |    | Template|    | +----------+|    |    +-----+     |
 | |    +---------+    |             |    |                |
 | |    +---------+    | +----------+|    |    +-----+     |
 | |    |  Node   | <--+-| NodeTypes|<----+----| VLD |     |
 | |    | Template|    | +----------+|    |    +-----+     |
 | |    +---------+    |             |    |                |
 | |    +---------+    | +----------+|    |    +-------+   |
 | |    |  Node   | <--+-| NodeTypes|<----+----| VNFFGD|   |
 | |    | Template|    | +----------+|    |    +-------+   |
 | |    +---------+    |             |    |                |
 | |    +---------+    | +----------+|    |    +-----+     |
 | |    |  Node   | <--+-| NodeTypes|<----+----| PNFD|     |
 | |    | Template|    | +----------+|    |    +-----+     |
 | |    +---------+    |             |    |                |
 | +-------------------+             |    |                |
 +-----------------------------------+    +----------------+

As shown in above picture, NSD can includes VNFD, VNFFGD, VLD and PNFD.
 * VNFD   --> Virtual Network Function Descriptor
 * VNFFGD --> VNF Forwarding Graph
 * VLD    --> Virtual Link Descriptor
 * PNFD   --> Physical Network Function

In current scope Tacker does not includes PNFD.


Problem description
===================

Tacker builds a generic VNF Manager and a NFV Orchestrator to deploy and
operate Virtual Network Functions (VNFs) on an NFV infrastructure platform
like OpenStack. But currently needs the ability to describe and orchestrate
a collection of VNFs to render a Network Service. It is desired by community
to manage and orchestrate network service. NSD template is the way to introduce
that capability.

To enable dynamic composition of network services, NFV introduces Network
Service Descriptors (NSDs) that describe the network service to be created.
NSDs mainly describes the what all network services to be instantiated in the
NFVI. An NFV Orchestrator can use NSD to instantiate a network service which
may have one or more VNFs, VLs and VNFFGs.

Tacker will provide the support for NSD so that user can orchestrate the
collection of VNFs and network services. With NSD support, Tacker will provide
a end-to-end TOSCA based network service.

Proposed change
===============

Introduce a new template for network service which contains VNFs, connection
points and virtual links.

::

     +---------------------------------+
     |   Network Service Descriptor    |
     |                                 |
     |            +--------+           |
     |            |  VNF1  |           |
     |            +--------+           |
     |                                 |
     |            +--------+           |
     |            |  VNF2  |           |
     |            +--------+           |
     |                                 |
     |                                 |
     |                                 |
     |            +--------+           |
     |            |  VNFn  |           |
     |            +--------+           |
     |                                 |
     |          +------------+         |
     |          | End Point1 |         |
     |          +------------+         |
     |                                 |
     |          +------------+         |
     |          | End Point2 |         |
     |          +------------+         |
     |                                 |
     |          +-------------+        |
     |          |VirtualLink 1|        |
     |          +-------------+        |
     |                                 |
     |          +-------------+        |
     |          |VirtualLink 2|        |
     |          +-------------+        |
     |                                 |
     |                                 |
     |          +-------------+        |
     |          |VirtualLink m|        |
     |          +-------------+        |
     |                                 |
     +---------------------------------+

Multiple changes will be required, which includes changes to Tacker Client,
Horizon, and Server.

::

 +-------------------------------------------+
 |     +------------------+                  |
 |     |Client Application|                  |
 |     +--------+---------+                  |
 |              |                            |
 |       +------v-----+                      |
 |       |  NFVO NS   +----------------+     |
 |       |    API     |                |     |
 |       +------+-----+             +--v---+ |
 |              |                   | VNFM | |
 |              |                   +---+--+ |
 |              |                       |    |
 | +------------v-------------+     +---v-+  |
 | |Network Service Descriptor|     | VNF |  |
 | +--------------------------+     +-----+  |
 +-------------------------------------------+


*API changes*

New APIs in NFVO plugin will be introduced for NSD and NS.

*DB Changes*

New tables will be added in database for 'nsd' and
'ns'. Changes in existing 'vnfd' will be required which involves `substitution_mappings`.

*Mistral driver Changes*

A new mistral driver layer between NFVO plugin and VNFM plugin to translate
tosca template into mistral workflow and all mistral APIs to instantiate NS.
This intermediate layer will provide a co-ordination between NFVO and
Mistral. Like:

  - Generate workflow from TOSCA template.
  - Call Mistral interfaces for NS requests.
  - Wait in PENDING_CREATE state for NS until all VNFs goes to ACTIVE state.
  - Decide to move forward/backward in case of partial failure.

*TOSCA Parser Changes*

To handle nsd template, TOSCA parser should be configured. TOSCA parser will
be updated to handle VNFD, VLD and CP for network service descriptor.

::

  A sample Tosca template for VNFD is below.
  Please refer appendix section for complete template.

  node_types:
     tosca.nodes.nfv.VNF1:
      requirements:
        - virtualLink1:
          type: tosca.nodes.nfv.VL
          required: true
      capabilities:
        forwarder1:
          type: tosca.capabilities.nfv.Forwarder
  topology_template:
    substitution_mappings:
      node_type: tosca.nodes.nfv.VNF1
      requirements:
        virtualLink1: [CP11, virtualLink]
      capabilities:
        forwarder1: [CP11, forwarder]
    node_templates:
      VDU1:
        type: tosca.nodes.nfv.VDU.Tacker
                .
                .
      CP11:
        type: tosca.nodes.nfv.CP.Tacker
                .
                .
      CP12:
        type: tosca.nodes.nfv.CP.Tacker
                .
                .
      VDU2:
        type: tosca.nodes.nfv.VDU.Tacker
                .
                .
      CP13:
        type: tosca.nodes.nfv.CP.Tacker
                .
                .
      VL1:
        type: tosca.nodes.nfv.VL
                .
                .
      VL2:
        type: tosca.nodes.nfv.VL
                .
                .


  Proposed sample Tosca template for NSD:

  tosca_definitions_version:      tosca_simple_profile_for_nfv_1_0
  imports:
      - VNF1
      - VNF2
  topology_template:
    VNF1:
      type: tosca.nodes.nfv.VNF1
      requirements:
        - virtualLink1: VL1
    VNF2:
      type: tosca.nodes.nfv.VNF2
    VL1:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net_mgmt
        vendor: tacker

Regarding above template:
 * 'CP' property represents the connection points that will be exposed as part
   of VNF(mainly to support VNF forwarding graph in future).

 * For each VNF, VIM can be mentioned in properties section, otherwise pick
   the default one. In current scope, all VNF will be landed on the same VIM,
   which can be provided in input.

NOTE: The scope of this spec is to handle existing vnfd and defining APIs for NS
and support creation of NS without creating the forwarding path.


Data model impact
-----------------

Data model impact includes the creation of 'NetworkServiceTemplate', and
'NetworkService' resource model. The schema for these are as:

::

 +--------------------------+
 | nsd                      |
 +--------------------------+
 | id                       |
 | name                     |
 | type                     |
 | description              |
 | network_service_template |
 | project_id               |
 +--------------------------+

 +-----------------+
 | ns              |
 +-----------------+
 | id              |
 | name            |
 | description     |
 | nsd_id          |
 +-----------------+

There is an impact on existing vnfd resource model. A new field 'nsd_id'
will be added in vnfd for nsd. In normal VNFD list call, rows corresponding
to 'nsd_id' will be empty.

REST API impact
---------------

NSD will needs to be created to instantiate Network Services. The method of
creating NSD follows the TOSCA template scheme we mentioned in the above section.

Example CLI calls:

First create required VNFDs:

.. code-block:: console

  tacker vnfd-create vnf1 --vnfd-file samples/nsd/tosca-vnf1.yaml

  tacker vnfd-create vnf2 --vnfd-file samples/nsd/tosca-vnf2.yaml

To create NSD:

.. code-block:: console

  tacker nsd-create --name NSD1 --nsd-file samples/nsd/tosca-nsd.yaml

To create NS

.. code-block:: console

  tacker ns-create --name ns1 --nsd-name NSD1 --vim-name VIM1 --param-file <PARAM-FILE>
  --config-file <CONFIG-FILE>

Example param file:

::

 vnfs:
   VNF1:
     vdu-name: VDU1
     cp-name: CP11
 nsd:
   virtual-link: VL1

Example config file:

::

 vnfs:
   VNF1:
    ....config


**/nsd**

::

 +------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description     |
 |Name          |       |        |Value     |Conversion  |                |
 +------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity        |
 |              |(UUID) |        |          |            |                |
 +------------------------------------------------------------------------+
 |name          |string |RW, All |None      |string      |human+readable  |
 |              |       |        |(required)|            |name            |
 +------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of  |
 |              |       |        |          |            |NSD             |
 +------------------------------------------------------------------------+
 |network_servic|dict   |RW, All |None      |template/   |network service |
 |e_template    |       |        |          |dict        |template        |
 +------------------------------------------------------------------------+
 |project_id    |string |RW, All |None      |string      |project id to   |
 |              |       |        |(required)|            |launch NSD      |
 +------------------------------------------------------------------------+

 +--------------------------------------------------------------------------+
 |REST Calls  |Type  |Expected  |Request     |Response    |Description      |
 |            |      |Response  |Body Schema |Body Schema |                 |
 +--------------------------------------------------------------------------+
 |create_nsd  |post  |201       |create_req  |create_resp |Creates NSD      |
 |            |      |Created   |            |            |                 |
 +--------------------------------------------------------------------------+
 |delete_nsd  |delete|204 No    |None        |            |Deletes NSD by   |
 |            |      |Content   |            |            |name or ID       |
 +--------------------------------------------------------------------------+
 |show_nsd    |get   |200 OK    |None        |show_resp   |Returns output of|
 |            |      |          |            |            |specific NSD ID  |
 +--------------------------------------------------------------------------+
 |list_nsd    |get   |200 OK    |None        |list_resp   |Returns list of  |
 |            |      |          |            |            |NSD Names/IDs    |
 +--------------------------------------------------------------------------+

**JSON Request and Response Sample:**

POST /v1.0/nsds

* create_req:

::

    {
        "nsd": {
            "name": "NSD_demo",
            "service_types": [
                {
                    "service_type": "nsd",
                }
            ],
            "description": "Sample NSD",
            "project_id": "4dd6c1d7b6c94af980ca886495bcfed0",
            "network_service_template": {
                "nsd": "vnf1: template_name:  \r\ndescription: template_description\r\n "vnf2: template_name: OpenWRT \r\ndescription: template_description
            },
        }
    }

* create_resp:

::

    {
        "nsd": {
            "name": "NSD_demo",
            "service_types": [
                {
                    "service_type": "nsd",
                    "id": "336fe422-9fba-47c7-87fb-d48475c3e0ce"
                }
            ],
            "description": "Sample NSD",
            "project_id": "4dd6c1d7b6c94af980ca886495bcfed0",
            "network_service_template": {
                "nsd": "template_name: OpenWRT \r\ndescription:
                template_description <sample_vnfd_template>"
            },
            "id": "ab10a543-22ee-43af-a441-05a9d32a57da",
        }
    }


GET /v1.0/nsds

List nsds - List nsds stored in the catalog.

* list_res:

::

    {
        "nsds": [
            "nsd": {
                "name": "NSD_demo",
                "service_types": [
                    {
                        "service_type": "nsd",
                        "id": "336fe422-9fba-47c7-87fb-d48475c3e0ce"
                    }
                ],
                "description": "Sample NSD",
                "project_id": "4dd6c1d7b6c94af980ca886495bcfed0",
                "network_service_template": {
                    "nsd": "template_name: OpenWRT \r\ndescription:
                    template_description <sample_vnfd_template>"
                 },
                "id": "ab10a543-22ee-43af-a441-05a9d32a57da",
            }
       ]
    }

GET /v1.0/nsds/{nsd_id}

Show nsd - Show information for a specified nsd id.

* show_res:

::

    {
        "nsd": {
            "name": "NSD_demo",
            "service_types": [
                {
                    "service_type": "nsd",
                    "id": "336fe422-9fba-47c7-87fb-d48475c3e0ce"
                }
            ],
            "description": "Sample NSD",
            "project_id": "4dd6c1d7b6c94af980ca886495bcfed0",
            "network_service_template": {
                "nsd": "template_name: OpenWRT \r\ndescription:
                template_description <sample_vnfd_template>"
            },
            "id": "ab10a543-22ee-43af-a441-05a9d32a57da",
        }
    }


**/ns**

::

 +-----------------------------------------------------------------------+
 |Attribute   |Type   |Access  |Default   |Validation/ |Description      |
 |Name        |       |        |Value     |Conversion  |                 |
 +-----------------------------------------------------------------------+
 |id          |string |RO, All |generated |N/A         |identity         |
 |            |(UUID) |        |          |            |                 |
 +-----------------------------------------------------------------------+
 |name        |string |RW, All |None      |string      |human+readable   |
 |            |       |        |(required)|            |name             |
 +-----------------------------------------------------------------------+
 |description |string |RW, All |''        |string      |description of   |
 |            |       |        |          |            |NSD              |
 +-----------------------------------------------------------------------+
 |vim_id      |string |RW, All |None      |string      |VIM ID where it  |
 |            |       |        |(required)|            |launches         |
 +-----------------------------------------------------------------------+
 |project_id  |string |RW, All |None      |string      |project id to    |
 |            |       |        |(required)|            |launch NSD       |
 +-----------------------------------------------------------------------+
 |nsd_id      |string |RW, All |None      |string      |NSD id to launch |
 |            |       |        |(required)|            |                 |
 +-----------------------------------------------------------------------+
 |attributes  |dict   |RW, All |None      |dict        |dict containing  |
 |            |       |        |(required)|            |config and/or    |
 |            |       |        |          |            |param values     |
 +-----------------------------------------------------------------------+

 +-----------------------------------------------------------------------+
 |REST Calls |Type  |Expected  |Body Data |Response   |Description       |
 |           |      |Response  |Schema    |Body Schema|                  |
 +-----------------------------------------------------------------------+
 |create_ns  |post  |202       |schema 1  |           |Creates NSD       |
 |           |      |Accepted  |          |           |                  |
 +-----------------------------------------------------------------------+
 |delete_ns  |delete|202       |None      |           |Deletes NSD by    |
 |           |      |Accepted  |          |           |name or ID        |
 +-----------------------------------------------------------------------+
 |show_ns    |get   |200 OK    |None      |           |Returns output of |
 |           |      |          |          |           |specific NSD ID   |
 |           |      |          |          |           |                  |
 +-----------------------------------------------------------------------+
 |list_ns    |get   |200 OK    |None      |           |Returns list of   |
 |           |      |          |          |           |NSD Names/IDs     |
 +-----------------------------------------------------------------------+



Security impact
---------------

Notifications impact
--------------------

None

Other end user impact
---------------------

Performance Impact
------------------
None

Other deployer impact
---------------------


Developer impact
----------------
*Using Mistral workflow for nsd:*

Use Mistral workflow for nsd feature. Tacker NFVO will generate Mistral
workflow through workflow generator and call to Mistral for generated
workflow request. Mistral will create the resources(VNFs, FFG) and respond
to NFVO.

::

 +-------------------------------------------+
 |     +------------------+                  |
 |     |Client Application|                  |
 |     +--------+---------+                  |
 |              |            +-------------+ |
 |        +-----v----+       |  Workflow   | |
 |        | NFVO:NSD +------->  Generator  | |
 |        +-----+----+       +---------+---+ |
 |              |                      |     |
 | +------------v-------------+   +----v---+ |
 | |Network Service Descriptor|   | Mistral| |
 | +--------------------------+   +----+---+ |
 |                                     |     |
 |                                 +---v--+  |
 |                                 | VNFM |  |
 |                                 +------+  |
 +-------------------------------------------+


Pros:
  1: Workflow can already handle multiple cases.
  2: In case of failure at any point of time, rollback possible.
  3: I think implementation of nsd like feature by using mistral
  workflow should be easy.
  4: After embading mistral with Tacker, any workflow or other already coded
  such remediation  will be in the reach of Tacker.
Cons:
  Mistral as third Component:
    1: As the Mistral is third components, so:
      * Any changes in mistral may impact the nsd flow.
      * Sometimes in case of compatibility or other issues may
        be we needs to work with Mistral team.
      * Mistral takes json file in input, so first we needs to create
        these json data. In case of large number of VNFDs, multiple
        files will be created. Needs to handle these creation/cleanup.
        (an investigation in this part required)
      * For an ns call:
          tacker --> Mistral --> tackerClient --> tacker
          Multiple context switching leads time consuming.

    2: An auto-generated workflow can be error prone, should be more
       careful while creating mistral workflow to handle corner cases.

    3: We have to generate workflow for each resource in nsd
       template(i.e . vnfd/vnf) which might be complex in case of
       large number of vnfs etc.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Dharmendra Kushwaha

Other contributors:
  Bharath Thiruveedula <bharath_ves@hotmail.com>

Work Items
----------

 * New APIs in NFVO plugin for NSD and NS
 * NFVO plugin side implementation.
 * Tacker DB configuration for 'NetworkServiceTemplate' and 'NetworkService'.
 * TOSCA parser support for NSD.
 * Mapping of TOSCA node to workflow task.
 * Workflow generator: TOSCA parser will iterate through the each nodes in
   template and then convert them into tasks.
 * Calls from NFVO-NSD plugin to Mistral to instantiate NS.
 * Logic to wait in PENDING_CREATE state for NS until all VNFs goes to
   ACTIVE state
 * Logic to take parameters at NS level and pass it onto VNFs
 * Changes for in tacker-horizon and python-tackerclient for NSD.
 * Documentation to explain NSD support feature.
 * Unit test cases
 * Functional test cases



Dependencies
============

None

Testing
=======
Unit testing
------------

Unit tests will be added for new interfaces. New test cases will be introduced
in VNFM for the related extensions.

Functional testing
------------------
Functional tests will be added to check the deployed state of all the VNFs.

Documentation Impact
====================

User Documentation
------------------

User documentation will describe the NSD features, operations with
samples. Python-tackerclient and tacker-horizon side documentation will
be added to describe cli/interface details.

Developer documentation
-----------------------

Add developer documentation for the api and usage details

References
==========
 * https://review.opendev.org/#/q/status:open+project:openstack/tacker+branch:master+topic:bp/nsd-support
 * http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf
 * http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/csd02/tosca-nfv-v1.0-csd02.html#_Toc433298703
 * http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/csd02/tosca-nfv-v1.0-csd02.html#_Toc433298756

Appendix
========
TOSCA sample vnf1
-----------------

::

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

  description: Demo example
    node_types:
    tosca.nodes.nfv.VNF1:
      requirements:
        - virtualLink1:
            type: tosca.nodes.nfv.VL
            required: true
        - virtualLink2:
            type: tosca.nodes.nfv.VL
            required: true
      capabilities:
        forwader1:
            type: tosca.capabilities.nfv.Forwarder
        forwader2:
            type: tosca.capabilities.nfv.Forwarder

  topology_template:
    substitution_mappings:
      node_type: tosca.nodes.nfv.VNF1
      requirements:
        virtualLink1: [CP11, virtualLink]
        virtualLink2: [CP14, virtualLink]
      capabilities:
        forwarder1: [CP11, forwarder]
        forwarder2: [CP14, forwarder]

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

      CP11:
        type: tosca.nodes.nfv.CP.Tacker
        properties:
          management: true
          anti_spoofing_protection: false
        requirements:
          - virtualBinding:
              node: VDU1
          - virtualLink:
              node: VL1

      CP12:
        type: tosca.nodes.nfv.CP.Tacker
        properties:
          anti_spoofing_protection: false
        requirements:
          - virtualLink:
              node: VL2
          - virtualBinding:
              node: VDU1

      VDU2:
        type: tosca.nodes.nfv.VDU.Tacker
        properties:
          image: cirros-0.3.4-x86_64-uec
          flavor: m1.medium
          availability_zone: nova
          mgmt_driver: noop
          config: |
            param0: key1
            param1: key2

      CP13:
        type: tosca.nodes.nfv.CP.Tacker
        properties:
          management: true
        requirements:
          - virtualLink:
              node: VL1
          - virtualBinding:
              node: VDU2

      CP14:
        type: tosca.nodes.nfv.CP.Tacker
        requirements:
          - virtualBinding:
              node: VDU2

      VL1:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: net_mgmt
          vendor: Tacker

      VL2:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: net0
          vendor: Tacker

TOSCA sample vnf2
-----------------

::

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

  description: Demo example

  node_types:
    tosca.nodes.nfv.VNF2:
      capabilities:
        forwarder1:
            type: tosca.capabilities.nfv.Forwarder
  topology_template:
    substitution_mappings:
      node_type: tosca.nodes.nfv.VNF2
      capabilities:
        forwarder1: [CP21, forwarder]
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

      CP21:
        type: tosca.nodes.nfv.CP.Tacker
        properties:
          management: true
          anti_spoofing_protection: false
        requirements:
          - virtualLink:
              node: VL1
          - virtualBinding:
              node: VDU1

      VDU2:
        type: tosca.nodes.nfv.VDU.Tacker
        properties:
          image: cirros-0.3.4-x86_64-uec
          flavor: m1.medium
          availability_zone: nova
          mgmt_driver: noop
          config: |
            param0: key1
            param1: key2

      CP22:
        type: tosca.nodes.nfv.CP.Tacker
        requirements:
          - virtualLink:
              node: VL2
          - virtualBinding:
              node: VDU2

      VL1:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: net_mgmt
          vendor: Tacker

      VL2:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: net0
          vendor: Tacker


TOSCA sample nsd template
-------------------------

::

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
  imports:
      - VNF1
      - VNF2

  topology_template:
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
            network_name: net_mgmt
            vendor: tacker

TOSCA sample nsd params
-----------------------

::

  vnfs:
    vnf1:
      vdus:
        vdu1:
          param:
            vdu-name: ns-test-vdu11
        vdu2:
          param:
            vdu-name: ns-test-vdu12
        cp11:
          param:
            cp-name: ns-test-cp11
        cp12:
          param:
            cp-name: ns-test-cp12

    vnf2:
      vdus:
        vdu1:
          param:
            vdu-name: ns-test-vdu21
        vdu2:
          param:
            vdu-name: ns-test-vdu22
        cp21:
          param:
            cp-name: ns-test-cp21
        cp22:
          param:
            cp-name: ns-test-cp22
