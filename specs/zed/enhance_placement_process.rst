..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


=========================
Enhance Placement Process
=========================

.. Blueprints:

- https://blueprints.launchpad.net/tacker/+spec/enhance-placement

This specification supports the placement functionality for VNF instance
and enhances the applicability of Tacker to various systems.

Problem description
===================

The placement constraints are defined in ETSI NFV-SOL 003 v3.3.1
[#NFV-SOL003_331]_ and that VNFM sends to NFVO in order to the resource
placement decision.
In VNF Lifecycle Management (LCM), there are some cases that VNFs are
not deployed due to placement constraints or lack of availability zone's
resources.
From a high-availability perspective, Tacker needs to implement a
``fallbackBestEffort`` option in Grant Request and availability zone
reselection functions.

Proposed change
===============

1. Add fallbackBestEffort parameter
-----------------------------------

``fallbackBestEffort`` is to look for an alternate best effort placement
for specified resources cannot be allocated based on specified placement
constraint and defined in ETSI NFV-SOL 003 v3.3.1 [#NFV-SOL003_331]_.
On this specification, Tacker will support additional parameter
``fallbackBestEffort`` in Grant Request (``PlacementConstrains``) and Tacker
configuration settings.
We will modify Tacker conductor and ``tacker.conf``.
Add definitions details are described in :ref:`3. Add definitions to the
configuration file<configuration-file>`.

* GrantRequest.PlacementConstrains

  .. list-table::
      :widths: 15 10 30 30
      :header-rows: 1

      * - Attribute name
        - Data type
        - Cardinality
        - Description
      * - fallbackBestEffort
        - Boolean
        - 0..1
        - Indication if the constraint is handled with fall back best
          effort. Default value is "false".

.. note::
  If ``fallbackBestEffort`` is present in placement constraints and set to
  "true", the NFVO shall process the Affinity/Anti-Affinity constraint
  in a best effort manner, in which case, if specified resources cannot
  be allocated based on specified placement constraint, the NFVO looks
  for an alternate best effort placement for the specified resources to
  be granted.

2. Availability zone reselection
--------------------------------

The VNFLCM v2 API (instantiate/heal/scale for VNF) process can change
the availability zone to be used from the one notified by the NFVO if
necessary.
If the availability zone notified by the NFVO has insufficient
resources, the VNF is created/updated in a different availability zone.
The availability zone is reselected considering Affinity/Anti-Affinity
and re-create/update until there are no more candidates.

1) Flowchart of availability zone reselection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. blockdiag::

  blockdiag {
    orientation = portrait;
    edge_layout = flowchart;

    create [shape=flowchart.condition,label='stack create/update'];
    start [shape=beginpoint];
    lin [shape=flowchart.loopin,label='stack create/update\nin other AZ'];
    recreate [shape=flowchart.condition,label='stack create/update'];
    lout [shape=flowchart.loopout,label='no more AZ\ncandidates'];
    failure [shape=endpoint,label='end'];
    success [shape=endpoint,label='end'];

    class none [shape=none];
    n [class=none];

    start -> create [label='NFVO AZ']
    create -> lin [label=error]
    lin -> recreate [label='other AZ']
    recreate -> lout [label='error']
    lout -> failure [label='failure'];

    create -> success;

    recreate -> n [dir=none]
    n -> success [label='success'];
  }

The procedure consists of the following steps as illustrated in above
flow:

#. Execute "stack create/update" in the availability zone notified by
   the NFVO.
#. If an error occurs in 1, get the availability zone list.
   Availability zone list details are described in :ref:`2) Get and
   manage availability zone list<az-list>`.
#. Select an availability zone (excluding the Availability Zone where
   the error occurred) randomly in compliance with
   Affinity/Anti-Affinity from the availability zone list obtained in 2,
   and re-execute “stack create/update”.
   Reselection policy details are described in :ref:`3) Availability
   zone reselection policy<reselection-policy>`.
#. If "stack create/update" in the availability zone reselected in 3
   becomes an error, reselect the availability zone and repeat until
   "stack create/update" succeeds or until all availability zone
   candidates fail.
   Detecting error details are described in :ref:`4) Detection method
   of insufficient resource error<detection-method>`.

.. _az-list:

2) Get and manage availability zone list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Get availability zone list``

+ Extract all availability zones as candidates for reselection without
  limiting the availability zones to be reselected.
  Although it is possible to extract only availability zones permitted
  by Grant as candidates for reselection, this is not adopted in this
  Spec because it depends on the NFVO product specifications.

+ The concept of availability zone exists for Compute/Volume/Network,
  but this Spec targets only Compute.
  The reason is that SOL(SOL003 v3.3.1 Type: GrantInfo
  [#NFV-SOL003_331]_) specifies that the zoneId of GrantInfo, which is
  the data type of addResources, etc., is usually specified as a COMPUTE
  resource.

  .. note::
    ``SOL003 v3.3.1 Type: GrantInfo``

    Reference to the identifier of the "ZoneInfo" structure in the
    "Grant" structure defining the resource zone into which this
    resource is to be placed. Shall be present for new resources if the
    zones concept is applicable to them (typically, Compute resources)
    and shall be absent for resources that have already been allocated.
    Shall be present for new resources if the zones concept is
    applicable to them (typically, Compute resources) and shall be
    absent for resources that have been allocated.

+ Call the Compute-API "GetDetailedAvailabilityZoneInformation"
  [#Compute-API]_ to get the availability zones from the "hosts"
  response associated with "nova-compute".

  Compute endpoints are obtained in the following way.

  1. Get Keystone endpoint from
     VnfInstance.vimConnectionInfo.interfaceInfo.endpoint
  2. Call "List endpoints" [#Keystone-API_endpoints]_ and "List
     services" [#Keystone-API_services]_ of Keystone-API to link obtained
     Compute's services and endpoint

``Manage availability zone list``

+ Keep in on-memory until availability zone reselection iterations are
  completed, and discard after completion (no storage in DB).

  .. note::
    ``Error-Handling Retry consideration``

    Since the availability zone list is not saved and is retrieved
    again, there is no guarantee that the availability zone is
    reselected in the same order when Retry is executed.

.. _reselection-policy:

3) Availability zone reselection policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Availability zones in error are excluded from the reselection
candidates, and Availability zones are reselected randomly in compliance
with Affinity/Anti-Affinity of PlacementConstraint.

The availability zone in error can be identified in the following way.

1. Call Heat-API "Show stack details" after an error occurs in "stack
   create/update"
2. Identify the VDU where the error occurred due to insufficient resource
   by the stack_status_reason in the response of 1.
3. Identify the availability zone by the VDU identified in 2.

.. note::

  Insufficient resource in availability zones that once failed during
  reselection attempts may be resolved, but the availability zones will
  not be reselected.
  In Scale/Heal operations, VDUs that have already been deployed will
  not be re-created.

Availability zone reselection for each PlacementConstraint is as
follows.

Precondition: availability zone AZ-1/AZ-2/AZ-3 exist and VNF VDU-1/VDU-2
are deployed

+ PlacementConstraint is Anti-Affinity

  + Before reselection, the following attempts to deploy failed (AZ-1
    has insufficient resource)

    + VDU-1: AZ-1

    + VDU-2: AZ-2

  + Reselect the following (except AZ-1, select AZ-2/AZ-3 in compliance
    with Anti-Affinity)

    + VDU-1: AZ-2

    + VDU-2: AZ-3

  .. note::

    The above is an example, and it is possible that the reverse
    availability zones are selected for VDU-1 and VDU-2, but it is
    guaranteed that they will not be the same availability zone.


+ PlacementConstraint is Affinity

  + Before reselection, attempt to deploy in the following and fail
    (AZ-1 has insufficient resource)

    + VDU-1: AZ-1

    + VDU-2: AZ-1

  + Reselect the following (except AZ-1, select AZ-2/AZ-3 in compliance
    with Affinity)

    + VDU-1: AZ-2

    + VDU-2: AZ-2

  .. note::

    The above is an example, and it is possible that the availability
    zone AZ-3 is selected for VDU-1 and VDU-2, but it is guaranteed
    that they will be the same availability zone.


.. _detection-method:

4) Detection method of insufficient resource error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When "stack create/update" fails, it is detected from "Show stack details"
[#Heat-API]_ of Heat-API response whether the failure is due to
insufficient resources.
The error message that indicates insufficient resources is extracted
from the parameter "stack_status_reason" in the response.

.. note::

  In the case of insufficient resources, the error occurs after "stack
  create/update" returns an acceptance response, so the "Show stack
  details" response is used to detect the cause.

The following is an example of an error message stored in
"stack_status_reason" when resources are insufficient.

+ ex1) Set the flavor defined in “OS::Nova::Server” to a large value
  that cannot be deployed (not enough storage/not enough vcpu/not enough
  memory).

  + Resource CREATE failed: ResourceInError: resources.<VDU-name>: Went
    to status ERROR due to “Message: No valid host was found. , Code:
    500”

+ ex2) Specifies an extra-spec that cannot be assigned for the flavor
  defined in "OS::Nova::Server."

  + Resource CREATE failed: ResourceInError: resources.<VDU-name>: Went
    to status ERROR due to “Message: Exceeded maximum number of retries.
    Exhausted all hosts available for retrying build failures for
    instance <server-UUID>., Code: 500”

Error messages that Tacker detects as insufficient resources are
specified by a regular expression in the configuration file.
Add definitions details are described in :ref:`3. Add definitions to the
configuration file<configuration-file>`.

By changing the method of specifying this regular expression in
accordance with the operational policy, it is possible to flexibly set a
policy to detect more error messages as insufficient resource with a
higher tolerance for misdetection, or to detect only specific error
messages as insufficient resource.

+ ex1) Regular expression for a policy to detect more error messages
  as insufficient resource by increasing the tolerance for
  misclassification

  + Resource CREATE failed:(. \*)

+ ex2) Regular expression to specify the policy to detect more error
  messages as insufficient resource with higher tolerance for false
  positives

  + Resource CREATE failed: ResourceInError: resources(. \*): Went to
    status ERROR due to "Message: No valid host was found. \*): Went to
    status ERROR due to "Message: Exceeded maximum number of retries.
    Exhausted all hosts available for retrying build failures for
    instance(. \*). , Code: 500".

5) AutoScalingGroup consideration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In BaseHOT which includes AutoScalingGroup definitions, there is a
constraint that each VNFC associated with a VDU under AutoScalingGroup
cannot be set to Anti-Affinity for the availability zone.
This constraint is due to the constraint in the HOT specification that
availability zones can only be set for each VDU under the
AutoScalingGroup.
This constraint occurs not only at the time of reselection, but also at
the time of initial execution.
Therefore, BaseHOT which includes AutoScalingGroup definitions, ignores
the PlacementConstraint for each VNFC associated with a VDU and
reselects a single availability zone for each VDU under the
AutoScalingGroup. (Always set to Affinity.)

top HOT:

.. code-block::

  resources:
    VDU1_scale_group:
      type: OS::Heat::AutoScalingGroup
      properties:
        min_size: 1
        max_size: 3
        desired_capacity: { get_param: [ nfv, VDU, VDU1, desired_capacity ] }
        resource:
          type: VDU1.yaml
          properties:
            flavor: { get_param: [ nfv, VDU, VDU1, computeFlavourId ] }
            image: { get_param: [ nfv, VDU, VDU1-VirtualStorage, vcImageId ] }
            zone: { get_param: [ nfv, VDU, VDU1, locationConstraints] }
            net1: { get_param: [ nfv, CP, VDU1_CP1, network] }
            net2: { get_param: [ nfv, CP, VDU1_CP2, network ] }
            subnet1: { get_param: [nfv, CP, VDU1_CP1, fixed_ips, 0, subnet ]}
            subnet2: { get_param: [nfv, CP, VDU1_CP2, fixed_ips, 0, subnet ]}
            net3: { get_resource: internalVL1 }
            net4: { get_resource: internalVL2 }
            net5: { get_resource: internalVL3 }

nested HOT:

.. code-block::

  resources:
    VDU1:
      type: OS::Nova::Server
      properties:
        flavor: { get_param: flavor }
        name: VDU1
        block_device_mapping_v2: [{"volume_id": { get_resource: VDU1-VirtualStorage }}]
        networks:
        - port:
            get_resource: VDU1_CP1
        - port:
            get_resource: VDU1_CP2
        - port:
            get_resource: VDU1_CP3
        - port:
            get_resource: VDU1_CP4
        - port:
            get_resource: VDU1_CP5
        availability_zone: { get_param: zone }

As shown above, top HOT specifies a single "zone" (availability zone)
for each VDU under the AutoScalingGroup, so each VNFC associated with a
VDU under the AutoScalingGroup is in the same availability zone.

.. _configuration-file:

3. Add definitions to the configuration file
--------------------------------------------

Add the following definition to the ``tacker.conf`` file.

+ Boolean value of "GrantRequest.PlacementConstrains.fallbackBestEffort"

  Default value: "false"

+ Whether or not to reselect availability zone

  Default value: not to reselect

+ Regular expression for detecting insufficient resource error

  Default value: regular expression for insufficient resource error

  .. note::
    Consider the regular expression that can catch stack create and
    stack update errors.

+ Maximum number of retries for reselection of availability zone

  Default value: no upper limit

  .. note::
    Consider the case where there are a large number of availability
    zones and the availability zone reselection process takes too long.


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
  Yuta Kazato <yuta.kazato.nw@hco.ntt.co.jp>

  Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>

Other contributors:
  Hiroo Kitamura <hiroo.kitamura@ntt-at.co.jp>

  Ai Hamano <ai.hamano@ntt-at.co.jp>

Work Items
----------

* Implement availability zone reselection functions.
* Add new parameter ``fallbackBestEffort`` in GrantRequest API.
* Add new definitions to the Tacker configuration file ``tacker.conf``.
* Add new unit and functional tests.
* Add new examples to the Tacker User Guide.

Dependencies
============

* VNF Lifecycle Operation Granting interface
  (Grant Lifecycle Operation) [#NFV-SOL003_331]_

* VNF Lifecycle Management interface
  (Instantiate/Heal/Scale VNF) [#NFV-SOL003_331]_

Testing
========

Unit and functional test cases will be added for the new placement functionalities.

Documentation Impact
====================

New supported functions need to be added into the Tacker User Guide.

References
==========

.. [#NFV-SOL003_331] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf

.. [#Compute-API] https://docs.openstack.org/api-ref/compute/?expanded=get-detailed-availability-zone-information-detail#availability-zones-os-availability-zone

.. [#Keystone-API_endpoints] https://docs.openstack.org/api-ref/identity/v3/?expanded=list-endpoints-detail#list-endpoints

.. [#Keystone-API_services] https://docs.openstack.org/api-ref/identity/v3/?expanded=list-services-detail#list-services

.. [#Heat-API] https://docs.openstack.org/api-ref/orchestration/v1/index.html?expanded=show-stack-details-detail#show-stack-details
