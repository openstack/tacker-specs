..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


================
VDU auto healing
================

https://blueprints.launchpad.net/tacker/+spec/vdu-auto-healing

With anti-affinity policy now in place, it's possible to deploy high
available VNF applications (High availability will be taken care by the
application running on VDUs). If one of the VDUs is not responding, then
the existing ``respawn`` action deletes entire stack and creates new
ones.

Our plan is to add a new action ``vdu_autohealing`` to bring back the
failed VDU instead of deleting entire stack and creating a new one.


Problem description
===================

If one of the VDUs is not responding, then there is no way to bring back
that particular failed VDU as the existing ``respawn`` action deletes
the entire stack and creates a new one. If all VDUs are deleted and
replaced by new ones, high availability feature will be hampered as
there will be some down time until the VDUs are back again.

Our plan is to add a new action ``vdu_autohealing`` to bring back the
failed VDU thereby enabling other VDU in VNF to switch over to master to
keep services uninterrupted.


Proposed change
===============

Add a new action 'vdu_autohealing' which will first mark the status
(here, this is the status of "Heat" side) of
VDU and CPs assigned to that particular VDU as unhealthy using
'resource-mark-unhealthy' heat api and then the second step will be to
update the stack which will bring back the VDU and CPs marked as
unhealthy to "CHECK_COMPLETE" again. Internally, when stack is updated,
heat deletes the VDUs and CPs marked as unhealthy and replaces it with a
new ones. The heat-apis will be called from respective infra driver used
by the VNF. Presently, we are going to support this action for
`openstack` infra driver. After stack is updated, it will keep checking
the status of VNF to `CREATE_COMPLETE` until that point monitoring of
that particular VNF will be stopped.

Note: No plan to support this new action `vdu_autohealing` for policy
type `tosca.policies.tacker.alarming` so this action will not be
included in constant `DEFAULT_ALARM_ACTIONS` as defined in
tacker.plugins.common.constants. If this action needs to be supported
for policy type alarms, then there is need to pass `metadata` where the
action is invoked. This metadata contains the name of the
`metering.server_group` that you specify in VDU metadata. In the action
itself, based on policy type and `metadata`, we can scan VNFD template
available in 'vnf_dict' parameter to get VDU name. Once we know the VDU
name, the same logic will be reused for auto-healing.

An example of VNFD is shown below. The VDU will be monitored using any
of the existing monitoring drivers. If it fails to monitor any specific
VDU, it will execute the new action `vdu_autohealing`.

.. code-block:: yaml

  :caption: Example VNFD
  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
  description: Monitoring policy action : vdu_autohealing
  topology_templete:
    node_templates:
      VDU:
        type: tosca.nodes.nfv.VDU.Tacker
   # ...snip...
        properties:
            monitoring_policy:
                name: ping
                parameters:
                    monitoring_delay: 45
                    count: 3
                    interval: 1
                    timeout: 2
                actions:
                    failure: vdu_autohealing

Alternatives
------------

The other alternative solution is the same one as described in
alternative section of vdu-affinity-policy spec [#f1]_. In NSD, we can
add two VNFs, one for active and another for standby. If tacker detects
any issues during monitoring, then `respawn` action will delete that
particular VNF and create a new one. If the failed VNF is active, then
the other standby VNF will become active and continue servicing request
without interruption.

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
  Bhagyashri Shewale <bhagyashri.shewale@nttdata.com>

Other contributors:
  Hiroyuki Jo <jo.hiroyuki@lab.ntt.co.jp>

  Tushar Patil <tushar.vitthal.patil@gmail.com>

Work Items
----------

* Add `vdu_autohealing` action to mark VDU status to unhealthy and
  update stack
* Unit Tests
* Functional Tests
* Update documentation

Dependencies
============

None

Testing
=======

Unit and functional tests are sufficient to test `vdu_autohealing`
action.

Documentation Impact
====================

* Add VNFD tosca-template under samples to show how to configure
  `vdu_autohealing` action.

* Add a new action `vdu_autohealing` in Tacker Monitoring Framework
  [#f2]_.

References
==========

.. [#f1] https://specs.openstack.org/openstack/tacker-specs/specs/rocky/vdu-affinity-policy.html
.. [#f2] https://docs.openstack.org/tacker/latest/contributor/monitor-api.html
