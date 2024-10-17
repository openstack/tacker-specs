..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

====================================
Performance Improvement of List APIs
====================================

This proposal is for an improvement of retrieving a list of resources below
managed in Tacker [#api_list_vnflcm_v2]_.

* VNF instance
* VNF LCM operation occurrence
* Active subscription

https://blueprints.launchpad.net/tacker/+spec/perf-improve-list-apis


Problem description
===================

In the current implementation of APIs in tacker, we've not
considered so much about performance or time to response of
retrieving data in a case of a lot of entries on the database,
which is likely more happened in large-scale commercial environment.
It might be registered a lot of entries and have long lifetime for each
entry. So, as a result, there are a lot of entries registered on the database
and it takes some more times to retrieve a target data.

From our simple performance analysis, it takes around 14 seconds or more for a
query for 50,000 entries.
The number of entries is not so much excesive which the response time is
not acceptable for users.
The main reason why the response is larger than expected is not for database
itself but for some implementation in Tacker for which we have not considered
well for performance optimization.

Use Cases
---------

There is no additional usecase because this proposal is for an improvement
of some ways of database usage or data processing after retrieving.


Proposed change
===============

The purpose of this proposal is make small changes for performance optimization
and reduce the total amount of times for retrieving a list of required data.
Although there are several approaches to improvement accessing database from
python program, this proposal is only focusing on the effective approaches
chosen from some simple evaluation tests.

There are four items of the problems and ideas for improvement described below.

#. Skip to convert to TackerObject

In current Tacker's implementation, each entry of data retrieved from
the database is converted to a TackerObject at once, then to a dict object
before setting up a response for a request of acquiring a list for convention.

For the most usecase in Tacker, converting to dict object is required
to setup the response, but to TackerObject is not required and can be skipped
for considering the usage it actually.

#. Refactor filtering

Tacker supports a set of attributes for filtering as defined
in ETSI NFV SOL013 [#sol013]_.
In the implementation of filtering for these attributes, it does not use any
filtering of database, but is done in Tacker's side after retrieving all the
entries from the database.

* eq
* neq
* in
* nin
* gt
* gte
* lt
* lte
* cont
* ncont

The filtering in Tacker is costly and the performance is lesser than
database's filtering.
Although it cannot support all the attributes of SOL013 specs, but
still enables to reduce the number of entries from database by giving
some limited query condition, then filter all the remained entries.

#. Cut off _link attribute

The `_link` attribute is added to all the entries of which should be included
in the results for ETSI NFV standards.
In the current Tacker implementation, this `_link` attribute is not included
in each entries in the database and added to the entries after the data is
retrieved from the database.

However, the process of adding `_link` is done in python code and it's also
costly.
In addition, there are just a few cases using `_link` attribute in reality
and can be skipped to add the attribute.

#. Revise checking attributes

There some tiny problems in checking attributes and which can make a
performance lesser such as:

* Refer to definition of TackerObject for each query
* Useless logging for debug messages

We can expect to reduce the total amount of time by refactoring them.

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
---------------------

None

Performance Impact
------------------

We have evaluated a response time of retrieving a list of
VNF instances several times.

.. code-block::

    GET /vnflcm/v2/vnf_instances

How to get the response time is simply adding log messages of
(1) time to query bunch of data from the database,
(2) time to convert the retrieved data in the required format
and (3) total amount of times as like as below code.

.. code-block:: python

    t1 = time.perf_counter_ns()
    query = context.session.query(model_cls.id, model_cls.vnfInstanceName,
        model_cls.vnfInstanceDescription, model_cls.vnfdId,
        model_cls.vnfProvider, model_cls.vnfProductName,
        model_cls.vnfSoftwareVersion, model_cls.vnfdVersion,
        model_cls.instantiationState)
    result = query.all()    # to query
    t2 = time.perf_counter_ns()
    ret = [cls.from_db_obj(item) for item in result]   # to convert
    t3 = time.perf_counter_ns()
    ret = [item.to_dict() for item in ret]             # to dict
    t4 = time.perf_counter_ns()
    LOG.debug("### query %d, convert %d %d ###", (t2 - t1)/1000000,
        (t3 - t2)/1000000, (t4 - t3)/1000000)  # msec

Here are some examples of the result.
Without any modification for improvement,
times to query and convert are around 3,000[ms] and total time is
14.12[sec].

* query: 2,598 [ms]
* convert: 3,724 [ms]
* total: 14.12 [sec]

On the other hand, it can be reduced if converting to TackerObject is discarded.

* query: 1,193 [ms]
* convert: 3,233 [ms]
* total: 9.54 [sec]

And more, the total time can be reduced up to about 2 [sec] in a noticeable case.

Other deployer impact
---------------------

None

Developer impact
----------------

None

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

Revise the current implementation for each item discussed in the previous
Proposed Changes section.

#. Skip to convert to TackerObject

Replace converting data directly to dict object to skip imtermediate TackerObject.

#. Refactor filtering

Change querying the database to limit the number of results by giving
appropriate conditions for each query and to avoid all the entries
from the database first.

#. Cut off _link attribute

Add an opiton to enable to exclude ``_link`` for a usecase in which
it's not required.
We should still remain this attribute to follow the SOL specification.

#. Revise checking attributes

  * Optimize queries refering to TackerObject.
  * Remove useless logging for debug messages

Dependencies
============

None


Testing
=======

None


Documentation Impact
====================

None

References
==========

.. [#api_list_vnflcm_v2] https://docs.openstack.org/api-ref/nfv-orchestration/v2/vnflcm.html
.. [#sol013] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.03.01_60/gs_nfv-sol013v030301p.pdf

History
=======

None
