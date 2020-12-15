===============================
Support Scale Operation for CNF
===============================

https://blueprints.launchpad.net/tacker/+spec/support-cnf-scale

This specification describes the "Scale VNF" operation of VNF Lifecycle
Management for Container Network Function (CNF) in Tacker.

Problem description
===================
In ``Victoria`` release, the Instantiate and Terminate VNF operations with VNF
Lifecycle Management defined in `ETSI NFV-SOL003 v2.6.1`_ for CNF are
supported in the spec `container-network-function`_. The CNF scale operation
with ETSI specifications also needs to be implemented. However, the current
ETSI NFV-SOL documents have not defined the detailed specifications for OS
container based VNF. This spec provides the definition of the scale operation
for CNF in Tacker and also the design to be implemented.

Proposed change
===============
This spec proposes the definition of the scale operation and its design to be
implemented.

Definition of CNF scaling
-------------------------
We propose the scale operation for CNF to be changing the number of VNFC in
a VNF instance. When a VNF instance is composed of OS containers and the
VIM is assumed to be Kubernetes, the VDUs can be mapped to Deployment,
DaemonSet, StatefulSet, or ReplicaSet, and a VNFC instance can be a Pod.
The scale operation changes the number of replicas for the VDU resource and
Kubernetes controller automatically creates or deletes Pods.

.. note:: It is also possible to define the scale operation to be
          changing the number of ``maxReplicas`` or ``minReplicas`` in
          ``HorizontalPodAutoscaler (HPA)``, however, it is a future work. To
          deploy HPA, how to instantiate and configure the required metrics
          server also needs to be defined.

.. note:: When scaling-in, the assigned PersistentVolume (PVC) and
          PersistentVolume (PV) are left. Also, when scaling-out, Users need
          to provision the required PVC and PV before the operation if the Pod
          has a spec section for PVC.

Design of the "Scale CNF" operation
-----------------------------------

Before the scale operation, CNF containing the resources which have the
properties for replicas need to be instantiated. Kubernetes Infra Driver
needs following changes:

#. To validate the target Kubernetes resource to support the scale operation
#. To load ``scalingAspect`` from VNFD
#. To calculate the required number of replicas with ``scalingAspect``
#. To store current ``scaleLevel`` to InstantiateVnfInfo.ScaleStatus after
   the scale operation
#. To support Kubernetes Python client to update the number of replicas for
   the following Kubernetes resource kinds:

   * Deployment
   * ReplicaSet
   * StatefulSet

.. note:: ``DaemonSet`` can be also mapped to VDU but it's not supported in
          the scale operation because it doesn't have the replicas property.

The diagram below shows the CNF scale operation for an instantiated CNF:

.. code-block::

                                                   +--------------------+
                                                   | Scale Request with |
                                                   | additional Params  |
                                                   +--------+-----------+
                                                            | 1. Request scale
                                                            |    CNF
                                                   +--------+----------------+
                                                   |        v                |
                                                   |  +-------------------+  |
                                                   |  |   Tacker-server   |  |
                                                   |  +-----+-------------+  |
                                                   |        |                |
                                                   |        v                |
                                                   | +--------------------+  |
                                     2. Scale CNF  | |  +--------------+  |  |
                                          +--------+-+--| Kubernetes   |  |  |
  +------------------+ 3. Change the      |        | |  | Infra Driver |  |  |
  |                  |    number of       v        | |  +--------------+  |  |
  | +-----+ +-----+  |    Pods     +------------+  | |                    |  |
  | | Pod | | Pod |<-+-------------| Kubernetes |  | |                    |  |
  | +-----+ +-----+  |             | cluster    |  | |                    |  |
  |                  |             | (Master)   |  | |                    |  |
  | Kubernetes       |             +------------+  | | Tacker-conductor   |  |
  | cluster (Worker) |                             | +--------------------+  |
  +------------------+                             +-------------------------+


#. Tacker-server receives the scale request by user.
#. Kubernetes Infra Driver calls Kubernetes client API for scaling.
#. Kubernetes cluster increases or decreases the number of pods running on
   worker nodes according to the calculated number of replicas.

VNFD for the "Scale CNF" operation
----------------------------------
VNFD needs to have ``ScalingAspects`` definition as the following sample:

.. code-block:: yaml

  node_templates:
    VNF:
      type: Company.Tacker.Kubernetes
      properties:
        flavour_description: The pre_installed flavour

    deployment_name:
      type: tosca.nodes.nfv.Vdu.Compute
      properties:
        name: deployment_name
        description: Deployment of Kubernetes resource
        vdu_profile:
          min_number_of_instances: 1
          max_number_of_instances: 3

  policies:
    - scaling_aspects:
        type: tosca.policies.nfv.ScalingAspects
        properties:
          aspects:
            deployment_name:
              name: deployment_name
              description: deployment_name scaling aspect
              max_scale_level: 3
              step_deltas:
                - delta_1

    - deployment_name_scaling_aspect_deltas:
        type: tosca.policies.nfv.VduScalingAspectDeltas
        properties:
          aspect: deployment_name
          deltas:
            delta_1:
              number_of_instances: 1
        targets: [ deployment_name ]


.. note:: The ``VDU`` and ``aspects`` names should be the same with the name
          of Kubernetes resource defined in Kubernetes manifest files.

.. note:: The other part of VNFD is described in the spec
          `container-network-function`_ with a sample.

Scale in/out of CNF
-------------------
User gives the following request parameters in "POST /vnf_instances/{id}/scale"
as ``ScaleVnfRequest`` data type defined in `ETSI NFV-SOL003 v2.6.1`_:


  +------------------+---------------------------------------------------------+
  | Attribute name   | Parameter description                                   |
  +==================+=========================================================+
  | type             | Indicates the type of the scale operation:\n            |
  |                  | "SCALE_IN" or "SCALE_OUT"                               |
  +------------------+---------------------------------------------------------+
  | aspectId         | Indicates the name of target Kubernetes resource. This  |
  |                  | is defined in VNFD, and user can find it as             |
  |                  | ``InstantiatedVnfInfo.ScaleStatus`` in the response     |
  |                  | of "GET /vnf_instances/{id}".                           |
  +------------------+---------------------------------------------------------+
  | numberOfSteps    | Number of scaling steps.                                |
  +------------------+---------------------------------------------------------+
  | additionalParams | Not needed.                                             |
  +------------------+---------------------------------------------------------+

The following is a sample of request body for scale-in:

.. code-block:: json

    {
      "type": "SCALE_IN",
      "aspectId": "deployment_name",
      "numberOfSteps": "1"
    }

The following sequence diagram describes the components and the flow involved
in the CNF scale operation:

.. seqdiag::

  seqdiag {
    node_width = 100;
    edge_length = 115;

    "Client" -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/scale"];
    "Client" <-- "Tacker-server" [label = "Response 202 Accepted"];
    "Tacker-server" --> "Tacker-conductor" [label = "Trigger asynchronous task"]
    "Tacker-conductor" -> "VnfLcmDriver" [label = "Call VnfLcmDriver"];
    "VnfLcmDriver" -> "KubernetesDriver" [label = "scale()"];
    "KubernetesDriver" -> "KubernetesPythonClient"
      [label = "Execute read API to get current replicas"];
    "KubernetesPythonClient" -> "Kubernetes" [label = "Call read API"];
    "KubernetesPythonClient" <-- "Kubernetes" [label = ""];
    "KubernetesDriver" <-- "KubernetesPythonClient" [label = ""];
    "KubernetesDriver" -> "KubernetesPythonClient"
      [label = "Execute patch API to change replicas"];
    "KubernetesPythonClient" -> "Kubernetes" [label = "Call patch API"];
    "KubernetesPythonClient" <-- "Kubernetes" [label = ""];
    "KubernetesDriver" <-- "KubernetesPythonClient" [label = ""];
    "VnfLcmDriver" <-- "KubernetesDriver" [label = ""];
    "VnfLcmDriver" -> "KubernetesDriver" [label = "scale_wait()"];
    "KubernetesDriver" -> "KubernetesPythonClient"
      [label = "Execute read API for check scale result"];
    "KubernetesPythonClient" -> "Kubernetes" [label = "Call read API"];
    "KubernetesPythonClient" <-- "Kubernetes" [label = ""];
    "KubernetesDriver" <-- "KubernetesPythonClient" [label = ""];
    "VnfLcmDriver" <-- "KubernetesDriver" [label = ""];
    "VnfLcmDriver" -->> "VnfLcmDriver" [label = "Save current scaleLevel"];
    "Tacker-conductor" <-- "VnfLcmDriver" [label = ""];

  }


#. Client sends a POST request to a CNF Instance.
#. Basically the same sequence as the one described in the spec
   `support-scale-api-based-on-etsi-nfv-sol`_, except for the
   Tacker-conductor. In case of the CNF scale operation, the MgmtDriver action
   is not needed.
#. KubernetesDriver sends get API request to Kubernetes with
   KubernetesPythonClient to read the current number of replicas in scale()
   method.
#. KubernetesDriver sends scale API request to Kubernetes with
   KubernetesPythonClient to scale in/out the resource in scale() method. The
   number of Pods to scale in/out is calculated by multiplying
   "number_of_steps" contained in the Scale VNF request and
   "number_of_instances" in VNFD.
#. KubernetesDriver checks the scaling result in scale_wait() method.
#. VnfLcmDriver saves the current scaleLevel in VnfInstance.InstantiatedVnfInfo\
   .scale_status if the scale operation is successful.

.. note:: The number of replicas after the scale operation is not stored in
          Tacker DB, therefore heal operation may result in the different Pod
          counts from the scaled CNF. The replicas should result in the
          number calculated with instantiation level of instantiation
          because Tacker terminates and instantiate CNF in the heal operation.

Kubernetes API support
----------------------
Kubernetes Infra Driver calls following API to get current number of replicas
and updates the number replicas of target resource.

  +-------------------+----------+-------------------------------------+
  | API Group         | Type     | API method                          |
  +===================+==========+=====================================+
  | apps (AppsV1Api)  | GET      | read_namespaced_deployment_scale    |
  |                   |          +-------------------------------------+
  |                   |          | read_namespaced_replica_set_scale   |
  |                   |          +-------------------------------------+
  |                   |          | read_namespaced_stateful_set_scale  |
  |                   +----------+-------------------------------------+
  |                   | PATCH    | patch_namespaced_deployment_scale   |
  |                   |          +-------------------------------------+
  |                   |          | patch_namespaced_replica_set_scale  |
  |                   |          +-------------------------------------+
  |                   |          | patch_namespaced_stateful_set_scale |
  +-------------------+----------+-------------------------------------+

The arguments of Read API are ``name`` and ``namespace``, and the return type
of API is V1Scale described in `V1Scale in Kubernetes-client docs`_.

The arguments of Patch API are ``name``, ``namespace``, and ``body``.
The body is set to be the updated value of "spec.replicas" with the returned
value in Read API.

The number of "spec.replicas" in V1Scale is calculated as follows:

* Scale-in: update_replicas = current_replicas - scaling_step * number_of_steps
* Scale-out: update_replicas = current_replicas + scaling_step * number_of_steps

The parameters used in the calculation are defined below:

  * current_replicas: "spec.replicas" from V1Scale got by Read API
  * scaling_spec: "number_of_instances" in scalingAspect defined in VNFD
  * number_of_steps: Parameter given in ScaleVnfRequest

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
  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  LiangLu <lu.liang@fujitsu.com>

Work Items
----------
* Validate the target Kubernetes resource to support the scale operation.
* Kubernetes Infra Driver will be modified to implement:

  * Load ``scalingAspect`` from VNFD
  * Calculate the required number of replicas with ``scalingAspect``
  * Store current ``scaleLevel`` to InstantiateVnfInfo.ScaleStatus after
    scale operation
  * Support Kubernetes Python client to update the number of replicas for
    following Kubernetes resource kind:

    * Deployment
    * ReplicaSet
    * StatefulSet

* Add new unit and functional tests.

Dependencies
============
None

Testing
=======
Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================
Complete user guide will be added to explain CNF scaling.

References
==========
None

.. _container-network-function : ../victoria/container-network-function.html
.. _support-scale-api-based-on-etsi-nfv-sol:
   ../victoria/support-scale-api-based-on-etsi-nfv-sol.html
.. _ETSI NFV-SOL003 v2.6.1 : https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_NFV-SOL003v020601p.pdf
.. _V1Scale in Kubernetes-client docs : https://github.com/Kubernetes-client/python/blob/release-11.0/Kubernetes/docs/V1Scale.md
