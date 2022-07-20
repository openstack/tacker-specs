=======
|title|
=======

.. |title| replace:: Support AutoHeal and AutoScale with
                     External Monitoring Tools via FM/PM Interfaces

https://blueprints.launchpad.net/tacker/+spec/support-auto-lcm

Problem description
===================

This spec provides some implementations for supporting AutoHeal and AutoScale
with external monitoring tools such as Prometheus [#Prometheus]_.
The implementations includes ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_ based
Fault Management / Performance Management interface
and a sample implementation of Prometheus Plugin.

The Fault Management and Performance Management interfaces are specified
in ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_, NFVO or EM takes the initiative
in making decisions on healing or scaling.

The Prometheus Plugin has a interface that is called from the External
Monitoring Tool and supports data model conversion related to Prometheus
monitoring data.

.. note::
   * If there are no special instructions, the Client described in
     this spec default to NFVO/EM, and VNFM default to Tacker.

Proposed change
===============

The following changes are needed:

#. Add support for Fault Management interface specified in
   SOL002/003

   + Add VNF Fault Management interface:

     + Get Alarm(s)

       + GET /vnffm/v1/alarms to get all alarms.
       + GET /vnffm/v1/alarms/{alarmId} to get the specified alarm.

     + Acknowledge Alarm

       + PATCH /vnffm/v1/alarms/{alarmId}
         to change target Alarm to be confirmed.

     + Subscribe

       + POST /vnffm/v1/subscriptions to create a new subscription.

     + Get Subscription(s)

       + GET /vnffm/v1/subscriptions to get all subscriptions.
       + GET /vnffm/v1/subscriptions/{subscriptionId}
         to get the specified subscription.

     + Delete Subscription

       + DELETE /vnffm/v1/subscriptions/{subscriptionId}
         to delete the specified subscription.

   + Send notification to Client

     + POST <Client URI from subscriptions>
       to notify Client that Tacker received an alarm.
     + GET <Client URI from subscriptions>
       to confirm that the URI of Client is correct.

#. Add support for Performance Management interface specified in
   SOL002/003

   + Add VNF Performance Management interface:

     + Create or Update a PM job

       + POST /vnfpm/v2/pm_jobs to create a PM job.
       + PATCH /vnfpm/v2/pm_jobs/{pmJobId} to update the specified PM job.

     + Get PM job(s)

       + GET /vnfpm/v2/pm_jobs to get all PM jobs.
       + GET /vnfpm/v2/pm_jobs/{pmJobId} to get the specified PM job.

     + Delete a PM job

       + DELETE /vnfpm/v2/pm_jobs/{pmJobId} to delete the specified PM job.

     + Get PM report

       + GET /vnfpm/v2/pm_jobs/{pmJobId}/reports/{reportId}
         to get the specified performance report.

   + Send notification to Client

     + POST <Client URI for notifications>
       to notify Client that Tacker received a PM related event.
     + GET <Client URI for notifications>
       to confirm that the URI of Client is correct.

#. Add support of RESTful API for communications between
   Tacker and External Monitoring Tool

   + POST /alert
     to receive the FM alert sent from External Monitoring Tool.
   + POST /pm_event
     to receive the PM event sent from External Monitoring Tool.

#. Create new DB tables

   + Create a new DB table for FM alarms.

   + Create a new DB table for FM subscription.

   + Create a new DB table for PM jobs.

   + Create a new DB table for PM reports.

.. note::
  * The External Monitoring Tool is a monitoring service.
    That is not included in Tacker.
    Operators implement the External Monitoring Tool.
    The External Monitoring Tool uses metrics service such as
    Prometheus and notifies FM/PM events using the Prometheus Plugin interface.

Prometheus Plugin
-----------------

The Prometheus Plugin is a sample implementation that operates
Prometheus specific function such as converting from
Prometheus specific data model to
SOL002/003 [#SOL002_v3.3.1]_ [#SOL003_v3.3.1]_ compliant data model.

The Prometheus Plugin is an optional feature. Tacker will decide whether
to enable it according to the content of the configuration file.
The detail of configuration file is described in
[#Alert_server_for_Prometheus_with_Kubernetes_cluster_VNF_sample]_.

AutoHeal on FM alert trigger
----------------------------

When the External Monitoring Tool detects that the CNF has failed,
it will send alert messages to Tacker. Tacker will convert the alert
to alarm and store it in the DB.

NFVO/EM gets alarm periodically (Polling Mode)
or triggered by notification (Notification Mode)
via FM interface based on SOL002/003 [#SOL002_v3.3.1]_ [#SOL003_v3.3.1]_.

The Polling Mode is a method in which NFVO/EM periodically inquiries about
monitoring information from VNFM. and The Notification Mode is a method
in which VNFM notifies NFVO/EM in the Subscribe/Notify subscription model.

Design of heal operation in FM Polling Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of heal in Polling Mode:

.. code-block:: console

                                  +------------------------+
                                  |                        |
                                  |    Client (NFVO/EM)    |
                                  |                        |
                                  +--+---------+-----------+
                             5. Heal |         | 4. Get Alarms and return result
                              +------|---------|------------------------------------------------------------+
                              |      |         |                                                       VNFM |
                              |  +---|---------|---------+ +---------------------------------+              |
                              |  |   |         |  Tacker | |                      Tacker     |              |
                              |  |   |         |  Server | |                      Conductor  |              |
                              |  |   |   +-----v------+  | |                                 |   +--------+ |
                              |  |   |   | VnfFm      +------------------------------------------> Tacker | |
  +----------------+          |  |   |   | Controller |  | |         +--------------+        |   |   DB   | |
  |  External      |          |  |   |   +------------+  | |  +------+ VnfFm        +------------>        | |
  |  Monitoring    |          |  |   |                   | |  |      | Driver       |        |   +--------+ |
  |  Tool          | 2. POST  |  |   |                   | |  |      +--------------+        |              |
  |  (based on     |    alert |  |   |   +------------+  | |  | 3. Convert alert to alarm    |              |
  |   Prometheus)  +---------------------> Prometheus +-------+                              |              |
  +--+-------------+          |  |   |   | Plugin     |  | |                                 |              |
     ^                        |  |   |   +------------+  | |                                 |              |
     | 1. Collect metrics     |  |   |                   | |                                 |              |
     |                        |  |   |   +------------+  | |         +--------------+        |              |
     |                        |  |   +---> Vnflcm     +--------------> VmfLcmDriver +---+    |              |
     |                        |  |       | Controller |  | |         +--------------+   |    |              |
     |                        |  |       +------------+  | |                  +---------v--+ |              |
     |                        |  |                       | |                  | Infra      | |              |
     |                        |  |                       | |                  | Driver     | |              |
     |                        |  |                       | |                  +----+-------+ |              |
     |                        |  +-----------------------+ +-----------------------|---------+              |
     |                        +----------------------------------------------------|------------------------+
     |                                                                             |
     |                        +----------------------------------------------------|------------+
     |                        |  CISM/CIS                                          |            |
     |                        |                  +---------------+-----------------+            |
     |                        | 6. Delete failed |               | 7. Create new                |
     |                        |    CNF           |               |    CNF                       |
     |                        |         +--------v----+   +------v------+    +-------------+    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |
     +----------------------------------> | CNF    |  |   | | CNF    |  |    |             |    |
                              |         | +--------+  |   | +--------+  |    |             |    |
                              |         |      Worker |   |      Worker |    |      Master |    |
                              |         +-------------+   +-------------+    +-------------+    |
                              +-----------------------------------------------------------------+

#. External Monitoring Tool collects metrics and decides whether
   triggering alert is needed or not.

#. External Monitoring Tool sends POST request to
   `/alert/vnf_instances/{vnf_instance_id}`.

#. Tacker receives informed alert, converts it to alarm,
   and saves it to Tacker DB.

#. The Client sends a request at regular intervals to get
   the alarm in the Tacker.
   Tacker searches Tacker DB with the query condition specified by the Client,
   and returns the alarm that matches the condition to the Client.

#. The Client recognizes the failure of the CNF from the alarm and
   sends a heal request to the Tacker.

#. Heal operation is triggered, old CNF is deleted.

#. New CNF is created.

Request parameters for operation in FM Polling Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

.. _sequence-fm-polling:

Sequence for operation in FM Polling Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following describes the processing flow of the Tacker after
the External Monitoring Tool sends the alert.

.. seqdiag::

  seqdiag {
    node_width = 100;
    edge_length = 150;

    "External Monitoring Tool"
    "Prometheus-Plugin"
    "VnfFmDriver"
    "Tacker DB"

    "External Monitoring Tool" -> "Prometheus-Plugin"
      [label = "1. Send alert to the specified URI"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "2. Check items of prometheus_plugin from cfg.CONF.tacker", note = "If prometheus_plugin is False, asynchronous task is over"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "3. Determine whether the alert is AutoHeal or AutoScale", note = "If it is scale, refer to the processing flow of AutoScale"];
    "Prometheus-Plugin" -> "Tacker DB"
      [label = "4. Find the corresponding ComputeResource from the DB"];
    "Prometheus-Plugin" <-- "Tacker DB"
      [label = "InstantiatedVnfInfo.vnfcResourceInfo.computeResource"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "5. Convert received alert to alarm"];
    "Prometheus-Plugin" -> "VnfFmDriver"
      [label = "6. Execute VnfFmDriver"];
    "VnfFmDriver" -> "Tacker DB"
      [label = "7. Save alarm to DB"];
    "VnfFmDriver" <-- "Tacker DB"
    "Prometheus-Plugin" <-- "VnfFmDriver"
  }

#. External Monitoring Tool detects fault event via Prometheus and inform the
   alert to specified URI(Tacker).

#. Prometheus Plugin obtains values from ``cfg.CONF.tacker.prometheus_plugin``
   to determine whether to enable this function.

#. Prometheus Plugin judges what kind of action to be performed
   according to the ``function_type`` field of the labels
   in the alert.

   * When the ``labels.function_type`` is ``vnffm``,
     AutoHeal is performed.

   * When the ``labels.function_type`` is ``vnfpm``,
     AutoScale is performed. See :ref:`sequence-pm-operation`.

#. Prometheus Plugin finds the corresponding CNF instance according to the
   value of the label in the alert.

#. Prometheus Plugin converts the alert to an alarm.

#. Prometheus Plugin calls VnfFmDriver and sends the alarm to it.

#. VnfFmDriver saves the alarm in the DB.

The following describes the Client's processing flow for
Tacker using Polling Mode to AutoHeal.

.. seqdiag::

  seqdiag {
    node_width = 100;
    edge_length = 150;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfFmDriver"
    "Tacker DB"

    "Client" -> "Tacker-server"
      [label = "8. Get alarms"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "9. Trigger synchronization task"];
    "Tacker-conductor" -> "VnfFmDriver"
      [label = "10. Get alarms"];
    "VnfFmDriver" -> "Tacker DB"
      [label = "11. Get alarms from DB according to conditions"];
    "VnfFmDriver" <-- "Tacker DB"
      [label = "Alarms"];
    "Tacker-conductor" <-- "VnfFmDriver"
      [label = "Alarms"];
    "Tacker-server" <-- "Tacker-conductor"
      [label = "Alarms"];
    "Client" <-- "Tacker-server"
      [label = "Alarms"];
    "Client" -> "Client"
      [label = "12. Get VNFC information from alarm", note = "If no alarm is returned, the processing is over"];
    "Client" -> "Tacker-server"
      [label = "13. Heal specified vnfc"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "14. Trigger asynchronous task", note = "The same with the default heal operation"];
    "Client" <-- "Tacker-server"
      [label = "Response 202 Accepted"];
  }


8. The Client sends a request to the Tacker to get the alarms of
   the specified conditions.

#. The request is processed synchronously.

#. Tacker-conductor calls VnfFmDriver to get the alarm.

#. VnfFmDriver filters out the alarms that meet the conditions according
   to the conditions in the request, and returns the result.

#. After the Client obtains the VNFC information from the alarm,
   it sends a request to the Tacker to heal the VNFC.

#. From this step, it is completely the same with
   the default heal operation.

Design of heal operation in FM Notification Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of heal in Notification Mode:

.. code-block:: console

                                  +------------------------+
                                  |                        |       5. Send alarm notification
                                  |   Client (NFVO/EM)     <-------------------+
                                  |                        |                   |
                                  +--+---------+-----------+                   |
                             6. Heal |         | 1. Create subscription        |
                              +------|---------|-------------------------------|----------------------------+
                              |      |         |                               |                       VNFM |
                              |  +---|---------|---------+ +-------------------|-------------+              |
                              |  |   |         |  Tacker | |                   |  Tacker     |              |
                              |  |   |         |  Server | |                   |  Conductor  |              |
                              |  |   |   +-----v------+  | |                   |             |   +--------+ |
                              |  |   |   | VnfFm      +------------------------+-----------------> Tacker | |
  +----------------+          |  |   |   | Controller |  | |         +---------+----+        |   | DB     | |
  |  External      |          |  |   |   +------------+  | |  +------> VnfFm        +------------>        | |
  |  Monitoring    |          |  |   |                   | |  |      | Driver       |        |   +--------+ |
  |  Tool          | 3. POST  |  |   |                   | |  |      +--------------+        |              |
  |  (based on     |    alert |  |   |   +------------+  | |  |  4. Convert alert to alarm   |              |
  |   Prometheus)  +---------------------> Prometheus +-------+                              |              |
  +--+-------------+          |  |   |   | Plugin     |  | |                                 |              |
     ^                        |  |   |   +------------+  | |                                 |              |
     | 2. Collect metrics     |  |   |                   | |                                 |              |
     |                        |  |   |   +------------+  | |         +--------------+        |              |
     |                        |  |   +---> Vnflcm     +--------------> VmfLcmDriver +---+    |              |
     |                        |  |       | Controller |  | |         +--------------+   |    |              |
     |                        |  |       +------------+  | |                  +---------v--+ |              |
     |                        |  |                       | |                  | Infra      | |              |
     |                        |  |                       | |                  | Driver     | |              |
     |                        |  |                       | |                  +----+-------+ |              |
     |                        |  +-----------------------+ +-----------------------|---------+              |
     |                        +----------------------------------------------------|------------------------+
     |                                                                             |
     |                        +----------------------------------------------------|------------+
     |                        |  CISM/CIS                                          |            |
     |                        |                  +---------------+-----------------+            |
     |                        | 7. Delete failed |               | 8. Create new                |
     |                        |    CNF           |               |    CNF                       |
     |                        |         +--------v----+   +------v------+    +-------------+    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |
     +----------------------------------> | CNF    |  |   | | CNF    |  |    |             |    |
                              |         | +--------+  |   | +--------+  |    |             |    |
                              |         |      Worker |   |      Worker |    |      Master |    |
                              |         +-------------+   +-------------+    +-------------+    |
                              +-----------------------------------------------------------------+



#. The Client sends a request to the Tacker to create a subscription.

   .. note::

      During the create subscription, Tacker sends a test notification
      request to the client's callback URI. The callback URI is included
      in the request parameter of the create subscription request.

#. Same as step 1 of the Polling Mode.

#. Same as step 2 of the Polling Mode.

#. Same as step 3 of the Polling Mode.

#. VnfFmDriver finds all subscriptions in the DB and matches
   the alerts to them. If there is a subscription that can match
   successfully, the alarm is sent to the specified path of the
   Client. If the match is not successful, the processing ends.

#. Same as step 5 of the Polling Mode.

#. Same as step 6 of the Polling Mode.

#. Same as step 7 of the Polling Mode.

Request parameters for operation in FM Notification Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

Sequence for operation in FM Notification Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following describes the Client's processing flow for
Tacker using Notification Mode to AutoHeal.

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 100;

    "Client"
    "External Monitoring Tool"
    "Prometheus-Plugin"
    "Tacker-server"
    "Tacker-conductor"
    "VnfFmDriver"
    "Tacker DB"

    "Client" -> "Tacker-server"
      [label = "1. Create subscription"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "Trigger synchronization task"];
    "Tacker-conductor" -> "VnfFmDriver"
      [label = "execute VnfFmDriver"];
    "VnfFmDriver" -> "VnfFmDriver"
      [label = "Get the callback_uri in the subscription"];
    "VnfFmDriver" -> "Client"
      [label = "Send a GET request to the callback_uri in the Client."];
    "VnfFmDriver" <-- "Client"
      [label = "Response 204 No Content"];
    "VnfFmDriver" -> "Tacker DB"
      [label = "Save subscription to DB"];
    "VnfFmDriver" <-- "Tacker DB"
    "Tacker-conductor" <-- "VnfFmDriver"
    "Tacker-server" <-- "Tacker-conductor"
    "Client" <-- "Tacker-server"
      [label = "Response 201 Created"];
    "External Monitoring Tool" -> "Prometheus-Plugin"
      [label = "2. Send alert to the specified URI"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "3. Check items of prometheus_plugin from cfg.CONF.tacker", note = "If prometheus_plugin is False, asynchronous task is over"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "4. Determine whether the alert is AutoHeal or AutoScale", note = "If it is scale, refer to the processing flow of AutoScale"];
    "Prometheus-Plugin" -> "Tacker DB"
      [label = "5. Find the corresponding ComputeResource from the DB"];
    "Prometheus-Plugin" <-- "Tacker DB"
      [label = "InstantiatedVnfInfo.vnfcResourceInfo.computeResource"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "6. Convert received alert to alarm"];
    "Prometheus-Plugin" -> "VnfFmDriver"
      [label = "7. execute VnfFmDriver"];
    "VnfFmDriver" -> "Tacker DB"
      [label = "8. Save alarm to DB"];
    "VnfFmDriver" <-- "Tacker DB"
    "VnfFmDriver" -> "Tacker DB"
      [label = "9. Get subscriptions from DB"];
    "VnfFmDriver" <-- "Tacker DB"
    "VnfFmDriver" -> "VnfFmDriver"
      [label = "10. Determine whether the alarm matches the subscriptions.", note = "If it does not match, the processing ends"];
    "VnfFmDriver" -> "Client"
      [label = "11. Send a Notify Alarm request to the Client"];
    "VnfFmDriver" <-- "Client"
      [label = "Response 204 No Content"];
    "Prometheus-Plugin" <-- "VnfFmDriver"
    "Client" -> "Client"
      [label = "12. Get VNFC information from alarm", note = "If no alarm is returned, the processing is over"];
    "Client" -> "Tacker-server"
      [label = "13. Heal specified vnfc"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "14. Trigger asynchronous task", note = "The same with the default heal operation"];
    "Client" <-- "Tacker-server"
      [label = "Response 202 Accepted"];
  }

#. The Client sends a request to create a subscription to the Tacker.
   After Tacker receives the subscription, it will get the callback_uri in it.
   In order to verify the correctness of the callback_uri,
   VnfFmDriver sends a request to the callback_uri address of Client.
   After getting the normal response HTTP 204 No Content from the Client,
   the Tacker will save the subscription to the DB.

From step 2 to 8, processes are same as step 1-7 of the Polling method.

9. VnfFmDriver gets all the subscriptions in the DB.

#. VnfFmDriver judges whether the alarm can be matched with subscriptions,
   if it does not match, the processing ends.

#. If the match is successful, VnfFmDriver sends a Notify Alarm request
   to the Client's callback_uri address. After the Client receives the
   request and processes it, it returns HTTP 204 No Content by default.

From step 12 to 14, processes are same as step 12-14 of the Polling method.

AutoScale on PM event trigger
-----------------------------

Tacker has a configuration value in tacker.conf file that indicates
uri of alert manager. Prometheus Plugin converts from PM job schema
to prometheus schema when a PM job has been created.

When the External Monitoring Tool detects that the CNF
have some PM events, it will send event messages to Tacker.
After Tacker receives the event, it will convert the event to report and
store it in the DB. At this time, according to
SOL002/003 [#SOL002_v3.3.1]_ [#SOL003_v3.3.1]_ 6. VNF Performance
Management interface.

Design of scale operation in PM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of scale:

.. code-block:: console

                                  +------------------------+
                                  |                        |       8. Send report notification
                                  |   Client (NFVO/EM)     <-------------------+
                                  |                        |                   |
                                  +--+---------+-----------+                   |
                                     |         | 1. Create PM job              |
                          10.  Scale |         | 9. Get PM report              |
                              +------|---------|-------------------------------|----------------------------+
                              |      |         |                               |                       VNFM |
                              |  +---|---------|---------+ +-------------------|-------------+              |
                              |  |   |         |  Tacker | |                   |  Tacker     |              |
                              |  |   |         |  Server | |                   |  Conductor  |              |
                              |  |   | +-------v------+  | |                   |             |   +--------+ |
                              |  |   | | VnfPm        +------------------------+-----------------> Tacker | |
                              |  |   | | ControllerV2 |  | |         +---------+----+        |   | DB     | |
  +----------------+          |  |   | +---------+----+  | |  +------> VnfPm        +------------>        | |
  |  External      |          |  |   | 2. set    |       | |  |      | DriverV2     |        |   +--------+ |
  |  Monitoring    | 5. POST  |  |   |    PM job |       | |  |      +--------------+        |              |
  |  Tool          |    event |  |   |   +-------v----+  | |  | 7. Convert event to report   |              |
  |  (based on     +---------------------> Prometheus +-------+                              |              |
  |   Prometheus)  <---------------------+ Plugin     |  | |                                 |              |
  |                | 6. get related data |            |  | |                                 |              |
  |                <---------------------+            |  | |                                 |              |
  +--+-------------+ 3. set   |  |   |   +------------+  | |                                 |              |
     ^                 PM job |  |   |                   | |                                 |              |
     | 4. Trigger event       |  |   |   +------------+  | |         +--------------+        |              |
     |                        |  |   +---> Vnflcm     +--------------> VmfLcmDriver +---+    |              |
     |                        |  |       | Controller |  | |         +--------------+   |    |              |
     |                        |  |       +------------+  | |                  +---------v--+ |              |
     |                        |  |                       | |                  | Infra      | |              |
     |                        |  |                       | |                  | Driver     | |              |
     |                        |  |                       | |                  +----+-------+ |              |
     |                        |  +-----------------------+ +-----------------------|---------+              |
     |                        +----------------------------------------------------|------------------------+
     |                                                                             |
     |                        +----------------------------------------------------|------------+
     |                        |  CISM/CIS                                          |            |
     |                        |                  +---------------+-----------------+            |
     |                        |                  |               | 11. Create or Delete         |
     |                        |                  |               |     CNF                      |
     |                        |         +--------v----+   +------v------+    +-------------+    |
     |                        |         | +--------+  |   | +--------+  |    |             |    |
     +----------------------------------> | CNF    |  |   | | CNF    |  |    |             |    |
                              |         | +--------+  |   | +--------+  |    |             |    |
                              |         |      Worker |   |      Worker |    |      Master |    |
                              |         +-------------+   +-------------+    +-------------+    |
                              +-----------------------------------------------------------------+

#. The Client sends a request to the Tacker to create a PM job.

   .. note::

      During the create PM job, Tacker sends a test notification
      request to the client's callback URI. The callback URI is included
      in request body of create PM job request.

#. VnfPmControllerV2 sends PM job information to Prometheus Plugin.

#. Prometheus Plugin sets PM job to External Monitoring Tool.

#. External Monitoring Tool collects metrics and decides whether
   triggering event is needed or not.

#. External Monitoring Tool sends POST request to Tacker with specified URI.

#. Tacker collects data related to the PM event.
   From the data obtained in 5-6,
   The value and context corresponding to performanceMetric
   are determined.

#. Tacker receives informed event, converts it to report, and saves it to DB.
   Tacker also saves timestamp of the event.

#. VnfPmDriverV2 finds all jobs in the DB and matches
   the report to job. If there is a job that can match
   successfully, the report is sent to the specified path of the
   Client. If the match is not successful, the processing ends.

#. The Client make a request for the content of the report, then
   make a decision of scaling.

#. Scale operation is triggered, new CNF is created
   in case of scale-out or old CNF is deleted in case
   of scale-in.

#. New CNF is created or old CNF is deleted.

Request parameters for operation in PM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

.. _sequence-pm-operation:

Sequence for operation in PM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following describes the Client's processing flow for
Tacker to AutoScale.

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 100;

    "Client"
    "External Monitoring Tool"
    "Prometheus-Plugin"
    "Tacker-server"
    "Tacker-conductor"
    "VnfPmDriverV2"
    "Tacker DB"

    "Client" -> "Tacker-server"
      [label = "1. Create PM job"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "Trigger synchronization task"];
    "Tacker-conductor" -> "VnfPmDriverV2"
      [label = "execute VnfPmDriverV2"];
    "VnfPmDriverV2" -> "VnfPmDriverV2"
      [label = "Get the callback_uri in the PM job"];
    "VnfPmDriverV2" -> "Client"
      [label = "Send a GET request to the callback_uri in the Client."];
    "VnfPmDriverV2" <-- "Client"
      [label = "Response 204 No Content"];
    "VnfPmDriverV2" -> "Tacker DB"
      [label = "Save PM job to DB"];
    "VnfPmDriverV2" <-- "Tacker DB"
    "VnfPmDriverV2" -> "Prometheus-Plugin"
      [label = "Set PM job to Prometheus-Plugin"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "Convert to Prometheus format PM job"];
    "Prometheus-Plugin" -> "External Monitoring Tool"
      [label = "Set PM job"];
    "Prometheus-Plugin" <-- "External Monitoring Tool"
    "VnfPmDriverV2" <-- "Prometheus-Plugin"
    "Tacker-conductor" <-- "VnfPmDriverV2"
    "Tacker-server" <-- "Tacker-conductor"
    "Client" <-- "Tacker-server"
      [label = "Response 201 Created"];
    "External Monitoring Tool" -> "Prometheus-Plugin"
      [label = "2. Send event to the specified URI"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "3. Check items of prometheus_plugin from cfg.CONF.tacker", note = "If prometheus_plugin is False, asynchronous task is over"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "4. Determine whether the report is AutoHeal or AutoScale", note = "If it is heal, refer to the processing flow of AutoHeal"];
    "Prometheus-Plugin" -> "Tacker DB"
      [label = "5. Find the corresponding resource from the DB"];
    "Prometheus-Plugin" <-- "Tacker DB"
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "6. Convert received event to report"];
    "Prometheus-Plugin" -> "VnfPmDriverV2"
      [label = "7. execute VnfPmDriverV2"];
    "VnfPmDriverV2" -> "Tacker DB"
      [label = "8. Save report to DB"];
    "VnfPmDriverV2" <-- "Tacker DB"
    "VnfPmDriverV2" -> "Tacker DB"
      [label = "9. Get job from DB"];
    "VnfPmDriverV2" <-- "Tacker DB"
    "VnfPmDriverV2" -> "VnfPmDriverV2"
      [label = "10. Determine whether the report matches the PM job.", note = "If it does not match, the processing ends"];
    "VnfPmDriverV2" -> "Client"
      [label = "11. Send a Notify Event request to the Client"];
    "VnfPmDriverV2" <-- "Client"
      [label = "Response 204 No Content"];
    "Prometheus-Plugin" <-- "VnfPmDriverV2"
    "Client" -> "Client"
      [label = "12. Get VNFC information from report", note = "If no report is returned, the processing is over"];
    "Client" -> "Tacker-server"
      [label = "13. Scale"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "14. Trigger asynchronous task", note = "The same with the default scale operation"];
    "Client" <-- "Tacker-server"
      [label = "Response 202 Accepted"];
  }

#. The Client sends a request to create a PM job to the Tacker.
   After Tacker receives the PM job, it will get the callback_uri in it.
   In order to verify the correctness of the callback_uri,
   VnfPmDriverV2 sends a request to the callback_uri address of Client.
   After getting the normal response HTTP 204 No Content from the Client,
   the Tacker will save the subscription to the DB.

#. VnfPmDriverV2 sends a PM job to Prometheus Plugin.
   Prometheus Plugin converts it into Prometheus format, then sends it to
   Prometheus.

#. External Monitoring Tool receives event sent from Prometheus and inform the
   event to specified URI(Tacker).

#. Prometheus Plugin obtains values from cfg.CONF.tacker.prometheus_plugin
   to determine whether to enable this function.

#. Prometheus Plugin judges what processing to perform according to
   the function_type field of the labels in the event.

   * When the ``labels.function_type`` is ``vnffm``,
     AutoHeal is performed. See :ref:`sequence-fm-polling`.

   * When the ``labels.function_type`` is ``vnfpm``,
     AutoScale is performed.

#. Prometheus Plugin finds the corresponding resource information
   according to the value of the node label in the event.

#. Prometheus Plugin converts the event to an report.

#. Prometheus Plugin calls VnfPmDriverV2 and sends the report
   to it.

#. VnfPmDriverV2 saves the report in the DB.

#. VnfPmDriverV2 gets all the PM job in the DB.

#. VnfPmDriverV2 judges whether the report can be matched with PM jobs,
   if it does not match, the processing ends.

#. If the match is successful, VnfPmDriverV2 sends a Notify Event request
   to the Client's callback_uri address. After the Client receives the
   request and processes it, it returns HTTP 204 No Content by default.

#. After the Client obtains the VNFC information from the report,
   it sends a request to the Tacker to scale the VNFC.

#. From this step, it is completely the same with
   the default scale operation.

Alternatives
------------

None

Data model impact
-----------------

Add below new db table in 'Tacker' database.

* | **Table**: AlarmV1

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Type
      - Constraint
    * - id
      - varchar(255)
      - Pri
    * - managedObjectId
      - varchar(255)
      - NOT NULL
    * - vnfcInstanceIds
      - JSON
      - NULL
    * - rootCauseFaultyResource
      - JSON
      - NULL
    * - alarmRaisedTime
      - datetime
      - NOT NULL
    * - alarmChangedTime
      - datetime
      - NULL
    * - alarmClearedTime
      - datetime
      - NULL
    * - alarmAcknowledgedTime
      - datetime
      - NULL
    * - ackState
      - Enum
      - NOT NULL
    * - perceivedSeverity
      - Enum
      - NOT NULL
    * - eventTime
      - datetime
      - NOT NULL
    * - eventType
      - Enum
      - NOT NULL
    * - faultType
      - varchar(255)
      - NULL
    * - probableCause
      - varchar(255)
      - NOT NULL
    * - isRootCause
      - boolean
      - NOT NULL
    * - correlatedAlarmIds
      - JSON
      - NULL
    * - faultDetails
      - JSON
      - NULL


  This table have `id` as primary key.
  `managedObjectId` will be foreign
  key of `vnf_instances`.

* | **Table**: FmSubscriptionV1

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Type
      - Constraint
    * - id
      - varchar(255)
      - Pri
    * - filter
      - JSON
      - NULL
    * - callbackUri
      - varchar(255)
      - NOT NULL
    * - authentication
      - JSON
      - NULL

  This table have `id` as primary key.

* | **Table**: PmJobV2

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Type
      - Constraint
    * - id
      - varchar(255)
      - Pri
    * - objectType
      - varchar(32)
      - NOT NULL
    * - objectInstanceIds
      - JSON
      - NOT NULL
    * - subObjectInstanceIds
      - JSON
      - NULL
    * - criteria
      - JSON
      - NOT NULL
    * - callbackUri
      - varchar(255)
      - NOT NULL
    * - reports
      - JSON
      - NULL
    * - authentication
      - JSON
      - NULL

  This table have `id` as primary key.

* | **Table**: PerformanceReportV2

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Type
      - Constraint
    * - id
      - varchar(255)
      - Pri
    * - jobId
      - varchar(255)
      - NOT NULL
    * - entries
      - JSON
      - NULL

  This table have `id` as primary key.

REST API impact
---------------

The following RESTful APIs are in compliance with
SOL002/003 [#SOL002_v3.3.1]_ [#SOL003_v3.3.1]_
6.VNF Performance Management interface and
7.VNF Fault Management interface.

* | **Name**: Get all alarms
  | **Description**: Allow users to filter out alarms
                     based on query parameter in the request
  | **Method type**: GET
  | **URL for the resource**: /vnffm/v1/alarms
  | **Query parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - filter
      - 0..1
      - Attribute-based filtering expression.
        The following attribute names shall be supported by the Tacker in the attribute-based
        filtering expression: id, managedObjectId,
        rootCauseFaultyResource/faultyResourceType, eventType, perceivedSeverity, probableCause.
        For example, below URI query parameter will matching alarms with
        perceivedSeverity=WARNING

        .. code-block:: console

           GET /vnffm/v1/alarms?filter=(eq,perceivedSeverity,WARNING)

  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - Alarm
      - 0..N
      - Success: 200
      - Shall be returned when information about zero or more
        alarms has been queried successfully.
    * - ProblemDetails
      - 1
      - Error: 400
      - Invalid attribute-based filtering expression.
        The response body shall contain a ProblemDetails
        structure, in which the "detail" attribute should convey
        more information about the error.
    * - ProblemDetails
      - 1
      - Error: 400
      - Response too big.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (Alarm)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this Alarm information element.
    * - managedObjectId
      - Identifier
      - 1
      - Identifier of the affected VNF instance.
    * - vnfcInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the affected VNFC instances.
    * - rootCauseFaultyResource
      - FaultyResourceInfo
      - 0..1
      - The virtualised resources that are causing the VNF
        fault. Shall be present if the alarm affects virtualised
        resources.
    * - >faultyResource
      - ResourceHandle
      - 1
      - Information that identifies the faulty resource instance
        and its managing entity.
    * - >>vimConnectionId
      - Identifier
      - 0..1
      - Identifier of the VIM connection to manage the resource.
        This attribute shall only be supported and present if VNFrelated
        resource management in direct mode is
        applicable.
        The applicable "VimConnectionInfo" structure, which is
        referenced by vimConnectionId, can be obtained from
        the "vimConnectionInfo" attribute of the "VnfInstance"
        structure.
    * - >>resourceProviderId
      - Identifier
      - 0..1
      - Identifier of the entity responsible for the management of
        the resource.
        This attribute shall only be supported and present when
        VNF-related resource management in indirect mode is
        applicable. The identification scheme is outside the
        scope of the present document.
    * - >>resourceId
      - IdentifierInVim
      - 1
      - Identifier of the resource in the scope of the VIM or the
        resource provider.
    * - >>vimLevelResourceType
      - String
      - 0..1
      - Type of the resource in the scope of the VIM or the
        resource provider. See note.
    * - >faultyResourceType
      - FaultyResourceType
      - 1
      - Type of the faulty resource.
        COMPUTE: Virtual compute resource,
        STORAGE: Virtual storage resource,
        NETWORK: Virtual network resource
    * - alarmRaisedTime
      - DateTime
      - 1
      - Time stamp indicating when the alarm is raised by
        the managed object.
    * - alarmChangedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was last
        changed. It shall be present if the alarm has been
        updated.
    * - alarmClearedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was cleared.
        It shall be present if the alarm has been cleared.
    * - alarmAcknowledgedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was
        acknowledged. It shall be present if the alarm has
        been acknowledged.
    * - ackState
      - Enum
      - 1
      - Acknowledgement state of the alarm.
        Permitted values: UNACKNOWLEDGED, ACKNOWLEDGED.
    * - perceivedSeverity
      - PerceivedSeverityType
      - 1
      - Perceived severity of the managed object failure.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - eventTime
      - DateTime
      - 1
      - Time stamp indicating when the fault was observed.
    * - eventType
      - EventType
      - 1
      - Type of event.
    * - faultType
      - String
      - 0..1
      - Additional information to clarify the type of the fault.
    * - probableCause
      - String
      - 1
      - Information about the probable cause of the fault.
    * - isRootCause
      - Boolean
      - 1
      - Attribute indicating if this fault is the root for other
        correlated alarms. If true, then the alarms listed in
        the attribute "correlatedAlarmIds" are caused by this
        fault.
    * - correlatedAlarmIds
      - Identifier
      - 0..N
      - List of identifiers of other alarms correlated to this
        fault.
    * - faultDetails
      - String
      - 0..N
      - Provides additional information about the fault.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >objectInstance
      - Link
      - 0..1
      - Link to the resource representing the VNF instance
        to which the notified alarm is correlated. Shall be
        present if the VNF instance information is
        accessible as a resource.

* | **Name**: Get the individual alarm
  | **Description**: Get the alarm specified in the Tacker.
  | **Method type**: GET
  | **URL for the resource**: /vnffm/v1/alarms/{alarmId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - Alarm
      - 1
      - Success: 200
      - Shall be returned when information about an
        individual alarm has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (Alarm)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this Alarm information element.
    * - managedObjectId
      - Identifier
      - 1
      - Identifier of the affected VNF instance.
    * - vnfcInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the affected VNFC instances.
    * - rootCauseFaultyResource
      - FaultyResourceInfo
      - 0..1
      - The virtualised resources that are causing the VNF
        fault. Shall be present if the alarm affects virtualised
        resources.
    * - >faultyResource
      - ResourceHandle
      - 1
      - Information that identifies the faulty resource instance
        and its managing entity.
    * - >>vimConnectionId
      - Identifier
      - 0..1
      - Identifier of the VIM connection to manage the resource.
        This attribute shall only be supported and present if VNFrelated
        resource management in direct mode is
        applicable.
        The applicable "VimConnectionInfo" structure, which is
        referenced by vimConnectionId, can be obtained from
        the "vimConnectionInfo" attribute of the "VnfInstance"
        structure.
    * - >>resourceProviderId
      - Identifier
      - 0..1
      - Identifier of the entity responsible for the management of
        the resource.
        This attribute shall only be supported and present when
        VNF-related resource management in indirect mode is
        applicable. The identification scheme is outside the
        scope of the present document.
    * - >>resourceId
      - IdentifierInVim
      - 1
      - Identifier of the resource in the scope of the VIM or the
        resource provider.
    * - >>vimLevelResourceType
      - String
      - 0..1
      - Type of the resource in the scope of the VIM or the
        resource provider. See note.
    * - >faultyResourceType
      - FaultyResourceType
      - 1
      - Type of the faulty resource.
        COMPUTE, STORAGE, NETWORK
    * - alarmRaisedTime
      - DateTime
      - 1
      - Time stamp indicating when the alarm is raised by
        the managed object.
    * - alarmChangedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was last
        changed. It shall be present if the alarm has been
        updated.
    * - alarmClearedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was cleared.
        It shall be present if the alarm has been cleared.
    * - alarmAcknowledgedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was
        acknowledged. It shall be present if the alarm has
        been acknowledged.
    * - ackState
      - Enum
      - 1
      - Acknowledgement state of the alarm.
        Permitted values: UNACKNOWLEDGED, ACKNOWLEDGED.
    * - perceivedSeverity
      - PerceivedSeverityType
      - 1
      - Perceived severity of the managed object failure.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - eventTime
      - DateTime
      - 1
      - Time stamp indicating when the fault was observed.
    * - eventType
      - EventType
      - 1
      - Type of event.
    * - faultType
      - String
      - 0..1
      - Additional information to clarify the type of the fault.
    * - probableCause
      - String
      - 1
      - Information about the probable cause of the fault.
    * - isRootCause
      - Boolean
      - 1
      - Attribute indicating if this fault is the root for other
        correlated alarms. If true, then the alarms listed in
        the attribute "correlatedAlarmIds" are caused by this
        fault.
    * - correlatedAlarmIds
      - Identifier
      - 0..N
      - List of identifiers of other alarms correlated to this
        fault.
    * - faultDetails
      - String
      - 0..N
      - Provides additional information about the fault.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >objectInstance
      - Link
      - 0..1
      - Link to the resource representing the VNF instance
        to which the notified alarm is correlated. Shall be
        present if the VNF instance information is
        accessible as a resource.

* | **Name**: Modify the confirmation status
  | **Description**: Modify the confirmation status of the alarm
                     specified in the Tacker.
  | **Method type**: PATCH
  | **URL for the resource**: /vnffm/v1/alarms/{alarmId}
  | **Content-Type**: application/mergepatch+json
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - AlarmModifications
      - 1
      - alarm modification

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AlarmModifications)
      - Data type
      - Cardinality
      - Description
    * - ackState
      - Enum
      - 1
      - New value of the "ackState" attribute in "Alarm".
        Permitted values: ACKNOWLEDGED, UNACKNOWLEDGED

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - AlarmModifications
      - 1
      - Success: 200
      - Shall be returned when the request has been
        accepted and completed.
    * - ProblemDetails
      - 1
      - Error: 409
      - The operation cannot be executed currently, due to a
        conflict with the state of the "Individual alarm"
        resource.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. note::

     Since current Tacker does not support http Etag, it does not support
     Error Code: 412 Precondition Failed. According to the ETSI NFV SOL
     document, there is no API request/response specification for
     Etag yet, and transactions using Etag are not defined
     by standardization. Tacker will support Etag after the ETSI NFV
     specification defines relevant transactions.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AlarmModifications)
      - Data type
      - Cardinality
      - Description
    * - ackState
      - Enum
      - 1
      - New value of the "ackState" attribute in "Alarm".
        Permitted values: ACKNOWLEDGED, UNACKNOWLEDGED

* | **Name**: Create a new subscription
  | **Description**: Create a new subscription in the Tacker.
  | **Method type**: POST
  | **URL for the resource**: /vnffm/v1/subscriptions
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - FmSubscriptionRequest
      - 1
      - Details of the subscription to be created

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (FmSubscriptionRequest)
      - Data type
      - Cardinality
      - Description
    * - filter
      - FmNotificationsFilter
      - 0..1
      - Filter settings for this subscription, to define the subset of
        all notifications this subscription relates to. A particular
        notification is sent to the subscriber if the filter matches,
        or if there is no filter.
    * - >vnfInstanceSubscriptionFilter
      - VnfInstanceSubscriptionFilter
      - 0..1
      - Filter criteria to select VNF instances about
        which to notify.
    * - >>vnfdIds
      - Identifier
      - 0..N
      - If present, match VNF instances that were
        created based on a VNFD identified by one of
        the vnfdId values listed in this attribute.
        See note 1.
    * - >>vnfProductsFromProviders
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products from certain providers.
        See note 1.
    * - >>>vnfProvider
      - String
      - 1
      - Name of the VNF provider to match.
    * - >>>vnfProducts
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain product names, from
        one particular provider.
    * - >>>>vnfProductName
      - String
      - 1
      - Name of the VNF product to match.
    * - >>>>versions
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain versions and a
        certain product name, from one particular
        provider.
    * - >>>>>vnfSoftwareVersion
      - Version
      - 1
      - Software version to match.
    * - >>>>>vnfdVersions
      - Version
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain VNFD versions, a
        certain software version and a certain product
        name, from one particular provider.
    * - >>vnfInstanceIds
      - Identifier
      - 0..N
      - If present, match VNF instances with an
        instance identifier listed in this attribute.
    * - >>vnfInstanceNames
      - String
      - 0..N
      - If present, match VNF instances with a VNF
        Instance Name listed in this attribute.
    * - >notificationTypes
      - Enum (inlined)
      - 0..N
      - Match particular notification types.
        Permitted values: AlarmNotification, AlarmClearedNotification,
        AlarmListRebuiltNotification
    * - >faultyResourceTypes
      - FaultyResourceType
      - 0..N
      - Match VNF alarms with a faulty resource type.
        COMPUTE, STORAGE, NETWORK
    * - >perceivedSeverities
      - PerceivedSeverityType
      - 0..N
      - Match VNF alarms with a perceived severity.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >eventTypes
      - EventType
      - 0..N
      - Match VNF alarms with an event type.
        COMMUNICATIONS_ALARM, PROCESSING_ERROR_ALARM,
        ENVIRONMENTAL_ALARM, QOS_ALARM, EQUIPMENT_ALARM
    * - >probableCauses
      - String
      - 0..N
      - Match VNF alarms with a probable cause listed
        in this attribute.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification to.
    * - authentication
      - SubscriptionAuthentication
      - 0..1
      - Authentication parameters to configure the use of
        Authorization when sending notifications corresponding
        to this subscription. See as clause 8.3.4 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - FmSubscription
      - 1
      - Success: 201
      - Shall be returned when the subscription has been
        created successfully.
    * - n/a
      -
      - Success: 303
      - Shall be returned when a subscription with the
        same callback URI and the same filter already
        exists and the policy of the VNFM is to not create
        redundant subscriptions.
        The HTTP response shall include a "Location"
        HTTP header that contains the resource URI of
        the existing "Individual subscription" resource.
        The response body shall be empty.
    * - ProblemDetails
      - 1
      - Error: 422
      - The content type of the payload body is supported
        and the payload body of a request contains
        syntactically correct data but the data cannot be
        processed.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (FmSubscription)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this "Individual subscription" resource.
    * - filter
      - FmNotificationsFilter
      - 0..1
      - Filter settings for this subscription, to define the subset of
        all notifications this subscription relates to. A particular
        notification is sent to the subscriber if the filter matches,
        or if there is no filter.
    * - >vnfInstanceSubscriptionFilter
      - VnfInstanceSubscriptionFilter
      - 0..1
      - Filter criteria to select VNF instances about
        which to notify.
    * - >>vnfdIds
      - Identifier
      - 0..N
      - If present, match VNF instances that were
        created based on a VNFD identified by one of
        the vnfdId values listed in this attribute.
        See note 1.
    * - >>vnfProductsFromProviders
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products from certain providers.
        See note 1.
    * - >>>vnfProvider
      - String
      - 1
      - Name of the VNF provider to match.
    * - >>>vnfProducts
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain product names, from
        one particular provider.
    * - >>>>vnfProductName
      - String
      - 1
      - Name of the VNF product to match.
    * - >>>>versions
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain versions and a
        certain product name, from one particular
        provider.
    * - >>>>>vnfSoftwareVersion
      - Version
      - 1
      - Software version to match.
    * - >>>>>vnfdVersions
      - Version
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain VNFD versions, a
        certain software version and a certain product
        name, from one particular provider.
    * - >>vnfInstanceIds
      - Identifier
      - 0..N
      - If present, match VNF instances with an
        instance identifier listed in this attribute.
    * - >>vnfInstanceNames
      - String
      - 0..N
      - If present, match VNF instances with a VNF
        Instance Name listed in this attribute.
    * - >notificationTypes
      - Enum (inlined)
      - 0..N
      - Match particular notification types.
        Permitted values: AlarmNotification, AlarmClearedNotification,
        AlarmListRebuiltNotification
    * - >faultyResourceTypes
      - FaultyResourceType
      - 0..N
      - Match VNF alarms with a faulty resource type.
        COMPUTE, STORAGE, NETWORK
    * - >perceivedSeverities
      - PerceivedSeverityType
      - 0..N
      - Match VNF alarms with a perceived severity.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >eventTypes
      - EventType
      - 0..N
      - Match VNF alarms with an event type.
        COMMUNICATIONS_ALARM, PROCESSING_ERROR_ALARM,
        ENVIRONMENTAL_ALARM, QOS_ALARM, EQUIPMENT_ALARM
    * - >probableCauses
      - String
      - 0..N
      - Match VNF alarms with a probable cause listed
        in this attribute.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification to.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.

* | **Name**: Get all subscriptions
  | **Description**: Allow users to filter out subscriptions
                     based on query parameter in the request
  | **Method type**: GET
  | **URL for the resource**: /vnffm/v1/subscriptions
  | **Query parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - filter
      - 0..1
      - Attribute-based filtering expression.
        The following attribute names shall be supported by the Tacker in the attribute-based
        filtering expression. All attribute names that appear in the FmSubscription and
        in data types referenced from it shall be supported by the VNFM in the filter
        expression.
        For example, below URI query parameter will matching alarms with
        perceivedSeverity=WARNING

        .. code-block:: console

           GET /vnffm/v1/alarms?filter=(eq,filter/perceivedSeverity,WARNING)

  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - FmSubscription
      - 0..N
      - Success: 200
      - Shall be returned when the list of subscriptions has
        been queried successfully.
    * - ProblemDetails
      - 1
      - Error: 400
      - Invalid attribute-based filtering expression.
        The response body shall contain a ProblemDetails
        structure, in which the "detail" attribute should convey
        more information about the error.
    * - ProblemDetails
      - 1
      - Error: 400
      - Response too big.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (FmSubscription)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this "Individual subscription" resource.
    * - filter
      - FmNotificationsFilter
      - 0..1
      - Filter settings for this subscription, to define the subset of
        all notifications this subscription relates to. A particular
        notification is sent to the subscriber if the filter matches,
        or if there is no filter.
    * - >vnfInstanceSubscriptionFilter
      - VnfInstanceSubscriptionFilter
      - 0..1
      - Filter criteria to select VNF instances about
        which to notify.
    * - >>vnfdIds
      - Identifier
      - 0..N
      - If present, match VNF instances that were
        created based on a VNFD identified by one of
        the vnfdId values listed in this attribute.
        See note 1.
    * - >>vnfProductsFromProviders
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products from certain providers.
        See note 1.
    * - >>>vnfProvider
      - String
      - 1
      - Name of the VNF provider to match.
    * - >>>vnfProducts
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain product names, from
        one particular provider.
    * - >>>>vnfProductName
      - String
      - 1
      - Name of the VNF product to match.
    * - >>>>versions
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain versions and a
        certain product name, from one particular
        provider.
    * - >>>>>vnfSoftwareVersion
      - Version
      - 1
      - Software version to match.
    * - >>>>>vnfdVersions
      - Version
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain VNFD versions, a
        certain software version and a certain product
        name, from one particular provider.
    * - >>vnfInstanceIds
      - Identifier
      - 0..N
      - If present, match VNF instances with an
        instance identifier listed in this attribute.
    * - >>vnfInstanceNames
      - String
      - 0..N
      - If present, match VNF instances with a VNF
        Instance Name listed in this attribute.
    * - >notificationTypes
      - Enum (inlined)
      - 0..N
      - Match particular notification types.
        Permitted values: AlarmNotification, AlarmClearedNotification,
        AlarmListRebuiltNotification
    * - >faultyResourceTypes
      - FaultyResourceType
      - 0..N
      - Match VNF alarms with a faulty resource type.
        COMPUTE, STORAGE, NETWORK
    * - >perceivedSeverities
      - PerceivedSeverityType
      - 0..N
      - Match VNF alarms with a perceived severity.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >eventTypes
      - EventType
      - 0..N
      - Match VNF alarms with an event type.
        COMMUNICATIONS_ALARM, PROCESSING_ERROR_ALARM,
        ENVIRONMENTAL_ALARM, QOS_ALARM, EQUIPMENT_ALARM
    * - >probableCauses
      - String
      - 0..N
      - Match VNF alarms with a probable cause listed
        in this attribute.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification to.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.

* | **Name**: Get a subscription
  | **Description**: Get the subscription in the Tacker
  | **Method type**: GET
  | **URL for the resource**: /vnffm/v1/subscriptions/{subscriptionId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - FmSubscription
      - 1
      - Success: 200
      - Shall be returned when information about an
        individual subscription has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (FmSubscription)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this "Individual subscription" resource.
    * - filter
      - FmNotificationsFilter
      - 0..1
      - Filter settings for this subscription, to define the subset of
        all notifications this subscription relates to. A particular
        notification is sent to the subscriber if the filter matches,
        or if there is no filter.
    * - >vnfInstanceSubscriptionFilter
      - VnfInstanceSubscriptionFilter
      - 0..1
      - Filter criteria to select VNF instances about
        which to notify.
    * - >>vnfdIds
      - Identifier
      - 0..N
      - If present, match VNF instances that were
        created based on a VNFD identified by one of
        the vnfdId values listed in this attribute.
        See note 1.
    * - >>vnfProductsFromProviders
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products from certain providers.
        See note 1.
    * - >>>vnfProvider
      - String
      - 1
      - Name of the VNF provider to match.
    * - >>>vnfProducts
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain product names, from
        one particular provider.
    * - >>>>vnfProductName
      - String
      - 1
      - Name of the VNF product to match.
    * - >>>>versions
      - Structure (inlined)
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain versions and a
        certain product name, from one particular
        provider.
    * - >>>>>vnfSoftwareVersion
      - Version
      - 1
      - Software version to match.
    * - >>>>>vnfdVersions
      - Version
      - 0..N
      - If present, match VNF instances that belong to
        VNF products with certain VNFD versions, a
        certain software version and a certain product
        name, from one particular provider.
    * - >>vnfInstanceIds
      - Identifier
      - 0..N
      - If present, match VNF instances with an
        instance identifier listed in this attribute.
    * - >>vnfInstanceNames
      - String
      - 0..N
      - If present, match VNF instances with a VNF
        Instance Name listed in this attribute.
    * - >notificationTypes
      - Enum (inlined)
      - 0..N
      - Match particular notification types.
        Permitted values: AlarmNotification, AlarmClearedNotification,
        AlarmListRebuiltNotification
    * - >faultyResourceTypes
      - FaultyResourceType
      - 0..N
      - Match VNF alarms with a faulty resource type.
        COMPUTE, STORAGE, NETWORK
    * - >perceivedSeverities
      - PerceivedSeverityType
      - 0..N
      - Match VNF alarms with a perceived severity.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >eventTypes
      - EventType
      - 0..N
      - Match VNF alarms with an event type.
        COMMUNICATIONS_ALARM, PROCESSING_ERROR_ALARM,
        ENVIRONMENTAL_ALARM, QOS_ALARM, EQUIPMENT_ALARM
    * - >probableCauses
      - String
      - 0..N
      - Match VNF alarms with a probable cause listed
        in this attribute.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification to.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.

* | **Name**: Delete a subscription
  | **Description**: Delete the subscription in the Tacker
  | **Method type**: DELETE
  | **URL for the resource**: /vnffm/v1/subscriptions/{subscriptionId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

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
      - Shall be returned when the "Individual subscription"
        resource has been deleted successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Notifies a VNF alarm
  | **Description**: Notify Client that Tacker received an alarm
  | **Method type**: POST
  | **URL for the resource**: <Client URI from subscriptions>
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - AlarmNotification
      - 1
      - Information of a VNF alarm
    * - AlarmClearedNotification
      - 1
      - Information of the clearance of a VNF alarm

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AlarmNotification)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this notification. If a notification is sent
        multiple times due to multiple subscriptions, the "id"
        attribute of all these notifications shall have the same
        value.
    * - notificationType
      - String
      - 1
      - Discriminator for the different notification types.
        Shall be set to "AlarmNotification" for this notification
        type.
    * - subscriptionId
      - Identifier
      - 1
      - Identifier of the subscription that this notification relates
        to.
    * - timeStamp
      - DateTime
      - 1
      - Date-time of the generation of the notification.
    * - alarm
      - Alarm
      - 1
      - Information about an alarm including AlarmId, affected
        VNF identifier, and FaultDetails.
    * - >id
      - Identifier
      - 1
      - Identifier of this Alarm information element.
    * - >managedObjectId
      - Identifier
      - 1
      - Identifier of the affected VNF instance.
    * - >vnfcInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the affected VNFC instances.
    * - >rootCauseFaultyResource
      - FaultyResourceInfo
      - 0..1
      - The virtualised resources that are causing the VNF
        fault. Shall be present if the alarm affects virtualised
        resources.
    * - >>faultyResource
      - ResourceHandle
      - 1
      - Information that identifies the faulty resource instance
        and its managing entity.
    * - >>>vimConnectionId
      - Identifier
      - 0..1
      - Identifier of the VIM connection to manage the resource.
        This attribute shall only be supported and present if VNFrelated
        resource management in direct mode is
        applicable.
        The applicable "VimConnectionInfo" structure, which is
        referenced by vimConnectionId, can be obtained from
        the "vimConnectionInfo" attribute of the "VnfInstance"
        structure.
    * - >>>resourceProviderId
      - Identifier
      - 0..1
      - Identifier of the entity responsible for the management of
        the resource.
        This attribute shall only be supported and present when
        VNF-related resource management in indirect mode is
        applicable. The identification scheme is outside the
        scope of the present document.
    * - >>>resourceId
      - IdentifierInVim
      - 1
      - Identifier of the resource in the scope of the VIM or the
        resource provider.
    * - >>>vimLevelResourceType
      - String
      - 0..1
      - Type of the resource in the scope of the VIM or the
        resource provider. See note.
    * - >>faultyResourceType
      - FaultyResourceType
      - 1
      - Type of the faulty resource.
        COMPUTE, STORAGE, NETWORK
    * - >alarmRaisedTime
      - DateTime
      - 1
      - Time stamp indicating when the alarm is raised by
        the managed object.
    * - >alarmChangedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was last
        changed. It shall be present if the alarm has been
        updated.
    * - >alarmClearedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was cleared.
        It shall be present if the alarm has been cleared.
    * - >alarmAcknowledgedTime
      - DateTime
      - 0..1
      - Time stamp indicating when the alarm was
        acknowledged. It shall be present if the alarm has
        been acknowledged.
    * - >ackState
      - Enum
      - 1
      - Acknowledgement state of the alarm.
        Permitted values: UNACKNOWLEDGED, ACKNOWLEDGED.
    * - >perceivedSeverity
      - PerceivedSeverityType
      - 1
      - Perceived severity of the managed object failure.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >eventTime
      - DateTime
      - 1
      - Time stamp indicating when the fault was observed.
    * - >eventType
      - EventType
      - 1
      - Type of event.
    * - >faultType
      - String
      - 0..1
      - Additional information to clarify the type of the fault.
    * - >probableCause
      - String
      - 1
      - Information about the probable cause of the fault.
    * - >isRootCause
      - Boolean
      - 1
      - Attribute indicating if this fault is the root for other
        correlated alarms. If true, then the alarms listed in
        the attribute "correlatedAlarmIds" are caused by this
        fault.
    * - >correlatedAlarmIds
      - Identifier
      - 0..N
      - List of identifiers of other alarms correlated to this
        fault.
    * - >faultDetails
      - String
      - 0..N
      - Provides additional information about the fault.
    * - >_links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >>self
      - Link
      - 1
      - URI of this resource.
    * - >>objectInstance
      - Link
      - 0..1
      - Link to the resource representing the VNF instance
        to which the notified alarm is correlated. Shall be
        present if the VNF instance information is
        accessible as a resource.
    * - _links
      - Structure (inlined)
      - 1
      - Links to resources related to this notification.
    * - >subscription
      - NotificationLink
      - 1
      - Link to the related subscription.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AlarmClearedNotification)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this notification. If a notification is sent
        multiple times due to multiple subscriptions, the "id"
        attribute of all these notifications shall have the same
        value.
    * - notificationType
      - String
      - 1
      - Discriminator for the different notification types.
        Shall be set to "AlarmClearedNotification" for this
        notification type.
    * - subscriptionId
      - Identifier
      - 1
      - Identifier of the subscription that this notification relates
        to.
    * - timeStamp
      - DateTime
      - 1
      - Date-time of the generation of the notification.
    * - alarmId
      - Identifier
      - 1
      - Alarm identifier.
    * - alarmClearedTime
      - DateTime
      - 1
      - The time stamp indicating when the alarm was cleared.
    * - _links
      - Structure (inlined)
      - 1
      - Links to resources related to this notification.
    * - >subscription
      - NotificationLink
      - 1
      - Link to the related subscription.
    * - >alarm
      - NotificationLink
      - 1
      - Link to the resource that represents the related alarm.

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
      - Shall be returned when the notification has been
        delivered successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Test the notification endpoint
  | **Description**: Confirm that the URI of Client is correct.
  | **Method type**: GET
  | **URL for the resource**: <Client URI from subscriptions>
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

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
      - Shall be returned to indicate that the notification
        endpoint has been tested successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Create a PM job
  | **Description**: Create a PM job. PM jobs group details
                     of performance collection
                     and reporting information
  | **Method type**: POST
  | **URL for the resource**: /vnfpm/v2/pm_jobs
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - CreatePmJobRequest
      - 1
      - PM job creation request

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (CreatePmJobRequest)
      - Data type
      - Cardinality
      - Description
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceIds
      - Identifier
      - 1..N
      - Identifiers of the measured object instances for
        which performance information is requested to be
        collected.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - PmJobCriteria
      - 1
      - Criteria of the collection of performance
        information.
    * - >performanceMetric
      - String
      - 0..N
      - This defines the types of performance metrics
        for the specified object instances. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >performanceMetricGroup
      - String
      - 0..N
      - Group of performance metrics.
        A metric group is a pre-defined list of metrics,
        known to the API producer that it can
        decompose to individual metrics. Valid values
        are specified as "Measurement Group" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >collectionPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will collect performance information.
        The unit shall be seconds.
    * - >reportingPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will report to the API consumer.
        about performance information. The unit shall be
        seconds. The reportingPeriod should be equal to
        or a multiple of the collectionPeriod.
    * - >reportingBoundary
      - DateTime
      - 0..1
      - Identifies a time boundary after which the
        reporting will stop.
        The boundary shall allow a single reporting as
        well as periodic reporting up to the boundary.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification to.
    * - authentication
      - SubscriptionAuthentication
      - 0..1
      - Authentication parameters to configure the use of
        Authorization when sending notifications corresponding
        to this subscription. See as clause 8.3.4 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - PmJob
      - 1
      - Success: 201
      - Shall be returned when the PM job has been created
        successfully.
    * - ProblemDetails
      - 1
      - Error: 422
      - The content type of the payload body is supported
        and the payload body of a request contains
        syntactically correct data but the data cannot be
        processed.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PmJob)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this PM job.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceIds
      - Identifier
      - 1..N
      - Identifiers of the measured object instances for
        which performance information is collected.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - PmJobCriteria
      - 1
      - Criteria of the collection of performance
        information.
    * - >performanceMetric
      - String
      - 0..N
      - This defines the types of performance metrics
        for the specified object instances. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >performanceMetricGroup
      - String
      - 0..N
      - Group of performance metrics.
        A metric group is a pre-defined list of metrics,
        known to the API producer that it can
        decompose to individual metrics. Valid values
        are specified as "Measurement Group" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >collectionPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will collect performance information.
        The unit shall be seconds.
    * - >reportingPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will report to the API consumer.
        about performance information. The unit shall be
        seconds. The reportingPeriod should be equal to
        or a multiple of the collectionPeriod.
    * - >reportingBoundary
      - DateTime
      - 0..1
      - Identifies a time boundary after which the
        reporting will stop.
        The boundary shall allow a single reporting as
        well as periodic reporting up to the boundary.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - reports
      - Structure (inlined)
      - 0..N
      - Information about available reports collected by
        this PM job.
    * - >href
      - Uri
      - 1
      - The URI where the report can be obtained.
    * - >readyTime
      - DateTime
      - 1
      - The time when the report was made available.
    * - >expiryTime
      - DateTime
      - 0..1
      - The time when the report will expire.
    * - >fileSize
      - UnsignedInt
      - 0..1
      - The size of the report file in bytes, if known.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >objects
      - Link
      - 0..N
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

* | **Name**: Get for PM jobs
  | **Description**: Allow users to filter out PM jobs
                     based on query parameter in the request
  | **Method type**: GET
  | **URL for the resource**: /vnfpm/v2/pm_jobs
  | **Query parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - filter
      - 0..1
      - Attribute-based filtering expression.
        according to clause 5.2 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_.

        For example, below URI query parameter will matching PM job with
        objectType=VNFC.

        .. code-block:: console

          GET /vnfpm/v2/pm_jobs?filter=(eq,objectType,VNFC)

    * - all_fields
      - 0..1
      - Include all complex attributes in the response. See clause 5.3 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_ for details.
    * - fields
      - 0..1
      - Complex attributes to be included into the response. See clause 5.3 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_ for details.
    * - exclude_fields
      - 0..1
      - Complex attributes to be excluded from the response. See clause 5.3 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_ for details.
    * - exclude_default
      - 0..1
      - Indicates to exclude the following complex attributes from the response.
        See clause 5.3 of ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ for details.

  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - PmJob
      - 0..N
      - Success: 200
      - Shall be returned when information about zero or
        more PM jobs has been queried successfully.
    * - ProblemDetails
      - 1
      - Error: 400
      - Invalid attribute-based filtering expression.
        The response body shall contain a ProblemDetails
        structure, in which the "detail" attribute should convey
        more information about the error.
    * - ProblemDetails
      - 1
      - Error: 400
      - Invalid attribute selector.
        The response body shall contain a ProblemDetails
        structure, in which the "detail" attribute should convey
        more information about the error.
    * - ProblemDetails
      - 1
      - Error: 400
      - Response too big.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PmJob)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this PM job.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceIds
      - Identifier
      - 1..N
      - Identifiers of the measured object instances for
        which performance information is collected.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - PmJobCriteria
      - 1
      - Criteria of the collection of performance
        information.
    * - >performanceMetric
      - String
      - 0..N
      - This defines the types of performance metrics
        for the specified object instances. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >performanceMetricGroup
      - String
      - 0..N
      - Group of performance metrics.
        A metric group is a pre-defined list of metrics,
        known to the API producer that it can
        decompose to individual metrics. Valid values
        are specified as "Measurement Group" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >collectionPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will collect performance information.
        The unit shall be seconds.
    * - >reportingPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will report to the API consumer.
        about performance information. The unit shall be
        seconds. The reportingPeriod should be equal to
        or a multiple of the collectionPeriod.
    * - >reportingBoundary
      - DateTime
      - 0..1
      - Identifies a time boundary after which the
        reporting will stop.
        The boundary shall allow a single reporting as
        well as periodic reporting up to the boundary.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - reports
      - Structure (inlined)
      - 0..N
      - Information about available reports collected by
        this PM job.
    * - >href
      - Uri
      - 1
      - The URI where the report can be obtained.
    * - >readyTime
      - DateTime
      - 1
      - The time when the report was made available.
    * - >expiryTime
      - DateTime
      - 0..1
      - The time when the report will expire.
    * - >fileSize
      - UnsignedInt
      - 0..1
      - The size of the report file in bytes, if known.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >objects
      - Link
      - 0..N
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

* | **Name**: Get a PM job
  | **Description**: Get a individual PM job
  | **Method type**: GET
  | **URL for the resource**: /vnfpm/v2/pm_jobs/{pmJobId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - PmJob
      - 1
      - Success: 200
      - Shall be returned when information about an individual
        PM job has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PmJob)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this PM job.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceIds
      - Identifier
      - 1..N
      - Identifiers of the measured object instances for
        which performance information is collected.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - PmJobCriteria
      - 1
      - Criteria of the collection of performance
        information.
    * - >performanceMetric
      - String
      - 0..N
      - This defines the types of performance metrics
        for the specified object instances. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >performanceMetricGroup
      - String
      - 0..N
      - Group of performance metrics.
        A metric group is a pre-defined list of metrics,
        known to the API producer that it can
        decompose to individual metrics. Valid values
        are specified as "Measurement Group" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        At least one of the two attributes (performance
        metric or group) shall be present.
    * - >collectionPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will collect performance information.
        The unit shall be seconds.
    * - >reportingPeriod
      - UnsignedInt
      - 1
      - Specifies the periodicity at which the API
        producer will report to the API consumer.
        about performance information. The unit shall be
        seconds. The reportingPeriod should be equal to
        or a multiple of the collectionPeriod.
    * - >reportingBoundary
      - DateTime
      - 0..1
      - Identifies a time boundary after which the
        reporting will stop.
        The boundary shall allow a single reporting as
        well as periodic reporting up to the boundary.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - reports
      - Structure (inlined)
      - 0..N
      - Information about available reports collected by
        this PM job.
    * - >href
      - Uri
      - 1
      - The URI where the report can be obtained.
    * - >readyTime
      - DateTime
      - 1
      - The time when the report was made available.
    * - >expiryTime
      - DateTime
      - 0..1
      - The time when the report will expire.
    * - >fileSize
      - UnsignedInt
      - 0..1
      - The size of the report file in bytes, if known.
    * - _links
      - Structure (inlined)
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >objects
      - Link
      - 0..N
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

* | **Name**: Modify a PM job
  | **Description**: Modify resource of an individual PM job
  | **Method type**: PATCH
  | **URL for the resource**: /vnfpm/v2/pm_jobs/{pmJobId}
  | **Content-Type**: application/mergepatch+json
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - PmJobModifications
      - 1
      - Parameters for the PM job modification.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PmJobModifications)
      - Data type
      - Cardinality
      - Description
    * - callbackUri
      - Uri
      - 0..1
      - New value of the "callbackUri" attribute. The value
        "null" is not permitted.
    * - authentication
      - SubscriptionAuthentication
      - 0..1
      - New value of the "authentication" attribute, or "null" to
        remove the attribute. If present in a request body,
        these modifications shall be applied according to the
        rules of JSON Merge Patch.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - PmJobModifications
      - 1
      - Success: 200
      - Shall be returned when the request has been
        processed successfully.
    * - ProblemDetails
      - 1
      - 422
      - The content type of the payload body is supported and the
        payload body of a request contains syntactically
        correct data but the data cannot be processed.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. note::

     Since current Tacker does not support http Etag, it does not support
     Error Code: 412 Precondition Failed. According to the ETSI NFV SOL
     document, there is no API request/response specification for
     Etag yet, and transactions using Etag are not defined
     by standardization. Tacker will support Etag after the ETSI NFV
     specification defines relevant transactions.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PmJobModifications)
      - Data type
      - Cardinality
      - Description
    * - callbackUri
      - Uri
      - 0..1
      - New value of the "callbackUri" attribute. The value
        "null" is not permitted.

  The authentication parameter shall not be present in response bodies.

* | **Name**: Delete a PM job
  | **Description**: Delete the PM job in the Tacker
  | **Method type**: DELETE
  | **URL for the resource**: /vnfpm/v2/pm_jobs/{pmJobId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

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
      - Shall be returned when the PM job has been deleted
        successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Get individual performance report
  | **Description**: Get an individual performance report
  | **Method type**: GET
  | **URL for the resource**: /vnfpm/v2/pm_jobs/{pmJobId}/reports/{reportId}
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - PerformanceReport
      - 1
      - Success: 200
      - Shall be returned when information of an individual
        performance report has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PerformanceReport)
      - Data type
      - Cardinality
      - Description
    * - entries
      - Structure (inlined)
      - 1..N
      - List of performance information entries.
    * - >objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a measurement
        is defined in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >objectInstanceId
      - Identifier
      - 1
      - Identifier of the measured object instance for which the
        performance metric is reported.
    * - >subObjectInstanceId
      - IdentifierInVnf
      - 0..1
      - Identifier of the sub-object instance of the measured
        object instance for which the performance metric is
        reported. Shall be present if this is required in clause 6.2
        of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_ for the related measured
        object type.
    * - >performanceMetric
      - String
      - 1
      - Name of the metric collected. This attribute shall contain
        the related "Measurement Name" value as defined in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >performanceValues
      - Structure (inlined)
      - 1..N
      - List of performance values with associated timestamp.
    * - >>timeStamp
      - DateTime
      - 1
      - Time stamp indicating when the data has been collected.
    * - >>value
      - (any type)
      - 1
      - Value of the metric collected. The type of this attribute
        shall correspond to the related "Measurement Unit" as
        defined in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >>context
      - KeyValuePairs
      - 0..1
      - Measurement context information related to the
        measured value. The set of applicable keys is defined
        per measurement in the related "Measurement Context"
        in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.

* | **Name**: Notifies a VNF Performance Management event
  | **Description**: Delivers a notification regarding
                     a Performance Management event
  | **Method type**: POST
  | **URL for the resource**: <Client URI for notifications>
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - PerformanceInformationAvailableNotification
      - 1
      - Notification about performance information availability

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PerformanceInformationAvailableNotification)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this notification. If a notification is sent multiple
        times due to multiple subscriptions, the "id" attribute of all
        these notifications shall have the same value.
    * - notificationType
      - String
      - 1
      - Discriminator for the different notification types.
        Shall be set to
        "PerformanceInformationAvailableNotification" for this
        notification type.
    * - timeStamp
      - DateTime
      - 1
      - Date and time of the generation of the notification.
    * - pmJobId
      - Identifier
      - 1
      - Identifier of the PM job for which performance information
        is available.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a measurement
        is defined in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceId
      - Identifier
      - 1
      - Identifier of the measured object instance as per
        clause 6.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the sub-object instances of the measured
        object instance for which the measurements have been
        taken.
        Shall be present if the related PM job has been set up to
        measure only a subset of all sub-object instances of the
        measured object instance and a sub-object is defined in
        clause 6.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_ for the related
        measured object type.
        Shall be absent otherwise.
    * - _links
      - Structure (inlined)
      - 1
      - Links to resources related to this notification.
    * - >objectInstance
      - NotificationLink
      - 0..1
      - Link to the resource representing the measured object
        instance to which the notification applies. Shall be present
        if the measured object instance information is accessible
        as a resource.
    * - >pmJob
      - NotificationLink
      - 1
      - Link to the resource that represents the PM job for which
        performance information is available.
    * - >performanceReport
      - NotificationLink
      - 1
      - Link from which the available performance information of
        data type "PerformanceReport" can
        be obtained.
        This link should point to an "Individual performance report"
        resource.

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
      - Shall be returned when the notification has been delivered
        successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Test the notification endpoint
  | **Description**: Confirm that the URI of Client is correct.
  | **Method type**: GET
  | **URL for the resource**: <Client URI for notifications>
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - n/a
      -
      -

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
      - Shall be returned to indicate that the notification
        endpoint has been tested successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

The following RESTful API is Tacker specific interface
used for Fault Management between Tacker and External Monitoring Tool.

* | **Name**: Send a alert event
  | **Description**: Receive the alert sent from External Monitoring Tool
  | **Method type**: POST
  | **URL for the resource**: /alert
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - AlertEvent
      - 1
      - the alert sent from External Monitoring Tool

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (AlertEvent)
      - Data type
      - Cardinality
      - Description
    * - receiver
      - String
      - 1
      - Defines the receiver's name that the notification will be sent to.
    * - status
      - String
      - 1
      - Defined as firing if at least one alert is firing, otherwise
        resolved.
    * - alerts
      - Structure(inlined)
      - 1..N
      - List of all alert objects in this group.
    * - >status
      - String
      - 1
      - Defines whether or not the alert is resolved or currently firing.
    * - >labels
      - Structure(inlined)
      - 1
      - A set of labels to be attached to the alert.
    * - >>receiver_type
      - String
      - 1
      - Type of receiver: tacker
    * - >>function_type
      - String
      - 1
      - Type of function: vnffm
    * - >>vnf_instance_id
      - Identifier
      - 1
      - Identifier of vnf instance.
    * - >>node
      - String
      - 0..1
      - Name of node.
    * - >>perceived_severity
      - String
      - 1
      - Perceived severity of the managed object failure.
        CRITICAL,MAJOR,MINOR,WARNING,INDETERMINATE,CLEARED
    * - >>event_type
      - String
      - 1
      - Event type.
        COMMUNICATIONS_ALARM, PROCESSING_ERROR_ALARM,
        ENVIRONMENTAL_ALARM, QOS_ALARM, EQUIPMENT_ALARM
    * - >annotations
      - Structure(inlined)
      - 1
      - A set of annotations for the alert.
    * - >>fault_type
      - String
      - 0..1
      - Additional information to clarify the type of the fault.
    * - >>probable_cause
      - String
      - 1
      - Information about the probable cause of the fault.
    * - >>fault_details
      - String
      - 0..1
      - Provides additional information about the fault.
    * - >startsAt
      - DateTime
      - 1
      - The time the alert started firing.
    * - >endsAt
      - DateTime
      - 1
      - The end time of an alert.
    * - >generatorURL
      - String
      - 1
      - A backlink which identifies the causing entity of this alert.
    * - >fingerprint
      - String
      - 1
      - Fingerprint that can be used to identify the alert.
    * - groupLabels
      - KeyValuePairs
      - 1
      - The labels these alerts were grouped by.
    * - commonLabels
      - KeyValuePairs
      - 1
      - The labels common to all of the alerts.
    * - commonAnnotations
      - KeyValuePairs
      - 1
      - Set of common annotations to all of the alerts. Used
        for longer additional strings of information about the alert.
    * - externalURL
      - String
      - 1
      - Backlink to the Alertmanager that sent the notification.
    * - version
      - String
      - 1
      -
    * - groupKey
      - String
      - 1
      -

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
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

The following RESTful APIs are Tacker specific interfaces
used for Performance Management between Tacker and External Monitoring Tool.

* | **Name**: Send a PM event
  | **Description**: Receive the PM event sent from External Monitoring Tool
  | **Method type**: POST
  | **URL for the resource**: /pm_event
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - PerformanceEvent
      - 1
      - The PM event sent from External Monitoring Tool

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (PerformanceEvent)
      - Data type
      - Cardinality
      - Description
    * - receiver
      - String
      - 1
      - Defines the receiver's name that the notification will be sent to.
    * - status
      - String
      - 1
      - Defined as firing if at least one alert is firing, otherwise
        resolved. This attribute is not referred by Tacker in case of PM.
    * - alerts
      - Structure(inlined)
      - 1..N
      - List of all alert objects in this group.
    * - >status
      - String
      - 1
      - Defines whether or not the alert is resolved or currently firing.
    * - >labels
      - Structure(inlined)
      - 1
      - A set of labels to be attached to the alert.
    * - >>receiver_type
      - String
      - 1
      - Type of receiver: tacker
    * - >>function_type
      - String
      - 1
      - Type of function: vnfpm
    * - >>job_id
      - Identifier
      - 1
      - Identifier of the PM job
    * - >>object_instance_id
      - Identifier
      - 1
      - Identifier of the measured object instance for which the
        performance metric is reported.
    * - >>sub_object_instance_id
      - Identifier
      - 0..1
      - Identifier of the measured object sub instance for which the
        performance metric is reported.
    * - >annotations
      - Structure(inlined)
      - 1
      - A set of annotations for the alert.
    * - >>value
      - (any type)
      - 0..1
      - Value of the metric collected.
    * - >startsAt
      - DateTime
      - 1
      - The time the alert started firing.
    * - >endsAt
      - DateTime
      - 1
      - The end time of an alert.
    * - >generatorURL
      - String
      - 1
      - A backlink which identifies the causing entity of this alert.
    * - >fingerprint
      - String
      - 1
      - Fingerprint that can be used to identify the alert.
    * - groupLabels
      - KeyValuePairs
      - 1
      - The labels these alerts were grouped by.
    * - commonLabels
      - KeyValuePairs
      - 1
      - The labels common to all of the alerts.
    * - commonAnnotations
      - KeyValuePairs
      - 1
      - Set of common annotations to all of the alerts. Used
        for longer additional strings of information about the alert.
    * - externalURL
      - String
      - 1
      - Backlink to the Alertmanager that sent the notification.
    * - version
      - String
      - 1
      -
    * - groupKey
      - String
      - 1
      -

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
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

Security impact
---------------

None

Notifications impact
--------------------

Fault Management:
  + Tacker sends POST <Client URI from subscriptions>
    to NFVO or EM to notify Client that Tacker received an alarm.

  + Tacker sends GET <Client URI from subscriptions>
    to NFVO or EM to confirm that the URI of Client is correct.

Performance Management:
  + Tacker sends POST <Client URI for notifications>
    to NFVO or EM to notify Client that Tacker received a PM related event.

  + Tacker sends GET <Client URI for notifications>
    to NFVO or EM to confirm that the URI of Client is correct.

  + Tacker sends GET/POST /api/v1/alerts to External Monitoring Tool
    to set PM jobs.

  + Tacker sends GET/POST /api/v1/query to External Monitoring Tool
    to get data related to a PM event.

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
  Masaki Ueno <masaki.ueno.up@hco.ntt.co.jp>

Other contributors:
  Koji Shimizu <shimizu.koji@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  Yusuke Niimi <niimi.yusuke@fujitsu.com>

Work Items
----------

* Implement Tacker to support:

  * Fault Management interface

    * Add new Rest API ``GET /vnffm/v1/alarms`` to get all alarms.
    * Add new Rest API ``GET /vnffm/v1/alarms/{alarmId}`` to get
      the specified alarm.
    * Add new Rest API ``PATCH /vnffm/v1/alarms/{alarmId}`` to change
      target Alarm to confirmed.
    * Add new Rest API ``POST /vnffm/v1/subscriptions`` to create
      a new subscription.
    * Add new Rest API ``GET /vnffm/v1/subscriptions`` to get
      all subscription.
    * Add new Rest API ``GET /vnffm/v1/subscriptions/{subscriptionId}``
      to get the specified subscription.
    * Add new Rest API ``DELETE /vnffm/v1/subscriptions/{subscriptionId}``
      to delete the specified subscription.
    * Add new Request ``POST <Client URI from subscriptions>`` to notify
      Client that Tacker received an alarm.
    * Add new Request ``GET <Client URI from subscriptions>`` to confirm
      that the URI of Client is correct.

  * Performance Management interface

    * Add new Rest API ``POST /vnfpm/v2/pm_jobs`` to create a PM job.
    * Add new Rest API ``GET /vnfpm/v2/pm_jobs`` to get all PM jobs.
    * Add new Rest API ``GET /vnfpm/v2/pm_jobs/{pmJobId}`` to get
      the specified PM job.
    * Add new Rest API ``PATCH /vnfpm/v2/pm_jobs/{pmJobId}`` to change
      target PM job.
    * Add new Rest API ``DELETE /vnfpm/v2/pm_jobs/{pmJobId}`` to delete
      the specified PM job.
    * Add new Rest API ``GET /vnfpm/v2/pm_jobs/{pmJobId}/reports/{reportId}``
      to get the specified PM report.
    * Add new request ``POST <Client URI for notifications>`` to notify
      Client that Tacker received an alarm.
    * Add new request ``GET <Client URI for notifications>`` to confirm
      that the URI of Client is correct.

  * External Monitoring interface

    * Add new Rest API ``POST /alert``
      to receive the FM alert sent from External Monitoring Tool.
    * Add new Rest API ``POST /pm_event``
      to receive the PM event sent from External Monitoring Tool.

* Add new unit and functional tests.

Dependencies
============

None.

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

* Complete user guide will be added to explain how to monitor
  by External Monitoring Tool.

* Update API documentation on the API additions mentioned in
  `REST API impact`_.

References
==========

.. [#Prometheus] https://prometheus.io/docs/introduction/overview/
.. [#SOL002_v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_nfv-sol002v030301p.pdf
.. [#SOL003_v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
.. [#Alert_server_for_Prometheus_with_Kubernetes_cluster_VNF_sample] https://review.opendev.org/c/openstack/tacker-specs/+/786573/1/specs/xena/prometheus-monitoring.rst
.. [#NFV-SOL013_341] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.04.01_60/gs_nfv-sol013v030401p.pdf
.. [#NFV-IFA027_331] https://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/027/03.03.01_60/gs_nfv-ifa027v030301p.pdf
