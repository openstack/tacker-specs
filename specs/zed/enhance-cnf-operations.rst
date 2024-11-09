==============================================
Enhancement of CNF operations using Helm Chart
==============================================

https://blueprints.launchpad.net/tacker/+spec/support-instantiationlevel-cnf

https://blueprints.launchpad.net/tacker/+spec/remove-cnf-restriction


Problem description
===================

This specification focuses on enhancing Tacker's Helm Chart handling,
as shown below.

#. When deploying a CNF using the Helm Chart, the initial number of Pods
   should be determined by the ``instantiationLevel`` parameter.
   However, the current v1 LCM API for CNF ignores this parameter.
   [#MGMT_DRIVER_DEPLOY_K8S_AND_CNF_WITH_HELM_1]_
   This specification supports the ``instantiationLevel``
   parameter to determine the initial number of Pods.

#. In the current implementation, only the v1 API supports the
   Instantiate/Terminate CNFs using the Helm Chart.
   This specification proposes supporting CNF operations
   using Helm Chart in the v2 API.

#. In the case of building a Kubernetes cluster according to
   "How to Install Helm to Kubernetes Cluster and Deploy CNF using Helm Chart",
   [#MGMT_DRIVER_DEPLOY_K8S_AND_CNF_WITH_HELM_1]_
   Tacker automatically configures MasterNode to use HelmChart and stores
   relevant access information in TackerDB.
   On the other hand, in the case of using an external Kubernetes cluster,
   access information needs to be set in Tacker DB manually.
   To remove this constraint,
   this specification enhances ``openstack vim register`` command and API
   to handle ``extra`` field.

   .. note:: The following is an example of manually registering access information of
             MasterNode to TackerDB.
             ::

              $ mysql
              mysql> use tacker;
              mysql> update vims set extra=json_object('helm_info', '{"masternode_ip": ["129.152.76.187"], "masternode_username": "root", "masternode_password": "root"}') where id="355a5b1c-4b7b-410c-8e2c-9d099d1f14f1";


Proposed Change
===============

.. _instantiation:

Support instantiation level
---------------------------

This specification proposes
adding the process of calculating the number of VNFCs to be instantiated
from the ``instantiationLevelId`` parameter
and the ``replica count`` parameter defined in VNFD.

Parameters for determining the number of pods to be started are described
in the VNFD.

The required parameters are listed below. [#ETSI-SOL001]_

* ``topology_template.policies.instantiation_levels``
  (type: tosca.policies.nfv.InstantiationLevels)
* ``topology_template.policies.vdu1_initial_delta``
  (type: tosca.policies.nfv.VduInitialDelta)
* ``topology_template.policies.vdu1_scaling_aspect_deltas``
  (type: tosca.policies.nfv.VduScalingAspectDeltas)


The logic for calculating the number of pods is as follows:

#. Extract the value of ``scale_level`` corresponding to the
   ``instantiationLevelId`` described in instantiation_levels
#. "Number of Pods to Launch" = ``vdu1_initial_delta`` +
   ( ``scale_level`` * ``vdu1_scaling_aspect_deltas`` )


The diagram below shows the CNF instantiation using Helm Chart.

::


                                                               +------+ +------------+
                                                               | VNFD | | Helm Chart |
                                                               |      | |            |
                                                               +-+----+ ++-----------+
                                                                 |       |
                                                               +-v-------v-+           +----------------------+
                                                               |           |           | Instantiate          |
                                                               | CSAR      |           | VNF request with     |
                                                               |           |           | instantiationLevelId |
                                                               +-----+-----+           +----------------+-----+
                                                                     |                                  |
       +-----------------------+                                     +--------------+                   |
       | CNF with Helm Chart   |                 1. Request with                    |                   |
       |                       |                    Helm Chart                      |                   |
       |                       |                  (with instantiationLevelId) +-------------------------------+
       |  +------+   +------+  |                                              |     |                   |     |
       |  | Pod  |   | Pod  |  |                                              |  +--v-------------------v--+  |
       |  |      |   |      |  <--------------------+                         |  |                         |  |
       |  +------+   +------+  |                    |                         |  |      TackerServer       |  |
       |                       |                    |                         |  |                         |  |
       +-----------------------+                    |                         |  +------+------------------+  |
                                                    |                         |         |                     |
    +--------------------------------------------------------+                |  +-------------------------+  |
    | Kubernetes cluster VNF                        |        |                |  |      |  TackerConductor |  |
    |                                               |        |                |  |      |                  |  |
    |  +-----------------------+  +-----------------------+  |                |  |  +---v---------------+  |  |
    |  |        Worker         |  |        Master   |     |  |                |  |  | VnflcmDriver      |  |  |
    |  |                       |  |                 |     |  |                |  |  | (V1/V2)           |  |  |
    |  |                       |  |  +--------------+--+  |  |                |  |  +---+---------------+  |  |
    |  |                       |  |  | kubelet         |  |  |                |  |      |                  |  |
    |  |                       |  |  +--------------^--+  |  |                |  |  +---v---------------+  |  |
    |  |                       |  |                 |     |  |                |  |  | Kubernetes        |  |  |
    |  |                       |  |  +--------------+--+  |  |                |  |  | InfraDriver       |  |  |
    |  |                       |  |  | Helm            |  |  |                |  |  |                   |  |  |
    |  |                       |  |  +-----------------+  |  |                |  |  |  +-------------+  |  |  |
    |  |                       |  |  | Helm cli        <-------------------------------+ Helm client |  |  |  |
    |  |                       |  |  +-----------------+  |  |                |  |  |  +-------------+  |  |  |
    |  |                       |  |  | Helm Repository |  |  |                |  |  |                   |  |  |
    |  |                       |  |  +-----------------+  |  | 2. Send        |  |  +-------------------+  |  |
    |  |                       |  |                       |  |    Helm Chart  |  |                         |  |
    |  +-----------------------+  +-----------------------+  |    files with  |  +-------------------------+  |
    |                                                        |    Helm cli    |                               |
    +--------------------------------------------------------+    via SSH     +-------------------------------+
                                                                  and deployment instructions

#. TackerServer receives an Instantiate VNF request with the
   ``instantiationLevelId`` parameter.
#. The KubernetesInfraDriver calculates the number of pods to launch from
   the ``InstantiationLevelId``,
   then send Helm Chart files with Helm cli via SSH.
   The KubernetesInfraDriver sends deployment instructions.

Following sequence diagram describes CNF instantiation with Helm Chart:

.. image:: ./enhance-cnf-operations/01.png

#. Tacker-server receives an Instantiate VNF request with
   ``instantiationLevelId`` in its parameter.
#. Tacker-server sends instantiate VNF request to Tacker-conductor.
#. Tacker-conductor sends instantiate VNF request to VnfLcmDriver(V1/V2)
#. VnfLcmDriver(V1/V2) sends a request to the KubernetesInfraDriver
   to apply deployment.
#. KubernetesInfraDriver gets VNFPackage information from TackerDB.
#. KubernetesInfraDriver calculates the number of Pods to launch
   according the logic described above.
#. KubernetesInfraDriver gets MasterNode access information from TackerDB.
#. KubernetesInfraDriver sends an instruction to deploy
   the Pod using Helm Chart with the calculated number of Pods as a parameter.
#. KubernetesInfraDriver gets manifest information from MasterNode.
#. KubernetesInfraDriver saves manifest information as `vnf_resource` to TackerDB.
#. KubernetesInfraDriver gets pod information from KubernetesDB.
#. KubernetesInfraDriver saves pod information to TackerDB.

.. note:: Saving manifest information as ``vnf_resource`` is performed
   only in the case of v1. v2 does not have ``vnf_resource`` data
   because it is Tacker's original data model not defined by NFV standard.

Sample VNFD file
~~~~~~~~~~~~~~~~

The parameters for calculating the initial number of pods
such as ``tosca.policies.nfv.InstantiationLevels`` defined by
ETSI NFV-SOL001 [#ETSI-SOL001]_
are described in the VNFD.

Following shows a sample VNFD file.


.. code-block:: yaml

  tosca_definitions_version: tosca_simple_yaml_1_2

  description: Sample CNF with helmchart

  imports:
    - etsi_nfv_sol001_common_types.yaml
    - etsi_nfv_sol001_vnfd_types.yaml
    - ipvlanpod1_vnfd_types.yaml

  topology_template:
  (Omit)
    node_templates:
      VNF:
        type: company.provider.VNF
        properties:
          flavour_description: A flavour for single resources

      VDU1:
        type: tosca.nodes.nfv.Vdu.Compute
        properties:
          name: ipvlanpod-ipvlanpod1
          description: kubernetes resource as VDU1
          vdu_profile:
            min_number_of_instances: 1
            max_number_of_instances: 3

    policies:
      (Omit)
      - vdu1_initial_delta:
          type: tosca.policies.nfv.VduInitialDelta
          properties:
            initial_delta:
              number_of_instances: 1
          targets: [ VDU1 ]

      - vdu1_scaling_aspect_deltas:
          type: tosca.policies.nfv.VduScalingAspectDeltas
          properties:
            aspect: vdu1_aspect
            deltas:
              delta_1:
                number_of_instances: 1
          targets: [ VDU1 ]

      - instantiation_levels:
          type: tosca.policies.nfv.InstantiationLevels
          properties:
            levels:
              instantiation_level_1:
                description: Smallest size
                scale_info:
                  vdu1_aspect:
                    scale_level: 0
              instantiation_level_2:
                description: Largest size
                scale_info:
                  vdu1_aspect:
                    scale_level: 2
            default_level: instantiation_level_1

.. _request_parameters:

Sample request parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

``InstantiateVnfRequest`` allows Client to specify the
following common parameter for the v1 and v2 APIs.

+------------------------+----------------------------------------------------+
| Attribute name         | Parameter description                              |
+========================+====================================================+
| instantiationLevelId   | Set instantiation level for number of running Pod  |
+------------------------+----------------------------------------------------+

When using the Helm chart,
The value of ``additionalParams.helm_replica_values`` needs to be contained
in ``InstantiateVnfRequest``.
This parameter indicates the parameter name of the number of pods
described in the helm chart.
Client have to specify it according to the Helm chart used in the LCM.

Following shows a sample request body for v1 Instantiate:

.. code-block:: json

  {
    "flavourId": "simple",
    "instantiationLevelId": "instantiation_level_1",
    "additionalParams": {
      "namespace": "default",
      "use_helm": "true",
      "using_helm_install_param": [
        {
          "exthelmchart": "false",
          "helmreleasename": "vdu1",
          "helmparameter": [
            "key1=value1",
            "key2=value2"
            ],
          "helmchartfile_path": "Files/kubernetes/localhelm-0.1.0.tgz"
        }
      ],
      "helm_replica_values": {
        "vdu1_aspect": "replicaCount"
      }
      "vdu_mapping": {
        "VDU1": {
          "kind": "Deployment",
          "name": "vdu1-localhelm",
          "helmreleasename": "vdu1"
        }
      }
    },
    "vimConnectionInfo": [
      {
        "id": "817954e4-c321-4a31-ae06-cedcc4ddb85c",
        "vimId": "690edc6b-7581-48d8-9ac9-910c2c3d7c02",
        "vimType": "kubernetes"
      }
    ]
  }

.. note:: There is a difference between v1 and v2
  in the vimConnectionInfo data type.
  ``vimConnectionInfo.id`` exists in only v1.
  v2 vimConnectionInfo is map structure
  instead of including ``id`` parameter.

Support CNF instantiate/terminate in v2 API using Helm Chart
------------------------------------------------------------

This specification proposes supporting the Helm chart in V2 API.

.. note::

 The v1 API for CNF Instantiate/Terminate operations using the Helm
 Chart has already been supported according to the specification,
 "Support Helm Chart for Kubernetes VIM." [#HELMCHART_K8S]_

v2 API architecture for using Helm Chart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The v2 API has an architectural change from the v1 API.
In the v1 API architecture, Helm is installed on Kubernetes master node
and Tacker uses it via SSH.
However, this architecture complicated the authentication process.
It requires Tacker to manage two authentication points,
Kubernetes for using API directly and its Host for SSH access.

To address this issue, the v2 API architecture installs Helm inside VNFM.
Since this change unifies the interface between VNFM and VIM
into the Kubernetes API, it simplifies the authentication process.

The following shows the each architecture.

* v1 API architecture for using Helm Chart
   The diagram is described in :ref:`the previous section<instantiation>`

* v2 API architecture for using Helm Chart
   ::

                                                                         +------+ +------------+
                                                                         | VNFD | | Helm chart |
                                                                         |      | |            |
                                                                         +-+----+ ++-----------+
                                                                           |       |
                                                                         +-v-------v-+ +-----------------+
                                                                         |           | | Instantiation   |
                                                                         | CSAR      | | Request with    |
                                                                         |           | | additionalParam |
                                                                         +-----+-----+ +-----------+-----+
                                                                               |                   |
        +-----------------------+                                              |  1. Request with  |
        | CNF with Helm chart   |                                              |     Helm chart    |
        |                       |                     +--------------------------------------------------+
        |  +------+   +------+  |                     | Tacker Host            |                   |     |
        |  | Pod  |   | Pod  |  |                     |                     +--v-------------------v--+  |
        |  |      |   |      |  <-------+             |                     |                         |  |
        |  +------+   +------+  |       |             |                     |      TackerServer       |  |
        |                       |       |             |                     |                         |  |
        +-----------------------+       |             |                     +------+------------------+  |
                                        |             |                            |                     |
     +-------------------------------------------+    |                     +-------------------------+  |
     | Kubernetes cluster VNF           |        |    |                     |      |  TackerConductor |  |
     |                                  |        |    |                     |      |                  |  |
     |  +----------+  +-----------------------+  |    |                     |  +---v---------------+  |  |
     |  |  Worker  |  |        Master   |     |  |    |                     |  | VnflcmDriver      |  |  |
     |  |          |  |                 |     |  |    |                     |  |                   |  |  |
     |  |          |  |                 |     |  |    |                     |  +---+---------------+  |  |
     |  |          |  |                 |     |  |    |                     |      |                  |  |
     |  |          |  |                 |     |  |    |                     |  +---v---------------+  |  |
     |  |          |  |                 |     |  |    | 2. Operate Helm cli |  | Kubernetes        |  |  |
     |  |          |  |  +--------------+--+  |  |    | +--------------+--+ |  | InfraDriver       |  |  |
     |  |          |  |  | kube-apiserver  <------------+ Helm            | |  |   |               |  |  |
     |  |          |  |  +-----------------+  |  |    | +-----------------+ |  | +-v-----------+   |  |  |
     |  |          |  |                       |  |    | | Helm cli        <------+ Helm client |   |  |  |
     |  |          |  |                       |  |    | +-----------------+ |  | +-------------+   |  |  |
     |  |          |  |                       |  |    | | Helm Repository | |  |                   |  |  |
     |  |          |  |                       |  |    | +-----------------+ |  +-------------------+  |  |
     |  |          |  |                       |  |    |                     |                         |  |
     |  +----------+  +-----------------------+  |    |                     +-------------------------+  |
     |                                           |    |                                                  |
     +-------------------------------------------+    +--------------------------------------------------+


Instantiate CNF for v2 API using Helm Chart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The v2 API implementation follows the v1 API implementation
including the following process:

#. Check parameter
#. Register Helm repository or send Helm Chart files
#. Create container using Helm Chart
#. Get resource information and
   update `VnfInstance` in TackerDB

Terminate CNF for v2 API using Helm Chart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The v2 API implementation follows the v1 API implementation
including the following process:

#. Delete container using Helm Chart
#. Delete Helm repository or delete Helm Chart files
#. Update `VnfInstance` in TackerDB

Support for vimConnectionInfo.extra field
-----------------------------------------

This specification proposes adding following features.

+ Support the `openstack vim register`
  command with the config file
  (vim config) including ``extra`` parameter.
  It handles the `extra` field in the TackerDB.
+ Support the ``extra`` parameter specified in
  `InstantiateVnfRequest.vimConnectionInfo`
  when running CNF Instantiate with Helm chart in v1 API.

Vim config sample
~~~~~~~~~~~~~~~~~

The following shows a sample configuration file (vim config)
including the ``extra`` parameter
for the `openstack vim register` command.

.. code-block:: yaml

  auth_url: "https://192.168.121.47:6443"
  bearer_token: "eyJhbGciOiJSUzI1NiIsImtpZCI6Ild2VTJCWDRMc2poR0hTSDhmNGMtMjRxdThkcUw4MlozbV9kcXNpRmg0bzQifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tbjk2bDIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjFjODZmNzZjLWEwZTktNDBhNC05ZjcyLTMwMGY4YzJjYzY2MyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.D0vcn61G9cdzQvruTisbhR3LLkMghj3fqQDs8KNgJifR_OpbgeLqHuHRxS-WA9yJ5pM8hmMNpyHi5_6BFVOnRnBTiNYgXwrVxBL7R62vXeeBeWlY_072SaDwutbXvCIXo4yl1MTqpWRl3YuoeAb_Js-HJA2gCavymTAFcESlt8EZDtp-AN4_QN1eIPGlQcWAfVrFP5xgIMpDZNFjWCS2n7TKNbXJ3U-vksZ8sBdBYqRtzmOHrJCI6KI85LmXKWCxo5KSsq54JsIj4iDjS-yL5MOQ-ClAVOAlnyMH-_EmkpO25LKhuYPCIUxSy6XddUv7-zR3-nNk9T9ifl5Rhy8B8w"
  ssl_ca_cert: "None"
  project_name: "default"
  type: "kubernetes"
  extra:
    helm_info:
      masternode_ip:
      - "192.168.121.47"
      masternode_username: "helm_user"
      masternode_password: "helm_pass"

Input Parameter sample
~~~~~~~~~~~~~~~~~~~~~~

The following shows a sample input parameters
for v1 Instantiate including the ``vimConnectionInfo.extra``
for the `openstack vnflcm instantiate` command.
As described in :ref:`the previous section<request_parameters>`,
the difference between v1 and v2 is in the ``vimConnectionInfo``.

.. code-block:: json

  {
    "flavourId": "simple",
    "additionalParams": {
      "namespace": "default",
      "use_helm": "true",
      "using_helm_install_param": [
        {
          "exthelmchart": "false",
          "helmreleasename": "vdu1",
          "helmparameter": [
            "key1=value1",
            "key2=value2"
            ],
          "helmchartfile_path": "Files/kubernetes/localhelm-0.1.0.tgz"
        }
      ],
      "helm_replica_values": {
        "vdu1_aspect": "replicaCount"
      }
      "vdu_mapping": {
        "VDU1": {
          "kind": "Deployment",
          "name": "vdu1-localhelm",
          "helmreleasename": "vdu1"
        }
      }
    },
    "vimConnectionInfo": [
      {
        "id": "817954e4-c321-4a31-ae06-cedcc4ddb85c",
        "vimId": "690edc6b-7581-48d8-9ac9-910c2c3d7c02",
        "vimType": "kubernetes",
        "extra": {
          "helm_info": {
            "masternode_ip": [
              "192.168.121.47"
            ],
            "masternode_username": "helm_user",
            "masternode_password": "helm_pass"
          }
        }
      }
    ]
  }


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
 Hirofumi Noguchi <hirofumi.noguchi.rs@hco.ntt.co.jp>

Other contributors:
 Hideki Matsuda <matsuda.hideki1@fujitsu.com>

 Ayumu Ueha <ueha.ayumu@fujitsu.com>

 Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

 Yusuke Niimi <niimi.yusuke@fujitsu.com>

Work Items
----------

+ Add new unit and functional tests.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added
to cover cases required in this specification.

Documentation Impact
====================

None

References
==========

.. [#MGMT_DRIVER_DEPLOY_K8S_AND_CNF_WITH_HELM_1] https://docs.openstack.org/tacker/latest/user/mgmt_driver_deploy_k8s_and_cnf_with_helm.html#check-results-of-instantiation-operations
.. [#ETSI-SOL001] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/03.03.01_60/gs_NFV-SOL001v030301p.pdf
.. [#HELMCHART_K8S] https://specs.openstack.org/openstack/tacker-specs/specs/xena/helmchart-k8s-vim.html

