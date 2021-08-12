# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, unused-argument, redefined-builtin

from re import match
import shlex
from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import InvalidArgumentValueError
from knack.log import get_logger
from ._resource_quantity import (
    validate_cpu as validate_and_normalize_cpu, 
    validate_memory as validate_and_normalize_memory)
from ._util_enterprise import (
    is_enterprise_tier
)

BUILDPACKS_BINDING_NAME_REGEX_PATTTERN=r"(^[a-zA-Z]$|^[a-zA-Z][-a-zA-Z0-9]*[a-zA-Z0-9]$)"
BUILDPACKS_BINDING_NAME_MAX_LENGTH=19

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


def validate_config_file_patterns(namespace):
    if not namespace.config_file_patterns:
        return
    pattern_list = namespace.config_file_patterns.split(',')
    invalid_list = [p for p in pattern_list if not _is_valid_pattern(p)]
    if invalid_list:
        logger.warning('Config file patterns "%s" are invalid.', ','.join(invalid_list))
        raise CLIError('--config-file-patterns should be the collection of patterns separated by comma, each pattern in the format of \'application\' or \'application/profile\'')


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
        raise InvalidArgumentValueError("Buildpacks Binding name should follow pattern {}".format(
            BUILDPACKS_BINDING_NAME_REGEX_PATTTERN))
    if not _is_valid_buildpacks_binding_name_length(namespace.name):
        raise InvalidArgumentValueError("Buildpacks Binding name character number should not exceed {}".format(
            BUILDPACKS_BINDING_NAME_MAX_LENGTH))


def _is_valid_buildpacks_binding_name_pattern(name):
    return match(BUILDPACKS_BINDING_NAME_REGEX_PATTTERN, name) is not None


def _is_valid_buildpacks_binding_name_length(name):
    return len(name) <= BUILDPACKS_BINDING_NAME_MAX_LENGTH


def validate_buildpacks_binding_properties(namespace):
    if namespace.properties is not None:
        if not _is_valid_pair_list(namespace.properties):
            raise InvalidArgumentValueError(
                'Invalid pair "{}", each pair of Buildpacks Binding properties should follow ' \
                'format key=value or key="value also include = symbol"' \
                .format(namespace.secrets))


def validate_buildpacks_binding_secrets(namespace):
    if namespace.secrets is not None:
        if not _is_valid_pair_list(namespace.secrets):
            raise InvalidArgumentValueError(
                'Invalid pair "{}", each pair of Buildpacks Binding secrets should follow ' \
                'format key=value or key="value also include = symbol"' \
                .format(namespace.secrets))


def _is_valid_pair_list(pair_list):
    keys = set()
    try:
        for token in shlex.split(pair_list):
            key, value = token.split('=', 1)
            if len(key) == 0 or len(value) == 0:
                raise InvalidArgumentValueError('Buildpacks Binding key or value should not be blank for pair "{}"' \
                                                .format(token))
            if key in keys:
                raise InvalidArgumentValueError('Buildpacks Binding duplicated key "{}" found'.format(key))
            keys.add(key)
    except ValueError:
        return False
    return True
