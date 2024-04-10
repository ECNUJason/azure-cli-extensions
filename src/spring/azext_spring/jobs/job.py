# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shlex
import time
from json import JSONEncoder

from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger

from .job_deployable_factory import deployable_selector
from .._utils import wait_till_end
from ..vendored_sdks.appplatform.v2024_05_01_preview import models

logger = get_logger(__name__)

LOG_RUNNING_PROMPT = "This command usually takes minutes to run. Add '--verbose' parameter if needed."
DEFAULT_BUILD_RESULT_ID = "<default>"


#  Job's command usually operates an Spring/Job and the Spring/Job/Execution under the job.
# The general idea of these command is putting all input command in parameter dict and let the Resource factory to construct the payload.
# - A job must consume a path can be deployable, it can be custom container or build result resource id,
# - _job_deployable_factory determines the deployable type and upload necessary binary/code to the service when constructing the deployable_path.

def job_create(cmd, client, resource_group, service, name):
    job_resource = models.JobResource(
        properties=models.JobResourceProperties(
            trigger_config=models.ManualJobTriggerConfig(),
            source=models.BuildResultUserSourceInfo(
                build_result_id=DEFAULT_BUILD_RESULT_ID,
            )
        )
    )

    logger.warning(f"Start to create job '{name}'..")
    poller = client.job.begin_create_or_update(resource_group, service, name, job_resource)
    wait_till_end(cmd, poller)
    logger.warning(f"Job '{name}' is created successfully.")
    return job_get(cmd, client, resource_group, service, name)


def job_update(cmd, client, resource_group, service, name,
               envs=None,
               secret_envs=None,
               args=None):
    '''job_update
    Update job with configuration
    TODO(jiec): Need to test the env and secret_env after backend is fixed.
    '''
    job_resource = client.job.get(resource_group, service, name)
    existing_secret_collection = client.job.list_env_secrets(resource_group, service, name)
    if existing_secret_collection is not None and existing_secret_collection.value is not None:
        target_env_list = _update_secrets(job_resource.properties.template.environment_variables,
                                          existing_secret_collection.value)
        job_resource.properties.template.environment_variables = target_env_list
    job_resource.properties = _update_job_properties(job_resource.properties, envs, secret_envs, args)

    logger.warning(f"Start to update job '{name}'..")
    poller = client.job.begin_create_or_update(resource_group, service, name, job_resource)
    wait_till_end(cmd, poller)
    logger.warning(f"Job '{name}' is updated successfully.")
    return job_get(cmd, client, resource_group, service, name)


def job_delete(cmd, client, resource_group, service, name):
    client.job.get(resource_group, service, name)
    return client.job.begin_delete(resource_group, service, name)


def job_get(cmd, client, resource_group, service, name):
    return client.job.get(resource_group, service, name)


def job_list(cmd, client, resource_group, service):
    return client.jobs.list(resource_group, service)


def job_deploy(cmd, client, resource_group, service, name,
               # job.source
               build_env=None,
               builder=None,
               build_cpu=None,
               build_memory=None,
               source_path=None,
               artifact_path=None,
               version=None,
               envs=None,
               secret_envs=None,
               args=None,
               # only used in validator
               disable_validation=None,
               no_wait=False):
    logger.warning(LOG_RUNNING_PROMPT)

    job_resource = client.job.get(resource_group, service, name)
    existing_secrets = client.job.list_env_secrets(resource_group, service, name)
    if existing_secrets is not None:
        job_resource.properties.template.environment_variables.secrets = existing_secrets
    job_resource.properties = _update_job_properties(job_resource.properties, envs, secret_envs, args)

    kwargs = {
        'cmd': cmd,
        'client': client,
        'resource_group': resource_group,
        'service': service,
        'job': name,
        'source_path': source_path,
        'artifact_path': artifact_path,
        'build_env': build_env,
        'build_cpu': build_cpu,
        'build_memory': build_memory,
        'builder': builder,
        'no_wait': no_wait
    }

    deployable = deployable_selector(**kwargs)
    kwargs['source_type'] = deployable.get_source_type(**kwargs)
    kwargs['total_steps'] = deployable.get_total_deploy_steps(**kwargs)
    deployable_path = deployable.build_deployable_path(**kwargs)

    job_resource.properties = _update_source(job_resource.properties, deployable_path, version)

    poller = sdk_no_wait(no_wait, client.job.begin_create_or_update,
                         resource_group, service, name, job_resource)
    if "succeeded" != poller.status().lower():
        return poller
    return client.job.get(resource_group, service, name)


def job_start(cmd, client, resource_group, service, name,
              envs=None,
              secret_envs=None,
              cpu=None,
              memory=None,
              args=None,
              wait_until_finished=False):
    job_execution_template = models.JobExecutionTemplate(
        environment_variables=_update_envs(None, envs, secret_envs),
        args=_convert_args(args),
        resource_requests=_update_resource_requests(None, cpu, memory))

    if wait_until_finished is False:
        return client.job.begin_start(resource_group, service, name, job_execution_template)
    else:
        poller = sdk_no_wait(False, client.job.begin_start,
                             resource_group, service, name, job_execution_template)
        execution_name = poller.result().name
        return _poll_until_job_end(client, resource_group, service, name, execution_name)


def job_execution_cancel(cmd, client,
                         resource_group,
                         service,
                         job,
                         execution,
                         no_wait=False):
    return sdk_no_wait(no_wait, client.job_execution.begin_cancel,
                       resource_group, service, job, execution)


def job_execution_get(cmd, client, resource_group, service, job, execution):
    return client.job_execution.get(resource_group, service, job, execution)


def job_execution_list(cmd, client, resource_group, service, job):
    return client.job_executions.list(resource_group, service, job)


def _update_job_properties(properties: models.JobResourceProperties, envs: dict, secret_envs: dict, args: str):
    if envs is None and secret_envs is None and args is None:
        return properties
    if properties is None:
        properties = models.JobResourceProperties()
    properties.template = _update_job_properties_template(properties.template, envs, secret_envs, args)
    return properties


def _update_source(properties, deployable_path, version):
    if properties is None:
        properties = models.JobResourceProperties()
    properties.source = models.BuildResultUserSourceInfo(
        build_result_id=deployable_path,
        version=version
    )
    return properties


def _update_job_properties_template(template, envs, secret_envs, args):
    if (template is None):
        template = models.JobExecutionTemplate()
    template.environment_variables = _update_envs(template.environment_variables, envs, secret_envs)
    template.args = _update_args(template.args, args)
    return template


def _update_envs(envs: [models.EnvVar], envs_dict: dict, secrets_dict: dict):
    if envs is None:
        envs = []
    existed_properties = [env for env in envs if env.value is not None]
    existed_secrets = [env for env in envs if
                       ((env.secret_value is not None) or (env.secret_value is None and env.value is None))]
    target_properties = existed_properties
    target_secrets = existed_secrets
    if envs_dict is not None and isinstance(envs_dict, dict):
        target_properties = [models.EnvVar(name=key, value=envs_dict[key]) for key in envs_dict.keys()]
    if secrets_dict is not None and isinstance(secrets_dict, dict):
        target_secrets = [models.EnvVar(name=key, secret_value=secrets_dict[key]) for key in secrets_dict.keys()]
    return target_properties + target_secrets


def _update_secrets(envs: [models.EnvVar], secrets: [models.Secret]):
    if envs is None:
        envs = []
    target_properties = [env for env in envs if env.value is not None]
    existed_secrets = [env for env in envs if
                       ((env.secret_value is not None) or (env.secret_value is None and env.value is None))]
    target_secrets = existed_secrets
    if secrets is not None:
        target_secrets = [models.EnvVar(name=secret.name, secret_value=secret.value) for secret in secrets]
    return target_properties + target_secrets


def _update_resource_requests(existing, cpu, memory):
    existing = existing if existing is not None else models.ResourceRequests()
    resource_requests = models.ResourceRequests(
        cpu=cpu or existing.cpu,
        memory=memory or existing.memory
    )
    return resource_requests


def _update_args(existing, args):
    args = _convert_args(args)
    if args is not None:
        return args
    return existing


def _convert_args(args):
    if args is None:
        return args

    return shlex.split(args)


def _poll_until_job_end(client, resource_group, service, job_name, job_execution_name):
    while True:
        execution = client.job_execution.get(resource_group, service, job_name, job_execution_name)
        status = execution.status
        if _is_job_execution_in_final_state(status):
            logger.warning(
                f"Job execution '{job_execution_name}' is in final status '{status}'. Exiting polling loop.")
            return execution
        else:
            logger.warning(
                f"Job execution '{job_execution_name}' is in status '{status}'. Polling again in 10 second...")
        time.sleep(10)


def _is_job_execution_in_final_state(status):
    return status is not None and status in (
        models.JobExecutionRunningState.COMPLETED,
        models.JobExecutionRunningState.FAILED,
        models.JobExecutionRunningState.CANCELED)
