# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from azext_spring.tests.latest.custom_recording_processor import (SpringTestEndpointReplacer, SpringApiVersionReplacer)
from azure.cli.testsdk import (ScenarioTest)

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class AsaJobDeployScnearioTest(ScenarioTest):
    """
    TODO(jiec): Add some test cases for environemnt variables when backend is ready.
    """

    def __init__(self, method_name):
        super(AsaJobDeployScnearioTest, self).__init__(
            method_name,
            recording_processors=[SpringTestEndpointReplacer(), SpringApiVersionReplacer()],
            replay_processors=[SpringApiVersionReplacer()],
        )

    def test_replacer(self):
        original_string = '"primaryKey":"xxxxxxxxx"abcdefg'
        expected_string = '"primaryKey":"fake"abcdefg'
        actual_string = SpringTestEndpointReplacer()._replace(original_string)
        self.assertEqual(expected_string, actual_string)

    def test_deploy_job(self):
        self.cmd('spring job create -n mason-job-cli-record-test-2 -g jiec-rg-target -s jiec-e-df-eus-acs-gen1')
