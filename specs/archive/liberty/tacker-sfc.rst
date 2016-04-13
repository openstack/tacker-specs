..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Implement Tacker Service Function Chaining
==========================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/tacker-sfc

This spec describes the plan to introduce Service Function Chaining (SFC) into
Tacker.  In it's current state, Tacker allows for managing VNFs; the purpose of
this spec is to also include managing SFCs.

Problem description
===================

There is a large desire from the NFV community to be able to orchestrate and
manage SFC.  A user of NFV would not only like to be able to create VNFs, but
also define SFCs to direct traffic between VNFs.  This goes hand in hand with
the work already done in Tacker to manage and monitor VNFs, but takes it a step
further to include SFC.

The goal is to be able to define a chain in orchestration via a logical and
abstract construct, while being able to render that chain down to the overlay
network.  The next step is to be able to classify tenant traffic that should
flow through that SFC.  The combination of VNFs, SFC, and the classification of
traffic to flow through them is described as the VNF Forwarding Graph (VNFFG).
This spec addresses the changes to Tacker necessary to orchestrate a VNFFG.


Proposed change
===============

The high-level changes needed to Tacker in order to accomodate this new feature
will include changes to Tacker Client, Horizon, and Server.  Changes include:

* Add an SFC tab to tacker-horizon where a user can create a chain from already
  created  VNFs, as well as a Classification tab to declare traffic
  into the chain.  These inputs can be implemented in multiple ways, including
  (1) a TOSCA VNF Forwarding Graph Descriptor (VNFFGD), as
  well as (2) a simple drop down menu of chaining VNFs in order and then
  defining classification schemes for tenants.  VNFFG describes network
  functions and how they are connected via yaml templates as input [9].  This is
  similar to how VNFDs already work in Tacker VNFM.  This spec proposes to
  implement (2) with (1) as a later add on feature.

* Tacker Client will also need similar changes to allow passing the CRUD Chain
  and CRUD Classification calls to Tacker Server

* Tacker Server will need another plugin extension, 'vnffg', similar to 'vnfm'
  (previously 'servicevm')

* Drivers for 'vnffg' extension will need to be written.  The known drivers to
  create SFCs are networking-sfc [4] (Neutron based SFC) and OpenDaylight
  SFC [5].  This spec will implement OpenDaylight supported as a functional
  driver, and networking-sfc driver (along with others) will be a separate
  effort.  The OpenDaylight driver will be considered experimental, and for
  testing purposes, until a Neutron driver + networking-odl support is added
  to be able to create SFC for ODL via Neutron.  When that support exists, the
  OpenDaylight driver shall be deprecated in favor of a Neutron driver.

* Similarly drivers for Classification will need to be written.
  These drivers will be handled as "mechanism drivers" which will drive
  Classification in the main SFC OpenDaylight driver.  The default
  classifier mechanism driver will be 'netvirtsfc" which corresponds to an
  OpenDaylight classifier for the OVSDB NetVirt project [8].  Upon migration to
  Neutron driver, this driver will also be deprecated.

::

 Tacker SFC Overview:
    +------------------------+
    |  Tacker Server         |
    |                        |
    +---------+--------------+
              |
      +-------+-------+
      |               |
      |VNFFG Extension|
      |  Plugin/DB    |
      |               |
      |               |
      +-+-------------+
        |
 +------+-------+      +--------------+
 |              |----->|netvirt       |
 | ODL Driver   |      |mech driver   |
 +--------------+      +--------------+
           |               |
           v               v
       +----------------------+
       |  OpenDaylight        |
       |  Controller          |
       +----------------------+

Alternatives
------------

None

Data model impact
-----------------

Data model impact includes the creation of 'vnffg_chain' and 'vnffg_classifier'
tables.  Those tables will hold the attributes listed below.  Another table
'acl_match_criteria' will hold the entries of match criteria mapped to the
classifier.

REST API impact
---------------

Two basic methods of SFC creation via the VNFFG extension will be supported.
The first is by specifying the VNF instances (already created via VNFM) to use
in the chain.  The order of these VNFs determine their order in the chain
itself.  The second method of SFC creation involves using abstract types.  A
type is declared in the VNFD, determining what type of VNF it is (ex. firewall,
nat, etc).  This type may be passed into the vnffg-create command, along with
the --abstract-types argument, to indicate an abstract type is being used.  The
VNFFG plugin will then search randomly for a VNF of the specified type to be
used in chain creation, unless the registered SFC driver (i.e. opendaylight)
supports abstract type selection.  OpenDaylight SFC supports being able to
select VNFs based on abstract types using many algorithms such as random,
round-robin, shortest-path [11].

In addition, when using abstract types, a VNF instance of that type must already
exist for the vnffg-create command to complete successfully.  The possibility of
being able to automatically spawn a non-existent VNF instance of a desired
abstract type (that matches an existing VNFD) is outside the scope of this
spec, but may be supported later by an additional spec.

Example CLI calls:

To create VNFFG SFC (where testVNF1, and testVNF2 are VNF instances):

tacker vnffg-create --name mychain --chain testVNF2,testVNF1 --symmetrical True

To create VNFFG SFC by abstract VNF types (ex. "firewall", "nat"):
tacker vnffg-create --name mychain --chain firewall,nat --abstract-types

To create SFC Classifier for a VNFFG:

tacker vnffg-classifier-create --name myclass --chain mychain
--match tcp_dest=80,ip_proto=6

**/vnffg/chain**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RW, All |''        |string      |human+readable      |
 |              |       |        |          |            |name                |
 +----------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of      |
 |              |       |        |          |            |Chain               |
 +----------------------------------------------------------------------------+
 |attributes    |dict   |RW, All |None      |dict        |driver specific attr|
 |              |       |        |          |            |shown in schema 3   |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RW, All |generated |string      |project id to       |
 |              |       |        |          |            |launch SFC          |
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of SFC              |
 +--------------+-------+--------+----------+---------------------------------+
 |sfc_driver    |string |RW, All |Open      |string      |driver to provision |
 |              |       |        |Daylight  |            |SFC                 |
 +----------------------------------------------------------------------------+
 |symmetrical   |bool   |RW, All |True      |bool        |Chain allows        |
 |              |       |        |          |            |reverse traffic     |
 +----------------------------------------------------------------------------+
 |chain         |list   |RW, All |None      |list        |SFC Chain as list of|
 |              |       |        |          |            |ordered VNF name/IDs|
 +----------------------------------------------------------------------------+
 |abstract_types|bool   |RW, All |None      |bool        |Specify service_    |
 |              |       |        |          |            |types in chain      |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |create_chain  |post  |200 OK    |schema 1   | Creates SFC for declared VNFFG|
 |              |      |          |           |                               |
 +----------------------------------------------------------------------------+
 |update_chain  |put   |200 OK    |schema 1   | Updates VNFFG SFC by name or  |
 |              |      |          |           | ID                            |
 +----------------------------------------------------------------------------+
 |delete_chain  |delete|200 OK    |None       | Deletes VNFFG SFC by name or  |
 |              |      |          |           | ID                            |
 +----------------------------------------------------------------------------+
 |show_chain    |get   |200 OK    |None       | Returns output of specific    |
 |              |      |          |           | VNFFG chain ID                |
 +----------------------------------------------------------------------------+
 |list_chains   |get   |200 OK    |None       | Returns list of configured    |
 |              |      |          |           | VNFFG Names/IDs               |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |create_chain  |post  |404 Not   |Unknown VNF      |No VNFs exist with       |
 |              |      |Found     |Abstract Type    |declared abstract type   |
 +----------------------------------------------------------------------------+
 |create_chain  |post  |404 Not   |VNF does not     |No VNFs exist with       |
 |              |      |Found     |exist            |declared instance        |
 +----------------------------------------------------------------------------+
 |update_chain  |put   |404 Not   |Chain does not   |No Chain exists with     |
 |              |      |Found     |exist            |provided Name/ID         |
 +----------------------------------------------------------------------------+
 |delete_chain  |delete|403       |Chain Update     |Chain already being      |
 |              |      |Forbidden |in progress      |updated by a request     |
 +----------------------------------------------------------------------------+


**/vnffg/classifier**

::

 +----------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description         |
 |Name          |       |        |Value     |Conversion  |                    |
 +----------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity            |
 |              |(UUID) |        |          |            |                    |
 +----------------------------------------------------------------------------+
 |name          |string |RW, All |''        |string      |human+readable      |
 |              |       |        |          |            |name                |
 +----------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of      |
 |              |       |        |          |            |Classifier          |
 +----------------------------------------------------------------------------+
 |attributes    |dict   |RW, All |None      |dict        |driver specific     |
 |              |       |        |          |            |attributes          |
 +----------------------------------------------------------------------------+
 |tenant_id     |string |RW, All |generated |string      |project id to       |
 |              |       |        |          |            |create SFCClassifier|
 +----------------------------------------------------------------------------+
 |status        |string |RO, All |generated |string      |current state       |
 |              |       |        |          |            |of SFC Classifier   |
 +--------------+-------+--------+----------+---------------------------------+
 |sfc_classifier|string |RW, All |netvirtsfc|string      |driver to provision |
 |_driver       |       |        |          |            |SFC Classification  |
 +----------------------------------------------------------------------------+
 |match         |dict   |RW, All |True      |acl_dict    |Match criteria      |
 |              |       |        |          |            |(see supported list)|
 +----------------------------------------------------------------------------+
 |chain         |string |RW, All |None      |string      |SFC Chain to        |
 |              |(UUID) |        |          |(UUID)      |classify on         |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Calls    |Type  |Expected  |Body Data  |Description                    |
 |              |      |Response  |Schema     |                               |
 +----------------------------------------------------------------------------+
 |create_       |post  |200 OK    |schema 2   | Creates Classifier for        |
 |classifier    |      |          |           | for an SFC                    |
 +----------------------------------------------------------------------------+
 |update_       |put   |200 OK    |schema 2   | Updates Classifier by name or |
 |classifier    |      |          |           | ID                            |
 +----------------------------------------------------------------------------+
 |delete_       |delete|200 OK    |None       | Deletes classifier by name or |
 |classifier    |      |          |           | ID                            |
 +----------------------------------------------------------------------------+
 |show_         |get   |200 OK    |None       | Returns output of specific    |
 |classifier    |      |          |           | classifier                    |
 +----------------------------------------------------------------------------+
 |list_         |get   |200 OK    |None       | Returns list of configured    |
 |classifiers   |      |          |           | Classifier Names/IDs          |
 +----------------------------------------------------------------------------+

 +----------------------------------------------------------------------------+
 |REST Call     |Type  |Negative  |Response Message |Scenario                 |
 |Failures      |      |Response  |                 |                         |
 +----------------------------------------------------------------------------+
 |create_       |post  |404 Not   |Chain Instance   |No Chain exists with     |
 |classifier    |      |Found     |Not Found        |provided Name/ID         |
 +----------------------------------------------------------------------------+
 |update_       |put   |400 Bad   |Unknown Match    |Unsupported ACL match    |
 |classifier    |      |Request   |Criteria         |criteria in request      |
 +----------------------------------------------------------------------------+
 |delete_       |delete|403       |Classifier update|Classifier already being |
 |classifier    |      |Forbidden |in progress      |updated by a request     |
 +----------------------------------------------------------------------------+
 |update_       |put   |409       |Conflicting Match|Conflicting ACL match    |
 |classifier    |      |Conflict  |Criteria         |associated with the chain|
 +----------------------------------------------------------------------------+


**Schema Definitions:**

* Schema 1: This schema describes a typical body for VNFFG SFC request:

::

  {u'vnffg': {u'attributes': {}, u'name': u'test_chain', u'chain':
   [u'c0f0500e-4dc4-4321-a188-40a6ecfea0ea',
    u'9d1c6854-bb71-4a99-934d-7bef3222d0bb'], u'symmetrical': u'True'}}

* Schema 2: This schema describes a typical body for Classifier request:

::

  {u'vnffg_classifier': {u'attributes': {}, u'match':
   {u'source_port': u'80',
   u'protocol': u'6'}, u'name': u'test_classifier', u'chain':
   u'9aa6e7e2-2e87-432d-abe9-8e97ffd155cd'}

* Schema 3: This schema is used to provide extra information about each VNF in
  the SFC as driver specific attributes about a chain.  For example,
  OpenDaylight driver may need the transport-type, or encapsulation-type
  specified, while networking-sfc does not.  These are handled as optional
  key,value pairs.

::

 {u'vnffg':
       {u'attributes':
         [{u'9d1c6854-bb71-4a99-934d-7bef3222d0bb':
            {u'transport-type': u'VXLAN-GPE',
            u'sfc_encap': u'NSH'}},
          {u'5e5e72c0-82a9-4318-bcd7-8d965afbae89':
            {u'transport-type': u'Ethernet',
            u'sfc_encap': u'None'}}
         ]
        }
 }


**Classifier Match Criteria:**

Supported list of matching attributes for classification are listed below.
These are used as key=value pairs in a "match" list specified in schema 2.  The
match criteria supported by OpenDaylight includes IETF ACL model [6].  In
addition, networking-sfc project has passed the supported Classifier match
criteria listed in the corresponding spec [7].  Tacker SFC Classifier will
aggregate the two into these supported attributes.  There should be at least
one match criteria attribute specified when creating/updating a classifier
from the following available attributes:

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
 |ip_proto      |IP protocol                    |
 |              |                               |
 +----------------------------------------------+
 |tcp_src       |Source TCP port                |
 |              |                               |
 +----------------------------------------------+
 |tcp_dest      |Destination TCP port           |
 |              |                               |
 +----------------------------------------------+
 |tcp_src_      |Source TCP port range          |
 |range_min     |minimum value                  |
 +----------------------------------------------+
 |tcp_src_      |Source TCP port range          |
 |range_max     |maximum value                  |
 +----------------------------------------------+
 |tcp_dst_      |Destination TCP port range     |
 |range_min     |minimum value                  |
 +----------------------------------------------+
 |tcp_dst_      |Destination TCP port range     |
 |range_max     |maximum value                  |
 +----------------------------------------------+
 |udp_src       |Source UDP port                |
 |              |                               |
 +----------------------------------------------+
 |udp_dest      |Destination UDP port           |
 |              |                               |
 +----------------------------------------------+
 |udp_src_      |Source UDP port range          |
 |range_min     |minimum value                  |
 +----------------------------------------------+
 |udp_src_      |Source UDP port range          |
 |range_max     |maximum value                  |
 +----------------------------------------------+
 |udp_dst_      |Destination UDP port range     |
 |range_min     |minimum value                  |
 +----------------------------------------------+
 |udp_dst_      |Destination UDP port range     |
 |range_max     |maximum value                  |
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
Classifiers across tenants [8].  Once Neutron supports RBAC along with ODL SFC
support, Tacker will migrate to inherently use the RBAC approach.  For now, the
netvirtsfc driver will be able to classify across multiple tenants.

Security impact
---------------

Exposes OpenDaylight login information via Tacker configuration file.  Similar
to Neutron ML2 plugin.  Will be removed when OpenDaylight driver is deprecated.

Notifications impact
--------------------

None

Other end user impact
---------------------

There will be changes to python-tackerclient for the end user in order to manage
SFC.  The changes will involve adding new SFC shell extensions to
python-tackerclient in order to allow CRUD operations.

In the case of using OpenDaylight as the SFC driver, an end user may opt to
manage SFC by directly logging into OpenDaylight's SFC GUI as another avenue of
SFC management.

There will also be changes to Horizon via the tacker-horizon plugin.  These
changes will allow a user to specify SFCs and SFC Classifiers from new tabs
in Horizon (similar to the design used for VNF Management).

Performance Impact
------------------

None

Other deployer impact
---------------------

New configuration will be added to Tackers configuration file.  The new
configuration will include using "opendaylight" SFC driver, mechanism
driver for Classification, and configuring OpenDaylight specific parameters
(login, IP address, REST port, etc).

Configuration impact for OpenStack when using networking-sfc as the SFC driver
will require changes to Neutron configuration.

Configuration impact for OpenStack with OpenDaylight includes modifying Neutron
configuration as well as avoiding a potential port conflict between Swift and
OpenDaylight on port 8080.

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

1. Add new plugin extension 'sfc' to Tacker-server.
2. Port and modify 'opendaylight' sfc driver to Tacker.
3. Port and modify 'netvirtsfc' as a classifier driver.
4. Port and modify tackerclient API
5. Add shell extensions to tackerclient
6. Modify tacker_horizon with new interface for creating SFC and Classifiers
7. Add unit tests for all of the above
8. Integration with OpenDaylight and OVS dependencies (see below)
9. Add REST api docs

Dependencies
============

Main dependencies include SFC work in OpenDaylight and OpenvSwitch (OVS).  NSH
is used to carry SFC information and provide security for the chain [1].  NSH
is not a transport protocol.  Therefore it cannot be the outer header of a
packet, and must be encapsulated by another protocol.  There are multiple ways
to do this which currently include using VXLAN+GPE or Ethernet as the
encapsulator.

OpenvSwitch currently has un-official patches to provide NSH from Cisco [2] and
Intel.  The former allows for VXLAN+GPE NSH enabled OVS while the latter allows
for Ethernet NSH encapsulation (but is DPDK only).

The NSH header must be forwarded to the VNF VM itself so that the VNF can
decrement the NSH header and ensure reliability of the chain.  The Tacker SFC
work is dependent on a solution to this OVS so that a VNF VM would be able to
receive an NSH packet.

Corresponding work must be done in OpenDaylight to allow these changes to be
leveraged by OpenDaylight SFC project.  The Tacker SFC work is also dependent on
the these changes in OpenDaylight.

Testing
=======

As of now, there are no tempest tests added to Tacker and will be tracked as a
separate activity.  Ultimately that activity would take place in OPNFV SFC to
leverage their Functest and CI teams to perform testing.

Documentation Impact
====================

New API docs will be added for SFC to the Tacker wiki [3].

References
==========

[1] https://datatracker.ietf.org/doc/draft-ietf-sfc-nsh/?include_text=1
[2] https://github.com/pritesh/ovs/tree/nsh-v8
[3] https://wiki.openstack.org/wiki/Tacker/API
[4] https://github.com/openstack/networking-sfc/blob/master/doc/source/api.rst
[5] https://github.com/opendaylight/sfc
[6] https://tools.ietf.org/html/draft-ietf-netmod-acl-model-05
[7] https://review.openstack.org/#/c/190463/20/specs/liberty/classifier.rst
[8] https://wiki.opendaylight.org/view/OVSDB_Integration:Main
[9] http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/tosca-nfv-v1.0.pdf
[10] http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf
[11] https://github.com/opendaylight/sfc/blob/master/sfc-model/src/main/yang/service-function-scheduler-type.yang
