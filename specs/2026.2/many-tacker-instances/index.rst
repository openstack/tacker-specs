..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================================================
Many OpenStack Tacker instances deployment
===================================================

https://blueprints.launchpad.net/tacker/+spec/many-tacker-instances

This specification describes the enhancement of OpenStack Tacker deployment for scalable and flexible depending on usecase and deployment scale of VNF instance. Current OpenStack Tacker allows to deploy OpenStack Tacker itself as single instance, and scale up by high performance compute is required if large scale deployment of VNF instance is necessary. However, scale up approach sometimes faces limitation issue and distributed OpenStack Tacker instance is required for reliability. For example, OpenStack Tacker needs to manage some thousands of VNF insntance for vRAN usecase, and one OpenStack Tacker instance manages less than some hundreds of VNF instance to reduce the impact when the OpenStack Tacker is failure.

This spec proposes to extend OpenStack Tacker deployment to support scale out/in approach for scalablity and reliability by improving single instance concept of current OpenStack Tacker implementation. The scope of this version is only scalablity of OpenStack Tacker instance, and assignment of VNF instance for particular OpenStack Tacker instance is addressed future version.


Problem description
===================
Current OpenStack Tacker implementation assumes 1:1 mapping between OpenStack Tacker and database. Therefore, OpenStack Tacker faces issue for multiple OpenStack Tacker instances as following when multiple OpenStack Tacker synchronizes with database:

* conflict of locks to synchronize between OpenStack Tacker conductor and database.

* many database synchronization when many Tacker instance runs due to unit of tacker conductor synchronizing database is per Tacker instance.

* huge memory usage when number of VNF instances are huge by all OpenStack Tacker conductor instances handles all VNF instaces (out of scope of this spec)

* slow query by API GW for huge number of VNF instances by 1 API GW queries all VNF instances (out of scope of this spec)


Use Cases
---------

As an operator, I want to deploy multiple OpenStack Tacker instance for large scale VNF instance deployment.

As an operator, I want to assign particular VNF instance to particular OpenStack Tacker instance (out of scope of this spec)

Proposed change
===============

This spec proposes to improve synchronization mechanism between OpenStack Tacker conductor and database.
1st change is "tacker/sol\_refactored/conductor/conductor\_v2.py" and "tacker/sol\_refactored/conductor/v2\_hook.py" will change lock mechanism from conductor instance to no lock to avoid conflict of lock for database.
2nd change is only leader conductor instance synchronize with database to avoid synchronization by all conductor insntances. Leader selection mechanism is TBD.


Alternatives
------------

None.

Data model impact
-----------------

None.

REST API impact
---------------

None.

Security impact
---------------

None.

Notifications impact
--------------------

None.

Other end user impact
---------------------

TBD

Performance Impact
------------------

Improves speed of synchronization between conductor and database by multiple conductor instances and saves memory usage.

Other deployer impact
---------------------

None.

Developer impact
----------------

When developing new features, developer needs to consider the possibility of multiple instances conflict for database access.

Upgrade impact
--------------

None.


Implementation
==============

Assignee(s)
-----------

TBD

Work Items
----------

TBD


Dependencies
============

TBD


Testing
=======

OpenStack Tacker pipeline can be test, because feature is not changed.



Documentation Impact
====================

None.

References
==========

None.
