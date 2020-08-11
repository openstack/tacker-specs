This work is licensed under a Creative Commons Attribution 3.0 Unported
License.

http://creativecommons.org/licenses/by/3.0/legalcode

===================
Inline VNF Template
===================

https://blueprints.launchpad.net/tacker/+spec/vnf-inline-template

This blueprint will bring in the support for making VNFD id optional for
tacker vnf-create. Instead support an option where VNFD template can be passed
in directly to the vnf-create API / CLI.

Problem description
-------------------

Currently VNF Catalog is an integral part of Tacker solution. VNFD template
should've been populated in the VNF Catalog before can instantiated. However,
when Tacker is used just as a G-VNFM there are scenarios where the VNF/NFV
Catalog exists outside Tacker. For those solutions it doesn't make sense to
use Tacker's VNF Catalog.

In such cases, a VNFD template would directly be provided via CLI/API during
VNF creation.

Proposed change
---------------

VNFD template will be directly provided to CLI/API while creating a VNF. The
template will not be onboarded as VNFD. Tacker DB will hold information about
the nature of the template used. Tacker server, while creating VNF, will
bypass logic to fetch VNFD and instead call tosca-parser and then Heat APIs to
spawn VNF. Inline VNF template will be given preference over VNFD name or id
specified during VNF creation.

Alternatives
------------

There are two options to implement this.

1. Not store the template at all in Tacker DB. This seems to fulfil the
   initial idea of this BP perfectly. However, in cases when there are too
   many VNFs, it becomes difficult to map VNFs to the templates used.

2. Store the template in VNFD table of Tacker DB. Template will be visible on
   CLI with "--all" flag in "vnfd list".

Option 2 is discussed in this specification.

Data model impact
-----------------

A new column "template-source" needs to be added to VNFD table indicating the
nature of the template. The field will have 2 values namely "inline" for
template passed directly or "onboarded" for template used from Tacker DB.

Logic to derive template name from vnf name is to be implemented. Template
name would be "tmpl-<random-hex>-vnf-name"

REST API impact
---------------

'Create VNF' API will have a "vnf-template" field which will hold the
template to be used for VNF.

'Show VNFD' API will have logic to drop "template" field based on whether
"--all" flag is provided or not.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

Client and Horizon changes:

1. Add "vnf-template" argument in "create vnf" command
2. Implement preference logic giving priority to vnfd-template in case when
   both a template and vnfd id or name are specified
3. Add "all" flag to "vnfd list" API to list inline templates too. This is
   applicable only to CLI and not Horizon

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
  Janki Chhatbar <jchhatba@redhat.com>

Work items
----------

1. Add "vnf-template" and "all" argument to Tackerclient
2. Implement logic to give priority to inline template
3. Implement changes on server
4. Add functional test cases
5. Add usage guide on using this feature
6. Update API reference guide at [1]

Dependencies
============

None

Testing
=======

Add functional and unit tests for this functionality.

Documentation Impact
====================

User-guide will be provided.

References
==========

[1]. https://opendev.org/openstack/tacker/src/branch/master/api-ref/source/v1/vnfs.inc
