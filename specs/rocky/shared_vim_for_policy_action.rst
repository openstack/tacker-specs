..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


======================================
Shared VIM for Policy Action Execution
======================================

https://blueprints.launchpad.net/tacker/+spec/shared-barbican-secret

This spec describes the plan to implement shared vim for policy action
execution.


Problem description
===================

In current implementation [1], a registered vim's password is encoded by
fernet, and the fernet key is saved in barbican as a secret. With barbican's
default policy, only the user who created the secret can obtain the secret,
which leads to a problem that registered vim can not be shared by other tenants.

So if we want to do VNF LCM operation not via tacker api, such as
policy action execution, we have no keystone token to access barbican secret.

BP [2] wants to use mistral to do vnf monitor and execute policy action，
depending on this spec's realization.


Proposed change
===============

There are three methods to fix this problem.
wo will use the first method.

* Save the fernet key in one specific tenant, such as tacker service tenant.
  This method will lead to all vims can be invoked by other tenants.

  The main implementation is as follows:
    * register vim
        We use fernet to encrypt the VIM password, then use the tacker service tenant
        configured in the tacker.conf to save the fernet key to the barbican as a secret.
        barbican will return **secret_uuid**.
        then save encrypted into vim db's field **password**, and save the secret uuid
        into vim db field **secret_uuid**.
    * retrieving vim
        We use the tacker service tenant configured in the tacker.conf and **secret_uuid**
        to get the fernet key from barbican, and decode with **password** using fernet.
    * delete vim
        We use the tacker service tenant configured in the tacker.conf to delete
        the secret by the **secret_uuid** in vim db from barbican.

* we add the tacker service tenant to the acl of all fernet_key in barbican.
  Only the service tenant can invoke all vims. The policy action will use
  this service tenant.
  this method we need to modify other project. So not recommended.

* When create a VNF with monitor policy, we save the context information (
  without token due to it has expired time). Then the policy action use these
  information to access barbican.Originally, the fernet key is based on VIM.
  If it is changed to this, it will be in VNF, so that it will store a lot of
  secrect information. So not recommended.

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

This feature requires "tacker" user which has "admin" role.
When creating a "tacker" user via devstack, we need to add
the "admin" role to the "tacker" user.

Developer impact
----------------

None


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Li Jiale <lijiale@cmss.chinamobile.com>

Other contributors:
  Yan Xing'an <yanxingan@cmss.chinamobile.com

Work Items
----------

 * Unit Tests
 * Functional Tests
 * Feature documentation in doc/source/devref/feature


Dependencies
============

None

Testing
=======

None


Documentation Impact
====================

* update doc/source/contributor/encrypt_vim_auth_with_barbican.rst
  with new steps.


References
==========

* https://blueprints.launchpad.net/tacker/+spec/encryption-with-barbican

* https://blueprints.launchpad.net/tacker/+spec/mistral-monitor-policy
