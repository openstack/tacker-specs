..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===========================================
Support Thresholds resource in PM Interface
===========================================

https://blueprints.launchpad.net/tacker/+spec/support-auto-lcm

Problem description
===================

This specification provides implementations of "Thresholds"
resource for supporting Performance Management interface
with external monitoring tools such as Prometheus [#Prometheus]_.
Tacker Zed release has supported ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_ based
Fault Management and Performance Management interfaces, however,
Thresholds resource is not implemented for the Performance Management interface in Tacker.
Tacker needs to support Thresholds resource for
advancing ETSI NFV standard compliance and functionality.

* | **Table**: Operations of Performance Management interface and Tacker support status

  .. list-table::
        :widths: 40 20 20
        :header-rows: 1

        * - Operations of PM interface
          - Supported in (Zed)
          - Supported in (Antelope)
        * - Create a PM Job
          - Yes
          - Yes
        * - Query PM Jobs
          - Yes
          - Yes
        * - Read a single PM job
          - Yes
          - Yes
        * - Update PM job callback
          - Yes
          - Yes
        * - Delete a PM Job
          - Yes
          - Yes
        * - Read an individual performance report
          - Yes
          - Yes
        * - Create a threshold
          - No
          - Yes
        * - Query thresholds
          - No
          - Yes
        * - Read a single threshold
          - No
          - Yes
        * - Update threshold callback
          - No
          - Yes
        * - Delete a threshold
          - No
          - Yes
        * - Notify about PM related events
          - Performance information
            availability only
          - Both performance information
            availability and threshold crossing
        * - Test the notification endpoint
          - PM jobs only
          - Both PM jobs and thresholds

Proposed change
===============

The following changes are needed:

#. Add support Thresholds resource for Performance Management interface
   specified in SOL002/003.

   + Add Thresholds resource in VNF Performance Management interface:

     + Create and Update a threshold

       + POST /vnfpm/v2/thresholds to create a threshold.
       + PATCH /vnfpm/v2/thresholds/{thresholdId} to update the specified threshold callback.

     + Get threshold(s)

       + GET /vnfpm/v2/thresholds to get all thresholds.
       + GET /vnfpm/v2/thresholds/{thresholdId} to get the specified threshold.

     + Delete a threshold

       + DELETE /vnfpm/v2/thresholds/{thresholdId} to delete the specified threshold.

   + Enhance notification to Client:

     + POST <Client URI for notifications> to notify Client that
       Tacker received a PM threshold related event.
     + GET <Client URI from subscriptions>
       to confirm that the URI of Client is correct.

#. Add support of RESTful API for communications between
   Tacker and External Monitoring Tool

   + POST /pm_threshold to receive the PM threshold
     event sent from External Monitoring Tool.

#. Create a new DB table for PM Thresholds.

.. note::

  The External Monitoring Tool is a monitoring service.
  That is not included in Tacker.
  Operators implement the External Monitoring Tool.
  The External Monitoring Tool uses metrics service such as
  Prometheus and notifies PM events using the Prometheus Plugin interface [#Prometheus_usecase_guide]_.

AutoScale on PM threshold event trigger
---------------------------------------

Tacker has a configuration value in metadata that indicates
uri of alert manager. Prometheus Plugin converts from PM threshold schema
to prometheus schema when a PM threshold has been created.

When the External Monitoring Tool detects that the CNF
have some PM threshold events, it will send event messages to Tacker.
After Tacker receives the event, it will convert the event to
store it in the DB.

Design of scale operation in PM Threshold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following is a schematic diagram of scale:

.. code-block:: console

                                  +------------------------+
                                  |                        |       9. Send threshold notification
                                  |   Client (NFVO/EM)     <-------------------+
                                  |                        |                   |
                                  +--+---------+-----------+                   |
                                     |         | 1. Create threshold           |
                          10. Scale  |         |                               |
                              +------|---------|-------------------------------|----------------------------+
                              |      |         |                               |                       VNFM |
                              |  +---|---------|---------+ +-------------------|-------------+              |
                              |  |   |         |  Tacker | |                   |  Tacker     |              |
                              |  |   |         |  Server | |                   |  Conductor  |              |
                              |  |   | +-------v------+  | |                   |             |   +--------+ |
                              |  |   | | VnfPm        +------------------------+-----------------> Tacker | |
                              |  |   | | ControllerV2 |  | |         +---------+----+        |   | DB     | |
  +----------------+          |  |   | +---------+----+  | |  +------> VnfPm        +------------>        | |
  |  External      |          |  |   | 2. Set    |       | |  |      | DriverV2     |        |   +--------+ |
  |  Monitoring    | 5. POST  |  |   | threshold |       | |  |      +--------------+        |              |
  |  Tool          |    event |  |   |   +-------v----+  | |  |    8. Create threshold       |              |
  |  (based on     +---------------------> Prometheus +-------+       notification           |              |
  |   Prometheus)  <---------------------+ Plugin     |  | |                                 |              |
  |                | 6. Get related data +------------+  | |                                 |              |
  |                |          |  |   |    7.Evaluate     | |                                 |              |
  +--+-------------+ 3. Set   |  |   |      threshold    | |                                 |              |
     ^              threshold |  |   |      crossing     | |                                 |              |
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

#. The Client sends a request to the Tacker to create a threshold.

#. VnfPmControllerV2 sends threshold information to Prometheus Plugin.

#. Prometheus Plugin sets a threshold to External Monitoring Tool.

#. External Monitoring Tool collects metrics and triggers events.

#. External Monitoring Tool sends POST request to Tacker with specified URI.

#. Tacker collects data related to the PM event.
   From the data obtained in 4-5,
   The value and context corresponding to
   threshold crossing are determined.
   Prometheus Plugin also update
   the corresponding resource from the DB.

#. Prometheus Plugin evaluates the event. If there is a threshold
   crossing condition that can match successfully,
   the event is sent to the specified path of the Client.
   If the evaluation is not successful, the processing ends.

#. VnfPmDriverV2 creates a threshold notification and
   save threshold information to the DB.

#. VnfPmDriverV2 sends a threshold notification to the Client.

#. The Client makes a request for the context of
   the notification, then make a decision of scaling.

#. Scale operation is triggered, new CNF is created
   in case of scale-out or old CNF is deleted in case
   of scale-in.

Request parameters for operation in PM Threshold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The detail of API is described at `REST API impact`_.

.. _sequence-pm-threshold-operation:

Sequence for operation in PM threshold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following sequence diagrams describes
the Client's processing flow for Tacker to AutoScale
by PM threshold.

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
      [label = "1. Create a threshold"];
    "Tacker-server" -> "Tacker-server"
      [label = "Get the callback_uri in the threshold"];
    "Tacker-server" -> "Client"
      [label = "Send a GET request to the callback_uri in the Client."];
    "Tacker-server" <-- "Client"
      [label = "Response 204 No Content"];
    "Tacker-server" -> "Tacker DB"
      [label = "Save the subscription to DB"];
    "Tacker-server" <-- "Tacker DB"
    "Tacker-server" -> "Prometheus-Plugin"
      [label = "2. Set a threshold to Prometheus-Plugin"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "Convert to Prometheus format"];
    "Prometheus-Plugin" -> "External Monitoring Tool"
      [label = "Set a threshold"];
    "Prometheus-Plugin" <-- "External Monitoring Tool"
    "Tacker-server" <-- "Prometheus-Plugin"
    "Tacker-server" -> "Tacker DB"
      [label = "Save a threshold to DB"];
    "Tacker-server" <-- "Tacker DB"
    "Client" <-- "Tacker-server"
      [label = "Response 201 Created"];
    "External Monitoring Tool" -> "Prometheus-Plugin"
      [label = "3. Send event to the specified URI"];
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "4. Check items of prometheus_plugin from cfg.CONF.tacker", note = "If prometheus_plugin is False, asynchronous task is over"];
    "Prometheus-Plugin" -> "Tacker DB"
      [label = "5. Find the corresponding resource from the DB"];
    "Prometheus-Plugin" <-- "Tacker DB"
    "Prometheus-Plugin" -> "Prometheus-Plugin"
      [label = "6. Evaluate a threshold crossing condition.", note = "If it does not match, the processing ends"];
    "Prometheus-Plugin" -> "Tacker DB"
      [label = "Update the corresponding resource from the DB"];
    "Prometheus-Plugin" <-- "Tacker DB"
    "Prometheus-Plugin" -> "VnfPmDriverV2"
      [label = "7. execute VnfPmDriverV2"];
    "VnfPmDriverV2" -> "Client"
      [label = "8. Send a Notify Threshold event request to the Client"];
    "VnfPmDriverV2" <-- "Client"
      [label = "Response 204 No Content"];
    "Prometheus-Plugin" <-- "VnfPmDriverV2"
    "Client" -> "Client"
      [label = "9. Get VNFC information from the notification.", note = "If no information is returned, the processing is over"];
    "Client" -> "Tacker-server"
      [label = "10. Scale"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "11. Trigger asynchronous task", note = "The same with the default scale operation"];
    "Client" <-- "Tacker-server"
      [label = "Response 202 Accepted"];
  }

#. The Client sends a request to create a threshold to the Tacker.
   After Tacker receives the threshold, it will get the callback_uri in it.
   In order to verify the correctness of the callback_uri,
   the Tacker sends a request to the callback_uri address of the Client.
   After getting the normal response HTTP 204 No Content from the Client,
   the Tacker saves the subscription to the DB.

#. Tacker sends a threshold to Prometheus Plugin.
   Prometheus Plugin converts it into Prometheus format,
   then sends it to External Monitoring Tool.
   Tacker saves a threshold to the DB and responses
   HTTP 201 Created to the Client.

#. External Monitoring Tool receives event sent from Prometheus
   and inform the event to specified URI (Tacker).

#. Prometheus Plugin obtains values from cfg.CONF.tacker.prometheus_plugin
   to determine whether to enable this function.
   Prometheus Plugin judges what processing to perform according to
   the function_type field of the labels in the event.
   When the ``labels.function_type`` is ``vnfpm``,
   AutoScale is performed.

#. Prometheus Plugin finds the corresponding resource information
   according to the value of the node label in the event.

#. Prometheus Plugin evaluates a threshold crossing condition,
   if it does not match, the processing ends.

#. Prometheus Plugin executes VnfPmDriverV2.

#. VnfPmDriverV2 sends a Notify Threshold event request
   to the Client's callback_uri address. After the Client receives the
   request and processes it, it returns HTTP 204 No Content by default.

#. The Client obtains the VNFC information from the notification.

#. The Client sends a request to the Tacker to scale the VNFC.

#. From this step, it is completely the same with
   the default scale operation.

Alternatives
------------

None

Data model impact
-----------------

Add below new db table in 'Tacker' database.

* | **Table**: ThresholdV2

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
    * - objectInstanceId
      - varchar(255)
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
    * - authentication
      - JSON
      - NULL
    * - metadata
      - JSON
      - NOT NULL

  This table have `id` as primary key.

REST API impact
---------------

The following RESTful APIs are in compliance with
SOL002/003 [#SOL002_v3.3.1]_ [#SOL003_v3.3.1]_
6.VNF Performance Management interface.

* | **Name**: Create a threshold
  | **Description**: Create a threshold. Thresholds group
                     details of performance information
  | **Method type**: POST
  | **URL for the resource**: /vnfpm/v2/thresholds
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - CreateThresholdRequest
      - 1
      - Threshold creation request

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (CreateThresholdRequest)
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
    * - objectInstanceId
      - Identifier
      - 1
      - Identifiers of the measured object instances
        associated with this threshold.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - ThresholdCriteria
      - 1
      - Criteria that define this threshold.
    * - >performanceMetric
      - String
      - 1
      - This defines the types of performance metrics
        associated with the threshold. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >thresholdType
      - Enum
      - 1
      - Type of threshold. This attribute determines
        which other attributes are present in the data structure.
        In ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
        ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_,
        "SIMPLE: Single-valued static threshold" is permitted.
    * - >simpleThresholdDetails
      - Structure
      - 0..1
      - Details of a simple threshold.
        Shall be present if thresholdType="SIMPLE".
    * - >>thresholdValue
      - Number
      - 1
      - The threshold value. Shall be represented
        as a floating point number.
    * - >>hysteresis
      - Number
      - 1
      - The hysteresis of the threshold. Shall be represented
        as a non-negative floating point number.
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
    * - metadata
      - Structure
      - 1
      - Additional parameters to create a threshold.
        (Tacker original attribute)
    * - >monitoring
      - Structure
      - 1
      - Treats to specify such as monitoring system and driver information.
    * - >>monitorName
      - String
      - 1
      - In case specifying "prometheus", backend of monitoring feature is
        to be Prometheus.
    * - >>driverType
      - String
      - 1
      - "external": SCP/SFTP for config file transfer.
    * - >>targetsInfo
      - Structure
      - 1..N
      - Information about the target monitoring system.
    * - >>>prometheusHost
      - String
      - 1
      - FQDN or ip address of target PrometheusServer.
    * - >>>prometheusHostPort
      - Int
      - 1
      - Port of the ssh target PrometheusServer.
    * - >>>alertRuleConfigPath
      - String
      - 1
      - Path of alertRuleConfig path for target Prometheus.
    * - >>>prometheusReloadApiEndpoint
      - String
      - 1
      - Endpoint url of reload API of target Prometheus.
    * - >>>authInfo
      - Structure
      - 1
      - Define authentication information to access host.
    * - >>>>ssh_username
      - String
      - 1
      - The username of the target host for ssh.
    * - >>>>ssh_password
      - String
      - 1
      - The password of the target host for ssh.

  | **Response**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 18 50

    * - Data type
      - Cardinality
      - Response Codes
      - Description
    * - Threshold
      - 1
      - Success: 201
      - Shall be returned when a threshold has been created
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

    * - Attribute name (Threshold)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this threshold.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceId
      - Identifier
      - 1
      - Identifiers of the measured object instances
        associated with this threshold.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - ThresholdCriteria
      - 1
      - Criteria that define this threshold.
    * - >performanceMetric
      - String
      - 1
      - This defines the types of performance metrics
        associated with the threshold. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >thresholdType
      - Enum
      - 1
      - Type of threshold. This attribute determines
        which other attributes are present in the data structure.
        In ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
        ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_,
        "SIMPLE: Single-valued static threshold" is permitted.
    * - >simpleThresholdDetails
      - Structure
      - 0..1
      - Details of a simple threshold.
        Shall be present if thresholdType="SIMPLE".
    * - >>thresholdValue
      - Number
      - 1
      - The threshold value. Shall be represented
        as a floating point number.
    * - >>hysteresis
      - Number
      - 1
      - The hysteresis of the threshold. Shall be represented
        as a non-negative floating point number.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - _links
      - Structure
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >object
      - Link
      - 0..1
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

  .. note::

    When processing a request to create a threshold,
    it should enforce a suitable minimum
    value for this attribute by override the value
    or reject the request.

  .. note::

    "Hysteresis" is implemented based on thresholdType,
    "Single-valued static threshold."
    A notification with crossing direction "UP"
    will be generated if the measured value reaches
    or exceeds "thresholdValue" + "hysteresis".
    A notification with crossing direction "DOWN"
    will be generated if the measured value reaches
    or undercuts "thresholdValue" - "hysteresis".
    These methods need to store the previous value
    in Tacker DB to detect the crossing direction.

* | **Name**: Query thresholds
  | **Description**: Allow users to filter out thresholds
                     based on query parameter in the request
  | **Method type**: GET
  | **URL for the resource**: /vnfpm/v2/thresholds
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

        For example, below URI query parameter will matching threshold with
        objectType=VNFC.

        .. code-block:: console

          GET /vnfpm/v2/thresholds?filter=(eq,objectType,VNFC)

    * - nextpage_opaque_marker
      - 0..1
      - Marker to obtain the next page of a paged response.
        according to clause 5.4 of ETSI
        GS NFV-SOL 013 [#NFV-SOL013_341]_.

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
    * - Threshold
      - 0..N
      - Success: 200
      - Shall be returned when information about zero or
        more thresholds has been queried successfully.
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

    * - Attribute name (Threshold)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this threshold.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceId
      - Identifier
      - 1
      - Identifiers of the measured object instances
        associated with this threshold.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - ThresholdCriteria
      - 1
      - Criteria that define this threshold.
    * - >performanceMetric
      - String
      - 1
      - This defines the types of performance metrics
        associated with the threshold. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >thresholdType
      - Enum
      - 1
      - Type of threshold. This attribute determines
        which other attributes are present in the data structure.
        In ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
        ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_,
        "SIMPLE: Single-valued static threshold" is permitted.
    * - >simpleThresholdDetails
      - Structure
      - 0..1
      - Details of a simple threshold.
        Shall be present if thresholdType="SIMPLE".
    * - >>thresholdValue
      - Number
      - 1
      - The threshold value. Shall be represented
        as a floating point number.
    * - >>hysteresis
      - Number
      - 1
      - The hysteresis of the threshold. Shall be represented
        as a non-negative floating point number.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - _links
      - Structure
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >object
      - Link
      - 0..1
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

* | **Name**: Read a single threshold
  | **Description**: Get a individual threshold
  | **Method type**: GET
  | **URL for the resource**: /vnfpm/v2/thresholds/{thresholdId}
  | **Path parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - thresholdId
      - 1
      - Threshold ID.

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
    * - Threshold
      - 1
      - Success: 200
      - Shall be returned when information about an individual
        threshold has been read successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (Threshold)
      - Data type
      - Cardinality
      - Description
    * - id
      - Identifier
      - 1
      - Identifier of this threshold.
    * - objectType
      - String
      - 1
      - Type of the measured object.
        The applicable measured object type for a
        measurement is defined in clause 7.2 of ETSI
        GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - objectInstanceId
      - Identifier
      - 1
      - Identifiers of the measured object instances for
        which performance information is collected.
    * - subObjectInstanceIds
      - IdentifierInVnf
      - 0..N
      - Identifiers of the measured object instances
        in case of a structured measured object.
    * - criteria
      - ThresholdCriteria
      - 1
      - Criteria that define this threshold.
    * - >performanceMetric
      - String
      - 1
      - This defines the types of performance metrics
        associated with the threshold. Valid values
        are specified as "Measurement Name" values in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - >thresholdType
      - Enum
      - 1
      - Type of threshold. This attribute determines
        which other attributes are present in the data structure.
        In ETSI NFV-SOL 002 v3.3.1 [#SOL002_v3.3.1]_ and
        ETSI NFV-SOL 003 v3.3.1 [#SOL003_v3.3.1]_,
        "SIMPLE: Single-valued static threshold" is permitted.
    * - >simpleThresholdDetails
      - Structure
      - 0..1
      - Details of a simple threshold.
        Shall be present if thresholdType="SIMPLE".
    * - >>thresholdValue
      - Number
      - 1
      - The threshold value. Shall be represented
        as a floating point number.
    * - >>hysteresis
      - Number
      - 1
      - The hysteresis of the threshold. Shall be represented
        as a non-negative floating point number.
    * - callbackUri
      - Uri
      - 1
      - The URI of the endpoint to send the notification
        to.
    * - _links
      - Structure
      - 1
      - Links for this resource.
    * - >self
      - Link
      - 1
      - URI of this resource.
    * - >object
      - Link
      - 0..1
      - Links to resources representing the measured
        object instances for which performance
        information is collected. Shall be present if the
        measured object instance information is
        accessible as a resource.

* | **Name**: Update threshold callback
  | **Description**: Modify resource of an individual threshold
  | **Method type**: PATCH
  | **URL for the resource**: /vnfpm/v2/thresholds/{thresholdId}
  | **Content-Type**: application/mergepatch+json
  | **Path parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - thresholdId
      - 1
      - Threshold ID.

  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - ThresholdModifications
      - 1
      - Parameters for the threshold modification.

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (ThresholdModifications)
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
    * - ThresholdModifications
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

    * - Attribute name (ThresholdModifications)
      - Data type
      - Cardinality
      - Description
    * - callbackUri
      - Uri
      - 0..1
      - New value of the "callbackUri" attribute. The value
        "null" is not permitted.

  The authentication parameter shall not be present in response bodies.

* | **Name**: Delete a threshold
  | **Description**: Delete the threshold in the Tacker
  | **Method type**: DELETE
  | **URL for the resource**: /vnfpm/v2/thresholds/{thresholdId}
  | **Path parameters**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Name
      - Cardinality
      - Description
    * - thresholdId
      - 1
      - Threshold ID.

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
      - Shall be returned when the threshold has been deleted
        successfully.
    * - ProblemDetails
      - See clause 6.4 of [#NFV-SOL013_341]_
      - Error: 4xx/5xx
      - In addition to the response codes defined above, any
        common error response code as defined in clause 6.4 of
        ETSI GS NFV-SOL 013 [#NFV-SOL013_341]_ may be returned.

* | **Name**: Notify about PM related events
  | **Description**: Delivers a notification regarding
                     a threshold crossing event.
  | **Method type**: POST
  | **URL for the resource**: <Client URI for notifications>
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - ThresholdCrossedNotification
      - 1
      - Notification about threshold crossing

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (ThresholdCrossedNotification)
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
        "ThresholdCrossedNotification for this
        notification type.
    * - timeStamp
      - DateTime
      - 1
      - Date and time of the generation of the notification.
    * - thresholdId
      - Identifier
      - 1
      - Identifier of the threshold for which has been crossed.
    * - crossingDirection
      - CrossingDirectionType
      - 1
      - An indication of whether the threshold was
        crossed in upward or downward direction.
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
    * - subObjectInstanceId
      - IdentifierInVnf
      - 0..1
      - Identifiers of the sub-object instances of the measured
        object instance for which the measurements have been
        taken.
        Shall be present if the related threshold has been set up to
        measure only a subset of all sub-object instances of the
        measured object instance and a sub-object is defined in
        clause 6.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_ for the related
        measured object type.
        Shall be absent otherwise.
    * - performanceMetric
      - String
      - 1
      - Name of the metric collected. This attribute shall contain
        the related "Measurement Name" value as defined in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - performanceValue
      - (any type)
      - 1
      - Value of the metric that resulted in threshold crossing.
        This attribute shall contain
        the related "Measurement Name" value as defined in
        clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
        Measurement context information related to the
        measured value. The set of applicable keys is defined
        per measurement in the related "Measurement Context"
        in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - context
      - KeyValuePairs
      - 0..1
      - Measurement context information related to the
        measured value. The set of applicable keys is defined
        per measurement in the related "Measurement Context"
        in clause 7.2 of ETSI GS NFV-IFA 027 [#NFV-IFA027_331]_.
    * - _links
      - Structure
      - 1
      - Links to resources related to this notification.
    * - >objectInstance
      - NotificationLink
      - 0..1
      - Link to the resource representing the measured object
        instance to which the notification applies. Shall be present
        if the measured object instance information is accessible
        as a resource.
    * - >threshold
      - NotificationLink
      - 1
      - Link to the resource that represents the threshold that was crossed.

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

The following RESTful APIs are Tacker specific interfaces
used for PM Threshold between Tacker and External Monitoring Tool.

* | **Name**: Send a PM Threshold event
  | **Description**: Receive the PM Threshold event
                     sent from External Monitoring Tool
  | **Method type**: POST
  | **URL for the resource**: /pm_threshold
  | **Request**:

  .. list-table::
    :header-rows: 1
    :widths: 18 10 50

    * - Data type
      - Cardinality
      - Description
    * - ThresholdEvent
      - 1
      - The PM Thresholdevent sent from
        External Monitoring Tool

  .. list-table::
    :header-rows: 1
    :widths: 18 18 10 50

    * - Attribute name (ThresholdEvent)
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
      - Type of function: vnfpm-threshold
    * - >>threshold_id
      - Identifier
      - 1
      - Identifier of the PM Threshold
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
      - Structure
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
      - 0..1
      - The end time of an alert.
    * - >fingerprint
      - String
      - 1
      - Fingerprint that can be used to identify the alert.

Security impact
---------------

None

Notifications impact
--------------------

Performance Management:
  + Tacker sends POST <Client URI for notifications>
    to NFVO or EM to notify Client that Tacker received
    a PM threshold related event.

  + Tacker sends GET <Client URI for notifications>
    to NFVO or EM to confirm that the URI of Client is correct.

  + Tacker creates prometheus rule files related to
    PM threshold requests and upload these files using SSH.

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
  Yuta Kazato <yuta.kazato.nw@hco.ntt.co.jp>

  Kenta Fukaya <kenta.fukaya.xv@hco.ntt.co.jp>

Other contributors:
  Koji Shimizu <shimizu.koji@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

Work Items
----------

* Implement Tacker to support:

  * Performance Management interface

    * Add new Rest API ``POST /vnfpm/v2/thresholds`` to create a threshold.

    * Add new Rest API ``GET /vnfpm/v2/thresholds`` to get all thresholds.

    * Add new Rest API ``GET /vnfpm/v2/thresholds/{thresholdId}`` to get
      the specified threshold.

    * Add new Rest API ``PATCH /vnfpm/v2/thresholds/{thresholdId}`` to update
      target threshold callback.

    * Add new Rest API ``DELETE /vnfpm/v2/thresholds/{thresholdId}`` to delete
      the specified threshold.

    * Add new request ``POST <Client URI for notifications>`` to notify
      Client that Tacker received a threshold alerm.

    * Add new request ``GET <Client URI for notifications>`` to confirm
      that the URI of Client is correct.

  * External Monitoring interface

    * Add new Rest API ``POST /pm_threshold``
      to receive the PM threshold event sent from External Monitoring Tool.

* Add new unit and functional tests.

Dependencies
============

None.

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

* Add Threshold examination to Tacker User guide.
* Update API documentation on the API additionsmentioned in
  `REST API impact`_.

References
==========

.. [#SOL002_v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_nfv-sol002v030301p.pdf
.. [#SOL003_v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
.. [#Prometheus_usecase_guide] https://docs.openstack.org/tacker/latest/user/prometheus_plugin_use_case_guide.html
.. [#Prometheus] https://prometheus.io/docs/introduction/overview/
.. [#NFV-SOL013_341] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.04.01_60/gs_nfv-sol013v030401p.pdf
.. [#NFV-IFA027_331] https://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/027/03.03.01_60/gs_nfv-ifa027v030301p.pdf
