============================================
Enhance CLI for handling large query results
============================================

https://blueprints.launchpad.net/tacker/+spec/paging-query-result

This proposal aims to enhance CLI for handling large query results.


Problem Description
===================

Tacker has supported for handling large query results [#TACKER-PAGING-SPEC]_
according to ETSI NFV SOL013 [#NFV-SOL013_351]_.
By this support, when the number of records to a query exceeds a certain value,
the list of records is paginated as default.
Because of this, Tacker's client needs to query next page one by one if it
exists.
Additionally, Tacker has been able to get all records at once by adding the
query parameter "all_records=yes" into the URL of the API to be queried.
The client commands existing in Yoga release and corresponding to target APIs
in Tacker are below.

+ openstack vnflcm list
+ openstack vnflcm op list
+ openstack vnf package list

Since there is no method to obtain next page in client side, currently these
commands cannot handle pagination.
From the user point of view, there is the case where the user needs to get all
records by single operation.
However, handling large query results at once affects the performance of the
server.
Therefore, it is necessary to design the pagination feature in client side with
moderating the impact of the performance in server side.


Proposed Change
===============

To solve the problem above, we introduce the following process as the target
CLI feature by default in case of handling large query results.

(1) When a CLI request is executed by user, Tacker server paginates records
    and responds to it with the first page of them to client side.

(2) When client side receives the response and recognizes that it contains the
    link for next page, the record in the response is retained internally and
    it queries next page to server side.

(3) Until there is no next page existing in the server, client side queries it
    one by one and retains records.

(4) After receiving all paginated records from the server, client side
    assembles retained records and then displays them as a CLI response.

.. seqdiag::

  seqdiag {
    user -> tacker-client [label = "execute list command"]
    tacker-client -> tacker-server [label = "execute HTTP GET method" ]
    tacker-client <-- tacker-server [label = "return the first page" ]
    tacker-client -> tacker-server [label = "execute HTTP GET method" ]
    tacker-client <-- tacker-server [label = "return next page" ]
    === loop while there is next page existing ===
    tacker-client -> tacker-server [label = "execute HTTP GET method" ]
    tacker-client <-- tacker-server [label = "return the last page" ]
    user <-- tacker-client [label = "show all records" ]
  }


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

Work Items
----------

The following items need to be performed in client side.

* Add checking if there is a link for next page of records in response
  header from Tacker server.

* Add a process to retain records from Tacker server and query next page.

* Add a process to assemble all retained records and display them as a
  single CLI response.


Dependencies
============

None

Testing
=======

Unit tests for this enhancement will be added.

Documentation Impact
====================

None

References
==========

.. [#TACKER-PAGING-SPEC]
  https://specs.openstack.org/openstack/tacker-specs/specs/yoga/paging-query-result.html
.. [#NFV-SOL013_351]
  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/03.05.01_60/gs_NFV-SOL013v030501p.pdf
