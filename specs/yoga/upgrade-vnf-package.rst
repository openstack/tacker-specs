=============================================================
Support ChangeCurrentVNFPackage for VNF software modification
=============================================================

Blueprint URL: https://blueprints.launchpad.net/tacker/+spec/upgrade-vnf-package

This specification describes the ChangeCurrentVNFPackage operation defined in ETSI NFV-SOL003 v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_.

Problem description
===================
The ChangeCurrentVNFPackage API and VNF LCM Coordination interface are newly defined in ETSI NFV-SOL003 v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_ and ETSI NFV-SOL002 v3.5.1 [#ETSI-NFV-SOL002-v3.5.1]_, respectively according to the VNF software modification procedure in ETSI NFV-IFA007 v3.3.1 [#ETSI-NFV-IFA007-v3.3.1]_.
These new functions enable Tacker to update VNF instances in two ways: Blue-Green deployment and Rolling update.
However, VNF LCM Coordination interface is not supported by most current VNF. We plan to implement this
interface within Tacker for future usage.
Therefore, this specification complies with ETSI NFV-SOL003 v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_ and ETSI NFV-SOL002 v3.3.1 [#ETSI-NFV-SOL002-v3.3.1]_, does not comply with ETSI NFV-SOL002 v3.5.1 [#ETSI-NFV-SOL002-v3.5.1]_.


Proposed change
===============
We propose the following changes:

#. Support for ChangeCurrentVNFPackage API.

#. VNF software modification performs the following operations:

   A. Blue-Green deployment process for OpenStack VIM.

      + Create new VNF (VM).
      + Invoke coordinate VNF method.
      + Delete old VNF (VM).
      + The attributes in the TackerDB to be updated are as follows:

        + VnfInstance.vnfdId: Replace the existing vnfd ID with the new vnfd ID.
        + VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId: Update resourceId with the new resource ID.
        + VnfInstance.instantiatedVnfInfo.vnfVirtualLinkResourceInfo.networkResource.resourceId: Update resourceId with the new connection point ID.
        + VnfInstance.instantiatedVnfInfo.virtualStorageResourceInfo.storageResource.resourceId: Update resourceId with the new storage ID.
        + VnfInstance.instantiatedVnfInfo.instance_id: Update id with the new stack ID.


   B. Rolling update process for OpenStack VIM.

      + Update the existing VNF (VM).

        + In this step, Tacker will repeat update stack operation for each target VM.

      + Invoke coordinate VNF method.
      + The attributes in the TackerDB to be updated are as follows:

        + VnfInstance.vnfdId: Replace the existing vnfd ID with the new vnfd ID.

        .. note:: Rolling update changes the VM on the original stack, so the stack, compute resource and connection point are not changed.
                  Therefore, this process only changes the VnfInstance.VnfdId in TackerDB.

   C. Blue-Green deployment process for Kubernetes VIM.

      + Create new CNF (Deployment).
      + Invoke coordinate VNF method.
      + Delete old CNF (Deployment).
      + The attributes in the TackerDB to be updated are as follows:

        + VnfInstance.vnfdId: Replace the existing vnfd ID with the new vnfd ID.
        + VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId: Update resourceId with the new Pod name.
        + VnfInstance.instantiatedVnfInfo.vnfVirtualLinkResourceInfo.networkResource.resourceId: Update resourceId with the new connection point ID.
        + VnfInstance.instantiatedVnfInfo.virtualStorageResourceInfo.storageResource.resourceId: Update resourceId with the new storage ID.
        + VnfResource.resourceName: Update resourceName with the new Deployment name.

   D. Rolling update process for Kubernetes VIM.

      + Update the existing CNF (Deployment).
      + Invoke coordinate VNF method.
      + The attributes in the TackerDB to be updated are as follows:

        + VnfInstance.vnfdId: Replace the existing vnfd ID with the new vnfd ID.
        + VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId: Update resourceId with the new Pod name.

        .. note:: Rolling update changes the Pod on the original Deployment, so the Deployment itself and connection point are not changed.
                  Therefore, this process does not need to modify VnfInstance.instantiatedVnfInfo.vnfVirtualLinkResourceInfo.networkResource.resourceId and VnfResource.resourceName in TackerDB.

#. Implements the mechanism by which the VnfLcmDriver invokes the CoordinateVNF script specified in the request parameter.

#. Provide sample CoordinateVNF script that uses the CoordinateVNF.

   + for OpenStack VIM

     + Configure the load balancer.

   + for Kubernetes VIM

     + Update Kubernetes Service.

   .. note:: The information used to access each VNFC is managed by load balancers in the case of OpenStack VIM and by Service objects in the case of Kubernetes VIM.

.. note:: If an error occurs during the ChangeCurrentVNFPackage processing, the LCM status will become FAILED_TEMP.
   The implementation of each Rollback operation for Blue-Green deployments and Rolling update will be as follows:

   + Delete new instances created by the ChangeCurrentVNFPackage operation for Blue-Green deployments.
   + Recreate VNFC instances with the old VNF package to revert to the old version for the one running with the new version.

.. note:: The evaluation of whether a VNF package can be changed is described in ETSI NFV-SOL003 v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_, but is not considered in this spec.

The following shows the operation flow for each use case.

Change current VNF Package operation for OpenStack VIM
------------------------------------------------------

HEAT Template Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sample file of HEAT Template Configuration for OpenStack VIM.

top.yaml

.. code-block:: yaml

    heat_template_version: 2013-05-23
    description: Sample template for Upgrade.

    parameters:
      image_id:
        type: string
        description: Image ID to use for the instance.
      flavor_name:
        type: string
        description: Flavor name to use for the instance.
      num_of_instances:
        type: number
        description: Number of instances to create.
      ext_network_id:
        type: string
        description: External Network ID.

    resources:
      group1:
        type: OS::Heat::AutoScalingGroup
        properties:
          min_size: 1
          max_size: 4
          desired_capacity: {get_param: num_of_instances}
          resource:
            type: nested_server.yaml
            properties:
              image_id: { get_param: image_id }
              flavor_name: { get_param: flavor_name }
              ext_network_id: { get_param: ext_network_id }

nested_server.yaml

.. code-block:: yaml

    heat_template_version: 2013-05-23
    description: Sample template for scaling.

    parameters:
      image_id:
        type: string
        description: Image ID to use for the instance.
      flavor_name:
        type: string
        description: Flavor name to use for the instance.
      ext_network_id:
        type: string

    resources:
      cp:
        type: OS::Neutron::Port
        properties:
          network: { get_param: ext_network_id }
      group1:
        type: OS::Nova::Server
        properties:
          name: sample_server
          image: {get_param: image_id}
          flavor: {get_param: flavor_name}
          networks:
          - port:
              get_resource: cp

Blue-Green deployment
^^^^^^^^^^^^^^^^^^^^^

Below is a diagram of the Blue-Green deployment process for OpenStack VIM:

.. code-block::


                                                                     +---------+
                                                                     |  VNFD   |
                                                                     |         |
                                                                     +-+-------+
                                                                       |
  6. Coordinate                          (Script is included           v     +-------------------+
     New resource +--------------------+  in the package)      +----------+  | Change current    |
  +---------------+ Coordinate VNF     +---------------------->|          |  | VNF Package       |
  |               | script             | 5. CoordinateVNF      |   CSAR   |  | Request with      |
  |   +-----------+                    |<------------------+   |          |  | Additional Params |
  |   |           +-------+------------+                   |   +----+-----+  +-+-----------------+
  |   | 8. Coordinate     | 7. Update load balancer        |        |          | 1. Change current VNF Package
  |   |    Old resource   |                                |        |          |    request
  |   |                   |                                |  +-----+----------+------------------------------+
  |   |                   |                                |  |     v          v        VNFM                  |
  |   |                   |                                |  |  +------------------------------+             |
  |   |                   |                                |  |  |   Tacker-server              |             |
  |   |                   |                                |  |  +--+---------------------------+             |
  |   |                   |                                |  |     |  2. Change current VNF Package request  |
  |   |                   |                                |  |     v                                         |
  |   |                   |                                |  |  +-----------------------------------------+  |
  |   |                   v                                |  |  |                                         |  |
  |   |           +--------------------+                   |  |  |   +----------------------+              |  |
  |   |           | LB                 |                   +--+--+---+ VnfLcmDriver         |              |  |
  |   |           +--------------------+                      |  |   |                      |              |  |
  |   |                                                       |  |   |                      |              |  |
  |   |           +--------------------+ 11. Update TackerDB  |  |   |                      |              |  |
  |   |           | TackerDB           |<---------------------+--+---+                      |              |  |
  |   |           +--------------------+                      |  |   |                      |              |  |
  |   |                                                       |  |   +-+---------------+----+              |  |
  |   |                                                       |  |     | 3. Create New | 9. Terminate Old  |  |
  |   |                                                       |  |     |    resource   |    resource       |  |
  |   |           +--------------------+                      |  |     v               v                   |  |
  |   |           |                    | 10. Terminate Old    |  |   +----------------------+              |  |
  |   |           |  +--------------+  |     resource         |  |   | InfraDriver          |              |  |
  |   +-----------+->| Old resource |<-+----------------------+--+---+                      |              |  |
  |               |  +--------------+  | 4. Create New        |  |   |                      |              |  |
  |               |  +--------------+  |    resource          |  |   |                      |              |  |
  +---------------+->| New resource |<-+----------------------+--+---+                      |              |  |
                  |  +--------------+  |                      |  |   +----------------------+              |  |
                  |  VNF               |                      |  |                                         |  |
                  +--------------------+                      |  |                                         |  |
                                                              |  |    Tacker-conductor                     |  |
                  +--------------------+                      |  +-----------------------------------------+  |
                  | Hardware Resources |                      |                                               |
                  +--------------------+                      +-----------------------------------------------+



Sequence for Blue-Green Deployment operation (For OpenStack VIM)

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver"
    "CoordinateVNF script"
    "TackerDB"
    "VIM (OpenStack)"
    "VNF"
    "LB"

    Client -> "Tacker-server"
      [label = "1. POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. ChangeCurrentVNFPackage"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "change_vnfpkg"];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "3. create_newVNF"];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "4. create_newVNF"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "CoordinateVNF script"
      [label = "5. CoordinateVNF"];
    "CoordinateVNF script" -> "VNF"
      [label = "6. Coordinate new VNF"];
    "CoordinateVNF script" <-- "VNF"
      [label = ""];
    "CoordinateVNF script" -> "LB"
      [label = "7. update_loadbalancer"];
    "CoordinateVNF script" <-- "LB"
      [label = ""];
    "CoordinateVNF script" -> "VNF"
      [label = "8. Coordinate old VNF"];
    "CoordinateVNF script" <-- "VNF"
      [label = ""];
    "VnfLcmDriver" <-- "CoordinateVNF script"
      [label = ""];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "9. terminate_oldVNF"];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "10. terminate_oldVNF"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "11. Update_DB"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }


#. The Client sends a POST request to the "Individual VNF instance" resource.
#. Tacker-server sends ChangeCurrentVNFPackage request to Tacker-conductor, then Tacker-conductor fetches an on-boarded VNF package and calls VnfLcmDriver.
#. VnfLcmDriver sends a request to the InfraDriver to create new VNF.
#. InfraDriver sends a request to the VIM to create new VNF.
#. VnfLcmDriver calls CoordinateVNF.
#. CoordinateVNF script sends a request to the new VNF to Coordinate VNF.
#. CoordinateVNF script sends a request to the load balancer to update configuration.
#. CoordinateVNF script sends a request to the old VNF to Coordinate VNF.
#. VnfLcmDriver sends a request to the InfraDriver to terminate old VNF.
#. InfraDriver sends a request to the VIM to terminate old VNF.
#. VnfLcmDriver updates the following attributes in TackerDB:

   + ``VnfInstance.vnfdId``
   + ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId``
   + ``VnfInstance.instantiatedVnfInfo.vnfVirtualLinkResourceInfo.networkResource.resourceId``
   + ``VnfInstance.instantiatedVnfInfo.virtualStorageResourceInfo.storageResource.resourceId``
   + ``VnfInstance.instantiatedVnfInfo.instance_id``


Rolling update
^^^^^^^^^^^^^^

Below is a diagram of the Rolling update process for OpenStack VIM:

.. code-block::


                                                                   +---------+
                                                                   |  VNFD   |
                                                                   |         |
                                                                   +-+-------+
                                                                     |
                                        (Script is included          v     +-------------------+
                +---------------------+  in the package)     +----------+  | Change current    |
  +------------>| CoordinateVNF       +--------------------->|          |  | VNF Package       |
  |             | script              |                      |   CSAR   |  | Request with      |
  |   +---------+                     |                      |          |  | Additional Params |
  |   |         +---------------------+                      +----+-----+  +-+-----------------+
  |   | 7. Coordinate resource                                    |          | 1. Change current VNF Package
  |   |                                                           |          |    request
  |   |                                                     +-----+----------+------------------------------+
  |   |                                                     |     v          v        VNFM                  |
  |   |                                                     |  +-----------------------+                    |
  |   |                                                     |  |   Tacker-server       |                    |
  |   |                                                     |  +--+--------------------+                    |
  |   |                                                     |     |  2. Change current VNF Package request  |
  |   |                                                     |     v                                         |
  |   |                                                     |  +-----------------------------------------+  |
  |   |                                                     |  |                                         |  |
  |   |                                                     |  |   +-------------------+                 |  |
  |   |         +--------------------+                      |  |   | VnfLcmDriver      |                 |  |
  |   |         | LB                 |                      |  |   |                   |                 |  |
  |   |         +--------------------+                      |  |   |                   |                 |  |
  |   |                                                     |  |   |                   |                 |  |
  |   |         +--------------------+ 9. Update TackerDB   |  |   |                   |                 |  |
  |   |         | TackerDB           |<---------------------+--+---+                   |                 |  |
  |   |         +--------------------+                      |  |   +-+-----------------+                 |  |
  |   |                                                     |  |     | 3. change_vnfpkg_process          |  |
  |   |         +--------------------+                      |  |     v                                   |  |
  |   |         |                    | 4. Get stack resource|  |   +-------------------+                 |  |
  |   |         |  +--------------+  |    to update         |  |   | InfraDriver       | 8. Repeat steps |  |
  |   |         |  | Resource     |<-+----------------------+--+---+                   |    5 through 7  |  |
  |   +---------+->|              |  | 5. Update VNFC       |  |   |                   |    for each VNFC|  |
  |             |  |              |<-+----------------------+--+---+                   +--------+        |  |
  |             |  +--------------+  |                      |  |   |                   |        |        |  |
  |             | VNF                |                      |  |   |                   |<-------+        |  |
  |             +--------------------+                      |  |   |                   |                 |  |
  |                                    6. Coordinate VNF    |  |   |                   |                 |  |
  +---------------------------------------------------------+--+---+                   |                 |  |
                                                            |  |   +-------------------+                 |  |
                                                            |  |    Tacker-conductor                     |  |
                +--------------------+                      |  +-----------------------------------------+  |
                | Hardware Resources |                      |                                               |
                +--------------------+                      +-----------------------------------------------+

Sequence for Rolling update operation (For OpenStack VIM)

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver"
    "CoordinateVNF script"
    "TackerDB"
    "VIM (OpenStack)"
    "VNF"

    Client -> "Tacker-server"
      [label = "1. POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. ChangeCurrentVNFPackage"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "change_vnfpkg"];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "3. change_vnfpkg_process"];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "4. Get stack resource to update"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "InfraDriver" -> "VIM (OpenStack)"
      [label = "5. update_stack"];
    "InfraDriver" <-- "VIM (OpenStack)"
      [label = ""];
    "InfraDriver" -> "CoordinateVNF script"
      [label = "6. CoordinateVNF"];
    "CoordinateVNF script" -> "VNF"
      [label = "7. Coordinate resource"];
    "CoordinateVNF script" <-- "VNF"
      [label = ""];
    "InfraDriver" <-- "CoordinateVNF script"
      [label = ""];
    "InfraDriver" -> "InfraDriver"
      [label = "8. Repeat steps 5 through 7 for each VNFC"];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "9. Update_DB"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }


#. The Client sends a POST request to the "Individual VNF instance" resource.
#. Tacker-server sends ChangeCurrentVNFPackage request to Tacker-conductor, then Tacker-conductor fetches an on-boarded VNF package and calls VnfLcmDriver.
#. VnfLcmDriver sends a request to the InfraDriver to change vnfpkg process.
#. InfraDriver sends a request to the VIM to get stack resource to update.
#. InfraDriver sends a request to the VIM to update stack.
#. InfraDriver calls CoordinateVNF.
#. CoordinateVNF script sends a request to the VNF to Coordinate VNF.
#. Repeat steps 5 through 7 for each VNFC.
#. VnfLcmDriver updates the following attributes in TackerDB:

   + ``VnfInstance.vnfdId``

Change current VNF Package operation for Kubernetes VIM
-------------------------------------------------------


Kubernetes deployment configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sample files of Kubernetes configuration.

deployment.yaml

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: app-name
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: app-name
     template:
       metadata:
         labels:
           app: app-name
           version: original-version
       spec:
         containers:
         - name: app-name
           image: nginx:alpine
           ports:
           - containerPort: 80
           volumeMounts:
           - name: config
             mountPath: /usr/share/nginx/html
         volumes:
         - name: config
           configMap:
             name: nginx-app-original
     strategy:
     type: RollingUpdate

service.yaml

.. code-block:: yaml

   apiVersion: v1
   kind: Service
   metadata:
     name: app-svc-name
   spec:
     selector:
       app: app-name
       version: original-version
     ports:
     - name: http
       protocol: TCP
       port: 8089
       targetPort: 80
     type: ClusterIP


Blue-Green deployment
^^^^^^^^^^^^^^^^^^^^^

Below is a diagram of the Blue-Green deployment process for Kubernetes VIM:

.. code-block::

                                                                     +---------+
                                                                     |  VNFD   |
                                                                     |         |
                                                                     +-+-------+
                                                                       |
   6. Update    +----------------------+ (Script is included           v     +-------------------+
      Service   | CoordinateVNF script |  in the package)      +----------+  | Change current    |
   +------------+                      +---------------------->|          |  | VNF Package       |
   |            |                      | 5. CoordinateVNF      |   CSAR   |  | Request with      |
   |            |                      |<------------------+   |          |  | Additional Params |
   |            +----------------------+                   |   +----+-----+  +-+-----------------+
   |                                                       |        |          | 1. Change current VNF Package
   |                                                       |        |          |    request
   |                                                       |  +-----+----------+------------------------------+
   |                                                       |  |     v          v        VNFM                  |
   |                                                       |  |  +------------------------------+             |
   |                                                       |  |  |   Tacker-server              |             |
   |                                                       |  |  +--+---------------------------+             |
   |                                                       |  |     |  2. Change current VNF Package request  |
   |                                                       |  |     v                                         |
   |                                                       |  |  +-----------------------------------------+  |
   |                                                       |  |  |                                         |  |
   |                                                       |  |  |   +--------------------------+          |  |
   |                                                       |  |  |   | VnfLcmDriver             |          |  |
   |            +----------------------+                   +--+--+---+                          |          |  |
   |            |  TackerDB            | 9. Update TackerDB   |  |   |                          |          |  |
   |            |                      |<---------------------+--+---+                          |          |  |
   |            +----------------------+                      |  |   |                          |          |  |
   |            +----------------------+                      |  |   +-+---------------+--------+          |  |
   |            |                      | 4. Create New        |  |     | 3. Apply New  | 7. Terminate      |  |
   |            |  +----------------+  |    Deployment        |  |     |    Deployment |    Old            |  |
   |            |  | New Deployment |<-+----------------------+--+-+   v               v    Deployment     |  |
   |            |  |                |  |                      |  | | +--------------------------+          |  |
   |            |  +----------------+  |                      |  | +-+ InfraDriver              |          |  |
   |            |  +----------------+  |                      |  |   |                          |          |  |
   +------------+->| Service        |  |                      |  |   |                          |          |  |
                |  |                |  |                      |  |   |                          |          |  |
                |  +----------------+  | 8. Terminate old     |  | +-+                          |          |  |
                |  +----------------+  |    Deployment        |  | | +--------------------------+          |  |
                |  | Old Deployment |<-+----------------------+--+-+                                       |  |
                |  |                |  |                      |  |                                         |  |
                |  +----------------+  |                      |  |                                         |  |
                |  Kubernetes cluster  |                      |  |                                         |  |
                +----------------------+                      |  |                                         |  |
                                                              |  |    Tacker-conductor                     |  |
                +----------------------+                      |  +-----------------------------------------+  |
                |  Hardware Resources  |                      |                                               |
                +----------------------+                      +-----------------------------------------------+


Sequence for Blue-Green deployment operation (For Kubernetes VIM)

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver"
    "CoordinateVNF script"
    "TackerDB"
    "VIM (Kubernetes)"

    Client -> "Tacker-server"
      [label = "1. POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. ChangeCurrentVNFPackage"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "change_vnfpkg"];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "3. apply_newDeployment"];
    "InfraDriver" -> "VIM (Kubernetes)"
      [label = "4. apply_newDeployment"];
    "InfraDriver" <-- "VIM (Kubernetes)"
      [label = ""];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "CoordinateVNF script"
      [label = "5. coordinate VNF"];
    "CoordinateVNF script" -> "VIM (Kubernetes)"
      [label = "6. update_label"];
    "CoordinateVNF script" <-- "VIM (Kubernetes)"
      [label = ""];
    "VnfLcmDriver" <-- "CoordinateVNF script"
      [label = ""];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "7. terminate oldDeployment"];
    "InfraDriver" -> "VIM (Kubernetes)"
      [label = "8. terminate Old Deployment"];
    "InfraDriver" <-- "VIM (Kubernetes)"
      [label = ""];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "9. Update_DB"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }

#. The Client sends a POST request to the "Individual VNF instance" resource.
#. Tacker-server sends ChangeCurrentVNFPackage request to Tacker-conductor, then Tacker-conductor fetches an on-boarded VNF package and calls VnfLcmDriver.
#. VnfLcmDriver sends a request to the InfraDriver to apply deployment.
#. InfraDriver sends a request to the VIM to apply deployment.
#. VnfLcmDriver calls CoordinateVNF.
#. CoordinateVNF script sends a request to VIM to update label of Kubernetes Service.
#. VnfLcmDriver sends a request to the InfraDriver to delete deployment.
#. InfraDriver sends a request to the VIM to delete deployment.
#. VnfLcmDriver updates the following attributes in TackerDB:

   + ``VnfInstance.vnfdId``
   + ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId``
   + ``VnfInstance.instantiatedVnfInfo.vnfVirtualLinkResourceInfo.networkResource.resourceId``
   + ``VnfInstance.instantiatedVnfInfo.virtualStorageResourceInfo.storageResource.resourceId``
   + ``VnfResource.resourceName``

Rolling update
^^^^^^^^^^^^^^

Below is a diagram of the Rolling update process for Kubernetes VIM:

.. code-block::

                                                     +---------+
                                                     |  VNFD   |
                                                     |         |
                                                     +-+-------+
                                                       |
  +----------------------+ (Script is included         v     +-------------------+
  | CoordinateVNF script |  in the package)    +----------+  | Change current    |
  |                      +-------------------->|          |  | VNF Package       |
  |                      | 5. CoordinateVNF    |   CSAR   |  | Request with      |
  |                      |<----------------+   |          |  | Additional Params |
  +----------------------+                 |   +----+-----+  +-+-----------------+
                                           |        |          | 1. Change current VNF Package
                                           |        |          |    request
                                           |  +-----+----------+------------------------------+
                                           |  |     v          v        VNFM                  |
                                           |  |  +------------------------------+             |
                                           |  |  |   Tacker-server              |             |
                                           |  |  +--+---------------------------+             |
                                           |  |     |  2. Change current VNF Package request  |
                                           |  |     v                                         |
                                           |  |  +-----------------------------------------+  |
                                           |  |  |                                         |  |
                                           |  |  |    +------------------------+           |  |
                                           |  |  |    | VnfLcmDriver           |           |  |
                                           +--+--+----+                        |           |  |
  +----------------------+ 6. Update TackerDB |  |    |                        |           |  |
  | TackerDB             |<-------------------+--+----+                        |           |  |
  +----------------------+                    |  |    |                        |           |  |
  +----------------------+                    |  |    |                        |           |  |
  |                      |                    |  |    +-+----------------------+           |  |
  |  +----------------+  |                    |  |      | 3. Update                        |  |
  |  | Service        |  |                    |  |      v    Deployment                    |  |
  |  +----------------+  | 4. Update          |  |    +------------------------+           |  |
  |  +----------------+  |    Deployment      |  |    | InfraDriver            |           |  |
  |  | Deployment     |<-+--------------------+--+----+                        |           |  |
  |  +----------------+  |                    |  |    |                        |           |  |
  | Kubernetes cluster   |                    |  |    +------------------------+           |  |
  +----------------------+                    |  |                                         |  |
                                              |  |    Tacker-conductor                     |  |
  +----------------------+                    |  +-----------------------------------------+  |
  | Hardware Resources   |                    |                                               |
  +----------------------+                    +-----------------------------------------------+


Sequence for Rolling update operation (For Kubernetes VIM)

.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver"
    "CoordinateVNF script"
    "TackerDB"
    "VIM (Kubernetes)"

    Client -> "Tacker-server"
      [label = "1. POST /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. ChangeCurrentVNFPackage"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "change_vnfpkg"];
    "VnfLcmDriver" -> "InfraDriver"
      [label = "3. apply_newDeployment"];
    "InfraDriver" -> "VIM (Kubernetes)"
      [label = "4. apply_newDeployment"];
    "InfraDriver" <-- "VIM (Kubernetes)"
      [label = ""];
    "VnfLcmDriver" <-- "InfraDriver"
      [label = ""];
    "VnfLcmDriver" -> "CoordinateVNF script"
      [label = "5. coordinate_VNF"];
    "VnfLcmDriver" <-- "CoordinateVNF script"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "6. Update_DB"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }


#. The Client sends a POST request to the "Individual VNF instance" resource.
#. Tacker-server sends ChangeCurrentVNFPackage request to Tacker-conductor, then Tacker-conductor fetches an on-boarded VNF package and calls VnfLcmDriver
#. VnfLcmDriver sends a request to the InfraDriver to apply deployment.
#. InfraDriver sends a request to the VIM to apply deployment.
#. VnfLcmDriver calls CoordinateVNF.

   .. note:: CoordinateVNF has no action for this use case.

#. VnfLcmDriver updates the following attributes in TackerDB:

   + ``VnfInstance.vnfdId``
   + ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId``


Alternatives
------------
None

Data model impact
-----------------
None

REST API impact
---------------

The following RESTful API will be added. This RESTful API will be based on ETSI NFV-SOL003 v3.3.1 [#ETSI-NFV-SOL003-v3.3.1]_.

* | **Name**: change current VNF Package
  | **Description**: Request to change current VNF package by vnfd ID.
  | **Method type**: POST
  | **URL for the resource**: /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg
  | **Request**:

  .. list-table::
      :widths: 15 10 30
      :header-rows: 1

      * - Data type
        - Cardinality
        - Description
      * - ChangeCurrentVnfPkgRequest
        - 1
        - Parameters for the change current VNF package.

  .. list-table::
      :widths: 15 15 10 30 10
      :header-rows: 1

      * - Attribute name
        - Data type
        - Cardinality
        - Parameter description
        - Supported in (Y)
      * - vnfdId
        - Identifier
        - 1
        - Identifier of the VNFD which defines the destination VNF Package for the change.
        - Yes
      * - extVirtualLinks
        - ExtVirtualLinkData
        - 0..N
        - Information about external VLs to connect the VNF to.
        - No
      * - extManagedVirtualLinks
        - ExtManagedVirtualLinkData
        - 0..N
        - Information about internal VLs that are managed by the NFVO.
        - No
      * - vimConnectionInfo
        - map (VimConnectionInfo)
        - 0..N
        - "vimConnectionInfo" attribute array in "VnfInstance".
        - No
      * - additionalParams
        - KeyValuePairs
        - 0..1
        - Additional parameters passed by the NFVO as input to the process.
        - Yes
      * - extensions
        - KeyValuePairs
        - 0..1
        - "extensions" attribute in "VnfInstance".
        - No
      * - vnfConfigurableProperties
        - KeyValuePairs
        - 0..1
        - "vnfConfigurableProperties" attribute in "VnfInstance".
        - No

  User gives following parameter as additionalParams:

  .. list-table:: additionalParams
      :widths: 15 10 30
      :header-rows: 1

      * - Attribute name
        - Cardinality
        - Parameter description
      * - upgrade_type
        - 1
        - Type of file update operation method. Specify Blue-Green or Rolling update.
      * - lcm-operation-coordinate-old-vnf
        - 1
        - The file path of the script that simulates the behavior of CoordinateVNF for old VNF.
      * - lcm-operation-coordinate-old-vnf-class
        - 1
        - The class name of CoordinateVNF for old VNF.
      * - lcm-operation-coordinate-new-vnf
        - 1
        - The file path of the script that simulates the behavior of CoordinateVNF for new VNF.
      * - lcm-operation-coordinate-new-vnf-class
        - 1
        - The class name of CoordinateVNF for new VNF.
      * - vdu_params
        - 0..N
        - VDU information of target VDU to update. Specifying a vdu_params is required for OpenStack VIM and not required for Kubernetes VIM.
      * - > vdu_id
        - 1
        - VDU name of target VDU to update.
      * - > old_vnfc_param
        - 0..1
        - Old VNFC connection information. Required for ssh connection in CoordinateVNF operation for application configuration to VNFC.
      * - >> cp-name
        - 1
        - Connection point name of old VNFC to update.
      * - >> username
        - 1
        - User name of old VNFC to update.
      * - >> password
        - 1
        - Password of old VNFC to update.
      * - > new_vnfc_param
        - 0..1
        - New VNFC connection information. Required for ssh connection in CoordinateVNF operation for application configuration to VNFC.
      * - >> cp-name
        - 1
        - Connection point name of new VNFC to update.
      * - >> username
        - 1
        - User name of new VNFC to update.
      * - >> password
        - 1
        - Password of new VNFC to update.
      * - external_lb_param
        - 0..1
        - Load balancer information that requires configuration changes. Required only for the Blue-Green deployment process of OpenStack VIM.
      * - > ip_address
        - 1
        - IP address of load balancer server.
      * - > username
        - 1
        - User name of load balancer server.
      * - > password
        - 1
        - Password of load balancer server.

  Following is a sample of request body:

  .. code-block:: json

    {
      "vnfdId": "093c38b5-a731-4593-a578-d12e42596b3e",
      "additionalParams": {
        "upgrade_type": "Blue-Green",
        "lcm-operation-coordinate-old-vnf": "./coordinate_old_vnf.py",
        "lcm-operation-coordinate-old-vnf-class": "CoordinateOldVnf",
        "lcm-operation-coordinate-new-vnf": "./coordinate_new_vnf.py",
        "lcm-operation-coordinate-new-vnf-class": "CoordinateNewVnf",
        "vdu_params": {
          "vdu_id": "VDU1",
          "old_vnfc_param": {
            "cp_name": "CP1",
            "username": "ubuntu",
            "password": "ubuntu"
          }
          "new_vnfc_param": {
            "cp_name": "CP1",
            "username": "ubuntu",
            "password": "ubuntu"
          }
        }
        "external_lb_param": {
          "ip_address": "10.10.0.50",
          "username": "ubuntu",
          "password": "ubuntu"
        }
      }
    }

  | **Response**:

  .. list-table::
      :widths: 15 30
      :header-rows: 1

      * - Response Codes
        - Description
      * - 202 Accepted
        - The request was accepted for processing, but the processing has not been completed.
      * - 404 Not Found
        - The requested resource could not be found.
      * - 409 Conflict
        - This operation conflicted with another operation on this resource.

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
  Hirofumi Noguchi<hirofumi.noguchi.rs@hco.ntt.co.jp>

  Masaki Ueno<masaki.ueno.up@hco.ntt.co.jp>

Other contributors:
  Yusuke Niimi<niimi.yusuke@fujitsu.com>

  Yoshiyuki Katada<katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha<ueha.ayumu@fujitsu.com>

Work Items
----------

#. Support for ChangeCurrentVNFPackage API.

#. Implement preamble and postamble for ChangeCurrentVNFPackage

#. VNF software modification performs the following operations:

   A. Blue-Green deployment process for OpenStack VIM.

   B. Rolling update process for OpenStack VIM.

   C. Blue-Green deployment process for Kubernetes VIM.

   D. Rolling update process for Kubernetes VIM.

#. Implements the mechanism by which the VnfLcmDriver invokes the CoordinateVNF script specified in the request parameter.

#. Provide sample CoordinateVNF script to simulate the CoordinateVNF.

Dependencies
============
None

Testing
=======
Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================
Complete user guide will be added to explain upgrading VNF package from the perspective of VNF LCM APIs.

References
==========

.. [#ETSI-NFV-SOL003-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/03.03.01_60/gs_nfv-sol003v030301p.pdf
.. [#ETSI-NFV-SOL002-v3.5.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.05.01_60/gs_NFV-SOL002v030501p.pdf
.. [#ETSI-NFV-IFA007-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-IFA/001_099/007/03.03.01_60/gs_nfv-ifa007v030301p.pdf
.. [#ETSI-NFV-SOL002-v3.3.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/03.03.01_60/gs_NFV-SOL002v030301p.pdf

