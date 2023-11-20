# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import (ScenarioTest, record_only, live_only)
from azure.cli.testsdk.base import ExecutionResult
from ....managed_components.managed_component import get_component


try:
    import unittest.mock as mock
except ImportError:
    from unittest import mock


class TestingWriter:
    def __init__(self, buffer):
        self.buffer = buffer

    def write(self, data, end='', file=None):
        self.buffer.append(data)


@record_only()
class ManagedComponentTest(ScenarioTest):
    def test_component_list(self):
        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
        })

        result: ExecutionResult = self.cmd('spring component list -s {serviceName} -g {rg}')
        self.assertTrue(isinstance(result.get_output_in_json(), list))
        component_list: list = result.get_output_in_json()

        for e in component_list:
            self.assertTrue(isinstance(e, dict))
            e: dict = e
            self.assertTrue("name" in e)
            component_obj = get_component(e["name"])
            self.assertIsNotNone(component_obj)

    def test_acs_component_instance_list(self):
        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'application-configuration-service'
        })

        # ACS (Gen1 or Gen2) is enabled in service instance.
        result: ExecutionResult = self.cmd('spring component instance list -s {serviceName} -g {rg} -c {component}')
        output = result.get_output_in_json()
        self.assertTrue(type(output), list)
        for e in output:
            self.assertTrue(isinstance(e, dict))
            self.assertTrue("name" in e)
            instance: str = e["name"]
            self.assertTrue(instance.startswith("application-configuration-service"))

    def test_flux_component_instance_list(self):
        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'flux-source-controller',
        })

        # flux is a subcomponent of ACS Gen2, make sure it's enabled in service instance.
        result: ExecutionResult = self.cmd('spring component instance list -s {serviceName} -g {rg} -c {component}')
        output = result.get_output_in_json()
        self.assertTrue(type(output), list)
        for e in output:
            self.assertTrue(isinstance(e, dict))
            self.assertTrue("name" in e)
            instance: str = e["name"]
            self.assertTrue(instance.startswith("fluxcd-source-controller"))

    def test_scg_component_instance_list(self):
        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'spring-cloud-gateway',
        })

        # scg is a subcomponent of Spring Cloud Gateway, need to enable it first.
        result: ExecutionResult = self.cmd('spring component instance list -s {serviceName} -g {rg} -c {component}')
        output = result.get_output_in_json()
        self.assertTrue(type(output), list)
        for e in output:
            self.assertTrue(isinstance(e, dict))
            self.assertTrue("name" in e)
            instance: str = e["name"]
            self.assertTrue(instance.startswith("asc-scg-default"))

    def test_scg_operator_component_instance_list(self):
        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'spring-cloud-gateway-operator'
        })

        # scg operator is a subcomponent of Spring Cloud Gateway, need to enable it first.
        result: ExecutionResult = self.cmd('spring component instance list -s {serviceName} -g {rg} -c {component}')
        output = result.get_output_in_json()
        self.assertTrue(type(output), list)
        for e in output:
            self.assertTrue(isinstance(e, dict))
            self.assertTrue("name" in e)
            instance: str = e["name"]
            self.assertTrue(instance.startswith("scg-operator"))

    @mock.patch('azext_spring.managed_components.managed_component_operations._get_default_writer', autospec=True)
    @mock.patch('azext_spring.managed_components.managed_component_operations._get_prefix_writer', autospec=True)
    def test_acs_log_stream(self, _get_default_writer_mock, _get_prefix_writer_mock):
        command_std_out = []
        _get_default_writer_mock.return_value = TestingWriter(command_std_out)
        _get_prefix_writer_mock.return_value = TestingWriter(command_std_out)

        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'application-configuration-service'
        })

        self.cmd('spring component logs -s {serviceName} -g {rg} -n {component} --all-instances --lines 50')
        self.assertTrue(len(command_std_out) > 10)

    @mock.patch('azext_spring.managed_components.managed_component_operations._get_default_writer', autospec=True)
    @mock.patch('azext_spring.managed_components.managed_component_operations._get_prefix_writer', autospec=True)
    def test_flux_log_stream(self, _get_default_writer_mock, _get_prefix_writer_mock):
        command_std_out = []
        _get_default_writer_mock.return_value = TestingWriter(command_std_out)
        _get_prefix_writer_mock.return_value = TestingWriter(command_std_out)

        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'flux-source-controller'
        })

        self.cmd('spring component logs -s {serviceName} -g {rg} -n {component} --all-instances --lines 50')
        self.assertTrue(len(command_std_out) > 10)

    @mock.patch('azext_spring.managed_components.managed_component_operations._get_default_writer', autospec=True)
    @mock.patch('azext_spring.managed_components.managed_component_operations._get_prefix_writer', autospec=True)
    def test_scg_log_stream(self, _get_default_writer_mock, _get_prefix_writer_mock):
        command_std_out = []
        _get_default_writer_mock.return_value = TestingWriter(command_std_out)
        _get_prefix_writer_mock.return_value = TestingWriter(command_std_out)

        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'spring-cloud-gateway'
        })

        self.cmd('spring component logs -s {serviceName} -g {rg} -n {component} --all-instances --lines 50')
        self.assertTrue(len(command_std_out) > 10)

    @mock.patch('azext_spring.managed_components.managed_component_operations._get_default_writer', autospec=True)
    @mock.patch('azext_spring.managed_components.managed_component_operations._get_prefix_writer', autospec=True)
    def test_scg_operator_log_stream(self, _get_default_writer_mock, _get_prefix_writer_mock):
        command_std_out = []
        _get_default_writer_mock.return_value = TestingWriter(command_std_out)
        _get_prefix_writer_mock.return_value = TestingWriter(command_std_out)

        self.kwargs.update({
            'serviceName': 'jiec-e-eastasia',
            'rg': 'jiec-rg',
            'component': 'spring-cloud-gateway-operator'
        })

        self.cmd('spring component logs -s {serviceName} -g {rg} -n {component} --all-instances --lines 50')
        self.assertTrue(len(command_std_out) > 10)
