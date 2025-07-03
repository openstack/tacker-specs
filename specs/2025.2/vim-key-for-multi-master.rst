..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================================================
Add support for a default VIM secret key for multi-master Tacker
================================================================

https://blueprints.launchpad.net/tacker/+spec/vim-key-for-multi-master

This specification proposes to support a default secret key as a simple feature
to share the VIM secret key within a multi-master Tacker cluster.


Problem description
===================

When Tacker is deployed as a multi-master cluster for load balancing, it fails
to perform VIM operations such as deleting or updating resources created by
another Tacker node.
For example, if tacker-0 creates a resource, trying to delete it from tacker-1
will fail.

This is because Tacker generates a new `fernet_key` for each VIM registration
and does not have a way to share or sync keys between nodes.
To avoid authentication failures, keys must be copied manually between nodes.


Proposed change
===============

Add an option to specify a common default VIM key across Tacker nodes.

To enable this, a new `default_secret_key` parameter will be added under
`[vim_keys]` in `tacker.conf`.

Administrators will generate a default Fernet key file in advance
(e.g., `default.key`), place it in the existing `openstack` directory
(default: `/etc/tacker/vim/fernet_keys`) on each Tacker node, and specify
the filename using the `default_secret_key` option.

Example of `tacker.conf`:

.. code-block:: ini

   [vim_keys]
   default_secret_key = default.key

This setting allows the Tacker conductor to use the specified default key
when registering a VIM. The value of `default_secret_key` is interpreted as
a file located within the `openstack` directory. If the parameter is not set,
the current behavior (auto-generating a key per VIM) remains unchanged.

To set up the default key on each Tacker node, administrators generate
a Fernet key using any method.

For example:

.. code-block:: bash

   python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' > /etc/tacker/vim/fernet_keys/default.key

As part of this improvement, we also plan to provide an official utility
(e.g., a new `tacker-db-manage` option or a script under `tools/`) that
performs this key generation. While administrators can still generate the key
manually as shown above, the recommended approach will be to use the provided
tool to ensure consistency.

The same key file ("default.key") is placed on each Tacker node.
This approach is simpler than configuring continuous key synchronization
(e.g., using rsync or NFS), and is suitable for environments where the key
does not need to change frequently, such as closed or static deployments.

Alternatives
------------

Set up an additional method to synchronize VIM keys between Tacker nodes
(e.g., using rsync or NFS).

Data model impact
-----------------

None

REST API impact
---------------

None

Security impact
---------------

This feature has a minor security impact because the shared secret key must be
securely generated, stored, and distributed between Tacker nodes.
However, this is optional and generally safe if used in a closed network.

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
  Hitomi Koba <hi-koba@kddi.com>

Work Items
----------
* Update Docs (`Documentation Impact`_).

* Update OpenStack Driver (`tacker/nfvo/drivers/vim/openstack_driver.py`) to
  check the `default_secret_key` config value and branch logic accordingly.

* Modify other related parts as needed.

Dependencies
============

None

Testing
=======

Add unit tests.

Documentation Impact
====================

* Configuration Options [#conf_options]_

* Manual Installation [#manual_instrallation]_

References
==========

.. [#conf_options] https://docs.openstack.org/tacker/latest/configuration/config.html#vim-keys
.. [#manual_instrallation] https://docs.openstack.org/tacker/latest/install/manual_installation.html
