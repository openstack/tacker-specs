..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


======================================================
Support fundamental VNF lifecycle management in Tacker
======================================================

https://blueprints.launchpad.net/tacker/+spec/support-fundamental-lcm

This specification describes APIs of fundamental VNF
lifecycle management based on ETSI NFV-SOL specification.

ETSI specifications within the NFV Architecture Framework [#etsi_nfv]_
describe the main aspects of NFV development and usage based on the
industry needs, feedback from SDN/NFV vendors and telecom operators.
These specifications include the REST API and data model architecture
which is used by NFV users and developers in related products.

Problem description
===================
Support of key ETSI NFV specifications will
significantly reduce efforts for Tacker integration into telecom production
networks and also will simplify further development and support of future
standards.

In the former release, we have added limited support of VNF lifecycle management as
defined in ETSI NFV SOL 002 [#etsi_sol002]_ and SOL 003 [#etsi_sol003]_.
Tacker should support more APIs and attributes to compliant ETSI NFV SOL specification
and expand a wide range of use cases.

Proposed change
===============

The operations provided through new APIs in this specification are below.
 - support additional APIs:
     - Notification endpoint (GET)
     - VNF LCM operation occurrences (GET)

The operations provided through additional attributes in this specification are below.
 - support additional attributes:
      - Individual VNF LCM operation occurrence (GET)
 - support filtering:
      - Subscriptions (POST, GET)
      - Individual subscription (GET)

1) Flow of Notification endpoint (GET)
--------------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " POST /subscriptions"];
    "tacker-server" -> Client [label = " GET {callback URI}"];
    "tacker-server" <-- Client [label = " Response 204 No Content"];
    "tacker-server" -> "tacker-server"
      [label = " generate subscription_id (uuid)"];
    Client <-- "tacker-server" [label = " Response 201 Created"];
  }

The procedure consists of the following steps as illustrated in the above sequence:

#. The Client sends a Create Subscription request.
#. VNFM sends Notification to test the notification endpoint obtained from Create
   Subscription request.
#. The Client returns a 204 No Content response to indicate success.
#. VNFM returns a 201 Created response.

2) Flow of VNF LCM operation occurrence (GET)
---------------------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " GET /vnf_lcm_op_occs"];
    "tacker-server" -> "tacker-server" [label = "request validation"];
    Client <-- "tacker-server" [label = " Response 200 OK"];
  }

The procedure consists of the following steps as illustrated in the above sequence:

#. The Client sends a GET request to the "VNF LCM operation occurrences" resource
   and can use attribute-based filtering expression that follows clause 5.2 of
   ETSI GS NFV SOL13 [#etsi_sol013]_.
#. VNFM returns a response that includes zero or more data structures of type
   "VnfLcmOpOcc" in the payload body.

3) Flow of individual VNF LCM operation occurrences (GET)
---------------------------------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " GET /vnf_lcm_op_occs/{vnfLcmOpOccId}"];
    Client <-- "tacker-server" [label = " Response 200 OK"];
  }

#. The Client sends a GET request to the "Individual VNF LCM operation occurrence" resource,
   addressed by the appropriate VNF LCM operation occurrence identifier in its resource URI.
#. VNFM returns a 200 OK response to the client, and includes one data structure of type
   "VnfLcmOpOcc" in the payload body.
   "grantId", "changedExtConnectivity", "_links > retry" and "_links > fail"attribute is
   newly supported in Wallaby version.

4) Flow of Subscriptions (POST)
-------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " POST /subscriptions"];
    "tacker-server" -> Client [label = " GET {callback URI}"];
    "tacker-server" <-- Client [label = " Response 204 No Content"];
    "tacker-server" -> "tacker-server"
      [label = " generate subscription_id (uuid)"];
    Client <-- "tacker-server" [label = " Response 201 Created"];
  }

#. The Client sends a POST request to the "Subscriptions" resource including in the
   payload body a data structure of type "LccnSubscriptionRequest".
   That data structure contains filtering criteria and a client side
   URI to which the VNFM will subsequently send notifications about events that match
   the filter.
   "filter > vnfInstanceSubscriptionFilter" and "filter > operationStates" attribute is
   newly supported in Wallaby version.
#. VNFM returns a 201 Created response containing a data structure of type "LccnSubscription"
   representing the "Individual subscription" resource just created by the VNFM.
   "filter > vnfInstanceSubscriptionFilter" and "filter > operationStates" attribute is
   newly supported in Wallaby version.

5) Flow of Subscriptions (GET)
------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " GET /subscriptions"];
    "tacker-server" -> "tacker-server" [label = "request validation"];
    Client <-- "tacker-server" [label = " Response 200 OK"];
  }

#. The Client sends a GET request to the resource representing the subscriptions.
#. VNFM returns a 200 OK response that contains zero or more representations of all existing
   subscriptions.
   "filter > vnfInstanceSubscriptionFilter" and "filter > operationStates" attribute is
   newly supported in Wallaby version.

6) Flow of Individual subscriptions (GET)
-----------------------------------------

.. seqdiag::

  seqdiag {
    Client -> "tacker-server" [label = " GET /subscriptions/{subscriptionId}"];
    Client <-- "tacker-server" [label = " Response 200 OK"];
  }

#. The Client sends a GET request to the resource representing the individual subscription.
#. VNFM returns a 200 OK response that contains a representation of that individual
   subscription.
   "filter > vnfInstanceSubscriptionFilter" and "filter > operationStates" attribute is
   newly supported in Wallaby version.

Alternatives
------------

None

Data model impact
-----------------

Modify following tables in current Tacker database. The corresponding
schemas are detailed below:

vnf_lcm_op_occs:

.. code-block:: python

   grant_id varchar(36)
   changed_ext_connectivity json

vnf_lcm_filters:

.. code-block:: python

   vnfd_ids MEDIUMBLOB
   vnf_products_from_providers json
   vnf_provider VARBINARY(255)
   vnf_product_name vnf_product_name
   vnf_software_version VARBINARY(255)
   vnfd_versions MEDIUMBLOB
   vnfd_versions_len int
   vnf_instance_ids MEDIUMBLOB
   vnf_instance_ids_len int
   vnf_instance_names MEDIUMBLOB
   vnf_instance_names_len int
   operation_states MEDIUMBLOB
   operation_states_len int

REST API impact
---------------
A) Support new APIs
~~~~~~~~~~~~~~~~~~~
The following APIs will be added. These attributes are based on
ETSI NFV SOL002 [#etsi_sol002]_ and SOL003 [#etsi_sol003]_.

The flow of the Subscriptions API is enhanced by a new API.
The notification endpoint API allows the server to test the
notification endpoint that is provided by the client during subscription.

* | **Name**: Notification endpoint
  | **Description**: The method allows the server to test
      the notification endpoint that is provided by the client.
  | **Method type**: GET
  | **URL for the resource**: The resource URI is provided by
      the client when creating the subscription.
  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - n/a
       - n/a
       - | Success 204
         | Error 4xx/ 5xx
       - The notification endpoint has been tested successfully.

Note: If this API returns an error response, the Subscriptions API
that triggers it will return a 400 error response.

* | **Name**: VNF LCM operation occurrence
  | **Description**: Request VNF lifecycle management operation occurrence
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_lcm_op_occs
  | **URI query parameters supported by the GET method**:

  .. list-table::
     :header-rows: 1

     * - URI query parameter
       - Cardinality
       - Support in Wallaby
     * - filter
       - 0..1
       - Yes
     * - all_fields
       - 0..1
       - Yes
     * - fields
       - 0..1
       - Yes
     * - exclude_fields
       - 0..1
       - Yes
     * - exclude_default
       - 0..1
       - Yes
     * - nextpage_opaque_marker
       - 0..1
       - No

  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - VnfLcmOpOcc
       - 1
       - | Success 200
         | Error 4xx
       - Status information for zero or more VNF lifecycle
         management operation occurrences has been queried successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - id
       - Identifier
       - 1
       - Yes
     * - operationState
       - LcmOperationStateType
       - 1
       - Yes
     * - stateEnteredTime
       - DateTime
       - 1
       - Yes
     * - startTime
       - DateTime
       - 1
       - Yes
     * - vnfInstanceId
       - Identifier
       - 1
       - Yes
     * - grantId
       - Identifier
       - 1
       - Yes
     * - operation
       - LcmOperationType
       - 1
       - Yes
     * - isAutomaticInvocation
       - Boolean
       - 1
       - Yes
     * - operationParams
       - Object
       - 1
       - Yes
     * - isCancelPending
       - Boolean
       - 0..N
       - No
     * - cancelMode
       - CancelModeType
       - 0..N
       - No
     * - error
       - ProblemDetails
       - 0..N
       - Yes
     * - resourceChanges
       - Structure(inlined)
       - 0..1
       - Yes
     * - changedInfo
       - VnfInfoModifications
       - 0..N
       - Yes
     * - changedExtConnectivity
       - ExtVirtualLinkInfo
       - 0..1
       - Yes
     * - _links
       - Structure (inlined)
       - 1
       - Yes
     * - >self
       - Link
       - 1
       - Yes
     * - >vnfInstance
       - Link
       - 1
       - Yes
     * - >grant
       - Link
       - 0..1
       - Yes
     * - >cancel
       - Link
       - 0..1
       - No
     * - >retry
       - Link
       - 0..1
       - Yes
     * - >rollback
       - Link
       - 0..1
       - Yes
     * - >fail
       - Link
       - 0..1
       - Yes


B) Support new attributes of implemented APIs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following attributes of REST APIs will be added. These attributes are
based on ETSI NFV SOL002 [#etsi_sol002]_ and SOL003 [#etsi_sol003]_.
Details of APIs implemented in previous versions are
described in NFV Orchestration API v1.0 [#NFV_Orchestration_API_v1.0]_.

B-1) Support additional attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* | **Name**: Query VNF occurrence
  | **Description**: Request individual VNF lifecycle
      management operation occurrence by its id
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}
  | **Resource URI variables for this resource:**:

  +----------------+---------------------------------------------------------------+
  | Name           | Description                                                   |
  +================+===============================================================+
  | vnfLcmOpOccId  | Identifier of a VNF lifecycle management operation occurrence.|
  +----------------+---------------------------------------------------------------+

  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - VnfLcmOpOcc
       - 1
       - | Success 200
         | Error 4xx
       - The operation has completed successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - grantId
       - Identifier
       - 0..1
       - Yes
     * - _links
       - Structure (inlined)
       - 1
       - Yes
     * - >retry
       - Link
       - 0..1
       - Yes
     * - >fail
       - Link
       - 0..1
       - Yes

B-2) Support filtering
~~~~~~~~~~~~~~~~~~~~~~

* | **Name**: List subscriptions
  | **Description**: Request list of all existing
      subscriptions to VNF lifecycle management
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/subscriptions
  | **URI query parameters supported by the GET method**:

  .. list-table::
     :header-rows: 1

     * - URI query parameter
       - Cardinality
       - Description
       - Supported in Wallaby
     * - filter
       - 0..1
       - Filter to list subscriptions
       - Yes

  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - LccnSubscription
       - 0..N
       - | Success 200
         | Error 4xx/ 5xx
       - The operation has completed successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - filter
       - LifecycleChangeNotificationsFilter
       - 0..1
       - Yes
     * - vnfInstanceSubscriptionFilter
       - VnfInstanceSubscriptionFilter
       - 0..1
       - Yes
     * - >operationStates
       - LcmOperationStateType
       - 0..N
       - Yes

* | **Name**: Subscriptions
  | **Description**: Subscribe to notifications
      related to VNF lifecycle management
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v1/subscriptions
  | **Request**:

  +--------------------------+-------------+----------------------------------+
  | Data type                | Cardinality | Description                      |
  +==========================+======+======+==================================+
  | LccnSubscriptionRequest  | 1           | Parameters for the Subscription. |
  +--------------------------+-------------+----------------------------------+

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - filter
       - LifecycleChangeNotificationFilter
       - 0..1
       - Yes
     * - callbackUri
       - Uri
       - 1
       - Yes
     * - authentication
       - SubscriptionAuthentication
       - 0..1
       - Yes

  **Response**:

  .. list-table::
     :widths: 10 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - LccnSubscription
       - n/a
       - | Success 201
         | Redirection 303
         | Error 4xx
       - The subscription has been created successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - filter
       - LifecycleChangeNotificationsFilter
       - 0..1
       - Yes
     * - >vnfInstanceSubscriptionFilter
       - VnfInstanceSubscriptionFilter
       - 0..1
       - Yes
     * - >operationStates
       - LcmOperationStateType
       - 0..N
       - Yes

* | **Name**: Query subscriptions
  | **Description**: Request individual subscription resource by its id
  | **Method type**: GET
  | **URL for the resource**: /vnflcm/v1/subscriptions/{subscriptionId}
  | **Resource URI variables for this resource:**:

  +----------------+----------------------------------+
  | Name           | Description                      |
  +================+==================================+
  | subscriptionId | Identifier of the subscriptions. |
  +----------------+----------------------------------+

  | **Response**:

  .. list-table::
     :widths: 12 10 18 50
     :header-rows: 1

     * - Data type
       - Cardinality
       - Response Codes
       - Description
     * - LccnSubscription
       - 1
       - | Success 200
         | Error Error 4xx/ 5xx
       - The operation has completed successfully.

  .. list-table::
     :header-rows: 1

     * - Attribute name
       - Data type
       - Cardinality
       - Supported in Wallaby
     * - filter
       - LifecycleChangeNotificationsFilter
       - 0..1
       - Yes
     * - >vnfInstanceSubscriptionFilter
       - VnfInstanceSubscriptionFilter
       - 0..1
       - Yes
     * - >operationStates
       - LcmOperationStateType
       - 0..N
       - Yes

Security impact
---------------

None


Notifications impact
--------------------

This specification enhances APIs related to
subscriptions and notification for VNF lifecycle management.

Other end user impact
---------------------

* Add new OSC commands in python-tackerclient to
  invoke VNF LCM operation occurrence and Query VNF occurrence.
* A client must be configured to return 204 for
  the request of notification endpoint (GET).

Performance impact
------------------

None

Other deployer impact
---------------------

The previously created VNFs will not be allowed to be managed using the newly
introduced APIs.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>
Other contributors:
  Keiko Kuriu <keiko.kuriu.wa@hco.ntt.co.jp>

Work Items
----------

* Add new REST APIs and supported attributes to Tacker-server.
* Make changes in python-tackerclient to add new OSC commands for calling
  APIs of VNF LCM operation occurrence and Query VNF occurrence.
* Add new unit and functional tests.
* Change API Tacker documentation.

Dependencies
============

None

Testing
========

Unit and functional test cases will be added for VNF lifecycle management
of VNF instances.

Documentation Impact
====================

Complete user guide will be added to explain how to invoke VNF lifecycle
management of VNF instances with examples.

References
==========

.. [#etsi_nfv] https://www.etsi.org/technologies-clusters/technologies/NFV
.. [#etsi_sol002]
   https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
   (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_sol003]
   https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
   (Chapter 5: VNF Lifecycle Management interface)
.. [#etsi_sol013]
   https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/02.06.01_60/gs_nfv-sol013v020601p.pdf
   (Chapter 5: Result set control)
.. [#NFV_Orchestration_API_v1.0]
   https://docs.openstack.org/api-ref/nfv-orchestration/v1/index.html#virtualized-network-function-lifecycle-management-interface-vnf-lcm
