======================================================================
Support VNFM for AutoHeal and AutoScale with External Monitoring Tools
======================================================================

https://blueprints.launchpad.net/tacker/+spec/support-auto-lcm

Problem description
===================

Zed release supported Fault Management / Performance Management (FM/PM)
interfaces, and AutoHeal and AutoScale with
External Monitoring Tools [#Zed_Spec]_.
However, Heal or Scale execution must be triggered by NFVO.

This spec provides some implementations for supporting receiving alerts
from External Monitoring Tools and VNFM(tacker)-driven AutoHeal and
AutoScale without NFVO. This implementation only supports VNF and CNF
instantiated through Tacker's v2 API.

Proposed change
===============

The following changes are needed:

#. Add AutoHeal RESTful API to receive alerts sent from External Monitoring
   Tool.

   + POST /alert/auto_healing

#. Modify AutoScale RESTful API to receive alerts sent from External Monitoring
   Tool.

   + POST /alert/auto_scaling

#. Add fields in config file to determine if AutoHeal should be
   triggered or not.

.. note::

  The External Monitoring Tool is a monitoring service. That is not
  included in Tacker. Operators implement the External Monitoring
  Tool. The External Monitoring Tool uses metrics service such as
  Prometheus and triggers AutoHeal and AutoScale events using the
  Prometheus Plugin interface.

Prometheus Plugin
-----------------

The Prometheus Plugin is a sample implementation that operates Prometheus
specific function.
In this spec, there are two APIs in the Prometheus Plugin for receiving
requests sent by Prometheus, and then calling Tacker's Heal or Scale
interfaces.

The Prometheus Plugin is an optional feature. The AutoHeal and AutoScale
APIs can be enabled in ``tacker.conf``.

.. code-block::

  [prometheus_plugin]
  auto_healing = True
  auto_scaling = True

Triggering of AutoHeal
----------------------

When the External Monitoring Tool detects the VNF or CNF resource failure
or problem, it will send an alert message to Tacker.
Tacker receives the alert and validates it. Then Tacker calls the internal
Heal function for the resource.
Use this Heal method to repair the failure and problem of VNF or CNF
resources.

Design of Heal operation
~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of Heal:

.. code-block::

                              +--------------------------------------------------------------------------+
                              |                                                                     VNFM |
                              |  +------------------------+  +----------------------------+              |
                              |  |                 Tacker |  |                  Tacker    |              |
                              |  |                 Server |  |                  Conductor |              |
  +----------------+          |  |                        |  |                            |              |
  |  External      | 2. POST  |  |         3. Check parameters and confirm vnfc_info_id   |              |
  |  Monitoring    |    alert |  |  +------------+        |  |                            |  +--------+  |
  |  Tool          +----------------> Prometheus +-------------------------------------------> Tacker |  |
  |  (based on     |          |  |  | Plugin     |        |  |                            |  | DB     |  |
  |   Prometheus)  |          |  |  +------+-----+        |  |                            |  +--------+  |
  +--+-------------+          |  |         | 4. Heal      |  |                            |              |
     | 1. Collect metrics     |  |         |              |  |                            |              |
     |                        |  |  +------v-----+        |  |  +---------------+         |              |
     |                        |  |  | Vnflcm     +--------------> Vnflcm Driver +--+      |              |
     |                        |  |  | Controller |        |  |  +---------------+  |      |              |
     |                        |  |  +------------+        |  |           +---------v--+   |              |
     |                        |  |                        |  |           | Infra      +--------------+   |
     |                        |  |                        |  |           | Driver     |   |          |   |
     |                        |  |                        |  |           +------------+   |          |   |
     |                        |  +------------------------+  +----------------------------+          |   |
     |                        +----------------------------------------------------------------------|---+
     |                                                                                               |
     |                        +-----------------------------------------------------------------+    |
     |                        |                                                      Kubernetes |    |
     |                        |                  +---------------+-----------------------------------+
     |                        | 5. Delete failed |               | 6. Create new Pod            |    |
     |                        |    Pod           |               |                              |    |
     |                        |         +--------v----+   +------v------+    +-------------+    |    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |    |
     +----------------------------------> | Pod    |  |   | | Pod    |  |    |             |    |    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |    |
     |                        |         |      Worker |   |      Worker |    |      Master |    |    |
     |                        |         +-------------+   +-------------+    +-------------+    |    |
     |                        +-----------------------------------------------------------------+    |
     |                                                                                               |
     |                        +-----------------------------------------------------------------+    |
     |                        |                                                       OpenStack |    |
     |                        |                  +---------------+-----------------------------------+
     |                        | 5. Delete failed |               | 6. Create new VM             |
     |                        |    VM            |               |                              |
     |                        |         +--------v----+   +------v------+    +-------------+    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |
     +----------------------------------> | VM     |  |   | | VM     |  |    |             |    |
                              |         | +--------+  |   | +--------+  |    |             |    |
                              |         |    Compute  |   |    Compute  |    |  Controller |    |
                              |         +-------------+   +-------------+    +-------------+    |
                              +-----------------------------------------------------------------+

#. External Monitoring Tool collects metrics and decides whether
   triggering alert is needed or not.

#. External Monitoring Tool sends POST request to
   ``/alert/auto_healing``.

#. Prometheus Plugin receives the alert request and validates its content.
   Then it confirms that the ``vnfc_info_id`` in the alert request exists
   in the DB.

#. Heal operation is triggered.

#. The specified VM or Pod is deleted.

#. New VM or Pod is created.

Request parameters for operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

Sequence for operation
~~~~~~~~~~~~~~~~~~~~~~

The following describes the processing flow of the Tacker after
the External Monitoring Tool sends the alert.

.. seqdiag::

  seqdiag {
    node_width = 150;
    edge_length = 160;

    "External Monitoring Tool"
    "Prometheus Plugin"
    "Vnflcm Controller"
    "Vnflcm Driver"
    "Tacker DB"

    "External Monitoring Tool" -> "Prometheus Plugin"
      [label = "1. POST /alert/auto_healing"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "2. Check if this API is enabled in Prometheus Plugin"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "3. Check the status of the received alert"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "4. Check if this alert is for AutoHeal"];
    "Prometheus Plugin" -> "Tacker DB"
      [label = "5. Find the corresponding resource from the DB"];
    "Prometheus Plugin" <-- "Tacker DB"
      [label = "vnf_instance"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "6. Check whether the resource has AutoHeal enabled"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "7. Check vnfc_info_id in vnf_instance"];
    "Prometheus Plugin" -> "Vnflcm Controller"
      [label = "8. Call the internal Heal function"];
    "Vnflcm Controller" -> "Vnflcm Driver"
      [label = "9. Trigger asynchronous task", note = "The same with the default Heal operation"];
    "Prometheus Plugin" <-- "Vnflcm Controller"
      [label = "Response 202 Accepted"];
    "External Monitoring Tool" <-- "Prometheus Plugin"
      [label = "Response 204 No Content"];
  }

#. As an External Monitoring Tool, Prometheus monitors specified resources
   through user-defined rules. When the data monitored by Prometheus matches
   the conditions of the rule, Prometheus will send an alert to Tacker.

#. After Tacker receives the alert, Prometheus Plugin first checks that the
   value of the ``auto_healing`` field in ``tacker.conf`` is True. If not,
   the process is terminated.

#. Prometheus Plugin checks that the value of the ``status`` field in alert
   is ``firing``. If not, the process is terminated.

#. Prometheus Plugin checks that the value of the ``function_type`` field
   in alert is ``auto_heal``. If not, the process is terminated.

#. According to the value of ``vnf_instance_id`` in the label in the alert,
   Prometheus Plugin gets the corresponding ``vnf_instance`` from the DB.

#. Prometheus Plugin checks that the key of ``isAutohealEnabled`` exists in
   ``vnf_instance.vnfConfigurableProperties`` and its value is True. If
   not, the process is terminated.

#. Prometheus Plugin checks that the value of ``vnfc_info_id`` in the alert
   request exists in ``vnf_instance.vnfc_info``.

#. According to the values of ``vnf_instance_id`` and ``vnfc_info_id``,
   Prometheus Plugin calls the internal Heal function of vnflcm.

#. From this step, it is completely the same with the default Heal operation.


.. note::

  The default Heal operation is ``all = False`` and
  specified VNFC instances are healed.
  When ``all = True`` is set, specified VNFC instances and
  storage resources are healed.

.. note::

  When multiple alerts occur, the alerts should be aggregated or filtered.
  This implementation will prevent repeated heal operations.

Triggering of AutoScale
-----------------------

When the External Monitoring Tool detects that the CPU, memory, disk and
other resources of the VNF or CNF are underloaded or overloaded, it will
send an alert message to Tacker. Tacker receives the alert and validates
it. Then Tacker calls the internal Scale function for the resource. Use
this Scale method to balance underloaded or overloaded VNF or CNF resources.

Design of Scale operation
~~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of Scale:

.. code-block::

                              +--------------------------------------------------------------------------+
                              |                                                                     VNFM |
                              |  +------------------------+  +----------------------------+              |
                              |  |                 Tacker |  |                  Tacker    |              |
                              |  |                 Server |  |                  Conductor |              |
  +----------------+          |  |                        |  |                            |              |
  |  External      | 2. POST  |  |         3. Check parameters and confirm aspect_id      |              |
  |  Monitoring    |    alert |  |  +------------+        |  |                            |  +--------+  |
  |  Tool          +----------------> Prometheus +-------------------------------------------> Tacker |  |
  |  (based on     |          |  |  | Plugin     |        |  |                            |  | DB     |  |
  |   Prometheus)  |          |  |  +------+-----+        |  |                            |  +--------+  |
  +--+-------------+          |  |         | 4. Scale     |  |                            |              |
     | 1. Collect metrics     |  |         |              |  |                            |              |
     |                        |  |  +------v-----+        |  |  +---------------+         |              |
     |                        |  |  | Vnflcm     +--------------> Vnflcm Driver +--+      |              |
     |                        |  |  | Controller |        |  |  +---------------+  |      |              |
     |                        |  |  +------------+        |  |           +---------v--+   |              |
     |                        |  |                        |  |           | Infra      +--------------+   |
     |                        |  |                        |  |           | Driver     |   |          |   |
     |                        |  |                        |  |           +------------+   |          |   |
     |                        |  +------------------------+  +----------------------------+          |   |
     |                        +----------------------------------------------------------------------|---+
     |                                                                                               |
     |                        +-----------------------------------------------------------------+    |
     |                        |                                                      Kubernetes |    |
     |                        |                  +---------------+-----------------------------------+
     |                        |                  |               | 5. Create or Delete Pod      |    |
     |                        |                  |               |                              |    |
     |                        |         +--------v----+   +------v------+    +-------------+    |    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |    |
     +----------------------------------> | Pod    |  |   | | Pod    |  |    |             |    |    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |    |
     |                        |         |      Worker |   |      Worker |    |      Master |    |    |
     |                        |         +-------------+   +-------------+    +-------------+    |    |
     |                        +-----------------------------------------------------------------+    |
     |                                                                                               |
     |                        +-----------------------------------------------------------------+    |
     |                        |                                                       OpenStack |    |
     |                        |                  +---------------+-----------------------------------+
     |                        |                  |               | 5. Create or Delete VM       |
     |                        |                  |               |                              |
     |                        |         +--------v----+   +------v------+    +-------------+    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |
     +----------------------------------> | VM     |  |   | | VM     |  |    |             |    |
                              |         | +--------+  |   | +--------+  |    |             |    |
                              |         |    Compute  |   |    Compute  |    |  Controller |    |
                              |         +-------------+   +-------------+    +-------------+    |
                              +-----------------------------------------------------------------+

#. External Monitoring Tool collects metrics and decides whether
   triggering alert is needed or not.

#. External Monitoring Tool sends POST request to
   ``/alert/auto_scaling``.

#. Prometheus Plugin receives the alert request and validates its content.
   Then it confirms that the ``aspect_id`` in the alert request exists in
   the DB.

#. Scale out/in operations are triggered.

#. There are two types of Scale processing:

   * If the Scale out operation is triggered, the VM or Pod in the
     corresponding VDU is created.

   * If the Scale in operation is triggered, the VM or Pod in the
     corresponding VDU is deleted.

Request parameters for operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

Sequence for operation
~~~~~~~~~~~~~~~~~~~~~~

The following describes the processing flow of
the Tacker after the External Monitoring Tool sends the alert.

.. seqdiag::

  seqdiag {
    node_width = 150;
    edge_length = 160;

    "External Monitoring Tool"
    "Prometheus Plugin"
    "Vnflcm Controller"
    "Vnflcm Driver"
    "Tacker DB"

    "External Monitoring Tool" -> "Prometheus Plugin"
      [label = "1. POST /alert/auto_scaling"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "2. Check if this API is enabled in Prometheus Plugin"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "3. Check the status of the received alert"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "4. Check if this alert is for AutoScale"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "5. Check that the received alert contains a valid type of Scale"];
    "Prometheus Plugin" -> "Tacker DB"
      [label = "6. Find the corresponding resource from the DB"];
    "Prometheus Plugin" <-- "Tacker DB"
      [label = "vnf_instance"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "7. Check whether the resource has AutoScale enabled"];
    "Prometheus Plugin" -> "Prometheus Plugin"
      [label = "8. Check aspect_id in vnf_instance"];
    "Prometheus Plugin" -> "Vnflcm Controller"
      [label = "9. Call the internal Scale function"];
    "Vnflcm Controller" -> "Vnflcm Driver"
      [label = "10. Trigger asynchronous task", note = "The same with the default Scale operation"];
    "Prometheus Plugin" <-- "Vnflcm Controller"
      [label = "Response 202 Accepted"];
    "External Monitoring Tool" <-- "Prometheus Plugin"
      [label = "Response 204 No Content"];
  }

#. As an External Monitoring Tool, Prometheus monitors specified resources
   through user-defined rules. When the data monitored by Prometheus matches
   the conditions of the rule, Prometheus will send an alert to Tacker.

#. After Tacker receives the alert, Prometheus Plugin first checks that
   the value of the ``auto_scaling`` field in ``tacker.conf`` is True. If
   not, the process is terminated.

#. Prometheus Plugin checks that the value of the ``status`` field in alert
   is ``firing``. If not, the process is terminated.

#. Prometheus Plugin checks that the value of the ``function_type`` field
   in alert is ``auto_scale``. If not, the process is terminated.

#. Prometheus Plugin checks that the value of the ``auto_scale_type`` field
   in alert must be ``SCALE_OUT`` or ``SCALE_IN``. If not, the process is
   terminated.

#. According to the value of ``vnf_instance_id`` in the label in the
   alert, Prometheus Plugin gets the corresponding ``vnf_instance`` from
   the DB.

#. Prometheus Plugin checks that the key of ``isAutoscaleEnabled`` exists in
   ``vnf_instance.vnfConfigurableProperties`` and its value is True. If
   not, the process is terminated.

#. Prometheus Plugin checks that the value of ``aspect_id`` in the alert
   request exists in ``vnf_instance.scale_status``.

#. According to the values of ``vnf_instance_id``, ``auto_scale_type``
   and ``aspect_id``, Prometheus Plugin calls the internal Scale
   function of vnflcm.

#. From this step, it is completely the same with the default Scale operation.

.. note::

  The default Scale operation is ``numberOfSteps = 1`` and
  one VNFC instance is scaled.

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

The following RESTful API is Tacker specific interface
used for AutoHeal between Tacker and External Monitoring Tool.

* | **Name**: Send an AutoHeal alert event
  | **Description**: Receive the AutoHeal alert sent from External
    Monitoring Tool
  | **Method type**: POST
  | **URL for the resource**: /alert/auto_healing
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - AutoHealAlertEvent
      - 1
      - the AutoHeal alert sent from External Monitoring Tool

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AutoHealAlertEvent)
      - Data type
      - Cardinality
      - Description
    * - alerts
      - Structure
      - 1..N
      - List of all alert objects in this group.
    * - >status
      - String
      - 1
      - Defines whether or not the alert is resolved or currently firing.
    * - >labels
      - Structure
      - 1
      - A set of labels to be attached to the alert.
    * - >>receiver_type
      - String
      - 1
      - Type of receiver: tacker
    * - >>function_type
      - String
      - 1
      - Type of function: auto_heal
    * - >>vnfInstanceId
      - Identifier
      - 1
      - Identifier of vnf instance.
    * - >>vnfcInfoId
      - String
      - 1
      - Identifier of vnfc info.
    * - >startsAt
      - DateTime
      - 1
      - The time the alert started firing.
    * - >endsAt
      - DateTime
      - 0..1
      - The end time of an alert.
    * - >fingerprint
      - String
      - 1
      - Fingerprint that can be used to identify the alert.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 204
      - Shall be returned when a request has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_331]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_331]_ may be returned.

The following RESTful API is Tacker specific interface
used for AutoScale between Tacker and External Monitoring Tool.

* | **Name**: Send an AutoScale alert event
  | **Description**: Receive the AutoScale alert sent from External
    Monitoring Tool
  | **Method type**: POST
  | **URL for the resource**: /alert/auto_scaling
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - AutoScaleAlertEvent
      - 1
      - the AutoScale alert sent from External Monitoring Tool

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AutoScaleAlertEvent)
      - Data type
      - Cardinality
      - Description
    * - alerts
      - Structure
      - 1..N
      - List of all alert objects in this group.
    * - >status
      - String
      - 1
      - Defines whether or not the alert is resolved or currently firing.
    * - >labels
      - Structure
      - 1
      - A set of labels to be attached to the alert.
    * - >>receiver_type
      - String
      - 1
      - Type of receiver: tacker
    * - >>function_type
      - String
      - 1
      - Type of function: auto_scale
    * - >>auto_scale_type
      - String
      - 1
      - Type of Scale: SCALE_OUT or SCALE_IN
    * - >>vnfInstanceId
      - Identifier
      - 1
      - Identifier of vnf instance.
    * - >>aspectId
      - String
      - 1
      - The target VDU to Scale.
    * - >startsAt
      - DateTime
      - 1
      - The time the alert started firing.
    * - >endsAt
      - DateTime
      - 0..1
      - The end time of an alert.
    * - >fingerprint
      - String
      - 1
      - Fingerprint that can be used to identify the alert.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - n/a
      -
      - Success: 204
      - Shall be returned when a request has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_331]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_331]_ may be returned.

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
  Kenta Fukaya <kenta.fukaya.xv@hco.ntt.co.jp>

  Yuta Kazato <yuta.kazato.nw@hco.ntt.co.jp>

Other contributors:
  Koji Shimizu <shimizu.koji@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

Work Items
----------

* Implement Tacker to support:

  * External Monitoring interface

    * Add new Rest API ``POST /alert/auto_healing``
      to receive the AutoHeal alert sent from External Monitoring Tool.
    * Modify Rest API ``POST /alert/auto_scaling``
      to receive the AutoScale alert sent from External Monitoring Tool.

* Add new unit and functional tests.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

* Complete user guide will be added to explain how to AutoHeal and
  AutoScale by External Monitoring Tool.

* Update API documentation on the API additions mentioned in
  `REST API impact`_.

References
==========

.. [#Zed_Spec] https://specs.openstack.org/openstack/tacker-specs/specs/zed/prometheus-plugin-autoheal-and-autoscale.html

.. [#NFV-SOL013_331] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.03.01_60/gs_nfv-sol013v030301p.pdf
