..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==========================================
Multisite VIM support in Tacker
==========================================

https://blueprints.launchpad.net/tacker/+spec/multi-site-vim

This proposal describes the plan to add multisite VIM support in Tacker. Tacker
currently deploys VNFs on a single OpenStack installation (VIM). With multisite
VIM support, Tacker can deploy VNFs on multiple OpenStack installations
providing a unified view of resource control and management through the NFV
Orchestrator (NFVO) component as shown below.

::

                      +----------------------+
                      |   Tacker Service     |
                      | +-------+  +-------+ |
                      | | NFVO  |  | VNFM  | |
                      | +-------+  +-------+ |
                      +----------------------+
           +----------------------------------XXX+------+
           |                     |                      |
    +------v------+    +---------------------+     +----v-----+
    |             |    |      |---------+    |     |          |
    |   +-------+ |    |    +---------+ |    |     | +------+ |
    | +------+  | |    |  +---------+ | |    |     | |      | |
    | | |    |  | |    |  | | |     | | |    |XXX  | |      | |
    | | +-------+ |    |  | | +---------+    |     | +------+ |
    | +------+    |    |  | +---------+      |     |          |
    | OpenStack   |    |  +---------+        |     | OpenStack|
    | Instances   |    | OpenStack Instances |     | Instance |
    +-------------+    +---------------------+     +----------+
        Site 1                 Site 2                 Site N


Problem description
===================

Telco operators have the need to deploy certain VNFs in close proximity to
customers for obvious performance requirements such as minimizing latency for
network services. Operators will need a way to control and manage these remote
VNFs without significantly impacting their existing OpenStack installations.

The challenge of optimal VIM selection for VNF placement involves several
requirements that need to be handled by the NFVO component as described below:

* NFVO should place the VNF on the best possible VIM that provides guaranteed
  SLA to the customer
* Continuous heartbeat monitoring and performance statistics of VIMs
* Policy driven VIM selection based on customer requirements such as
  geo-redundancy
* Resource usage information of VIMs for optimized VNF placements

VNFM component currently deploys VNFs on localized infrastructure. With this
proposal, we intend to take the first step towards supporting multisite VIM
deployments by introducing the NFVO component. This will enable Tacker to
deploy remote VNFs in a seamless manner.

Proposed change
===============

*API changes*

A new 'nfvo' extension will be introduced in Tacker API v1 that defines the
NFVO interface layer and describes the VIM REST APIs. The 'nfvo-plugin' will
implement NFVO interface layer. The plugin will support 'openstack' as the
default VIM driver. Initializing a new VIM will involve supporting basic CRUD
operations, validating and storing VIM information in the database. The
workflow can be visualized as below:
::

  +--------+    +------+    +------+
  |  NFVO  +---->  VIM +----> VNF  |
  +---+----+    +---^--+    +--^---+
      |             |          |
      |         +---+--+       |
      +---------> VNFM +-------+
                +------+

*Identity changes*

Tacker will dynamically construct the keystone client for the remote VIM using
the user provided auth information. The auth information is validated against
the remote VIM. If successful, VIM's auth info as well as VIM's regions are
stored in Tacker database during the VIM register operation. The vnf-create
operation will retrieve this vim auth info and deploy VNF in the special "nfv"
tenant on the remote VIM.

VIM sensitive data such as password will be encrypted and stored in a 'vimauth'
table. It will be decrypted during vnf-create using a fernet key generated for
individual VIM passwords. The fernet keys are stored in the root file system
path /etc/keystone/fernet_keys accessible only to the admin.

*VIM id in VNF Creation*

User can provide the VIM id argument during the VNF create workflow to specify
the VIM selection. If VIM id is not specified during VNF create operation, VNF
will be deployed on the localized OpenStack instance as default behavior.
Region name can also be provided during VNF create operation to deploy in a
specific region of selected VIM. Availability zone will continue to be supported
using VNFD placement_policy attribute [#]_.

*python-tackerclient and horizon dashboard changes*

Client changes will be made to include VIM CRUD operations: tacker vim-register,
vim-show, vim-list, vim-update and vim-delete operations that handle 'VIM' REST
API calls to Tacker server. A typical vim-register command can be described as
below:

.. code-block:: console

  tacker vim-register --name VIM3 --config-file ~/vim3.yaml

The --config/--config-file argument will take VIM specific information as a
direct input or as a file:

.. code-block:: ini

  auth_url: http://10.10.10.13:5000
  username: nfv_user
  password: tacker_pw
  tenant_name: nfv

tacker vim-update command will allow the user to update VIM information for a
specific VIM.

.. code-block:: console

  tacker vim-update --vim-id VIM3 --config-file ~/vim_update.yaml

The --config/--config-file argument can override existing VIM information or
provide additional parameters:

.. code-block:: ini

  username: new_user
  password: 123456
  user_domain_id: default

tacker vnf-create command will be updated to provide two new optional
arguments --vim-id and --region-name that will allow a user to specify VIM id
along with a region.

Similar changes will be done on the horizon dashboard. A new tab 'NFVO' will
include a 'VIM Orchestration' sub-tab to handle the orchestration of new VIMs.
The page will also display the current list of VIMs configured in Tacker.

*devstack changes*

Changes will be made to tacker devstack plugin to automatically configure local
VIM (VIM0) as the default VIM for deploying VNFs.

*Error handling*

* If a new VIM cannot be configured successfully, appropriate error should be
  displayed to the user stating the reason.
* If an invalid vim_id is specified during vnf-create, it should display a
  suitable message on the client/horizon dashboard.
* If a certain VIM is unreachable, it should gracefully be set to 'ERROR'
  state. The criteria for deciding the VIM health status check will be based on
  accessing the keystone service and heat service on remote site. The existing
  VNF monitor policy will have same behaviour for single site as well as multi-
  site when monitoring is enabled for VNFs.

*Assumptions*

Each OpenStack deployment is assumed to have its own L2 sub domain (individual
provider network) or can belong to one big L2 domain with no overlapping
provider address (shared provider network).

Each VIM is configured with core services (nova, neutron, cinder, glance,
horizon, identity) as well as orchestration (heat) service. This feature allows
VIM registration independent of versions and supports releases starting from
Kilo version.

This feature will further utilize OpenStack's multisite capabilities(such as
regions, availability zones, shared identity service) within telco's
infrastructure to translate VIM requests in to granular placements of VNFs.
Tacker multisite feature is intended to work with existing single site as well
as multisite OpenStack deployments and bring them into one orchestration view.


Further enhancements specific to multisite deployments listed below will be
taken up in future iterations:

* Role-based Access Control for users to create VNFs in their own tenants
* Resource utilization and management across VIMs
* SFC across multisite VNFs
* Support for non-OpenStack VIM types such as VMware, Xen, KVM

Hybrid cloud deployments with public clouds such as AWS, Azure is beyond the
scope of this blueprint.

Alternatives
------------
The alternate way of addressing the multisite challenge is to deploy Tacker
server on each of the OpenStack instances and allow them to manage VNFs
deployed locally. It will be practically overwhelming to deploy Tacker server
in thousands of OpenStack instances and further perform VNF life cycle
management in each of these instances.

There are projects such as Keystone federation [#]_, OPNFV multisite [#]_ and
Tricircle [#]_ that have ongoing work to address multisite challenges. Tacker
can help add NFVO/VNFM requirements to these projects as they evolve in future
iterations. Unique workflows in telco infrastructure and still evolving NFV
requirements provide a challenge to implement NFVO in single phase. Hence, it
is practical to develop this component in iterations and address some immediate
requirements.

Data model impact
-----------------
A new 'vim' resource will be added to Tacker resource model whose attributes
include id, name, description, placement_attr, type, and tenant_id. A new
'vimauth' resource will contain vim's authentication information and will
include the following attributes: id, vim_id, password, auth_url, auth_attr.
Existing 'device' resource will be modified to include a new attribute 'vim_id'
which is mapped to the 'vim' resource on which VNF is deployed. Every 'vim'
entry is uniquely identified by an UUID in the 'vim' db table. The same UUID
will be associated as vim_id in the corresponding VNF entry in 'device' table.

REST API impact
---------------

New 'nfvo' extension will be introduced in Tacker API v1 that implements REST
API end points for 'vim' resource as described below:

**/vim**

::

 +---------------------------------------------------------------------------+
 |Attribute     |Type   |Access  |Default   |Validation/ |Description        |
 |Name          |       |        |Value     |Con^ersion  |                   |
 +---------------------------------------------------------------------------+
 |id            |string |RO, All |generated |N/A         |identity           |
 |              |(UUID) |        |          |            |                   |
 +---------------------------------------------------------------------------+
 |name          |string |RW, All |''        |string      |human+readable     |
 |              |       |        |          |            |name               |
 +---------------------------------------------------------------------------+
 |description   |string |RW, All |''        |string      |description of     |
 |              |       |        |          |            |template           |
 +---------------------------------------------------------------------------+
 |auth_url      |string |RW, All |''        |string      |identity service   |
 |              |       |        |          |            |endpoint           |
 +---------------------------------------------------------------------------+
 |auth_attr     |string |RW, All |None      |string      |tenant_name, user- |
 |              |       |        |          |            |name, password, etc|
 +---------------------------------------------------------------------------+
 |placement_attr|dict   |RO, All |None      |dict        |VIM region and     |
 |              |       |        |          |            |availability zones |
 +---------------------------------------------------------------------------+
 |tenant_id     |string |RO, All |N/A       |string      |project id of VIM  |
 +---------------------------------------------------------------------------+
 |type          |string |RW, All |openstack |string      |driver implementing|
 |              |       |        |          |            |VIM specific logic |
 +--------------+-------+--------+----------+--------------------------------+


Security impact
---------------
VIM passwords are encrypted and stored in a separate 'vimauth' table accessible
to db admin only. The fernet keys are stored in root file system and will be
used to decrypt vim passwords.

Secure inter VNF communication will be an important factor to consider as we
enhance multisite VIM feature for SFC and other complex NFV use cases.

Notifications impact
--------------------

None

Other end user impact
---------------------

Horizon dashboard will include a new 'NFVO' feature under 'NFV' tab that can be
used to add a new VIM and also list current VIMs. python-tackerclient will
include the necessary changes to support VIM CRUD commands. A new optional
argument --vim-id will be provided for vnf-create workflow along with other
optional arguments as already listed in Proposed Changes section.

Operator will have to configure the default VIM information in tacker.conf
under the [nfvo] section as default_vim = <vim_name>.

Performance Impact
------------------
None

Other deployer impact
---------------------


Developer impact
----------------
None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  sseetha

Other contributors:
  None

Work Items
----------

* Add new extension 'vim' to tacker v1 and implemented the 'vim' plugin base.
* Tacker DB configuration for 'vim', 'vimauth' and 'device' tables including
  alembic migration scripts.
* Modifications to vnfm plugin and heat infra driver to handle the VIM option
  for VNFs.
* Changes for tacker-horizon and python-tackerclient for multisite VIM
  support.
* Add unit tests cases for the multisite VIM support
* Modify devstack tacker plugin to auto configure default local VIM (VIM0).
* Add functional test cases for multisite VIM support.
* Provide user documentation and developer documentation which explains the
  multisite VIM support.

Dependencies
============

None

Testing
=======
Unit testing
------------
Unit test cases will be written for the new extension. Also, existing vnfm test
plugin will be extended to add additional test cases for vim_id option.

Functional testing
------------------

New functional test cases will be added for VIM CRUD operations.
New VNFM test cases will be provided to test the vim_id option for vnf-register
workflow.

Scenario testing
------------------
This feature will require scenario test cases to validate operations in
multisite deployments. OpenStack Jenkins gate does not yet support multiregion
testing scenarios with devstack [#]_ as of writing this spec.


Documentation Impact
====================

User Documentation
------------------
Multisite VIM feature usage will be documented in Tacker usage guide [#]_ that
will describe the VIM operations that the operator can use for both new and
existing OpenStack deployments. VNF deployment guide will be modified to
describe the usage of new optional argument vim_id in both python-tackerclient
and tacker-horizon.

Developer documentation
-----------------------
Developer docs will be added to capture the VIM REST API in detail.

References
==========

.. [#] https://opendev.org/openstack/tacker/src/branch/master/samples/tosca-templates/vnffg-nsd/tosca-vnfd1-sample.yaml#L28
.. [#] http://docs.openstack.org/developer/keystone/configure_federation.html
.. [#] https://wiki.opnfv.org/multisite
.. [#] https://wiki.openstack.org/wiki/Tricircle
.. [#] https://review.opendev.org/#/c/200309/
.. [#] https://docs.openstack.org/tacker/latest/user/multisite_vim_usage_guide.html
