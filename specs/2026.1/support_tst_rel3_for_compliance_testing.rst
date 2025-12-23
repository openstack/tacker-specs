==================================================
Support TST v3.1.1 for ETSI NFV Compliance Testing
==================================================

This specification aims an enhancement to Tacker’s ETSI NFV compliance
testing framework by introducing additional support for a newer ETSI
NFV TST release (rel3 v3.3.1).


Problem Description
===================

Tacker's compliance testing framework currently supports TST v2.6.1 [#f1]_
for validating conformance with ETSI NFV SOL specifications. This version
is much older, and sometime critical fixes are not backported to this
branch. Also since then, TST has released multiple newer versions
including rel3, rel4, and rel5.

This spec proposes support of TST rel3 v3.3.1 (along with existing
support of v2.6.1), which aligns with ETSI NFV v3.3.1 specifications [#f2]_.
The additional support will enable validation of Tacker's V2 API
implementations against current ETSI standards and ensure continued
compliance with NFV specifications.


Proposed Change
===============

This proposal aims to provide additional support of TST v3.3.1 along
with existing v2.6.1 support to Tacker's compliance testing framework,
following the documented TST Release Transition Guidelines [#f3]_. The
implementation will proceed through a structured transition process.

Key Implementation Phases
-------------------------

1. **Impact Assessment**: Execute TST rel3 against current Tacker
   compliance test code to determine the effect of TST changes on
   existing functionality.
2. **Test Case Development**: Implement new compliance test cases per
   TST rel3 (v3.3.1) requirements.
3. **Gap Analysis and Reporting**: Categorize and report gaps at their
   respective tracking locations based on gap type (specification vs.
   implementation).
4. **CI Pipeline Integration**: Integrate implemented tests into
   Tacker's CI pipeline for automated execution.
5. **Documentation Updates**: Create or update documentation to reflect
   TST v3.3.1 compliance status and testing procedures.


Data Model Impact
-----------------

None

REST API Impact
---------------

No direct REST API changes are proposed. However, this work will validate
Tacker's existing V2 REST API implementations against TST v3.3.1 test
cases and may identify areas requiring API corrections to achieve full
compliance with ETSI specifications.

Security Impact
---------------

None

Notifications Impact
--------------------

None

Other End User Impact
---------------------

None

Performance Impact
------------------

None


Other Deployer Impact
---------------------

None

Developer Impact
----------------

Developers working on V2 APIs will need to ensure their changes
pass TST v3.3.1 compliance tests. This requirement will improve
code quality and standards compliance but necessitates
familiarity with ETSI specifications.
Also, TST v3.3.1 test execution will be added to the CI
pipeline, which may increase overall CI run time for patches
submitted by developers.

Community Impact
----------------

This upgrade demonstrates Tacker's commitment to maintaining
ETSI NFV compliance and strengthens collaboration with the
ETSI NFV-TST team. It positions Tacker as a standards-compliant
VNF management solution aligned with current industry
specifications.


Alternatives
------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:

1. Shivam Shukla

Work Items
----------

1. Execute TST rel3 against current Tacker compliance test code
   to assess impact on existing functionality.
2. Implement new compliance test cases per TST rel3 (v3.3.1)
   specifications.
3. Integrate implemented tests into Tacker's CI pipeline for
   automated execution.
4. Perform gap analysis and report findings to appropriate
   tracking systems based on gap type (specification gaps to
   ETSI TST repository, implementation gaps to Tacker Launchpad).
5. Create or update documentation to reflect TST v3.3.1
   compliance status and test execution procedures.

Dependencies
============

None

Testing
=======

NFV compliant API tests will be executed in Robot Framework.


Tempest Tests
-------------

None

Functional Tests
----------------

None

API Tests
---------

APIs compliant with ETSI NFV SOL002, SOL003, and SOL005
specifications will be tested using Robot Framework with
test code released by ETSI NFV-TST v3.1.1.

Documentation Impact
====================

Create or update compliance testing documentation to reflect
TST v3.1.1 support and test execution procedures.

References
==========

.. [#f1] https://forge.etsi.org/rep/nfv/api-tests/-/tree/2.6.1-fix-plu
.. [#f2] https://forge.etsi.org/rep/nfv/api-tests/-/tree/3.3.1-fix-plu
.. [#f3] https://docs.openstack.org/tacker/latest/contributor/tst_release_transition_guidelines.html
