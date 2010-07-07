#  Copyright 2008 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import copy
import os
import unittest
from os.path import abspath, dirname, join, normcase
import shutil

from robot.utils.asserts import *
from robot.version import get_version
ROBOT_VERSION = get_version()

from mabot.model import io
from mabot.model.model import DATA_MODIFIED
from mabot.settings import SETTINGS


DATA_FOLDER = normcase(join(dirname(__file__), 'data',))
SUITES_FOLDER = join(DATA_FOLDER, 'suites')
SUITES_FOLDER_WITH_OS_SEP = SUITES_FOLDER + os.sep
HTML_DATASOURCE_ONLY = join(SUITES_FOLDER, 'testcases.html')
TSV_DATASOURCE_ONLY = join(SUITES_FOLDER, 'tsv_testcases.tsv')
XML_DATASOURCE_ONLY = join(SUITES_FOLDER, 'output.xml')
HTML_DATASOURCE_WITH_XML = join(SUITES_FOLDER, 'testcases2.html')
HTML_DATASOURCES_XML = join(SUITES_FOLDER, 'testcases2.xml')
INVALID_FORMAT_DATASOURCE = join(SUITES_FOLDER, 'text.inv')
NON_EXISTING_DATASOURCE = join(DATA_FOLDER, 'foo.html')
NON_EXISTING_XML = join(DATA_FOLDER, 'foo.xml')
DUPLICATE_USERKEYWORDS = join(DATA_FOLDER, 'duplicate_keywords.html')
INVALID_HTML = join(DATA_FOLDER, 'invalid.html')
INVALID_XML = join(DATA_FOLDER, 'invalid.xml')
VALID_HTML_INVALID_XML_DATASOURCE = join(DATA_FOLDER, 'valid_html_invalid_xml.html')
VALID_HTML_INVALID_XML_XML = join(DATA_FOLDER, 'valid_html_invalid_xml.xml')
HTML_DATASOURCE_WITH_UPDATES = join(DATA_FOLDER, 'html_with_updates.html')
SAME_TEST_NAME = join(DATA_FOLDER, 'same_test_name.html')


class _TestIO(unittest.TestCase):

    def setUp(self):
        self.orig_settings = copy.deepcopy(io.SETTINGS)
        self.io = io.IO()

    def tearDown(self):
        DATA_MODIFIED.saved()
        io.SETTINGS = self.orig_settings

    def _test_error(self, path, message, method=None):
        if not method:
            method = self.io.load_data
        message = "Could not load data!\n%s" % (message)
        assert_raises_with_msg(IOError, message, method, path)


class TestLoadData(_TestIO):

    def _test_loading(self, source, name):
        suite = self.io.load_data(source)
        self.assertEqual(suite.name, name)
        return suite

    def test_load_data_without_datasources(self):
        suite = self._test_loading(None, '')

    def test_load_data_with_only_html_datasource(self):
        suite = self._test_loading(HTML_DATASOURCE_ONLY, 'Testcases')

    def test_load_data_with_only_html_datasource_and_xml_loading_on(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        suite = self._test_loading(HTML_DATASOURCE_ONLY, 'Testcases')

    def test_load_data_with_only_tsv_datasource(self):
        suite = self._test_loading(TSV_DATASOURCE_ONLY, 'Tsv Testcases')

    def test_load_data_with_only_xml_datasource(self):
        suite = self._test_loading(XML_DATASOURCE_ONLY, 'Xml Testcases')

    def test_load_data_with_html_and_xml_datasources_xml_loading_off(self):
        io.SETTINGS["always_load_old_data_from_xml"] = False
        suite = self._test_loading(HTML_DATASOURCE_WITH_XML, 'Testcases2')
        self.assertEqual(suite.tests[0].status, 'FAIL')

    def test_load_data_with_html_and_xml_datasources_xml_loading_on(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        suite = self._test_loading(HTML_DATASOURCE_WITH_XML, 'Testcases2')
        self.assertEqual(suite.tests[0].status, 'PASS')

    def test_load_data_with_directory_and_xml_datasources_with_xml_loading_on(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        suite = self._test_loading(SUITES_FOLDER, 'Suites')
        self.assertEqual(suite.suites[0].tests[0].status, 'PASS')

    def test_load_datasource_and_xml_with_updates_in_html(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        suite = self._test_loading(HTML_DATASOURCE_WITH_UPDATES,
                                   'Html With Updates')
        self.assertEquals(len(suite.tests), 2)
        self.assertEquals(suite.tests[0].message, 'Failure!')
        self.assertTrue(DATA_MODIFIED.is_modified(),
                        "Status should be True as there is modifications.")

    def test_load_datasource_and_xml_with_no_updates_in_html(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        suite = self._test_loading(HTML_DATASOURCE_WITH_XML, 'Testcases2')
        self.assertFalse(DATA_MODIFIED.is_modified(),
                        "Status should be False as there is no modifications.")

    def test_load_datasource_and_xml_with_same_test_case_names(self):
        io.SETTINGS["always_load_old_data_from_xml"] = False
        msg = "Found test 'TC' from suite 'Same Test Name' 2 times.\n"
        msg += "Mabot supports only unique test case names!\n"
        self._test_error(SAME_TEST_NAME, msg)

    def test_load_data_with_html_suite_with_dublicate_keywords(self):
        msg = "Could not create keyword 'UK' in testcase 'Duplicate Keywords.TC1'."
        msg += "\nKeyword 'UK' defined multiple times\n"
        self._test_error(DUPLICATE_USERKEYWORDS, msg)

    def test_load_data_with_non_existing_datasource(self):
        msg = "Path '%s' does not exist!" % (NON_EXISTING_DATASOURCE)
        self._test_error(NON_EXISTING_DATASOURCE, msg)

    def test_load_data_with_non_existing_xml_datasource(self):
        msg = "Path '%s' does not exist!" % (NON_EXISTING_XML)
        self._test_error(NON_EXISTING_XML, msg)

    def test_load_data_with_non_existing_datasource_with_xml_loading_on(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        msg = "Path '%s' does not exist!" % (NON_EXISTING_DATASOURCE)
        self._test_error(NON_EXISTING_DATASOURCE, msg)

    def test_load_data_with_invalid_datasource_and_valid_xml(self):
        io.SETTINGS["include"] = ['no-tag']
        io.SETTINGS["always_load_old_data_from_xml"] = True
        msg = "Suite 'Testcases2' with includes 'no-tag' contains no test cases.\n"
        self._test_error(HTML_DATASOURCE_WITH_XML, msg)

    def test_load_data_with_valid_datasource_and_invalid_xml(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        msg =  self._get_invalid_xml_message(VALID_HTML_INVALID_XML_XML)
        self._test_error(VALID_HTML_INVALID_XML_DATASOURCE, msg)

    def _get_invalid_xml_message(self, path):
        if ROBOT_VERSION < '2.1':
            msg = "File '%s' is not a valid XML file.\n"
        else:
            msg = "Opening XML file '%s' failed: SyntaxError: no element found: line 1, column 0\n"
        return msg % (path)

    def test_load_data_with_xml_error_and_datasource_error(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        msg = "Parsing '%s' failed: File has no test case table. and\n" % (INVALID_HTML)
        msg += self._get_invalid_xml_message(INVALID_XML)
        self._test_error(INVALID_HTML, msg)


class TestGetDatasourceAndXml(_TestIO):

    def test_get_datasource_and_xml_from_xml(self):
        self.assertEqual(self.io._get_datasource_and_xml_from(XML_DATASOURCE_ONLY),
                         (None, XML_DATASOURCE_ONLY))

    def test_get_datasource_and_xml_from_html_loading_off(self):
        io.SETTINGS["always_load_old_data_from_xml"] = False
        self.assertEqual(self.io._get_datasource_and_xml_from(HTML_DATASOURCE_WITH_XML),
                         (HTML_DATASOURCE_WITH_XML, None))

    def test_get_datasource_and_xml_from_html(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        self.assertEqual(self.io._get_datasource_and_xml_from(HTML_DATASOURCE_WITH_XML),
                         (HTML_DATASOURCE_WITH_XML,
                          HTML_DATASOURCE_WITH_XML.replace('.html', '.xml')))

    def test_get_datasource_and_xml_from_dir_without_os_sep(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        self.assertEqual(self.io._get_datasource_and_xml_from(SUITES_FOLDER),
                         (SUITES_FOLDER, SUITES_FOLDER+'.xml'))

    def test_get_datasource_and_xml_from_dir_ending_with_os_sep(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        folder = SUITES_FOLDER.endswith(os.sep) and SUITES_FOLDER
        self.assertEqual(self.io._get_datasource_and_xml_from(SUITES_FOLDER_WITH_OS_SEP),
                         (SUITES_FOLDER, SUITES_FOLDER+'.xml'))

    def test_get_datasource_and_xml_from_tsv(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        self.assertEqual(self.io._get_datasource_and_xml_from(TSV_DATASOURCE_ONLY),
                         (TSV_DATASOURCE_ONLY, TSV_DATASOURCE_ONLY.replace('.tsv', '.xml')))

    def test_get_datasource_and_xml_from_txt(self):
        msg = "Parsing '%s' failed: Unsupported file format 'inv'.\n" % (INVALID_FORMAT_DATASOURCE)
        self._test_error(INVALID_FORMAT_DATASOURCE, msg, self.io.load_data)

    def test_get_datasource_and_xml_from_non_existing_file(self):
        msg = "Path '%s' does not exist!" % (NON_EXISTING_DATASOURCE)
        self._test_error(NON_EXISTING_DATASOURCE, msg,
                         self.io._get_datasource_and_xml_from)


class TestBackUp(_TestIO):

    def setUp(self):
        _TestIO.setUp(self)
        self.remove_files = []
        self.orig_get_timestamp = self.io._get_timestamp
        self.io._get_timestamp = self._get_timestamp
        io.SETTINGS["always_load_old_data_from_xml"] = True


    def tearDown(self):
        _TestIO.tearDown(self)
        self.io._get_timestamp = self.orig_get_timestamp
        for path in self.remove_files:
            if os.path.exists(path):
                os.remove(path)

    def test_backup_non_existing_xml(self):
        self._test_creating_backup(NON_EXISTING_XML, False)

    def test_backup_existing_xml(self):
        self._test_creating_backup(XML_DATASOURCE_ONLY, True)

    def test_backup_existing_xml_setting_always_load_off(self):
        io.SETTINGS["always_load_old_data_from_xml"] = False
        self._test_creating_backup(XML_DATASOURCE_ONLY, False)

    def test_backup_existing_xml_backup_exists(self):
        backup = self._get_backup(XML_DATASOURCE_ONLY)
        self._write(backup, "NOT IN XML")
        self.io._make_backup()
        self.assertTrue(os.path.exists(backup))
        self.assertTrue("NOT IN XML" not in self._read(backup))

    def test_backup_existing_xml_backup_exists_and_is_processed(self):
        backup = self._get_backup(XML_DATASOURCE_ONLY)
        data = """<?xml version="1.0" encoding="UTF-8"?>
<robot generated="20081204 10:49:05.015">NOT IN REAL XML
</robot>"""
        f = file(backup, 'w')
        f.write(data)
        self.io._make_backup()
        f.close()
        self.assertTrue(os.path.exists(backup))
        self.assertTrue('NOT IN REAL XML' in self._read(backup))

    def test_backup_invalid_xml_backup_exists(self):
        io.SETTINGS["always_load_old_data_from_xml"] = True
        backup = self._get_backup(INVALID_XML)
        self._write(backup, 'NOT IN REAL XML')
        self.assertRaises(IOError, self.io._make_backup)
        self.assertTrue(os.path.exists(backup))
        self.assertTrue(os.path.exists(self._get_timestamp_backup(INVALID_XML)))

    def test_backup_invalid_xml_backup_does_not_exist(self):
        self._test_creating_backup(INVALID_XML, False)
        self.assertFalse(os.path.exists(self._get_timestamp_backup(INVALID_XML)))

    def _test_creating_backup(self, path, backup_exists):
        backup = self._get_backup(path)
        self.io._make_backup()
        msg = backup_exists and 'Backup should exist' or 'Backup should not exist'
        self.assertEquals(os.path.exists(backup), backup_exists, msg)

    def _get_backup(self, path):
        backup = '%s.bak' % path
        self.remove_files.append(backup)
        self.io.output = path
        return backup

    def _get_timestamp_backup(self, path):
        backup = '%s_%s.bak' % (path, self._get_timestamp())
        self.remove_files.append(backup)
        return backup

    def _read(self, path):
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data

    def _write(self, path, data):
        f = open(path, 'w')
        f.write(data)
        f.close()

    def _get_timestamp(self):
        return '20090114092000'


class TestGetTimeStamp(_TestIO):

    def test_get_timestamp(self):
        timestamp = self.io._get_timestamp()
        self.assertEquals(len(timestamp), 14)
        try:
            int(timestamp)
        except ValueError:
            raise AssertionError('Timestamp is not valid!')


class TestSavingData(_TestIO):

    def setUp(self):
        _TestIO.setUp(self)
        shutil.copy(HTML_DATASOURCES_XML, HTML_DATASOURCES_XML+'.utest')
        self.io.load_data(HTML_DATASOURCE_WITH_XML)

    def tearDown(self):
        _TestIO.tearDown(self)
        shutil.move(HTML_DATASOURCES_XML+'.utest', HTML_DATASOURCES_XML)
        backup = HTML_DATASOURCES_XML + '.bak'
        if os.path.exists(backup):
            os.remove(backup)
        DATA_MODIFIED.saved()

    def test_save_data_without_output(self):
        generated = self.io._get_xml_generation_time()
        saved, changes = self.io.save_data(None, None)
        self.assertEquals(generated, self.io._get_xml_generation_time())
        self.assertFalse(saved)
        self.assertFalse(changes)

    def test_save_data_without_output_and_modifications(self):
        generated = self.io._get_xml_generation_time()
        DATA_MODIFIED.modified()
        saved, changes = self.io.save_data(None, None)
        self.assertNotEquals(generated, self.io._get_xml_generation_time())
        self.assertTrue(saved)
        self.assertFalse(changes)

    def test_save_data_with_output(self):
        generated = self.io._get_xml_generation_time()
        saved, changes = self.io.save_data(HTML_DATASOURCES_XML, None)
        self.assertNotEquals(generated, self.io._get_xml_generation_time())
        self.assertTrue(saved)
        self.assertFalse(changes)

    def test_save_data_should_change_output(self):
        output = HTML_DATASOURCES_XML.replace('testcases2.xml', 'new.xml')
        try:
            self.io.save_data(output, None)
            self.assertEquals(self.io.output, output)
            self.assertTrue(os.path.exists(output))
        finally:
            os.remove(output)

    def test_saving_when_data_is_reloaded_from_xml(self):
        self._prepare_settings_for_reload()
        self.io.xml_generated = "changed"
        try:
            saved, changes = self.io.save_data(HTML_DATASOURCES_XML, None)
        finally:
            self._restore_settings()
        self.assertTrue(changes)
        self.assertTrue(saved)

    def _prepare_settings_for_reload(self):
        self._orig_always_load = SETTINGS["always_load_old_data_from_xml"]
        self._orig_check = SETTINGS["check_simultaneous_save"]
        SETTINGS["always_load_old_data_from_xml"] = True
        SETTINGS["check_simultaneous_save"] = True

    def _restore_settings(self):
        SETTINGS["always_load_old_data_from_xml"] = self._orig_always_load
        SETTINGS["check_simultaneous_save"] = self._orig_check


if __name__ == "__main__":
    unittest.main()
