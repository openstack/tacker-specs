================================================
Support handling large query results by ETSI NFV
================================================

https://blueprints.launchpad.net/tacker/+spec/paging-query-result

This proposal aims to support handling large query results according to ETSI
NFV SOL013 [#NFV-SOL013_351]_.


Problem Description
===================

According to ETSI NFV SOL013, if the performance of a server is affected by
large number of query results, it should return 400 Bad Request or handle them
as subset results with using URI query parameter "nextpage_opaque_marker".
Target APIs which exist in current Tacker are the following.

+ SOL002 [#NFV-SOL002_261]_

  + {apiRoot}/vnflcm/v1/vnf_lcm_op_occs

+ SOL003 [#NFV-SOL003_261]_

  + {apiRoot}/vnflcm/v1/vnf_instances
  + {apiRoot}/vnflcm/v1/vnf_lcm_op_occs
  + {apiRoot}/vnflcm/v1/subscriptions
  + {apiRoot}/vnfpkgm/v1/vnf_packages

+ SOL005 [#NFV-SOL005_261]_

  + {apiRoot}/vnfpkgm/v1/vnf_packages

However, even with the above APIs, current Tacker handles all query results as
a single query. In addition, each API cannot return 400 Bad Request even if
there are large query results.


Proposed Change
===============

Paging query results according to SOL013
----------------------------------------

Between two alternatives described in the above, we choose paging query results
as Tacker's behavior.

When the number of searches reaches a certain value (set for each API), the API
which provides the paging feature returns already searched results as a
response.
In the Link header of the response, a query parameter "nextpage_opque_marker"
and its arbitrary value, which has the UUID format, are included with a URL like
the following.

::

<http://example.com:9890/vnflcm/v1/vnf_lcm_op_occs?nextpage_opaque_marker=603b2a59-2483-4d0d-ad13-25b2a7e87eac>; rel="next"

The client accesses this URL and fetches next page.

Tacker recognizes the previous query by the value of "nextpage_opaque_marker"
parameter, and then returns a subset which belongs to the next page by checking
already fetched search results.
At that time, when the next page also exists, Tacker adds a URL with
"nextpage_opaque parameter" into Link header in a similar way.
When there is no next page, Tacker doesn't provide the Link header in the
response anymore.

If there are already returned pages among the fetched results, these are
deleted. Also, if there are pages which have not been returned and a certain
time period has passed, these are deleted. The time period for deleting can be
configurable.

Fetching entire records as a result
-----------------------------------

When "all_records=yes" exists in a query parameter, Tacker returns all records
without paging behavior even if a specific value is set as a query.

Two behaviors of responses described in the above varies each other as below.

First of all, each target API has a configurable value, which indicates the
number of maximum records to be contained in a paged response.

When there is no query parameter in an API request and the number of all
records to be responded is not more than the maximum records value, Tacker
returns all records as a single response. In the similar situation, if the
number of all records to be responded is more than the maximum records value,
Tacker returns records separating its number by the value.

On the other hand, when there is the query parameter "all_records=yes" in an
API request, Tacker returns all records as a single response regardless of the
number of all records to be responded, even if the maximum records value is
set.


Data Model Impact
-----------------
None

REST API Impact
---------------
The following features are added into target APIs by this specification.

+ New query parameters "nextpage_opaque_marker" and "all_records=yes" become
  settable into URIs.

+ Receiving all query results at once becomes selectable.

+ Multiple requests and responses of REST API can occur between a client and
  Tacker in case of paging.

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
Large query results for API request become separated into shorter ones. It can
improve the performance of the server during API response process.

IPv6 Impact
-----------
None

Other Deployer Impact
---------------------
None

Developer Impact
----------------
None

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
  Koichi Edagawa <edagawa.kc@nec.com>

Other contributors:
  Tsukasa Inoue <inoue.tsk@nec.com>

Work Items
----------

#. To define the maximum value of records in a page as configurable per target
   API.

#. To change existing code so that records in a response of a target API can be
   shown as paged response with "nextpage_opaque_marker" during a request.

#. To change existing code so that all records in a response of a target API can
   be shown as a single query result in case of setting "all_records=yes" in a
   request.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added.

Documentation Impact
====================

Complete API Documentation in Contributor Guide will be added to explain about
new queries as request parameters for each target API.

References
==========

.. [#NFV-SOL013_351]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.05.01_60/gs_NFV-SOL013v030501p.pdf
.. [#NFV-SOL002_261]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/002/02.06.01_60/gs_nfv-sol002v020601p.pdf
.. [#NFV-SOL003_261]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. [#NFV-SOL005_261]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.06.01_60/gs_NFV-SOL005v020601p.pdf
