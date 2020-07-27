==========================================
Enhance VNF package (TOSCA CSAR) in Tacker
==========================================
https://blueprints.launchpad.net/tacker/+spec/tosca-csar-mgmt-driver

This specification describes enhancement of VNF Packages Management in
Tacker.

Problem description
===================

In Train release, we have added limited support of VNF Package
Management as defined in ETSI NFV-SOL 005 [#etsi_sol005]_. Now, we want
to extend that support and implement following REST APIs.

* Read VNFD of an on-boarded VNF package ``GET /vnf_packages/{vnfPkgId}/vnfd``.
* Fetch an on-boarded VNF package ``GET /vnf_packages/{vnfPkgId}/package_content``.
* Update information about an individual VNF package ``PATCH /vnf_packages/{vnfPkgId}``.
* Implement query parameter support for list VNF packages.
* Upload VNF Package from URI REST API
  `` POST /vnf_packages/{id}/package_content/upload_from_uri`` accepts
  userName and password parameter but internally these parameters are
  not used while getting the CSAR zip file from the URI as specified in
  the addressInformation. If the server serving the CSAR zip requires
  authentication, it would return 401 error and the downloading of VNF
  package will fail thereby reverting back VNF package
  ``PackageOnboardingStateType`` status from ``uploading`` to
  ``create``. Use ``userName`` and ``password`` parameters to create
  ``Authorization`` HTTP header so that the server requiring
  authentication for getting VNF package will succeed.


Proposed change
===============

To implement new REST APIs we will need to make changes in the following
components:

* Tacker API service

  * Add new APIs for managing VNF Packages.
  * Modify the list VNF package API
    ``GET {apiRoot}/vnfpkgm/v1/vnf_packages`` to accept query parameters
    and filter out VNF packages accordingly.
  * Modify the upload VNF package from URI API to enable authentication
    using given username and password.
* Add new OSC commands in python-tackerclient to support management of
  VNF packages.

Tacker-server's new REST API Resources and methods overview:

+---------------------------------------------------------------+-------------+----------------------------------------+
| Resource URI                                                  | HTTP Method | Meaning                                |
+===============================================================+=============+========================================+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}/vnfd             | GET         | Read VNFD of an on-boarded VNF package |
+---------------------------------------------------------------+-------------+----------------------------------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}/package_content  | GET         | Fetch an on-boarded VNF package        |
+---------------------------------------------------------------+-------------+----------------------------------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}                  | PATCH       | Update information about an individual |
|                                                               |             | VNF package                            |
+---------------------------------------------------------------+-------------+----------------------------------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages?filter=                     | GET         | Get list of VNF packages using query   |
| (eq, vnfSoftwareVersion,'value')                              |             | URI parameters. This REST API is       |
|                                                               |             | already supported in Train release     |
|                                                               |             | except URI query parameters.           |
+---------------------------------------------------------------+-------------+----------------------------------------+

Fetch an on-boarded VNF Package
-------------------------------

In order to fetch an on-boarded VNF package based on ``HTTP_RANGE`` HTTP
request header, it's important to know the size of the CSAR zip file in
advance but currently size is not persisted in the ``vnf_packages`` db
table. So we need to add ``size`` db column of ``BigInteger`` type in
``vnf_package`` db table. For existing VNF packages, we will need to
calculate the size of the CSAR file and store it in the ``size`` db
column at the time of fetching an on-boarded VNF package if it's not
set. For new VNF packages, size will be calculated and set at the time
of uploading VNF package.



Use auth parameters for uploading VNF package from URI
------------------------------------------------------

Use ``userName`` and ``password`` parameters to set "Authorization"
header as shown below if these parameters are passed in the request body
of ``POST /vnf_packages/{id}/package_content/upload_from_uri`` REST API.

* The userName and password are combined with a single colon (:).
  This means that the userName itself cannot contain a colon.
* The resulting string is encoded using a variant of Base64.
* The authorization method (Basic and a space (e.g. "Basic ") is then
  prepended to the encoded string.

For example, if userName and password are "xyz" and "xyzpassword", then
the field's value is the base64-encoding of xyz:xyzpassword, or
eHl6Onh5enBhc3N3b3Jk and the Authorization header will appear as:

Authorization: Basic eHl6Onh5enBhc3N3b3Jk

Data model Impact
=================

Modify ``vnf_packages`` db table to add ``size`` column of type
``BigInteger``. The default value of ``size`` column will be set to 0.


REST API impact
===============

Below RestFul APIs will be added:

+--------------------------------------------------------------+-------------+----------------------------------------+-----------------+
| Resource URI                                                 | HTTP Method | Meaning                                | Response Codes  |
+==============================================================+=============+========================================+=================+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}/vnfd            | GET         | Read VNFD of an on-boarded VNF package | Success: 200    |
|                                                              |             |                                        | Error: 401,403  |
|                                                              |             |                                        | 404, 406, 409   |
+--------------------------------------------------------------+-------------+----------------------------------------+-----------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}/package_content | GET         | Fetch an on-boarded VNF package        | Success: 200    |
|                                                              |             |                                        | Error: 401, 403 |
|                                                              |             |                                        | 404, 406, 409,  |
|                                                              |             |                                        | 416             |
+--------------------------------------------------------------+-------------+----------------------------------------+-----------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages/{vnfPkgId}                 | PATCH       | Update information about an individual | Success: 200    |
|                                                              |             | VNF package                            | Error: 401,403  |
|                                                              |             |                                        | 404, 409        |
+--------------------------------------------------------------+-------------+----------------------------------------+-----------------+
| {apiRoot}/vnfpkgm/v1/vnf_packages?filter=                    | GET         | Get list of VNF packages using query   | Success: 200    |
| (eq, vnfSoftwareVersion,'value')                             |             | URI parameters. This REST API is       | Error: 400, 401,|
|                                                              |             | already supported in Train release     | 403             |
|                                                              |             | except URI query parameters.           |                 |
+--------------------------------------------------------------+-------------+----------------------------------------+-----------------+


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Hiroyuki Jo <hiroyuki.jo.mt@hco.ntt.co.jp>

Other contributors:
 * Nitin Uikey <nitin.uikey@nttdata.com>
 * Niraj Singh <niraj.singh@nttdata.com>

Work Items
----------

* Implement new REST APIs in /vnfpkgm/v1 endpoint.
* Add new OSC commands in python-tackerclient to support new REST APIs.
* Modify OSC ``vnf package list`` command to add command line options to
  filter out VNF packages.
* Add ``Authorization`` HTTP header support for downloading VNF package
  requiring authentication.
* Add unit and functional tests.

Dependencies
============

None

Testing
=======

Unit and functional test cases will be added for onboarding of VNF
Packages.

Documentation Impact
====================

None

References
==========

.. [#etsi_sol005] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.06.01_60/gs_nfv-sol005v020601p.pdf
