..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode


===============================
Support CNF Scale in v2 LCM API
===============================

.. Blueprints:

https://blueprints.launchpad.net/tacker/+spec/support-nfv-solv3-scale-vnf

This specification enhances
version 2 (v2) of Scale API for supporting CNF.

Problem description
===================

Yoga release supported VNF Lifecycle Management (LCM) operations
defined in ETSI NFV SOL002 v3.3.1 [#NFV-SOL002_331]_
and SOL003 v3.3.1 [#NFV-SOL003_331]_.
It also supported CNF Lifecycle Management with v2 APIs
such as Instantiate API, Terminate API, and ChangeCurrentVnfPackage API.

However, v2 Scale API has not supported CNF yet.
Supporting CNF in v2 LCM API makes Tacker more powerful generic VNFM.


Proposed change
===============

This specification enhances the following API to support CNF.

* Scale VNF (POST /v2/vnf_instances/{vnfInstanceId}/scale)

Definition of CNF scaling
-------------------------

The definition of v2 CNF scaling is the same as the v1 CNF scaling.

In case of using Kubernetes VIM, the VDUs are mapped to
ReplicaSet, Deployment, DaemonSet, or StatefulSet, and a VNFC is a Pod.
The scale operation changes the number of replicas for the VDU resource
and Kubernetes controller automatically creates or deletes Pods.

The following Kubernetes resource kinds support
Updating the number of replicas.

* ReplicaSet
* Deployment
* StatefulSet

.. note:: ``DaemonSet`` can be also mapped to VDU but it's not supported in
          the scale operation because it doesn't have the replicas property.


.. note:: When scale-in, the assigned PersistentVolumeClaim (PVC) and
          PersistentVolume (PV) are left. Also, when scale-out, users need
          to provision the required PVC and PV before the operation if the Pod
          has a spec section for PVC.
          This prerequisite is the same as the v1 API.

Flow of Scale VNF
-----------------

There is no change from the current implementation except for
InfraDriver (KubernetesDriver) processing.

.. seqdiag::

  seqdiag {

    node_width = 100;
    edge_length = 120;

    Client; NFVO; tacker-server; tacker-conductor; VnfLcmDriver;
    MgmtDriver; KubernetesDriver; Kubernetes; VNF;

    Client -> "tacker-server"
      [label = "POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/scale"];
    Client <-- "tacker-server" [label = "Response 202 Accepted"];
    "tacker-server" ->> "tacker-conductor"
      [label = "trigger asynchronous task"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (STARTING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "tacker-conductor"
      [label = "calculates the number of Pods to scale"];
    NFVO <- "tacker-conductor" [label = "POST /grants"];
    NFVO --> "tacker-conductor" [label = "201 Created"];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor" [label = "POST {callback URI} (PROCESSING)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute preamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute preamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute LCM operation"];
    "VnfLcmDriver" -> "VnfLcmDriver"
      [label = "calculate the number of VMs to scale-out or scale-in"];
    "VnfLcmDriver" -> "KubernetesDriver" [label = "execute KubernetesDriver"];
    "KubernetesDriver" -> "Kubernetes"
      [label = "call Update API to change replicas of target VDU"];
    "KubernetesDriver" <-- "Kubernetes" [label = ""];
    "KubernetesDriver" -> "Kubernetes"
       [label = "call Read API to check the status of resources"];
    "KubernetesDriver" <-- "Kubernetes" [label = "resource information"];
    "VnfLcmDriver" <-- "KubernetesDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" -> "VnfLcmDriver" [label = "execute postamble operation"];
    "VnfLcmDriver" -> "MgmtDriver" [label = "execute postamble operation"];
    "MgmtDriver" -> "VNF" [label = "VNF Configuration"];
    "MgmtDriver" <-- "VNF" [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver" [label = ""];
    "tacker-conductor" <-- "VnfLcmDriver" [label = ""];
    "tacker-conductor" ->> "tacker-conductor"
      [label = "execute notification process"];
    Client <- "tacker-conductor"
      [label = "POST {callback URI} (COMPLETED or FAILED_TEMP)"];
    Client --> "tacker-conductor" [label = "Response: 204 No Content"];
  }

The procedure consists of the following steps as illustrated in above sequence:

Precondition: VNF instance in "INSTANTIATED" state.

#. Client sends VNFM a POST request for the Scale VNF Instance.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "STARTING" state to indicate the start occurrence of
   the lifecycle management operation.
#. VNFM calculates the number of Pods to scale by multiplying
   "number_of_steps" contained in Scale VNF request and "number_of_instances"
   contained in VNFD.
#. VNFM and NFVO exchange granting information.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "PROCESSING" state to indicate the processing
   occurrence of the lifecycle management operation.
#. MgmtDriver executes preamble operation according to a MgmtDriver script.
#. The total number of Pods is calculated by current resources obtained by
   ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo``
   and scaled Pods obtained by ``grant.addResources and grant.removeResources``.
#. KubernetesDriver sends Kubernetes a Update request with the incremented
   or decremented "replicas" for the target VDU.
#. KubernetesDriver sends Kubernetes a Read request
   to check the status of resources.
#. MgmtDriver executes postamble operation according to a MgmtDriver script.
#. VNFM sends endpoints such as Client
   a VNF lifecycle management operation occurrence
   notification with the "COMPLETED" state or "FAILED_TEMP" state
   to indicate the result of the lifecycle management operation.


Postcondition: VNF instance is still in "INSTANTIATED" state and VNF has been
scaled.

.. note:: V2 Scale-in operation for VNF using OpenStack VIM deletes
   VNFC from the last registered one.
   However, Scale-in operation for CNF using Kubernetes VIM
   cannot control the order of deletion due to Kubernetes's functionality.

.. note:: Tacker does not support *non-uniform deltas*
  defined in ETSI NFV SOL001 [#NFV-SOL001_331]_.
  Therefore, *uniform delta* corresponding to "number_of_instances" can be set
  and "number_of_instances" is the same regardless of scale_level.


Kubernetes API support
----------------------

KubernetesDriver calls following API to get current number of replicas
and updates the number replicas of target resource.

+-------------------+----------+-------------------------------------+
| API Group         | Type     | API method                          |
+===================+==========+=====================================+
| apps (AppsV1Api)  | Read     | read_namespaced_replica_set_scale   |
|                   |          +-------------------------------------+
|                   |          | read_namespaced_deployment_scale    |
|                   |          +-------------------------------------+
|                   |          | read_namespaced_stateful_set_scale  |
|                   +----------+-------------------------------------+
|                   | Update   | patch_namespaced_replica_set_scale  |
|                   |          +-------------------------------------+
|                   |          | patch_namespaced_deployment_scale   |
|                   |          +-------------------------------------+
|                   |          | patch_namespaced_stateful_set_scale |
+-------------------+----------+-------------------------------------+

The arguments of Read API are ``name`` and ``namespace``.

The arguments of Update API are ``name``, ``namespace``, and ``body``.
The body is set to be the updated value of "spec.replicas" with the returned
value in Read API.

The number of "spec.replicas" is calculated as follows:

* Scale-in: update_replicas = current_replicas - scaling_step * number_of_steps
* Scale-out: update_replicas = current_replicas + scaling_step * number_of_steps

The parameters used in the calculation are defined below:

* current_replicas: the number of ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo``
  belonging to the target VDU,
  which is judged by ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.vduId``
* scaling_step: "number_of_instances" in scalingAspect defined in VNFD
* number_of_steps: Parameter given in ``ScaleVnfRequest``


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

Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>


Work Items
----------

* Implement KubernetesDriver processes running on Tacker-conductor.
* Add new unit and functional tests.
* Update the Tacker user guide.

Dependencies
============

* Scale operation

  Depends on spec "Enhance NFV SOL_v3 LCM operation"
  [#Enhance_NFV_SOL_v3_LCM_operation]_.

Testing
========

Unit and functional test cases will be added for v2 CNF scale operations
using Kubernetes VIM.

Documentation Impact
====================

Description about v2 scale operations will be added to the Tacker user guide.

References
==========

.. [#NFV-SOL002_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_nfv-sol002v030301p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#NFV-SOL003_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
  (Chapter 5: VNF Lifecycle Management interface)
.. [#Enhance_NFV_SOL_v3_LCM_operation]
  https://specs.openstack.org/openstack/tacker-specs/specs/yoga/enhance-nfv-solv3-lcm-operation.html
.. [#NFV-SOL001_331]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/03.03.01_60/gs_nfv-sol001v030301p.pdf
