..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================================================
Allow duplicate vnfdId across tenants for VNF package onboarding
================================================================

https://blueprints.launchpad.net/tacker/+spec/multi-tenant-vnfdid-onboarding

This change addresses bug [#bug2129983]_, where onboarding fails
if another tenant has already onboarded a package with the same ``vnfdId``.

Today, Tacker treats ``vnfdId`` as globally unique across all tenants.
As a result, onboarding a VNF-package fails when another tenant has already
onboarded a package with the same vnfdId. This behavior is not suitable for
multi-tenant deployments.
This spec proposes to make vnfdId uniqueness tenant-scoped by updating the DB
schema and related lookup logic so that different tenants can onboard and use
VNF packages that share the same vnfdId.

Problem description
===================

When tenant A onboards a package that contains vnfdId = X, tenant B cannot
onboard another package that also contains vnfdId = X. The onboarding fails
with ``VnfPackageVnfdIdDuplicate``, and the package stays in ``CREATED`` state.

The root cause is that the ``vnf_package_vnfd`` table enforces a uniqueness
constraint on ``vnfd_id``, effectively making ``vnfdId`` globally unique.

This is inconsistent with the tenant-scoped nature of other Tacker resources,
and it prevents independent tenants from using the same VNFD identifier in
their own VNF-packages.

Proposed change
===============

DB schema changes
-----------------

Make ``vnf_package_vnfd`` tenant-scoped by adding a ``tenant_id`` column.

* Add a new column ``tenant_id`` to ``vnf_package_vnfd``.
* Populate ``tenant_id`` from the referenced VNF package record
  (e.g., ``vnf_packages.tenant_id``) to keep consistency between tables.

Uniqueness constraint
~~~~~~~~~~~~~~~~~~~~~

Change the uniqueness constraint to be tenant-scoped.

* Current: unique on ``(vnfd_id, deleted)`` (soft-delete aware).
* Proposed: unique on ``(tenant_id, vnfd_id, deleted)``.

This preserves the existing soft-delete behavior while allowing the same
``vnfdId`` across different tenants.

Logic changes (package onboarding and vnfdId lookups)
-----------------------------------------------------

Update all code paths that resolve a package by ``vnfdId`` to include
tenant scoping.

Onboarding
~~~~~~~~~~

* Modify duplicate checks to be evaluated within the same tenant only.
* Allow a different tenant to onboard a package with the same ``vnfdId``.

VNF lifecycle operations (e.g., Create VNF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Replace "lookup by ``vnfdId`` only" with "lookup by ``(tenant_id, vnfdId)``",
  using the request context project ID.
* This keeps the "unambiguous package resolution" requirement while removing
  the global uniqueness assumption.

Alternatives
------------

As a workaround, tenants can regenerate ``vnfdId`` and onboard the same VNFD
content with different ``vnfdId`` values per tenant. However, this adds
operational overhead and does not address the root cause.

Data model impact
-----------------

The ``vnf_package_vnfd`` table will be updated to include a new ``tenant_id``
column and a tenant-scoped uniqueness constraint on ``(tenant_id, vnfd_id, deleted)``.
Existing rows will be backfilled from the corresponding VNF package record
(e.g., ``vnf_packages.tenant_id``) via a database migration.

REST API impact
---------------

None (no API contract changes). However, this change affects both v1 and v2
users because it updates the backend DB schema/constraints and the tenant-scoped
``vnfdId`` lookup used by API flows in both versions.

Security impact
---------------

Ensure all ``vnfdId`` queries are filtered by the request context tenant/project
to prevent cross-tenant data exposure.

Notifications impact
--------------------

None

Other end user impact
---------------------

Tenants will be able to onboard VNF packages that contain the same ``vnfdId``
as packages onboarded by other tenants. Duplicate ``vnfdId`` will still be
rejected within the same tenant.

Performance Impact
------------------

Negligible. Queries that resolve a package by ``vnfdId`` will additionally
filter by ``tenant_id`` and use a tenant-scoped uniqueness constraint.

Other deployer impact
---------------------

Deployers must run the database migration that adds ``tenant_id`` to
``vnf_package_vnfd`` and updates the uniqueness constraint.

Developer impact
----------------

Code paths that look up VNF packages by ``vnfdId`` must be updated to include
tenant scoping (e.g., using the request context project ID).

Upgrade impact
--------------

A database migration is required to add ``tenant_id`` to ``vnf_package_vnfd``,
backfill existing rows from the referenced VNF package record, and replace the
unique constraint with ``(tenant_id, vnfd_id, deleted)``.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Hitomi Koba <hi-koba@kddi.com>

Work Items
----------

* Add ``tenant_id`` column to ``vnf_package_vnfd`` and implement an Alembic
  migration to backfill existing rows from ``vnf_packages.tenant_id``.

* Update the unique constraint on ``vnf_package_vnfd`` from ``(vnfd_id, deleted)``
  to ``(tenant_id, vnfd_id, deleted)``.

* Update onboarding logic to evaluate ``vnfdId`` duplication within the same
  tenant only (allow duplicates across tenants).

* Update all code paths that resolve a VNF package by ``vnfdId`` to include
  tenant scoping (use request context project ID).

* Add/extend unit and functional tests to cover multi-tenant onboarding and
  ``vnfdId``-based package resolution.

Dependencies
============

None

Testing
=======

Add and update unit tests to cover:

* onboarding the same ``vnfdId`` in different tenants (should succeed),
* onboarding duplicated ``vnfdId`` within the same tenant (should fail),
* resolving a VNF package by ``vnfdId`` using tenant scoping in relevant flows
  (e.g., Create VNF).

Documentation Impact
====================

None

References
==========

.. [#bug2129983] https://bugs.launchpad.net/tacker/+bug/2129983
