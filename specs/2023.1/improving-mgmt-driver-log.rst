===========================================
Improvement of Error Message of Mgmt Driver
===========================================

https://blueprints.launchpad.net/tacker/+spec/improving-mgmt-driver-log

This specification proposes two improvements as follows.

- Defining the interface of error handling between Tacker and Mgmt Driver
- Improving the message of exception raised when Ansible playbook fails

Problem description
===================

No clear interface between Tacker and Mgmt Driver
-------------------------------------------------

When an error occurs in Mgmt Driver, Tacker-conductor receives any type of
exception raised from Mgmt Driver.
Then, Tacker-conductor converts it to the type of
``ProblemDetails`` defined in ETSI GS NFV-SOL 013 v2.6.1 [#ETSI-GS-NFV-SOL013-v2.6.1]_
and stores it in the error field in VnfLcmOpOcc
defined in ETSI GS NFV-SOL 003 v2.6.1 [#ETSI-GS-NFV-SOL003-v2.6.1]_.

In this way, there are no rules of handling an error message
between Tacker and Mgmt Driver,
and how to define the type of error raised from Mgmt Driver depends on
users' implementation.

Mgmt Driver is a user-customizable plugin in Tacker.
Therefore, it is desirable that there is clear interface of error handling
between Tacker and Mgmt Driver for users.


Lack of information in error message of Ansible Mgmt Driver
-----------------------------------------------------------

The Tacker source code has
the Ansible Mgmt Driver sample [#sample-ansible-driver]_.

When using this sample,
the information included in the exception
generated when the Ansible playbook fails
is just "the return code of the command is not 0",
and users can only check this message by CLI "vnflcm op show".

The ``tacker-conductor.log`` includes more information about the error.
But in general, only an administrator has the authority
to access the log, and so there is no way for users to debug the error.

Therefore, it is necessary to improve the error users see through CLI command.

Proposed change
===============

This specification proposes two improvements.

1) Defining the interface of error handling between Tacker and Mgmt Driver
--------------------------------------------------------------------------

Defining the following rules for error handling
between Tacker-conductor and Mgmt Driver.

- The exception raised from Mgmt Driver must conform to the format
  of ``ProblemDetails`` defined in ETSI GS
  NFV-SOL 013 [#ETSI-GS-NFV-SOL013-v2.6.1]_ specification.
- Tacker-conductor must be able to catch the type of exception.

.. note:: For backward compatibility reasons, exceptions of any type
          can also be received. In that case, the exception is converted to a
          string and stored in the error field of VnfLcmOpOccs
          as the current implementation.

The definition of ``ProblemDetails`` is as follows.

.. csv-table::  Table 6.3-1: Definition of the ``ProblemDetails`` data type [#ETSI-GS-NFV-SOL013-v2.6.1]_
    :header: Attribute name, Data type, Cardinality, Description

    type,Uri,0..1, "A URI reference according to IETF RFC 3986 [#IETF-RFC-3986]_ that identifies
    the problem type. It is encouraged that the URI provides
    human-readable documentation for the problem (e.g. using
    HTML) when dereferenced. When this member is not present,
    its value is assumed to be 'about:blank'."
    title,String,0..1, "A short, human-readable summary of the problem type.
    It should not change from occurrence to occurrence of the problem,
    except for purposes of localization. If type is given and other
    than 'about:blank', this attribute shall also be provided."
    status,Integer,1, "The HTTP status code for this
    occurrence of the problem."
    detail,String,1, "A human-readable explanation specific
    to this occurrence of the problem."
    instance,Uri,0..1, "A URI reference that identifies the specific
    occurrence of the problem. It may yield further
    information if dereferenced"
    (additional attributes),Not specified.,0..N, "Any number of additional
    attributes, as defined in a specification or by an implementation."

To implement this rule, there should be the base exception class
complied with ``ProblemDetails`` in Tacker side.
And developers of Mgmt Driver use it to make exceptions in their Mgmt Driver
compatible with ``ProblemDetails``.

The base class is defined in `tacker/common/exceptions.py`.
The format is like this.

.. code-block:: python

  class ManagementDriverException(TackerException):
      def __init__(self, type=None, title=None, status, detail, instance=None)
          self.type = type
          self.title = title
          self.status = status
          self.detail = detail
          self.instance = instance

The exceptions in Mgmt Driver must inherit the base class to comply with
``ProblemDetails`` like this.

.. code-block:: python

  class CommandExecutionError(ManagementDriverError):


2) Improving the message of exception raised when Ansible playbook fails
------------------------------------------------------------------------
In Ansible Mgmt Driver sample,
``CommandExecutionError`` is raised when Ansible playbook fails.
This error always outputs the same message regardless of what task fails.

In this spec, it is modified to include following 3 points.

- VDU name to be configured
- Failed task name
- Extracted stdout message of the ansible-playbook command
  Related to the failed task

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
  Masaki Oyama <ma-ooyama@kddi.com>

Other contributors:
  Yukihiro Kinjo <yu-kinjou@kddi.com>

  Xu Hongjin <ho-xu@kddi.com>

  Hitomi Koba <hi-koba@kddi.com>

Work Items
----------
- Implement interface of error handling between Tacker and Mgmt Driver
- Improving the message of exception raised when Ansible playbook fails
- Add unittest for the interface

Dependencies
============
None

Testing
=======
None

Documentation Impact
====================
Documentation about the interface of error handling
between Tacker and Mgmt Driver will be added.

References
==========

.. [#ETSI-GS-NFV-SOL013-v2.6.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/013/02.06.01_60/gs_nfv-sol013v020601p.pdf
.. [#ETSI-GS-NFV-SOL003-v2.6.1] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. [#sample-ansible-driver]  https://opendev.org/openstack/tacker/src/branch/master/samples/mgmt_driver/ansible
.. [#IETF-RFC-3986] https://www.rfc-editor.org/rfc/rfc3986
