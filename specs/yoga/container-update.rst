..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.
 http://creativecommons.org/licenses/by/3.0/legalcode

=======================================================================
Support VNF update operations on changing VNF instances with MgmtDriver
=======================================================================

Blueprint URL: https://blueprints.launchpad.net/tacker/+spec/container-update

This specification describes VNF Modify Information operation
for configuration support in case of Container update.

Problem description
===================

VNF update API in ETSI NFV-SOL003 v2.6.1 [#ETSI-NFV-SOL003-v2.6.1]_ supports
updating VNFD itself in the current Tacker implementation
`support-vnf-update-api-based-on-etsi-nfv-sol`_,
but there is no way to reflect configuration changes to VNF instances.
Currently there is no preamble or postamble supported in the MgmtDriver
for the Modify VNF operation, so we will support configuration changes
to VNF instances by adding preamble and postamble to MgmtDriver.
There are many use cases for Modify VNF operations, but this specification
focuses on changing the configuration of ConfigMap and Secret in Kubernetes
and changing the image parameters in the Pod and Deployment manifests.

Proposed change
===============
We would propose the following changes:

#. Implement preamble and postamble for modify VNF operation.

   + VnfLcmDriver supports modify_start and modify_end to invoke the process
     provided by MgmtDriver scripts,
     which is created and included in VNF packages by users.
     Refer to `mgmt_driver_deploy_k8s_usage_guide`_ for how to use MgmtDriver.

   .. note::

      modify_start has no action for this use case.

#. Provide Updated manifest file to perform the following operations:

   + Update Kubernetes ConfigMap and Secret.
   + Recreate Kubernetes Pod.

   .. note::

      The image parameter is the only modifiable parameter
      in the manifest file for a Pod or Deployment.
      Changing parameters other than image is not supported
      because they may be inconsistent with information managed by Tacker.

#. Modify VNF operation performs the following operations:

   + The attributes in the TackerDB to be updated are as follows:

     + ``VnfInstance.vnfdId``:
       Replace the existing vnfd ID with the new vnfd ID.
     + ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId``:
       Update resourceId with the new resource ID because the resource ID
       changes after the Pod is recreated.

.. note::

   In the current implementation, this vnfd_id parameter is updated
   in conductor_server.
   We will move this update process of vnfd_id from conductor_server
   to VnfLcmDriver.

.. note::

   The operation flow of the modify VNF is shown below:

   1. Onboard and instantiate the original VNF package.
   2. Onboard the new VNF package and modify the existing VNF instance.

   Because of the above procedure, the old VNF package
   and the new VNF package coexist.
   The old VNF package must be deleted by the user after modify VNF operation.

Design of operation
---------------------

Below is a diagram of the VNF Modify Information operation:

.. code-block::

                                         +---------------+ +--------+
                                         | Updated       | |  VNFD  |
                                         | manifest file | |        |
                                         +-------------+-+ +-+------+
                                                       |     |
                                                       v     v
                                                     +----------+  +------------------+
                                                     |   CSAR   |  | Modify Request   |
                                                     |          |  | with new vnfd_id |
                                                     +----+-----+  +-+----------------+
                                                          |          | 1. Modify VNF Information request
                                                          |          |
                                                    +-----+----------+--------------------------------------+
                                                    |     v          v        VNFM                          |
                                                    |  +------------------------------+                     |
                                                    |  |   Tacker-server              |                     |
                                                    |  +--+---------------------------+                     |
                                                    |     |  2. Modify VNF Information request              |
                                                    |     v                                                 |
  +--------------------------+                      |  +-------------------------------------------+        |
  |  TackerDB                |                      |  |                                           |        |
  |                          |                      |  |    +------------------------+             |        |
  |                          | 4. Update vnfdId     |  |    |  VnfLcmDriver          |             |        |
  |                          |<---------------------+--+----+                        |             |        |
  |                          |                      |  |    |                        |             |        |
  |                          | 6. Update resourceId |  |    |                        |             |        |
  |                          |<---------------------+--+----+                        |             |        |
  |                          |                      |  |    |                        |             |        |
  +--------------------------+                      |  |    +--+-------------------+-+             |        |
                                                    |  |       |  3. modify_start  | 5. modify_end |        |
  +--------------------------+                      |  |       v                   v               |        |
  |  +--------------------+  | 5-1. Replace config  |  |    +------------------------+             |        |
  |  |  Kubernetes        |<-+----------------------+--+----+                        |             |        |
  |  |  ConfigMap/Secret  |  |                      |  |    |  MgmtDriver            |             |        |
  |  +--------------------+  |                      |  |    |                        |             |        |
  |  +--------------------+  | 5-2. Replace Pod     |  |    |                        |             |        |
  |  |  Kubernetes Pod    |<-+----------------------+--+----+                        |             |        |
  |  +--------------------+  |                      |  |    +------------------------+             |        |
  |    Kubernetes cluster    |                      |  |                                           |        |
  +--------------------------+                      |  |   Tacker-conductor                        |        |
  +--------------------------+                      |  +-------------------------------------------+        |
  |    Hardware Resources    |                      |                                                       |
  +--------------------------+                      +-------------------------------------------------------+


Request parameters for operation
----------------------------------
User gives following modify parameter
to "PATCH /vnflcm/v1/vnf_instances/{vnfInstanceId}"
as ``VnfInfoModificationRequest`` data type in:

.. list-table:: Definition of the VnfInfoModificationRequest data type
    :widths: 15 10 30
    :header-rows: 1

    * - Attribute name
      - Cardinality
      - Parameter description
    * - vnfInstanceName
      - 0..1
      - String. "vnfInstanceName" attribute in "VnfInstance".
    * - vnfInstanceDescription
      - 0..1
      - String. "vnfInstanceDescription" attribute in "VnfInstance".
    * - vnfdId
      - 0..1
      - Identifier. "vnfdId" attribute in "VnfInstance".
    * - vnfConfigurableProperties
      - 0..1
      - KeyValuePairs. "vnfConfigurableProperties" attribute in "VnfInstance".
    * - metadata
      - 0..1
      - KeyValuePairs. "metadata" attribute in "VnfInstance".
    * - extensions
      - 0..1
      - KeyValuePairs. "extensions" attribute in "VnfInstance".
    * - vimConnectionInfo
      - 0..N
      - map (VimConnectionInfo). "vimConnectionInfo" attribute array
        in "VnfInstance".
    * - vimConnectionInfoDeleteIds
      - 0..N
      - Identifier. To be deleted from the "vimConnectionInfo"
        attribute array in "VnfInstance",

Following is a sample of request body:

.. code-block:: json

  {
    "vnfdId": "093c38b5-a731-4593-a578-d12e42596b3e"
  }


.. note::

   Refer to chapter REST API impact in the spec
   `support-vnf-update-api-based-on-etsi-nfv-sol`_ for the parameters supported
   by Tacker.

Using ConfigMap and Secret with Kubernetes
--------------------------------------------

ConfigMap and Secret can be used in a Pod either by setting
the environment variable or mounting to volume.
The following are examples of the Kubernetes object file
when using ConfigMap and Secret.

Sample file to define the Kubernetes ConfigMap and Secret:

.. code-block:: yaml

  ---
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: cm-data
  data:
    cmKey1.txt: |
      configmap data
      foo
      bar
  ---
  apiVersion: v1
  kind: Secret
  metadata:
    name: secret-data
  stringData:
    password: 1mbb1G968fb1CUg
    secKey1.txt: |
      secret data
      baz


Sample file of Kubernetes object when using ConfigMap and Secret
as environment variables:

.. code-block:: yaml

   apiVersion: v1
   kind: Pod
   metadata:
     name: env-test
   spec:
     containers:
     - image: alpine
       name: alpine
       env:
       - name: CMENV
         valueFrom:
           configMapKeyRef:
             name: cm-data
             key: cmkey1.txt
       - name: SECENV
         valueFrom:
           secretKeyRef:
             name: secret-data
             key: password
       envFrom:
       - prefix: CM_
         configMapRef:
           name: cm-data
       - prefix: SEC_
         secretRef:
           name: secret-data
   terminationGracePeriodSeconds: 0

Sample file of Kubernetes object when using ConfigMap and Secret
by mounting to volume:

.. code-block:: yaml

   apiVersion: v1
   kind: Pod
   metadata:
     name: modify-VNF-volume-test
   spec:
     containers:
     - image: alpine
       name: alpine
       volumeMounts:
       - name: cm-volume
         mountPath: /config
       - name: sec-volume
         mountPath: /etc/secrets
     volumes:
     - name: cm-volume
       configMap:
         name: cm-data
         defaultMode: 0666
         items:
         - key: cmKey1.txt
           path: cm/config.txt
     - name: secret-volume
       secret:
         secretName: secret-data
         defaultMode: 0600
         items:
         - key: secKey1.txt
           path: creds/secret.txt
   terminationGracePeriodSeconds: 0


Sequence for operation
------------------------
.. seqdiag::

  seqdiag {
    node_width = 80;
    edge_length = 100;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "MgmtDriver"
    "TackerDB"
    "VIM(Kubernetes)"

    Client -> "Tacker-server"
      [label = "1. PATCH /vnflcm/v1/vnf_instances/{vnfInstanceId}"];
    Client <-- "Tacker-server"
      [label = "Response 202 Accepted"];
    "Tacker-server" -> "Tacker-conductor"
      [label = ""];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "2. modify_vnf"];
    "VnfLcmDriver" -> "MgmtDriver"
      [label = "3. modify_start"];
    "VnfLcmDriver" <-- "MgmtDriver"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "4. Update vnfdid"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "VnfLcmDriver" -> "MgmtDriver"
      [label = "5. modify_end"];
    "MgmtDriver" -> "VIM(Kubernetes)"
      [label = "5-1. replace config"];
    "MgmtDriver" <-- "VIM(Kubernetes)"
      [label = ""];
    "MgmtDriver" -> "VIM(Kubernetes)"
      [label = "5-2. recreate Pod"];
    "MgmtDriver" <-- "VIM(Kubernetes)"
      [label = ""];
    "VnfLcmDriver" <-- "MgmtDriver"
      [label = ""];
    "VnfLcmDriver" -> "TackerDB"
      [label = "6. Update resourceid"];
    "VnfLcmDriver" <-- "TackerDB"
      [label = ""];
    "Tacker-conductor" <-- "VnfLcmDriver"
      [label = ""];
  }

.. note::

   The sequence described in the above and the below supposes
   that Tacker fetches the new VNF package in advance.


1. The Client sends a PATCH request to the "Individual VNF instance" resource.

2. Tacker-conductor sends modify VNF request to VnfLcmDriver.

3. VnfLcmDriver calls modify_start of MgmtDriver.

4. VnfLcmDriver updates ``VnfInstance.vnfdId`` in the TackerDB to the ID
   of the new VNFD.

5. VnfLcmDriver calls modify_end of MgmtDriver.
   modify_end uses the "kubectl replace" command to replace ConfigMap,
   Secret, and Pod.

   5-1. MgmtDriver sends request to replace config of ConfigMap and Secret
   to the VIM (Kubernetes).

   5-2. MgmtDriver sends request to recreate Pod to the VIM (Kubernetes).

   .. note::

      It is desirable to recreate only the Pods that refer the changed
      ConfigMap or Secret, but in this time we are considering to recreate
      all Pods defined in the same package.
      From the viewpoint of the data model of the VnfInfoModificationRequest,
      it is necessary to continue to examine which parameter is appropriate
      as a parameter for specifying this or whether a parameter
      for this purpose exists.

   .. note::

      If the image parameter in the manifest file for the Pod or Deployment
      has changed, the image will be replaced when the Pod is recreated.

6. VnfLcmDriver updates
   ``VnfInstance.instantiatedVnfInfo.vnfcResourceInfo.computeResource.resourceId``
   in the TackerDB to the ID of the recreated Pod.



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
  Hirofumi Noguchi<hirofumi.noguchi.rs@hco.ntt.co.jp>

  Masaki Ueno<masaki.ueno.up@hco.ntt.co.jp>

Other contributors:
  Yusuke Niimi<niimi.yusuke@fujitsu.com>

  Yoshiyuki Katada<katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha<ueha.ayumu@fujitsu.com>

Work Items
----------
#. Add preamble and postamble of Modify VNF Information operation
   using MgmtDriver.

#. Add a Updated manifest file that performs the following,
   to reflect configuration changes in VNF instance:

   + Update Kubernetes ConfigMap and Secret.
   + Recreate Kubernetes Pod.

#. Add Modify VNF operation to perform the following:

   + Update vnfdId and resourceId attribute in TackerDB.

Dependencies
============
None

Testing
=======
Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================
Complete user guide will be added to explain modifying VNF information
from the perspective of VNF LCM APIs.

References
==========

.. [#ETSI-NFV-SOL003-v2.6.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. _support-vnf-update-api-based-on-etsi-nfv-sol : https://specs.openstack.org/openstack/tacker-specs/specs/victoria/support-vnf-update-api-based-on-etsi-nfv-sol.html
.. _mgmt_driver_deploy_k8s_usage_guide : https://docs.openstack.org/tacker/wallaby/user/mgmt_driver_deploy_k8s_usage_guide.html
