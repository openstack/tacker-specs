..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================================
LCM operation with user data
===========================================
This spec describes LCM operation method using LCM operation user data.

Problem description
===================

In Tacker, consumer uses VNFD in order to manage and orchestrate network
services and virtualized resources on the NFVI. However, depending on VNF type,
there are more requirements than can be described in current VNFD. it is limited
to describe specific VNF deployment information in the VNFD compared with actual
commercial use case.

Here are examples of actual use cases.

* Operators must design CPU pinning assignments at the physical level.
* Depending on the VNF type, a operator may want to attach external storage
  instead of Cinder.
* Operators can modify the high availability design of VNF depending on the
  availability of VIM/NFVI.

Current standardization [sol001]_ does not support describing those
configurations in VNFD. On the other hand, in a real complex use case,
VIM and NFVI configuration described above must be considered.
This proposed method realizes that HOT can be described more flexibly and
consumer can execute VNF deployment that meets specific requirements.

Proposed change
===============
.. note:: This methodology is under discussion within ETSI ISG NFV. The specification
          can be modified according to standardization [sol014]_.

The scope of this spec focuses on: designing LCM operation method using
LCM operation user data. Consumer provides the choice of input parameters
for HOT. in this method, consumer provides contents described below to Tacker
via VNF Package:

* Base HOT: Native cloud orchestration template, HOT in this context,
  which is commonly used for LCM operations in different VNFs.
  This base HOT can work on OpenStack API and be filled by input parameters.
* LCM operation user data: A script that returns key/value data as Heat
  input parameters used for base HOT. As Heat input parameter, OpenStack
  parameters that are not statically defined in the VNFD.(E.g. flavors,
  images, hardware acceleration, driver-setup, etc.) can be assigned.

Instantiation procedure with LCM operation user data
----------------------------------------------------
As an example, VNF instantiation procedure using LCM operation user data is
described below.

.. seqdiag::

  seqdiag {
    Client -> VNFMplugin [label = "Request InstantiateVNF"];
    VNFMplugin -> VNFMplugin [label = "Decide instantiation method"];
    VNFMplugin -> NFVOplugin [label = "Get VNF package"];
    VNFMplugin <<- NFVOplugin [label = "VNFD, baseHOT,
                                        LCM operation user data"];
    VNFMplugin -> Glance [label = "Create image"];
    VNFMplugin <<- Glance [label = "ImageId"];
    VNFMplugin -> LCMOperationUserData [label = "Call LCM operation user data"];
    VNFMplugin <<- LCMOperationUserData [label = "key-value parameters"];
    VNFMplugin -> Heat [label = "Create stack with key-value
                                 parameters and baseHOT"];
    VNFMplugin <<- Heat;
    Client <<- VNFMplugin;
  }

Instantiating VNF, as illustrated in above sequence diagram, consists of
following steps.

1. Consumer sends VNF instantiation request through Instantiate VNF API
   Request. In this term, VNF package including base HOT,
   LCM operation user data, and VNFD has already been uploaded in Tacker.

2. There is a decision-making process to choose instantiation method.
   Tacker will check the value of "additionalParam", one of attributes in
   InstantiateVNFRequest API, and decide which LCM method
   should be executed. If there is a flag regarding LCM operation user data,
   for exmaple `-additionalParam "lcm-operation-user-data:file_name.py
   lcm-operation-user-data-class:class_name"`, Tacker proceed VNF
   instantiation with LCM operation user data as described below. If not,
   Tacker proceed it with Tosca-parser and Heat-translator supported in
   current OpenStack.

3. Tacker will get VNFD, parameter LCM operation user data, and base HOT from VNF package.

4. Tacker creates an image file and Flavor and get Ids.
   According to ETSI NFV document [sol003]_, the creation of images and
   flavors are executed by NFVO plugin. In this proposal, Tacker as VNFM
   handle these operation instead of NFVO because these features will not
   be introduced in Ussuri version of Tacker.

5. Tacker runs LCM operation user data with ImageId and FlavorId
   to extract Heat input parameters from VNFD, VNF Instantiation Request
   body, and Response of Granting from NFVO.

   * External network information can be extracted from
     InstatiateVNFRequest API and passed on as a program arguments.
   * According to ETSI NFV documents, Image Id and Flavor Id are passed
     from NFVO with Responce of Grant API. In this proposal, Tacker as VNFM
     handle these Ids instead of NFVO because Grant API will not be
     introduced in Ussuri version of Tacker.

6. Tacker creates stack with Heat input parameters and base HOT.

.. note:: Though LCM operation user data contains parameter mappings for different
          LCM operation such as VNF update, VNF instantiation can be supported
          in this release.

Alternatives
------------
Since the current VNF instantiation by Tacker with Tosca Parser / Heat
translator and the proposed method are common in creating a HOT using VNFD,
this proposal is only an optional method. In case there is a special
requirement for VNF in addition to the contents described in VNFD,
it is appropriate that the proposed method is able to describe the
HOT more flexibly.

Data model impact
------------------
None

REST API impact
---------------
This proposed function will be utilized with new LCM API proposed
in other spec [nfv_api_spec]_.

Security
--------
None

Notifications impact
--------------------

None

Other end user impact
---------------------
Consumer has to create parameter LCM operation user data and Base HOT.

Performance impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

None

Implementation
===============

Assignee(s)
------------

Primary assignee:
  Keiko Kuriu <keiko.kuriu.wa@hco.ntt.co.jp>

Other contributors:
  Hiroo Kitamura <hiroo.kitamura@ntt-at.co.jp>

Work Items
-----------
#. Implement decision-making process to choose LCM method
#. Implement runtime environment for parameter LCM operation user data
#. Implement Unit and functional tests
#. Documentation

Dependencies
=============
This methodology will work with upcoming development for LCM API [lcmapi_spec]_.


Testing
========
- VNF instantiation with LCM operation user data

Reference
==========
.. [sol001] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/02.06.01_60/gs_NFV-SOL001v020601p.pdf
.. [sol014] https://docbox.etsi.org/ISG/NFV/Open/Drafts/SOL014ed271_VR_descriptor_stage_3/NFV-SOL014ed271v070.docx
.. [sol003] https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_NFV-SOL003v020601p.pdf
.. [lcmapi_spec] https://review.opendev.org/#/c/591866/
.. [nfv_api_spec] https://review.opendev.org/#/c/591866/
