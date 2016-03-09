..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


===================================
Tacker & networking-sfc Integration
===================================

https://blueprints.launchpad.net/networking-sfc/+spec/tacker-networking-sfc-driver

This specification describes an SFC driver for Tacker that will interface with
the port-chain API of the
`Neutron networking-sfc <http://docs.openstack.org/developer/networking-sfc/>`_
project. The `Tacker API <https://wiki.openstack.org/wiki/Tacker>`_
provides for the management of Service VNFs and with [1], provides support for
the creation of VNF Forwarding Graphs (VNFFG).

A VNFFG is a graph of VNFs logically connected, by which Network Forwarding
Paths (NFPs) create paths through the graph. The port-chain API can be used
to build one or more NFPs through the graph.

Problem description
===================

Tacker VNFFG and Neutron networking-sfc operate on two different levels of
abstraction. While Neutron networking-sfc constructs a service chain via
stitching together a list of Neutron ports, and is generally service agnostic,
Tacker VNFFG operates on service instance or even higher service type
constructs (such as 'load-balancer', 'firewall'...etc).

In order to be able to render the NFPs of a VNFFG, networking-sfc is required
to provide the ability to create SFCs and Classifiers for Tacker.

Proposed changes
================
The new networking-sfc driver for Tacker will map from the high-level abstract
description of a VNFFG to a Neutron port description of a VNFFG, namely a
port-chain. The diagram below shows the networking-sfc driver integrated with
the Tacker NFVO plugin and the Tacker VNF Manager (VNFM) plugin in the
Tacker Server.

The NFVO extension has a dependency on the VNFM extension.

::

    +---------------------------------------------+
    |              Client Application             |
    +-----------+---------------------+-----------+
                | Tacker VNFFG API    | Tacker VNFM API
    +-----------|---------------------|-----------+
    |           v                     v           |
    |  +-----------------+    +----------------+  |
    |  |      Tacker     |    |    Tacker      |  |
    |  |  NFVO Extension |<-->| VNFM Extension |  |
    |  |   Plugin/DB     |    |   Plugin       |  |
    |  +------------+----+    +----------------+  |
    |               |                             |
    |               v                             |
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

The NFVO plugin will pass the VNFFG CRUD operations to the networking-sfc
driver. The driver will map the VNFFG CRUD operations to port-chain CRUD
operations and call the port-chain API of the networking-sfc Port Chain plugin.

The NFVO plugin also interfaces with the Tacker VNFM to retrieve
VNF instances and their ingress/egress interfaces in the case where the VNFFG
is specified in terms of abstract VNF types.

The NFVO plugin sends a query to the VNFM with a filter that specifies the
abstract VNF type and additional type-specific metadata.
The VNFM may indicate that there is no matching VNF instance available to
support the desired abstract VNF type specified in the query. The VNFM
may return one or more VNF instances that are able to support the desired
VNF type.

Although scaling is a future Tacker enhancement, VNF scaling is currently
supported by networking-sfc. If the VNFM returns multiple VNF instances the
NFVO plugin may select one VNF instance to create a port-pair-group with
a single port-pair. When the NFVO plugin does support scaling, it may
alternatively create a port-pair-group that includes all the VNF instances
returned by the VNFM.

The networking-sfc driver will include the following functionality:

* Map a VNFFG chain definition to a networking-sfc port-chain definition.

* The driver will format port-chain CRUD operations and call the port-chain API.

* If a VNFFG is specified as symmetrical, the driver will set 'symmetric'
  to true in the chain parameters atrribute.

* Map the VNFFG classifier to a flow-classifier for the port chain.
  As the flow-classifier defined in Tacker VNFFG currently contains more
  matching fields --- those that aren't supported by networking-sfc would
  simply be resulting in unimplemented exception.

* The default driver of Tacker VNFFG will be 'networking-sfc'

The current Tacker NFVO workflow to stage and deploy a VNFFG is as follows

::

 tacker vnffg-create --name myvnffg --vnfm_mapping VNF1:testVNF2,VNF2:testVNF1
                     --symmetrical True

networking-sfc follows the following workflow::

 neutron port-pair-create --ingress <port-id> --egress <port-id>

 neutron port-pair-group-create --port-pairs <port-pair-id>

 neutron flow-classifier-create --protocol tcp --destination-port 80:80

 neutron port-chain-create --port-pair-group <port-pair-group-id>
                           --flow-classifier <classifier-id> <name>

a port-chain can be created without flow-classifier, but the network plumbing
would be configured after the port-chain-create command.

The mapping of Tacker VNFFG APIs to Neutron networking-sfc client calls::

 +---------------------------------------------------------------------+
 |   Tacker VNFFG API          |   networking-sfc client CLI           |
 +-----------------------------+---------------------------------------+
 |                             |                                       |
 |       vnffg-create          |   neutron port-pair-create            |
 |                             |       --ingress [Neutron port]        |
 |                             |       --egress [Neutron port]         |
 |                             |                                       |
 |                             |   neutron port-pair-group-create      |
 |                             |       --port-pairs [port pair id]     |
 |                             |                                       |
 |                             |   neutron flow-classifier-create      |
 |                             |       [parameters]                    |
 |                             |                                       |
 |                             |   neutron port-chain-create           |
 |                             |       --port-pair-group <id>          |
 |                             |       --flow-classifier <fc-id>       |
 |                             |                                       |
 +-----------------------------+---------------------------------------+



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

User would need to specify the backend driver for networking-sfc via Neutron
config file. By default it will be OVS driver.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

* Stephen Wong (stephen.kf.wong@gmail.com)
* Cathy Zhang (cathy.h.zhang@huawei.com)
* Louis Fourie (louis.fourie@huawei.com)
* Farhad Sunavala (farhad.sunavala@huawei.com)

Work Items
----------

1. Add new driver 'networking-sfc' for Tacker NFVO extension.

   * Add mapping from VNFFG chain definition to port-chain.
   * Add mapping from VNFFG classifier to port-chain flow-classifier.
   * Add mapping from NFVO plugin to networking-sfc API.

2. Add unit tests for all of the above.
3. Integrate with networking-sfc port-chain.
4. devstack config to include networking-sfc.

Dependencies
============

Testing
=======

Unit tests and function tests will be added.

Documentation Impact
====================

None

References
==========

[1] https://github.com/openstack/tacker-specs/blob/master/specs/newton/tacker-vnffg.rst

