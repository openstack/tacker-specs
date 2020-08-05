=======================================================
Adopt Robot Framework to use ETSI NFV-TST API test code
=======================================================

This proposal aims to efficiently achieve ETSI NFV compliant automated testing
by using the Robot Framework and ETSI NFV-TST API test codes.
The scope here is implementation for using Robot Framework and improvement
of the Tacker documentations for ETSI NFV compliance testing.


Problem Description
===================

Currently Tacker functional tests mainly focus on checking various VNF
patterns such as a simple VNF, multi VDU, volume attach and affinity set.

Tacker community is advancing ETSI NFV standard compliance,
and coverage of compliant API testing becomes important.


Proposed Change
===============

Our plan is to use Robot Framework [#f1]_ to achieve automated API testing.
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

      + ETSI NFV-TST test using Robot Framework
        (NFV-TST010 is the first step, others are future work)

  * Documentation explaining the above to Tacker contributors and users

Overview of testing by Robot Framework and ETSI NFV-TST010 test codes:
::

    +------------------------------------------------------------+
    |                                                            |
    |          +----------------------------------------+        |
    |          |Tacker repository                       |        |
    |          | +---------------+  +-----------------+ |        |
    |          | |Community robot|  |Zuul configurtion| |        |
    |          | |test code      |  |.zuul.yaml       | |        |
    |          | |(future work)  |  +-----------------+ |        |
    |          | +---------------+                      |        |
    |          |                        +-------------+ |        |
    |          | +--------------+       |playbook     | |        |
    |          | |testitem.robot|       |runrobot.yaml| |        |
    |          | +--------------+       +-------------+ |        |
    |          +----------------------------------------+        |
    |                                               |            |
    |        +------------+  download (pip)         |            |
    |        |            |  Robot framework        |            |
    |        | python     +---------------------+   |            |
    |        | repository |                     |   |            |
    |        |            |                     |   |            |
    |        +------------+                     |   |            |
    |                                           v   v            |
    |   +-----------------+  download          ++---+-+          |
    |   |                 |  robot test code   |      |          |
    |   | ETSI repository +------------------->+ Zuul |          |
    |   | api-tests       |                    |      |          |
    |   |                 |      +-------------+      +---+      |
    |   +-----------------+      |             +------+   |      |
    |                            |                        |      |
    |                            | execute        execute |      |
    |                            v                        v      |
    |                      +-----+-----+        +---------+--+   |
    |                      |           |        |            |   |
    |                      | Robot     |  test  | Tacker     |   |
    |                      | framework +------->+ (devstack) |   |
    |                      |           |        |            |   |
    |                      +-----------+        +------------+   |
    |                                                            |
    +------------------------------------------------------------+


`testitem.robot` is a list of test cases selected from the test code
released by ETSI NFV-TST. It depends on API implementation of Tacker.

We also provide the document for testing that describes the criteria
and responsibility of Robot Framework
for unit tests, functional tests and compliant (includes API) tests.
Using Robot Framework is a first step of implementation
of compliant tests.

The structure of the document is as follows.
1. Summary
2. Testing Framework
3. Development Process
4. Running Tests
5. Coverage


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

Running autometed API test will be available to run.
We will discuss with OpenStack QA team if necesarry.


Alternatives
------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:

1. Toshiaki Takahashi

Other contributors:

(T.B.D.)

Work Items
----------

1. Make a test list from TST test cases (Choose APIs implemented by Tacker)
2. Make Robot execution playbook

  * Install Robot Framework
  * Download test code from ETSI NFV-TST repository
  * Execute test with the above test list

3. Add the above playbook execution jobs to Zuul setting

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

.. note:: In future, some functional tests are execeted by
          Robot Framework.

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

We will make documentations about testing policy.

References
==========

.. [#f1] https://robotframework.org/
.. [#f2] https://forge.etsi.org/rep/nfv/api-tests

