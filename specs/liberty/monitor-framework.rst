..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

====================================
Monitoring Framework for VNF Manager
====================================

https://blueprints.launchpad.net/tacker/+spec/health-monitor

Problem Description
===================
The VNF Manager needs to monitor various status conditions of the VNF entities
it deploys and manages.  Tacker currently supports a single method of
monitoring a VNF, pinging the management IP address.  Complex VNFs require
additional monitoring methods in order to be able to use Tacker as a VNF
Manager.

Proposed Change
===============

Expanding Tacker's ability to do simple monitoring and take advantage
of external monitoring systems is best accomplished with a driver model
similar to the existing Management and Infrastructure Drivers.

By duplicating the structure and implementation of the existing Management
Driver we can modularize the monitoring function and allow for
additional monitoring methods to be easily added.

This spec proposes the creation of a "mon_driver" under tacker/vm/drivers,
and moving the existing ping functionality into the new modular driver.

Alternatives
------------

The existing monitor framework could be extended with additional functionality
without changing the architecture. However by using drivers it will be
easier to use other monitoring projects such as Monasca and Ceilometer in the
future.

TOSCA Monitoring Framework Enhancements
=======================================

Monitoring Format
-----------------
::

    vduN:
      monitoring_policy:
        <monitoring-driver-name>:
          monitoring_params:
            <param-name>: <param-value>
            ...
          actions:
            <event>: <action-name>
            ...
        ...


Example Template
----------------
::

    vdu1:
      monitoring_policy:
        ping:
          actions:
            failure: respawn

    vdu2:
      monitoring_policy:
        http-ping:
          monitoring_params:
            port: 8080
            url: ping.cgi
          actions:
            failure: respawn

        acme_scaling_driver:
          monitoring_params:
            resource: cpu
            threshold: 10000
          actions:
            max_foo_reached: scale_up
            min_foo_reached: scale_down


The driver specified must exist as a loadable class in the
monitor_drivers directory structure and must be included in
the setup.cfg file so that it is loaded during the Tacker
server initialization.

The monitoring thread will use the global boot_wait configured
time (default is 30s) to delay the start of monitoring of the
VDU/VNF.  Monitoring will invoke the driver using the global
check_intvl interval time (default is 10s).

Both boot_wait and check_intvl should be moved to the template
at some point in the future so they can be specified at the
VDU level to provide more flexibility.

Monitoring Driver Parameters
----------------------------

Parameters can be specified for the driver and will be passed to
as kwargs.

Events and Actions
------------------

Events received from the driver will be mapped to the associated
action.  Events are driver-specific and are not pre-defined in
Tacker.

Actions are pre-defined in Tacker as follows:

- respawn
- scale_up (to be added by autoscaling feature)
- scale_down (to be added by autoscaling feature)

Data model impact
-----------------

- Add column "monitor_driver" to table DeviceTemplate

REST API impact
---------------

None

Security impact
---------------

Contributed drivers will need to be examind for security impact

Notifications impact
--------------------

There is no immediate impact for notifications.  It may be
beneficial to investigate the use of a Message Bus for both
internal and external notifications.

Other end user impact
---------------------

The existing syntax for monitoring_policy and failure_policy will be retained
for at least one release and deprecated.  The old syntax will be mapped into
the "ping" driver with action "respawn" so the functionality remains the same.

This syntax will be removed in a future release.

Performance Impact
------------------

The existing implementation uses a single thread to cycle through all of
the deployed VNFs, determine their status and respawn if needed.  This
will need to be extended into a thread for each VNF to help prevent threads
from blocking each other.  This will be examing as part of this effort
but may be deferred.

Other deployer impact
---------------------

VNF providers should follow the Tacker custom monitoring driver documentation
to add a custom monitoring driver.

Developer impact
----------------

VNF Developers should conform to this framework when developing custom monitor
drivers.


Assignee(s)
-----------

bobh - Bob Haddleton
tbh - Bharath Thiruveedula

Work Items
----------

- Create new monitor driver using the existing mgmt_driver as a
  model
- Implement the existing ping monitor as a module and remove
  existing implementation
- Document the interface requirements for providing a custom
  monitoring driver
- Unit tests need to be written to validate basic functionality
- Devref documentation of the monitor syntax is needed


Dependencies
============

The existing implementation assumes a single monitoring policy (ping)
will be applied to all of the VDUs, even if it is specified in only
one VDU.  The device data structure that is created by the infra
driver (heat) retries the monitoring_policy and failure_policy
attributes from the VDU definition and stores them at the device
(VNF) level.  This prevents different VDUs from having different
monitors specified.

In addition, the existing implementation uses the stack output,
which is a list of management IP addresses for the VDUs, as the
list of IP addresses to verify.



Testing
=======

Automated testing should include test VNF templates that use
each of the supported monitoring types.

Documentation Impact
====================

- Documentation of the driver interface is needed for future
  developers to create drivers


References
==========

[1] http://www.etsi.org/deliver/etsi_gs/NFV-MAN/001_099/001/01.01.01_60/gs_nfv-man001v010101p.pdf

[2] http://docs.oasis-open.org/tosca/tosca-nfv/v1.0/csd01/tosca-nfv-v1.0-csd01.html#_Toc421872062

[3] http://www.etsi.org/deliver/etsi_gs/NFV-REL/001_099/001/01.01.01_60/gs_nfv-rel001v010101p.pdf

