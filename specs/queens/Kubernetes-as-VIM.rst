..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


===========================
Kubernetes as VIM in Tacker
===========================
Disscusion document: [#first]_

This proposal describes the plan to add Kubernetes as VIM in Tacker, so Tacker can support cloud
native applications through Python Kubernetes client. OpenStack and Kubernetes will be used as
VIMs for Virtual machine and Container based VNFs respectively. This feature further is used to
create Kubernetes type of containerized VNF(c-VNF) and also hybrid cloud deployments of VM and
Container based VNF, NS.

**Architecture when applying Kubernetes as VIM**

.. code-block:: console

  +-----------------------------------------------+
  |                                               |
  |                   Tacker API                  |
  |                                               |
  +-----------+-------------------------+---------+
              |                         |
              |                         |
  +-----------v--------+     +----------v---------+
  |                    |     |                    |
  |       C-VNFM       |     |        VNFM        |
  |                    |     |                    |
  +-----------+--------+     +----------+---------+
              |                         |
              |                         |
  +-----------v--------+     +----------v---------+
  |                    |     |                    |
  |   Kubernetes VIM   |     |    OpenStack VIM   |
  |                    |     |                    |
  +--------------------+     +--------------------+

  +-----------------------------------------------+
  |        Neutron network & Kuryr Kubernetes     |
  +-----------------------------------------------+


Problem description
===================

Currently Tacker only supports OpenStack as VIM, that means VNFs are created in virtual machines.
In some Telco scenarios, virtualized network services need to quickly react with the change such as
updating, respawning from failure, scaling, migrating. VM-based VNF may not be a good solution,
instead, other solutions such as container should be used. In the other hand, containerized VNFs are
lightweight, small footprint and lower use of system resources, they improve operational efficiency
and reduce operational costs.

Kubernetes is an open source project for automating deployment, scaling and management of
containerized applications. K8s also provides scheduling/deploying a group of related containers,
self-healing features by using service discovery and continuous monitoring. Although it is not yet
suitable for all VNF cases, it is one of the more mature container orchestration engine (COE).
Currently, Kubernetes is chosen as COE in Container4NFV project (OPNFV) [#second]_.

Proposed changes
================

Kubernetes as VIM
-----------------

This proposal is based on current status of available upstream projects (OpenStack, Kubernetes,
Kuryr, etc) to support containerized VNFs in Tacker. Kuryr-kubernetes will be used as networking
between containers and VMs. However, Tacker doesn't manage Kubernetes cluster or care about where
cluster is deployed (on Magnum or bare-metal), Tacker just need their information about Kubernetes
clusters and registers Kubernetes as its VIM. Deploying DPDK, SR-IOV, multiple networking or
storage technologies for container (Kubernetes) should be role of other projects, such as
Container4NFV in OPNFV, that mostly focuses on VIM. OpenStack Tacker will support c-VNF with
enhanced platform-aware (EPA) placement of high-performance NFV workloads in Kubernetes VIM.

**OpenStack VIM configuration change**

Currently, when creating the VIM, its default type is OpenStack. This spec will add 'type'
in vim-config.yaml file to specify which type of VIM.

.. code-block:: console

  auth_url: 'http://127.0.0.1/identity'
  username: 'admin'
  password: 'password'
  project_name: 'demo'
  project_domain_name: 'Default'
  user_domain_name: 'Default'
  type: 'openstack'

**Sample configuration file for creating Kubernetes VIM**

User needs to provide namespace where Kubernetes resources are deployed by specifying in
'project_name'. By default, every Pods will be deployed in namespace *default* if namespace
is not mentioned.

There are two options of Kubernetes API authentication [#third]_:

* Using Bearer token

.. code-block:: console

  auth_url: "https://192.168.11.110:6443"
  bearer_token: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tc2ZqcTQiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjBiMzZmYTQ2LWFhOTUtMTFlNy05M2Q4LTQwOGQ1Y2Q0ZmJmMSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.MBjFA18AjD6GyXmlqsdsFpJD_tgPfst2faOimfVob-gBqnAkAU0Op2IEauiBVooFgtvzm-HY2ceArftSlZQQhLDrJGgH0yMAUmYhI8pKcFGd_hxn_Ubk7lPqwR6GIuApkGVMNIlGh7LFLoF23S_yMGvO8CHPM-UbFjpbCOECFdnoHjz-MsMqyoMfGEIF9ga7ZobWcKt_0A4ge22htL2-lCizDvjSFlAj4cID2EM3pnJ1J3GXEqu-W9DUFa0LM9u8fm_AD9hBKVz1dePX1NOWglxxjW4KGJJ8dV9_WEmG2A2B-9Jy6AKW83qqicBjYUUeAKQfjgrTDl6vSJOHYyzCYQ"
  ssl_ca_cert: "-----BEGIN CERTIFICATE-----
  MIIDUzCCAjugAwIBAgIJANPOjG38TA+fMA0GCSqGSIb3DQEBCwUAMCAxHjAcBgNV
  BAMMFTE3Mi4xNy4wLjJAMTUwNzI5NDI2NTAeFw0xNzEwMDYxMjUxMDVaFw0yNzEw
  MDQxMjUxMDVaMCAxHjAcBgNVBAMMFTE3Mi4xNy4wLjJAMTUwNzI5NDI2NTCCASIw
  DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKlPwd5Dp484Fb+SjBZeV8qF4k8s
  Z06NPdlHKuXaxz7+aReGSwz09JittlqQ/2CwSd5834Ll+btfyTyrB4bv+mr/WD3b
  jxEhnWrUK7oHObzZq0i60Ard6CuiWnv5tP0U5tVPWfNBoHEEPImVcUmgzGSAWW1m
  ZzGdcpwkqE1NznLsrqYqjT5bio7KUqySRe13WNichDrdYSqEEQwFa+b+BO1bRCvh
  IYSI0/xT1CDIlPmVucKRn/OVxpuTQ/WuVt7yIMRKIlApsZurZSt7ypR7SlQOLEx/
  xKsVTbMvhcKIMKdK8pHUJK2pk8uNPAKd7zjpiu04KMa3WsUreIJHcjat6lMCAwEA
  AaOBjzCBjDAdBgNVHQ4EFgQUxINzbfoA2RzXk584ETZ0agWDDk8wUAYDVR0jBEkw
  R4AUxINzbfoA2RzXk584ETZ0agWDDk+hJKQiMCAxHjAcBgNVBAMMFTE3Mi4xNy4w
  LjJAMTUwNzI5NDI2NYIJANPOjG38TA+fMAwGA1UdEwQFMAMBAf8wCwYDVR0PBAQD
  AgEGMA0GCSqGSIb3DQEBCwUAA4IBAQB7zNVRX++hUXs7+Fg1H2havCkSe63b/oEM
  J8LPLYWjqdFnLgC+usGq+nhJiuVCqqAIK0dIizGaoXS91hoWuuHWibSlLFRd2wF2
  Go2oL5pgC/0dKW1D6V1Dl+3mmCVYrDnExXybWGtOsvaUmsnt4ugsb+9AfUtWbCA7
  tepBsbAHS62buwNdzrzjJV+GNB6KaIEVVAdZdRx+HaZP2kytOXqxaUchIhMHZHYZ
  U0/5P0Ei56fLqIFO3WXqVj9u615VqX7cad4GQwtSW8sDnZMcQAg8mnR4VqkF8YSs
  MkFnsNNkfqE9ck/D2auMwRl1IaDPVqAFiWiYZZhw8HsG6K4BYEgk
  -----END CERTIFICATE-----"
  project_name: "default"
  type: "kubernetes"

* Using basic authentication with username and password

.. code-block:: console

  auth_url: "https://192.168.11.110:6443"
  username: "k8s_username"
  password: "k8s_password"
  ssl_ca_cert: "-----BEGIN CERTIFICATE-----
  MIIDUzCCAjugAwIBAgIJANPOjG38TA+fMA0GCSqGSIb3DQEBCwUAMCAxHjAcBgNV
  BAMMFTE3Mi4xNy4wLjJAMTUwNzI5NDI2NTAeFw0xNzEwMDYxMjUxMDVaFw0yNzEw
  MDQxMjUxMDVaMCAxHjAcBgNVBAMMFTE3Mi4xNy4wLjJAMTUwNzI5NDI2NTCCASIw
  DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKlPwd5Dp484Fb+SjBZeV8qF4k8s
  Z06NPdlHKuXaxz7+aReGSwz09JittlqQ/2CwSd5834Ll+btfyTyrB4bv+mr/WD3b
  jxEhnWrUK7oHObzZq0i60Ard6CuiWnv5tP0U5tVPWfNBoHEEPImVcUmgzGSAWW1m
  ZzGdcpwkqE1NznLsrqYqjT5bio7KUqySRe13WNichDrdYSqEEQwFa+b+BO1bRCvh
  IYSI0/xT1CDIlPmVucKRn/OVxpuTQ/WuVt7yIMRKIlApsZurZSt7ypR7SlQOLEx/
  xKsVTbMvhcKIMKdK8pHUJK2pk8uNPAKd7zjpiu04KMa3WsUreIJHcjat6lMCAwEA
  AaOBjzCBjDAdBgNVHQ4EFgQUxINzbfoA2RzXk584ETZ0agWDDk8wUAYDVR0jBEkw
  R4AUxINzbfoA2RzXk584ETZ0agWDDk+hJKQiMCAxHjAcBgNVBAMMFTE3Mi4xNy4w
  LjJAMTUwNzI5NDI2NYIJANPOjG38TA+fMAwGA1UdEwQFMAMBAf8wCwYDVR0PBAQD
  AgEGMA0GCSqGSIb3DQEBCwUAA4IBAQB7zNVRX++hUXs7+Fg1H2havCkSe63b/oEM
  J8LPLYWjqdFnLgC+usGq+nhJiuVCqqAIK0dIizGaoXS91hoWuuHWibSlLFRd2wF2
  Go2oL5pgC/0dKW1D6V1Dl+3mmCVYrDnExXybWGtOsvaUmsnt4ugsb+9AfUtWbCA7
  tepBsbAHS62buwNdzrzjJV+GNB6KaIEVVAdZdRx+HaZP2kytOXqxaUchIhMHZHYZ
  U0/5P0Ei56fLqIFO3WXqVj9u615VqX7cad4GQwtSW8sDnZMcQAg8mnR4VqkF8YSs
  MkFnsNNkfqE9ck/D2auMwRl1IaDPVqAFiWiYZZhw8HsG6K4BYEgk
  -----END CERTIFICATE-----"
  project_name: "default"
  type: "kubernetes"


Tacker supports authenticating with basic information and bearer token. If user want
to use insecure HTTPS request, user can set ssl_ca_cert to "None", but adding certificate
verification is strongly advised.

.. code-block:: console

  ssl_ca_cert: None


See Kubernetes documents [#fourth]_ to get more information about Kubernetes authentication.


**Add Kubernetes HTTP client for managing c-VNF life cycle**

For managing kubernetes type of c-VNF, Tacker will use Python Kubernetes client [#fifth]_.
to manage Kubernetes resources, user can create Pod, Deployment, Horizontal Pod Autoscaling,
Service and ConfigMap in Kubernetes environment.

KubernetesHttpApi class will be initiated in Tacker, it implements Python Kubernetes Client to
manage Kubernetes VIM and in the future it will be used to manage Kubernetes resources for CRUD
c-VNF.

**Assumptions**

This feature will further be utilized to create c-VNF. When Kubernetes as VIM is deployed, user
can create c-VNF with TOSCA template.

TOSCA to Kubernetes translator will be used in Tacker. User can define TOSCA template as
normal, and the translator will translate resources from TOSCA to Kubernetes templates
such as Pod, Deployment, Horizontal Pod Autoscaling, Service and ConfigMap. We plan to apply
translating from TOSCA to Kubernetes in Heat translator.

VNFFG and NS will be rendered through Service (not the Pod), which is implemented as a Load Balancer
in Kuryr-Kubernetes, which meets the VNF Load Balancing Models in ETSI standard [#sixth]_.

Alternatives
------------
There are some other options of implementing containerized VNF in Tacker.

1. Magnum

Magnum is a service to make COE such as Kubernetes, Docker Swarm, Apache Mesos. Considering Magnum
will stitch containerized VNF as nested containers (container inside VM). In this proposal, we
abstract registering Kubernetes as VIM, therefore the Kubernetes clusters can be deployed on VMs
(Magnum) or bare-metal.

2. Zun

In terms of NFV definition, Tacker can use Zun as VIM to manage containers on OpenStack environment.
Zun also provides native OpenStack APIs for managing containers easily.We will consider Zun in the
future when Zun provides the way to register or when it can be separated from OpenStack.

3. Docker

Directly use Dockerfile to create image for VNF in Docker, but we can not limit the resource usages
of each VNF by using Dockerfile. Otherwise, Docker only focuses on CRUD container on each machine,
we need the orchestration tools for scheduling and managing containers on multiple hosts.

4. Multus-CNI [#seventh]_

For multiple networking in Kubernetes, Multus-CNI can be one solution. Currently Kuryr-Kubernetes
doesn't support it. So Multus-CNI will be considered in the future. Kubernetes also has plan for
multiple networking [#eighth]_.

Identity changes
----------------

Kubernetes VIM information includes *username* and *password* or *bearer_token* and *ssl_ca_cert*,
is used for authenticating Kubernetes VIM, these information will be stored in 'vimauth' table.

After authenticating is success, Tacker encrypt secret data (password, bearer_token, ssl_ca_cert)
using fernet key, then fernet key will be stored by Barbican.

Example of encrypting 'password' in Tacker:

.. code-block:: console

  fernet_key, fernet_obj = self.kubernetes.create_fernet_key()

  # password is encrypted by fernet_key
  encoded_auth = fernet_obj.encrypt(auth['password'].encode('utf-8'))

  # store fernet_key in Barbican
  secret_uuid = keymgr_api.store(context, fernet_key)
  auth['key_type'] = 'barbican_key'
  auth['secret_uuid'] = secret_uuid

Everytime Tacker need to execute Kubernetes client, Tacker temporarily create a temp file from
ssl_ca_cert, which is stored in temp folder (eg. /tmp, /var/tmp or /usr/tmp), to authenticate to
Kubernetes master node. After finishing, ssl_ca_cert temp file will be removed.

python-tackerclient and horizon dashboard changes
-------------------------------------------------

1. python-tackerclient

There are several changes in the code to process separately between 'openstack' and 'kubernetes' VIMs
There is no change in syntax of Tacker client commands.

.. code-block:: console

  tacker vim-register --config-file kubernetes-VIM.yaml vim-kubernetes

With kubernetes-VIM.yaml is the configuration file which is already mentioned before.

2. Tacker horizon dashboard

Tacker horizon will add an option to support registering Kubernetes VIM using *bearer_token*
and *ca_ssl_cert*.

Devstack changes
----------------

User can enable kuryr-kubernetes plugin to reuse creating Kubernetes cluster and support neutron
networking between OpenStack VMs and Kubernetes Pods by adding following.

.. code-block:: console

  KUBERNETES_VIM=True
  NEUTRON_CREATE_INITIAL_NETWORKS=False
  enable_plugin kuryr-kubernetes https://git.openstack.org/openstack/kuryr-kubernetes master
  enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas master
  enable_plugin devstack-plugin-container https://git.openstack.org/openstack/devstack-plugin-container master

In the future, Service Function Channing between VM and container based VNFs will be supported.

REST API impact
---------------

None

Security impact
---------------


Notifications impact
--------------------


Other end user impact
---------------------


Performance Impact
------------------


Other deployer impact
---------------------


Developer impact
----------------


Implementation
==============

Assignee(s)
-----------
  Hoang Phuoc <hoangphuocbk2.07@gmail.com>

  Janki Chhatbar <jchhatba@redhat.com>

  Trinath Somanchi <trinath.somanchi@nxp.com>

  Xuan Jia <jiaxuan@chinamobile.com>

Work Items
----------

1. Support creating Kubernetes cluster in devstack environment

2. Add Python Kubernetes client

3. Update Tacker client and horizon

4. Implement Kubernetes as VIM

5. Write tests and documents

Dependencies
============


Testing
=======

(TBD)

Documentation Impact
====================


References
==========
.. [#first] https://docs.google.com/document/d/1zhJxoMc-_nFop8q2aB2mSjXZ_bjMQq1Ju9_P9ppV_Vo/edit#
.. [#second] https://wiki.opnfv.org/display/OpenRetriever/Container4NFV
.. [#third] https://kubernetes.io/docs/admin/authentication/
.. [#fourth] https://kubernetes.io/docs/admin/authentication
.. [#fifth] https://github.com/kubernetes-incubator/client-python
.. [#sixth] http://www.etsi.org/deliver/etsi_gs/NFV-SWA/001_099/001/01.01.01_60/gs_NFV-SWA001v010101p.pdf
.. [#seventh] https://github.com/Intel-Corp/multus-cni
.. [#eighth] https://docs.google.com/document/d/1TW3P4c8auWwYy-w_5afIPDcGNLK3LZf0m14943eVfVg/edit?ts=58877ea7#

