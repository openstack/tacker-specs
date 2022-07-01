=================
DB Migration Tool
=================

https://blueprints.launchpad.net/tacker/+spec/db-migration-tool

This specification describes a tool to perform DB migration from
v1 API to v2 API.

Problem description
===================

Tacker supports multi-version API: v1 API based on
SOL 003 v2.6.1 [#ETSI-NFV-SOL003-v2.6.1]_ and
v2 API based on v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_.
Since v2 API doesn't have backward compatibility for v1 API,
the v1 API users who want to shift from v1 API to v2 API have to terminate
their VNF once and re-instantiate them with v2 API.
However, this will incur a service outage and thus not realistic.
Moreover, some VNFs run for more than 5 years, which consequently means that
Tacker cannot deprecate an old API version for more than 5 years.
This can be a barrier to the future update roadmap of Tacker when it plans to
implement a new ETSI SOL release, e.g., Rel. 4.
This is simply because, without the deprecation of an old API,
the maintenance cost increases as the supported versions increase.
Therefore, a means of migrating from v1 API to v2 API
without service outage of the VNF is necessary.
This specification proposes a DB migration tool for API version update.

Proposed change
===============

We would implement a DB migration tool by adding DB migration functionality
to the tacker-db-manage command. Details are described below.

1) Target tables of migration:
------------------------------

Target tables to be migrated

- VnfInstanceV2
- VnfLcmOpOccV2

Source tables to be migrated

- vnf
- vnf_attribute
- vnf_instances
- vnf_instantiated_info
- vnf_lcm_op_occs

2) Target VNFs:
-----------------

One of the following can be selected when executing the command.

- The VNF that is specified by VNFID
- All VNFs that their records in the vnf_instances table for which the
  "deleted" field is not 1.

3) Tool execution method:
----------------------------

DB migration is executed by the following command.

.. code-block:: bash

   $ tacker-db-manage migrate-to-v2 { --all | [ --mark-delete --api-ver { v1 | v2 } ] --vnf-id <vnf-id> } [--keep-orig]

The options are defined as follows:

- ``--all``: Migrate all VNFs on vnf_instances that "deleted" field is not 1
- ``--vnf-id <vnf-id>``: The specific VNF will be migrated
- ``--keep-orig``: Keep v1 records without erasing them
  (Erasing them is default)

``--keep-orig`` option can be specfied to
keep the pre-migration records, oppositely,
the ``--mark-delete --api-ver { v1 | v2 } --vnf-id <vnf-id>`` option can be used
to complete or rollback the migration:

- ``--mark-delete --api-ver v1 --vnf-id <vnf-id>``: To complete the migration and erase
  the records before migration. It updates the value of the
  v1 records' "deleted" field to 1 with specific
  VNF and complete DB migration
- ``--mark-delete --api-ver v2 --vnf-id <vnf-id>``: To rollback the migration and erase
  the records after the migration. It updates the value of the
  v2 records' "deleted" field to 1 with specific
  VNF and rollback DB migration

Then records can be deleted completely by executing the ``tacker-db-manage`` command
with subcommand of ``purge_deleted``.

4) Sequence of tool execution:
--------------------------------

When the command is

.. code-block:: bash

   $ tacker-db-manage migrate-to-v2 --all [ --keep-orig ]

.. seqdiag::

  seqdiag {
    User -> Tacker-db-manage [label = "tacker-db-manage migrate-to-v2 --all [ --keep-orig ]"];
    Tacker-db-manage -> SQL_Alchemy [label = "Search for objects with deleted=0 from Vnf_instances"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get Vnf_instances objects"];
    === Repeat every Vnf_instances object ===
    Tacker-db-manage -> SQL_Alchemy [label = "Define VnfInstanceV2 Object"];
    Tacker-db-manage <-- SQL_Alchemy
    === Repeat every field ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Refer to the field of gotten object and update the field of VNFInstanceV2"];
    Tacker-db-manage <-- SQL_Alchemy
    === End line of "Repeat every field" ===
    Tacker-db-manage -> SQL_Alchemy [label = "Create VnfInstanceV2 Object"];
    SQL_Alchemy -> Tacker_DB [label = "Insert record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    ... ...
    Tacker-db-manage -> SQL_Alchemy [label = "Define VnfLcmOpOccV2 Object"];
    Tacker-db-manage <-- SQL_Alchemy;
    === Repeat every field ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Refer to the field of gotten object and update the field of VnfLcmOpOccV2"];
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Repeat every field" ===
    Tacker-db-manage -> SQL_Alchemy [label = "Create VnfLcmOpOccV2 Object"];
    SQL_Alchemy -> Tacker_DB [label = "Insert record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === Skip if the keep original records flag is ON ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Delete object"];
    SQL_Alchemy -> Tacker_DB [label = "Delete record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Skip if the keep original records flag is ON" ===
    === End line of "Repeat every Vnf_instances object" ===
    User <-- Tacker-db-manage;
  }

When the command is

.. code-block:: bash

   $ tacker-db-manage migrate-to-v2 --vnf-id <vnf-id> [ --keep-orig ]

.. seqdiag::

  seqdiag {
    User -> Tacker-db-manage [label = "tacker-db-manage migrate-to-v2 --vnf-id <vnf-id> [ --keep-orig ]"];
    Tacker-db-manage -> SQL_Alchemy [label = "Define VnfInstanceV2 Object"];
    Tacker-db-manage <-- SQL_Alchemy
    === Repeat every field ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Refer to the field of gotten object and update the field of VNFInstanceV2"];
    Tacker-db-manage <-- SQL_Alchemy
    === End line of "Repeat every field" ===
    Tacker-db-manage -> SQL_Alchemy [label = "Create VnfInstanceV2 Object"];
    SQL_Alchemy -> Tacker_DB [label = "Insert record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    ... ...
    Tacker-db-manage -> SQL_Alchemy [label = "Define VnfLcmOpOccV2 Object"];
    Tacker-db-manage <-- SQL_Alchemy;
    === Repeat every field ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Refer to the field of gotten object and update the field of VnfLcmOpOccV2"];
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Repeat every field" ===
    Tacker-db-manage -> SQL_Alchemy [label = "Create VnfLcmOpOccV2 Object"];
    SQL_Alchemy -> Tacker_DB [label = "Insert record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === Skip if the keep original records flag is ON ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Delete object"];
    SQL_Alchemy -> Tacker_DB [label = "Delete record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Skip if the keep original records flag is ON" ===
    User <-- Tacker-db-manage;
  }


When the command is

.. code-block:: bash

   $ tacker-db-manage migrate-to-v2 --mark-delete --api-ver v1 --vnf-id <vnf-id>

.. seqdiag::

  seqdiag {
    User -> Tacker-db-manage [label = "tacker-db-manage migrate-to-v2 --mark-delete --api-ver v1 --vnf-id <vnf-id>"];
    === Repeat related v1 tables ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Update the deleted field of gotten object to 1"];
    Tacker-db-manage <-- SQL_Alchemy
    Tacker-db-manage -> SQL_Alchemy [label = "Save gotten object"];
    SQL_Alchemy -> Tacker_DB [label = "Update record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Repeat related v1 tables" ===
    User <-- Tacker-db-manage;
  }

When the command is

.. code-block:: bash

   $ tacker-db-manage migrate-to-v2 --mark-delete --api-ver v2 --vnf-id <vnf-id>

.. seqdiag::

  seqdiag {
    User -> Tacker-db-manage [label = "tacker-db-manage migrate-to-v2 --mark-delete --api-ver v2 --vnf-id <vnf-id>"];
    === Repeat related v2 tables ===
    Tacker-db-manage -> SQL_Alchemy [label = "Search for related objects with the specified VNFID as a primary key or foreign key"];
    Tacker-db-manage <- SQL_Alchemy [label = "Get object"];
    Tacker-db-manage -> SQL_Alchemy [label = "Update the deleted field of gotten object to 1"];
    Tacker-db-manage <-- SQL_Alchemy
    Tacker-db-manage -> SQL_Alchemy [label = "Save gotten object"];
    SQL_Alchemy -> Tacker_DB [label = "Update record"];
    SQL_Alchemy <-- Tacker_DB;
    Tacker-db-manage <-- SQL_Alchemy;
    === End line of "Repeat related v2 tables" ===
    User <-- Tacker-db-manage;
  }

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
  Masaki Oyama <ma-ooyama@kddi.com>

Other contributors:
  Kinjou Yukihiro <yu-kinjou@kddi.com>

  Xu Hongjin <ho-xu@kddi.com>


Work Items
----------
* Implement migration function to tacker-db-manage command
* Add unit test
* Add functional test
* Add user document

Dependencies
============

None

Testing
=======

Unit test and functional test will be added.

Documentation Impact
====================

Documentation about tool usage will be added.

References
==========

.. [#ETSI-NFV-SOL003-v2.6.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. [#ETSI-NFV-SOL003-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
