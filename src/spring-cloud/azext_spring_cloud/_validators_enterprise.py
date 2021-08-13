# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, unused-argument, redefined-builtin

from re import match
from azure.cli.core.util import CLIError
from azure.cli.core.commands.validators import validate_tag
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.core.exceptions import ResourceNotFoundError
from knack.log import get_logger
from ._enterprise import DEFAULT_BUILD_SERVICE_NAME
from ._resource_quantity import (
    validate_cpu as validate_and_normalize_cpu, 
    validate_memory as validate_and_normalize_memory)
from ._util_enterprise import (
    is_enterprise_tier
)
from .vendored_sdks.appplatform.v2022_05_01_preview import (
    AppPlatformManagementClient as AppPlatformManagementClient_20220501preview
)


"""
Define the binding name of buildpacks. The binding name have some restrictions from kpack as below.

At most 63 chars.
Have one fixed prefix binding-metadata- 17 char, only 46 chars left.
Must consist of alphabetic characters or '-', and must start and end with an alphabetic character

We need encode build_service_name, buildpacks_binding_name and type.
We need 2 '-' for separator, 44 chars left.
We need 2 int value for type, 42 chars left.
We need 2 prefix number for encoding prefix for build_service_name and buildpacks_binding_name, 38 char left.

So there are at most 38 chars for build_service_name and buildpacks_binding_name in total.
We leave 19 character each for build_service_name and buildpacks_binding_name
"""
BUILDPACKS_BINDING_NAME_REGEX_PATTTERN=r"(^[a-zA-Z]$|^[a-zA-Z][-a-zA-Z0-9]{0,17}[a-zA-Z]$)"

logger = get_logger(__name__)

def only_support_enterprise(cmd, namespace):
    if namespace.resource_group and namespace.service and not is_enterprise_tier(cmd, namespace.resource_group, namespace.service):
        raise CLIError("'{}' only supports for Enterprise tier Spring instance.".format(namespace.command))


def not_support_enterprise(cmd, namespace):
    if namespace.resource_group and namespace.service and is_enterprise_tier(cmd, namespace.resource_group, namespace.service):
        raise CLIError("'{}' doesn't support for Enterprise tier Spring instance.".format(namespace.command))


def validate_cpu(namespace):
    namespace.cpu = validate_and_normalize_cpu(namespace.cpu)


def validate_memory(namespace):
    namespace.memory = validate_and_normalize_memory(namespace.memory)


def validate_git_uri(namespace):
    uri = namespace.uri
    if uri and (uri.startswith("https://") or uri.startswith("git@")):
        return
    raise CLIError("Git URI should start with \"https://\" or \"git@\"")


def validate_config_file_patterns(namespace):
    if namespace.config_file_patterns:
        _validate_patterns(namespace.config_file_patterns)


def validate_acs_patterns(namespace):
    _validate_patterns(namespace.patterns)


def _validate_patterns(patterns):
    pattern_list = patterns.split(',')
    invalid_list = [p for p in pattern_list if not _is_valid_pattern(p)]
    if len(invalid_list) > 0:
        logger.warning("Patterns '%s' are invalid.", ','.join(invalid_list))
        raise CLIError("Patterns should be the collection of patterns separated by comma, each pattern in the format of 'application' or 'application/profile'")


def _is_valid_pattern(pattern):
    return _is_valid_app_name(pattern) or _is_valid_app_and_profile_name(pattern)


def _is_valid_app_name(pattern):
    return match(r"^[a-zA-Z][-_a-zA-Z0-9]*$", pattern) is not None


def _is_valid_profile_name(profile):
    return profile == "*" or _is_valid_app_name(profile)


def _is_valid_app_and_profile_name(pattern):
    parts = pattern.split('/')
    return len(parts) == 2 and _is_valid_app_name(parts[0]) and _is_valid_profile_name(parts[1])


def validate_buildpacks_binding_name(namespace):
    if not _is_valid_buildpacks_binding_name_pattern(namespace.name):
        raise CLIError("Buildpacks Binding name should follow pattern {}"
                       .format(BUILDPACKS_BINDING_NAME_REGEX_PATTTERN))


def _is_valid_buildpacks_binding_name_pattern(name):
    return match(BUILDPACKS_BINDING_NAME_REGEX_PATTTERN, name) is not None


def validate_buildpacks_binding_properties(namespace):
    """ Extracts multiple space-separated properties in key[=value] format """
    if isinstance(namespace.properties, list):
        properties_dict = {}
        for item in namespace.properties:
            properties_dict.update(validate_tag(item))
        namespace.properties = properties_dict


def validate_buildpacks_binding_secrets(namespace):
    """ Extracts multiple space-separated secrets in key[=value] format """
    if isinstance(namespace.secrets, list):
        secrets_dict = {}
        for item in namespace.secrets:
            secrets_dict.update(validate_tag(item))
        namespace.secrets = secrets_dict


def enterprise_only_and_binding_not_exist(cmd, namespace):
    only_support_enterprise(cmd, namespace)
    client = get_mgmt_service_client(cmd.cli_ctx, AppPlatformManagementClient_20220501preview)
    _validate_binding_not_exists(client,
                                 namespace.resource_group,
                                 namespace.service,
                                 namespace.name)


def enterprise_only_and_binding_exist(cmd, namespace):
    only_support_enterprise(cmd, namespace)
    client = get_mgmt_service_client(cmd.cli_ctx, AppPlatformManagementClient_20220501preview)
    _validate_binding_exists(client,
                             namespace.resource_group,
                             namespace.service,
                             namespace.name)


def _validate_binding_not_exists(client, resource_group, service, binding_name):
    try:
        binding_resource = client.buildpacks_binding.get(resource_group,
                                                         service,
                                                         DEFAULT_BUILD_SERVICE_NAME,
                                                         binding_name)
        if binding_resource is not None:
            raise CLIError('Buildpacks Binding {} already exists '
                           'in resource group {}, service {}. You can edit it by set command.'
                           .format(binding_name, resource_group, service))
    except ResourceNotFoundError as e:
        # Excepted case
        pass


def _validate_binding_exists(client, resource_group, service, binding_name):
    try:
        client.buildpacks_binding.get(resource_group, service, DEFAULT_BUILD_SERVICE_NAME, binding_name)
    except ResourceNotFoundError as e:
        raise CLIError('Buildpacks Binding {} does not exist '
                       'in resource group {}, service {}. Please create before set.'
                       .format(binding_name, resource_group, service))
