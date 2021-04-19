==========================
Add VIM monitoring feature
==========================

https://blueprints.launchpad.net/tacker/+spec/vim-monitor-feature

This spec shows the feature of monitoring VIM inside Tacker itself.


Problem description
===================

In the current Tacker implementation, Mistral workflow service is used as
the VIM monitoring function.
It indicates Tacker requires Mistral component for its VNFM feature.
However, the VNFM feature should be achieved and also processed only inside
Tacker component.

Proposed change
===============

In this change, a VIM monitoring feature is newly added instead of calling
the same feature in Mistral.

This feature contains the following two functions.

* Monitoring VIM function

Each existing VIM is got health-check with ping from a VIM monitor.
As long as the VIM is alive, the monitor sets its status as "REACHABLE".
A monitor is dispatched every time a new VIM is created by the VIM monitor
manager and associated with the VIM one-to-one.

* Managing VIM monitor function

Monitoring VIM function is controlled by the VIM monitor manager.
When a VIM is newly created, the manager generates a monitor ID and register
a monitor associated with the VIM.
Also, when a VIM is deleted, the manager unregisters the monitor associated
with the VIM.
The manager periodically checks each monitor's status.
If there is a monitor which status is not processing, the manager forcibly
deletes it.

The code corresponding to this feature is placed in a new directory named
"vim_monitor", which is under tacker/nfvo directory.

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

The VNFM feature can be processed without Mistral workflow service.

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
  Koichi Edagawa <edagawa.kc@nec.com>


Work Items
----------

* Add monitoring VIM function
* Add managing VIM monitor function
* Change to use the above two functions instead of using Mistral


Dependencies
============

None


Testing
=======

Unit test cases will be added.


Documentation Impact
====================

Contributor guide will be modified to explain that monitoring VIM feature is
contained in Tacker instead of using Mistral.


References
==========

None


History
=======

None
