..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

..
 This template should be in ReSTructured text. The filename in the git
 repository should match the launchpad URL, for example a URL of
 https://blueprints.launchpad.net/tacker/+spec/awesome-thing should be named
 awesome-thing.rst .  Please do not delete any of the sections in this
 template.  If you have nothing to say for a whole section, just write: None
 For help with syntax, see http://sphinx-doc.org/rest.html
 To test out your formatting, see http://www.tele3.cz/jbar/rest/rest.html

========================================
Tacker support in python-openstackclient
========================================

https://blueprints.launchpad.net/tacker/+spec/tacker-support-python-openstackclient

Implement a new set of tacker commands as python-openstackclient plugins.

Problem description
===================

python-openstackclient is becoming the default command line client for many
OpenStack projects. Tacker would benefit from implementing all of its client
commands as python-openstackclient plugins implemented in the python-tackerclient
repository.

Proposed change
===============

The intent of this spec is to identify the commands to be implemented and
establish conventions for command and argument names. This spec is not intented
to be a full and correct specification of command and argument names.

The following conventions will be adopted for argument flags:

- When the name/ID is specified it will be the first positional argument
  after the full command names
- When the resource name is specified it will be the second positional argument
  after the name/ID.
- ``show`` and ``list`` commands should show an appropriate quantity of data
  by default and ``--short`` or ``--long`` arguments will display a different
  level of details.

For certain commands which conflict with other OpenStack projects,'nfv'
is prefixed to differentiate the commands. The commands that may conflict
include ``network-service``, ``classifier``, ``nfp``, ``chain`` and ``event``.

The following ``tacker`` commands will be implemented for ``openstack`` initially
suggesting these command names:


VNF Commands
------------

::

  tacker vnf-create
  openstack vnf create

  tacker vnf-delete
  openstack vnf delete

  tacker vnf-list
  openstack vnf list

  tacker vnf-resource-list
  openstack vnf resource list

  tacker vnf-scale
  openstack vnf scale

  tacker vnf-show
  openstack vnf show

  tacker vnf-update
  openstack vnf set

  tacker vnfd-create
  openstack vnf descriptor create

  tacker vnfd-delete
  openstack vnf descriptor delete

  tacker vnfd-list
  openstack vnf descriptor list

  tacker vnfd-show
  openstack vnf descriptor show

  tacker vnfd-template-show
  openstack vnf descriptor template show

VIM commands
------------

::

  tacker vim-list
  openstack vim list

  tacker vim-register
  openstack vim register

  tacker vim-show
  openstack vim show

  tacker vim-update
  openstack vim set

  tacker vim-delete
  openstack vim delete


Network Service Commands
------------------------

::

  tacker ns-create
  openstack ns create

  tacker ns-delete
  openstack ns delete

  tacker ns-list
  openstack ns list

  tacker ns-show
  openstack ns show

  tacker nsd-create
  openstack ns descriptor create

  tacker nsd-delete
  openstack ns descriptor delete

  tacker nsd-list
  openstack ns descriptor list

  tacker nsd-show
  openstack ns descriptor show

  tacker nsd-template-show
  openstack ns descriptor template show

VNFFG Commands
-------------------

::

  tacker vnffg-create
  openstack vnf graph create

  tacker vnffg-delete
  openstack vnf graph delete

  tacker vnffg-list
  openstack vnf graph list

  tacker vnffg-show
  openstack vnf graph show

  tacker vnffg-update
  openstack vnf graph set

  tacker vnffgd-create
  openstack vnf graph descriptor create

  tacker vnffgd-delete
  openstack vnf graph descriptor delete

  tacker vnffgd-list
  openstack vnf graph descriptor list

  tacker vnffgd-show
  openstack vnf graph descriptor show

  tacker vnffgd-template-show
  openstack vnf graph descriptor template show

VNFFG - Service Function Chain commands
---------------------------------------

::

 tacker chain-list
 openstack vnf chain list

 tacker chain-show
 openstack vnf chain show

VNFFG - Flow Classifier Commands
--------------------------------

::

 tacker classifier-list
 openstack vnf classifier list

 tacker classifier-show
 openstack vnf classifier show

VNFFG - Network Forwarding Path
-------------------------------

::

  tacker nfp-list
  openstack vnf network forwarding path list

  tacker nfp-show
  openstack vnf network forwarding path show

Event Commands
--------------

::

  tacker event-show
  openstack nfv event show

  tacker events-list
  openstack nfv event list

Alternatives
------------

- Continue to evolve ``tacker`` commands and do not implement any ``openstack``
  commands.
- Instead of implementing this inside python-tackerclient, create a new project
  which depends on python-tackerclient and python-openstackclient.

Implementation
==============

Assignee(s)
-----------

  Trinath Somanchi <trinath.somanchi@nxp.com>

  yong sheng gong <gong.yongsheng@99cloud.net>

  dharmendra kushwaha <dharmendra.kushwaha@nectechnologies.in>

  Nguyen Hai <nguyentrihai93@gmail.com> <nguyentrihai@soongsil.ac.kr>

  Srikanth Kumar Lingala <srikanth.lingala@nxp.com>

  Veera Reddy B <veera.b@nxp.com>


Milestones
----------

Target Milestone for completion:
  rocky-1

Work Items
----------

Work items or tasks -- break the feature up into the things that need to be
done to implement it. Those parts might end up being done by different people,
but we're mostly trying to understand the timeline for implementation.


Dependencies
============
OpenStack Client Command list
- https://docs.openstack.org/developer/python-openstackclient/command-list.html
