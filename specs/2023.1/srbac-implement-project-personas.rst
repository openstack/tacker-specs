..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


============================================
SRBAC: Implement Support Of Project Personas
============================================
https://blueprints.launchpad.net/tacker/+spec/implement-project-personas

This specification discusses the implementation of project-personas
in Tacker.

Role-Based Access Control (RBAC) is used by most OpenStack services
to control user access to resources. Authorization is granted if a
user has the necessary role to perform an action.

Problem description
===================

In the Zed cycle, OpenStack Technical Committee proposed to implement
support project personas [#TC-GOALS]_.

Implement support project personas.
This is to introduce the member and reader roles to operate things
within their project. By default, any other project role like foo
will not be allowed to do anything in the project.

Legacy admin will be unchanged and continue to work the same way as it
does today.

In OpenStack, the existing "owner" rule allows any role user to access
project resources. For instance, say role:foo behaves as the owner of the
project resources.

The implementation of the project personas will help in restricting any
role user to access project resources other than admin, member or reader.

In Tacker, we need to fix the existing "owner" rule and implement new
rules as project-member and project-reader to restrict access to
project-owned resources.

Proposed change
===============

The OpenStack Keystone already supports implied roles which means the
assignment of one role implies the assignment of another.

The new default roles reader and member also have been added in bootstrap.
If the bootstrap process is re-run, and a reader, member, or admin role
already exists, a role implication chain will be created: admin implies
member implies reader.

It means if we make something like role:reader in policy rule means
role:admin and role:member can still access that policy.

Implement support of project-reader
-----------------------------------

The project-reader persona will operate within its own project
resource, and have read-only access within the project.
Not allowed to make any writable changes to the project-owned
resources.

The project-reader changes will make sure that by default any other
role for example foo in that project will not be able to do anything.

project-reader is denoted by someone with the reader role on a project.
It is intended to be used by end users for read-only access within a
project.

The existing rule "admin_or_owner" allows admin or any role in the project
to access project resources.

.. code-block::

  policy.RuleDefault(
      "admin_or_owner",
      "is_admin:True or project_id:%(project_id)s",
      "Default rule for most non-Admin APIs."
  )

The new rule "project_reader_or_admin" will allow admin, project-member
and project-reader to access project resources.

Add project_reader policy in the tacker policy file.

.. code-block::

  RULE_PROJECT_READER = 'rule:project_reader'
  RULE_PROJECT_READER_OR_ADMIN = 'rule:project_reader_or_admin'

  policy.RuleDefault(
      "project_reader",
      "role:reader and project_id:%(project_id)s",
      "Default rule for Project level read only APIs."
      deprecated_rule=DEPRECATED_ADMIN_OR_OWNER_POLICY)

  policy.RuleDefault(
      "project_reader_or_admin",
      "rule:project_reader or rule:context_is_admin",
      "Default rule for Project reader or admin APIs.",
      deprecated_rule=DEPRECATED_ADMIN_OR_OWNER_POLICY)

project_reader persona in the policy check string:

For example, the policy check string for the query to show an individual VNF
instance. The existing rule "RULE_ADMIN_OR_OWNER" allows admin, or any role
in the project to get the VNF instance.

.. code-block::

  policy.DocumentedRuleDefault(
      name=VNFLCM % 'show',
      check_str=base.RULE_ADMIN_OR_OWNER,
      description="Query an Individual VNF instance.",
      operations=[
          {
              'method': 'GET',
              'path': '/vnflcm/v1/vnf_instances/{vnfInstanceId}'
          }
      ]
  )

The new rule "RULE_PROJECT_READER_OR_ADMIN" allows admin, project-member
and project-reader to get a VNF instance.

.. code-block::

  policy.DocumentedRuleDefault(
      name=VNFLCM % 'show',
      check_str=base.RULE_PROJECT_READER_OR_ADMIN
      description="Query an Individual VNF instance.",
      operations=[
          {
              'method': 'GET',
              'path': '/vnflcm/v1/vnf_instances/{vnfInstanceId}'
          }
      ]
  )

Fix the existing 'owner' rule
-----------------------------

The existing "owner" rule allows any role user to access project resources.
Introduction of  dedicated project member and reader role helps in addressing
the issue.
Additionally, to implement project-reader persona to behave as a reader role
in the Tacker we need to fix the existing "owner" rule.

The project-member is denoted by someone with a member role on a project.
It is intended to be used by end users who consume resources within a project.
It inherits all the permissions of a project-reader.

The existing "admin_or_owner" rule gives access to any role (say foo)
in the project to behave as the owner of the project.

.. code-block::

  policy.RuleDefault(
      "admin_or_owner",
      "is_admin:True or project_id:%(project_id)s",
      "Default rule for most non-Admin APIs."
  )

The new rule "project_member_or_admin" will give access to the admin or member
role in that project to behave as the owner of the project.

Add project_member policy in the tacker policy file.

.. code-block::

  RULE_PROJECT_MEMBER = 'rule:project_member'
  RULE_PROJECT_MEMBER_OR_ADMIN = 'rule:project_member_or_admin'

  policy.RuleDefault(
      "project_member",
      "role:member and project_id:%(project_id)s",
      "Default rule for Project level non admin APIs."
      deprecated_rule=DEPRECATED_ADMIN_OR_OWNER_POLICY)

  policy.RuleDefault(
      "project_member_or_admin",
      "rule:project_member_api or rule:context_is_admin",
      "Default rule for Project Member or admin APIs.",
      deprecated_rule=DEPRECATED_ADMIN_OR_OWNER_POLICY)

project-member persona in the policy check string:

For example, the policy check string for query to create a VNF instance.
The existing rule "RULE_ADMIN_OR_OWNER" allows admin or any role in
project to create a VNF instance.

.. code-block::

  policy.DocumentedRuleDefault(
      name=VNFLCM % 'create',
      check_str=base.RULE_ADMIN_OR_OWNER,
      description="Creates vnf instance.",
      operations=[
          {
              'method': 'POST',
              'path': '/vnflcm/v1/vnf_instances'
          }
      ]
  )

The new rule "RULE_PROJECT_MEMBER_OR_ADMIN" will allow admin or member
role to create a VNF instance.

.. code-block::

  policy.DocumentedRuleDefault(
      name=VNFLCM % 'create',
      check_str=base.RULE_PROJECT_MEMBER_OR_ADMIN,
      description="Creates vnf instance.",
      operations=[
          {
              'method': 'POST',
              'path': '/vnflcm/v1/vnf_instances'
          }
      ]
  )

.. note:: Tacker APIs with a policy define as "RULE ANY" will not be change.

How to design Functional Testing
--------------------------------

In current sol-based v1 functional test cases, single tenancy use cases are
validated using an admin role user. And multi-tenancy use cases are validated
by member role users.
To validate the project-reader role in the Tacker, we need to create a new
test user having the project-reader role.
The new test user will then validate the sol-based v1 read-only Tacker APIs.

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

List of impacted Tacker APIs:

#. VNF packages

   * Create VNF Packages
   * List VNF Packages
   * Show VNF Package
   * Delete VNF Package
   * Upload VNF Package from content
   * Upload VNF Package from uri
   * Update VNF Package Information
   * Read VNFD of an individual VNF package
   * Fetch an on-boarded VNF package with HTTP_RANGE
   * Fetch an on-boarded VNF package Artifacts with HTTP_RANGE

#. VNF Life Cycle Management

   * Creates a new VNF instance resource
   * Instantiate a VNF instance
   * Terminate a VNF instance
   * Heal a VNF instance
   * Delete a VNF instance
   * Show VNF Instance
   * List VNF Instance
   * Scale a VNF instance
   * Modify a VNF instance
   * Change External VNF Connectivity
   * Show VNF LCM operation occurrence
   * List VNF LCM operation occurrence
   * Roll back a VNF lifecycle operation
   * Fail a VNF lifecycle operation
   * Create a new subscription
   * Delete a subscription
   * Show subscription
   * List subscription
   * Retry

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
  Manpreet Kaur <kaurmanpreet2620@gmail.com>

Work Items
----------

* Add project-reader and project-member rules in the Tacker policies.
* Add unit test cases to validate the policy changes.
* Implement functional test cases to validate read-only sol-based v1 APIs
  with the project-reader role.

Dependencies
============

None

Testing
=======

Add unit and functional test cases to validate the new rules.

Documentation Impact
====================

Update the Tacker policy document [#TACKER-POLICY-DOC]_ by adding details for new project personas.

References
==========

.. [#TC-GOALS] https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html
.. [#TACKER-POLICY-DOC] https://docs.openstack.org/tacker/latest/configuration/policy.html
