..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


=================================
Add CentOS Stream Testing in Zuul
=================================

https://blueprints.launchpad.net/tacker/+spec/centos-stream-testing

This proposal aims to test Tacker on CentOS Stream in Zuul.


Problem description
===================

Currently OpenStack is tested only on Ubuntu OS. However, some commercial
systems use Fedora family OS.
Some users want to know Tacker works properly on Fedora family OS.


Proposed change
===============

To check that Tacker works properly on Fedora family OS, we plan to add
testsets on CentOS Stream 9 nodeset to the testsets in Zuul.

Target testsets are the following:

* tacker-functional-devstack-multinode-legacy
* tacker-functional-devstack-multinode-sol
* tacker-functional-devstack-multinode-sol-separated-nfvo
* tacker-functional-devstack-multinode-sol-kubernetes
* tacker-functional-devstack-multinode-libs-master
* tacker-functional-devstack-multinode-sol-v2
* tacker-functional-devstack-multinode-sol-separated-nfvo-v2
* tacker-functional-devstack-multinode-sol-kubernetes-v2
* tacker-functional-devstack-multinode-sol-multi-tenant
* tacker-functional-devstack-multinode-sol-kubernetes-multi-tenant
* tacker-compliance-devstack-multinode-sol

The above is a list of testsets on Ubuntu.
We will create new testsets changing nodeset definition of the above
testsets from Ubuntu to CentOS Stream 9.

The new testsets will be non-voting tests.

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

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Toshiaki Takahashi <ts-takahashi@nec.com>

  Renu Rani <renu.rani@gmail.com>

Work Items
----------

* Add new testsets on CentOS Stream 9

Dependencies
============

None

Testing
=======

* Add new testsets on CentOS Stream 9

Documentation Impact
====================

None

References
==========

None
