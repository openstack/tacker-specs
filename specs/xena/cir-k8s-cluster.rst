======================================================================
Support Docker private registry for Kubernetes cluster with MgmtDriver
======================================================================

https://blueprints.launchpad.net/tacker/+spec/cir-k8s-cluster

Problem description
===================

The Tacker Wallaby release supports spec "Support deploying Kubernetes
cluster with MgmtDriver" [#SPEC-K8S-CLUSTER]_.
Deployed Kubernetes cluster supports only Images registered in the Docker
public registry but doesn't support Images in Docker private registry.
This specification adds functionality to enable the use of Docker private
registry images in a Kubernetes Cluster environment.
This specification assumes spec "Support deploying Kubernetes cluster with
MgmtDriver" [#SPEC-K8S-CLUSTER]_.

Proposed change
===============

The following operations are supported:

#. Deploy Docker private registry VNF for Kubernetes cluster before deploying
   Kubernetes cluster VNF.

#. Deploy Kubernetes cluster VNF that can support both the Docker private
   registry created above and any others created outside of Tacker.

The LCM operations for Docker private registry VNF requires the following
changes:

+ Instantiate operation with MgmtDriver to install Docker private registry.

+ Heal operation with MgmtDriver to re-install Docker private registry.

.. note::

  + Scale operation is not supported.
  + Terminate operation is out of scope in this spec. There is no specific
    processes in the termination of Docker private registry VNF, so it is
    already supported by existing implementation.

The LCM operations for Kubernetes cluster VNF requires the following changes:

+ Instantiate operation for Kubernetes cluster with
  MgmtDriver [#SPEC-K8S-CLUSTER]_.

  Changes: MgmtDriver configures connections to Docker private registries on
  newly created all Master/Worker VMs.

+ Scale-out operation for Kubernetes cluster Worker-nodes with
  MgmtDriver [#SPEC-K8S-SCALE]_.

  Changes: MgmtDriver configures connections to Docker private registries on
  newly created Worker VMs.

+ Heal operation for the entire Kubernetes cluster with
  MgmtDriver [#SPEC-K8S-HEAL]_.

  Changes: MgmtDriver configures connections to Docker private registries on
  the created all Master/Worker VMs.

+ Heal operation for a single node (Master/Worker) in Kubernetes cluster with
  MgmtDriver [#SPEC-K8S-HEAL]_.

  Changes: MgmtDriver configures connections to Docker private registries on
  the created Master/Worker VM.


Deploy Docker private registry VNF for Kubernetes cluster
---------------------------------------------------------

Deploy the Docker private registry for Kubernetes cluster as a VNF.
The diagram below shows creating VM and set up Docker private registry:

::

                                      +--------------+ +---------+
                                      | Docker Image | |  VNFD   |
                                      | (Optional)   | |         |
                                      +------------+-+ +-+-------+
                                                   |     |
                                                   v     v    +---------------+
                                                +----------+  | Instantiation |
                                                |          |  | Request with  |
                                                |   CSAR   |  | Additional    |
                                                |          |  | Params        |
                                                +----+-----+  +-+-------------+
                                                     |          | 1. Instantiate VNF
                                                     |          |
                                               +-----+----------+-------------+
                                               |     v          v        VNFM |
                                               |  +-------------------+       |
                                               |  |   Tacker-server   |       |
                                               |  +-------+-----------+       |
                                               |          |                   |
                                               |          v                   |
  +--------------------------+ 4. Run Private  |  +------------------------+  |
  |                          |    registry     |  |                        |  |
  |  +--------------------+  |    container    |  |    +--------------+    |  |
  |  | Docker container   |<-+-----------------+--+----+              |    |  |
  |  | (Private registry) |  |                 |  |    |  MgmtDriver  |    |  |
  |  +--------------------+  | 3. Docker       |  |    |              |    |  |
  |  +--------------------+  |    Installation |  |    |              |    |  |
  |  |       Docker       |<-+-----------------+--+----+              |    |  |
  |  +--------------------+  |                 |  |    +--------------+    |  |
  |                          |                 |  |    +--------------+    |  |
  |                          | 2. Create VM    |  |    | OpenStack    |    |  |
  |                          |<----------------+--+----+ Infra Driver |    |  |
  |                          |                 |  |    +--------------+    |  |
  |            VM            |                 |  |                        |  |
  +--------------------------+                 |  |    Tacker-conductor    |  |
  +--------------------------+                 |  +------------------------+  |
  |    Hardware Resources    |                 |                              |
  +--------------------------+                 +------------------------------+


VNFD for Docker private registry VNF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One VDU and one or more CPs, and the interface definitions of
``instantiate_end`` and ``heal_end`` are required in VNFD as the
following sample:

.. code-block:: yaml

   node_templates:
    VNF:
      ...
      interfaces:
        Vnflcm:
          ...
          instantiate_end:
            implementation: mgmt-drivers-private-registry
          heal_end:
            implementation: mgmt-drivers-private-registry
      artifacts:
        mgmt-drivers-private-registry:
          description: Management driver for Docker private registry
          type: tosca.artifacts.Implementation.Python
          file: Scripts/private_registry_mgmt.py

    PrivateRegistryVDU:
      type: tosca.nodes.nfv.Vdu.Compute
      ...

    CP1:
      type: tosca.nodes.nfv.VduCp
      ...
      requirements:
        - virtual_binding: PrivateRegistryVDU
      ...


Request parameters for Instantiate Docker private registry VNF operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

User gives ``InstantiateVnfRequest`` data type defined in ETSI NFV-SOL003
v2.6.1 [#NFV-SOL003]_ as request parameters.
It is basically the same parameters as described in the spec "REST API for
VNF based on ETSI NFV-SOL specification" [#SPEC-SOL-REST-API]_.
User can use the following ``additionalParams``:

+-------------------------------------+-------------+-------------------------------------------------------------+
| Attribute name                      | Cardinality | Parameter description                                       |
+=====================================+=============+=============================================================+
| private_registry_installation_param | 1           | Configuration for private registry installation.            |
+-------------------------------------+-------------+-------------------------------------------------------------+
| >ssh_cp_name                        | 1           | CP name that MgmtDriver uses when SSH/SFTP access to        |
|                                     |             | the Private registry VM.                                    |
+-------------------------------------+-------------+-------------------------------------------------------------+
| >ssh_username                       | 1           | User name that MgmtDriver uses when SSH/SFTP access to      |
|                                     |             | the Private registry VM.                                    |
+-------------------------------------+-------------+-------------------------------------------------------------+
| >ssh_password                       | 1           | User password that MgmtDriver uses when SSH/SFTP access to  |
|                                     |             | the Private registry VM.                                    |
+-------------------------------------+-------------+-------------------------------------------------------------+
| >image_path                         | 0..1        | Optional. Path of the Docker image file in the VNF Package  |
|                                     |             | for the Private registry container to run on Docker.        |
|                                     |             | If this attribute is omitted, the image for the Private     |
|                                     |             | registry container is pulled from the Docker public         |
|                                     |             | registry.                                                   |
|                                     |             | If the Private registry VM is unable to connect to          |
|                                     |             | the Docker public registry, put the file created using      |
|                                     |             | "docker save" command into the VNF Package and specify      |
|                                     |             | the path of the file in this attribute.                     |
+-------------------------------------+-------------+-------------------------------------------------------------+
| >port_no                            | 0..1        | Optional. The default value is 5000.                        |
|                                     |             | TCP port number that provides the Private registry service. |
+-------------------------------------+-------------+-------------------------------------------------------------+

The following is a sample of body provided in the Instantiate VNF request
`POST /vnflcm/v1/vnf_instances/{vnfInstanceId}/instantiate`:

.. code-block:: json

    {
      "flavourId": "simple",
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
        "private_registry_installation_param": {
          "ssh_cp_name": "CP1",
          "ssh_username": "ubuntu",
          "ssh_password": "ubuntu",
          "image_path": "Files/images/private_registry.tar"
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


Sequence for Instantiate Docker private registry VNF operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/01.png

The procedure consists of the following steps as illustrated in
above sequence:

#. Client sends a POST Instantiate VNF request.

#. It is basically the same sequence as described in the "2) Flow of
   Instantiation of
   a VNF instance" chapter of spec "REST API for VNF based on ETSI NFV-SOL
   specification" [#SPEC-SOL-REST-API]_,
   except for the MgmtDriver.

#. The following processes are performed in ``instantiate_end``.

   #. MgmtDriver gets IP address of Private registry VM from Heat.
   #. MgmtDriver installs Docker on Private registry VM.
   #. MgmtDriver transfers a Docker image file to Private registry VM if
      specified by request parameter "image_path".
   #. MgmtDriver uses a Docker image to run Private registry container
      on Docker.

      MgmtDriver uses a command like the following to start the Private
      registry container:

      .. code-block::

         sudo docker run -d -p 5000:5000 -v /home/ubuntu/registry:/var/lib/registry --restart=always --name private_registry registry:latest

      .. note::

        The Docker image name for the Private registry container is
        ``registry``.
        If the request parameter "image_path" is specified, "docker load"
        command is used to load the ``registry`` image from the transferred
        image file.
        If the request parameter "image_path" is omitted, "docker pull"
        command is used to pull the ``registry`` image from the Docker
        public registry.

      .. note::

        The above sample command assumes that the OS of the Private
        registry VM is Ubuntu 20.04.


Heal operation for Docker private registry VNF with MgmtDriver
--------------------------------------------------------------

The diagram below shows the Heal VNF operation for Docker private
registry VNF:

::

                                                    +--------------+
                                                    | Heal Request |
                                                    +-+------------+
                                                      | 1. Heal VNF
                                                      |
                                                +-----+------------------------+
                                                |     v                   VNFM |
                                                |  +-------------------+       |
                                                |  |   Tacker-server   |       |
                                                |  +-------+-----------+       |
                                                |          |                   |
  +--------------------------+                  |          v                   |
  |                          | 5. Run Private   |  +------------------------+  |
  |                          |    registry      |  |                        |  |
  |  +--------------------+  |    container     |  |    +--------------+    |  |
  |  | Docker container   |<-+------------------+--+----+              |    |  |
  |  | (Private registry) |  |                  |  |    |  MgmtDriver  |    |  |
  |  +--------------------+  | 4. Docker        |  |    |              |    |  |
  |  +--------------------+  |    Installation  |  |    |              |    |  |
  |  |       Docker       |<-+------------------+--+----+              |    |  |
  |  +--------------------+  |                  |  |    +--------------+    |  |
  |                          | 3. Create new VM |  |    +--------------+    |  |
  |            VM            |<-----------------+--+----+ OpenStack    |    |  |
  +--------------------------+                  |  |    | Infra Driver |    |  |
                               2. Delete     +--+--+----+              |    |  |
  +--------------------------+    failed VM  |  |  |    +--------------+    |  |
  |            VM            |<--------------+  |  |                        |  |
  +--------------------------+                  |  |    Tacker-conductor    |  |
  +--------------------------+                  |  +------------------------+  |
  |    Hardware Resources    |                  |                              |
  +--------------------------+                  +------------------------------+


VNFD for Heal operation
^^^^^^^^^^^^^^^^^^^^^^^

Same as "VNFD for Docker private registry VNF" chapter.

Request parameters for Heal Docker private registry VNF operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same parameters as described in the spec "REST API for VNF based on
ETSI NFV-SOL specification" [#SPEC-SOL-REST-API]_.

Sequence for Heal Docker private registry VNF operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/02.png

The procedure consists of the following steps as illustrated in
above sequence:

#. Client sends a POST Heal VNF request.

#. It is basically the same sequence as described in the "3) Flow of Heal
   of a VNF instance"
   chapter of spec "REST API for VNF based on ETSI NFV-SOL
   specification" [#SPEC-SOL-REST-API]_,
   except for the MgmtDriver.

#. The following processes are performed in ``heal_end``.

   #. MgmtDriver gets IP address of the new Private registry VM from Heat.
   #. MgmtDriver gets ``additionalParams`` of Instantiate VNF request from
      VnfInstance(Tacker DB).
   #. MgmtDriver installs Docker on the new Private registry VM.
   #. MgmtDriver transfers a Docker image file to the new Private registry VM
      if specified by Instantiate VNF request parameter "image_path".
   #. MgmtDriver uses a Docker image to run the Private registry container
      on Docker.


Deploy Kubernetes cluster VNF that can connect to Docker private registries
---------------------------------------------------------------------------

Add the function to connect to Docker private registries based on
spec "Support deployment Kubernetes cluster with
MgmtDriver" [#SPEC-K8S-CLUSTER]_.

The diagram below shows creating Kubernetes cluster and configure
connections to Docker private registries:

::

                                         +---------+ +---------+
                                         | Cluster | |         |
                                         | Install | |  VNFD   |
                                         | Script  | |         |
                     +----------------+  +-------+-+ +-+-------+
                     | CA certificate +--+       |     |
                     +----------------+  |       v     v
                      +---------------+  |    +----------+  +---------------+
                      | LCM operation |  +--->|          |  | Instantiation |
                      | UserData      +------>|   CSAR   |  | Request with  |
                      +---------------+       |          |  | Additional    |
                         +------------+  +--->|          |  | Params        |
                         | Heat       |  |    +----+-----+  +-+-------------+
                         | Template   +--+         |          | 1. Instantiate VNF
                         | (Base HOT) |            |          |
                         +------------+      +-----+----------+-------------+
                                             |     v          v        VNFM |
                                             |  +------------------+        |
                                             |  |   Tacker-server  |        |
                                             |  +-------+----------+        |
          3. Kubernetes Cluster              |          |                   |
             Installation                    |          v                   |
          4. Configure connections           |  +------------------------+  |
             to Docker private registries    |  |    +--------------+    |  |
          +-------------+--------------------+--+----+  MgmtDriver  |    |  |
          |             |                    |  |    +--------------+    |  |
  +-------+-------------+--------+           |  |                        |  |
  |       |             |        |           |  |                        |  |
  |  +----+-----+  +----+-----+  |           |  |                        |  |
  |  |    v     |  |    v     |  |           |  |    +--------------+    |  |
  |  | +------+ |  | +------+ |  |           |  |    | OpenStack    |    |  |
  |  | |Worker| |  | |Master| |<-+-----------+--+----+ Infra Driver |    |  |
  |  | +------+ |  | +------+ |  | 2. Create |  |    +--------------+    |  |
  |  |    VM    |  |    VM    |  |    VMs    |  |                        |  |
  |  +----------+  +----------+  |           |  |                        |  |
  +------------------------------+           |  |    Tacker-conductor    |  |
  +------------------------------+           |  +------------------------+  |
  |      Hardware Resources      |           |                              |
  +------------------------------+           +------------------------------+


VNFD for Kubernetes cluster VNF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from user guide "How to use Mgmt Driver for deploying Kubernetes
Cluster" [#USER-GUIDE-K8S-CLUSTER]_.


Request parameters with Docker private registries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the following attributes to ``additionalParams`` described in the user
guide "How to use Mgmt Driver for deploying Kubernetes
Cluster" [#USER-GUIDE-K8S-CLUSTER]_.

+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| Attribute name                    | Cardinality | Parameter description                                                               |
+===================================+=============+=====================================================================================+
| k8s_cluster_installation_param    | 1           | Configuration for Kubernetes cluster installation.                                  |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >private_registry_connection_info | 0..N        | Optional. Configuring to connect to Docker private                                  |
|                                   |             | registries.                                                                         |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>connection_type                 | 1           | | Type of connection. Set one of the following values.                              |
|                                   |             | | 0 : HTTP, 1 : HTTPS                                                               |
|                                   |             | | Set to 0 if connecting to the deployed Docker private registry VNF                |
|                                   |             |   or a Docker private registry outside of Tacker over HTTP.                         |
|                                   |             | | Set to 1 if connecting to a Docker private registry outside of Tacker over HTTPS. |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>server                          | 1           | Server name of the Docker private registry to connect to.                           |
|                                   |             | For example, "192.168.0.10:5000"                                                    |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>username                        | 0..1        | Optional. Username to log in to the Docker private registry.                        |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>password                        | 0..1        | Optional. Password to log in to the Docker private registry.                        |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>certificate_path                | 0..1        | Optional. The path of the CA certificate file to use for                            |
|                                   |             | HTTPS connection.                                                                   |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+
| >>hosts_string                    | 0..1        | Optional. String to add to /etc/hosts.                                              |
|                                   |             | The base Kubernetes cluster environment does not have a                             |
|                                   |             | DNS server and must be added to /etc/hosts.                                         |
|                                   |             | The value consists of "<IP address> <FQDN>".                                        |
|                                   |             | For example, "192.168.0.20 registry.example.com"                                    |
+-----------------------------------+-------------+-------------------------------------------------------------------------------------+

The following is a sample of body provided in the Instantiate VNF request
`POST /vnflcm/v1/vnf_instances/{vnfInstanceId}/instantiate`:

.. code-block:: json

    {
      "flavourId": "simple",
      "additionalParams": {
        "k8s_cluster_installation_param": {
          "script_path": "Scripts/install_k8s_cluster.sh",
          "vim_name": "kubernetes_vim",
          "master_node": {
            "aspect_id": "master_instance",
            "ssh_cp_name": "masterNode_CP1",
            "nic_cp_name": "masterNode_CP1",
            "username": "ubuntu",
            "password": "ubuntu",
            "pod_cidr": "192.168.3.0/24",
            "cluster_cidr": "10.199.187.0/24",
            "cluster_cp_name": "masterNode_CP1"
          },
          "worker_node": {
            "aspect_id": "worker_instance",
            "ssh_cp_name": "workerNode_CP2",
            "nic_cp_name": "workerNode_CP2",
            "username": "ubuntu",
            "password": "ubuntu"
          },
          "proxy": {
            "http_proxy": "http://user1:password1@host1:port1",
            "https_proxy": "https://user2:password2@host2:port2",
            "no_proxy": "192.168.246.0/24,10.0.0.1,registry.example.com",
            "k8s_node_cidr": "192.168.0.0/24"
          },
          "private_registry_connection_info": [
            {
              "connection_type": "0",
              "server": "192.168.0.10:5000"
            },
            {
              "connection_type": "1",
              "server": "registry.example.com",
              "username": "user01",
              "password": "user01",
              "certificate_path": "Files/registries/ca.crt",
              "hosts_string": "192.168.0.20 registry.example.com"
            }
          ]
        },
        "lcm-operation-user-data": "./UserData/k8s_cluster_user_data.py",
        "lcm-operation-user-data-class": "KubernetesClusterUserData"
      },
      "extVirtualLinks": [
        {
          "id": "net0_master",
          "resourceId": "f0c82461-36b5-4d86-8322-b0bc19cda65f",
          "extCps": [
            {
              "cpdId": "masterNode_CP1",
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
        },
        {
          "id": "net0_worker",
          "resourceId": "f0c82461-36b5-4d86-8322-b0bc19cda65f",
          "extCps": [
            {
              "cpdId": "workerNode_CP2",
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
      "vimConnectionInfo": [
        {
          "id": "8a3adb69-0784-43c7-833e-aab0b6ab4470",
          "vimId": "8d8373fe-6977-49ff-83ac-7756572ed186",
          "vimType": "openstack"
        }
      ]
    }


Sequence for Instantiate Kubernetes cluster VNF with Docker private registries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/03.png

The procedure consists of the following steps as illustrated in
above sequence.

#. Client sends a POST Instantiate VNF request.

#. It is basically the same sequence as described in spec "Support deployment
   Kubernetes cluster with MgmtDriver" [#SPEC-K8S-CLUSTER]_,
   except for following additional processes.

#. The following processes are added to ``instantiate_end``.

   #. MgmtDriver transfers CA certificate files to all Master/Worker VMs if
      specified by request parameter.
   #. MgmtDriver configure connections to the Docker private registries on all
      Master/Worker VMs.


Scale-out operation for Kubernetes cluster Worker-nodes with MgmtDriver
-----------------------------------------------------------------------

Add the function to connect to Docker private registries based on
spec "Support scaling Kubernetes Worker-nodes with
Mgmtdriver" [#SPEC-K8S-SCALE]_.

The diagram below shows Scale-out VNF operation:

::

                                                             +---------------+
                                                             | Scale Request |
                                                             +--+------------+
                                                                | 1. Scale VNF
                                                                |    (Scale-out)
                                               +----------------+------------+
                                               |                v       VNFM |
                                               |  +------------------+       |
                                               |  |   Tacker-server  |       |
                                               |  +-------+----------+       |
               3. Kubernetes Cluster           |          |                  |
                  Installation                 |          v                  |
               4. Configure connections        |  +-----------------------+  |
                  to Docker private registries |  |    +-------------+    |  |
                        +----------------------+--+----+ MgmtDriver  |    |  |
                        |                      |  |    +-------------+    |  |
  +---------------------+--------+             |  |                       |  |
  |                     |        |             |  |                       |  |
  |  +----------+  +----+-----+  |             |  |                       |  |
  |  |          |  |    v     |  | 2. Add      |  |    +-------------+    |  |
  |  | +------+ |  | +------+ |  |    new VM   |  |    | OpenStack   |    |  |
  |  | |Master| |  | |Worker| |<-+-------------+--+----+ InfraDriver |    |  |
  |  | +------+ |  | +------+ |  |             |  |    +-------------+    |  |
  |  |    VM    |  |    VM    |  |             |  |                       |  |
  |  +----------+  +----------+  |             |  |                       |  |
  |                +----------+  |             |  |                       |  |
  |                | +------+ |  |             |  |                       |  |
  |                | |Worker| |  |             |  |                       |  |
  |                | +------+ |  |             |  |                       |  |
  |                |    VM    |  |             |  |                       |  |
  |                +----------+  |             |  |                       |  |
  +------------------------------+             |  |    Tacker-conductor   |  |
  +------------------------------+             |  +-----------------------+  |
  |      Hardware Resources      |             |                             |
  +------------------------------+             +-----------------------------+


VNFD for Scaling operation
^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support scaling Kubernetes Worker-nodes with
Mgmtdriver" [#SPEC-K8S-SCALE]_.

Request parameters for Scaling operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support scaling Kubernetes Worker-nodes with
Mgmtdriver" [#SPEC-K8S-SCALE]_.

Sequence for Scale-out operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/04.png

The procedure consists of the following steps as illustrated in
above sequence.

#. Client sends a POST Scale VNF request.

#. It is basically the same sequence as described in spec "Support scaling
   Kubernetes Worker-nodes with Mgmtdriver" [#SPEC-K8S-SCALE]_,
   except for following additional processes.

#. The following processes are added to ``scale_end``.

   #. MgmtDriver gets ``private_registry_connection_info`` of Instantiate
      VNF request from VnfInstance(Tacker DB).
   #. MgmtDriver transfers CA certificate files to the new Worker VM if
      specified by Instantiate VNF request parameter.
   #. MgmtDriver configure connections to Docker private registries on the
      new Worker VM.


Heal operation for the entire Kubernetes cluster with MgmtDriver
----------------------------------------------------------------

Add the function to connect to Docker private registries based on
spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

The diagram below shows Heal VNF (entire Kubernetes cluster) operation:

::

                                                             +--------------+
                                                             | Heal Request |
                                                             +-+------------+
                                                               | 1. Heal VNF
                                                               |
                                              +----------------+------------+
                                              |                v       VNFM |
                                              |  +-------------------+      |
                                              |  |   Tacker-server   |      |
                                              |  +---------+---------+      |
             5. Kubernetes Cluster            |            |                |
                Installation                  |            v                |
             6. Configure connections         |  +-----------------------+  |
                to Docker private registries  |  |    +-------------+    |  |
          +-------------+---------------------+--+----+ MgmtDriver  |    |  |
          |             |                     |  |    +-------------+    |  |
          |             |                     |  |  2. Delete old        |  |
          |             |                     |  |  Kubernetes cluster   |  |
          |             |                     |  |  information          |  |
          |             |                     |  |  7. Register new      |  |
  +-------+-------------+--------+            |  |  Kubernetes cluster   |  |
  |       |             |        |            |  |  information          |  |
  |  +----+-----+  +----+-----+  |            |  |                       |  |
  |  |    v     |  |    v     |  | 4. Create  |  |    +-------------+    |  |
  |  | +------+ |  | +------+ |  | new VMs    |  |    | OpenStack   |    |  |
  |  | |Master| |  | |Worker| |  |<-----------+--+----+ InfraDriver |    |  |
  |  | +------+ |  | +------+ |  |            |  |    +---+---------+    |  |
  |  |    VM    |  |    VM    |  |            |  |        |              |  |
  |  +----------+  +----------+  |            |  |        |              |  |
  |   Kubernetes cluster(new)    |            |  |        |              |  |
  +------------------------------+            |  |        |              |  |
  +------------------------------+            |  |        |              |  |
  |  +----------+  +----------+  | 3. Delete  |  |        |              |  |
  |  | +------+ |  | +------+ |  | failed VMs |  |        |              |  |
  |  | |Master| |  | |Worker| |  |<-----------+--+--------+              |  |
  |  | +------+ |  | +------+ |  |            |  |                       |  |
  |  |    VM    |  |    VM    |  |            |  |                       |  |
  |  +----------+  +----------+  |            |  |                       |  |
  |   Kubernetes cluster(old)    |            |  |                       |  |
  +------------------------------+            |  |   Tacker-conductor    |  |
  +------------------------------+            |  +-----------------------+  |
  |      Hardware Resources      |            |                             |
  +------------------------------+            +-----------------------------+


VNFD for Healing operation
^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Request parameters for Healing operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Sequence for Healing (entire Kubernetes cluster) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/05.png

The procedure consists of the following steps as illustrated in
above sequence.

#. Client sends a POST Heal VNF request.

#. It is basically the same sequence as described in spec "Support Healing
   Kubernetes Master/Worker-nodes with Mgmtdriver" [#SPEC-K8S-HEAL]_,
   except for following additional processes.

#. The following processes are added to ``heal_end``.

   #. MgmtDriver gets ``private_registry_connection_info`` of Instantiate VNF
      request from VnfInstance(Tacker DB).
   #. MgmtDriver transfers CA certificate files to all new Master/Worker VMs
      if specified by Instantiate VNF request parameter.
   #. MgmtDriver configure connections to Docker private registries on all new
      Master/Worker VMs.


Heal operation for a single node (Master/Worker) in Kubernetes cluster with MgmtDriver
--------------------------------------------------------------------------------------

Add the function to connect to Docker private registries based on
spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

The diagram below shows Heal VNF (single node) operation:

::

                                                       +--------------+
                                                       | Heal Request |
                                                       +-+------------+
                                                         | 1. Heal VNF
                                                         |
                                        +----------------+------------+
                                        |                v       VNFM |
                                        |  +-------------------+      |
                                        |  |   Tacker-server   |      |
                                        |  +---------+---------+      |
        5. Kubernetes Cluster           |            |                |
           Installation                 |            v                |
        6. Configure connections        |  +-----------------------+  |
           to Docker private registries |  |    +-------------+    |  |
               +------------------------+--+----+ MgmtDriver  |    |  |
               |                        |  |    +------------++    |  |
               |                        |  |  2. Evacuating  |     |  |
               |                        |  |  Pods(Worker)   |     |  |
  +------------+------------+           |  |  and removing   |     |  |
  |            |            |           |  |  failed node    |     |  |
  |            |            |           |  |  from cluster   |     |  |
  |            |            |           |  | (Master/Worker) |     |  |
  |  +---------+---------+  |           |  |                 |     |  |
  |  |         v         |  | 4. Create |  | +-------------+ |     |  |
  |  | +---------------+ |  | new VM    |  | | OpenStack   | |     |  |
  |  | | Master/Worker | |<-+-----------+--+-+ InfraDriver | |     |  |
  |  | +---------------+ |  |           |  | +------+------+ |     |  |
  |  |         VM        |  |           |  |        |        |     |  |
  |  +-------------------+  |           |  |        |        |     |  |
  |  +-------------------+  | 3. Delete |  |        |        |     |  |
  |  | +---------------+ |  | failed VM |  |        |        |     |  |
  |  | | Master/Worker | |<-+-----------+--+--------+        |     |  |
  |  | +---------------+ |  |           |  |                 |     |  |
  |  |         VM        |<-+-----------+--+-----------------+     |  |
  |  +-------------------+  |           |  |                       |  |
  +-------------------------+           |  |   Tacker-conductor    |  |
  +-------------------------+           |  +-----------------------+  |
  |   Hardware Resources    |           |                             |
  +-------------------------+           +-----------------------------+


VNFD for Healing operation
^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Request parameters for Healing operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Sequence for Healing (single node) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: ./cir-k8s-cluster/06.png

The procedure consists of the following steps as illustrated in
above sequence.

#. Client sends a POST Heal VNF request.

#. It is basically the same sequence as described in spec "Support Healing
   Kubernetes Master/Worker-nodes with Mgmtdriver" [#SPEC-K8S-HEAL]_,
   except for following additional processes.

#. The following processes are added to ``heal_end``.

   #. MgmtDriver gets ``private_registry_connection_info`` of Instantiate
      VNF request from VnfInstance(Tacker DB).
   #. MgmtDriver transfers CA certificate files to the new Master/Worker
      VM if specified by Instantiate VNF request parameter.
   #. MgmtDriver configure connections to Docker private registries on the
      new Master/Worker VM.


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
  Masaki Ueno <masaki.ueno.up@hco.ntt.co.jp>

Other contributors:
  Yoshito Ito <yoshito.itou.dr@hco.ntt.co.jp>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  Liang Lu <lu.liang@fujitsu.com>

Work Items
----------

+ Provide the following sample scripts executed by MgmtDriver:

  + For Docker private registry VNF:

    Install the Docker private registry in ``instantiate_end`` and
    ``heal_end``.

  + For Kubernetes cluster VNF:

    Add processes to connect to Docker private registries based on the
    Wallaby released Kubernetes cluster script.

+ Add new unit and functional tests.

Dependencies
============

LCM operations for the Kubernetes cluster depend on the following
specifications:

+ Instantiate operation for the Kubernetes cluster

  Depends on spec "Support deploying Kubernetes cluster with
  MgmtDriver" [#SPEC-K8S-CLUSTER]_.

+ Scale operation for the Kubernetes cluster

  Depends on spec "Support scaling Kubernetes Worker-nodes with
  Mgmtdriver" [#SPEC-K8S-SCALE]_.

+ Heal operation for the Kubernetes cluster

  Depends on spec "Support Healing Kubernetes Master/Worker-nodes with
  Mgmtdriver" [#SPEC-K8S-HEAL]_.

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

Complete user guide will be added to explain how to deploy Docker private
registry VNF
and how to connect to Docker private registry from Kubernetes cluster.

References
==========

.. [#SPEC-K8S-CLUSTER] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-cluster.html
.. [#SPEC-K8S-SCALE] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-scale.html
.. [#SPEC-K8S-HEAL] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-heal.html
.. [#NFV-SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_NFV-SOL003v020601p.pdf
.. [#SPEC-SOL-REST-API] https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol-rest-api-for-VNF-deployment.html
.. [#USER-GUIDE-K8S-CLUSTER] https://docs.openstack.org/tacker/latest/user/mgmt_driver_deploy_k8s_usage_guide.html
