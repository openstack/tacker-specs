==============================================================
Support Healing Kubernetes Master/Worker-nodes with Mgmtdriver
==============================================================

https://blueprints.launchpad.net/tacker/+spec/mgmt-driver-for-k8s-heal

This specification describes enhancement of Heal operation for the VNF which
includes Kubernetes cluster.

Problem description
===================
The ETSI-compliant VNF Heal operation has been implemented in ``Ussuri``
release and updated to support Notification and Grant operations in
``Victoria`` release. For the use case with OS container based VNF with
Kubernetes cluster, it's important to support the cluster management. In this
spec, we propose the Heal operation for Kubernetes Master or Worker-nodes
when the VNF is composed of Kubernetes cluster with the spec
`mgmt-driver-for-k8s-cluster`_.

To support healing Kubernetes cluster nodes, MgmtDriver needs to be extended.
After deploying a Kubernetes cluster using MgmtDriver as the VNF Lifecycle
Management interface with ETSI NFV-SOL 003 [#SOL003]_, the heal related
operations are required.
When healing a Master or Worker-node, you need not only the default Heal
operation, but also the ``heal_end`` operation to register the node to an
existing Kubernetes cluster.
If you want to heal a Master-node, you need to configure etcd and HA proxy.
Also, when healing a Worker-node, you need to apply the required configuration
and to make it to leave and join the cluster with the same way in scale-in
and scale-out.

Proposed change
===============

The two patterns of Heal operations are supported:

#. Heal a single node (Master / Worker) in Kubernetes cluster
   based on ETSI NFV-SOL002 [#SOL002]_.

   + Heal Master-node of Kubernetes cluster

     Delete a failed Master-node, create a new VM, and incorporate a new
     Master-node into the existing Kubernetes cluster. The etcd cluster and
     the load balancer configured as a Master-node are also repaired by
     MgmtDriver.

   + Heal Worker-node of Kubernetes cluster

     Delete the failed Worker-node, create a new VM, and incorporate the new
     Worker-node into the existing Kubernetes cluster.

#. Heal the entire Kubernetes cluster based on ETSI NFV-SOL003 [#SOL003]_.

.. note:: The Healing of the Pods in the Kubernetes cluster is
          out of scope of this specification.

.. note:: Failure detection is also out of scope.
          It is assumed that the user performs a Heal operation to the known
          node being failed.

.. note:: Kubernetes v1.16.0 and Kubernetes python client v11.0 are supported
          for Kubernetes VIM.



VNFD for Healing operation
--------------------------

VNFD needs to have ``heal_start`` and ``heal_end`` definitions in interfaces
as the following sample:

.. code-block:: yaml

  node_templates:
    VNF:
      ...
      interfaces:
        Vnflcm:
          ...
          heal_start:
            implementation: mgmt-drivers-kubernetes
          heal_end:
            implementation: mgmt-drivers-kubernetes
      artifacts:
        mgmt-drivers-kubernetes:
          description: Management driver for kubernetes cluster
          type: tosca.artifacts.Implementation.Python
          file: /.../mgmt_drivers/kubernetes_mgmt.py

    MasterVDU:
      type: tosca.nodes.nfv.Vdu.Compute
      ...

    WorkerVDU:
      type: tosca.nodes.nfv.Vdu.Compute
      ...


Request data for Healing operation
----------------------------------

User gives following heal parameter to "POST /vnf_instances/{id}/heal" as
``HealVnfRequest`` data type. It is not the same in SOL002 and SOL003.

In ETSI NFV-SOL002 v2.6.1 [#SOL002]_:


  +------------------+---------------------------------------------------------+
  | Attribute name   | Parameter description                                   |
  +==================+=========================================================+
  | vnfcInstanceId   | User specify heal target, user can know "vnfcInstanceId"|
  |                  | by ``InstantiatedVnfInfo.vnfcResourceInfo`` that        |
  |                  | contained in the response of "GET /vnf_instances/{id}". |
  +------------------+---------------------------------------------------------+
  | cause            | Not needed                                              |
  +------------------+---------------------------------------------------------+
  | additionalParams | Not needed                                              |
  +------------------+---------------------------------------------------------+
  | healScript       | Not needed                                              |
  +------------------+---------------------------------------------------------+

In ETSI NFV-SOL003 v2.6.1 [#SOL003]_:


  +------------------+---------------------------------------------------------+
  | Attribute name   | Parameter description                                   |
  +==================+=========================================================+
  | cause            | Not needed                                              |
  +------------------+---------------------------------------------------------+
  | additionalParams | Not needed                                              |
  +------------------+---------------------------------------------------------+


Tacker in ``Ussuri`` release, ``vnfcInstanceId``, ``cause``, and
``additionalParams`` are supported for both of SOL002 and SOL003.

If the vnfcInstanceId parameter is null, this means that healing operation is
required for the entire Kubernetes cluster, which is the case in SOL003.


Following is a sample of healing request body for SOL002:

.. code-block::

  {
    "vnfcInstanceId": "311485f3-45df-41fe-85d9-306154ff4c8d"
  }



Healing a node in Kubernetes cluster with SOL002
------------------------------------------------

Healing a Master-node
^^^^^^^^^^^^^^^^^^^^^

The following changes are needed:

+ Extend MgmtDriver to support ``heal_start`` and ``heal_end``

  + In ``heal_start``, the target node is removed from the Kubernetes cluster
    by deleting it from the etcd cluster and disabling the load balance in HA
    proxy. These are executed in a sample script invoked in MgmtDriver.

  + In ``heal_end``, MgmtDriver invokes a sample script to install and
    configure the new Master-node, to add it to the etcd cluster, and to
    register in HA proxy for load balancing.

.. note:: It is assumed that the required information for Heal operation in
          MgmtDriver is stored in the additional parameter of the Instantiate
          and/or Heal request. MgmtDriver passes them to the sample script.

The diagram below shows the Heal VNF operation for a Master-node:

::

                                                           +---------------+
                                                           | Heal          |
                                                           | Request with  |
                                                           | Additional    |
                                                           | Params        |
                                                           +---+-----------+
                                                               |
                                              +----------------+-----------+
                                              |                v      VNFM |
                                              |  +-------------------+     |
                                              |  |   Tacker-server   |     |
                                              |  +---------+---------+     |
                                              |            |               |
                       4. heal_end            |            v               |
                          Kubernetes cluster  |  +----------------------+  |
                                    (Master)  |  |    +-------------+   |  |
                       +----------------------+--+----| MgmtDriver  |   |  |
                       |                      |  |    +-----------+-+   |  |
                       |                      |  |                |     |  |
                       |                      |  |  1. heal_start |     |  |
                       |                      |  |     Kubernetes |     |  |
  +--------------------+----------+           |  |        cluster |     |  |
  |                    |          |           |  |        (Master)|     |  |
  |                    |          |           |  |                |     |  |
  |                    |          |           |  |                |     |  |
  |  +----------+  +---+------+   |           |  |                |     |  |
  |  |          |  |   v      |   | 3. Create |  | +-----------+  |     |  |
  |  | +------+ |  | +------+ |   |    new VM |  | |OpenStack  |  |     |  |
  |  | |Worker| |  | |Master| |<--------------+--+-|InfraDriver|  |     |  |
  |  | +------+ |  | +------+ |   |           |  | +------+----+  |     |  |
  |  |   VM     |  |   VM     |   |           |  |        |       |     |  |
  |  +----------+  +----------+   |           |  |        |       |     |  |
  |  +----------+  +----------+   | 2. Delete |  |        |       |     |  |
  |  | +------+ |  | +------+ |   | failed VM |  |        |       |     |  |
  |  | |Worker| |  | |Master| |<--+-----------+--+--------+       |     |  |
  |  | +------+ |  | +------+ |   |           |  |                |     |  |
  |  |   VM     |  |   VM     |<--+-----------+--+----------------+     |  |
  |  +----------+  +----------+   |           |  |                      |  |
  +-------------------------------+           |  |      Tacker-conductor|  |
  +-------------------------------+           |  +----------------------+  |
  |       Hardware Resources      |           |                            |
  +-------------------------------+           +----------------------------+


The diagram shows related component of this spec proposal and an overview of
the following processing:

#. MgmtDriver pre-processes to remove Master-node from the existing etcd cluster
   in ``heal_start`` before deleting the failed VM.

   #. Remove the failed Master-node from etcd cluster by notifying the other
      active Master-node of the failure.
   #. Remove the failed VM from a load balancing target by changing the HA Proxy
      setting.

#. OpenStackInfraDriver deletes failed VM.
#. OpenStackInfraDriver creates a new VM as a replacement for a failed VM.

#. MgmtDriver heals the Kubernetes cluster in ``heal_end``.

   #. MgmtDriver setup new Master-node on new VMs.
      This setup procedure can be implemented with the shell script or the
      python script including installation and configuration tasks.
   #. Invoke the script for repairing etcd cluster if the Heal target is
      Master-node.
   #. Invoke the script for changing HA proxy configuration.

.. note:: The failed VMs are expected to be identified by checking
          vnfcInstanceId parameter in the Heal request. In case of this
          parameter is null, it means that entire rebuild is required.
          Those procedure is defined in the specification of
          etsi-nfv-sol-rest-api-for-VNF-deployment [#VNF-deployment]_.

.. note:: To identify the VMs newly created, it is assumed that information
          such as the number of Worker-node VMs before Heal and the creation
          time of each VM will need to be referenced.






Following sequence diagram describes the components involved and the flow of
Healing Master-node operation:

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
    "VnfInstance(Tacker DB)"
    "RemoteCommandExecutor"

    Client -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/heal"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_start"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get the vim connection info"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "MgmtDriver"
      [label = "get the vm info to be deleted by the request data"];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "remove the failed Master-node from etcd cluster by notifying
      the other active Master-node of the failure"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "remove the failed Master-node from HA proxy"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];

    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "OpenstackDriver"
      [label = "execute OpenstackDriver"];
    "OpenstackDriver" -> "Heat"
      [label = "resource signal"];
    "OpenstackDriver" -> "Heat"
      [label = "update stack"];
    "OpenstackDriver" <-- "Heat"
      [label = ""];
    "VnfLcmDriver" <-- "OpenstackDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_end"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get the vim connection info"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "Heat"
      [label = "get the new vm info created by Heal operation."];
    "MgmtDriver" <-- "Heat"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Install Kubernetes on the new Master-node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Repairs etcd cluster by invoking shell script"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Changes HA proxy configuration"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];

    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];
  }

The procedure consists of the following steps as illustrated in above sequence:

#. Client sends a POST request to the Heal VNF Instance resource.
#. Basically the same sequence as described in the "3) Flow of Heal of a VNF
   instance "chapter of spec `etsi-nfv-sol-rest-api-for-VNF-deployment`_,
   except for the MgmtDriver.

#. The following processes are performed in ``heal_start``.

   #. MgmtDriver gets Vim connection information in order to get failed
      Kubernetes cluster information such as auth_url.
   #. MgmtDriver gets the failed VM information by checking vnfcInstanceId
      parameter in the Heal request.
   #. MgmtDriver remove the failed Master-node from etcd cluster by notifying
      the other active Master-node of the failure.
   #. MgmtDriver Remove the failed VM from a load balancing target by changing
      the HA Proxy setting.

#. OpenStack Driver uses Heat to delete failed VM.
#. OpenStack Driver uses Heat to create a new VM.

#. The following processes are performed in ``heal_end``.

   #. MgmtDriver gets Vim connection information in order to get existing
      Kubernetes cluster information such as auth_url.
   #. MgmtDriver gets the new VM information from the stack resource in Heat.
   #. MgmtDriver install and configure the Master-node on the VM by invoking a
      shell script using RemoteCommandExecutor.
   #. MgmtDriver adds the new Master-node to etcd cluster by invoking shell
      script using RemoteCommandExecutor.
   #. MgmtDriver changes HA proxy configuration by invoking shell script using
      RemoteCommandExecutor.

Healing a Worker-node
^^^^^^^^^^^^^^^^^^^^^

The following changes are needed:

+ Extend MgmtDriver to support ``heal_start`` and ``heal_end``

  + In ``heal_start``

    + Try evacuating the pod running on the failed VM to another worker node.
    + Remove the failed Worker-node by notifying the existing Master-node of
      the failure.

  + In ``heal_end``

    + the same as ``scale_end`` described in the specification of
      `mgmt-driver-for-k8s-scale`_.

      MgmtDriver setup new Worker-node on new VMs in ``heal_end``.
      This setup procedure can be implemented with the shell script or the
      python script including installation and configuration tasks.

.. note:: It is assumed that the required information for Heal operation in
          MgmtDriver is stored in the additional parameter of the Instantiate
          and/or Heal request. MgmtDriver passes them to the sample script.

The diagram below shows VNF Heal operation for a Worker-node:

::

                                                           +---------------+
                                                           | Heal          |
                                                           | Request with  |
                                                           | Additional    |
                                                           | Params        |
                                                           +---+-----------+
                                                               |
                                              +----------------+-----------+
                                              |                v      VNFM |
                                              |  +-------------------+     |
                                              |  |   Tacker-server   |     |
                                              |  +---------+---------+     |
                                              |            |               |
                       4. heal_end            |            v               |
                          Kubernetes cluster  |  +----------------------+  |
                                    (Worker)  |  |    +-------------+   |  |
                       +----------------------+--+----| MgmtDriver  |   |  |
                       |                      |  |    +-----------+-+   |  |
                       |                      |  |                |     |  |
                       |                      |  |  1. heal_start |     |  |
                       |                      |  |     Kubernetes |     |  |
  +--------------------+----------+           |  |        cluster |     |  |
  |                    |          |           |  |        (Worker)|     |  |
  |                    |          |           |  |                |     |  |
  |                    |          |           |  |                |     |  |
  |  +----------+  +---+------+   |           |  |                |     |  |
  |  |          |  |   v      |   | 3. Create |  | +-----------+  |     |  |
  |  | +------+ |  | +------+ |   |    new VM |  | |OpenStack  |  |     |  |
  |  | |Master| |  | |Worker| |<--------------+--+-|InfraDriver|  |     |  |
  |  | +------+ |  | +------+ |   |           |  | +------+----+  |     |  |
  |  |   VM     |  |   VM     |   |           |  |        |       |     |  |
  |  +----------+  +----------+   |           |  |        |       |     |  |
  |  +----------+  +----------+   | 2. Delete |  |        |       |     |  |
  |  | +------+ |  | +------+ |   | failed VM |  |        |       |     |  |
  |  | |Master| |  | |Worker| |<--+-----------+--+--------+       |     |  |
  |  | +------+ |  | +------+ |   |           |  |                |     |  |
  |  |   VM     |  |   VM     |<--+-----------+--+----------------+     |  |
  |  +----------+  +----------+   |           |  |                      |  |
  +-------------------------------+           |  |      Tacker-conductor|  |
  +-------------------------------+           |  +----------------------+  |
  |       Hardware Resources      |           |                            |
  +-------------------------------+           +----------------------------+

The diagram shows related component of this spec proposal and an overview of
the following processing:

#. MgmtDriver pre-processes to remove Worker-node from the Kubernetes cluster in
   ``heal_start`` before deleting the failed VM.

   #. Try evacuating the pod running on the failed VM to another worker node.
   #. Remove the failed Worker-node by notifying the existing Master-node of
      the failure.

#. OpenStackInfraDriver deletes failed VM.
#. OpenStackInfraDriver creates a new VM as a replacement for a failed VM.
#. MgmtDriver heals the Kubernetes cluster in ``heal_end``.

   This Heal procedure is basically the same as ``scale_end`` described in the
   specification of `mgmt-driver-for-k8s-scale`_.

   MgmtDriver setup new Worker-node on new VMs in ``heal_end``.
   This setup procedure can be implemented with the shell script or the python
   script including installation and configuration tasks.

.. note:: The failed VMs are expected to be identified by checking
          vnfcInstanceId parameter in the Heal request. In case of this
          parameter is null, it means that entire rebuild is required.
          Those procedure is defined in the specification of
          etsi-nfv-sol-rest-api-for-VNF-deployment [#VNF-deployment]_.

.. note:: To identify the VMs newly created, it is assumed that information
          such as the number of Worker-node VMs before Heal and the creation
          time of each VM will need to be referenced.




Following sequence diagram describes the components involved and the flow of
Heal the Worker-node operation:

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
    "VnfInstance(Tacker DB)"
    "RemoteCommandExecutor"

    Client -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/heal"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_start"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get the vim connection info"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "MgmtDriver"
      [label = "get the vm info to be deleted by the request data"];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "try evacuating the pod running on the failed VM to another
      worker node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Notify the Master-node of the failed VM"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];

    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "OpenstackDriver"
      [label = "execute OpenstackDriver"];
    "OpenstackDriver" -> "Heat"
      [label = "resource signal"];
    "OpenstackDriver" -> "Heat"
      [label = "update stack"];
    "OpenstackDriver" <-- "Heat"
      [label = ""];
    "VnfLcmDriver" <-- "OpenstackDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_end"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get the vim connection info"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "Heat"
      [label = "get the new vm info created by Heal operation."];
    "MgmtDriver" <-- "Heat"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "Install Kubernetes on the new Worker-node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];

    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];
  }

The procedure consists of the following steps as illustrated in above sequence:

#. Client sends a POST request to the Heal VNF Instance resource.
#. Basically the same sequence as described in the "3) Flow of Heal of a VNF
   instance "chapter of spec `etsi-nfv-sol-rest-api-for-VNF-deployment`_,
   except for the MgmtDriver.

#. The following processes are performed in ``heal_start``.

   #. MgmtDriver gets Vim connection information in order to get failed
      Kubernetes cluster information such as auth_url.
   #. MgmtDriver gets the failed VM information by checking vnfcInstanceId
      parameter in the Heal request.
   #. Try evacuating the pod running on the failed VM to another worker node.
   #. Remove the failed Worker-node by notifying the existing Master-node of
      the failure.

#. OpenStack Driver uses Heat to delete failed VM.
#. OpenStack Driver uses Heat to create a new VM.

#. The following processes are performed in ``heal_end``.

   #. MgmtDriver gets Vim connection information in order to get existing
      Kubernetes cluster information such as auth_url.
   #. MgmtDriver gets the new VM information from the stack resource in Heat.
   #. MgmtDriver setup a Worker-node on the VM by invoking shell script using
      RemoteCommandExecutor.


Healing a Kubernetes cluster with SOL003
----------------------------------------

Basically, Heal operation for the entire Kubernetes cluster is based on the
spec of `mgmt-driver-for-k8s-cluster`_, which specifies operations for
instantiation and termination. For deleting an existing resource in a Heal
operation, ``heal_start`` is same as ``terminate_end``, and for generating a
new resource in a Heal operation, ``heal_end`` is same as ``instantiate_end``.
During the Heal of the entire VNF instance, the VIM information must be
deleted and the old Kubernetes cluster information stored in the
``vim_connection_info`` of the VNF Instance table must also be cleared. These
operations are required to be implemented in both ``heal_start`` and
``terminate_end``.




Following sequence diagram describes the components involved and the flow of
Heal operation for an entire VNF instance:

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
    "VnfInstance(Tacker DB)"
    "RemoteCommandExecutor"
    "NfvoPlugin"

    Client -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/heal"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_start"];
    "MgmtDriver" -> "NfvoPlugin"
      [label = "delete the failed VIM information"];
    "MgmtDriver" <-- "NfvoPlugin"
      [label = ""];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "Clear the old Kubernetes cluster information stored in the
      vim_connection_info of the VNF Instance"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"

    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];

    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "OpenstackDriver"
      [label = "execute OpenstackDriver"];
    "OpenstackDriver" -> "Heat"
      [label = "resource signal"];
    "OpenstackDriver" -> "Heat"
      [label = "update stack"];
    "OpenstackDriver" <-- "Heat"
      [label = ""];
    "VnfLcmDriver" <-- "OpenstackDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];

    "Tacker-conductor" -> "MgmtDriver"
      [label = "heal_end"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get stack id"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "Heat"
      [label = "get ssh ip address and Kubernetes address using stack id"];
    "MgmtDriver" <-- "Heat"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "install Kubernetes on the new node"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "install etcd cluster by invoking shell script"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "NfvoPlugin"
      [label = "register Kubernetes VIM to tacker"];
    "MgmtDriver" <-- "NfvoPlugin"
      [label = ""]
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "append Kubernetes cluster VIM info to VimConnectionInfo"]
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""]
    "Tacker-conductor" <-- "MgmtDriver"
      [label = ""];

  }

The procedure consists of the following steps as illustrated in above sequence:

#. Client sends a POST request to the Heal VNF Instance resource.
#. Basically the same sequence as described in the "3) Flow of Heal of a VNF
   instance "chapter of spec `etsi-nfv-sol-rest-api-for-VNF-deployment`_,
   except for the MgmtDriver.

#. ``heal_start`` works the same as `mgmt-driver-for-k8s-cluster`_ of
   terminate_end.

#. OpenStack Driver uses Heat to delete failed VM.
#. OpenStack Driver uses Heat to create a new VM.

#. ``heal_end`` works the same as `mgmt-driver-for-k8s-cluster`_ of
   instantiate_end.


Alternatives
------------
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

  + Support the healing of Kubernetes nodes in ``heal_start`` and ``heal_end``.

  + Provides the following sample script executed by MgmtDriver:

    + to incorporate the new Master-node into the existing etcd cluster.

    + to change HA Proxy settings due to replacement of old and new VMs in the
      process of ``heal_start`` and ``heal_end``

+ Add new unit and functional tests.

Dependencies
============

This spec depends on the following specs:

+ `mgmt-driver-for-k8s-cluster`_
+ `mgmt-driver-for-ha-k8s`_
+ `mgmt-driver-for-k8s-scale`_

``heal_end`` referred in "Proposed change" is based on ``instantiate_end``
in the spec of `mgmt-driver-for-k8s-cluster`_.
Healing operation for individual Master-node is performed assuming that the
Kubernetes cluster is an HA configuration, as described in the spec of
`mgmt-driver-for-ha-k8s`_. Also, Healing operation for individual Worker-node
is referring `mgmt-driver-for-k8s-scale`_ for the ``scale_start``.

Testing
=======
Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================
Complete user guide will be added to explain Kubernetes cluster Healing from the
perspective of VNF LCM APIs.

References
==========
.. _support-scale-api-based-on-etsi-nfv-sol:
  ../victoria/support-scale-api-based-on-etsi-nfv-sol.html
.. _mgmt-driver-for-k8s-cluster:
  ./mgmt-driver-for-k8s-cluster.html
.. _mgmt-driver-for-k8s-scale:
  ./mgmt-driver-for-k8s-scale.html
.. _mgmt-driver-for-ha-k8s:
  ./mgmt-driver-for-ha-k8s.html
.. _etsi-nfv-sol-rest-api-for-VNF-deployment:
  https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol
  -rest-api-for-VNF-deployment.html
.. [#SOL002] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/
.. [#SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/
.. [#VNF-deployment] https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol-rest-api-for-VNF-deployment
