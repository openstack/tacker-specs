..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

======================================================
Enhancement of the Ansible Driver (sample mgmt driver)
======================================================

https://blueprints.launchpad.net/tacker/+spec/enhance-ansible-driver-2024oct

Add several features to make it more flexible for tenant usage and tacker
administrators.

* **Feature 1**: A feature to specify the Ansible version in the Ansible Driver
  configuration file within the VNF-Package.

* **Feature 2**: A feature to specify environment variables for
  ansible-playbook execution in `tacker.conf`.


Problem description
===================

Tacker currently supports only a single version of Ansible.
As a result, when tenants include Playbooks in the VNF-Package that only work
with specific versions of Ansible, there may be compatibility problems with
the Playbooks.

Tacker administrators must modify the Ansible Driver's source code directly
if they want to enforce options related to ansible-playbook execution,
such as specifying log storage locations or custom callback plugins.

These issues lack flexibility for both tenants and administrators.

Proposed change
===============

The scope of modifications is limited to the `samples/mgmt_driver/ansible`.

Feature 1
---------

Tacker administrator creates environments for each version of Ansible and
specifies the mapping of the Ansible version identifier to the venv path in
`tacker.conf`.

Example of `tacker.conf`:

.. code-block:: ini

   [ansible]
   venv_path=ansible-2.9:/opt/my-envs/2.9
   venv_path=ansible-2.10:/opt/my-envs/2.10
   venv_path=ansible-2.11:/opt/my-envs/2.11

Tacker tenant specifies the Ansible version identifier in the configuration
for the Ansible Driver within the VNF-Package.

Example of ansible-driver configuration in VNFD:

.. code-block:: yaml

   vdus:
     NodeA_0:
       config:
         order: 0
         vm_app_config:
           type: ansible
           instantiation:
             - path: _VAR_vnf_package_path/Scripts/test/test_ansible.yml
               ansible_version: "ansible-2.9" # here

Tacker conductor checks the version identifier in the package and switches to
the matching venv path to execute `ansible-playbook`.

If the path does not exist or the version identifier is not defined,
the `ansible-playbook` will be executed using the default
version (same as before).

Feature 2
---------

Tacker administrator specifies environment variables in `tacker.conf` for use
when executing `ansible-playbook`.

Example of `tacker.conf`:

.. code-block:: ini

   [ansible]
   env_vars = ANSIBLE_LOG_PATH:/var/log/tacker/ansible_driver/ansible.log
   env_vars = ANSIBLE_STDOUT_CALLBACK:kddi-custom-callback

These are passed as the environment variable `ANSIBLE_CONFIG` during execution,
so they take precedence over those specified by the tenant in the
`ansible.cfg` [#ansible_cfg]_ within the VNF-Package.

This allows the administrator to enforce settings such as log storage locations
according to the environment.

Tacker conductor checks the environment variables in `tacker.conf` during LCM
and executes `ansible-playbook`.


Alternatives
------------

* Feature 1

  None

* Feature 2

  Tacker administrators modify the source code of the Ansible Driver directly.

Data model impact
-----------------

None

REST API impact
---------------

None

Security impact
---------------

Previously, Tacker tenants could freely specify ansible-playbook execution
options in the ansible.cfg within the VNF-Package. However, with this change,
Tacker administrators can enforce configurations through tacker.conf, thereby
preventing unintended actions and enhancing security.

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
  Hitomi Koba <hi-koba@kddi.com>

Work Items
----------

* Update part of the code in `samples/mgmt_driver/ansible`.
* Update part of the docs.

Dependencies
============

None

Testing
=======

None (Because of ansible-driver is sample implementation)

Documentation Impact
====================

* How to use Mgmt Driver for Ansible Driver [#doc_ansible_driver]_

References
==========

.. [#ansible_cfg] https://docs.ansible.com/ansible/latest/reference_appendices/config.html#the-configuration-file
.. [#doc_ansible_driver] https://docs.openstack.org/tacker/latest/user/mgmt_driver_for_ansible_driver_usage_guide.html
