..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Enhanced VNF placements
==========================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/enhanced-vnf-placement

This spec tries to use declartive way to place VNF's VDUs effctively.


Problem description
===================

VNF's VDUs are placed just like normal VMs. This does not satisfy the VNF's
performance requirements:

* IO intensive

* Computation intensive


Proposed change
===============

Introduce new host properties in VNFD template that allows to specify CPU
pinning, Huge pages, NUMA placements and vCPU topology per VDU. Additionally,
allows for a way to specify SR-IOV nics for the VDU network interfaces.

CPU pinning avoids unpredicatable latency and host CPU overcommit by
pinning guest vCPUs to host CPUs, thereby improving performance of
applications running in guest.

Huge pages helps ensure that guest has 100% dedicated RAM that will never be
swapped out.

NUMA placement decreases latency by avoiding cross-node memory and I/O device
access by guests.

SR-IOV port allocation to a guest enables network traffic to bypass the
software layer of the hypervisor and flow directly between the SR-IOV nic and
the guest therby improving performance.

VNFD host properties schema:

**topology_template**:

  **node_templates:**
    **vdu1:**
      **type: tosca.nodes.nfv.VDU:**

      **capabilities:**

        **nfv_compute**:

          **properties:**
            **disk_size: {get_input: dsize}**
            #disk size value of VM in GB

            **num_cpus: {get_input: cpu_count}**
            #CPU count for VM

            **mem_size: {get_input: msize}**
            #Memory Size in MB for VM

          **cpu_allocation:**
            **cpu_affinity: {get_input: affinity}**

            #valid value supported is 'dedicated'. The value 'dedicated'
            ensures that the guest vCPU associated with VDU will be strictly
            pinned to a set of host pCPUs. Any other value specified or not,
            will allow guest vCPU to float freely across host pCPUs.

            **thread_allocation: {get_input: threadalloc}**

            #valid values  are 'avoid', 'separate', 'isolate' and 'prefer'.
            The values applies only if 'cpu_affinity' is set to 'dedicated'.
            The value 'avoid' indicates to not place the guest on a host that
            has hyperthreads. The value 'separate' allows to place each vCPU
            on a different core if host has threads. The value 'isolate' will
            place each vCPU on a different core and no vCPUs from other
            guests will be placed on the same core. If a host has threads,
            the value 'prefer' allows to place vCPUs on the same core, so
            they are thread siblings.


            **socket_count: {get_input: sock_cnt}**

            #specifies preferred number of sockets to expose to the guest. A
            socket count greater than 1 enables a VM to be spread across NUMA
            nodes.
            Note: While the template specifies the exact socket, core and
            thread count the underlying IaaS system (in this case Nova) might
            optimize into a slightly different core count combination across
            sockets, cores and threads.

            **core_count: {get_input: core_cnt}**

            #specifies preferred number of cores per socket to expose to the
            guest.

            **thread_count: {get_input: thrdcnt}**

            #specifies preferred number of threads per core to expose to the
            guest.

          **mem_page_size: {get_input: mem_pg_sz}**

          #allows to specify values when Huge pages are used, allowed values
          are 'small', 'large', 'any' and 'custom page size in MB'.'small'
          usually maps to 4K page sizes on x86, large maps to either 2 MB or
          1 GB on x86, 'any' leaves it to driver implementation.

          **numa_node_count**: **count:** {get_input: numa_count}

          # specifies the number of NUMA nodes to expose to the guest.
          When numa_node_count is specified, the CPU and Memory resources for
          the guest are symmetrically allocated across the numa nodes.
          Specifying only one of either numa_node_count or numa_nodes is
          supported, if both are specified, the numa_node_count value is
          considered.

          **numa_nodes**:

          #Allows for specifying asymmetrical allocation of CPUs and RAM. A
          minimum of 2 nodes with unique node labels should be defined for
          this to take effect.

            **<node_label>**:
              #specify a unique name for the node_label.

                **id: {get_input: numa_id}**

                # Specifies NUMA node id

                **vcpus: {get_input: vcpu_list}**

                # specifies mapping of vCPUs list to the NUMA node

                **memory: {get_input: mem_size}**

                #specifies mapping of RAM in MB to NUMA node

For SR-IOV support, a new property called "type" that would accept value of
'sriov' is introduced for the tosca.nodes.nfv.CP type



VNFD template schema examples
-----------------------------

1. CPU Pinning
~~~~~~~~~~~~~~

Below would be an example of pinning guest vCPUs to host pCPUs:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 4096 # Memory Size in MB
                disk_size: 8 # Value in GB
    
                cpu_allocation:
                  cpu_affinity: dedicated
                  thread_allocation: isolate

2. Huge Pages
~~~~~~~~~~~~~

An example of specifying Huge pages be used for a guest VM:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 4096 # Memory Size in MB
                disk_size: 8 # Value in GB
                mem_page_size: large

3. Asymmetrical NUMA placement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below would be an example of specifying asymmetrical
allocation of CPUs and RAM across NUMA nodes:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 6144
                disk_size: 8
                numa_nodes:
    
                  node1:
                    id: 0
                    vcpus: [ 0,1 ]
                    mem_size: 2048
                  node2:
                    id: 1
                    vcpus: [ 2, 3, 4, 5]
                    mem_size: 4096

4. Symmetrical NUMA placement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below would be an example of specifying symmetrical
allocation of CPUs and RAM across NUMA nodes:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 6144
                disk_size: 8
                numa_node_count: 2


5. Combination Example
~~~~~~~~~~~~~~~~~~~~~~

Below would be an example that specifies HugePages,
CPU pinning, NUMA placement, host hyper-threading disabled, as well providing
sockets, cores and thread count to be exposed to guest:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 4096
                disk_size: 80
                mem_page_size: 1G
                cpu_allocation:
    
                  cpu_affinity: dedicated
                  thread_allocation: avoid
                  socket_count: 2
                  core_count: 2
                  thread_count: 2
    
                numa_node_count: 2


6. Network Interfaces example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below would be an example that defines multiple
network interfaces and sriov nic types:

.. code-block:: ini

    topology_template:
      node_templates:
        VDU1:
          type: tosca.nodes.nfv.VDU
    
          capabilities:
            nfv_compute:
              properties:
                num_cpus: 8
                mem_size: 4096 MB
                disk_size: 8 GB
                mem_page_size: 1G
    
                cpu_allocation:
                  cpu_affinity: dedicated
                  thread_allocation: isolate
                  socket_count: 2
                  core_count: 8
                  thread_count: 4
    
                numa_node_count: 2
    
        CP11:
          type: tosca.nodes.nfv.CP
    
          requirements:
            - virtualbinding: VDU1
            - virtualLink: net_mgmt
    
        CP12:
         type: tosca.nodes.nfv.CP
    
         properties:
             anti_spoof_protection: false
             type : sriov
         requirements:
          - virtualbinding: VDU1
          - virtualLink: net_ingress
    
        CP13:
          type: tosca.nodes.nfv.CP
    
         properties:
             anti_spoof_protection: false
             type : sriov
    
          requirements:
            - virtualbinding: VDU1
            - virtualLink: net_egress
    
        net_mgmt:
          type: tosca.nodes.nfv.VL.ELAN
    
        net_ingress:
          type: tosca.nodes.nfv.VL.ELAN


Alternatives
------------

The alternative would be to create a flavor ahead of time and use that flavor
in the VNFD template.

Data model impact
-----------------
None

REST API impact
---------------


Security impact
---------------


Other end user impact
---------------------


Performance Impact
------------------


Other deployer impact
---------------------
The deployer is expected to prepare the Host OS (grub changes) on the compute
nodes for reserving Huge Pages, isolating CPUs and enabling SR-IOV.
Configuration changes are expected in nova and neutron configuration files.


Developer impact
----------------



Implementation
==============

Assignee(s)
-----------


Primary assignee:
  gong yong sheng gong.yongsheng@99cloud.net

Other contributors:
  Vishwanath Jayaraman <vishwanathj@hotmail.com>

Work Items
----------

1) numa support
2) sriov support


Dependencies
============

* https://blueprints.launchpad.net/tacker/+spec/automatic-resource-creation



Testing
=======

To test the numa, sriov and pci passthough needs special hardware, the normal
environment on openstack CI does not satisfy it.

So manual testing is a must, and hopefully, some one can provide their own
hosts in lab to do the third party testing.

Other options are:

1. Approach openstack-infra / -qa teams to request compute resources be added
   at the gate for testing the capabilities in the spec.
2. Have a vendor to support a 3rd party CI job and vote against the features
   called out in the spec.


Documentation Impact
====================

The document will be updated to guide how to use this feature.


References
==========

.. [#] `<http://docs.openstack.org/developer/nova/testing/libvirt-numa.html>`_
.. [#] `<http://redhatstackblog.redhat.com/2015/05/05/cpu-pinning-and-numa-topology-awareness-in-openstack-compute/>`_
.. [#] `<https://wiki.openstack.org/wiki/VirtDriverGuestCPUMemoryPlacement>`_
.. [#] `<https://specs.openstack.org/openstack/nova-specs/specs/kilo/implemented/input-output-based-numa-scheduling.html>`_
.. [#] `<http://specs.openstack.org/openstack/nova-specs/specs/mitaka/approved/virt-driver-cpu-pinning.html>`_
.. [#] `<http://redhatstackblog.redhat.com/2015/03/05/red-hat-enterprise-linux-openstack-platform-6-sr-iov-networking-part-i-understanding-the-basics/>`_
