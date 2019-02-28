..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


=============
Tacker Studio
=============

https://blueprints.launchpad.net/tacker/+spec/tacker-studio

This spec describes the plan to implement a new horizon panel for the NFV
dashboard that helps to visually design TOSCA templates for Tacker.

::

  +----------------------+       +---------------------+
  |                      |   +--->     Django form     |
  |    NFV dashboard     |   |   |   to define VNFD,   |
  |                      |   |   |     VNFFGD, NSD     |
  +---------+------------+   |   |      properties     |
            |                |   +---------------------+
  +---------v------------+   |   +---------------------+
  |                      |   |   |    Save to files    |
  |                      +---+   |    & store in       |
  |     Django Views     |       |  Tacker DB or in a  |
  |                      +------->   tacker-horizon's  |
  |                      |       |    static dir or    |
  |                      +-+     |   an NFS share(+)   |
  +-----------+-----+----+ |     +---------------------+
              |     |      |     +---------------------+
              |     |      +----->  Load and display   |
              |     |            | saved files content |
              |     |            +---------------------+
              |     |            +---------------------+
              |     +------------> Export and import   |
              |                  | external YAML files |
              |                  +---------------------+
              |                  +---------------------+
              +------------------> Onboard templates   |
                                 +----------+----------+
                                            |
  +-----------------------------------------v----------+
  |                                                    |
  |                 Tacker API                         |
  |                                                    |
  +----------------------------------------------------+

Problem description
===================

In order to launch a new VNF, VNFFG, or NS, we have to manually prepare a TOSCA
template YAML [#f1]_ file which may have typos, unexpected indents, wrong fields
etc... This spec proposes to build a web interface (horizon panel [#f3]_) that helps
us to design, store, and export VNFD, VNFFGD, NSD templates beautifully with
less errors.

Proposed changes
================

A new horizon panel will be implemented and plugged into the NFV dashboard
[#f2]_ which contains a form for generating each kind of descriptors (VNFD,
VNFFGD, NSD). The forms will have these input fields along with the template
attributes (name, description etc...):

::

  +----------------+-------------------------+
  | Resource type  | Description             |
  +================+=========================+
  |       VDU      | Virtual Deployment Unit |
  +----------------+-------------------------+
  |       CP       | Connection Point        |
  +----------------+-------------------------+
  |       VL       | Virtual Link            |
  +----------------+-------------------------+
  |      FIP       | Floating IPs            |
  +----------------+-------------------------+
  |    policies    | Policies                |
  +----------------+-------------------------+

and their properties.

The above forms will be implemented based on the Django form.
This forms will be integrated to the above panel and give us these abilities:

* Input information for the VDU (Tacker's resources and properties)

* Save and store designed templates to files (YAML format) in a
  tacker-horizon's static directory,

A Django view (controller) can help us to store the designed templates into
files in a tacker-horizon's static directory. If we do it this way, we keep
tacker-horizon database independant from the Tacker server.

The directory that contains the uploaded templates can be set in the Django's
setting of tacker-horizon as following [#f4]_:

MEDIA_ROOT = /path/to/uploaded/templates/

(+) If the user decides to put multiple tacker-horizon instances behind an
  HAProxy, It's his job to make sure the templates are replicated across
  those instances. And, it's out of scope of this spec.
(+) The path can be a local directory where we place tacker-horizon or an NFS
  path.
(+) Future works will store the templates in the Tacker's database and we
  can use tacker API to query.

* Load, parse and display the saved templates (YAML) on the panel view,

* Export designed templates to yaml file

A YAML parser python module needs to be implemented to handle template to YAML
conversion. Also, another module will be used to process the downloading
of the YAML file.

* Import and display external YAML files on the panel,

With the YAML parser and upload/download module, we can provide the ability to
import the external YAML files into Tacker Studio and re-config them (modify
their properties).

* Onboard designed templates (VNFD, VNFFGD, NSD) directly to Tacker server.

Tacker Studio will call the Tacker's API to onboard the designed templates.

Alternatives
------------

* The Heat Dashboard project [#f5]_ employs a drag and drop UI to generate
  heat templates which is quite advanced and complicated in the users point of
  view.

* Open Source MANO (OSM) has developed a GUI [#f6]_ that allows users to
  generate VNFD and NSD templates (packages) using a very simple web forms.

Data model impact
-----------------

In the future work, we can save the designed templates into the Tacker
database using Tacker API. In that case, a new table need to be created
to store the templates. The table model will be as following:

::

  +----------------------------------------------------------------+
  |                  Table name: tosca_templates                   |
  +------------------+--------+------------------------------------+
  | Column           | Type   | Default value                      |
  +------------------+--------+------------------------------------+
  | template_name    | string |                                    |
  +------------------+--------+------------------------------------+
  | tosca_version    | string | tosca_simple_profile_for_nfv_1_0_0 |
  +------------------+--------+------------------------------------+
  | template_type    | int    | 0                                  |
  +------------------+--------+------------------------------------+
  | template_content | text   |                                    |
  +------------------+--------+------------------------------------+

**Note:** template_type values are:

* 0: VNFD
* 1: VNFFGD
* 2: NSD


REST API impact
---------------

A set of new Tacker API functions needed to be made to manipulate the new
tosca_templates table (CRUD).

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
  Trinh Nguyen <dangtrinhnt@gmail.com>

Work Items
----------

1. Buil up a new Horizon panel that plug into NFV dashboard

2. Develope a set of Python modules that provides these functionalities:

* Django forms to input TOSCA template properties for Tacker,
* Export to yaml file,
* Import yaml files and display them,
* Save the template to draft files stores inside
  tacker-horizon,
* Load the template from draft files and display it,
* Delete existing draft,
* Call tacker api to onboarding vnfd, vnffgd, nsd from
  the draft templates.

3. Add the unit test cases of all of the above functions

4. Write the user guide for Tacker Studio

Dependencies
============

None

Testing
=======

A new set of unit test cases will need to be developed to check the generated
templates whether they have the proper TOSCA form with correct syntax.

Documentation Impact
====================

A new user guide for Tacker Studio will be added.

References
==========

.. [#f1] https://docs.openstack.org/tacker/latest/contributor/vnfd_template_description.html
.. [#f2] https://github.com/openstack/tacker-horizon
.. [#f3] https://docs.openstack.org/horizon/latest/
.. [#f4] https://docs.djangoproject.com/en/1.11/ref/settings/#media-root
.. [#f5] https://docs.openstack.org/heat-dashboard/latest/
.. [#f6] https://osm.etsi.org/wikipub/index.php/Creating_your_own_VNF_package_(Release_THREE)
