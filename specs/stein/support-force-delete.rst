..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

======================
Force Delete resources
======================

https://blueprints.launchpad.net/tacker/+spec/force-delete-resources

Provide support to force delete resources being stuck in some states
such as pending, error, etc..

Problem description
===================

In the current implementation, if any resource (i.e., VNFs) stuck in an abnormal
state, we don't have a mechanism to clean them. It is required to clean those
resource from the database even if somehow deletion from backend got failed.
For example, when the VNFs are failed to delete due to underlying system or
software error, those VNFs goes into PENDING_DELETE state. As a result,
vnf-delete on these PENDING_DELETE VNFs doesn't work and these VNFs are stuck
forever. We need to provide some mechanism for admin to "force" the deletion of
resources in PENDING_DELETE state.


Proposed change
===============

Add a new parameter --force in delete command for resources (i.e., VNF, NS & VNFFG)
and corresponding support in the server will be added to force delete these resources.

The purpose is to make admin capable to quickly delete the resources that are
not further usable and stuck in ERROR or PENDING_* state.

To delete VNF

.. code-block:: console

  openstack vnf delete <VNF name / id> --force

To delete VNFFG

.. code-block:: console

  openstack vnf graph delete <VNFFG name / id> --force

To delete NS

.. code-block:: console

  openstack ns delete <NS name / id> --force

* This feature will be required to clean Tacker DB for the cases when normal
  delete workflow is failed. To avoid the chances of accident and any
  inconsistency, we will keep it as an admin-only operation. So that admin
  can verify/debug the issue and can take suitable action on the backend.

* A success message will have some information that resource has been deleted
  with --force. For example:

.. code-block:: console

  ubuntu@nti:~/dk$ openstack vnf delete test_vnf --force
  All specified vnf(s) deleted forcefully

Alternatives
------------

After login to Tacker database, we can use the SQL commands to list the resources
which are stuck in PENDING_* state and then remove them manually from the database.
Keep in mind that we also need to update other related tables too.

Data model impact
-----------------

None

REST API impact
---------------

Addition of new parameter (i.e. {"force": true}) in request body.

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
  Cong Phuoc Hoang <hoangphuocbk2.07@gmail.com>

Other contributors:
  Dharmendra Kushwaha <Dharmendra.kushwaha@india.nec.com>

  Nguyen Hai <nguyentrihai93@gmail.com> <nguyentrihai@soongsil.ac.kr>

Work Items
----------

* Support in CLI for VNF, VNFFG & NS.
* Support in GUI for VNF, VNFFG & NS.
* Support in Server side.
* Add Test cases
* Update docs for these support.


Dependencies
============

None


Testing
=======

None


Documentation Impact
====================

Tacker documentation will need to be updated to show this new feature and
how to use it.

References
==========

None
