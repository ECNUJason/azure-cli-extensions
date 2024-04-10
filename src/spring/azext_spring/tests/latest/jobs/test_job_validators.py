# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import unittest
from argparse import Namespace

from azext_spring.jobs.job_validators import (validate_job_delete, _validate_job_name, _validate_envs,
                                              _ensure_job_not_exist,
                                              validate_job_get, _validate_secret_envs,
                                              validate_job_create, validate_job_update, validate_job_start,
                                              validate_job_execution_cancel, validate_job_execution_get,
                                              validate_job_execution_list)
from azext_spring.vendored_sdks.appplatform.v2024_05_01_preview import models
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.azclierror import (ValidationError)

from ..common.test_utils import get_test_cmd

try:
    import unittest.mock as mock
except ImportError:
    from unittest import mock


class TestJobValidators(unittest.TestCase):
    empty_string = ''

    def test_validate_job_name(self):
        valid_job_names = [
            "job1",
            "job2",
            "job-hh",
            "job-1234567890-1234567890"
        ]

        for name in valid_job_names:
            _validate_job_name(name)

        invalid_job_names = [
            "j",
            "09jb",
            "JOBS",
            "asdflkjhkljlkajsdfhajksdfaklsdjfasdkjf",
            "asdf asdf",
            "asdf,asdf,asdf,asdf.dfef"
        ]

        for name in invalid_job_names:
            with self.assertRaises(InvalidArgumentValueError):
                _validate_job_name(name)

    def test_validate_envs(self):
        envs_input = ["a", "b=v_b", "c=v_c"]
        ns = Namespace(envs=envs_input)
        _validate_envs(ns)

        self.assertTrue(isinstance(ns.envs, dict))
        self.assertEqual(self.empty_string, ns.envs['a'])
        self.assertEqual("v_b", ns.envs['b'])
        self.assertEqual("v_c", ns.envs['c'])
        self.assertEqual(3, len(ns.envs.keys()))

    def test_validate_secret_envs(self):
        secret_envs = ["a", "b=v_b", "c=v_c"]
        ns = Namespace(secret_envs=secret_envs)
        _validate_secret_envs(ns)

        self.assertTrue(isinstance(ns.secret_envs, dict))
        self.assertEqual(self.empty_string, ns.secret_envs['a'])
        self.assertEqual("v_b", ns.secret_envs['b'])
        self.assertEqual("v_c", ns.secret_envs['c'])
        self.assertEqual(3, len(ns.secret_envs.keys()))

    @mock.patch('azext_spring.jobs.job_validators.get_client', autospec=True)
    def test_ensure_job_not_exist_raise_exception(self, get_client_mock):
        client = mock.MagicMock()
        client.job.get.return_value = self._get_mocked_job_resource()

        get_client_mock.return_value = client

        with self.assertRaises(ValidationError):
            _ensure_job_not_exist(get_test_cmd(), "fake-rg", "fake-service-name", "fake-job-name")

    @mock.patch('azext_spring.jobs.job_validators.get_client', autospec=True)
    def test_ensure_job_not_exist_pass(self, get_client_mock):
        client = mock.MagicMock()
        client.job.get.return_value = self._get_none_job_resource()

        get_client_mock.return_value = client

        _ensure_job_not_exist(get_test_cmd(), "fake-rg", "fake-service-name", "fake-job-name")

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    @mock.patch('azext_spring.jobs.job_validators.get_client', autospec=True)
    def test_validate_job_create(self, get_client_mock, only_support_enterprise_mock):
        self._prepare_client_mock_return_none_job_resource(get_client_mock)
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            name="fake-job-name"
        )

        validate_job_create(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_update(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            name="fake-job-name",
            envs=["a=v_a", "b=v_b"],
            secret_envs=["c=v_c", "d=v_d"],
        )

        validate_job_update(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_delete(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            name="fake-job-name",
            envs=["a=v_a", "b=v_b"],
            secret_envs=["c=v_c", "d=v_d"],
        )

        validate_job_delete(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_get(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            name="fake-job-name",
            envs=["a=v_a", "b=v_b"],
            secret_envs=["c=v_c", "d=v_d"],
        )

        validate_job_get(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_start(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            name="fake-job-name",
            envs=["a=v_a", "b=v_b"],
            secret_envs=["c=v_c", "d=v_d"],
            cpu='500m',
            memory='512Mi'
        )

        validate_job_start(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_execution_cancel(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            job="fake-job-name",
            name="fake-execution-name"
        )

        validate_job_execution_cancel(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_execution_get(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            job="fake-job-name",
            name="fake-execution-name"
        )

        validate_job_execution_get(get_test_cmd(), ns)

    @mock.patch('azext_spring.jobs.job_validators.only_support_enterprise', autospec=True)
    def test_validate_job_execution_list(self, only_support_enterprise_mock):
        self._prepare_is_enterprise_mock(only_support_enterprise_mock)

        ns = Namespace(
            resource_group="fake-rg",
            service="fake-service",
            job="fake-job-name"
        )

        validate_job_execution_list(get_test_cmd(), ns)

    def _get_mocked_job_resource(self):
        return models.JobResource()

    def _get_none_job_resource(self):
        return None

    def _prepare_client_mock_return_none_job_resource(self, get_client_mock):
        client = mock.MagicMock()
        client.job.get.return_value = self._get_none_job_resource()
        get_client_mock.return_value = client

    def _prepare_is_enterprise_mock(self, only_support_enterprise_mock):
        only_support_enterprise_mock.return_value = True
