..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==================================================
Add Kubernetes type of containerized VNF to Tacker
==================================================


Problem description
===================

Kubernetes [#first]_ is a container orchestration project that is part of the Cloud Native
Computing Foundation. Because container use OS virtualization instead of hardware virtualization,
therefore container based VNF is lighter than VM based VNF. In this spec, we propose to support
network functions as containers using Kubernetes type, that will be deployed on Kubernetes VIM.

Proposed change
===============

**Tacker architecture with OpenStack and Kubernetes as VIM**

.. code-block:: console

        +--------------------------------------------------------------------+
        |                                                                    |
        |                            Tacker NFVO                             |
        |                                                                    |
        |                                                                    |
        +---------------------------------+----------------------------------+
                                          |
        +---------------------------------v----------------------------------+
        |VNFM                                                                |
        |        +---------------+                  +---------------+        |
        |        |  Kubernetes   |                  |     Heat      |        |
        |        | infra driver  |                  | infra driver  |        |
        |        +------+--------+                  +--------+------+        |
        |               |                                    |               |
        +--------------------------------------------------------------------+
                        |                                    |
        +---------------v--------------+       +-------------v---------------+
        |                              |       |                             |
        |          Kubernetes VIM      |       |       OpenStack VIM         |
        |                              |       |                             |
        +------------------------------+       +-----------------------------+

        +--------------------------------------------------------------------+
        |                     Neutron network & kuryr-kubernetes             |
        +--------------------------------------------------------------------+

In this plan, we will introduce Kubernetes infra driver in VNFM, that will be used to manage c-VNF
in Kubernetes VIM. Kubernetes infra driver use Kubernetes APIs through Kubernetes python client to
create Kubernetes resources like Service, Deployment, ConfigMap, Horizontal Pod Autoscaling, which
will be used as a C-VNF. Kuryr-Kubernetes also use to connect between VM based and container based
VNFs.

**Introduce TOSCA to Kubernetes translator**

.. code-block:: console

                                     +-------------------+
                                     |                   |
                              +------>   TOSCA Parser    |
                              |      |                   |
                              |      |                   |               +-------------------+
      +-------------------+   |      +-------------------+        +------>    K8s service    |
      |                   |   |                                   |      |      template     |
      |       TOSCA       +---+                                   |      +-------------------+
      |    VNF template   |   |                                   |
      |                   |   |      +-------------------+        |
      +-------------------+   |      |    TOSCA to K8S   |        |      +-------------------+
                              +------>     translator    +--------------->   K8s deployment  |
                                     |      (Phase 1)    |        |      |     template      |
                                     |                   |        |      +-------------------+
                                     +----------+--------+        |
                                                |                 |
                                                |                 |      +-------------------+
                                                |                 +------>   K8s Configmap   |
                                     +----------v--------+        |      |      template     |
                                     |                   |        |      +-------------------+
                                     |  Heat Traslator   |        |
                                     | (Phase 2 - Future)|        |
                                     |                   |        |      +-------------------+
                                     +-------------------+        +------>    Horizon Pod    |
                                                                         |    Autoscaling    |
                                                                         +-------------------+

Tacker will implement TOSCA to K8S translator, to help translating from TOSCA NFV tempalte to K8S
template. The benifit of translator is unified VNF template, using one kind of template (TOSCA
template), we can deploy it on multiple environments.

We have plan to work with translator in 2 phases:

1. Phase 1, TOSCA to K8S translator will be applied in Tacker first.

2. Phase 2, Tacker will move "TOSCA to K8S" to Heat Translator if possbile


**TOSCA to K8S translator use idea from Kompose project (https://github.com/kubernetes/kompose)**

There are 2 main parts:

1. Loader:

User can find Loader function in "translate_input.py" on tacker/vnfm/infra_drivers/kubernetes/k8s
Firstly, Tacker load TOSCA VNF template to in-memory TOSCA object. After that, map in-memory TOSCA
object to "ToscaKubeObject" objects.

2. Transformer:

This function is described in "translate_output.py" on tacker/vnfm/infra_drivers/kubernetes/k8s
translate_output.py translates ToscaKubeObjects to Kubernetes objects (currently, we only support
translate to Deployment, Service, Horizon Pod Autoscaling - HPA and ConfigMap).

.. code-block:: console


                           +------------------+
                           |TOSCA NFV template|
                           +------------------+
                                    |
                                    |  TOSCA Parser
                                    |
                       +------------v-------------+
                       |      In-memory TOSCA     |
    Loader             |          object          |
                       +--------------------------+
                                    |
                                    |
                                    |
                       +------------v--------------+
                       |      ToscaKubeObject      |
                       |                           |
                       +---------------------------+
                                    |
    +------------------------------------------------------------+
                                    |
                                    |
                       +------------v--------------+
                       |  ConfigMap, Deployment,   |
    Tranformer         |    Service, HPA           |
                       +---------------------------+
                                    |
    +------------------------------------------------------------+
                                    |
                                    |
                       +------------v--------------+
    Outputter          |      output objects       |
                       |                           |
                       +---------------------------+


Currently Kubernetes doesn't support multiple network, CP and VL are not mentioned in translating
to real entity. In implementation, we add network name as label of Service object in Kubernetes
such as: {"network_name": "net_mgmt"}

1. Definition of ToscaKubeObject:

ToscaKubeObject holds the basic struct of a VDU. That is used for translating TOSCA to Kubernetes
templates such as Service, Deployment, Horizon Pod Autoscaling, ConfigMap. We choose Deployment
to support scaling out/in manually and guaranty the number of pods. Service helps balance traffic
to replicas in Deployment.

.. code-block:: console

  class ToscaKubeObject(object):
    def __init__(self, name=None, namespace=None, mapping_ports=None,
                 containers=None, network_name=None,
                 mgmt_connection_point=False, scaling_object=None,
                 service_type=None, labels=None):
      self._name = name
      self._namespace = namespace
      self._mapping_ports = mapping_ports
      self._containers = containers
      self._network_name = network_name
      self._mgmt_connection_point = mgmt_connection_point
      self._scaling_object = scaling_object
      self._service_type = service_type
      self._labels = labels

Example of an VDU in Tacker:

.. code-block:: console

    VDU1:
      type: tosca.nodes.nfv.VDU.Tacker
      properties:
        namespace: default
        mapping_ports:
          - "80:8080"
          - "443:443"
        labels:
          - "app: webserver"
        service_type: ClusterIP
        vnfcs:
          web_server:
            properties:
              num_cpus: 0.5
              mem_size: 512 MB
              image: celebdor/kuryr-demo
              ports:
                - "8080"
              config: |
                param0: key1
                param1: key2

Tacker map VDU's properties to ToscaKubeObject, which is mainly used to define Service, Deployment
and its Containers:

* name: set as "svc-" + VDU name + random uuid, such as "svc-VDU1-2k531". Tacker will set all Kubernetes
  objects with this name for managing.

* namespace: namespace of kubernetes where Service, Deployment, HPA, ConfigMap objects are deployed.

* mapping_ports: published ports and target ports (container ports) of Service Kubernetes.

* containers: it defines Container objects in Pod. See "2. Definition of VnfcConfigurableProperties"
  to know about how to model each container.

* labels: set labels for all Kubernetes objects as selector. If labels is not provided,
  {'selector': 'service-VDU1'} will be used as default.

* service_type: set service type for Service object, example "service_type: ClusterIP". Currently,
  Tacker only support ClusterIP and NodePort.

* scaling_object: used to map scaling policy to Horizontal Pod Autoscaling. See more details in
  "3. Definition of Scaling policy".

* network_name: network of VDU, for pure Kubernetes, it is used when enable neutron network
  with Kuryr-Kubernetes.

2. Definition of VnfcConfigurableProperties

Each instance of VnfcConfigurableProperties presents for a Container. To parser this type, Tacker
add new "VDU.tosca.datatypes.nfv.VnfcConfigurableProperties" datatype. In the example below, we
define two Containers as VnfcConfigurableProperties are front_end and backend.

.. code-block:: console

    VDU1:
      type: tosca.nodes.nfv.VDU.Tacker
      properties:
        namespace: default
        mapping_ports:
          - "80:80"
          - "88:88"
        labels:
          - "app: rss-site"
        vnfcs:
          front_end:
            properties:
              num_cpus: 0.5
              mem_size: 512 MB
              image: nginx
              ports:
                - "80"
          rss_reader:
            properties:
              num_cpus: 0.5
              mem_size: 512 MB
              image: nickchase/rss-php-nginx:v1
              ports:
                - "88"

To model it, we define class Container. When translate to Kubernetes objects, it is transformed
to **Container** objects in each Deployment object in Kubernetes. Container holds the basic
struct of a container inside Pod.

.. code-block:: console

  class Container(object):
    def __init__(self, name=None, num_cpus=None, mem_size=None, image=None,
                 command=None, args=None, ports=None, config=None):
      self._name = name
      self._num_cpus = num_cpus
      self._mem_size = mem_size
      self._image = image
      self._command = command
      self._args = args
      self._ports = ports
      self._config = config

Tacker map each instances of VnfcConfigurableProperties to Container object in Pod Kubernetes.

* name: container's name, such as front_end, rss_reader

* num_cpus: specify CPU resource for each Container (num_cpus can be integer or
  float with decimal point, e.g. 1,3,0.5,1.25 and precision finer than 1m is
  not allowed)

* mem_size: specify memory (RAM) resource (e.g. 200 KiB, MiB, GiB, KB, MB, GB)

* image: container's image

* ports: container's exposed ports

* command: example ['/bin/sh', 'echo']

* args: example ['hello']

* config: set value for variables, example

.. code-block:: console

  config: |
    param0: key1
    param1: key2

All configs will be translate to ConfigMap object in Kubernetes.

3. Definition of Scaling policy

Tacker map Scaling policy to ScalingObject class. When transform to Kubernetes object, it is
described as **Horizon Pod Autoscaling**. We can look at mapping between ScalingObject and
Scaling policy in below.

.. code-block:: console

  class ScalingObject(object):
    def __init__(self, scaling_name=None, min_replicas=None, max_replicas=None,
                 scale_target_name=None, target_cpu_utilization_percentage=None):
      self._scaling_name = scaling_name
      self._min_replicas = min_replicas
      self._max_replicas = max_replicas
      self._scale_target_name = scale_target_name
      self._target_cpu_utilization_percentage = target_cpu_utilization_percentage


  policies:
    - SP1:
      type: tosca.policies.tacker.Scaling
      targets: [VDU1]
      properties:
        min_instances: 1
        max_instances: 3
        target_cpu_utilization_percentage: 40

In the future, we are going to upgrade to ScalingV2 to support more alarm metrics than
CPU utilization.

4. C-VNF Model in Tacker

This C-VNF model is composed of three parts above.

.. code-block:: console


                         VNF
                         +----------------------------------------------------------------------+
                         |                                                                      |
                         |           VDU2                                                       |
                         |           +---------------------------------------------------+      |
                         |      VDU1 |                                                   |      |
                         |      +-----------------------------------------------------+  |      |
                         |      |                                                     |  |      |
                         |      |                           +---------------------+   |  |      |
  +---------------+      |      |    +---------------+     +--------------------+ |   |  |      |
  |               |      |      |    |               |     |                    | |   |  |      |
  |    Peer NF    +------+      |    |      K8S      +-----+    Deployment,     | |   |  |      |
  |               |      |      |    |    Service    |     | HPA, ConfigMap, etc| |   |  |      |
  +---------------+      |      |    |               |     |                    +-+   |  |      |
                         |      |    +---------------+     +--------------------+     +--+      |
                         |      |                                                     |         |
                         |      +-----------------------------------------------------+         |
                         |                                                                      |
                         |                                                                      |
                         +----------------------------------------------------------------------+


This picture depicts the C-VNF models [#third]_ in Kubernetes VIM. In this figure, a VNF includes
two VDUs: VDU1 and VDU2 (VNF can have more than one VDUs). Each VDU, we map it to Service,
Deployment, Horizon Pod Autoscaling and ConfigMap objects in Kubernetes. All components in 1 VDU,
which are using the same name (e.g. svc-VDU1-24k41da) for managing.

We support scaling VDU manually through scaling replica function of Deployment, and automatically
by Horizon Pod Autoscaling. Service object presents for all Pods in Deployment, its function is
balancing requests to the back-end Pods.

Alternatives
------------


Data model impact
-----------------

TBD

REST API impact
---------------

TBD

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

Primary assignee(s)
-------------------

  Hoang Phuoc <phuoc.hc@dcn.ssu.ac.kr>
  Digambar Patil <digambarpat@gmail.com>

Co-author
---------

  Janki Chhatbar <jchhatba@redhat.com>
  Digambar Patil <digambarpat@gmail.com>
  Hyunsik Yang <yangun@dcn.ssu.ac.kr>


Work Items
----------

1. Introduce K8s python library in Tacker repo
2. Implement translator to translate from TOSCA to k8s template
3. Add support in VNFM for managing Containerized VNFs

Dependencies
============
Kubenetes python libray

Testing
=======
Yes

Documentation Impact
====================
Yes. We have to describe how to use containerized VNF's

References
==========
.. [#first] https://kubernetes.io/
.. [#third] http://www.etsi.org/deliver/etsi_gs/NFV-SWA/001_099/001/01.01.01_60/gs_NFV-SWA001v010101p.pdf
