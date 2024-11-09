=====================================
Support Helm chart for Kubernetes VIM
=====================================

https://blueprints.launchpad.net/tacker/+spec/helmchart-k8s-vim

Problem description
===================

Tacker Wallaby release supports Kubernetes resource files as
Managed Container Infrastructure Object Package (MCIOP)
in VNF Lifecycle Management for CNF.
On the other hand, Helm chart should be also supported as MCIOP
due to the trend of cloud-native application development.

This specification proposes new interface for Kubernetes VIM with Helm chart.
It enables users to include Helm chart files in their VNF Packages and
instantiate, scale-out/in, and heal CNF.


Proposed Change
===============

When Users manage Kubernetes cluster as VNF instance with ETSI NFV-SOL003 VNF
Lifecycle Management, it must also update MgmtDriver to support
Helm chart.
Otherwise, Users need to install and configure Helm chart environment in
their Kubernetes cluster.

This spec describes how to change MgmtDriver sample in
Tacker repository [#K8S-MGMT-DRIVER]_
and what to be changed in CNF operations such as Instantiate, Scale, and Heal.

The following changes are required in MgmtDriver for Kubernetes cluster VNF:

#. Instantiate Kubernetes Cluster VNF

   + Add new logic to install Helm related packages in
     ``instantiate_end`` method.

   + Store Master nodes SSH connection info into ``VIM`` table and
     ``VnfInstance.vimConnectionInfo`` in ``instantiate_end`` method.

   .. note::

     HA Master nodes described in the spec "Support HA Kubernetes Master
     deployment with MgmtDriver" [#SPEC-HA-K8S]_ may not be supported due to
     the challenge of how to manage plural connection info.

#. Heal Master node in Kubernetes Cluster VNF

   + Add new logic to install Helm related packages in ``heal_end`` method.

#. Heal entire Kubernetes Cluster VNF

   + Store new Master nodes SSH connection info into ``VIM`` table and
     ``VnfInstance.vimConnectionInfo`` in ``heal_end`` method.

The following changes are required for CNF operations:

#. CNF common operations

   + Detects Helm chart mode according to
     ``InstantiateVnfRequest.vimConnectionInfo`` in Kubernetes InfraDriver.
   + Implement Helm chart client.

#. CNF Instantiate

   + Register Helm chart to Helm repository.
   + Call Helm chart client from Kubernetes InfraDriver.
   + Store deployed Kubernetes resources info in Helm chart to Database.

#. CNF Terminate

   + Deregister Helm chart from Helm repository.
   + Call Helm chart client from Kubernetes InfraDriver.

#. CNF Scale

   + Call Helm chart client from Kubernetes InfraDriver.

   .. note::

     The Scale operation may need to use Kubernetes PythonClient other than
     Helm chart client.
     The number of replicas may not be exposed in `values.yaml` in Helm chart.
     In this case, Tacker needs to store the same Database as
     the case of Kubernetes Python Client in Instantiate operation.

#. CNF Heal

   + Call Helm chart client from Kubernetes InfraDriver

   .. note::

     The Heal operation may need to use Kubernetes PythonClient other than
     Helm chart client.
     Helm cli doesn't support Heal operations.
     In this case, Tacker needs to store the same Database as the
     case of Kubernetes Python Client in Instantiate operation.


Instantiate Kubernetes Cluster VNF
-----------------------------------

::

                                       +--------------+ +---------+
                                       | Helm         | |         |
                                       | Install      | |  VNFD   |
                                       | Script       | |         |
                                       +-------+------+ +-+-------+
                                               |          |
                                               +-----v    v     +---------------+
                                                  +----------+  | Instantiation |
                                                  |          |  | Request       |
                                                  |   CSAR   |  | Additional    |
                                                  |          |  | Params        |
                                                  +----+-----+  +-+-------------+
                                                       |          |
                                                       |          |
                                                 +-----+----------+--------------+
                                                 |     v          v         VNFM |
                                                 |  +-------------------+        |
                                                 |  |   Tackerserver    |        |
                                                 |  +-------+-----------+        |
                                                 |          |                    |
                                                 |          v                    |
             2. Kubernetes Cluster               |  +----------------------+     |
                & Helm Installation              |  |    +-------------+   |     |
          +-------------+------------------------+--+----| MgmtDriver  |   |     |
          |             |                        |  |    +-------------+   |     |
  +-------|-------------|------------+           |  |                      |     |
  |       |             |            |           |  |                      |     |
  |  +----|------+  +---|-------+    |           |  |                      |     |
  |  |    v      |  |   v       |    |           |  |    +-------------+   |     |
  |  |  +------+ |  | +------+  |    | 1. Create |  |    |OpenStack    |   |     |
  |  |  |Worker| |  | |Master|  |<---------------+--+----|Infra Driver |   |     |
  |  |  +------+ |  | +------+  |    |    VMs    |  |    +-------------+   |     |
  |  |    VM     |  |   VM      |    |           |  |                      |     |
  |  +-----------+  +-----------+    |           |  |                      |     |
  +----------------------------------+           |  |      Tacker Conductor|     |
  +----------------------------------+           |  +----------------------+     |
  |       Hardware Resources         |           |                               |
  +----------------------------------+           +-------------------------------+


The diagram shows Instantiate operation of Kubernetes cluster VNF.
When MgmtDriver invokes ``instantiate_end``, following steps are added:

#. MgmtDriver uses a shell script to install Helm.

#. MgmtDriver add Master node access information to TackerDB as
   ``VIM`` and ``VnfInstance.vimConnectionInfo``.


Following sequence diagram describes the components involved and the flow of
install Helm with MgmtDriver operation:

.. image:: ./helmchart-k8s-vim/01.png

The procedure consists of the following steps as illustrated in above sequence.

#. Client sends an instantiate request.

#. It is basically the same with the spec "Support deploying Kubernetes
   cluster with MgmtDriver" [#SPEC-K8S-DEPLOY]_.

#. The following processes will be added in ``instantiate_end``.

   #. MgmtDriver installs Helm on the new Master nodes by a shell script.

      #. Access to Master nodes via SSH
      #. Copy the script files from "helm_installation_script_path"
         to the Master nodes.
      #. Run the scripts.

   #. MgmtDriver adds Master node access information to
      ``VnfInstance.vimConnectionInfo``.


Sample request parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following parameters are required in
``InstantiateVnfRequest`` for Helm chart support.

+--------------------------------------+---------------------------------------------------------+
| Attribute name                       | Parameter description                                   |
+======================================+=========================================================+
| helm_installation_script_path        | File path of the script file to install Helm.           |
+--------------------------------------+---------------------------------------------------------+

Following is a sample of request body:

.. code-block:: json

  {
    "flavourId": "ha_k8s_install",
    "extVirtualLinks": [
      {
        "id": "net0",
        "resourceId": "f0c82461-36b5-4d86-8322-b0bc19cda65f",
        "extCps": [
          {
            "cpdId": "CP1",
            "cpConfig": [
              {
                "cpProtocolData": [
                  {
                    "layerProtocol": "IP_OVER_ETHERNET"
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "additionalParams": {
      "lcm-operation-user-data": "./UserData/lcm_user_data.py",
      "lcm-operation-user-data-class": "SampleUserData",
      "k8s_cluster_installation_param": {
        "script_path": "Scripts/install_k8s_ha.sh",
        "vim_name": "kubernetes_vim_all_param",
        "master_node": {
          "aspect_id": "master_instance",
          "ssh_cp_name": "CP1",
          "username": "ubuntu",
          "password": "ubuntu",
          "pod_cidr": "192.168.3.0/16",
          "cluster_cidr": "10.199.187.0/24",
          "cluster_cp_name": "vrrp_CP"
        },
        "worker_node": {
          "aspect_id": "worker_instance",
          "ssh_cp_name": "CP2",
          "username": "ubuntu",
          "password": "ubuntu"
        },
        "proxy": {
          "http_proxy": "http://user1:password1@host1:port1",
          "https_proxy": "https://user2:password2@host2:port2",
          "no_proxy": "192.168.10.0/24,10.0.0.1"
        },
        "helm_installation_script_path": "Scripts/install_helm.sh"
      }
    },
    "vimConnectionInfo": [
      {
        "id": "8a3adb69-0784-43c7-833e-aab0b6ab4470",
        "vimId": "8d8373fe-6977-49ff-83ac-7756572ed186",
        "vimType": "openstack"
      }
    ]
  }


Sample Database table for Helm chart support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following parameters are stored in ``extra`` field of
``VnfInstance.vimConnectionInfo`` as access info to Master node.
This ``extra`` field is defined as key/value pair in
ETSI NFV-SOL003 v2.6.1 [#ETSI-SOL003]_.

+----------------------------+-----------------------------------------------------------+
| Attribute name             | Parameter description                                     |
+============================+===========================================================+
|helm_info                   | Access information to install Helm in Master nodes.       |
+----------------------------+-----------------------------------------------------------+
|> masternode_ip             | IP address of Master node.                                |
+----------------------------+-----------------------------------------------------------+
|> masternode_username       | Username for SSH login to Master node.                    |
+----------------------------+-----------------------------------------------------------+
|> masternode_password       | Password for SSH login to Master node.                    |
+----------------------------+-----------------------------------------------------------+


Sample of the table stored in the database:

.. code-block:: json

  {
    "vim_type": "kubernetes",
    "access_info": {
      "auth_url":"http://123.124.64.6:8443",
      "username": "some-username",
      "password": "some-password",
      "bearer_token": "value of bearer token",
      "ssl_ca_cert_hash": "hash value of ssl ca certification",
      "certificate_key": "value of certificate key"
    },
    "interface_info": {
    },
    "extra": {
      "helm_info": {
          "masternode_ip": "192.168.100.100",
          "masternode_username": "user1",
          "masternode_password": "password",
      }
    }
  }


Heal Kubernetes Cluster VNF for Helm chart support
--------------------------------------------------

Required change is limited in ``heal_end`` method of MgmtDriver.
Tacker supports VNFC Heal operation with SOL002 and VNF Heal operation
with SOL003.
In both cases, a similar process in Instantiate operation is added.

Heal Master node with SOL002
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following processes will be added in ``heal_end``.

#. MgmtDriver installs Helm on the new Master nodes by a shell script.

   #. Access to Master nodes via SSH
   #. Copy the script files from "helm_installation_script_path" to
      the Master nodes.
   #. Run the scripts.

#. MgmtDriver deletes access information of healed Master nodes and
   adds new ones to ``VnfInstance.vimConnectionInfo``.

Heal entire Kubernetes Cluster VNF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This case follows the same logic in Terminate and Instantiate operations.
It is worth noting that ``VIM`` and ``VnfInstance.vimConnectionInfo``
table should be updated with new Kubernetes Cluster information.


Instantiate CNF with Helm chart
--------------------------------

The diagram below shows the Instantiate operation with Helm chart:

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
     +-----------------------+                                                    |  1. Request with  |
     | CNF with Helm chart   |                                                    |     Helm chart    |
     |                       |                                              +-------------------------------+
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
  |  |                       |  |                 |     |  |                |  |  |                   |  |  |
  |  |                       |  |  +--------------+--+  |  |                |  |  +---+---------------+  |  |
  |  |                       |  |  | kubectl         |  |  |                |  |      |                  |  |
  |  |                       |  |  +--------------^--+  |  |                |  |  +---v---------------+  |  |
  |  |                       |  |                 |     |  |                |  |  | Kubernetes        |  |  |
  |  |                       |  |  +--------------+--+  |  |                |  |  | InfraDriver       |  |  |
  |  |                       |  |  | Helm            |  |  | 3. Helm cli    |  |  |                   |  |  |
  |  |                       |  |  +-----------------+  |  |    via SSH     |  |  |  +-------------+  |  |  |
  |  |                       |  |  | Helm cli        <-------+-----------------------+ Helm client |  |  |  |
  |  |                       |  |  +-----------------+  |  | |              |  |  |  +-------------+  |  |  |
  |  |                       |  |  | Helm Repository <-------+              |  |  |                   |  |  |
  |  |                       |  |  +-----------------+  |  | 2. Register    |  |  +-------------------+  |  |
  |  |                       |  |                       |  |    repository  |  |                         |  |
  |  +-----------------------+  +-----------------------+  |    with Helm   |  +-------------------------+  |
  |                                                        |    cli via SSH |                               |
  +--------------------------------------------------------+                +-------------------------------+


#. The KubernetesInfraDriver registers Helm charts using Helm cli to
   the Helm repository.
#. The KubernetesInfraDriver creates Kubernetes resource using Helm cli.

Following sequence diagram describes CNF instantiation with Helm chart:

.. image:: ./helmchart-k8s-vim/02.png


#. The Client sends an instantiate request.

#. No changes from existing implementation until Kubernetes
   InfraDriver is invoked.

#. The Kubernetes InfraDriver performs the following steps.

   #. Determine "use_helm" parameter in the ``InstantiateVnfRequest``.

   #. Get Master node access information from
      ``VnfInstance.vimConnectionInfo.extra`` in Tacker Database.

   #. (Optional: "exthelmchart" == "false") Get Helm chart from
      VNF Package and forward it to the Master node.

      .. code-block::

         scp /<helmchartfile_path> <masternode username>@<masternode_ip>:/var/tacker/helm/<vnf_instance_id>

      .. note::

         + <helmchartfile_path>: Path of Helm chart files in the request.
         + <masternode_username>: Username of Master node for SSH login
           stored in ``VnfInstance.vimConnectionInfo``.
         + <masternode_ip>: IP address of Master node stored in
           ``VnfInstance.vimConnectionInfo``.
         + <vnf_instance_id>: ID of VNF instance provided in
           TackerAPI requests.

      Extract the forwarded package file on Master node.

      .. code-block::

         tar -xzf /var/tacker/helm/<vnf_instance_id>/<chartfilepackage>

      .. note::
         + <chartfilepackage>: Forwarded ``.tgz`` package file name, which will be
           obtained from <helmchartfile_path>.

   #. (Optional: "exthelmchart" == "true") Get target Helm chart from repository.

      .. code-block::

         helm repo add <helmrepositoryname> <repositoryURL>

      .. note::
         + <helmrepositoryname>: Directory name specified as the name of
           repository. This parameter is provided by "helmrepositoryname" field
           in ``additionalParams``.
         + <repositoryURL>: This parameter specifies "exthelmrepo_url"
           of request parameter or URL of local repository otherwise.

   #. Instantiate CNF via Helm cli.

      If "exthelmchart" is "true",

      .. code-block::

         helm install <helmreleasename> <helmrepositoryname>/<helmchartname> --namespace <namespace> <helmparameter>

      If "exthelmchart" is "false",

      .. code-block::

         helm install <helmreleasename> /var/tacker/helm/<vnf_instance_id>/<extracted_package>

      .. note::

         + <namespace>: This parameter is obtained from the "namespace"
           of request parameter. If it is not set in the "namespace" of
           request parameter, this parameter is not set.
         + <helmchartname>: This parameter is obtained from the "helmchartname"
           of the request parameter.
         + <helmreleasename>: This parameter is obtained from the
           "helmreleasename" of request parameter and set.
         + <helmparameter>: This parameter is obtained from the
           "helmparameter" of  request parameter and set. Those parameters must
           be added with ``--set`` flag in ``helm install`` cli command.
         + <extracted_package>: This parameter will be a directory name
           extracted from <chartfilepackage>.

   #. Get Kubernetes resource files.

      .. code-block::

         helm get manifest <helmreleasename>

      .. note::

         + <helmreleasename>: This parameter is obtained from the
           "helmreleasename" of request parameter and set.

   #. Save Kubernetes resource in TackerDB.

      .. note::

         The data table should be generated in the same manner
         with Python client.

   #. Get and update the status of deployed resources.


Request data for CNF instantiate using Helm chart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following parameters will be required to instantiate CNF with Helm chart.
These are specified in ``additionalParams``, which is defined as
KeyValuePairs in ETSI NFV-SOL003 v2.6.1 [#ETSI-SOL003]_.

+----------------------------+-----------+-----------------------------------------------------------+
| Attribute name             | Data type | Parameter description                                     |
+============================+===========+===========================================================+
|namespace                   | String    | Namespace to deploy Kubernetes resources.                 |
|                            |           | If absent, the value in Helm chart is used as default.    |
+----------------------------+-----------+-----------------------------------------------------------+
|use_helm                    | Boolean   | If "true", Kubernetes InfraDriver utilizes Helm client,   |
|                            |           | otherwise, Kubernetes Python client is used.              |
|                            |           | true: with Helm, false: without Helm                      |
+----------------------------+-----------+-----------------------------------------------------------+
|using_helm_install_param    | Array     | Parameters for the step related to Helm chart.            |
|                            |           | Shall be present if "use_helm" is "true".                 |
+----------------------------+-----------+-----------------------------------------------------------+
|> exthelmchart              | Boolean   | If true, Helm chart is not in VNF Package.                |
|                            |           | true: external Helm chart, false: in VNF Package          |
+----------------------------+-----------+-----------------------------------------------------------+
|> helmchartfile_path        | String    | Path of Helm chart files in VNF Package.                  |
|                            |           | Shall be present if "exthelmchart" is "false".            |
+----------------------------+-----------+-----------------------------------------------------------+
|> helmreleasename           | String    | Name of release as instance of Helm chart.                |
+----------------------------+-----------+-----------------------------------------------------------+
|> helmparameter             | Array     | Parameters of KeyValuePairs,                              |
|                            |           | which is specified during Helm installation.              |
+----------------------------+-----------+-----------------------------------------------------------+
|> helmrepostitoryname       | String    | Helm repository name.                                     |
|                            |           | Shall be present if "exthelmchart" is "true".             |
+----------------------------+-----------+-----------------------------------------------------------+
|> helmchartname             | String    | Helm chart name.                                          |
|                            |           | Shall be present if "exthelmchart" is "true".             |
+----------------------------+-----------+-----------------------------------------------------------+
|> exthelmrepo_url           | String    | URL of external Helm repository.                          |
|                            |           | Shall be present if "exthelmchart" is "true".             |
+----------------------------+-----------+-----------------------------------------------------------+

The following sample shows a request body with the case of exthelmchart is "true":

.. code-block:: json

  {
    "additionalParams": {
      "namespace": "namespaceA",
      "use_helm": "true",
      "using_helm_install_param": [
        {
          "exthelmchart": "true",
          "helmreleasename": "myrelease",
          "helmparameter": [
            "key1=value1",
            "key2=value2"
            ],
          "helmrepositoryname": "mychart",
          "helmchartname": "example",
          "exthelmrepo_url": "http://helmrepo.example.com/sample-charts"
        }
      ]
    }
  }

The following sample shows a request body with the case of exthelmchart is "false":

.. code-block:: json

  {
    "additionalParams": {
      "namespace": "namespaceA",
      "use_helm": "true",
      "using_helm_install_param": [
        {
          "exthelmchart": "false",
          "helmchartfile_path": "Files/kubernetes/example-0.1.0.tgz",
          "helmreleasename": "myrelease",
          "helmparameter": [
            "key1=value1",
            "key2=value2"
          ]
        }
      ]
    }
  }


Terminate CNF with Helm chart
-----------------------------

In the Terminate operation for CNF, Kubernetes InfraDriver performs
the following steps to deregister Helm chart from repository and to
delete Kubernetes resources.
In other parts, no change is required.

#. Get Helm chart related information from ``VnfInstance.vimConnectionInfo``.

#. Delete Kubernetes resources via Helm cli.

   .. code-block::

      helm uninstall <helmreleasename>

   .. note::

      + <helmreleasename>: This parameter is obtained from the
        "Additional Params" table in TackerDB.

      **Discussion:** It might be better to use other tables because
      ``additionalParams`` should not be in Tacker DB
      according to ETSI NFV-SOL003 ``VnfInstance.instantiatedVnfInfo``.


#. (Optional: "exthelmchart" == "true") Delete the Helm repository.

   .. code-block::

      helm repo remove <helmrepositoryname>

   .. note::

      **Discussion:** It might be better to use other tables because
      ``additionalParams`` should not be in Tacker DB
      according to ETSI NFV-SOL003 ``VnfInstance.instantiatedVnfInfo``.

#. KubernetesInfraDriver deletes Helm chart. This processing is executed
   if "exthelmchart" of TackerDB's "Additional params" table is "false".

   .. code-block::

      rm -f /var/tacker/helm/<vnf_instance_id>


Data model impact
-----------------

Helm chart support described in this spec adds ``extra`` column
into ``vims`` table as type ``json``.

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
+ Implement MgmtDriver to support:

  + Provide a sample script to be executed to install Helm related packages
    when instantiate Kubernetes Cluster VNF and when heal Master node VNF.
  + Store Master nodes SSH connection info when instantiate Kubernetes
    cluster VNF and when heal entire Kubernetes cluster VNF.

+ Implement Kubernetes InfraDriver to support:

  + Register Helm chart to Helm repository when CNF Instantiate.
  + DeRegister Helm chart to Helm repository when CNF Terminate.
  + Call Helm chart client when CNF Instantiate, scale, heal and terminate.
  + Store deployed Kubernetes resources info in Helm chart to Database
    when CNF Instantiate.

+ Add new unit and functional tests.

Dependencies
============

+ Instantiate operation for the Kubernetes cluster

  Depends on spec "Support deploying Kubernetes cluster with
  MgmtDriver" [#SPEC-K8S-DEPLOY]_.

+ Scale operation for the Kubernetes cluster

  Depends on spec "Support scaling Kubernetes Worker-nodes with
  MgmtDriver" [#SPEC-K8S-SCALE]_.

+ Heal operation for the Kubernetes cluster

  Depends on spec "Support Healing Kubernetes Master/Worker-nodes with
  MgmtDriver" [#SPEC-K8S-HEAL]_.

+ Instantiate operation for the Kubernetes cluster

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

Complete user guide will be added to explain CNF instantiation
using Helm chart.

References
==========

.. [#K8S-MGMT-DRIVER] https://opendev.org/openstack/tacker/src/branch/master/samples/mgmt_driver/kubernetes_mgmt.py
.. [#SPEC-HA-K8S] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-ha-k8s.html
.. [#SPEC-K8S-DEPLOY] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-cluster.html
.. [#ETSI-SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_NFV-SOL003v020601p.pdf
.. [#SPEC-K8S-SCALE] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-scale.html
.. [#SPEC-K8S-HEAL] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-heal.html
