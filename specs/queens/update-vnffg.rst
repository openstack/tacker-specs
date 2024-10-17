..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Update VNFFG's Chain and Classifier
==========================================

https://blueprints.launchpad.net/tacker/+spec/update-vnffg

This spec describes the plan to implement the functionality for the update
of a forwarding graph or a classifier through an already created VNFFG.

Problem description
===================

Currently in Tacker there is already implemented the functionality to succesfully create
and delete forwarding graphs and classifiers through the introduced VNFFG concept.
To be more specific the user has the capability to describe the forwarding graph of VNFs and
the classification criteria to a VNFFG template and during the creation time of the VNFFG,
Tacker through the networking-sfc driver will create the actual classification rules
where the traffic will be matched and the actual forwarding graph where the traffic will be forwarded to.

The problem occurs when the user is interested to update the already created VNFFG.
Tacker currently has no actual implementation of updating a forwarding graph or a classifier through
its networking-sfc driver.

The goal here is to implement the necessary functionality in the Tacker
server and the Tacker client side so the user has the capability to update
succesfully an already created VNFFG which means that he will be capable of
updating the VNFs of a forwarding graph, add or delete VNFs to an existing forwarding graph
and updating the classifier criteria which correspond to an already created VNFFG.


Proposed change
===============

To address the problem that was described above we need to introduce several
changes not only in the Tacker server side but also in the Tacker client side.

Changes include:

* Add extra parameters to the python-tackerclient vnffg-update command so we can
  be able to update the VNFs which are part of the forwarding graph, add or delete
  VNFs in the already created VNFFG and also update the classifier's criteria which
  are described in that VNFFG.

* Specific changes also required by the NFVO plugin in the tacker server side
  where is located the core functionality for the update of a VNFFG.
  To be more specific the user should be able to update the classifier's criteria
  or the VNFs in a forwarding graph or the classifier's criteria and the VNFs in a
  forwarding graph simultaneously. This means that we should run some validation checks for the
  data that the user passes in. Checks like that could be that the criteria do
  not already exist in the database or that the VNFs that the user passes in the
  update command are not already used in the forwarding graph and they are VNFs which
  are already created in the past. In addition to that we need to update the items
  which are located in the database. This means that we need to replace in an existing
  classifier the old criteria with the new ones or create a new classifier in case
  the criteria that the user passes in the update command are new. Also we need to
  update the forwarding graph by replacing the old VNFs with the new ones which are passed to
  the vnf-mapping parameter.
  Furthermore we need to be able to add and delete VNFs to and from
  the forwarding graph when the user uses the parameter which corresponds to the addition
  or deletion of VNFs in an already created VNFFG.
  To keep the things simple here we should allow the addition of a VNF to the forwarding graph
  only when this VNF is derived from a VNFD which is not already used in the
  existing forwarding graph.
  As an additional step we should update the items of the already created VNFFGD template
  when we update the forwarding graph or the criteria though Tacker client. For instance
  we should update the constituent_vnfs item when we add or delete VNFDs to the forwarding graph.
  Finally we need to update also the state of all the items in the database when the
  whole procedure comes to an end.

* As a final step we need to implement the functionality for the update of
  the forwarding graph and the classifier in the networking-sfc driver which is located in the
  tacker server side. The networking-sfc driver is the Tacker component which
  interacts with the networking-sfc openstack component and is responsible to
  forward the calls to the networking-sfc API.
  To be more specific when the user wants to update an existing classifier by adding
  another one or update the criteria of an existing one the procedure which should be
  followed is first to clear the chain from the existing classifiers which are associated
  with it, after that delete the old classifier and create a new one which contains the old
  criteria and the updated ones and also create a new classifier because the user wants to add
  a new classifier to the chain too. As final step we need to reassign the classifiers to the
  existing forwarding graph. We should follow this procedure because the networking-sfc API doesn't
  support the update of the criteria of an existing classifier on the fly, which means that if we
  want to update an existing classifier we need to delete it first and create a new one, which
  contains the old and the new criteria.
  If the user wants to replace the VNFs in an existing forwarding graph we need first to strip the chain
  from its port-pair-groups create a new port-pair and a new port-pair-group for the new VNF,
  delete the port-pair and the port-pair-group of the replaced VNF and reassign all the
  port-pair-groups to the chain.
  Finally if the user wants to add or delete a VNF to or from the forwarding graph we need again to
  strip the existing chain from its port-pair-groups create or delete a port-pair-group for the new
  or the removed VNF and reassign the VNFs to the chain.

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

End user impact
===============

Tacker client changes
---------------------

There will be changes to python-tackerclient for the end user in order to be able to
update an existing VNFFG. Parameter "--vnffgd-file" will be added in tacker command.

Example CLI calls:

.. code-block:: console

   tacker vnffg-update --vnffgd-file vnffgd-template.yml <already created VNFFG name>

User can use vnffg-template file to update criteria of flowclassifier and path in VNFFG.
The value of the --vnffgd-file parameter is vnffgd-template.yaml where user can pass
information which will contain the criteria that the updated classifier will have and
the new path of VNFFG.



**Tacker will support 2 types of updating VNFFG:**

1. Update criteria of flowclassifier
2. Update the path

A vnffgd-template.yaml, which is the orginal vnffgd-file to create vnffgd, user can add, delete
or change criteria of flowclassifiers and path.

Example, user can add the second criteria in vnffgd-template.yaml (add new criteria to connect
port 443 in destination server) or add new VNF3 to the path. Then run "tacker update" to update
the created VNFFG.

.. code-block:: yaml

  tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

  description: Sample VNFFG template

  topology_template:
    description: Sample VNFFG template

    node_templates:
      Forwarding_path1:
        type: tosca.nodes.nfv.FP.Tacker
        description: creates path (CP12->CP22)
        properties:
          id: 51
          policy:
            type: ACL
            criteria:
              - network_src_port_id: 640dfd77-c92b-45a3-b8fc-22712de480e1
                destination_port_range: 80
                ip_proto: 6
                ip_dst_prefix: 192.168.1.2/24
              - network_src_port_id: 640dfd77-c92b-45a3-b8fc-22712de480e1
                destination_port_range: 443
                ip_proto: 6
                ip_dst_prefix: 192.168.1.2/24
          path:
            - forwarder: VNFD1
              capability: CP12
            - forwarder: VNFD2
              capability: CP22
            - forwarder: VNFD3
              capability: CP32
    groups:
      VNFFG1:
        type: tosca.groups.nfv.VNFFG
        description: HTTP to Corporate Net
        properties:
          vendor: tacker
          version: 1.0
          number_of_endpoints: 3
          dependent_virtual_link: [VL12,VL22,VL32]
          connection_point: [CP12,CP22,CP32]
          constituent_vnfs: [VNFD1,VNFD2,VNFD3]
        members: [Forwarding_path1]

Tacker server processes changes
-------------------------------

Processes when updating vnffg:

1. When first time VNFFG is updated

Tacker will create a new vnffgd (with template_source is inline) from
vnffgd-template.yml file which user provide in tacker update command.

2. Compare changes in new vnffgd and the original

Tacker will run update chain, flowclassifiers, new path if there are changes.
Tacker also update vnffgd_id in vnffgs database to the id of new vnffgd.

3. If VNFFG is updated more than one time

If the last vnffgd has template_source is onboarded, Tacker keeps vnffgd
because it is the original. Tacker will delete the last vnffgd if
its template_source is in-line.

Performance Impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

None

Alternatives
============

The addition of the --criteria-add, --criteria-delete parameters can passed to
tacker client command so user can be capable to add, delete the criteria of
classifiers in an already created VNFFG.

Example CLI calls:

.. code-block:: console

     tacker vnffg-update
         --criteria-add {ip_protol:6, neutron_src_port:<neutron port id>, etc}
         --forwarding-path Forwarding_path1
         <already created VNFFG name>

     tacker vnffg-update
         --criteria-delete {ip_protol:6, neutron_src_port:<neutron port id>, etc}
         --forwarding-path Forwarding_path1
         <already created VNFFG name>

In the future, Tacker will support update VNFFG use parameters beside using
vnffgd-template.yml file.

Implementation
==============

Assignee(s)
-----------

Primary assignee
  Dimitrios Markou <mardim@intracom-telecom.com>

Other contributors:
  Hoang Phuoc <phuoc.hc@dcn.ssu.ac.kr>

Work Items
----------

1. Extend update-vnffg functionality to the Tacker server NFVO plugin
2. Implement the update functionality in the networking-sfc driver in
   the Tacker server side.
3. Modify the update vnffg command in the Tacker client side.
4. Add unit and functional tests.

Dependencies
============

The update-vnffg functionality is dependent on networking-sfc being able to
update SFCs and classifiers. For more information check [#first]_ .

Testing
=======

The testing of the VNFFG update functionality can be addressed by the OPNFV/SFC
project.


Documentation Impact
====================

Extend the API docs to include the new parameter of the python-tackerclient
regarding the classifier criteria update.

References
==========

.. [#first] https://opendev.org/openstack/networking-sfc/src/branch/master/doc/api_samples
