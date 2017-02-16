======================================
Enable auto-healing function for VNFFG
======================================

https://blueprints.launchpad.net/tacker/+spec/vnffg-healing

This proposal aims at providing auto-healing function for VNFFG based on the
existing policy actions in VNFM
The spec is referred to Network service fault management in ETSI standard [#first]_.

Problem description
===================

Currently Tacker already supported auto-healing function for individual VNFs by
using (ping, http-ping) and alarm driver. However, only VNF ID is kept after
respawning VNFs, Connection Point (CP) could be seriously changed.
This problem is exacerbated when these VNFs are being used to on-board VNFFG.
The reason is CP-id is now used to create SFC using Neutron SFC [#second]_.

This spec is supposed to provide auto-healing for VNFFG in single site,
multi-sites support will be taken into account in the future. In addition,
Tacker had plan to add VNFFG to Network Service (NS), therefore this spec also
considers extending scope to support VNFFG inside NSs.


Proposed change
===============

Introduce a vnffg-ha engine in Tacker NFVO

::

  +---------------------------------+
  |          Tacker_NFVO            |
  |      +------------------+       |
  |      |                  |       |
  |      |  NFVO API/TOSCA  |       |               +-----------------------+
  |      |                  |       |               |                       |
  |      +---------+--------+       |               |      Tacker_VNFM      |
  |                |                |               | +-------------------+ |
  |                |                |               | |  VNFM API/TOSCA   | |
  |                |                |               | |                   | |
  |                |                |               | +---------+---------+ |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |                |                |               |           |           |
  |          +-----v-----+          |               |    +------v------+    |
  |          |NFVO Plugin|          |               |    | VNFM Plugin |    |
  |          |           |          |               |    |             |    |
  |          +-----+-----+          |               |    +------+------+    |
  |                |                |               |           |           |
  |  +-------------v--------------+ |               |           |           |
  |  |      vnffg-ha engine       | |               |   +-------v--------+  |
  |  |                            <-----conductor-------+ policy actions |  |
  |  |                            | |               |   +----------------+  |
  |  +----------------------------+ |               +-----------------------+
  |                                 |
  +---------------------------------+


*Component*

vnffg-ha engine: When vnffg-ha receives a trigger from policy actions:
  1. Firstly, it finds which VNFFGs VNF belongs to.
  2. It then makes the changes in VNFFG corresponding to VNF policy action.
     In this spec, respawning action is taken into account. In this case,
     CPs in VNF is changed, we will use neutron port-pair update in order to
     deal with this change.


Security impact
---------------

None

Notifications impact
--------------------

Because the failure of VNFs happened in VNFM layer, VNFFGs is orchestrated in NFV layer.
A broken VNF could make one or several VNFFGs fail. Therefore, we need to have a method to
inform VNFFGs about their VNFs. In short term, tacker conductor will be used to emit events
from VNFM to NFVO. The future consideration is to use event/auditing functions.

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
  Tung Doan <doantungbk.203@gmail.com>

Work Items
----------

 * Implement vnffg-ha engine in NFVO
 * Modify the existing VNFFG implementation in NFVO plugin
 * Add event/auditing function
 * Add unit and functional tests



Dependencies
============

None

References
==========
.. [#first] http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf
.. [#second] https://github.com/openstack/tacker/blob/master/tacker/db/nfvo/vnffg_db.py#L405&L431
