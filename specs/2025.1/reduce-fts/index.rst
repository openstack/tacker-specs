..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

======================================================
Reduce the amount of time of Tacker's functional tests
======================================================

This proposal is for improving our development experience by reducing
the cost of tests on zuul for which we usually takes several weeks to
complete to merge a patch in some worst case.


Use Cases
---------

This proposal is for revising the current functional tests and no additional
use cases.


Problem Description
===================

The number of functional tests in tacker has been increased since we've
added several features without considering efficiency of the tests.
These tests are not only Tacker and Openstack, but also other functionalities
since we should support several usecases in addition to basic OpenStack's
ones, such as deploying VNFs on Kubernetes, authentication/authorization
using other than Keystone. As the result, the number of functional tests
is totally 23 and around half of them are for the usecases including
external tools or features.

It's a good behavior to implement functional tests as end-to-end tests for
ensuring whole the related functionalities working fine instead of using any
mocks just always return an expected result.
On zuul, we can check the functionalities on actual deployed virtual machines
each time we upload a change and find any problem not only on the change
itself but also on a all related functionality caused by the change. It's
very useful to find a bug especially on a large system because we cannot
understand all of the details on such a system while developing a feature
running on. If something wrong happened for the change while running the
functional tests, we can get detailed logs from gerrit and analyze them
anytime after running the tests.

However, we cannot have not so much resources for the functional tests
as we actually want to reserve because there are several projects other
than Tacker run their jobs while the total amount of resources is limited.
For example, the maximum resources of the number of CPUs or size of memory
are less than Tacker's controller node requires.

The functional tests can be run on zuul somehow, but it's not enough as
each of tests can be done in the period of timeout which is defined in
zuul, three hours preciously, and sometimes failed to run before it's
finished in the time.
It is ended up with a unstability in the CI/CD process on zuul, such as
a failure because of over the limit of timeout or lack of resources
available on tests on zuul.
Here is an example of the current status on zuul to show how much time
cost in each tests.
You notice that the result of time consuming on
``tacker-functional-devstack-multinode-sol-v2-individual-vnfc-mgmt`` and
``tacker-compliance-devstack-multinode-sol`` are over 2 hours, and
most of other test scenarios are over 1 hour.

- tacker-functional-devstack-multinode-sol-legacy-nfvo : SUCCESS in 42m 53s
- tacker-functional-devstack-multinode-sol-vnflcm : SUCCESS in 1h 11m 24s
- tacker-functional-devstack-multinode-sol-vnflcm-userdata : SUCCESS in 1h 58m 39s
- tacker-functional-devstack-multinode-sol-vnfpkgm : SUCCESS in 30m 55s
- tacker-functional-devstack-multinode-sol-separated-nfvo : SUCCESS in 55m 19s
- tacker-functional-devstack-multinode-sol-kubernetes : SUCCESS in 1h 23m 54s
- tacker-functional-devstack-multinode-sol-v2-basic : SUCCESS in 1h 38m 09s
- tacker-functional-devstack-multinode-sol-v2-vnflcm : SUCCESS in 1h 51m 29s
- tacker-functional-devstack-multinode-sol-v2-notification : SUCCESS in 1h 01m 53s
- tacker-functional-devstack-multinode-sol-v2-prometheus : SUCCESS in 56m 07s
- tacker-functional-devstack-multinode-sol-separated-nfvo-v2 : SUCCESS in 1h 05m 16s
- tacker-functional-devstack-multinode-sol-v2-individual-vnfc-mgmt : SUCCESS in 2h 10m 32s
- tacker-functional-devstack-multinode-sol-kubernetes-v2 : SUCCESS in 1h 26m 28s
- tacker-functional-devstack-multinode-sol-multi-tenant : SUCCESS in 53m 24s
- tacker-functional-devstack-multinode-sol-https-v2 : SUCCESS in 1h 04m 48s
- tacker-functional-devstack-multinode-sol-encrypt-cred-barbican : SUCCESS in 37m 21s
- tacker-functional-devstack-multinode-sol-encrypt-cred-local : SUCCESS in 39m 47s
- tacker-functional-devstack-multinode-sol-kubernetes-multi-tenant : SUCCESS in 54m 16s
- tacker-functional-devstack-kubernetes-oidc-auth : SUCCESS in 49m 48s
- tacker-functional-devstack-multinode-sol-v2-az-retry : SUCCESS in 38m 01s
- tacker-functional-devstack-enhanced-policy-sol : SUCCESS in 1h 28m 04s
- tacker-functional-devstack-enhanced-policy-sol-kubernetes : SUCCESS in 1h 06m 13s
- tacker-compliance-devstack-multinode-sol : FAILURE in 2h 37m 13s (non-voting)
- tacker-functional-devstack-multinode-sol-terraform-v2 : SUCCESS in 1h 01m 25s


Proposed Change
===============

To complete the goal of reducing the total amount of time of Tacker's functional
tests, we will propose to take four steps to focus on dominant ones.
(1) Divide time consuming tests,
(2) Move tests less frequently updated to move to non-voting,
(3) Drop tests almost not updated from zuul, and
(4) Rename each test scenarios and revise directory structure.

The first priority in this proposal is to reduce the maximum time of each time
of zuul's check when a patch is uploaded although it's also important to
reduce the number of retries of the tests. So, the first thing we have to do
is to divide the most time consuming tests in to several ones.
This is the reason why we put (1) as the top of the list.

The second priority is to reduce the number of retries of the tests when
a patch is uploaded because of unstability for an unexpected failure.
The failure is not caused the change itself, but other uninterested
part. Although it can be avoided by doing retry several times usually,
the total amount of time is also increased lineary.
To reduce the number of retries, move to tests which are not so much
updated frequently to non-voting as listed at (2).
This revising is useful when a change causes a failure which is no need to be
fixed before the patch is merged but should be fixed later. We can focus on
the change itself first without being interrupted by such an uninterested
failure.

Although it is expected to reduce the certain amount of time if we complete
(1) and (2), the number of tests will be increased for dividing current
time consuming tests and it requires more resources for running the tests.
It is not a good situation and we should avoid it.
Considering the current activities of development on Tacker,
legacy or v1 features have been updated almost nothing and we don't need to
run the functional tests for them everytime a patch is uploaded.
So, we had better to drop such a tests from zuul and enable to run on
local environment instead.

The final (4) is another approach for reducing time by improving
maintainability of the test codes. The current codes are not so
organized well, for instance, each name of functional tests is too long
to make it hard to develop or review.
``.zuul.yaml`` should be also revised because its contents has become large
and mess since there a lot of similar parameters defined.

Each of strategies for the four items how we improve the functional tests
are described below.


1. Divide time consuming tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From a brief analysis of the reports on gerrit which describe the results of
functional tests, we have found that there are not so much different for
each of consuming times among all test scenarios.
So, it is enough to pick up just a few cases as samples for determining how
much time is consuming for each test scenario.

Here is the list of functional test scenarios as same as the previous one,
but a ``category`` is added to indicate the amount of time
consumed. It consists of four levels,
``S`` (Short) for less than one hour,
``M`` (Middle) for less than one and half hours but over ``S``,
``L`` (Long) for less than two hours but over ``M``, and
``LL`` (Extra Long) for over two hours.

.. list-table::
  :header-rows: 1
  :widths: 45 5 10
  :align: left

  * - Test Name
    - Category
    - Time to Run
  * - tacker-functional-devstack-multinode-sol-legacy-nfvo
    - S
    - 42m 53s
  * - tacker-functional-devstack-multinode-sol-vnflcm
    - M
    - 1h 11m 24s
  * - tacker-functional-devstack-multinode-sol-vnflcm-userdata
    - L
    - 1h 58m 39s
  * - tacker-functional-devstack-multinode-sol-vnfpkgm
    - S
    - 30m 55s
  * - tacker-functional-devstack-multinode-sol-separated-nfvo
    - S
    - 55m 19s
  * - tacker-functional-devstack-multinode-sol-kubernetes
    - M
    - 1h 23m 54s
  * - tacker-functional-devstack-multinode-sol-v2-basic
    - L
    - 1h 38m 09s
  * - tacker-functional-devstack-multinode-sol-v2-vnflcm
    - L
    - 1h 51m 29s
  * - tacker-functional-devstack-multinode-sol-v2-notification
    - M
    - 1h 01m 53s
  * - tacker-functional-devstack-multinode-sol-v2-prometheus
    - S
    - 56m 07s
  * - tacker-functional-devstack-multinode-sol-separated-nfvo-v2
    - M
    - 1h 05m 16s
  * - tacker-functional-devstack-multinode-sol-v2-individual-vnfc-mgmt
    - LL
    - 2h 10m 32s
  * - tacker-functional-devstack-multinode-sol-kubernetes-v2
    - M
    - 1h 26m 28s
  * - tacker-functional-devstack-multinode-sol-multi-tenant
    - S
    - 53m 24s
  * - tacker-functional-devstack-multinode-sol-https-v2
    - M
    - 1h 04m 48s
  * - tacker-functional-devstack-multinode-sol-encrypt-cred-barbican
    - S
    - 37m 21s
  * - tacker-functional-devstack-multinode-sol-encrypt-cred-local
    - S
    - 39m 47s
  * - tacker-functional-devstack-multinode-sol-kubernetes-multi-tenant
    - S
    - 54m 16s
  * - tacker-functional-devstack-kubernetes-oidc-auth
    - S
    - 49m 48s
  * - tacker-functional-devstack-multinode-sol-v2-az-retry
    - S
    - 38m 01s
  * - tacker-functional-devstack-enhanced-policy-sol
    - M
    - 1h 28m 04s
  * - tacker-functional-devstack-enhanced-policy-sol-kubernetes
    - M
    - 1h 06m 13s
  * - tacker-compliance-devstack-multinode-sol
    - LL
    - 2h 37m 13s
  * - tacker-functional-devstack-multinode-sol-terraform-v2
    - M
    - 1h 01m 25s

We don't need to take care about the tests categorized as ``S``
because waiting for tests for an hour does not a matter in general.
On the other hand, we focus on ``M`` or higher level and
start to divide them from ``LL``.

Although dividing the test excessively is not a good way from stand
point of view of optimization because dividing test into several
one means the common process among the tests such as running setup
script is run before each test scenario.
However, it is still useful if we can reduce the whole time of
interval of zuul job.


2. Move tests less frequently updated to non-voting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On Tacker's repository, there are not so much features under active
development and it also the same for its tests recently.
The rest of inactive features are usually updated sometimes just for a
maintenance purpose.

We have been focusing on developing for ETSI NFV v2 APIs and container
support in the recent releases, and the situation is going to be the same
for a while. So, we can move the tests other than for the active developed
features or basic features.
Considering the recent activities on the Tacker's repo, the following four
test scenarios are enough.

- tacker-functional-devstack-multinode-sol-v2-basic
- tacker-functional-devstack-multinode-sol-v2-vnflcm
- tacker-functional-devstack-multinode-sol-v2-individual-vnfc-mgmt
- tacker-functional-devstack-multinode-sol-kubernetes-v2

And the rest of the tests can be move to ``non-voting``, or dropped from zuul.

- tacker-functional-devstack-multinode-sol-legacy-nfvo
- tacker-functional-devstack-multinode-sol-vnflcm
- tacker-functional-devstack-multinode-sol-vnflcm-userdata
- tacker-functional-devstack-multinode-sol-vnfpkgm
- tacker-functional-devstack-multinode-sol-separated-nfvo
- tacker-functional-devstack-multinode-sol-kubernetes
- tacker-functional-devstack-multinode-sol-v2-notification
- tacker-functional-devstack-multinode-sol-v2-prometheus
- tacker-functional-devstack-multinode-sol-separated-nfvo-v2
- tacker-functional-devstack-multinode-sol-multi-tenant
- tacker-functional-devstack-multinode-sol-https-v2
- tacker-functional-devstack-multinode-sol-encrypt-cred-barbican
- tacker-functional-devstack-multinode-sol-encrypt-cred-local
- tacker-functional-devstack-multinode-sol-kubernetes-multi-tenant
- tacker-functional-devstack-kubernetes-oidc-auth
- tacker-functional-devstack-multinode-sol-v2-az-retry
- tacker-functional-devstack-enhanced-policy-sol
- tacker-functional-devstack-enhanced-policy-sol-kubernetes
- tacker-compliance-devstack-multinode-sol
- tacker-functional-devstack-multinode-sol-terraform-v2

Of course we can change the categories as the situation is changed.


3. Drop tests almost not updated from zuul
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In general, although keeping health of the code by running end-to-end tests
for all the features frequently is one of the best way to ensure the quality,
we cannot cover whole the features in reality considering to run on zuul
environment because of the limitation of resources.

For considering current development activity in Tacker team,
the features for legacy or ETSI NFV v1 supports have not been active and rarely
updated for maintenance.
So, we can drop these tests from zuul jobs if there will be no plan to
re-activate.
We can still run on them on local environment to check health of the features
even if these tests are dropped from zuul check.

.. note::

   The decision which tests will be dropped is under discussion.

- tacker-functional-devstack-multinode-sol-legacy-nfvo
- tacker-functional-devstack-multinode-sol-vnflcm
- tacker-functional-devstack-multinode-sol-vnflcm-userdata
- tacker-functional-devstack-multinode-sol-vnfpkgm
- tacker-functional-devstack-multinode-sol-separated-nfvo
- tacker-functional-devstack-multinode-sol-kubernetes
- tacker-functional-devstack-multinode-sol-multi-tenant
- tacker-functional-devstack-multinode-sol-kubernetes-multi-tenant

4. Rename each test scenarios and revise directory structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All the name of each test scenario is named like as
``tacker-functional-devstack-A-B-C`` for some historical reason.
However, it is not so organized well because there is no rules for
`A``, ``B``, ``C`` and ``D`` might be added,
and the prefix is too long for maintaining the tests.

Looking the names on other projects, such as
``nova-tox-functional-py310`` in nova or
``neutron-functional-with-uwsgi`` neutron,
it is OK to use more conscious names in our project.

- Remain the prefix ``tacker-functional`` to show the project name and
  the category of the test.

- Remove ``devstack`` has no meaning actually.

- Use shortnames such as ``k8s`` for ``kubernetes`` or ``multi`` for
  ``multinode``.

Revising directory or file structure of test codes and ``.zuul.yaml``.
We don't need to change the test codes itself without changing the test name,
should do introduce ``zuul.d`` directory to divide ``.zuul.yaml`` into
several files as a manner of maintenance the zuul jobs when the number of
tasks is getting large.
However, how we should divide ``.zuul.yaml`` is under discussion.


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
=====================

For the purpose of evaluating Tacker with the functional tests as
end-to-end tests,
You will be able to run the tests on your local environment by following
the instruction which is added to the documentation.
This instruction includes several test cases such as running on multinodes, or
deploying depending applications such as Prometheus for testing
performance/fault management features.

The functional tests running on local environment can be run as the similar way
to on zuul. It is launched from ``tox`` command and all the results of tests
are reported on your terminal.
Moreover, you can actively evaluate functional tests with your favorite tools
which is not able to do on zuul. It also the same for developers become to
debug actively with their favorite debugging tools.

Example of configuration files such as ``local.conf`` are also included in
the instructions.

Performance Impact
------------------

None


Other deployer impact
---------------------

None

Developer impact
----------------

Same as described in ``Other end user impact``.

Upgrade impact
--------------

None


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  * Yasufumi Ogawa <yasufum.o@gmail.com>

Work Items
----------

- Revise functional test codes or way to run the test to reduce the total
  amount of time for running the test by following these steps.

  - (1) Divide time consuming tests
  - (2) Move tests less frequently updated to move to non-voting
  - (3) Drop tests almost not updated from zuul
  - (4) Rename each test scenarios and revise directory structure

- Add instructions for running functional tests on your local environment
  mainly for supporting the tests dropped from zuul jobs.


Dependencies
============

None


.. _testing:

Testing
=======

We will provide a set of scripts for deploying Tacker's controller and worker
nodes and some additional helper scripts for creating VNF package which is
required for running the functional tests.

Here is an image of running a test case.
First of all, deploy dedicating VMs for Tacker's controller or worker roles
on your host machine. This is an example of using ``vagrant``, but how we
deploy VMs is still under consideration.

.. code-block:: console

  vagrant up

Then, setup all the nodes with ``ansible``

.. code-block:: console

  ansible-playbook -i host site.yaml

After all the nodes are ready to run tests, login to the controller node
and run setup script and test.

.. code-block:: console

  ssh stack@controller
  cd /path/to/tacker
  sh /path/to/setup-script.sh
  tox -e tacker-functional-devstack-multinode-sol-vnflcm-userdata


Documentation Impact
====================

Add documentation for describing the details of usages explained in the
previous :ref:`Testing` section.


References
==========


History
=======

None
