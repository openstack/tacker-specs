# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import glob
import re

import docutils.core
from docutils.parsers import rst
from docutils.parsers.rst import directives
import testtools


class FakeDirective(rst.Directive):
    has_content = True
    def run(self):
        return []


directives.register_directive('seqdiag',  FakeDirective)
directives.register_directive('blockdiag',  FakeDirective)
directives.register_directive('nwdiag',  FakeDirective)
directives.register_directive('actdiag',  FakeDirective)


class TestTitles(testtools.TestCase):
    def _get_title(self, section_tree):
        section = {
            'subtitles': [],
        }
        for node in section_tree:
            if node.tagname == 'title':
                section['name'] = node.rawsource
            elif node.tagname == 'section':
                subsection = self._get_title(node)
                section['subtitles'].append(subsection['name'])
        return section

    def _get_titles(self, spec):
        titles = {}
        for node in spec:
            if node.tagname == 'section':
                section = self._get_title(node)
                titles[section['name']] = section['subtitles']
        return titles

    def _check_trailing_spaces(self, tpl, raw):
        for i, line in enumerate(raw.split("\n")):
            trailing_spaces = re.findall(" +$", line)
            self.assertEqual(
                0, len(trailing_spaces),
                "Found trailing spaces on line %s of %s" % (i+1, tpl))

    def _check_titles(self, titles):
        # No explicit titles check, leaving this as a placeholder
        return

    def test_template(self):
        releases = [x.split('/')[1] for x in glob.glob('specs/*/')]
        for release in releases:
            if release[0] < 'm':
                # Don't bother enforcement for specs before Mitaka,
                # or that belong to 'archive' and 'backlog'
                continue
            try:
                # Support release-specific template.
                with open("specs/%s-template.rst" % release) as f:
                    template = f.read()
            except IOError:
                # Base template if release template not found.
                with open("specs/template.rst") as f:
                    template = f.read()
            spec = docutils.core.publish_doctree(template)
            template_titles = self._get_titles(spec)

            files = glob.glob("specs/%s/*" % release)
            for filename in files:
                self.assertTrue(filename.endswith(".rst"),
                                "spec's file must uses 'rst' extension.")

                with open(filename) as f:
                    data = f.read()
                    spec = docutils.core.publish_doctree(data)
                    titles = self._get_titles(spec)
                    self._check_titles(titles)
                    # TODO(kanagaraj-manickam): Fix the same old specs as well
                    if filename.startswith('specs/newton') or \
                            filename.startswith('specs/ocata'):
                        self._check_trailing_spaces(filename, data)
