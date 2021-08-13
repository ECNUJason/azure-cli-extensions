# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._enterprise import DEFAULT_BUILD_SERVICE_NAME
from .vendored_sdks.appplatform.v2022_05_01_preview import models
from azure.core.exceptions import ResourceNotFoundError
from knack.util import CLIError


def buildpacks_binding_create(cmd, client, resource_group, service,
                              name, type, properties=None, secrets=None):
    _assert_binding_not_exists(client, resource_group, service, name)
    binding_resource = _build_buildpacks_binding_resource(type, properties, secrets)
    return _create_or_update_buildpacks_binding(client, resource_group, service, name, binding_resource)


def buildpacks_binding_set(cmd, client, resource_group, service,
                           name, type, properties=None, secrets=None):
    _assert_binding_exists(client, resource_group, service, name)
    binding_resource = _build_buildpacks_binding_resource(type, properties, secrets)
    return _create_or_update_buildpacks_binding(client, resource_group, service, name, binding_resource)


def buildpacks_binding_show(cmd, client, resource_group, service, name):
    return _get_buildpacks_binding(client, resource_group, service, name)

def buildpacks_binding_delete(cmd, client, resource_group, service, name):
    return _delete_buildpacks_binding(client, resource_group, service, name)


def _build_buildpacks_binding_resource(binding_type, properties_dict, secrets_dict):
    launch_properties = models.BuildpacksBindingLaunchProperties(properties=properties_dict,
                                                                 secrets=secrets_dict)
    binding_properties = models.BuildpacksBindingProperties(binding_type=binding_type,
                                                            launch_properties=launch_properties)
    return models.BuildpacksBindingResource(properties=binding_properties)


def _create_or_update_buildpacks_binding(client, resource_group, service, name, binding_resource):
    return client.buildpacks_binding.create_or_update(resource_group,
                                                      service,
                                                      DEFAULT_BUILD_SERVICE_NAME,
                                                      name,
                                                      binding_resource)


def _get_buildpacks_binding(client, resource_group, service, binding_name):
    return client.buildpacks_binding.get(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, binding_name)


def _delete_buildpacks_binding(client, resource_group, service, binding_name):
    client.buildpacks_binding.delete(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, binding_name)


def _assert_binding_not_exists(client, resource_group, service, binding_name):
    try:
        binding_resource = _get_buildpacks_binding(client, resource_group, service, binding_name)
        if binding_resource is not None:
            raise CLIError('Buildpacks Binding {} already exists '
                           'in resource group {}, service {}. You can edit it by set command.'
                           .format(binding_name, resource_group, service))
    except ResourceNotFoundError as e:
        # Excepted case
        pass


def _assert_binding_exists(client, resource_group, service, binding_name):
    try:
        _get_buildpacks_binding(client, resource_group, service, binding_name)
    except ResourceNotFoundError as e:
        raise CLIError('Buildpacks Binding {} does not exist '
                       'in resource group {}, service {}. Please create before set.'
                       .format(binding_name, resource_group, service))
