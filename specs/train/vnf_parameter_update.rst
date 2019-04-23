..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


===============================
enable updating VNF parameters
===============================

https://blueprints.launchpad.net/tacker/+spec/reservation-vnfm

This proposal aims at supporting to update parameters of created VNF.

Problem description
===================

Current Tacker supports updating only `config` attribute of VNFs
[#VNF_update]_ and does not support updating `param_values` of VNFs. So,
operators have to re-create the VNF if they want to update parameters.
This spec enables updating the parameters without a VNF re-creation.

Use case
--------

For example, some VNFs are deployed with a different priority on the
limited infra resources and scale-up of the higher priority VNF will
be expected due to increased demand in certain periods for upcoming
events like concerts, festivals or sport games. Operators of higher
priority VNF need to reserve resources for their VNF so that the
required resources aren't consumed by other VNFs.

The resource reservation function that current Tacker supports
[#VNF_reservation]_ enables extending resources during the certain
periods by applying a reservation-id that was issued at reserving the
resource to the VNF. Operators need to update the reservation-id because
such a large-scale event usually occurs multiple times. Operators can
prepare for such events without re-creating VNFs by introducing this
parameter updating function.

Proposed change
===============

* Enabling to update parameter in vnf update.

Adding a new parameter `--param-file` to openstack vnf set command.

.. code-block:: console

  openstack vnf set --param-file PARAM-FILE <VNF>

`parameters` here means inputs parameters in VNFDs. So users have to
parameterize what they want to update later in their VNFDs before
creating VNFs.  For example, the parameters include flavor, image,
network, etc. like below.  The detail is described in
[#VNFD_parameterization]_.

.. code-block:: yaml

  :caption: Example Parameterized VNFD
  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

  description: VNF TOSCA template with input parameters

  metadata:
    template_name: sample-tosca-vnfd

  topology_template:
    inputs:
      image_name:
        type: string
        description: Image Name

      flavor:
        type: string
        description: Flavor Information

      network:
        type: string
        description: management network

    node_templates:
      VDU1:
        type: tosca.nodes.nfv.VDU.Tacker
        properties:
          image: {get_input: image_name}
          flavor: {get_input: flavor}
          availability_zone: nova
          ...

      VL1:
        type: tosca.nodes.nfv.VL
        properties:
          network_name: {get_input: network}
          vendor: Tacker
          ...

Updated values of parameters are described in parameter file.

.. code-block:: yaml

  :caption: Example parameter file
  image_name: cirros-0.4.0-x86_64-disk
  flavor: m1.tiny
  network: net_mgmt

* internal updating procedure

When parameter update, Tacker issues Heat stack update with setting True
to existing flag to keep stack resources which do not consist updating
parameter.  It depends on the updated property if parameter updating
brings re-creation of the stack resource or not. For example, updating
`image` property of OS::Nova::Server resource type causes replacement of
its VM but `name` property doesn't. The detail is described in
[#HOT_guide]_ [#update_stack_api]_ .

.. code-block:: python

        # run stack update
        stack_update_param = {
        'parameters': update_values,
        'existing': True}
    heatclient.update(vnf_id, **stack_update_param)

* miscellaneous error handling

Users can use either config or parameter file, but not both at the
same time. It's because updating config may fail if VM re-creation
occurs by updating parameter.

.. code-block:: python

    class UpdateVNF(command.ShowOne):
        _description = _("Update a given VNF.")

        def get_parser(self, prog_name):
            parser = super(UpdateVNF, self).get_parser(prog_name)
            group = parser.add_mutually_exclusive_group(required=True)
            group.add_argument(
                '--config-file',
                help=_('YAML file with VNF configuration'))
            group.add_argument(
                '--config',
                help=_('Specify config YAML data'))
            group.add_argument(
                '--param-file',
                help=_('Specify parameter yaml file'))
            parser.add_argument(
                _VNF,
                metavar="<VNF>",
                help=_("VNF to update (name or ID)"))
            return parser

.. code-block:: console

  :caption: Example error message
  openstack vnf set --param-file PARAM-FILE --config CONFIG <VNF>
  openstack vnf set: error: argument --config: not allowed with argument --param-file

If there is no difference between parameter values that are passed by
vnf set command and current, Tacker cancels updating parameters with
warning messages. It prevents unnecessary updating processes.

.. code-block:: python

        # check update values
        update_values = {}
        for key, value in update_param_dict.items():
            if update_param_dict[key] != param_dict[key]:
                update_values[key] = value
        if not update_values:
            raise vnfm.VNFUpdateInvalidInput(
                reason="WARNING: parameter is same value")

.. code-block:: console

  :caption: Example warning message
  openstack vnf set --param-file PARAM-FILE <VNF>
  WARNING: parameter is same value

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

Adding "param_values" to "Request Parameters" of Update VNF API.

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
  Hiroyuki Jo <jo.hiroyuki@lab.ntt.co.jp>

Work Items
----------

* Adding "param-file" argument to vnf set command in python-tackerclient.
* Adding a function to get the difference between existing parameter and new parameter to Tacker.
* Adding a function to call stack update with new parameter to Tacker
* Unit Tests
* Functional Tests
* Update documentation

Dependencies
============

None

Testing
=======

Unit and functional test cases will be added for updating VNF by applying new parameter to existing VNF

Documentation Impact
====================

Adding "Updating VNF" to tacker/doc/source/user/vnfm_usage_guide.rst

References
==========
.. [#VNF_update] https://developer.openstack.org/api-ref/nfv-orchestration/v1/index.html?expanded=update-vnf-detail#update-vnf
.. [#VNF_reservation] https://docs.openstack.org/tacker/latest/reference/reservation_policy_usage_guide.html
.. [#VNFD_parameterization] https://docs.openstack.org/tacker/latest/contributor/vnfd_template_parameterization.html
.. [#HOT_guide] https://docs.openstack.org/heat/latest/template_guide/openstack.html
.. [#update_stack_api] https://developer.openstack.org/api-ref/orchestration/v1/#update-stack
