..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================================
VNF Workflows Customization by Action Driver
============================================

Problem description
===================

ETSI NFV doesn't define Lifecycle Management (LCM) workflow behaviors.
Currently, Tacker has a default LCM workflow, VNF vendors can't change the default workflow.
The default workflow doesn't satisfy some VNF's LCM requirements.

* For healing, evacuation is used instead of deletion and creation.

We want to enable VNF vendor to customize their workflows by Action Driver.

Proposed change
===============

This proposal suggests providing the Action Driver function to flexibly choose
customized LCM workflows. Expanding Tacker's ability is best accomplished with
a driver model similar to the existing Management and Infrastructure Drivers.

Currently, Mgmt Driver function configures applications provided by VNF vendors.
So we should also enable VNF vendors to customize configuration methods
for applications via Mgmt Driver.

These customizations are specified by "interface" definition in
ETSI NFV-SOL001 [#NFV-SOL001]_ "6.7 Interface Types".

Overview of Action Driver function is as follows
(Concrete non-standard driver implementations are future works.
Only import Python implementation drivers is the first scope.):

::

  +------------------+                             interface of Lifecycle
  |                  |        +-----------------+         +-----------------+           +----------------+
  |                  |        |                 |         |                 |           |                |
  |  VNFM API        +------->+  VNF Lifecycle  +-----+-->+  Action Driver  +---------->+  Infra Driver  |
  |                  |        |  Management     |     |   |                 |           |                |
  |                  |        |                 |     |   |                 +-+         |                +-+
  |                  |        +-----------------+     |   +-+---------------+ |         +-+--------------+ |
  +------------------+                                |     | [standard]      |           | OpenStack_T    |
                                                      |     | Instantiate     |           | OpenStack_V    |
                                                      |     | Heal_evacuate   |           | Kubernetes_3   |
                                                      |     | Heal_recreate   |           | :              |
                                                      |     |                 |           +----------------+
                                                      |     | [custom]        |
                                                      |     | Heal_evacuate   |
                                                      |     |                 |
                                                      |     | [mistral WF]    |
                                                      |     | (Future work)   |
                                                      |     | Instantiate_    |
                                                      |     |           VNF_A |
                                                      |     | Instantiate_    |
                                                      |     |           VNF_B |
                                                      |     |                 |
                                                      |     +-----------------+
                                                      |
                                                      |     +----------------+
                                                      +---->+                |
                                       interface of         |  Mgmt Driver   |
                                       Lifecycle start/end  |                |
                                       (xxx_start/xxx_end)  |                +-+
                                                            +-+--------------+ |
                                                              | Ansible        |
                                                              | cloud+init     |
                                                              | Kubernetes     |
                                                              | :              |
                                                              +----------------+


Flow of instantiation of a VNF instance with Action Driver is as follows:

::

  +----------+     +---------------+    +-----------+     +---------------+     +--------------+
  |          |     |               |    |           |     |               |     |              |
  | VNFM API |     | VNF Lifecycle |    | Tacker DB |     | Action Driver |     | Mgmt Driver  |
  |          |     | Management    |    |           |     |               |     |              |
  |          |     |               |    |           |     |               |     |              |
  +----+-----+     +------+--------+    +-----+-----+     +-------+-------+     +------+-------+
       |                  |                   |                   |                    |
       | Instantiate VNF  |                   |                   |                    |
       +------------------>                   |                   |                    |
       <- - - - - - - - - +   Fetch action    |                   |                    |
       |    (async)       |   from vnfd_dict  |                   |                    |
       |                  |                   |                   |                    |
       |                  +------------------->                   |                    |
       |                  <-------------------+                   |                    |
       |                  |                   |                   |                    |
       |                  |                   |                   |                    |
       |                  | mgmt_call(        |                   |                    |
       |                  | method='instantiate_start')           |                    |
       |                  |                   |                   |                    |
       |                  +----------------------------------------------------------->|
       |                  <------------------------------------------------------------+
       |                  |                   |                   |                    |
       |                  |                   |                   |                    |
       |                  | action_call(      |                   |                    |
       |                  | method='action_instantiate_vnf')      |                    |
       |                  |                   |                   |                    |
       |                  +--------------------------------------->     +------+       |
       |                  |                   |                   |     |Infra |       |
       |                  |                   |                   |     |Driver|       |
       |                  |                   |                   |     +---+--+       |
       |                  |                   |                   |         |          |
       |                  |                   |                   |         |          |
       |                  |                   |                   | instantiate_vnf    |
       |                  |                   |                   |         |          |
       |                  |                   |                   +--------->          |
       |                  |                   |                   <---------+          |
       |                  <---------------------------------------+         |          |
       |                  |                   |                   |         +          |
       |                  |                   |                   |                    |
       |                  | mgmt_call(        |                   |                    |
       |                  | method='instantiate_end')             |                    |
       |                  |                   |                   |                    |
       |                  +----------------------------------------------------------->|
       |                  <------------------------------------------------------------+
       |                  |                   |                   |                    |
       |                  |                   |                   |                    |
       +                  +                   +                   +                    +

How to Define the Drivers
-------------------------
Action Driver and Mgmt Driver are specified by VNFD.

How to specify Action Driver is as follows:

::

  node_templates:
    VNF:
      type: tacker.sample.VNF
      properties:
        flavour_description: A simple flavour
      interfaces:
        Vnflcm:
          instantiate:
            implementation: action-drivers-custom
  .
  .
  .
      artifacts:
        action-drivers-custom:
          description: Action driver standard
          type: tosca.artifacts.Implementation.Python
          file: /usr/local/lib/python3.6/site-packages/tacker/vnfm/action_drivers/custom_action_driver_1.py

How to specify Mgmt Driver is as follows:

::

  node_templates:
    VNF:
      type: tacker.sample.VNF
      properties:
        flavour_description: A simple flavour
      interfaces:
        Vnflcm:
          instantiate: []
          instantiate_start:
            implementation: mgmt-drivers-noop
          instantiate_end:
            implementation: mgmt-drivers-custom
          terminate: []
          terminate_start: []
          terminate_end: []

      artifacts:
        mgmt-drivers-custom:
          description: Management driver custom
          type: tosca.artifacts.Implementation.Python
          file: /usr/local/lib/python3.6/site-packages/tacker/vnfm/mgmt_drivers/custom_mgmt.py

      artifacts:
        mgmt-drivers-noop:
          description: Management driver noop
          type: tosca.artifacts.Implementation.Python
          file: /usr/local/lib/python3.6/site-packages/tacker/vnfm/mgmt_drivers/noop.py

In the case that we use artifacts in VNF package,
we write relative path as the value of 'file:' in 'artifacts:' block.

The following is the default VNFD description
which specify all driver implementations as standard.
i.e. We can customize the following implementations.

::

  interfaces:
    Vnflcm:
      instantiate: []
      instantiate_start: []
      instantiate_end: []
      terminate: []
      terminate_start: []
      terminate_end: []
      heal: []
      heal_start: []
      heal_end: []
      scale: []
      scale_start: []
      scale_end: []


Action Driver Directories Structure
-----------------------------------
This spec proposes the creation of a "action_drivers" under tacker/vnfm.

::

  tacker
  |-- plugin.py
  |-- vnfm
      |-- action_drivers
          |-- abstract_driver.py
          |-- custom_action_driver_1.py
          |-- custom_action_driver_2.py
          :

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

Users can specify LCM action and pre/post setting with VNFD.

Performance impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

None

Implementations
===============

Assignee(s)
-----------

Primary assignee:

1. Toshiaki Takahashi

Work Items
----------

* Action Driver main process
* Cooperation with existing Mgmt Driver Framework
* Calling Action Driver process from LCM process
* VNFD reading and Action Driver setting
* Unit tests
* Functional tests

Dependencies
============

Testing
=======

Unit and functional tests are sufficient to test specified process
written in VNFD is called correctly.

Documentation Impact
====================

* Add document about how to customize LCM with Action Driver

References
==========

.. [#NFV-SOL001] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/02.06.01_60/gs_NFV-SOL001v020601p.pdf
