..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=================================================
Enable using resources reserved by Blazar for VNF
=================================================

https://blueprints.launchpad.net/tacker/+spec/reservation-vnfm

This proposal aims at supporting reservation_id for a VDU in a VNFD.
The spec is referred to management of compute resource reservations in
ETSI standard [#nfv-ifa010]_.

Problem description
===================

Currently Tacker doesn't support resource reservation. However in the
telco industry, system resource reservations are often needed for VNF
stable operation. VNF could be operated under conditions with limited
infrastructure resources. In such situation, resource reservation is
useful for upcoming scaling-out, maintenance works, disaster recovery
[#usecase]_.

For example, some VNFs are deployed with a different priority on the
limited infra resources and scaling-out of the higher priority VNF will
be expected due to increased demand in certain periods. Operators of
higher priority VNF need to reserve resources for their VNF not to all
resources are consumed by other VNFs.

Architecture of reservation feature in NFV is specified in "Management
of resource reservations" ETSI GS NFV-IFA010 [#nfv-ifa010]_. According
to this standard, each component in MANO shall support features as
below.

* NFVO

  * decides if and when a resource reservation is needed
  * requests a reservation to VIM
  * inform a reservation identifier provided by VIM to VNFM

* VNFM

  * requesting reserved resource with reservation identifier

* VIM

  * provide resource reservation interface

Compute resource reservation interfaces are implemented by Blazar
project [#blazar_wiki]_ and now available. Blazar supports ``Host
Reservation`` and ``Instance Reservation``. To use ``Host Reservation``,
a user specifies ``--hint reservation=<reservation_id>`` parameter when
creating a instance [#blazar_host]_. To use ``Instance Reservation``, a
user use a flavor and server_group_id created by Blazar
[#blazar_instance]_. However Tacker doesn't support to specify this
parameter and this spec plans to support it.

Additionally if a VNF is deployed using reserved resources, as for the
case described above the VNF is expected scaling-out at the timing of
start of the reservation and scaling-in at end of it. This spec also
plans to support these scaling-out or scaling-in without human
operations.

Proposed change
===============

* Add a new section 'reservation_metadata' under properties of node type
  `tosca.nodes.nfv.VDU.Tacker`.

  ``tacker_nfv_defs.yaml`` and ``tacker_defs.yaml`` are changed as below.

  .. code-block:: yaml

    node_types:
      tosca.nodes.nfv.VDU.Tacker:
        derived_from: tosca.nodes.nfv.VDU
        ...
        properties:
          ...
          reservation_metadata:
            required: false
            type: tosca.datatypes.tacker.VduReservationMetadata

  .. code-block:: yaml

    datatypes:
      ...
      tosca.datatypes.tacker.VduReservationMetadata:
       properties:
         resource_type:
           type: string
           required: true
           constraints:
             - valid_values: [ physical_host, virtual_instance ]
         id:
           type: string
           required: true

  Operator should include `reservation_metadata` and specify parameters
  `resource_type` and `id` as per the resources reserved by the `Blazar`
  service. The parameter `resource_type` can be of two types
  `physical_host` or `virtual_instance`. When you create a lease in
  `Blazar`, you need to specify what kind of resources you want to
  reserve. If the `resource_type` is `virtual_instance` then after the
  lease is created successfully it returns `server_group_id` in the
  response and this `server_group_id` should be specified in the `id`
  parameter above. Similarly, if the `resource_type` is `physical_host`,
  then the `reservation.id` should be specified in the `id` parameter
  above. This `id` parameter will be used to instruct `Nova` how to
  schedule a `VDU`.

  Below example of VNFD template shows reservation for
  `virtual_instance` resource_type:

  .. code-block:: yaml

    :caption: Example VNFD with reservation for `virtual_instance`
              resource_type
    tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
    description: VDU with a reserved `virtual_instance`
    node_templates:
      - VDU_RSV:
        type: tosca.node.nfv.VDU.Tacker
        properties:
          ...
          reservation_metadata:
            resource_type: virtual_instance
            id: { get_input: server_group_id }


  .. code-block:: yaml

    :caption: Example parameter file
    topology_template:
      inputs:
        server_group_id:
          type: string
          description: server group id

  The above VNFD template will be translated to Heat Orchestration
  Template as shown below:

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    resources:
      VDU_RSV:
        type: OS::Nova::Server
        ...
        scheduler_hints: { group: <server_group_id> }

  On the other hand, an example of reservation for `physical_host` is
  below:

  .. code-block:: yaml

    :caption: Example VNFD with reservation for `physical_host`
              resource_type
    tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
    description: VDU with a reserved `physical_host`
    node_templates:
      - VDU_RSV:
        type: tosca.node.nfv.VDU.Tacker
        properties:
          ...
          reservation_metadata:
            resource_type: physical_host
            id: { get_input: reservation_id }


  .. code-block:: yaml

    :caption: Example parameter file
    topology_template:
      inputs:
        reservation_id:
          type: string
          description: reservation id

  The above VNFD template will be translated to Heat Orchestration
  Template as shown below:

  .. code-block:: yaml

    heat_template_version: 2013-05-23
    resources:
      VDU_RSV:
        type: OS::Nova::Server
        ...
        scheduler_hints: { reservation: <reservation_id> }

* Add a new policy "tosca.policies.tacker.Reservation"

  In this policy, you can specify actions that you want to execute when
  Blazar triggers event for start of lease, before end of lease and end
  of lease.

  For the use case described above, only scaling-out and in actions are
  enough to support, that is, ``tosca.policies.tacker.Scaling`` type
  policy can be specified in ``start_actions``, ``before_end_actions``
  and ``end_actions`` parameters. However, in the future, other actions
  may be needed if we find new use cases.

  We are planning to execute scaling-out as ``start_actions`` action for
  start of lease and scaling-in as ``before_end_actions`` before end of
  lease as shown in below sample of VNFD. In this sample, VNF scales out
  at start of reservation, so this means that the VNF is created before
  the start of reservation. Therefore VDU are not allow to be created
  using reserved resources at the timing of VNF creation. To solve this
  problem, VNF will be created with no VDUs for ``VDU_RSV`` in the
  beginning as the ``default_instances`` and ``min_instances``
  parameters in scaling policy is specified as 0. If VNF requires VDU
  before the start of reservation, other VDU must be specified (like
  ``VDU_NO_RSV`` in the sample).

  Here is an example of VNFD including reservation triggered policies:

  .. code-block:: yaml

    :caption: Example VNFD with reservation policy
    tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
    description: VDU with a reserved resource
    node_templates:
      - VDU_RSV:
        type: tosca.node.nfv.VDU.Tacker
        properties:
          ...
          reservation_medata:
            resource_type: { get_input: physical_host }
            id: { get_input: reservation_id }
      - VDU_NO_RSV:
        type: tosca.node.nfv.VDU.Tacker
          ...

    policies:
      - RSV:
        type: tosca.policies.tacker.Reservation
        properties:
          lease_id: { get_input: lease_id }
          start_actions: [SP_RSV]
          before_end_actions: [SP_RSV]
          end_actions: noop
      - SP_RSV:
          type: tosca.policies.tacker.Scaling
          properties:
            increment: 5
            min_instances: 0
            max_instances: 5
            default_instances: 0
            targets: [VDU_RSV]

  The above reservation policy will be translated to Heat Orchestration
  Template as shown below.

  .. code-block:: yaml

   description: 'VNF TOSCA template with reservation_id input parameters
   parameters: {}
   resources:
     start_actions:
       type: OS::Aodh::EventAlarm
       properties:
         alarm_actions: ['http://hostname:9890/v1.0/vnfs/61b705ca-6dcc-4178-8402-bb4b85882760/start_actions/SP_RSV-out/eqmz4otj']
         event_type: lease.event.start_lease
         query:
         - {field: traits.lease_id, op: eq, value: 1933495b-0066-4243-aa48-d1fdd895fd5c}
     before_end_actions:
       type: OS::Aodh::EventAlarm
       properties:
         alarm_actions: ['http://hostname:9890/v1.0/vnfs/61b705ca-6dcc-4178-8402-bb4b85882760/before_end_actions/SP_RS-in/rfcz0v6y']
         event_type: lease.event.before_end_lease
         query:
         - {field: traits.lease_id, op: eq, value: 1933495b-0066-4243-aa48-d1fdd895fd5c}
     end_actions:
       type: OS::Aodh::EventAlarm
       properties:
         alarm_actions: ['http://hostname:9890/v1.0/vnfs/61b705ca-6dcc-4178-8402-bb4b85882760/end_actions/noop/eqmz4otj']
         event_type: lease.event.end_lease
         query:
         - {field: traits.lease_id, op: eq, value: 1933495b-0066-4243-aa48-d1fdd895fd5c}
     SP_RSV_scale_out:
       type: OS::Heat::ScalingPolicy
       properties:
         auto_scaling_group_id: {get_resource: SP_RSV_group}
         adjustment_type: change_in_capacity
         scaling_adjustment: 1
         cooldown: 120
     SP_RSV_group:
       type: OS::Heat::AutoScalingGroup
       properties:
         min_size: 1
         desired_capacity: 1
         cooldown: 120
         resource: {type: SP_RSV_res.yaml}
         max_size: 3
     SP_RSV_scale_in:
       type: OS::Heat::ScalingPolicy
       properties:
         auto_scaling_group_id: {get_resource: SP_RSV_group}
         adjustment_type: change_in_capacity
         scaling_adjustment: -1
         cooldown: 120

* Create and process alarms (tacker->heat->aodh->tacker)

  If policy ``tosca.policies.tacker.Reservation`` is specified in VNFD
  template, tacker will translate that policy to heat template which
  will create alarms in Aodh service. When Blazar trigger events
  ``start_lease``, ``before_end_lease`` and ``end_lease``, in the
  lifecycle of lease, these events will be received by Aodh service and
  then Aodh service will raise alarms which will be processed by Tacker
  service. We plan to re-use the existing ``AlarmReceiver`` middleware
  to process alarms for ``tosca.policies.tacker.Reservation`` policy.

  .. note::

    need to configure Ceilometer to enable event alarm
    [#ceilometer_event]_

Alternatives
------------

Another way to translate ``reservation_metadata`` property to
``schedular_hints.reservation`` or ``scheduler_hints.group`` is updating
heat-translator. However, ``reservation_metadata`` property in VDU is a stuff
of NFV and bringing such logic into heat-translator is not good way.

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
  nirajsingh <niraj.singh@nttdata.com>

Other contributors:
  Hiroyuki Jo <jo.hiroyuki@lab.ntt.co.jp>

Work Items
----------

* Add new property ``reservation_metadata`` to tosca.nodes.nfv.VDU.Tacker.
* Tosca Parser: Add a new policy type and properties like
  'start_actions', 'before_end_actions' and 'end_actions' used for
  reservation policy to parse tosca template.
* heat-translator: Translate ``tosca.policies.tacker.Reservation`` to Heat
  Orchestration Template.
* Write unit/functional test cases
* Add release and installation documentation

Dependencies
============

* Many changes are required to be done in projects other than tacker as
  listed in ``Work Items`` section to implement this feature.

Testing
=======

Add functional tests to test this feature. It will require you to create
a lease, create a vnfd template using lease id and reservation id,
create a vnf from vnfd template and finally check whether the alarms are
received against each of the events triggered by Blazar during the lifecycle
of the lease.

Documentation Impact
====================

* Add documentation to explain how to use reservation feature
* Update installation guide. Blazar, Aodh and Ceilometer services are
  required to use this feature.

References
==========
.. [#nfv-ifa010] http://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/010/02.03.01_60/gs_NFV-IFA010v020301p.pdf
.. [#usecase] http://specs.openstack.org/openstack/development-proposals/development-proposals/proposed/capacity-management.html#usage-scenarios-examples
.. [#blazar_wiki] https://wiki.openstack.org/wiki/Blazar/latest/
.. [#blazar_host] https://docs.openstack.org/blazar/latest/cli/host-reservation.html
.. [#blazar_instance] https://docs.openstack.org/blazar/latest/cli/instance-reservation.html
.. [#ceilometer_event] https://docs.openstack.org/aodh/latest/contributor/event-alarm.html
