..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


=====================================
Implement Tacker VNF Forwarding Graph
=====================================

https://blueprints.launchpad.net/tacker/+spec/tacker-vnffg

This spec describes the plan to introduce VNF Forwarding Graph
(VNFFG) capability into Tacker.  In its current state, Tacker allows for
managing VNFs; the purpose of this spec is to also include managing network
traffic through paths of ordered VNFs.

Problem description
===================

There is a large desire from the NFV community to be able to orchestrate and
manage traffic through VNFs, also known as Service Function Chaining (SFC)
[#first]_.  A user of NFV would not only like to be able to create VNFs, but
also define SFCs to direct traffic between VNFs.  In the ETSI MANO context
[#tenth]_ a SFC construct is part of a larger graph of VNFs (VNFFG) which
defines how VNFs are connected in a graph and the network traffic paths
which flow through the graph.

The goal is to be able to define a graph in orchestration via a logical and
abstract construct, while being able to render that graph down to the overlay
network as SFCs.  The next step is to be able to classify tenant traffic that
should flow through that SFC.  The combination of VNFs, SFC, and the
classification of traffic to flow through them is described as the VNF
Forwarding Graph (VNFFG).

A VNFFG can be complex with multiple paths through the graph.  Today the
SFC implementations that Tacker VNFFG will rely on to render a graph are
only capable of creating single-path SFCs.  In order to solve this problem,
Tacker VNFFG can be made capable to parse a multi-path graph into several
single-path SFCs to create the larger VNFFG.  This feature can be thought
of as "chain optimization" by gathering info about all of the defined paths
through the graph, and breaking up common pieces of path into single chains.
This is a key part of VNFFG orchestration, but will be handled as a follow
up spec due to the complexity of logic required to orchestrate and manage
such a task. This spec addresses the changes to Tacker necessary to
orchestrate full paths through a VNFFG using single SFCs.

In addition, a VNF may also be able to re-classify traffic once inside of
the graph.  For example, a VNF capable of L7 Deep Packet Inspection (DPI)
determines from packet payload that the next path through the graph should be
modified.  To implement such a feature there would need to be some type of
coordination between VNFM and a Network Service (NS) extension, and is
beyond the scope of this VNFFG specification (but may integrate with such a
feature in a future spec).

Proposed change
===============

The high-level changes needed to Tacker in order to accommodate this new
feature will include changes to Tacker Client, Horizon, and Server.  Changes
include:

* Add an VNFFG tab to tacker-horizon where a user can create a graph from
  already created VNFs, as well as a Classification sub-tab to declare traffic
  into the graph.  These inputs can be implemented in multiple ways, including
  (1) a TOSCA VNF Forwarding Graph Descriptor (VNFFGD) [#ninth]_, as well as
  (2) a simple drop down menu of chaining VNFs in order and then defining
  classification schemes for tenants.  VNFFG describes network functions and
  how they are connected via yaml templates as input [#ninth]_.  This is
  similar to how VNFDs already work in Tacker VNFM.  This spec proposes to
  implement VNFFG creation via (1) as a first priority.

* Tacker Client will also need similar changes to allow passing the CRUD VNFFG
  calls to Tacker Server.

* Tacker Server will need updates to the NFVO extension and plugin in order
  to integrate VNFFG resources and functionality.

* Drivers for 'vnffg' will need to be written.  The known drivers to
  create SFCs are networking-sfc [#fourth]_ (Neutron based SFC) and
  OpenDaylight SFC [#fifth]_.  The driver that will be supported for the
  VNFFG plugin will be the networking-sfc driver [#eleventh]_.  The
  OpenDaylight functionality and driver will be addressed as a separate spec
  in the networking-sfc project as a driver to networking-sfc.  The
  networking-sfc driver will handle both: SFC and Classification CRUD
  operations.

::

    +---------------------------------------------+
    |              Client Application             |
    +-----------+---------------------+-----------+
                | Tacker VNFFG API    | Tacker VNFM API
    +-----------|---------------------|-----------+
    |           v                     v           |
    |  +-----------------+    +----------------+  |
    |  |      Tacker     |    |    Tacker      |  |
    |  | NFVO Extension  |<-->| VNFM Extension |  |
    |  |   Plugin/DB     |    |   Plugin       |  |
    |  +--------+--------+    +----------------+  |
    |           |                                 |
    |         +==========================+        |
    |         |     networking-sfc       |        |
    |         |     Port Chain Driver    |        |
    |         +==========================+        |
    | Tacker Server        |                      |
    +----------------------|----------------------+
                           | Port Chain API
    +----------------------|----------------------+
    | Neutron Server       v                      |
    |            +-------------------+            |
    |            | networking-sfc    |            |
    |            | Port Chain Plugin |            |
    |            +-------------------+            |
    +---------------------------------------------+

Alternatives
------------

None

Data model impact
-----------------

Data model impact includes the creation of 'vnffgd', 'vnffgd_nfp', 'vnffg',
'vnffg_nfp', 'vnffg_chain' and 'vnffg_classifier' tables.  The 'vnffgd'
table will hold all of the currently defined VNFFGD templates as defined by
TOSCA, while the associated table 'vnffgd_nfp' will hold the Network
Forwarding Paths (NFP) associated with that VNFFGD.

The 'vnffg' table will hold relevant VNFFG instance creation attributes,
along with associated NFPs held in the 'vnffg_nfp' table and references to
the associated SFC and classifier created in the 'vnffg_chain' and
'vnffg_classifier' tables.  Another table 'acl_match_criteria' will hold the
entries of match criteria mapped to the classifier created in
'vnffg_classifier'.

In VNFM the VNFD template will need to add the following TOSCA properties:

.. code-block:: yaml

  tosca.nodes.nfv.VNF:
    properties:
      nsh_aware:
        type: boolean
        required: false
        description: Does this VNF support IETF NSH

  tosca.nodes.nfv.CP:
    properties:
      sfc_encapsulation:
        type: string
        required: false
        description: Identifies the method of encapsulation for NSH/SFC
        constraints:
          - [vxlan_gpe, ethernet, mpls]

These properties will allow the VNFFG to indicate to the SFC provider if the
VNF is Network Service Header (NSH) [#first]_ aware and what encapsulation to
use in transporting the packet.  NSH is an IETF protocol which passes
information about a SFC hop by hop.  The NSH header is added to each packet
which traverses the chain, and holds properties about that chain so that when
a packet arrives at the next VNF in the chain, the VNF is able to determine
which chain that packet belongs to, and some idea about how many nodes in the
chain the packet has traversed previously.

REST API impact
---------------

VNFFGD will need to be created in order to instantiate VNFFGs.  The method
of creating VNFFGD follows the TOSCA template scheme.  The format will
require one or more VNFFGs defined in Groups along with one or more
associated "Forwarding_paths".  Example:

.. code-block:: yaml

  Forwarding_path1:
    type: tosca.nodes.nfv.FP
    id: 51
    description: creates path (CP11->CP12->CP32)
    properties:
      policy:
        type: ACL
        criteria:
          - neutron_net_name: tenant1_net
          - dest_port_range: 80-1024
          - ip_proto: tcp
          - ip_dest: 192.168.1.2
    requirements:
      - forwarder: VNF1
        capability: CP11
      - forwarder: VNF1
        capability: CP12
      - forwarder: VNF3
        capability: CP32

  groups:
    VNFFG1:
      type: tosca.groups.nfv.VNFFG
      description: HTTP to Corporate Net
      properties:
        vendor: tacker
        version: 1.0
        number_of_endpoints: 5
        dependent_virtual_link: [VL1,VL2,VL3]
        connection_point: [CP11,CP12,CP32]
        constituent_vnfs: [VNF1,VNF3]
      members: [Forwarding_path1]


VNFs, Connection Points (CPs) and Virtual Links (VLs) are described the VNFD
template.  Due to this dependency, to validate a VNFFGD the VNFD templates
need to be created first.  In TOSCA the VL should actually be defined in the
Network Service (NS) template, as well as the VNF itself as an abstract
construct.  In addition, the TOSCA specification defines a "capability"
object for each abstract VNF which resolves via substitution mappings to a
specific CP (which is exposed as a VNF external type CP).  The
combination of the capability object and abstract VNF object make up
the "forwarders" in an Network Forwarding Path (NFP).  However, the NS
is outside of the scope of this spec and will be addressed as a follow up
specification.  Therefore this spec takes the more simple and direct
approach to define a path "forwarder" as a CP associated to a VNFD name.  The
"forwarder" key listed in the above yaml specifies the VNFD name, while the
"capability" key references the external CP for that VNF.

The basic method of VNFFG creation will be accomplished by instantiating a
created VNFFGD.  The default behavior of VNFFG creation will rely on
selecting abstract VNF types.  The VNFFGD contains one or more NFPs, each
containing a list of forwarders used in the path.  The "forwarder" in
requirements references a VNFD name to be used in the path.  At VNFFG creation
time, the NFVO plugin will query VNFM to find available VNF instances that
exist from the corresponding VNFDs for each NFP.  For the first
iteration of this spec the selection algorithm to choose which VNF to use if
more than one exist for a given VNFD will be random, but may be enhanced in
a future spec.  VNFs will be allowed to be part of multiple paths, but are not
allowed to be part of multiple VNFFGs.  The ability to specify the VNF
instances (already created via VNFM) to use in the graph can be done by using
the '--vnf-mapping' argument.  This argument will map
<VNFD>:<VNF Instance ID/NAME>.  For example, if using the above
"Forwarding_path1" yaml input as an example, it contains VNF1 and VNF3 VNFDs.
Therefore if there were two instances spawned from those VNFDs, VNF1Test and
VNF3Test, the argument would look like
'--vnf-mapping VNF1:VNF1Test,VNF3:VNF3Test' in order to indicate to NFVO to
specifically use those VNF instances (rather than searching).

The possibility of being able to automatically spawn a non-existent VNF
instance of a desired type (that matches an existing VNFD) is outside the
scope of this spec, but may be supported later by an additional
spec for a NS extension.

The Forwarding Path element (nfv.FP) of the TOSCA input defines a path
through the graph.  A VNFFGD can contain multiple paths (NFPs) through a
VNFFG.  Multiple NFPs are associated with a VNFFG by listing it as a target
in the VNFFG definition.  The initial implementation of this spec will focus
on creating a single chain and classifier per path.  As previously mentioned
this functionality could evolve to optimize common paths through a graph
into consolidated chains, but that is outside the scope of this initial spec.
The classifier for a path is defined as a policy as shown in the example
above, while the chain is listed under requirements.  The CPs in the
requirements map to a virtual port that must be defined in the VNFD for the
specified forwarder.  The CP must be defined as having 'forwarding' capability
to be part of the chain.  The logical CP in a VNFD will map to a Neutron port
for the VNF instance.  VNFFG will query VNFM to GET the neutron-port ID for a
given CP.  VNFM will then invoke it's Heat driver to find the information.
This will be new behavior and change needed to VNFM.  If a single CP is
provided per VNF in the Forwarding Path, then it will be considered to be the
ingress and egress port for that VNF.  If two ordinal CPs are provided per VNF
in the Forward Path, then the first will be interpreted to be the ingress port
to the VNF, while the second is the egress.

An additional argument, '--symmetrical', will automatically create reverse
paths for the paths listed as targets in the VNFFG.  The reverse path
alternatively may be defined in the VNFFGD, but as a convenience factor
--symmetrical may be used instead.

Example CLI calls:

To create VNFFGD:

.. code-block:: console

  tacker vnffgd-create --name VNFFG1 --vnffgd-file ./test-vnffgd.yaml

  tacker vnffgd-create --name VNFFG1 --vnffgd <raw vnffgd TOSCA>

To create VNFFG (where testVNF1, and testVNF2 are VNF instances):

.. code-block:: console

  tacker vnffg-create --name myvnffg --vnfm_mapping VNF1:testVNF2,
  VNF2:testVNF1 --symmetrical True --vnffgd-name VNFFG1

  tacker vnffg-create --name myvnffg --vnfm_mapping VNF1:testVNF2,
  VNF2:testVNF1 --symmetrical True --vnffgd-id
  65056908-1946-11e6-b6ba-3e1d05defe78

To list forwarding paths for the vnffg, which will list associated chains
and classifiers:

.. code-block:: console

  tacker vnffg-show myvnffg

::

 +--------------------+-------------------------------------------------------+
 | Field              | Value                                                 |
 +--------------------+-------------------------------------------------------+
 | forwarding_paths   | Forwarding_path1                                      |
 | id                 | 19233232-d3e2-4c47-a94d-d1b1ab9889e5                  |
 | name               | myvnffg                                               |
 | tenant_id          | 0b324885958c42ad939e7d636abe2352                      |
 | vnffgd_id          | 5279690a-2153-11e6-b67b-9e71128cae77                  |
 | vnf_mapping        | [{VNFD1:testVNF1}, {VNFD2:testVNF2}]                  |
 | status             | ACTIVE                                                |
 +--------------------+-------------------------------------------------------+

To see the associated chains and classifiers to a specific forwarding path:

.. code-block:: console

  tacker vnffg-show myvnffg --nfp Forwarding_path1

::

 +--------------------+-------------------------------------------------------+
 | Field              | Value                                                 |
 +--------------------+-------------------------------------------------------+
 | chain_id           | b8ad61b1-5fac-48ab-9231-dc7d5de6ad4d                  |
 | classifier_id      | 0a52a0d9-2a1f-4019-94c3-5401c4af5d36                  |
 | id                 | 19233232-d3e2-4c47-a94d-d1b1ab9889e5                  |
 | name               | Forwarding-path1                                      |
 | tenant_id          | 0b324885958c42ad939e7d636abe2352                      |
 | path_id            | 200                                                   |
 | symmetrical        | false                                                 |
 | vnffg_id           | 19233232-d3e2-4c47-a94d-d1b1ab9889e5                  |
 +--------------------+-------------------------------------------------------+

To show the chain itself:

.. code-block:: console

  tacker vnffg-show --sfc b8ad61b1-5fac-48ab-9231-dc7d5de6ad4d

::

 +--------------+--------------------------------------+
 | Field        | Value                                |
 +--------------+--------------------------------------+
 | chain        | 0a52a0d9-2a1f-4019-94c3-5401c4af5d36 |
 | id           | b8ad61b1-5fac-48ab-9231-dc7d5de6ad4d |
 | path_id      | 181                                  |
 | nfp_id       | 19233232-d3e2-4c47-a94d-d1b1ab9889e5 |
 | status       | PENDING_CREATE                       |
 | symmetrical  | False                                |
 | tenant_id    | 0b324885958c42ad939e7d636abe2352     |
 +--------------+--------------------------------------+

To show the classifier itself:

.. code-block:: console

  tacker vnffg-show --classifier 0a52a0d9-2a1f-4019-94c3-5401c4af5d36

::

 +--------------------+-------------------------------------------------------+
 | Field              | Value                                                 |
 +--------------------+-------------------------------------------------------+
 | acl_match_criteria | {"source_port": 2005, "protocol": 6, "dest_port": 80} |
 | chain_id           | b8ad61b1-5fac-48ab-9231-dc7d5de6ad4d                  |
 | id                 | 0a52a0d9-2a1f-4019-94c3-5401c4af5d36                  |
 | nfp_id             | 19233232-d3e2-4c47-a94d-d1b1ab9889e5                  |
 | status             | PENDING_CREATE                                        |
 | tenant_id          | 0b324885958c42ad939e7d636abe2352                      |
 +--------------------+-------------------------------------------------------+

**/vnffgd**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RW, All |None      |string      |human+readable      |
 |              |       |        |(required)|            |name                |
 +----------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of      |
 |              |       |        |          |            |VNFFGD              |
 +----------------------------------------------------------------------------+
 |attributes    |dict   |RW, All |None      |template/   |VNFFGD template     |
 |              |       |        |          |dict        |                    |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RW, All |None      |string      |project id to       |
 |              |       |        |(required)|            |launch VNFFGD       |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |create_vnffgd |post  |200 OK    |schema 1   |Creates VNFFGD                 |
 |              |      |          |           |                               |
 +----------------------------------------------------------------------------+
 |delete_vnffgd |delete|200 OK    |None       |Deletes VNFFG by name or ID    |
 |              |      |          |           |                               |
 +----------------------------------------------------------------------------+
 |show_vnffgd   |get   |200 OK    |None       |Returns output of specific     |
 |              |      |          |           |VNFFG ID, including associated |
 |              |      |          |           |chains and classifiers         |
 +----------------------------------------------------------------------------+
 |list_vnffgds  |get   |200 OK    |None       |Returns list of configured     |
 |              |      |          |           |VNFFGD Names/IDs               |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |create_vnffgd |post  |404 Not   |VNFD does not    |Declared VNFD in an NFP  |
 |              |      |Found     |exist            |specified in VNFFGD      |
 |              |      |          |                 |does not exist           |
 +----------------------------------------------------------------------------+
 |create_vnffgd |post  |404 Not   |Connection Point |Specified CP does not    |
 |              |      |Found     |for VNF does not |exist for defined VNFD   |
 |              |      |          |exist            |in NFP                   |
 +----------------------------------------------------------------------------+
 |create_vnffgd |post  |409       |Connection Point |CP defined in VNFFGD     |
 |              |      |Conflict  |does not have    |maps to a VNFD, but lacks|
 |              |      |          |forwarding       |forwarding capability    |
 |              |      |          |capability       |                         |
 +----------------------------------------------------------------------------+
 |delete_vnffgd |delete|403       |VNFFG Create     |VNFFG already being      |
 |              |      |Forbidden |in progress      |created by a request     |
 +----------------------------------------------------------------------------+



**/vnffg**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RW, All |None      |string      |human+readable      |
 |              |       |        |(required)|            |name                |
 +----------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of      |
 |              |       |        |          |            |VNFFG               |
 +----------------------------------------------------------------------------+
 |vnffgd_id     |string |RO, All |None      |uuid        |VNFFGD to use to    |
 |              |(UUID) |        |(required)|            |create this VNFFG   |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RW, All |None      |string      |project id to       |
 |              |       |        |(required)|            |launch VNFFG        |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of VNFFG            |
 +----------------------------------------------------------------------------+
 |vnf_mapping   |list   |RW, All |None      |list        |Mapping of VNFD name|
 |              |       |        |          |            |to VNF instances to |
 |              |       |        |          |            |use in VNFFG        |
 +----------------------------------------------------------------------------+
 |forwarding_   |list   |RO, All |None      |list        |List of associated  |
 |paths         |       |        |          |            |NFPs                |
 +----------------------------------------------------------------------------+


 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |create_vnffg  |post  |200 OK    |schema 1   |Creates VNFFG and triggers     |
 |              |      |          |           |underlying chain and           |
 |              |      |          |           |classifier creation            |
 +----------------------------------------------------------------------------+
 |update_vnffg  |put   |200 OK    |schema 1   |Updates VNFFG by name or ID    |
 |              |      |          |           |                               |
 +----------------------------------------------------------------------------+
 |delete_vnffg  |delete|200 OK    |None       |Deletes VNFFG by name or ID    |
 |              |      |          |           |                               |
 +----------------------------------------------------------------------------+
 |show_vnffg    |get   |200 OK    |None       |Returns output of specific     |
 |              |      |          |           |VNFFG ID, including associated |
 |              |      |          |           |chains and classifiers         |
 +----------------------------------------------------------------------------+
 |list_vnffgs   |get   |200 OK    |None       |Returns list of configured     |
 |              |      |          |           |VNFFG Names/IDs                |
 +----------------------------------------------------------------------------+


 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |create_vnffg  |post  |404 Not   |VNF does not     |No VNFs exist with       |
 |              |      |Found     |exist            |declared instance when   |
 |              |      |          |                 |using vnf_mapping        |
 +----------------------------------------------------------------------------+
 |create_vnffg  |post  |500       |Failed to create |Failed to create         |
 |              |      |Internal  |SFC              |chain with underlying    |
 |              |      |Server    |                 |driver                   |
 |              |      |Error     |                 |                         |
 +----------------------------------------------------------------------------+
 |create_vnffg  |post  |500       |Failed to create |Failed to create         |
 |              |      |Internal  |Classifier       |classifier with          |
 |              |      |Server    |                 |underlying driver        |
 |              |      |Error     |                 |                         |
 +----------------------------------------------------------------------------+
 |update_vnffg  |put   |404 Not   |VNFFG does not   |No VNFFG exists with     |
 |              |      |Found     |exist            |provided Name/ID         |
 +----------------------------------------------------------------------------+
 |delete_vnffg  |delete|403       |VNFFG Update     |VNFFG already being      |
 |              |      |Forbidden |in progress      |updated by a request     |
 +----------------------------------------------------------------------------+

Allow a user to access and show the nfp resource for a vnffg:
**/vnffg/nfp**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RO, All |''        |string      |human+readable      |
 |              |       |        |          |            |name                |
 +----------------------------------------------------------------------------+
 |vnffg_id      |string |RO, All |generated |uuid        |Associated VNFFG ID |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RO, All |None      |string      |project id to       |
 |              |       |        |(required)|            |for this NFP        |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of the NFP          |
 +----------------------------------------------------------------------------+
 |classifier_id |string |RO, All |None      |string      |ID of associated    |
 |              |       |        |          |            |classifier          |
 +----------------------------------------------------------------------------+
 |chain_id      |string |RO, All |None      |string      |ID of associated    |
 |              |       |        |          |            |chain               |
 +----------------------------------------------------------------------------+
 |path_id       |integer|RO, All |nfv.FP ID |string      |Path ID described   |
 |              |       |        |          |            |in VNFFGD           |
 +--------------+-------+--------+----------+---------------------------------+
 |symmetrical   |bool   |RO, All |True      |bool        |Path allows         |
 |              |       |        |          |            |reverse traffic     |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |show_nfp      |get   |200 OK    |None       | Returns output of specific    |
 |              |      |          |           | forwarding_path for a VNFFG   |
 +----------------------------------------------------------------------------+
 |list_nfps     |get   |200 OK    |None       |Returns list of configured     |
 |              |      |          |           |NFPs fora specific VNFFG       |
 +----------------------------------------------------------------------------+
 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |show_nfp      |get   |404 Not   |Instance         |No NFP exists            |
 |              |      |Found     |Not Found        |with provided Name/ID    |
 |              |      |          |                 |provided Name/ID         |
 +----------------------------------------------------------------------------+

Allow a user to access and show the chain resource as it was rendered:
**/vnffg/chain**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RO, All |None      |string      |project id to       |
 |              |       |        |(required)|            |launch SFC          |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of SFC              |
 +----------------------------------------------------------------------------+
 |symmetrical   |bool   |RO, All |True      |bool        |Chain allows        |
 |              |       |        |          |            |reverse traffic     |
 +----------------------------------------------------------------------------+
 |chain         |list   |RO, All |None      |list        |SFC Chain as list of|
 |              |       |        |          |            |ordered VNF name/IDs|
 +----------------------------------------------------------------------------+
 |path_id       |integer|RO, All |generated |string      |NFP/SFC Path ID     |
 |              |       |        |          |            |(e.g. NSH SPI)      |
 +--------------+-------+--------+----------+---------------------------------+
 |nfp_id        |string |RO, All |None      |string      |Associated NFP      |
 |              |(UUID) |        |          |            |ID                  |
 +--------------+-------+--------+----------+---------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |show_chain    |get   |200 OK    |None       | Returns output of specific    |
 |              |      |          |           | chain                         |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |show_chain    |get   |404 Not   |Instance         |No chain exists          |
 |              |      |Found     |Not Found        |with provided Name/ID    |
 |              |      |          |                 |provided Name/ID         |
 +----------------------------------------------------------------------------+

Allow a user access and show the classifier information as it was rendered:
**/vnffg/classifier**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RO, All |None      |string      |project id to       |
 |              |       |        |(required)|            |create Classifier   |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of Classifier       |
 +----------------------------------------------------------------------------+
 |match         |dict   |RO, All |True      |acl_dict    |Match criteria      |
 |              |       |        |          |            |(see supported list)|
 +----------------------------------------------------------------------------+
 |chain_id      |string |RO, All |None      |string      |SFC Chain to        |
 |              |(UUID) |        |          |(UUID)      |classify on         |
 +----------------------------------------------------------------------------+
 |nfp_id        |string |RO, All |None      |string      |Associated NFP      |
 |              |(UUID) |        |          |            |ID                  |
 +--------------+-------+--------+----------+---------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |show_         |get   |200 OK    |None       | Returns output of specific    |
 |classifier    |      |          |           | classifier                    |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |show_         |get   |404 Not   |Instance         |No classifier exists     |
 |classifier    |      |Found     |Not Found        |with provided Name/ID    |
 |              |      |          |                 |provided Name/ID         |
 +----------------------------------------------------------------------------+

**Schema Definitions:**

* Schema 1: This schema describes a typical body for VNFFG SFC request:

::

  {u'vnffg': {u'attributes': {vnffgd: <VNFFGD>}, u'name': u'test_vnffg',
    u'vnf_mapping': {u'VNF1': u'c0f0500e-4dc4-4321-a188-40a6ecfea0ea',
    u'VNF2': u'9d1c6854-bb71-4a99-934d-7bef3222d0bb'}, u'symmetrical':
    u'True'}}

**Classifier Match Criteria:**

Supported list of matching attributes for classification are listed below.
These are used as key=value pairs in a "match" list specified in schema 2.  The
match criteria supported by OpenDaylight includes IETF ACL model [#sixth]_.  In
addition, networking-sfc project has passed the supported Classifier match
criteria listed in the corresponding spec [#seventh]_.  Tacker SFC Classifier
will aggregate the two into these supported attributes.  There should be at
least one match criteria attribute specified when creating/updating a
classifier from the following available attributes:

::

 +----------------------------------------------+
 |Attribute     |Description                    |
 |              |                               |
 +----------------------------------------------+
 |eth_type      |Specifies Ethernet frame type  |
 |              |See IEEE 802.3                 |
 +----------------------------------------------+
 |eth_src       |Ethernet source address        |
 |              |                               |
 +----------------------------------------------+
 |eth_dst       |Ethernet destination address   |
 |              |                               |
 +----------------------------------------------+
 |vlan_id       |VLAN ID                        |
 |              |                               |
 +----------------------------------------------+
 |vlan_pcp      |VLAN Priority                  |
 |              |                               |
 +----------------------------------------------+
 |mpls_label    |MPLS Label                     |
 |              |                               |
 +----------------------------------------------+
 |mpls_tc       |MPLS Traffic Class             |
 |              |                               |
 +----------------------------------------------+
 |ip_dscp       |IP DSCP (6 bits in ToS field)  |
 |              |                               |
 +----------------------------------------------+
 |ip_ecn        |IP ECN (2 bits in ToS field)   |
 |              |                               |
 +----------------------------------------------+
 |ip_src_prefix |IP source address prefix       |
 |              |                               |
 +----------------------------------------------+
 |ip_dst_prefix |IP destination address prefix  |
 |              |                               |
 +----------------------------------------------+
 |ip_proto      |IP protocol number or name     |
 |              |                               |
 +----------------------------------------------+
 |tcp_src       |Source TCP port range          |
 |              |                               |
 +----------------------------------------------+
 |tcp_dest      |Destination TCP port range     |
 |              |                               |
 +----------------------------------------------+
 |udp_src       |Source UDP port range          |
 |              |                               |
 +----------------------------------------------+
 |udp_dest      |Destination UDP port range     |
 |              |                               |
 +----------------------------------------------+
 |sctp_src      |SCTP source port               |
 |              |                               |
 +----------------------------------------------+
 |sctp_dest     |SCTP destination port          |
 |              |                               |
 +----------------------------------------------+
 |icmpv4_type   |ICMP type                      |
 |              |                               |
 +----------------------------------------------+
 |icmpv4_code   |ICMP code                      |
 |              |                               |
 +----------------------------------------------+
 |arp_op        |ARP opcode                     |
 |              |                               |
 +----------------------------------------------+
 |arp_spa       |ARP source ipv4 address        |
 |              |                               |
 +----------------------------------------------+
 |arp_tpa       |ARP target ipv4 address        |
 |              |                               |
 +----------------------------------------------+
 |arp_sha       |ARP source hardware address    |
 |              |                               |
 +----------------------------------------------+
 |arp_tha       |ARP target hardware address    |
 |              |                               |
 +----------------------------------------------+
 |ipv6_src      |IPv6 source address            |
 |              |                               |
 +----------------------------------------------+
 |ipv6_dst      |IPv6 destination address       |
 |              |                               |
 +----------------------------------------------+
 |ipv6_flabel   |IPv6 Flow Label                |
 |              |                               |
 +----------------------------------------------+
 |icmpv6_type   |ICMPv6 type                    |
 |              |                               |
 +----------------------------------------------+
 |icmpv6_code   |ICMPv6 code                    |
 |              |                               |
 +----------------------------------------------+
 |ipv6_nd_target|Target address for ND          |
 |              |                               |
 +----------------------------------------------+
 |ipv6_nd_sll   |Source link-layer for ND       |
 |              |                               |
 +----------------------------------------------+
 |ipv6_nd_tll   |Target link-layer for ND       |
 |              |                               |
 +----------------------------------------------+
 |neutron_src   |Neutron source port            |
 |_port         |                               |
 +----------------------------------------------+
 |neutron_dst   |Neutron destination port       |
 |_port         |                               |
 +----------------------------------------------+
 |tenant_id     |OpenStack Tenant ID            |
 |              |                               |
 +----------------------------------------------+
 |neutron_net   |Neutron Network ID             |
 |_id           |                               |
 +----------------------------------------------+

Note: OpenDaylight is able to classify based on tenant_id and neutron_net_id.
This means that it is possible to create classifiers that match more than one
tenant.  Networking-sfc relies on Role Based Access Control (RBAC) to share
Classifiers across tenants [#eighth]_.  Networking-sfc will handle this type
of match to ensure classifiers via RBAC can match multiple tenants/tenant
networks.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

There will be changes to python-tackerclient for the end user in order to
manage VNFFG.  The changes will involve adding new VNFFG shell extensions to
python-tackerclient in order to allow CRUD operations.

There will also be changes to Horizon via the tacker-horizon plugin.  These
changes will allow a user to specify VNFFG from new tabs in Horizon (similar
to the design used for VNF Management).

Performance impact
------------------

None

Other deployer impact
---------------------

New configuration will be added to Tackers configuration file.  The new
configuration will include using "networking-sfc" VNFFG driver.

Configuration impact for OpenStack when using networking-sfc as the SFC driver
will require changes to Neutron configuration.

Configuration impact for OpenStack with OpenDaylight includes modifying Neutron
configuration as well as avoiding a potential port conflict between Swift and
OpenDaylight on port 8080.  OpenDaylight uses the ML2 plugin and OpenDaylight
configuration must be present in ML2 configuration file.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  trozet

Other contributors:

Work Items
----------

1. Add new plugin functionality for 'vnffg' to Tacker-server NFVO plugin
2. Port and modify 'plugin' for vnffg
3. Port and modify tackerclient API
4. Add shell extensions to tackerclient
5. Modify tacker_horizon with new interface for creating VNFFG
6. Add unit tests for all of the above
7. Add REST api docs
8. Add devref to document how VNFFG works

Dependencies
============

Tacker VNFFG/SFC is dependent on networking-sfc being able to create SFCs and
Classifiers.  Networking-sfc already supports creating chains and classifiers
via an OpenvSwitch (OVS) driver.  As previously mentioned, another method of
SFC includes using OpenDaylight, coupled with Network Service Header protocol,
and a transport medium such as VXLAN+GPE.

NSH is used to carry SFC information and provide security for the chain
[#first]_.  NSH is not a transport protocol.  Therefore it cannot be the
outer header of a packet, and must be encapsulated by another protocol.
There are multiple ways to do this which currently include using VXLAN+GPE
or Ethernet as the method of encapsulation.

OpenvSwitch currently has un-official patches to provide NSH from Cisco
[#second]_ and Intel.  The former allows for VXLAN+GPE NSH enabled OVS while
the latter allows for Ethernet NSH encapsulation (but is DPDK only).

The NSH header must be forwarded to the VNF VM itself so that the VNF can
decrement the NSH header and ensure reliability of the chain.  The Tacker SFC
work is dependent on a solution to this OVS so that a VNF VM would be able to
receive an NSH packet.

The dependencies around this method involve networking-sfc including a working
OpenDaylight driver.  Further down-stream dependencies include OpenDaylight SFC
and OpenvSwitch.

In addition, there may be dependencies on tosca-parser.  Some additional
support may be required when parsing VNFFG and related VNFD additions as
defined in this spec.

Testing
=======

As of now, there are no tempest tests added to Tacker and will be tracked as a
separate activity.  Ultimately that activity would take place in OPNFV SFC to
leverage their Functest and CI teams to perform testing.

Documentation Impact
====================

New API docs will be added for VNFFG to the Tacker repo.

References
==========

.. [#first] https://datatracker.ietf.org/doc/draft-ietf-sfc-nsh/?include_text=1
.. [#second] https://github.com/pritesh/ovs/tree/nsh-v8
.. [#fourth] https://github.com/openstack/networking-sfc/blob/master/doc/source/api.rst
.. [#fifth] https://github.com/opendaylight/sfc
.. [#sixth] https://tools.ietf.org/html/draft-ietf-netmod-acl-model-05
.. [#seventh] https://review.opendev.org/#/c/190463/20/specs/liberty/classifier.rst
.. [#eighth] https://specs.openstack.org/openstack/neutron-specs/specs/liberty/rbac-networks.html
.. [#ninth] http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.pdf
.. [#tenth] http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf
.. [#eleventh] https://review.opendev.org/#/c/290771/
