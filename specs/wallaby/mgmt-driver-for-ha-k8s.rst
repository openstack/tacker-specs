=======================================================
Support HA Kubernetes Master deployment with MgmtDriver
=======================================================

https://blueprints.launchpad.net/tacker/+spec/mgmt-driver-for-ha-Kubernetes

This specification describes enhancement of HA operation for the VNF which
includes Kubernetes cluster.

Problem description
===================

The Kubernetes cluster can be deployed as a VNF instance, but in
high availability(HA) use cases, Master-nodes need to be composed of three or
more.
This spec enables to deploy a Kubernetes cluster with HA-Master-nodes.

Proposed change
===============

The Kubernetes cluster can be instantiated with VNF Lifecycle Management
Interface in ETSI NFV-SOL 003 [#SOL003]_.
According to ETSI NFV-SOL 001 [#SOL001]_, ``instantiate_end`` operation allows
users to setup their Kubernetes cluster with MgmtDriver support.
This spec extends the ``instantiate_end`` operation with MgmtDriver to deploy HA
Master-nodes.

In the HA configuration, the HAProxy that performs load balancing is deployed
in front of the multiple Master-nodes, and etcd is installed on each Master-node
to build an in-memory DB. If one Master-node fails, the etcd ensures service
continuity as a Kubernetes cluster by taking over synchronization information
stored in the in-memory DB running on the other Master-node.





The following changes are needed:

#. MgmtDriver supports the construction of an HA master node through the
   ``instantiate_end`` process as follows:

   + Identify the VMs created by OpenStackInfraDriver.
   + Invoke the script to configure for HAProxy to start signal
     distribution to Master nodes.
   + Install all Master-nodes first, followed by Worker-nodes by invoking the
     script setting up the new Kubernetes cluster.

#. Provide a sample script to be executed by MgmtDriver

   + To install the Kubernetes cluster for an HA configuration that requires
     information such as the IP address of the HAProxy as input.
   + To configure for HAProxy to start signal distribution to Master nodes.


.. note:: Regarding the configuration of HAProxy, it is assumed that HAProxy
          has a representative address of multiple Master-nodes, and all control
          signals for Kubernetes cluster from VNFM are distributed to each
          Master-node node via HAProxy. Since there is a concern that the HA
          Proxy may become a SPOF, it is preferable to adopt a redundant
          configuration of the HAProxy in combination with keepalived.

.. note:: HAProxy can be configured in two ways, one to deploy outside of a
          Master-node and the other to coexist within each Master-node. The
          diagram below shows the latter. Each HAProxy has a representative
          address as a VIP and is configured for signal distribution to each
          Master-node. It should be noted that the signal distribution settings
          for k8s-api and etcd are required. On the other hand, redundancy of
          HAProxy routes can be implemented by Virtual Router Redundancy
          Protocol (VRRP) and failure monitoring of HAProxy can be implemented
          by keepalived.

.. note:: Kubernetes v1.16.0 and Kubernetes python client v11.0 are supported
          for Kubernetes VIM.



The diagram below shows Kubernetes HA deployment operation:

.. code-block::

                                     +---------+ +---------+  +---------------+
                                     | Cluster | |         |  | Instantiation |
                                     | Install | |  VNFD   |  | Request with  |
                                     | Script  | |         |  | Additional    |
                                     +---------+ +---------+  | Params        |
                                          |           |       +---------------+
                                          |           v                   |
                                          |      +---------+              |
                                          |      |         |              |
                                          +----->|  CSAR   |------+       |
                                                 |         |      |       |
                                                 +---------+      |       |
                                                               +--|-------|----+
                                                               |  v       v    |
                                                               |+------------+ |
                                                               ||TackerServer| |
                                                               |+------+-----+ |
                                                               |       |       |
                                                               |       v       |
       3.Kubernetes Cluster                                    |+-------------+|
         Installation to all VMs                               ||+----------+ ||
           +-----------------------------------------------------|MgmtDriver| ||
           |                                                   ||+------+---+ ||
  +--------+------------------------------------+              ||       |     ||
  |        |                                    | 2.HAProxy    ||       |     ||
  |        |                                    | Configuration||       |     ||
  |        |         +--------------------------------------------------+     ||
  |        v         |                          |              ||             ||
  |+-----------------|----------+    +--------+ |              ||             ||
  ||                 v          |    |        | |              ||+-----------+||
  ||+---------+    +---------+  |    |        | | 1.Create VMs |||OpenStack  |||
  ||| VIP -   |    | HAProxy |  |    |        | |<---------------|InfraDriver|||
  |||  Active |--->| (Active)|----+  |        | |              |||           |||
  |||(keep-   |    +---------+  | |  |        | |              ||+-----------+||
  |||  alived)|    +---------+  | |  |        | |              ||             ||
  ||+---------+    | k8s-api |<---+  |        | |              ||             ||
  ||       ^       +---------+  | |  |        | |              ||             ||
  ||       |       +---------+  | |  |        | |              ||             ||
  ||  VRRP |    +->|  etcd   |  | |  |        | |              ||             ||
  ||       |    |  +---------+  | |  |Worker01| |              ||             ||
  ||       |    |   Master01 VM | |  |   VM   | |              ||             ||
  |+-------|--- | --------------+ |  +--------+ |              ||             ||
  |        |    |                 |             |              ||             ||
  |+-------|--- | --------------+ |  +--------+ |              ||             ||
  ||       v    |               | |  |        | |              ||             ||
  ||+---------+ |  +---------+  | |  |        | |              ||             ||
  ||| VIP -   | |  | HAProxy |  | |  |        | |              ||             ||
  |||  Standby| |  |(Standby)|  | |  |        | |              ||             ||
  |||(keep-   | |  +---------+  | |  |        | |              ||             ||
  |||  alived)| |  +---------+  | |  |        | |              ||             ||
  ||+---------+ |  | k8s-api |<---+  |        | |              ||             ||
  ||       ^    |  +---------+  | |  |        | |              ||             ||
  ||       |    |  +---------+  | |  |        | |              ||             ||
  ||  VRRP |    +->|  etcd   |  | |  |        | |              ||             ||
  ||       |    |  +---------+  | |  |Worker02| |              ||             ||
  ||       |    |   Master02 VM | |  |   VM   | |              ||             ||
  |+-------|--- | --------------+ |  +--------+ |              ||             ||
  |        |    |                 |             |              ||             ||
  |+-------|--- | --------------+ |  +--------+ |              ||             ||
  ||       v    |               | |  |        | |              ||             ||
  ||+---------+ |  +---------+  | |  |        | |              ||             ||
  ||| VIP -   | |  | HAProxy |  | |  |        | |              ||             ||
  |||  Standby| |  |(Standby)|  | |  |        | |              ||             ||
  |||(keep-   | |  +---------+  | |  |        | |              ||             ||
  |||  alived)| |  +---------+  | |  |        | |              ||             ||
  ||+---------+ |  | k8s-api |<---+  |        | |              ||             ||
  ||            |  +---------+  |    |        | |              ||             ||
  ||            |  +---------+  |    |        | |              ||             ||
  ||            +->|  etcd   |  |    |        | |              ||             ||
  ||               +---------+  |    |Worker03| |              ||             ||
  ||                Master03 VM |    |   VM   | |              ||             ||
  |+----------------------------+    +--------+ |              ||  Tacker     ||
  +---------------------------------------------+              ||  Conductor  ||
  +---------------------------------------------+              |+-------------+|
  |             Hardware Resources              |              |     VNFM      |
  +---------------------------------------------+              +---------------+


The diagram shows related component of this spec proposal and an overview of
the following processing:

#. OpenStackInfraDriver creates the VMs.
#. MgmtDriver invokes the script to configure the HAProxy.
#. MgmtDriver constructs of an HA Kubernetes cluster in ``instantiate_end``.

   #. MgmtDriver uses a shell script to install Kubernetes on multiple Master
      and Worker nodes.

.. note:: In this configuration, because the HA Proxy lives in the Master-node,
          you must configure the ports separately to avoid conflicts between the
          receiving ports on the k8s-api and the receiving ports on the
          HAProxy side.



VNFD for Kubernetes HA deployment operation
-------------------------------------------

VNFD needs to have ``instantiate_end`` definition as the following sample:

.. code-block::

  node_templates:
    VNF:
      ...
      interfaces:
        Vnflcm:
          instantiate: []
          instantiate_start: []
          instantiate_end:
            implementation: mgmt-drivers-kubernetes
      artifacts:
        mgmt-drivers-kubernetes:
          description: Management driver for Kubernetes cluster
          type: tosca.artifacts.Implementation.Python
          file: /.../mgmt_drivers/kubernetes_mgmt.py]

    masterNode:
      type: tosca.nodes.nfv.Vdu.Compute
      properties:
        name: masterNode
        description: masterNode
        vdu_profile:
          min_number_of_instances: 3
          max_number_of_instances: 3

    workerNode:
      type: tosca.nodes.nfv.Vdu.Compute
      properties:
        name: workerNode
        description: workerNode
        vdu_profile:
          min_number_of_instances: 1
          max_number_of_instances: 3


This specification assumes that the number of min_number_of_instances for the
Master-node must be set to a value greater than or equal to 3.



.. note:: Example of /etc/keepalived/keepalived.conf
          By changing ``priority``, change the order of activation when a
          failure occurs.

          Master-node01

          .. code-block::

            vrrp_script chk_haproxy {
                script "killall -0 haproxy"
                interval 3 fall 3
            }
            vrrp_instance VRRP1 {
                state MASTER
                interface enp0s3
                virtual_router_id 123
                priority 103
                advert_int 1
                virtual_ipaddress {
                    192.168.128.80/24
                }
                track_script {
                    chk_haproxy
                }
            }

          Master-node02

          .. code-block::

            vrrp_script chk_haproxy {
                script "killall -0 haproxy"
                interval 3 fall 3
            }
            vrrp_instance VRRP1 {
                state BACKUP
                interface enp0s3
                virtual_router_id 123
                priority 102
                advert_int 1
                virtual_ipaddress {
                    192.168.128.80/24
                }
                track_script {
                    chk_haproxy
                }
            }



          Master-node03

          .. code-block::

            vrrp_script chk_haproxy {
                script "killall -0 haproxy"
                interval 3 fall 3
            }
            vrrp_instance VRRP1 {
                state BACKUP
                interface enp0s3
                virtual_router_id 123
                priority 101
                advert_int 1
                virtual_ipaddress {
                    192.168.128.80/24
                }
                track_script {
                    chk_haproxy
                }
            }


.. note:: Example of /etc/haproxy/haproxy.cfg
          The following is an example of SSL pass-through setting.

          .. code-block::

            frontend k8s-api
                bind *:6440
                mode tcp
                default_backend    k8s-api

            backend k8s-api
                balance   roundrobin
                mode      tcp
                server    master1  master01:6443  check
                server    master2  master02:6443  check  backup
                server    master3  master03:6443  check  backup




Request data for Kubernetes HA deployment operation
---------------------------------------------------

Below is a sample of body provided in the VNF instantiation request
`POST /vnflcm/v1/vnf_instances/{vnfInstanceId}/instantiate`

.. code-block:: json

  {
    "flavourId": "cluster_install",
    "additionalParams": {
      "input_params":""
    },
    "vimConnectionInfo": [
      {
        "id": "8a3adb69-0784-43c7-833e-aab0b6ab4470",
        "vimId": "7dc3c839-bf15-45ac-8dff-fc5b95c2940e",
        "vimType": "openstack"
      }
    ]
  }


Sequence diagram
----------------

Following sequence diagram describes the components involved and the flow of
HA Kubernetes Master deployment in ``instantiate_end``:

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "OpenstackDriver"
    "Heat"
    "MgmtDriver"
    "RemoteCommandExecutor"

    Client -> "Tacker-server"
      [label = "instantiate VNF"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];

    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];

    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "instantiate VNF"];

    "VnfLcmDriver" -> "OpenstackDriver"
      [label = "pre instantiate VNF"];
    "VnfLcmDriver" <-- "OpenstackDriver"
      [label = ""];

    "VnfLcmDriver" -> "OpenstackDriver"
      [label = "instantiate VNF"];

    "OpenstackDriver" -> "Heat"
      [label = "create stack"];
    "OpenstackDriver" <-- "Heat"
      [label = ""];

    "VnfLcmDriver" <-- "OpenstackDriver"
      [label = "return stack id"];

    "VnfLcmDriver" -> "VnfLcmDriver"
      [label = "update DB"];

    "VnfLcmDriver" -> "MgmtDriver"
      [label = "instantiate_end"];

    "MgmtDriver" -> "Heat"
      [label = "get the new vm info created."];
    "MgmtDriver" <-- "Heat"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Changes HAProxy configuration"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Install Kubernetes on the new Master-node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Install Kubernetes on the new Worker-node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];

    "VnfLcmDriver" <-- "MgmtDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }

The procedure consists of the following steps as illustrated in above sequence.
The following No.3 and later processes are executed as ``instantiate_end``.

#. Client sends a POST request to the Instantiate VNF.
#. Basically the same sequence as described in the "2) Flow of Instantiation of
   a VNF instance" chapter of spec `etsi-nfv-sol-rest-api-for-VNF-deployment`_,
   except for the MgmtDriver.

   .. note:: Heat templates contain resource information for VM instantiation.
             This specification assumes that the number of redundant VMs for the
             Master node is specified in the variable "desired_capacity".
             This variable must be set to a value greater than or equal to 3.

#. MgmtDriver gets new VM information from Heat.
#. MgmtDriver changes HAProxy configuration by invoking shell script using
   RemoteCommandExecutor.
#. MgmtDriver repeats the setup of the Master-node and Worker-node for the
   number of newly created VMs by invoking shell script using
   RemoteCommandExecutor.

Alternatives
------------

As an alternative, HA Proxy can be configured in another VM other than the
Master-node VM. However the number of deployed VM increases and it may lead
poor resource effectiveness.


The diagram below shows the operation with the alternative:

.. code-block::

                                     +---------+ +---------+  +---------------+
                                     | Cluster | |         |  | Instantiation |
                                     | Install | |  VNFD   |  | Request with  |
                                     | Script  | |         |  | Additional    |
                                     +---------+ +---------+  | Params        |
                                          |           |        +---------------+
                                          |           v                   |
                                          |      +---------+              |
                                          |      |         |              |
                                          +----->|  CSAR   |------+       |
                                                 |         |      |       |
                                                 +---------+      |       |
                                                               +--|-------|----+
                                                               |  v       v    |
                                                               |+------------+ |
                                                               ||TackerServer| |
                                                               |+------+-----+ |
                                                               |       |       |
                                                               |       v       |
           3.Kubernetes Cluster                                |+-------------+|
             Installation to Master-nodes and Worker-nodes     ||+----------+ ||
           +-----------------------------------------------------|MgmtDriver| ||
           |                                                   ||+------+---+ ||
  +--------+------------------------------------+              ||       |     ||
  |        |          +------------------------+|              ||       |     ||
  |        |          |                        ||              ||       |     ||
  |        |          |+---------+  +---------+|| 2.HAProxy    ||       |     ||
  |        |          || HAProxy |  | VIP -   ||| Configuration||       |     ||
  |        |       +---|(Active) |<-|  Active |<------------------------+     ||
  |        |       |  ||         |  |(keep-   |||              ||             ||
  |        |       |  ||         |  |  alived)|||              ||+-----------+||
  |        |       |  |+---------+  +---------+|| 1.Create VMs |||OpenStack  |||
  |        |       |  |                    ^   ||<---------------|InfraDriver|||
  |        |       |  |     HAProxy01 VM   |   ||              |||           |||
  |        |       |  +--------------------|---+|              ||+-----------+||
  |        |       |                  VRRP |    |              ||             ||
  |        |       |  +--------------------|---+|              ||             ||
  |        |       |  |                    v   ||              ||             ||
  |        |       |  |+---------+  +---------+||              ||             ||
  |        |       |  || HAProxy |  | VIP -   |||              ||             ||
  |        |       |  ||(Standby)|  |  Standby|||              ||             ||
  |        |       |  ||         |  |(keep-   |||              ||             ||
  |        |       |  ||         |  |  alived)|||              ||             ||
  |        |       |  |+---------+  +---------+||              ||             ||
  |        |       |  |     HAProxy02 VM       ||              ||             ||
  |        v       |  +------------------------+|              ||             ||
  |+-------------+ |  +--------+                |              ||             ||
  ||+---------+  | |  |        |                |              ||             ||
  ||| k8s-api |<---+  |        |                |              ||             ||
  ||+---------+  | |  |        |                |              ||             ||
  ||+---------+  | |  |        |                |              ||             ||
  |||  etcd   |<----+ |        |                |              ||             ||
  ||+---------+  | || |Worker01|                |              ||             ||
  || Master01 VM | || |   VM   |                |              ||             ||
  |+-------------+ || +--------+                |              ||             ||
  |                ||                           |              ||             ||
  |+-------------+ || +--------+                |              ||             ||
  ||+---------+  | || |        |                |              ||             ||
  ||| k8s-api |<---+| |        |                |              ||             ||
  ||+---------+  | || |        |                |              ||             ||
  ||+---------+  | || |        |                |              ||             ||
  |||  etcd   |<----+ |        |                |              ||             ||
  ||+---------+  | || |Worker02|                |              ||             ||
  || Master02 VM | || |   VM   |                |              ||             ||
  |+-------------+ || +--------+                |              ||             ||
  |                ||                           |              ||             ||
  |+-------------+ || +--------+                |              ||             ||
  ||+---------+  | || |        |                |              ||             ||
  ||| k8s-api |<---+| |        |                |              ||             ||
  ||+---------+  |  | |        |                |              ||             ||
  ||+---------+  |  | |        |                |              ||             ||
  |||  etcd   |<----+ |        |                |              ||             ||
  ||+---------+  |    |Worker03|                |              ||             ||
  || Master03 VM |    |   VM   |                |              ||             ||
  |+-------------+    +--------+                |              ||  Tacker     ||
  +---------------------------------------------+              ||  Conductor  ||
  +---------------------------------------------+              |+-------------+|
  |             Hardware Resources              |              |     VNFM      |
  +---------------------------------------------+              +---------------+


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
  Yoshito Ito <yoshito.itou.dr@hco.ntt.co.jp>

Other contributors:
  Shotaro Banno <banno.shotaro@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  Liang Lu <lu.liang@fujitsu.com>

Work Items
----------
+ MgmtDriver will be modified to implement:

  + Support the construction of HA Master-nodes in "instantiate_end".

  + Provide a sample script to be executed by MgmtDriver to install and/or
    configure Kubernetes cluster and HAProxy.

+ Add new unit and functional tests.

Dependencies
============


``instantiate_end`` referred in "Proposed change" is based on the spec of
`mgmt-driver-for-k8s-cluster`_.


Testing
=======
Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================
Complete user guide will be added to explain how to build Kubernetes HA from the
perspective of VNF LCM APIs.

References
==========
.. [#SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/
.. [#SOL001] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/
.. _mgmt-driver-for-k8s-cluster:
  ./mgmt-driver-for-k8s-cluster.html
.. _flow-of-instantiation-of-a-vnf-instance:
  https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol
  -rest-api-for-VNF-deployment.html#flow-of-instantiation-of-a-vnf-instance
.. _etsi-nfv-sol-rest-api-for-VNF-deployment:
  https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol-rest-api-for-VNF-deployment.html
