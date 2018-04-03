..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


============================================
Scalable VNF monitor policies using Mistral
============================================

https://blueprints.launchpad.net/tacker/+spec/mistral-monitor-policy


Problem description
===================

Currently, Tacker server hosts a local variable to keep the monitoring
of VNFs and uses local threads to do the monitoring. This causes tacker
server not to be scalable and impacts the API performance as well:

* If we have a lot of VNFs which needs monitoring, the tacker server will
  have to run a lot of threads to monitor them, which will impact the API
  function of tacker server.

* If the tacker server restarts, the monitor threads will not start.

* The system cannot run more than one tacker server, since this is
  making tacker server stateful.


Proposed change
===============

asciiflow::

	                             +---------------------+
	                             |  Mistral workflow   |
	                     +-(1)---> VNF monitor action  |
	+---------------+    |       |                     |
	| Tacker server +----+       +--------^------------+
	+-----+---------+                     |
	      |      |                        |
	      |      |                        |
	      |      |                        |
	      |      |                        |
	      |      |               +--------v----+
	      |      |----(3)-------->  MSG Queue  <----+
	      |                      +-------------+    (2)
	      |                                         |
	      |                                 +-------v----------+
	      |                                 |     Tacker       |
	      |                                 | conductor server |
	      |       +------+-----+     +------+                  |
	      |       |            |     |      +------------------+
	      +-------> Tacker DB  <-----+
	              |            |
	              +-------------


(1) Since Mistral is an integral part of tacker system, a long-live Mistral
    workflow action can be used to do this kind of task.
    Tacker server will generate a VNF monitoring workflow and execute it if
    there is a VNF configured with monitor policies. The workflow and execution
    will be removed once the monitored target VDU is removed.

(2) Monitor actions cannot access tacker database directly, so we introduce a
    Tacker-conductor server to do database access for the mistral actions.

(3) Mistral does not stop long-live running action even if the workflow
    execution is deleted.
    So a mechanism is devised for action to exit. When the workflow is removed,
    the VNFM plugin will kill the mistral action via MSG queue.


Mistral action will use RPC to communicate with conductor server.
To deal with scalability of monitoring, multiple conductors will be deployed.

The mistral action communicates with the conductor via the following interface
VNFPolicyActionRPC:

.. code-block:: python

	class VNFPolicyActionRPC(object)
	  # execute policy action
	  def  execute_policy_action(context, vnf, monitor_return_value,
	                             policy_actions, action_id):
	     # The response message containing the operation result
	     # the status should be the passed in by request or 'bad_action'
	     # if the action is not the wanted action.
	     status = rpc call conductor
	     return status


After workflow is removed due to VNF change or removal, VNFM plugin kills the mistral
action via the following interface VNFPolicyMonitorRPC asynchronously:

.. code-block:: python

	class VNFPolicyMonitorRPC(object)
	  # kill the mistral action job
	  def  kill(context, action_id):
	     pass

      # update the mistral action job
      def update(context, action_id, parameter):
         pass


The update method in above interface is used to notify policy monitor that changes
happened on the monitored vnf, for example the VNF was scaled, and was respawned.

Sequence diagram for create VNF:

.. seqdiag::

  seqdiag {
    user  -> vnfmplugin [label = "create_vnf with monitor_policies property"];
    vnfmplugin -> vnfmplugin [label = "generate workflow with auto generated action id"];
    vnfmplugin -> vnfmplugin [label = "update vnf with monitor action id"];
    vnfmplugin -> mistral [label = "run the workflow to start vnf_policy_monitor"];
  }

Monitor policy is divided into two parts: policy monitor and policy action. Policy monitor,
such as ping and http_ping is implemented as mistral task action. Policy action will
be run in tacker conductor.

Each VNF with monitor policies will have a workflow generated, and will be kept as meta
information of VNF instance so that they can be managed.

.. seqdiag::

  seqdiag {
    === loop according to monitor policy ===
    vnf_policy_monitor -> conductor [label = "execute_policy_action"]
    conductor -> policy_action [label = "execute_action" ]
  }

The mistral workflow action will be run once the workflow is started. The action will do
its job according to monitor policy. When policy action is needed, the monitor action will
call conductor's execute_policy_action RPC method.

Method execute_policy_action in conductor will call policy action, which will do actual job,
such as respawn, log etc.

If the policy action needs to update the vnf_policy_monitor, it will notify vnf_policy_monitor
the change.

.. seqdiag::

  seqdiag {
      conductor -> vnf_policy_monitor [label = "update action job via RPC"]
  }

If conductor finds the action is obsolete, it will return bad_action to vnf_policy_monitor,
then the vnf_policy_monitor will exit.


Sequence diagram for update VNF:

No need for this operation to do workflow stuff since VNF update is just used to config
VDUs.


Sequence diagram for deleting VNF:

.. seqdiag::

  seqdiag {
    user  -> vnfmplugin [label = "delete_vnf with monitor_policies property"];
    vnfmplugin -> vnfmplugin [label = "get workflow with action id for the VNF"];
    vnfmplugin -> mistral [label = "delete workflow and its execution"];
    vnfmplugin -> vnf_policy_monitor [label = "kill action job via RPC"]
  }


Sequence diagram for scale VNF:

.. seqdiag::

  seqdiag {
    user  -> vnfmplugin [label = "scale_vnf with monitor_policies property"];
    vnfmplugin -> vnfmplugin [label = "get workflow with action id for the VNF"];
    vnfmplugin -> vnf_policy_monitor [label = "update action job via RPC"]
  }


Alternatives
------------

None

Data model impact
-----------------

VNF database will be extended to contain a Mistral action id column to record
the current action id.


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

Other developer impact
-----------------------

None

Developer impact
----------------

None


Implementation
==============

Assignee(s)
-----------
  Yong sheng gong <gong.yongsheng@99cloud.net>

  Nguyen Hai <nguyentrihai93@gmail.com> <nguyentrihai@soongsil.ac.kr>

  dharmendra <dharmendra.kushwaha@nectechnologies.in>


Milestones
----------

Target Milestone for completion:
  rocky-1


Work Items
----------

* Implement workflow version of monitor policy for VNF
* Unit Tests


Dependencies
============

* rabbitmq
* oslo message


Testing
=======

 This feature can be tested in these scenarios.

 To test the VNF instantiation scenario:

* setup up tacker system which will start tacker conductor servers
* onboard a VNFD with monitor policy under VDU properties and boot a VNF
* check the VNF monitor policy workflow is setup and there is a ping action
  is running on mistral executor component (take the ping policy for example)
* make the VDU VM un-accessable, to check if the related policy action will
  be called ( take the respawn action for example)
* to check if the policy monitor in mistral will monitor the new management IPs


 To test the VNF deletion scenario:

* onboard a VNFD with monitor policy under VDU properties
* check the VNF monitor policy workflow is setup and there is a ping action
  is running on mistral executor component (take the ping policy for example)
* To check if VNF is marked as active
* delete VNF and check if the mistral related stuff is removed


 To test the behaviour for scaled VNF:

* onboard a VNFD with monitor policy under VDU properties and scale policy
  and boot a VNF
* scale out the VNF and check if the policy monitor is pinging more than one
  management IPs
* scale in the VNF and check if the policy monitor is not pinging the removed
  IPs.


Documentation Impact
====================

* Change tacker deployment document
* Add a document about mistral workflow way to do actions in tacker server


References
==========

* https://docs.openstack.org/mistral/ocata/dsl/dsl_v2.html
