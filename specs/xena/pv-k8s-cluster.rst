=================================================================
Support persistent volumes for Kubernetes cluster with MgmtDriver
=================================================================

https://blueprints.launchpad.net/tacker/+spec/pv-k8s-cluster

Problem description
===================

The Tacker Wallaby release supports managing a Kubernetes cluster as VNF
instance with ETSI NFV-SOL003 [#NFV-SOL003]_ VNF Lifecycle Management
interface with MgmtDriver according to the spec "Support deploying Kubernetes
cluster with MgmtDriver" [#SPEC-K8S-CLUSTER]_.
This specification proposes that the deployed Kubernetes cluster VNF has a
Storage server with Cinder volume to enable Users to deploy CNF which has
PersistentVolume on it.

Proposed change
===============

The LCM operations for Kubernetes cluster VNF require the following changes:

+ Instantiate operation for Kubernetes cluster with
  MgmtDriver [#SPEC-K8S-CLUSTER]_.

  #. Create a Storage server VM with Cinder volume.

  #. MgmtDriver exposes Cinder volume as NFS shared directories in
     the Storage server.

  #. MgmtDriver registers NFS shared directories as Kubernetes
     PersistentVolumes.

+ Heal operation for the entire Kubernetes cluster with
  MgmtDriver [#SPEC-K8S-HEAL]_.

  #. MgmtDriver exposes Cinder volume as NFS shared directories in the
     respawned Storage server.

  #. MgmtDriver registers NFS shared directories as Kubernetes
     PersistentVolumes.

+ Heal operation for the Storage server VM with MgmtDriver.

  MgmtDriver performs the following processes in ``heal_start``.

  #. Check that all registered PersistentVolumes in the Kubernetes cluster
     are not in use, otherwise fail.

  #. Deletes all the PersistentVolumes.

  .. note::

     All the PersistentVolumes should be deleted before healing
     the Storage server VM.
     Not to make Pods go failed state, it is also required to
     terminate the Pods with PersistentVolumes.

  MgmtDriver performs the following processes in ``heal_end``.

  #. MgmtDriver exposes Cinder volume as NFS shared directories in
     the respawned Storage server.

  #. MgmtDriver registers NFS shared directories as Kubernetes
     PersistentVolumes.

Install NFS client on newly created Master/Worker VMs in all LCM operations.
The following LCM operations need some additional process to install NFS
client in the created Master/Worker VMs.

+ Scale-out operation for Kubernetes cluster Worker-nodes with
  MgmtDriver [#SPEC-K8S-SCALE]_.

  MgmtDriver installs the NFS client in ``scale_end``.

+ Heal operation for a single node (Master/Worker) in Kubernetes cluster
  with MgmtDriver [#SPEC-K8S-HEAL]_.

  MgmtDriver installs the NFS client in ``heal_end``.

.. note:: + Scale operation for the Storage server VM is not supported.

          + Scale-in operation for Worker nodes is unchanged.

          + Terminate operation is unchanged.

.. note::

  When user deploys their CNF as Pods with PersistentVolume,
  PersistentVolumeClaim should be defined in Kubernetes resource files.
  PersistentVolumeClaim and controller resources such as Deployment,
  ReplicaSet, and Pod, are already supported in "Container Network Function
  (CNF) with VNFM and CISM" in Victoria release [#SPEC-CNF]_.


Instantiate operation for Kubernetes cluster with PersistentVolumes
-------------------------------------------------------------------

Add PersistentVolumes provided by Storage server VM to spec "Support deploying
Kubernetes cluster with MgmtDriver" [#SPEC-K8S-CLUSTER]_.

The diagram below shows creation of Kubernetes cluster and registration
of PersistentVolumes:

::

                                                   +---------+ +---------+
                                                   | Cluster | |         |
                                                   | Install | |  VNFD   |
                            +-------------------+  | Script  | |         |
                            | PersistentVolumes |  +-------+-+ +-+-------+
                            | manifest(yaml)    +--+       |     |
                            +-------------------+  |       v     v
                                +---------------+  |    +----------+  +---------------+
                                | LCM operation |  +--->|          |  | Instantiation |
                                | UserData      +------>|   CSAR   |  | Request with  |
                                +---------------+       |          |  | Additional    |
                                   +------------+  +--->|          |  | Params        |
                                   | Heat       |  |    +----+-----+  +-+-------------+
                                   | Template   +--+         |          | 1. Instantiate VNF
                                   | (Base HOT) |            |          |
                                   +------------+      +-----+----------+-------------+
                                                       |     v          v       VNFM  |
                                                       |  +-------------------+       |
                                                       |  |   TackerServer    |       |
                                                       |  +-------+-----------+       |
          3. Kubernetes Cluster                        |          |                   |
             Installation                              |          v                   |
          6. NFS client                                |  +----------------------+    |
             Installation                              |  |   +--------------+   |    |
          +--------------+-----------------------------+--+---+              |   |    |
          |              |                             |  |   |              |   |    |
  +-------+--------------+--------+                    |  |   |              |   |    |
  |       |              |        |                    |  |   |              |   |    |
  |  +----+-----+   +----+-----+  | 7. Kubernetes      |  |   |              |   |    |
  |  |    v     |   |    v     |  | PersistentVolumes  |  |   |              |   |    |
  |  | +------+ |   | +------+ |  | Registration       |  |   |  MgmtDriver  |   |    |
  |  | |Worker| |   | |Master|<+--+--------------------+--+---+              |   |    |
  |  | +------+ |   | +------+ |  |                    |  |   |              |   |    |
  |  |    VM    |   |    VM    |  |                    |  |   |              |   |    |
  |  +----------+   +----------+  |                  +-+--+---+              |   |    |
  |  +-------------------------+  | 5. NFS server    | |  |   |              |   |    |
  |  |    +---------------+    |  | Installation     | |  | +-+              |   |    |
  |  |    |      NFS      |<---+--+------------------+ |  | | +--------------+   |    |
  |  |    +---------------+    |  | 4. Set up Cinder   |  | |                    |    |
  |  |    +---------------+    |  | volume directories |  | |                    |    |
  |  |    | Cinder volume |<---+--+--------------------+--+-+ +--------------+   |    |
  |  |    +---------------+    |  |                    |  |   | OpenStack    |   |    |
  |  |                         |  |<-------------------+--+---+ Infra Driver |   |    |
  |  |    Storage server VM    |  | 2. Create VMs      |  |   +--------------+   |    |
  |  +-------------------------+  |(MasterVM/WorkerVM/ |  |                      |    |
  +-------------------------------+ Storage server VM  |  |   Tacker Conductor   |    |
  +-------------------------------+ with Cinder volume)|  +----------------------+    |
  |      Hardware Resources       |                    |                              |
  +-------------------------------+                    +------------------------------+


VNFD for Kubernetes cluster with UserData
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is basically the same as user guide "How to use Mgmt Driver for deploying
Kubernetes Cluster" [#USER-GUIDE-K8S-CLUSTER]_,
except for the following additions.

Add definitions related to the Storage server VM to the VNFD and Heat template
(Base HOT) as the following samples:

VNFD:

.. code-block:: yaml

   node_templates:
     ...
     storage_server:
       type: tosca.nodes.nfv.Vdu.Compute
       ...
       requirements:
         - virtual_storage: storage_server_volume
       ...

     storage_server_volume:
       type: tosca.nodes.nfv.Vdu.VirtualBlockStorage
       properties:
         virtual_block_storage_data:
           ...

     storage_server_CP:
       type: tosca.nodes.nfv.VduCp
       ...
       requirements:
         - virtual_binding: storage_server
       ...

Heat template(Base HOT):

.. code-block:: yaml

   resources:
     ...
     storage_server_volume:
       type: OS::Cinder::Volume
       properties:
         ...

     storage_server_CP:
       type: OS::Neutron::Port
       properties:
         ...

     storage_server:
       type: OS::Nova::Server
       properties:
         name: storage_server
         block_device_mapping_v2:
         - device_name: vdb
           volume_id: {get_resource: storage_server_volume}
           boot_index: -1
         networks:
         - port: {get_resource: storage_server_CP}
         ...


Request parameters for Instantiate Kubernetes cluster with PersistentVolumes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the following attributes to ``additionalParams`` described in the user
guide "How to use Mgmt Driver for deploying Kubernetes
Cluster" [#USER-GUIDE-K8S-CLUSTER]_.

.. list-table::
  :widths: 15 10 40
  :header-rows: 1

  * - Attribute name
    - Cardinality
    - Parameter description
  * - k8s_cluster_installation_param
    - 1
    - Configuration for Kubernetes cluster installation.
  * - >storage_server
    - 0..1
    - Optional. Configuration for the Storage server VM.
      If the function of this specification is not used, the attribute is omitted.
  * - >>ssh_cp_name
    - 1
    - CP name that MgmtDriver uses when SSH/SFTP access to the Storage server VM.
  * - >>username
    - 1
    - User name that MgmtDriver uses when SSH/SFTP access to the Storage server VM.
  * - >>password
    - 1
    - User password that MgmtDriver uses when SSH/SFTP access to the Storage server VM.
  * - >>cinder_volume_setup_params
    - 1..N
    - Configurations for Cinder volume directories on the Storage server VM.
  * - >>>volume_resource_id
    - 1
    - The resource ID of the Cinder volume defined in the heat template
      (Base HOT).  This attribute is used by the MgmtDriver
      to identify the Cinder volume.
  * - >>>mount_to
    - 1
    - Directory path where the Cinder volume will be mounted
      on the Storage server VM.
  * - >>nfs_server_setup_params
    - 1..N
    - Configurations for NFS exports on the Storage server VM.
  * - >>>export_dir
    - 1
    - Directory path to be exported over NFS.
  * - >>>export_to
    - 1
    - The network address to which the directory is exported over NFS.
  * - >pv_registration_params
    - 0..N
    - Optional. Configuration for Kubernetes PersistentVolumes.
      If the function of this specification is not used,
      the attribute is omitted.
  * - >>pv_manifest_file_path
    - 1
    - Path of manifest file for Kubernetes PersistentVolume in VNF Package.
  * - >>nfs_server_cp
    - 1
    - CP name of the NFS server. If DHCP is enabled for the network
      used by NFS, the NFS server IP address in the manifest file
      for Kubernetes PersistentVolume cannot be preconfigured.
      Therefore, the NFS server IP address in the manifest file
      is replaced with the IP address of the CP specified
      by this attribute.

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
            "pod_cidr": "192.168.3.0/16",
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
            "no_proxy": "192.168.246.0/24,10.0.0.1",
            "k8s_node_cidr": "10.10.0.0/24"
          },
          "storage_server": {
            "ssh_cp_name": "storage_server_CP",
            "username": "ubuntu",
            "password": "ubuntu",
            "cinder_volume_setup_params": [
              {
                "volume_resource_id": "storage_server_volume",
                "mount_to": "/volume"
              }
            ],
            "nfs_server_setup_params": [
              {
                "export_dir": "/volume/nfs/pv1",
                "export_to": "10.10.0.0/24"
              },
              {
                "export_dir": "/volume/nfs/pv2",
                "export_to": "10.10.0.0/24"
              },
              {
                "export_dir": "/volume/nfs/pv3",
                "export_to": "10.10.0.0/24"
              }
            ]
          },
          "pv_registration_params": [
            {
              "pv_manifest_file_path": "Files/kubernetes/nfs-pv1.yaml",
              "nfs_server_cp": "storage_server_CP"
            },
            {
              "pv_manifest_file_path": "Files/kubernetes/nfs-pv2.yaml",
              "nfs_server_cp": "storage_server_CP"
            },
            {
              "pv_manifest_file_path": "Files/kubernetes/nfs-pv3.yaml",
              "nfs_server_cp": "storage_server_CP"
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
        },
        {
          "id": "net0_storage",
          "resourceId": "f0c82461-36b5-4d86-8322-b0bc19cda65f",
          "extCps": [
            {
              "cpdId": "storage_server_CP",
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


Sequence for Instantiate Kubernetes cluster with PersistentVolumes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "OpenStackInfraDriver"
    "Heat"
    "MgmtDriver"
    "VnfInstance(Tacker DB)"
    "RemoteCommandExecutor"
    "SFTPClient"
    "NfvoPlugin"

    Client -> "Tacker-server"
      [label = "POST /vnf_instances/{vnfInstanceId}/instantiate"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" -> "Tacker-conductor"
      [label = "trigger asynchronous task"];

   "Tacker-conductor" -> "VnfLcmDriver"
      [label = "execute VnfLcmDriver"];
    "VnfLcmDriver" -> "OpenStackInfraDriver"
      [label = "execute OpenStackInfraDriver"];
    "OpenStackInfraDriver" -> "Heat"
      [label = "create stack"];
    "OpenStackInfraDriver" <-- "Heat"
      [label = "return stack id"];
    "VnfLcmDriver" <-- "OpenStackInfraDriver"
      [label = "return instance_id"];

    "VnfLcmDriver" -> "MgmtDriver"
      [label = "instantiate_end"];
    "MgmtDriver" -> "VnfInstance(Tacker DB)"
      [label = "get stack id"];
    "MgmtDriver" <-- "VnfInstance(Tacker DB)"
      [label = ""];
    "MgmtDriver" -> "Heat"
      [label = "get SSH/SFTP IP addresses and Kubernetes addresses using stack id"];
    "MgmtDriver" <-- "Heat"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "install Kubernetes and create cluster on Master/Worker VMs"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "get identification token from Kubernetes cluster"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "set up Cinder volume directories on the Storage server VM"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "install NFS server and set up NFS exports on the Storage server VM"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "install NFS client on all Master/Worker VMs"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "SFTPClient"
      [label = "transfer manifest files for Kubernetes PersistentVolumes to the Master VM"];
    "MgmtDriver" <-- "SFTPClient"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "replace the NFS server IP address in manifest files for Kubernetes PersistentVolumes"];
    "MgmtDriver" <-- "RemoteCommandExecutor"
      [label = ""];
    "MgmtDriver" -> "RemoteCommandExecutor"
      [label = "register Kubernetes PersistentVolumes on the Master VM"];
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
    "VnfLcmDriver" <-- "MgmtDriver"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];

  }

The procedure consists of the following steps as illustrated in above sequence.

#. Client sends a POST Instantiate VNF request.

#. It is basically the same sequence as described in spec "Support deployment
   Kubernetes cluster with MgmtDriver" [#SPEC-K8S-CLUSTER]_,
   except for the following additional processes.

#. The following processes are added to ``instantiate_end``.

   #. MgmtDriver creates file system for Cinder volume and mounts it to a
      directory on the Storage server VM.
   #. MgmtDriver installs the NFS server and sets up NFS exports on the
      Storage server VM.
   #. MgmtDriver installs the NFS client on all Master/Worker VMs.
   #. MgmtDriver transfers manifest files for Kubernetes PersistentVolumes
      to the Master VM.
   #. MgmtDriver replaces the NFS server IP address in manifest files for
      Kubernetes PersistentVolumes with the actual NFS server IP address.
   #. MgmtDriver uses CLI to register PersistentVolumes on the Master VM.

   .. note::

     It is assumed that the OS of the Storage Server VM is Ubuntu.
     The file system for the Cinder volume is created with "ext4".


Heal operation for the entire Kubernetes cluster with PersistentVolumes
-----------------------------------------------------------------------

Add PersistentVolumes provided by Storage server VM to spec "Support Healing
Kubernetes Master/Worker-nodes with Mgmtdriver" [#SPEC-K8S-HEAL]_.

The diagram below shows Heal(entire Kubernetes cluster) operation:

::

                                                                      +---------------+
                                                                      | Heal Request  |
                                                                      +---+-----------+
                                                                          | 1. Heal VNF
                                                                          |
                                                         +----------------+-------------+
                                                         |                v       VNFM  |
                                                         |  +-------------------+       |
                                                         |  |   TackerServer    |       |
                                                         |  +-------+-----------+       |
          5. Kubernetes Cluster                          |          |                   |
             Installation                                |          v                   |
          8. NFS client                                  |  +----------------------+    |
             Installation                                |  |   +--------------+   |    |
          +--------------+-------------------------------+--+---+              |   |    |
          |              |                               |  |   |              |   |    |
  +-------+--------------+--------+                      |  |   |              |   |    |
  |       |              |        |                      |  |   |              |   |    |
  |  +----+-----+   +----+-----+  | 9. Kubernetes        |  |   |              |   |    |
  |  |    v     |   |    v     |  | PersistentVolumes    |  |   |              |   |    |
  |  | +------+ |   | +------+ |  | Registration         |  |   |  MgmtDriver  |   |    |
  |  | |Worker| |   | |Master|<+--+----------------------+--+---+              |   |    |
  |  | +------+ |   | +------+ |  |                      |  |   |              |   |    |
  |  |    VM    |   |    VM    |  |                      |  |   |              |   |    |
  |  +----------+   +----------+  |                      |  |   |              |   |    |
  |  +-------------------------+  | 7. NFS server        |  |   |              |   |    |
  |  |    +---------------+    |  | Installation         |  |   |              |   |    |
  |  |    |      NFS      |<---+--+----------------------+--+---+              |   |    |
  |  |    +---------------+    |  | 6. Set up Cinder     |  |   |              |   |    |
  |  |    +---------------+    |  | volume directories   |  |   |              |   |    |
  |  |    | Cinder volume |<---+--+----------------------+--+---+              |   |    |
  |  |    +---------------+    |  |                      |  |   +--------------+   |    |
  |  |    Storage server VM    |  |                      |  |  2. Delete old       |    |
  |  +-------------------------+  |                      |  |   Kubernetes cluster |    |
  |            New VMs            |<-------------------+ |  |   information        |    |
  +-------------------------------+ 4. Create VMs      | |  |  10. Register new    |    |
  +-------------------------------+(MasterVM/WorkerVM/ | |  |   Kubernetes cluster |    |
  |  +----------+   +----------+  | Storage server VM  | |  |   information        |    |
  |  | +------+ |   | +------+ |  | with Cinder volume)| |  |                      |    |
  |  | |Worker| |   | |Master| |  |                    | |  |                      |    |
  |  | +------+ |   | +------+ |  |                    | |  |                      |    |
  |  |    VM    |   |    VM    |  |                    | |  |                      |    |
  |  +----------+   +----------+  |                    | |  |                      |    |
  |  +-------------------------+  |                    | |  |                      |    |
  |  |    +---------------+    |  |                    | |  |   +--------------+   |    |
  |  |    |      NFS      |    |  |                    +-+--+---+              |   |    |
  |  |    +---------------+    |  |                      |  |   | OpenStack    |   |    |
  |  |    +---------------+    |  |                      |  |   | Infra Driver |   |    |
  |  |    | Cinder volume |    |  |<---------------------+--+---+              |   |    |
  |  |    +---------------+    |  | 3. Delete VMs        |  |   +--------------+   |    |
  |  |    Storage server VM    |  |(MasterVM/WorkerVM/   |  |                      |    |
  |  +-------------------------+  | Storage server VM    |  |                      |    |
  |            Old VMs            | with Cinder volume)  |  |                      |    |
  +-------------------------------+                      |  |   Tacker Conductor   |    |
  +-------------------------------+                      |  +----------------------+    |
  |      Hardware Resources       |                      |                              |
  +-------------------------------+                      +------------------------------+


VNFD for Heal(entire Kubernetes cluster) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Request parameters for Heal(entire Kubernetes cluster) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No change from spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Procedure for Heal(entire Kubernetes cluster) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The procedure consists of the following steps.

#. Client sends a POST Heal VNF request.

#. It is basically the same sequence as described in spec "Support Healing
   Kubernetes Master/Worker-nodes with Mgmtdriver" [#SPEC-K8S-HEAL]_,
   except for the following additional processes.

#. The following processes are added to ``heal_end``.

   #. MgmtDriver gets ``additionalParams`` of Instantiate VNF request from
      VnfInstance(Tacker DB).
   #. MgmtDriver creates file system for Cinder volume and mounts it to a
      directory on the new Storage server VM.
   #. MgmtDriver installs the NFS server and sets up NFS exports on the new
      Storage server VM.
   #. MgmtDriver installs the NFS client on all new Master/Worker VMs.
   #. MgmtDriver transfers manifest files for Kubernetes PersistentVolumes
      to the new Master VM.
   #. MgmtDriver replaces the NFS server IP address in manifest files for
      Kubernetes PersistentVolumes with the actual NFS server IP address.
   #. MgmtDriver uses CLI to register Kubernetes PersistentVolumes on the
      new Master VM.


Heal operation for the Storage server VM
----------------------------------------

The diagram below shows Heal operation for the Storage server VM:

::

                                                                      +---------------+
                                                                      | Heal Request  |
                                                                      +---+-----------+
                                                                          | 1. Heal VNF
                                                                          |
                                                         +----------------+-------------+
                                                         |                v       VNFM  |
                                                         |  +-------------------+       |
                                                         |  |   TackerServer    |       |
                                    2. Delete old        |  +-------+-----------+       |
                                       Kubernetes        |          |                   |
  +-------------------------------+    PersistentVolumes |          v                   |
  |                 +----------+  | 7. Register new      |  +----------------------+    |
  |                 |          |  |    Kubernetes        |  |   +--------------+   |    |
  |                 | +------+ |  |    PersistentVolumes |  |   |              |   |    |
  |                 | |Master|<+--+----------------------+--+---+              |   |    |
  |                 | +------+ |  |                      |  |   |              |   |    |
  |                 |    VM    |  |                      |  |   |              |   |    |
  |                 +----------+  |                      |  |   |              |   |    |
  |  +-------------------------+  | 6. NFS server        |  |   |  MgmtDriver  |   |    |
  |  |    +---------------+    |  | Installation         |  |   |              |   |    |
  |  |    |      NFS      |<---+--+----------------------+--+---+              |   |    |
  |  |    +---------------+    |  | 5. Set up Cinder     |  |   |              |   |    |
  |  |    +---------------+    |  | volume directories   |  |   |              |   |    |
  |  |    | Cinder volume |<---+--+----------------------+--+---+              |   |    |
  |  |    +---------------+    |  |                      |  |   +--------------+   |    |
  |  |  New Storage server VM  |<-+--------------------+ |  |                      |    |
  |  +-------------------------+  | 4. Create new      | |  |                      |    |
  |  +-------------------------+  | Storage server VM  | |  |                      |    |
  |  |    +---------------+    |  |                    | |  |                      |    |
  |  |    |      NFS      |    |  |                    | |  |   +--------------+   |    |
  |  |    +---------------+    |  |                    +-+--+---+              |   |    |
  |  |    +---------------+    |  |                      |  |   | OpenStack    |   |    |
  |  |    | Cinder volume |    |  |                      |  |   | Infra Driver |   |    |
  |  |    +---------------+    |<-+----------------------+--+---+              |   |    |
  |  |  Old Storage server VM  |  | 3. Delete old        |  |   +--------------+   |    |
  |  +-------------------------+  | Storage server VM    |  |                      |    |
  +-------------------------------+                      |  |   Tacker Conductor   |    |
  +-------------------------------+                      |  +----------------------+    |
  |      Hardware Resources       |                      |                              |
  +-------------------------------+                      +------------------------------+


VNFD for Heal(Storage server VM) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

VNFD needs to have ``heal_start`` and ``heal_end`` definitions.
Same as spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Request parameters for Heal(Storage server VM) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

User gives ``HealVnfRequest`` data type defined in ETSI NFV-SOL002
v2.6.1 [#NFV-SOL002]_ as request parameters.
Same as spec "Support Healing Kubernetes Master/Worker-nodes with
Mgmtdriver" [#SPEC-K8S-HEAL]_.

Procedure for Heal(Storage server VM) operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The procedure consists of the following steps.

#. Client sends a POST Heal VNF request.

#. It is basically the same sequence as described in the "3) Flow of Heal
   of a VNF instance"
   chapter of spec "REST API for VNF based on ETSI NFV-SOL
   specification" [#SPEC-SOL-REST-API]_, except for the MgmtDriver.

#. The following processes are performed in ``heal_start``.

   #. MgmtDriver gets ``additionalParams`` of Instantiate VNF request from
      VnfInstance(Tacker DB).
   #. MgmtDriver uses CLI to get status of Kubernetes PersistentVolumes,
      and check that they are not in use.
      If Kubernetes PersistentVolumes are in use, raise exception and Heal
      operation fails.
   #. MgmtDriver uses CLI to delete Kubernetes PersistentVolumes on the
      Master VM.

#. The following processes are performed in ``heal_end``.

   #. MgmtDriver gets IP address of the new Storage server VM from Heat.
   #. MgmtDriver gets ``additionalParams`` of Instantiate VNF request from
      VnfInstance(Tacker DB).
   #. MgmtDriver creates file system for new Cinder volume and mounts it to a
      directory on the new Storage server VM.
   #. MgmtDriver installs the NFS server and sets up NFS exports on the new
      Storage server VM.
   #. MgmtDriver transfers manifest files for Kubernetes PersistentVolumes to
      the Master VM.
   #. MgmtDriver replaces the NFS server IP address in manifest files for
      Kubernetes PersistentVolumes with the actual NFS server IP address.
   #. MgmtDriver uses CLI to register Kubernetes PersistentVolumes on the
      Master VM.


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

+ Provide the sample script executed by MgmtDriver based on the Wallaby
  released sample script for Kubernetes cluster with the following changes:

  + Expose Cinder volume of Storage server VM as NFS shared directories,
    and register NFS shared directories as Kubernetes PersistentVolumes.

  + Install NFS client on all Master/Worker VMs.

  + When healing the Storage server VM, re-register the Kubernetes
    PersistentVolumes.

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

Complete user guide will be added to explain how to use a Kubernetes cluster
with a Storage server containing Cinder volume.

References
==========

.. [#NFV-SOL003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_NFV-SOL003v020601p.pdf
.. [#SPEC-K8S-CLUSTER] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-cluster.html
.. [#SPEC-K8S-HEAL] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-heal.html
.. [#SPEC-K8S-SCALE] https://specs.openstack.org/openstack/tacker-specs/specs/wallaby/mgmt-driver-for-k8s-scale.html
.. [#SPEC-CNF] https://specs.openstack.org/openstack/tacker-specs/specs/victoria/container-network-function.html
.. [#USER-GUIDE-K8S-CLUSTER] https://docs.openstack.org/tacker/latest/user/mgmt_driver_deploy_k8s_usage_guide.html
.. [#NFV-SOL002] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
.. [#SPEC-SOL-REST-API] https://specs.openstack.org/openstack/tacker-specs/specs/ussuri/etsi-nfv-sol-rest-api-for-VNF-deployment.html
