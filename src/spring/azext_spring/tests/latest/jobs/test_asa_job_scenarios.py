# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import os
import re

from azext_spring.vendored_sdks.appplatform.v2024_05_01_preview import models
from azure.cli.testsdk import (ScenarioTest)

from ..custom_dev_setting_constant import SpringTestEnvironmentEnum
from ..custom_preparers import (SpringPreparer, SpringResourceGroupPreparer, SpringJobNamePreparer)
from ..custom_recording_processor import (SpringTestEndpointReplacer, SpringApiVersionReplacer)

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
        self.job_resource_type = 'Microsoft.AppPlatform/Spring/jobs'
        self.job_resource_id_regex_pattern = r"/subscriptions/[^/]+/resourceGroups/[^/]+/providers/Microsoft\.AppPlatform/Spring/[^/]+/jobs/[^/]+"

    def test_replacer(self):
        original_string = '"primaryKey":"xxxxxxxxx"abcdefg'
        expected_string = '"primaryKey":"fake"abcdefg'
        actual_string = SpringTestEndpointReplacer()._replace(original_string)
        self.assertEqual(expected_string, actual_string)

    @SpringResourceGroupPreparer(dev_setting_name=SpringTestEnvironmentEnum.STANDARD['resource_group_name'],
                                 location="eastus")
    @SpringPreparer(**SpringTestEnvironmentEnum.ENTERPRISE_WITH_TANZU['spring'])
    @SpringJobNamePreparer()
    def test_deploy_job_1(self, resource_group, spring, job):
        self._prepare_kwargs_for_deploy_job(resource_group, spring, job)
        self._test_deploy_job_step_1()

    def _test_deploy_job_step_1(self):
        response_in_json = self.cmd('spring job create -n {job} -g {rg} -s {serviceName}', checks=[
            self.check('name', '{job}'),
            self.check('type', 'Microsoft.AppPlatform/Spring/jobs'),
        ]).get_output_in_json()

        job_resource = models.JobResource.deserialize(response_in_json)
        self.assertEqual(self.kwargs['job'], job_resource.name)
        self.assertEqual(self.job_resource_type, job_resource.type)
        self.assertIsNotNone(job_resource.properties)
        self.assertIsNotNone(job_resource.system_data)
        self.assertTrue(re.match(self.job_resource_id_regex_pattern, job_resource.id))
        job_properties = job_resource.properties
        self.assertIsNone(job_properties.managed_component_references)
        self.assertEqual("Succeeded", job_properties.provisioning_state)
        self.assertEqual("BuildResult", job_properties.source.type)
        self.assertIsNone(job_properties.source.version)

    @SpringResourceGroupPreparer(dev_setting_name=SpringTestEnvironmentEnum.STANDARD['resource_group_name'],
                                 location="eastus")
    @SpringPreparer(**SpringTestEnvironmentEnum.ENTERPRISE_WITH_TANZU['spring'])
    @SpringJobNamePreparer()
    def test_deploy_job_2(self, resource_group, spring, job):
        self._prepare_kwargs_for_deploy_job(resource_group, spring, job)

        response_in_json = self.cmd(
            'spring job deploy -n {job} -g {rg} -s {serviceName} --source-path {filePath} '
            '--build-env {java17}')

    def _prepare_kwargs_for_deploy_job(self, resource_group, spring, job):
        # TODO(jiec): Use the param from the test method

        py_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(py_path, 'testing_project/hello_world').replace("\\", "/")
        self.kwargs.update({
            'job': 'mason-job-cli-record-test-2',
            'serviceName': 'jiec-e-df-eus-acs-gen1',
            'rg': 'jiec-rg-target',
            'filePath': file_path,
            'java17': 'BP_JVM_VERSION=17'
        })
