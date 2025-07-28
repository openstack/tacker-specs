..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================================================
Option to Enable/Disable Cinder Volume Recreation in v1 Heal
============================================================

https://blueprints.launchpad.net/tacker/+spec/v1-heal-cinder-volume

This specification proposes adding an option to enable or disable
Cinder volume recreation when issuing a v1 Heal request.

Problem description
===================

The current v1 Heal request always recreates the specified VNFC instance
along with its related Cinder storage resources, which is not flexible
for users who want to keep their storage data.
The v2 Heal request already provides an option to control this behavior.

Proposed change
===============

The existing ``additionalParams`` field in the v1 Heal request will be extended
to include a new parameter that allows users to choose whether to recreate
the Cinder storage resources.

To achieve this, two new parameters will be added under ``[vnf_lcm]`` in
``tacker.conf``.
If neither parameter is defined, the existing behavior will remain unchanged.

``heal_vnfc_block_storage`` sets the default behavior. If the Heal request does
not specify it, this value is used.

``heal_include_block_storage_key`` sets the parameter name that can be used in
the ``additionalParams`` field of the Heal request. This allows users to align
the request format with v2 or choose a different name if preferred.
(Setting this to "all" will match the v2 request format. [#v2_heal]_ )

By configuring these two parameters, users can flexibly adjust the behavior
to suit their operational requirements.

Example of ``tacker.conf``:

.. code-block:: ini

   [vnf_lcm]
   heal_vnfc_block_storage = false
   heal_include_block_storage_key = heal_include_storage  # customized name

In this case, Example  of Heal request with tacker-cli and additional-param:

.. code-block::

   openstack vnflcm heal --vnfc-instance <vnfc_id> --additional-param-file <file_path> -- <vnflcm_id>

.. code-block:: json

   {
     "additionalParams":
       {
         "heal_include_storage": true
       }
   }

In this case, the storage will only be recreated if explicitly specified
in the Heal request.
This means it is suitable for environments where most users prefer to keep
their storage data during a heal operation.

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
  Hitomi Koba <hi-koba@kddi.com>

Work Items
----------

* Consider making ``heal_include_block_storage_key`` configurable, based on
  ETSI-NFV direction (under discussion).

* Update Docs (`Documentation Impact`_).

* Update OpenStack Driver (``tacker/nfvo/drivers/vim/openstack_driver.py``) to
  check the ``heal_vnfc_block_storage`` and ``heal_include_block_storage_key``
  config value and branch logic accordingly.

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
* ETSI NFV-SOL VNF Healing (v1) [#v1_heal]_
* NFV Orchestration API Reference (v1) [#v1_api_ref]_
* Command-Line Interface Reference (v1) [#v1_cli_ref]_

References
==========

.. [#v2_heal] https://docs.openstack.org/tacker/latest/user/v2/vnf/heal/index.html#vnf-healing-procedure
.. [#conf_options] https://docs.openstack.org/tacker/latest/configuration/config.html#vnf-lcm
.. [#v1_heal] https://docs.openstack.org/tacker/latest/user/etsi_vnf_healing.html#vnf-healing-procedure
.. [#v1_api_ref] https://docs.openstack.org/api-ref/nfv-orchestration/v1/vnflcm.html#heal-a-vnf-instance
.. [#v1_cli_ref] https://docs.openstack.org/tacker/latest/cli/cli-etsi-vnflcm.html#heal-vnf
