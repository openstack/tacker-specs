=======================================
Support Multi-tenant for Kubernetes VIM
=======================================

https://blueprints.launchpad.net/tacker/+spec/k8s-namespace

Problem description
===================
ETSI NFV-SOL003 VNF Lifecycle Management for CNF on Kubernetes VIM is
supported in Wallaby release such as Instantiate [#DOC-CNF-DEPLOY]_,
Scale [#DOC-CNF-SCALE]_, and Heal [#DOC-CNF-HEAL]_,
but its operations with specified namespace are not provided.
This specification proposes VNF Lifecycle Management operations for CNF
with specified namespace.
Users should be a ServiceAccount which is bound to ClusterRoles as admin
or to Roles as general users.

Proposed Change
===============

The Instantiate operation in ETSI NFV-SOL003 VNF Lifecycle Management
2.6.1 [#NFV-SOL003]_ enable Users to specify the target namespace in
the InstantiateVnfRequest to deploy CNF on Kubernetes VIM.
``additionalParams`` field provides new parameter ``namespace`` for
the target namespace.

.. note::

   A VNF instance should be in a single namespace.
   It's possible to deploy plural Kubernetes resources as a VNF instance,
   but they should be managed in the same namespace.


The following changes are required in LCM operation for CNF:

#. CNF Instantiate

   + Add namespace field to ``InstantiateVnfRequest``.
   + Add logic to use specified namespace in Kubernetes InfraDriver.
   + Store specified namespace in Tacker DB.

   .. note::

     Namespaces are stored in both ``VnfResource.resource_name`` and
     ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.metadata``.
     This spec proposes aggregating them into ``VnfInstance.metadata``
     for ease of managing namespaces in Tacker DB.

   .. note::

      The specified namespace should be described in the response of
      ``GET /vnf_instances/{vnfInstanceId}/``.


#. CNF Scale

   + Add logic to get stored namespace in ``VnfInstance`` table.

   .. note::

      Need to design how to manage namespace after instantiation.
      This may not be required.


#. CNF Heal

   + Add logic to get stored namespace in ``VnfInstance`` table.

   .. note::

      Need to design how to manage namespace after instantiation.
      This may not be required.


#. CNF Terminate

   + Add logic to get stored namespace in ``VnfInstance`` table.


CNF Instantiate with specified namespace
----------------------------------------

The diagram of CNF Instantiate with specified namespace is shown below:

::

                                  +----------+
                                  |          |
                                  |  VNFD    |
                                  |          |
                                  +-+--------+
                                    |
                                  +----------------+  +--------v-+ +------------------+
                                  | CNF Definition |  |          | | Instantiation    |
                                  | File           +-->   CSAR   | | Request with     |
                                  |                |  |          | | additionalParams |
                                  +----------------+  +------+---+ +--+---------------+
                                                             |        |
                                                             |        | 1. Request
                                                             |        |    with namespace
  +------------------------------+                    +-----------------------------+
  | CNF                          |                    |      |        |       VNFM  |
  |                              |                    |   +--v--------v----+        |
  |  +----------+  +----------+  |                    |   | TackerServer   |        |
  |  | Pod      |  | Pod      |  |                    |   +------+---------+        |
  |  |          |  |          |  |                    |          |                  |
  |  +----------+  +----------+  |                    |   +---------------------+   |
  +------------------------------+                    |   |      |              |   |
                                                      |   |  +-v-+----------+   |   |
  +------------------------------+                    |   |  | VnflcmDriver |   |   |
  | Kubernetes cluster VNF       |                    |   |  |              |   |   |
  |                              |                    |   |  +-+-^----------+   |   |
  |  +----------+  +----------+  |                    |   |    | | 3. Store     |   |
  |  |    VM    |  |    VM    |  | 2. Set namespace   |   |    | |    namespace |   |
  |  | +------+ |  | +------+ |  |    in K8s API call |   |  --v-+----------+   |   |
  |  | |Worker| |  | |Master+<-------------------------------+ Kubernetes   |   |   |
  |  | +------+ |  | +------+ |  |                    |   |  | InfraDriver  |   |   |
  |  +----------+  +----------+  |                    |   |  +--------------+   |   |
  |                              |                    |   |                     |   |
  +------------------------------+                    |   |    Tacker Conductor |   |
                                                      |   |                     |   |
  +------------------------------+                    |   +---------------------+   |
  | Hardware Resources           |                    |                             |
  +------------------------------+                    +-----------------------------+


#. The specified namespace is sent in ``InstantiateVnfRequest``.

#. Kubernetes InfraDriver call K8s API with specified namespace.

#. VnflcmDriver stores the namespace in Database.


Sample input parameters
~~~~~~~~~~~~~~~~~~~~~~~

A new attribute named ``namespace`` is added to ``additionalParams`` parameter
in ``InstantiateVnfRequest`` defined in ETSI NFV-SOL003 v2.2.6 [#NFV-SOL003]_.
No change is required for the other parameters from existing CNF operation.

+------------------+---------------------------------------------------------+
| Attribute name   | Parameter description                                   |
+==================+=========================================================+
| namespace        | Namespace for Kubernetes API call.                      |
|                  | If absent, the namespace in the resource file is used.  |
+------------------+---------------------------------------------------------+

Following is a sample:

.. code-block:: json

  {
    "flavourId": "simple",
    "additionalParams": {
      "lcm-kubernetes-def-files": [
        "Files/kubernetes/pod.yaml"
      ],
      "namespace": "namespaceA"
    },
    "vimConnectionInfo": [
      {
        "id": "8a3adb69-0784-43c7-833e-aab0b6ab4470",
        "vimId": "specified by response of vim list",
        "vimType": "kubernetes"
      }
    ]
  }


Sequence of CNF Instantiate with specified namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "KubernetesInfraDriver"
    "Heat"
    "TackerDB"
    "k8s client"

    Client -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/instantiate"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
   "Tacker-conductor" -> "VnfLcmDriver"
      [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "KubernetesInfraDriver"
      [label = "execute KubernetesInfraDriver"];
    "KubernetesInfraDriver" -> "TackerDB"
      [label = "get package info"];
    "KubernetesInfraDriver" <-- "TackerDB"
      [label = "return package info"];
    "KubernetesInfraDriver" -> "TackerDB"
      [label = "Save the namespace to the vnf_resources table"]
    "KubernetesInfraDriver" <-- "TackerDB"
      [label = ""]
    "KubernetesInfraDriver" -> "k8s client"
      [label = "create Kubernetes resource"]
    "KubernetesInfraDriver" <-- "k8s client"
      [label = ""]
    "KubernetesInfraDriver" -> "TackerDB"
      [label = "save pod information"]
    "KubernetesInfraDriver" <-- "TackerDB"
      [label = ""]
    "VnfLcmDriver" <-- "KubernetesInfraDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }


The procedure consists of the following steps as illustrated above.

#. Client sends instantiate request.

#. Same as the steps in `Wallaby` release until the KubernetesInfraDriver
   is invoked.

#. The KubernetesInfraDriver call Kubernetes API with specified namespace:

   #. The Kubernetes Client send request with the namespace in
      ``InstantiateVnfRequest.additionalParams``.
      If namespace is not provided, one in Kubernetes resource file is used.

   #. KubernetesInfraDriver add the namespace to "vnf_resources" table
      in TackerDB.

      .. note::

         The ``namespace`` stored in the "vnf_resources" table is used
         in the Scale, Heal, and Terminate operations for CNF.


Data model impact
-----------------

As mentioned above, stored namespaces in Tacker DB
will be aggregated into ``VnfInstance.vnf_metadata`` by this implementation.
Those fields will be changed as follows:

+ ``VnfResource.resource_name``

  + This field contains namespace and resource name as comma separated value,
    but will store only resource name in this specification.

+ ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.metadata``

  + This field is not modified in this specification, but will no longer be
    referred from Tacker.


.. note::

   The metadata field in ``vnf_instances`` table is defined as JSON.
   No change is required, but it's worth to note that
   metadata field is implemented as ``vnf_metadata``.


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

Performance impact
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
  Tatsuhiro Furuya <tatu.furuya@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  Liang Lu <lu.liang@fujitsu.com>

Work Items
----------
+ Implement to support:

  + Specify the target namespace to deploy CNF on Kubernetes VIM when CNF instantiate.
  + Store specified namespace in Tacker DB when CNF instantiate.
  + Get specified namespace from Tacker DB and Use it when CNF scale and heal.

+ Add new unit and functional tests.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

User guide will be modified to explain to VNF Lifecycle Management operations for CNF with specified namespace.

References
==========

.. [#DOC-CNF-DEPLOY] https://docs.openstack.org/tacker/latest/user/etsi_containerized_vnf_usage_guide.html
.. [#DOC-CNF-SCALE] https://docs.openstack.org/tacker/latest/user/etsi_cnf_scaling.html
.. [#DOC-CNF-HEAL] https://docs.openstack.org/tacker/latest/user/etsi_cnf_healing.html
.. [#NFV-SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
