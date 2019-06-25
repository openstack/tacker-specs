..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


======================================================
Adding Multi-Interface for Containerized VNF in Tacker
======================================================

https://blueprints.launchpad.net/tacker/+spec/multi-interface-container

Problem description
===================

Currently, Tacker provides container-based VNF [#first]_,[#third]_.
Current Kuryr-Kubernetes support multiple interfaces.
However, when creating a C-VNF using a VNFD template in
the tacker, it provides only a single interface.
Therefore, it has a limitation to use C-VNF as a Network Function.
this proposal suggests providing the multi network interfaces on a container
using Kuryr-Kubernetes based 'npwg_multiple_interfaces' [#second]_.

Proposed change
===============
Currently, the template used to create C-VNF in Tacker is as follows.


.. code-block:: yaml

    VDU1:
      type: tosca.nodes.nfv.VDU.Tacker
      properties:
        namespace: default
        mapping_ports:
          - "80:8080"
          - "443:443"
        labels:
          - "app: webserver"
        service_type: ClusterIP
        vnfcs:
          web_server:
            properties:
              num_cpus: 0.5
              mem_size: 512 MB
              image: celebdor/kuryr-demo
              ports:
                - "8080"
              config: |
                param0: key1
                param1: key2

This format allows the creation of C-VNFs. However, in order to use
multi-interface, annotation part should be available like below.

.. code-block:: console

  metadata:
    name: my-pod
    namespace: my-namespace
    annotations:
      k8s.v1.cni.cncf.io/networks: net-a,net-b,other-ns/net-c


Therefore, in this specification, we want to add functionality to the
translator so that we can use multi-interface feature mentioned above
when deploying C-VNF.


1. Definition of ToscaKubeObject:

ToscaKubeObject holds the basic struct of a VDU.
That is used for translating TOSCA to Kubernetes templates such as Service,
Deployment, Horizon Pod Autoscaling, ConfigMap. In this specification,
we use VL section for multi interface. When user defines VL more than one,
it makes to provide multiple interface for C-VNF.

Example of an VNFD in Tacker:

.. code-block:: yaml

    VDU1:
      type: tosca.nodes.nfv.VDU.Tacker
      properties:
        namespace: default
        mapping_ports:
          - "80:8080"
          - "443:443"
        labels:
          - "app: webserver"
        service_type: ClusterIP
        vnfcs:
          web_server:
            properties:
              num_cpus: 0.5
              mem_size: 512 MB
              image: celebdor/kuryr-demo
              ports:
                - "8080"
              config: |
                param0: key1
                param1: key2
    VL1:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net-a
        vendor: Tacker

    VL2:
      type: tosca.nodes.nfv.VL
      properties:
        network_name: net-b
        vendor: Tacker


Basically, this specification follows previous containerized VNF
specification [#third]_. To support multi-interface, we use
VL section and network name.

* network_name: network of VDU, for pure Kubernetes, it is used when enable
                neutron network with Kuryr-Kubernetes.
                When user define virtual link more than one, user can use
                multi-interface network in the C-VNF.

When user define virtual link more than one, kubernetes translator get the network
information from network_name. These information is used to make a
kubernetes template which used to create POD with multi interface.

To support this function, kubernetes translator of Tacker should be
changed to create multiple-interface using VL information.

Alternatives
------------


Data model impact
-----------------


REST API impact
---------------



Security impact
---------------

Notifications impact
--------------------

Other end user impact
---------------------

Performance Impact
------------------

Other deployer impact
---------------------

Developer impact
----------------

Implementation
==============
To implement this spec, we modify Kubernetes translator which used for C-VNF.
Modification part will provide multi-interface using VL information which is
defined in the TOSCA template.

Assignee(s)
-----------

Primary assignee:
  Hyunsik Yang <yangun@dcn.ssu.ac.kr>

Work Items
----------

1. Implement translator to translate from TOSCA to k8s template for multi-interface

Dependencies
============

Kuryr-Kubenetes python library

Testing
=======

Unit testing
Functional testing

Documentation Impact
====================

Yes. We have to describe how to use multi-interface in containerized VNF's

References
==========
.. [#first] https://kubernetes.io/
.. [#second] https://docs.openstack.org/kuryr-kubernetes/latest/specs/rocky/npwg_spec_support.html
.. [#third] https://specs.openstack.org/openstack/tacker-specs/specs/queens/kubernetes-type-for-containerized-VNF.html
