=======================================================
Adopt Robot Framework to use ETSI NFV-TST API test code
=======================================================

https://blueprints.launchpad.net/tacker/+spec/use-robot-api-tests

This proposal aims to test the API of ETSI NFV SOL002, 003 and 005 implemented
in Tacker with NFV-TST test code.


Problem Description
===================

The codes to test the SOL002, 003 and 005 APIs are provided by NFV-TST.
But the raw test codes to test the APIs will not pass.
This is because each API test has "preconditions", which is the last LCM
condition to be operated before running the test.
For example, the API test for "create VNF package" needs "upload VNF package"
as its preconditions.

Currently there are no implementation to make preconditions to run the tests.


Proposed Change
===============

Our plan is to have codes in the tacker community to make preconditions,
and to use Robot Framework [#f1]_ to achieve automated API testing.
We adopt API test code released by ETSI NFV-TST010 [#f2]_.

The final Tacker test improvement plan is as follows.

  * Test implementation

    - Unit tests

      + Continue current improvement (not related to this spec)

    - Functional tests

      + Continue current improvement (not related to this spec)

      + Expand scenario tests by developing Tacker community robot test codes
        using Robot Framework (Future work)

    - Compliant tests

      + NFV-TST test using Robot Framework
        (NFV-TST010 is the first step, others are future work)

List to test the APIS implemented by Tacker:

  * SOL002, SOL003

    - /vnf_instances

      + GET (Query multiple VNF instances)

      + POST (Create a new "Individual VNF instance" resource)

    - /vnf_instances/{vnfInstanceId}

      + GET (Read an "Individual VNF instance" resource)

      + PATCH (Modify VNF instance information)

      + DELETE (Delete an "Individual VNF instance" resource)

    - /vnf_instances/{vnfInstanceId}/instantiate

      + POST (Instantiate a VNF instance)

    - /vnf_instances/{vnfInstanceId}/scale

      + POST (Scale a VNF instance incrementally)

    - /vnf_instances/{vnfInstanceId}/terminate

      + POST (Terminate a VNF instance)

    - /vnf_instances/{vnfInstanceId}/heal

      + POST (Heal a VNF instance)

    - /vnf_instances/{vnfInstanceId}/change_ext_conn

      + POST (Change the external connectivity of a VNF instance)

    - /vnf_lcm_op_occs

      + GET (Query information about multiple VNF lifecycle management
           operation occurrences)

    - /vnf_lcm_op_occs/{vnfLcmOpOccId}

      + GET (Read information about an "Individual VNF lifecycle management
           operation occurrences" resource)

    - /vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback

      + POST (Rollback a VNF lifecycle management operation occurrence)

    - /vnf_lcm_op_occs/{vnfLcmOpOccId}/retry

      + POST (Retry a VNF lifecycle management operation occurrence)

    - /subscriptions

      + POST (Subscribe to VNF lifecycle change notifications)

      + GET (Query multiple subscriptions)

    - /subscriptions/{subscriptionId}

      + GET (Read an "Individual subscription" resource)

      + DELETE (Terminate a subscription)

  * SOL005

    - /vnf_packages

      + GET (Query VNF packages information)

      + POST (Create a new individual VNF package resource)

    - /vnf_packages/{vnfPkgId}

      + GET (Read information about an individual VNF package)

      + DELETE (Delete an individual VNF package)


Overview of testing by Robot Framework and NFV-TST010 test codes:
::

    +-------------------------------------------------------------+
    |                                                             |
    |          +-------------------------------------------+      |
    |          |Tacker repository                          |      |
    |          | +---------------+    +------------------+ |      |
    |          | |Community robot|    |Zuul configuration| |      |
    |          | |test code      |    |.zuul.yaml        | |      |
    |          | |(future work)  |    +------------------+ |      |
    |          | +---------------+                         |      |
    |          |                      +------------------+ |      |
    |          | +------------------+ |tox configuration | |      |
    |          | |tacker/tests/     | |tox.ini           | |      |
    |          | |functional/base.py| +------------------+ |      |
    |          | +------------------+                      |      |
    |          +-------------------------------------------+      |
    |                                               |             |
    |        +------------+  download (pip)         |             |
    |        |            |  Robot framework        |             |
    |        | python     +---------------------+   |             |
    |        | repository |                     |   |             |
    |        |            |                     |   |             |
    |        +------------+                     |   |             |
    |                                           v   v             |
    |   +-----------------+  download          ++---+-+           |
    |   |                 |  robot test code   |      |           |
    |   | ETSI repository +------------------->+ Zuul |           |
    |   | api-tests       |                    |      |           |
    |   |                 |      +-------------+      +---+       |
    |   +-----------------+      |             +------+   |       |
    |                            |                        |       |
    |                            | execute        execute |       |
    |                            v                        v       |
    |                      +-----+-----+        +---------+--+    |
    |                      |           |        |            |    |
    |                      | Robot     |  test  | Tacker     |    |
    |                      | framework +------->+ (devstack) |    |
    |                      |           |        |            |    |
    |                      +-----------+        +------------+    |
    |                                                             |
    +-------------------------------------------------------------+


When a Zuul test is started, the package of Robot Framework from the python
repository and the test code so called "api-tests" from ETSI repository are
downloaded according to tox.ini.
After that, Zuul executes Compliant tests for each target API.
During each test, the routine of Robot Framework is called and verifies if the
target API is compliant to ETSI NFV specification or not.

'tacker/tests/functional/base.py' is used to make the preconditions.

.. note:: We need to discuss with NFV-TST about the implementations to make the preconditions.

Data Model Impact
-----------------

None

REST API Impact
---------------

None

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

IPv6 Impact
-----------

None

Other Deployer Impact
---------------------

None

Developer Impact
----------------

Writing new APIs might require getting/writing ROBOT tests for them, as well
as unit and function tests.

Community Impact
----------------

None


Alternatives
------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:

1. Tsukasa Inoue

Other contributors:

(T.B.D.)

Work Items
----------

1. Make python codes to make precondition and run robot framework.
2. Make tox.ini

  * Download test code from ETSI NFV-TST repository
  * Install Robot Framework
  * Run tests with the above python codes

3. Add the above tox jobs to Zuul setting

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

APIs compliant with ETSI NFV-SOL002, 003 and 005 are tested
by Robot Framework and test code released by ETSI NFV-TST010.


Documentation Impact
====================

User Documentation
------------------

None

Developer Documentation
-----------------------

Complete contributor guide will be added for explaining the overview of
Robot Framework and how to develop with it in Tacker.


References
==========

.. [#f1] https://robotframework.org/
.. [#f2] https://forge.etsi.org/rep/nfv/api-tests


