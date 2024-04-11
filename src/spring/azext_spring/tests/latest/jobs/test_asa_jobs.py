# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest

from azext_spring.jobs.job import (job_create, _update_args, _update_envs, _update_job_properties, _update_secrets,
                                   _is_job_execution_in_final_state)
from azext_spring.vendored_sdks.appplatform.v2024_05_01_preview.models import (EnvVar, JobExecutionTemplate,
                                                                               JobResourceProperties,
                                                                               Secret)

from .test_asa_job_utils import SAMPLE_JOB_RESOURCE
from ..common.test_utils import get_test_cmd

try:
    import unittest.mock as mock
except ImportError:
    from unittest import mock


class TestAsaJobs(unittest.TestCase):

    def setUp(self) -> None:
        self.envs_dict = {
            "prop1": "value1",
            "prop2": "value2"
        }
        self.secrets_dict = {
            "secret1": "secret_value1",
            "secret2": "secret_value2"
        }
        self.args_str = "random-args sleep 2"

    def test_create_env_list(self):

        env_list = _update_envs(None, self.envs_dict, self.secrets_dict)

        self.assertEquals(4, len(env_list))
        for env in env_list:
            self.assertTrue(isinstance(env, EnvVar))

        self._verify_env_var(env_list[0], "prop1", "value1", None)
        self._verify_env_var(env_list[1], "prop2", "value2", None)
        self._verify_env_var(env_list[2], "secret1", None, "secret_value1")
        self._verify_env_var(env_list[3], "secret2", None, "secret_value2")

    def test_update_env_props_only(self):
        existed_env_list = [
            EnvVar(name="prop1", value="value1"),
            EnvVar(name="prop2", value="value1"),
            EnvVar(name="prop3", value=""),  # This is the case when only key is set
            EnvVar(name="secret1", secret_value="secret_value1"),
            EnvVar(name="secret2", secret_value="secret_value2"),
            EnvVar(name="secret3", secret_value=None),  # Backend won't response value of secret
        ]

        envs_dict = {
            "prop4": "value4"
        }

        secrets_dict = None

        env_list = _update_envs(existed_env_list, envs_dict, secrets_dict)

        self.assertEquals(4, len(env_list))
        for env in env_list:
            self.assertIsNotNone(env)
            self.assertTrue(isinstance(env, EnvVar))

        self._verify_env_var(env_list[0], "prop4", "value4", None)
        self._verify_env_var(env_list[1], "secret1", None, "secret_value1")
        self._verify_env_var(env_list[2], "secret2", None, "secret_value2")
        self._verify_env_var(env_list[3], "secret3", None, None)

    def test_update_env_secrets_only(self):
        existed_env_list = [
            EnvVar(name="prop1", value="value1"),
            EnvVar(name="prop2", value="value2"),
            EnvVar(name="secret1", secret_value="secret_value1"),
            EnvVar(name="secret2", secret_value="secret_value2"),
        ]

        secrets_dict = {
            "secret3": "secret_value3"
        }

        env_list = _update_envs(existed_env_list, None, secrets_dict)

        self.assertEquals(3, len(env_list))
        for env in env_list:
            self.assertIsNotNone(env)
            self.assertTrue(isinstance(env, EnvVar))

        self._verify_env_var(env_list[0], "prop1", "value1", None)
        self._verify_env_var(env_list[1], "prop2", "value2", None)
        self._verify_env_var(env_list[2], "secret3", None, "secret_value3")

    def test_update_secrets(self):
        existed_env_list = [
            EnvVar(name="prop1", value="value1"),
            EnvVar(name="prop2", value="value2"),
            EnvVar(name="secret1", secret_value="secret_value1"),
            EnvVar(name="secret2", secret_value="secret_value2"),
        ]

        secrets = [
            Secret(name="secret3", value="secret_value3")
        ]

        env_list = _update_secrets(existed_env_list, secrets)
        self._verify_env_var(env_list[0], "prop1", "value1", None)
        self._verify_env_var(env_list[1], "prop2", "value2", None)
        self._verify_env_var(env_list[2], "secret3", None, "secret_value3")

    def test_create_args(self):
        args = self.args_str
        target_args = _update_args(None, args)
        self.assertEquals(["random-args", "sleep", "2"], target_args)

    def test_update_args(self):
        args = self.args_str
        target_args = _update_args(["current-args"], args)
        self.assertEquals(["random-args", "sleep", "2"], target_args)

    def test_create_job_properties(self):
        existed_properties = None
        envs = self.envs_dict
        secret_envs = self.secrets_dict
        args = self.args_str
        target_properties = _update_job_properties(existed_properties, envs, secret_envs, args)

        self._verify_env_var(target_properties.template.environment_variables[0], "prop1", "value1", None)
        self._verify_env_var(target_properties.template.environment_variables[1], "prop2", "value2", None)
        self._verify_env_var(target_properties.template.environment_variables[2], "secret1", None, "secret_value1")
        self._verify_env_var(target_properties.template.environment_variables[3], "secret2", None, "secret_value2")
        self.assertEquals(["random-args", "sleep", "2"], target_properties.template.args)

    def test_update_job_properties(self):
        existed_properties = JobResourceProperties(
            template=JobExecutionTemplate(
                environment_variables=[
                    EnvVar(name="prop1", value="value1"),
                    EnvVar(name="secret1", secret_value="secret_value1"),
                ],
                args=["arg1", "arg2"]
            )
        )
        envs = self.envs_dict
        secret_envs = None
        args = self.args_str
        target_properties = _update_job_properties(existed_properties, envs, secret_envs, args)
        self.assertEquals(3, len(target_properties.template.environment_variables))
        self._verify_env_var(target_properties.template.environment_variables[0], "prop1", "value1", None)
        self._verify_env_var(target_properties.template.environment_variables[1], "prop2", "value2", None)
        self._verify_env_var(target_properties.template.environment_variables[2], "secret1", None, "secret_value1")
        self.assertEquals(["random-args", "sleep", "2"], target_properties.template.args)

    def test_is_job_execution_in_final_state(self):
        for status in ("Running", "Pending"):
            self.assertFalse(_is_job_execution_in_final_state(status))

        for status in ("Canceled", "Failed", "Completed"):
            self.assertTrue(_is_job_execution_in_final_state(status))

    @mock.patch('azext_spring.jobs.job.wait_till_end', autospec=True)
    def test_create_asa_job(self, wait_till_end_mock):
        wait_till_end_mock.return_value = None

        client_mock = mock.MagicMock()
        client_mock.job.begin_create_or_update.return_value = None

        client_mock.job.get = lambda resource_group, service, job_name: SAMPLE_JOB_RESOURCE

        job_create(get_test_cmd(), client_mock, "myResourceGroup", "myservice", "test-job")

    def _verify_env_var(self, env: EnvVar, name, value, secret_value):
        self.assertIsNotNone(env)
        self.assertEquals(name, env.name)
        if value is not None:
            self.assertEquals(value, env.value)
            self.assertIsNone(env.secret_value)
        elif secret_value is not None:
            self.assertIsNone(env.value)
            self.assertEquals(secret_value, env.secret_value)
