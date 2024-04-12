# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from re import match

from azext_spring._app_validator import (validate_cpu, validate_memory)
from azext_spring._util_enterprise import (get_client)
from azext_spring._validators_enterprise import (only_support_enterprise, validate_source_path, validate_artifact_path,
                                                 validate_build_env)
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.azclierror import (ValidationError)
from azure.cli.core.commands.validators import validate_tag


def validate_job_create(cmd, namespace):
    _validate_job_name(namespace.name)
    only_support_enterprise(cmd, namespace)
    _ensure_job_not_exist(cmd, namespace.resource_group, namespace.service, namespace.name)


def validate_job_update(cmd, namespace):
    _validate_job_name(namespace.name)
    _validate_envs(namespace)
    _validate_secret_envs(namespace)
    only_support_enterprise(cmd, namespace)


def validate_job_delete(cmd, namespace):
    _validate_job_name(namespace.name)
    only_support_enterprise(cmd, namespace)


def validate_job_get(cmd, namespace):
    _validate_job_name(namespace.name)
    only_support_enterprise(cmd, namespace)


def validate_job_list(cmd, namespace):
    only_support_enterprise(cmd, namespace)


def validate_job_deploy(cmd, namespace):
    _validate_job_name(namespace.name)
    _validate_envs(namespace)
    _validate_secret_envs(namespace)
    validate_source_path(namespace)
    validate_artifact_path(namespace)
    validate_build_env(cmd, namespace)
    only_support_enterprise(cmd, namespace)


def validate_job_start(cmd, namespace):
    _validate_job_name(namespace.name)
    _validate_envs(namespace)
    _validate_secret_envs(namespace)
    validate_cpu(namespace)
    validate_memory(namespace)
    only_support_enterprise(cmd, namespace)


def validate_job_execution_cancel(cmd, namespace):
    _validate_job_name(namespace.job)
    only_support_enterprise(cmd, namespace)


def validate_job_execution_get(cmd, namespace):
    _validate_job_name(namespace.job)
    only_support_enterprise(cmd, namespace)


def validate_job_execution_list(cmd, namespace):
    _validate_job_name(namespace.job)
    only_support_enterprise(cmd, namespace)


def _validate_job_name(job_name):
    matchObj = match(r'^[a-z][a-z0-9-]{2,30}[a-z0-9]$', job_name)
    if matchObj is None:
        raise InvalidArgumentValueError(
            '--name should start with lowercase and only contain numbers and lowercases with length [4,31]')


def _validate_envs(namespace):
    """ Extracts multiple space-separated properties in key[=value] format """
    if isinstance(namespace.envs, list):
        properties_dict = {}
        for item in namespace.envs:
            properties_dict.update(validate_tag(item))
        namespace.envs = properties_dict


def _validate_secret_envs(namespace):
    """ Extracts multiple space-separated secrets in key[=value] format """
    if isinstance(namespace.secret_envs, list):
        secrets_dict = {}
        for item in namespace.secret_envs:
            secrets_dict.update(validate_tag(item))
        namespace.secret_envs = secrets_dict


def _ensure_job_not_exist(cmd, resource_group, service, job_name):
    job = None
    client = get_client(cmd)
    try:
        job = client.job.get(resource_group, service, job_name)
    except Exception:
        # ignore
        return
    if job:
        raise ValidationError('Job {} already exist, cannot create.'.format(job.id))
