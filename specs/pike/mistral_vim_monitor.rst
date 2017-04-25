..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Scalable VIM Monitor using Mistral
==========================================

https://blueprints.launchpad.net/tacker/+spec/refactor-vim-monitor


Problem description
===================

currently, a thread will be started by tacker server once a vim is registered,
which is not scalable:

 * if we have a lot of vims, the tacker server will have to run a lot of threads
   to monitor them, which will impact the API function of tacker server

 * if the tacker server restarts, the monitor thread will not start

 * cannot run more than one tacker server



Proposed change
===============

asciiflow::

	                             +---------------------+
	                             | mistral workflow    |
	                     +-------> vim monitor action  |
	+--------------+     |       |                     |
	| Tacker server+-----+       +------------------+--+
	+-----+--------+                                |
	      |                                         |
	      |                                         |
	      |                                 +-------v----------+
	      |                                 |                  |
	      |                                 | conductor server |
	      |       +------------+     +------+                  |
	      |       |            |     |      +------------------+
	      +-------> tacker DB  <-----+
	              |            |
	              +-------------


Since Mistral is an integral part of tacker system, a long-live Mistral workflow
action can be used to do this kind of task.

Tacker server will generate a VIM reachability test workflow and execute it if
a new vim is registered. The workflow and execution will be removed once the
vim is de-registered from tacker server.

Vim monitor actions cannot access tacker database directly, so we introduce a conductor
server to do database access for the mistral actions.

Mistral does not stop long-live running action even if the workflow execution is deleted.
So a mechanism is devised for action to exit. Every 1 minute, action will contact the
conductor to see if it is the wanted action class, if it is not the one, the action should
exit the loop and exit. To deal with scalability of lots of VIM, load balancer can be
placed before conductor(s).

Mistral action will use RPC to communicate with conductor server. Ping action communicates
with the conductor via the following interface VimMonitor:

.. code-block:: python

	class VimMonitorAction2ConductorRPC(object)
	  # update vim's status, action_id is the task action
	  def update_vim (vim_id, status, action_id):
	     # The response message containing the operation result
	     # the status should be the passed in by request or 'bad_action'
	     # if the action is not the wanted action.
	     status = rpc call conductor
	     return status


sequence diagram for register vim:

.. seqdiag::

  seqdiag {
    user  -> nfvoplugin [label = "register_vim"];
    nfvoplugin -> nfvoplugin [label = "generate workflow with auto generated action id"];
    nfvoplugin -> nfvoplugin [label = "update vim with monitor action id"];
    nfvoplugin -> mistral [label = "run the workflow"];
    mistral_vim_monitor_action -> conductor [label = "update_vim"]
  }


sequence diagram for de-register vim:

.. seqdiag::

  seqdiag {
    user  -> nfvoplugin [label = "de_register_vim"];
    nfvoplugin -> nfvoplugin [label = "remove monitor workflow"];
    nfvoplugin -> nfvoplugin [label = "remove vim from db"];
    mistral_vim_monitor_action -> conductor [label = "update_vim"];
    mistral_vim_monitor_action <-- conductor [label = "replies with bad_action"];
    mistral_vim_monitor_action -> mistral_vim_monitor_action [label = "exit"];
  }


sequence diagram for update vim with auth url change:

.. seqdiag::

  seqdiag {
    user  -> nfvoplugin [label = "update_vim"];
    nfvoplugin -> nfvoplugin [label = "remove old monitor workflow"];
    nfvoplugin -> nfvoplugin [label = "generate workflow with auto generated action uuid"];
    nfvoplugin -> nfvoplugin [label = "update vim with monitor action uuid"];
    nfvoplugin -> mistral [label = "run the workflow"];
    new_mistral_vim_monitor_action -> conductor [label = "update_vim"]
    new_mistral_vim_monitor_action <-- conductor
    old_mistral_vim_monitor_action -> conductor [label = "update_vim"]
    old_mistral_vim_monitor_action <-- conductor [label = "replies with bad_action"];
    old_mistral_vim_monitor_action -> old_mistral_vim_monitor_action [label = "exit"];
  }


Alternatives
------------

Another way to use mistral is to use a loop workflow:

asciiflow::

	start_task -----> ping_task ------> update_task
	                      ^               |
	                      |               |
	                      |               |
	                      |   on_succes   |
	                       ---------------+


But Mistral will save task executions into Mistral database, so the loop
workflow will populate mistral db with thousands of ping_task and update_task
records for each VIM, which will impact Mistral DB.


Data model impact
-----------------

VIM database will be extended to contain a Mistral action id column to record
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

A new RPC server will be started, and Load balancer can be used for more
than one tacker conductor deployment.

And this will help to deploy more than one tacker servers

Developer impact
----------------

None


Implementation
==============

Assignee(s)
-----------


Primary assignee:
  gongysh

Other contributors:
  <launchpad-id or None>

Work Items
----------

 * refactor work flow codes in tacker server
 * implement workflow version of vim reachability monitor
 * Unit Tests


Dependencies
============

 * rabbitmq
 * oslo message


Testing
=======

 this feature can be tested by the following steps:

 * setup up tacker system which will start tacker conductor servers
 * register a vim
 * check the vim monitor workflow is setup and there is a ping action
   is running on mistral executor component
 * de-register the vim to check if the mistral action will exit


Documentation Impact
====================

 * change tacker deployment document
 * add a document about mistral workflow way to do actions in tacker server


References
==========

 * https://docs.openstack.org/developer/mistral/dsl/dsl_v2.html
