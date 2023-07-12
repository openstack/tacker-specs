..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


======================================================================
Support Kubernetes Custom Resources for Cluster API Provider OpenStack
======================================================================

This specification describes the enhancement of Kubernetes infra-driver in
Tacker to support LCM operation of Kubernetes Custom Resources (CR) as CNF,
using Kubernetes Cluster API (CAPI) [#capi]_ as an example CR. The scope of the
present document includes instantiation, termination, scale and update of CNFs
including CRs for CAPI.

https://blueprints.launchpad.net/tacker/+spec/support-k8s-cr


Problem description
===================

Tacker only allows specific types (a.k.a., kind) of Kubernetes resources and
CR, which is user-defined kinds complying with the Kubernetes API, is not
included yet. However, CRs are already widely used to instruct Kubernetes to
manage more than just containers. For example, CAPI enables users to manage
Kubernetes clusters as Kubernetes resources by defining some CRs, such as
Cluster, Machine, etc, corresponding to the components composing Kubernetes
clusters. By supporting CAPI CRs, Tacker can create Kubernetes Cluster with
Kubernetes infra-driver, which is much simpler than existing Tacker's
management drivers for similar use cases [#tacker_k8s_cluster1]_,
[#tacker_k8s_cluster2]_.

As described above, the limited supported resources in Tacker may prevent a
better implementation. In this sense, adding base classes and utilities for
handling CRs in Kubernetes infra-driver helps other developers to extend the
supported CRs in the future, such as some prerequisites (e.g., drivers, device
plugins, etc) to use GPU from containers [#nvidia_gpu]_.

Proposed change
===============

This spec proposes to support CRs of CAPI, including enhancement of the
Kubernetes infra-driver to handle LCM operations for CRs. CAPI is a set of CRs
to bring declarative, Kubernetes-style APIs to cluster creation, configuration,
and management. Using CAPI as an example of CNF consisting of CRs, creating the
basic utilities and classes to add more CRs in the future.

For this to happen, the following items have to be implemented.

* Instantiation of CNF including CRs (using Cluster API as an example)
* Termination of CNF including CRs (using Cluster API as an example)
* Scaling of CNF including CRs (using Cluster API as an example)
* Updating of CNF including CRs (using Cluster API as an example)
* Sample VNF (i.e., CNF) packages with manifests of CRs for CAPI
* Updating user document

Kubernetes Custom Resources
---------------------------

Custom resources are extensions of the Kubernetes API. This feature allows
users to define new resource types, beyond the built-in resources of
Kubernetes, such as Pods, Services, and Deployments. Once a custom resource is
installed, users can create and access its objects using Kubernetes APIs, just
as they do for built-in resources.

Some examples of popular custom resources for projects are:

* Cluster API: Cluster, MachineDeployment, MachineSet, Machine, etc
* Istio: VirtualService, DestinationRule, and Gateway.
* Prometheus: ServiceMonitor
* Elasticsearch: Elasticsearch
* Kubernetes Operators: Kubernetes Operators are a way to automate the
  deployment and management of complex applications on Kubernetes. Examples
  include the Nvidia GPU operator, the PostgreSQL operator, and the MongoDB
  operator.

In general, to use custom resources, users have to install CR Definition (CRD)
and CR controller to Kubernetes cluster.

Cluster API
-----------

We picked CAPI as the first CR Tacker support because Tacker already covered a
similar use case. Tacker has supported deploying a Kubernetes cluster by using
management drivers. CAPI
enables users to manage Kubernetes clusters as Kubernetes resources by defining
some CRs, such as Cluster, Machine, etc, corresponding to the components
composing Kubernetes clusters. Therefore, by supporting CAPI CRs we can create
Kubernetes Cluster with Kubernetes infra-driver.

The following are the characteristics of CAPI:

#. Management Cluster and Workload Cluster
    CAPI is also a Kubernetes resource and must be deployed on a cluster.
    Therefore, when using CAPI, there are two types of clusters: clusters where
    CAPI is installed and clusters that are created by CAPI. In CAPI, the
    former is called a Management Cluster and the latter a Workload Cluster.
#. Providers
    CAPI consists of a number of CR called Providers and their controllers.
    Among them, the infrastructure provider is particularly unique. There are
    many providers and each provider supports different cloud platforms. For
    example, CAPI Provider OpenStack (CAPO) is used to build a Kubernetes
    cluster on OpenStack. The role of an infrastructure provider is to prepare
    nodes (in most cases, creating VMs) for Kubernetes clusters and
    install/configure Kubernetes components (e.g., etcd, kube-api server) on
    those nodes.

This figure shows the overview of the operation of CAPI.

.. uml::

    @startuml

    actor User
    package manifest
    component ManagementCluster {
        component "ClusterAPI" as capi
        component "KubernetesAPI" as kapi1
    }
    component Infrastructure {
        component WorkloadCluster {
            component "KubernetesAPI" as kapi2
        }
    }

    User --> manifest: 2. create
    User -> kapi1: 3. apply manifest
    kapi1->capi
    capi -> WorkloadCluster: 4. create
    User -> ManagementCluster: 1. create


    @enduml


Officially supported providers (i.e., cloud platforms) [#capi_providers]_ are:

* AWS
* Azure
* Azure Stack HCI
* BYOH
* CloudStack
* CoxEdge
* DigitalOcean
* Equinix Metal (formerly Packet)
* GCP
* Hetzner
* IBM Cloud
* KubeKey
* KubeVirt
* MAAS
* Metal3
* Microvm
* Nested
* Nutanix
* OCI
* OpenStack
* Outscale
* Sidero
* Tinkerbell
* vcluster
* Virtink
* VMware Cloud Director
* vSphere

Among them, we choose OpenStack (i.e., CAPO) for the first step. This is
simply because it is easier to test and matches the previous use cases
supported by management drivers.


Enhancement of Kubernetes Infra-driver for CAPI
-----------------------------------------------

In this section, we describe the enhancement of Kubernetes Infra-driver to
create Kubernetes clusters with CAPI. As described in the previous section, we
need to create two kinds of Kubernetes clusters: i) Management Cluster and ii)
Workload Cluster. We first explain the steps to create those two Kubernetes
clusters, then we also describe scaling and changing current VNF package
operations of the Workload Cluster.

Creating Management Cluster
```````````````````````````

This figure shows an overview of creating Management Cluster with Kubernetes
infra-driver supporting CRs of CAPI. As CAPI itself consist of Kubernetes
resources, creating Management Cluster can be the same operation as Instantiate
CNF. Terminate CNF is omitted as it is almost the same as the Instantiate CNF.
Also, LCM operations other than instantiation/termination are out of the scope
of this specification.

#. Request create CNF
    Users request create CNF with a VNF package that contains CAPI CRDs.
#. Request instantiate VNF
    Users request instantiate VNF with an instantiate parameters.
#. Call Kubernetes API
    Kubernetes infra-driver calls Kubernetes APIs to create a set of CRs of
    CAPI as a CNF.
#. Create a set of CRs for CAPI
    Kubernetes Control Plane creates a set of CRs according to the contents of
    the VNF package.

Upon CRs successfully deployed, CAPI is available on Kubernetes VIM (i.e.,
Kubernetes VIM becomes Management Cluster).

.. uml::

    @startuml

    frame "python-tackerclient" {
        component "tacker-client" as client {
        package "VNF Package" as vnfpkg {
            file "VNFD" as vnfd
            file "CNF (Cluster API)\nDefinition" as cnfd
        }
        file "Instantiate\nparameters" as inst_param
    }
    }

    frame "tacker" {
        component "tacker-server" {
            component "Server" as serv
        }
        component "tacker-conductor" {
            component "Conductor" as cond
          component "Vnflcm driver" as vld
            component "Kubernetes\ninfra-driver" as infra
        }
    }

    frame "Kubernetes Cluster" as k8s {
    node "Control Plane" as k8s_m {
            node "Cluster API" as capi
    }
    node "Worker" as k8s_w
    }

    '# Relationships
    vnfpkg --> serv: 1. Request\n create VNF
    inst_param --> serv: 2. Request\n instantiate VNF
    serv --> cond
    cond --> vld
    vld --> infra
    infra -right-> k8s_m: 3. Call Kubernetes\n API
    k8s_m -> capi: 4. Create a CRs\n for Cluster API

    capi -[hidden]-> k8s_w

    @enduml


Creating Workload Cluster
`````````````````````````

This figure shows an overview of creating Workload Cluster with Kubernetes
infra-driver supporting CRs of CAPO. As CAPI defines Kubernetes cluster as
Kubernetes resources, creating Workload Cluster corresponds can be the same
operation as Instantiate CNF. Terminate CNF is omitted as it is almost the
same as the Instantiate CNF.

#. Request create VNF
    Users request create VNF with a VNF package that contains CAPI CRDs.
#. Request instantiate VNF
    Users request instantiate VNF with an instantiate parameters.
#. Call Kubernetes API
    Kubernetes infra-driver calls Kubernetes APIs to create a set of CRs of
    CAPI as a CNF.
#. Create a Cluster resource
    Kubernetes Control Plane creates a Cluster resource. In general, several
    sub resources are also created which are omitted in the figure.
#. Create a Workload Cluster
    CAPI creates Workload Cluster according to the contents of VNF Package.
#. Execute the management driver
    The vnflcm driver executes management driver contained in VNF
    Package.
#. Get credentials for Workload Cluster
    The management driver obtains credentials for Workload Cluster which is
    automatically stored as Secret on Management Cluster by CAPI.
#. Send the credentials
    The management driver sends obtained credentials to the web server
    according to the pre-configured URL. The web server must be managed by
    users to receive credentials.

.. note:: In order to use the Workload Cluster as VIM, users have to register
          VIM with the credentials sent by the management driver.

.. uml::

  @startuml

  component "Web Server" as w

  frame "python-tackerclient" {
      component "tacker-client" as client {
      package "VNF Package" as vnfpkg {
          file "VNFD" as vnfd
          file "CNF (k8s Cluster)\nDefinition" as cnfd
        file "Scripts for\n Management Driver\n(Credentials Sender)" as mgmtd
      }
      file "Instantiate\nparameters" as inst_param
  }
  }

  vnfd -[hidden]> cnfd
  cnfd -[hidden]> mgmtd

  frame "tacker" {
      component "tacker-server" {
          component "Server" as serv
      }
      component "tacker-conductor" {
          component "Conductor" as cond
          component "Vnflcm driver" as vld
          component "Kubernetes\ninfra-driver" as infra
      }
  }

  frame "Management Cluster" as mgmt {
  node "Control Plane" as k8s_m_m {
          node "Cluster API" as capi
  }
      node "Worker" as k8s_m_w {
          node "Cluster" as cluster
      }
  }

  component "Management Driver\n(Credentials Sender)" as mgmtdi

  cloud "Hardware Resources" as hw_w {
  frame "Workload Cluster" as wkld {
  node "Control Plane" as k8s_w_m
      node "Worker" as k8s_w_w {
      }
  }
  }

  '# Relationships
  vnfpkg --> serv: 1. Request\n create VNF
  inst_param --> serv: 2. Request\n instantiate VNF
  serv --> cond
  cond --> vld
  vld --> infra
  infra -right-> k8s_m_m: 3. Call Kubernetes\n API
  capi --> cluster: 4. Create a Cluster Resource
  cluster --> wkld: 5. Create a Workload Cluster
  k8s_w_m -[hidden]-> k8s_w_w
  vld -right-> mgmtdi: 6. Execute management driver
  mgmtdi <--- mgmt: 7. Get credentials for Workload Cluster
  mgmtdi -> w: 8. Send credentials


  @enduml

Scale Workload Cluster
``````````````````````

This figure shows an overview of scaling Workload Cluster with Kubernetes
infra-driver supporting CRs of CAPO.

#. Request scale VNF
    Users request scale VNF
#. Call Kubernetes API
    Kubernetes infra-driver calls Kubernetes APIs to change a parameter that
    represents the number of worker nodes in the Workload Cluster which must be
    ``replicas``.
#. Change a parameter for the number of worker nodes
    CAPI in Kubernetes Control Plane changes the parameter for the number of
    worker nodes according to the API calls.
#. Change the number of worker nodes
    CAPI changes the number of worker nodes according to the Cluster resource.


.. uml::

  @startuml

  frame "python-tackerclient" {
      component "tacker-client" as client {
  }
  }

  frame "tacker" {
      component "tacker-server" {
          component "Server" as serv
      }
      component "tacker-conductor" {
          component "Conductor" as cond
          component "Vnflcm driver" as vld
          component "Kubernetes\ninfra-driver" as infra
      }
  }

  frame "Management Cluster" as mgmt {
  node "Control Plane" as k8s_m_m {
          node "Cluster API" as capi
  }
      node "Worker" as k8s_m_w {
          node "Cluster" as cluster
      }
  }

  cloud "Hardware Resources" as hw_w {
  frame "Workload Cluster" as wkld {
  node "Control Plane" as k8s_w_m
      node "Worker" as k8s_w_w
      node "Worker" as k8s_w_w2
  }
  }

  '# Relationships
  client --> serv: 1. Request\n scale VNF
  serv --> cond
  cond --> vld
  vld --> infra
  infra -right-> k8s_m_m: 2. Call Kubernetes\n API
  capi --> cluster: 3. Change a parameter\n for the number of worker nodes
  cluster --> wkld: 4. Change the number of worker nodes
  k8s_w_m -[hidden]-> k8s_w_w
  k8s_w_m -[hidden]-> k8s_w_w2

  @enduml

Update Workload Cluster
```````````````````````

This figure shows an overview of updating Workload Cluster with Kubernetes
infra-driver supporting CRs of CAPO. Similar to the other Kubernetes
resources, CRs of CAPI (e.g., Cluster) can be updated by applying the updated
version of manifest. This operation can be covered by the change current VNF
package in Tacker.

#. Request update VNF
    Users request to change the current VNF package
#. Call Kubernetes API
    Kubernetes infra-driver calls Kubernetes APIs to override Cluster resource.
#. Change a parameter for the number of worker nodes
    CAPI in Kubernetes Control Plane changes the Cluster resource according to
    the API calls.
#. Change the number of worker nodes
    CAPI changes worker nodes according to the Cluster resource.

.. uml::

  @startuml

  frame "python-tackerclient" {
      component "tacker-client" as client {
  }
  }

  frame "tacker" {
      component "tacker-server" {
          component "Server" as serv
      }
      component "tacker-conductor" {
          component "Conductor" as cond
          component "Vnflcm driver" as vld
          component "Kubernetes\ninfra-driver" as infra
      }
  }

  frame "Management Cluster" as mgmt {
  node "Control Plane" as k8s_m_m {
          node "Cluster API" as capi
  }
      node "Worker" as k8s_m_w {
          node "Cluster" as cluster
      }
  }

  cloud "Hardware Resources" as hw_w {
  frame "Workload Cluster" as wkld {
  node "Control Plane" as k8s_w_m
      node "Worker" as k8s_w_w
      node "Worker" as k8s_w_w2
  }
  }

  '# Relationships
  client --> serv: 1. Request\n change current VNF package
  serv --> cond
  cond --> vld
  vld --> infra
  infra -right-> k8s_m_m: 2. Call Kubernetes\n API
  capi --> cluster: 3. Update the resources
  cluster --> wkld: 4. Change the resources of worker nodes
  k8s_w_m -[hidden]-> k8s_w_w
  k8s_w_m -[hidden]-> k8s_w_w2

  @enduml

Alternatives
------------

None.

Data model impact
-----------------

None.

REST API impact
---------------

None.

Security impact
---------------

None.

However, we have to carefully manage credentials for created Workload Cluster.
CAPI stores those credentials as Secret of Management Cluster. Therefore,
unless the security of Management Cluster is violated, the credentials are
safe. Such security management is the out of scope of Tacker.

Notifications impact
--------------------

None.

Other end user impact
---------------------

None.

Performance Impact
------------------

None.

Other deployer impact
---------------------

* Deployer who uses this feature may have to create a server to receive
  credentials for Workload Cluster and may have to create script to register
  those credentials as VIM.
* Deployer who uses this feature may have to prepare VNF packages containing
  appropriate CAPI CRs and cluster definitions.

Developer impact
----------------

* VNF package developers need to contain the management driver to obtain the
  credentials of Workload Cluster or alternative scripts to do the same thing.
* VNF package developers may need to update the packages according to the
  update of CAPI.
* VNF package developers may need to fix bugs in the package caused by CAPI.
* Tacker developers may need to fix bugs in Kubernetes infra-driver caused by
  CAPI.
* Developers may need to be careful to change components of Tacker, especially
  when they want to support additional CRs in Kubernetes infra-driver so that
  it complies with implementation of the present document.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  * Reina Yoshitani <yoshitanir@intellilink.co.jp>

Other contributors:
  * Shun Higuchi <higuchis@intellilink.co.jp>
  * Hiromu Asahina (hiromu) <hiromu.asahina@ntt.com> <hiromu.a5a@gmail.com>

Work Items
----------

* Instantiation of CNF including CRs (using Cluster API as an example)
* Termination of CNF including CRs (using Cluster API as an example)
* Scaling of CNF including CRs (using Cluster API as an example)
* Updating of CNF including CRs (using Cluster API as an example)
* Sample VNF (i.e., CNF) packages with manifests of CRs for CAPI
* Updating user document

Dependencies
============

* Kubernetes v1.25.0 or later

Testing
=======

We can enhance existing functional tests for Kubernetes VIM by adding test
cases for CRs. Those CRs do not necessarily have to be CAPI as the main scope
of the present document is to support CRs.

Documentation Impact
====================

Need to explain the use cases of the enhanced Kubernetes infra-driver.

References
==========

.. [#capi] https://cluster-api.sigs.k8s.io/
.. [#nvidia_gpu] https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/getting-started.html#install-nvidia-gpu-operator
.. [#tacker_k8s_cluster1] https://docs.openstack.org/tacker/latest/user/mgmt_driver_deploy_k8s_usage_guide.html
.. [#tacker_k8s_cluster2] https://docs.openstack.org/tacker/latest/user/mgmt_driver_deploy_k8s_kubespary_usage_guide.html
.. [#capi_providers] https://cluster-api.sigs.k8s.io/reference/providers.html
