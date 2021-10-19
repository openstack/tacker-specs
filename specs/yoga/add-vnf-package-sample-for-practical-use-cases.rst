==============================================
Add VNF package sample for practical use cases
==============================================

https://blueprints.launchpad.net/tacker/+spec/add-vnf-package-sample-for-practical-use-cases

This specification describes features of the VNF package we aim to add.
In this package, use cases listed below will be supported.

- use multiple deployment flavours
- deploy VNF connected to an external network
- deploy VNF as HA cluster
- deploy scalable VNF
- configure VNF with an ansible mgmt driver

Problem description
===================

There are some samples in current tacker repository, but these represent
a simple structure and not for users who want to deploy complicated VNF used in
a practical environment.
Therefore, it is important to add a VNF package sample in order to help them
know how to deploy VNF required in practical use cases.

Proposed change
===============

We aim to add a VNF package as a sample and explain
how to use it in documentation.
The diagram below shows the structure of VNFD used in this sample package.

::


  +-------------------------------------------------------------------------------------------------------------------------------------------------+
  |  VNFD                                                                                                                                           |
  |                                                                                                                                                 |
  |    +----------------------------+    +----------------------------------------------------------------------------------------------------+     |
  |    | Deployment flavour: ha     |    |   Deployment flavour: scalable                                                                     |     |
  |    |  +---------+ +---------+   |    | |------------------------------+ +------------------------------+ +------------------------------+ |     |
  |    |  | VDU0    | | VDU1    |   |    | | VDU0                         | | VDU1                         | | VDU2                         | |     |
  |    |  |         | |         |   |    | |   properties:                | |   properties:                | |   properties:                | |     |
  |    |  |         | |         |   |    | |     vdu_profile:             | |     vdu_profile:             | |     vdu_profile:             | |     |
  |    |  |         | |         |   |    | |       min_num_of_instance:1  | |       min_num_of_instance:0  | |       min_num_of_instance:0  | |     |
  |    |  +------+--+ +--+------+   |    | |       max_num_of_instance:1  | |       max_num_of_instance:1  | |       max_num_of_instance:1  | |     |
  |    |         |\     /|          |    | +------+--------------+--------+ +------+--------------+--------+ +------+--------------+--------+ |     |
  |    |         | \   / |          |    |        |              |                 |              |                 |              |          |     |
  |    |         |  \ /  |          |    |        |              |                 |              |                 |              |          |     |
  |    |         |   +vip|          |    |        |              |                 |              |                 |              |          |     |
  |    |         |   |   |          |    |        |              |                 |              |                 |              |          |     |
  |    |         |   |   |  int net |    |        |              |                 |              |                 |              |  int net |     |
  |    |   ------+---+---+-------   |    |    ----+--------------|-----------------+--------------|-----------------+--------------|-------   |     |
  |    |         |   |   |          |    |                       |                                |                                |          |     |
  |    +---------|---|---|----------+    +-----------------------|--------------------------------|--------------------------------|----------+     |
  |              |   |   |                                       |                                |                                |                |
  |              |   |   |                                       |                                |                                |                |
  +--------------|---|---|---------------------------------------|--------------------------------|--------------------------------|----------------+
                 |   |   |                                       |                                |                                |
                 |   |   |  ext net                              |                                |                                |   ext net
             ----+---+---+---------                     ---------+--------------------------------+--------------------------------+-------


The package and documentation support the following use cases.


1) Use multiple deployment flavours:
------------------------------------

The sample has multiple deployment flavours,
and each defines different topologies of VNF.
As in the diagram above, the deployment flavour of ha
and scalable are defined.
Users can easily try deploying different type of VNF by using this sample
and can learn about the following things.

- structure of a VNF package supporting multiple deployment flavours.
- how to write VNF descriptor and Heat template in each deployment flavour.
- how to designate deployment flavour in a request.

2) Deploy VNF connected to external network:
--------------------------------------------

The sample has VNF that has a connection to an external network and
has fixed ip addresses assigned to its CPs.
As in the diagram above, the VDU0 in the deployment flavour of scalable
has the CP connected to the external network of ext net.
Users can easily try deploying VNF connected to an external network
by using this sample and can learn about the following things.

- how to write VNF descriptor and Heat template
  that have connections to both internal and external networks.
- how to write VNF descriptor and Heat template
  that have fixed ip addresses assigned to its CPs.
- how to pass parameters about an external network in a request.

3) Deploy VNF as HA cluster:
----------------------------

The sample has VNF that has a vip shared by VDUs.
As in the diagram above, the deployment flavour of ha defines the vip
shared by the VDU0 and VDU1.
Users can easily try deploying VNF as HA cluster by using this sample
and can learn about the following things.

- how to write VNF descriptor and Heat template
  that have a vip shared by multiple VDUs.
- how to pass parameters about vip in a request.

4) Deploy scalable VNF:
-----------------------

The sample has VNF that has scalable VDUs and each VDU has
fixed ip addresses.
As in the diagram above, the deployment flavour of scalable defines
the VDUs whose number of instances can be 0 or 1.
Users can easily try deploying scalable VNF by using this sample
and can learn about the following things.

- how to write VNF descriptor and Heat template
  that have scalable VDUs and have fixed ip addresses assigned to the VDUs.
- how to designate the initial number of VDUs.
- how to designate the number of the VDUs in a scale request.
- how to designate the information about the CPs binding to the VDU
  designed not to be created until scale operation is excuted.

5) Configure VNF with an ansible mgmt driver
--------------------------------------------

The sample uses an ansible mgmt driver to configure VNF.
Users can learn about the following things.

- structure of VNF package supporting an ansible mgmt driver.
- how to write scripts using an ansible mgmt dirver.

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

None

Developer impact
----------------

None

Upgrade impact
--------------

None


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Masaki Oyama <ma-ooyama@kddi.com>


Work Items
----------
* Create VNF package
* Write documentation to explain how to use the sample

Dependencies
============

None


Testing
=======

None


Documentation Impact
====================

User guide will be modified to explain how to use the sample.

References
==========

None

History
=======

None
