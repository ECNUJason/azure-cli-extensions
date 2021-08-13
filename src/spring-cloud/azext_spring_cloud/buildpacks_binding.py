# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=wrong-import-order
from ._enterprise import DEFAULT_BUILD_SERVICE_NAME
from .vendored_sdks.appplatform.v2022_05_01_preview import models
from knack.util import CLIError


def buildpacks_binding_create(cmd, client, resource_group, service,
                              name, type, properties=None, secrets=None):
    return _create_or_update_buildpacks_binding(client, resource_group, service, name,
                                                type, properties, secrets)


def buildpacks_binding_set(cmd, client, resource_group, service,
                           name, type, properties=None, secrets=None):
    return _create_or_update_buildpacks_binding(client, resource_group, service, name,
                                                type, properties, secrets)


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


def _create_or_update_buildpacks_binding(client, resource_group, service, name, type, properties, secrets):
    binding_resource = _build_buildpacks_binding_resource(type, properties, secrets)
    return client.buildpacks_binding.create_or_update(resource_group,
                                                      service,
                                                      DEFAULT_BUILD_SERVICE_NAME,
                                                      name,
                                                      binding_resource)


def _get_buildpacks_binding(client, resource_group, service, binding_name):
    return client.buildpacks_binding.get(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, binding_name)


def _delete_buildpacks_binding(client, resource_group, service, binding_name):
    client.buildpacks_binding.delete(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, binding_name)

