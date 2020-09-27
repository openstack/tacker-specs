This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


====================
Tacker API Framework
====================

Currently there is an API implementation in tacker but it doesn't follow the
OpenStack standard. There are two API frameworks which are largely adopted
by the community 1. PECAN 2. Falcon
I have gone through all the possibilities about the selecting the framework
but the PECAN's adoption is very high as compare to Falcon by Openstack
community. Currently there are many OpenStack project already using
PECAN like zaqar, magnum & others but Ironic is facing lot of issues in
PECAN + WSME approach. Pecan community is not providing the support on
filed bugs. Falcon is faster and more secure as compare to PECAN.
We don't need to depend on third part project like WSME for attribute
validation if we use Falcon. Falcon has less dependencies as compare to
PECAN.
There are many project using PECAN now but taking all the above
considerations, we should better choose Falcon over PECAN.
Falcon is developed for complete Cloud REST API's. Currently Zaqar is using.

Problem description
===================

We need an API framework which gives us better performance, secure and
has good community support.
Current implementation is not adopted by OpenStack community & has less
performance as compare to Falcon/PECAN.

Proposed changes
================

It has huge impact on the API implementation layer. So we need to re-write
every API implementation but API endpoints remain the same.
All the API files we need to change & current directory structure will also
get changed.

WSGI Application Server -

Falcon uses gunicorn a Python WSGI HTTP Server. We should create an
application class where we can keep all the implementation related to WSGI.
Running Falcon API application is very simple.
Falcon used gunicorn to run the application & that's the reason falcon is
faster as compare to other frameworks.
Gunicorn is a Python WSGI HTTP server for UNIX.

Following are the changes -

Implement Controllers instead extensions -

We have written separate extension for nfvo & vnfm for API. We need to
introduce new controllers to below extensions.
tacker/extension/nfvo.py
tacker/extension/vnfm.py

Falcon Controllers -
tacker/api/controller/v1/nfvo.py
tacker/api/controller/v1/vnfm.py
All model attributes are defined under the same file which will be effective
way to handle all things at one level.

Handling attributes -

We can add validation hooks for images etc for checking given image type is
valid. Falcon offer before hooks, its decorator for validation attributes.

Example:

@falcon.before(validate_image_type)
def create_vim()

In this file, we can handle build-in types as well as custom types like
ImageName, TemplateName etc.

Exception Handling -

Falcon offers its own API level exception, no need to depend on other modules
to handle API level exceptions.

Example -
falcon.HTTPNotFound
falcon.HTTPForbidden
falcon.HTTPInternalServerError

Plugins -

I don't think there will be direct impact on existing plugins, but for new
features, we should write separate controllers & introduce the functionality.
Like VNFFG, it's better to write separate api/controller/v1/vnffg.py because
we are offering complete CRUD for VNFFG.
It's always better to write separate controller file for those who offer
complete CRUD operations.

Authentication -

Falcon supports multi authentication like SSL/TLS/HTTPS.

Tacker Web -
I don't think there is any impact on Tacker Web UI because we use HTTP WSGI
for new Tacker API framework. We will use Apache server to launch Tacker Web
UI.


Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

We have to rewrite API framework but endpoints remain same.

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

None

Other deployer impact
---------------------

We need add falcon to build.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

* Digambar Patil (digambarpat@gmail.com)

Work Items
----------

1. Introduce new API directory structure.
2. Implement validation using falcon hooks.
3. Implement controller for every extensions.
4. Write script to run tacker-api
5. Write unittests & functional tests

Dependencies
============

Testing
=======

API controller testing will be done.
Unit tests and function tests will be added for new API framework.

Documentation Impact
====================

We need to write how to new API framework implementation.

References
==========

https://wiki.openstack.org/wiki/Zaqar/pecan-evaluation
http://falcon.readthedocs.io/en/stable/user/tutorial.html
http://gunicorn.org
https://pypi.org/project/falcon-mutualauth
