# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import shlex
import time
from json import JSONEncoder
from threading import Thread
from time import sleep

import requests
from azext_spring._utils import (get_hostname, get_bearer_auth, wait_till_end)
from azext_spring.vendored_sdks.appplatform.v2024_01_01_preview import models
from azure.cli.core.azclierror import (ValidationError)
from azure.cli.core.util import sdk_no_wait
from knack.log import get_logger
from knack.util import CLIError

from .job_deployable_factory import deployable_selector
from .model.job_execution_instance import (JobExecutionInstanceCollection, JobExecutionInstance)
from ..log_stream.log_stream_operations import (attach_logs_query_options, log_stream_from_url,
                                                LogStreamBaseQueryOptions)
from ..log_stream.log_stream_validators import validate_thread_number
from ..log_stream.writer import (DefaultWriter, PrefixWriter)

logger = get_logger(__name__)

# pylint: disable=line-too-long
LOG_RUNNING_PROMPT = "This command usually takes minutes to run. Add '--verbose' parameter if needed."


#  Job's command usually operates an Spring/Job and the Spring/Job/Execution under the job.
# The general idea of these command is putting all input command in parameter dict and let the Resource factory to construct the payload.
# - A job must consume a path can be deployable, it can be custom container or build result resource id,
# - _job_deployable_factory determines the deployable type and upload necessary binary/code to the service when constructing the deployable_path.

class MyEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__ 


def job_create(cmd, client, resource_group, service, name):
    _ensure_job_not_exist(client, resource_group, service, name)
    job_resource = models.JobResource(
        properties = models.JobResourceProperties(
            trigger_config = models.ManualJobTriggerConfig(
                trigger_type = "Manual"
            ),
            source = models.BuildResultUserSourceInfo(
                type = "BuildResult",
                build_result_id = "<default>",
            )
        )
    )

    logger.warning("Start to create job '{}'..".format(name))
    poller = client.job.begin_create_or_update(resource_group, service, name, job_resource)
    wait_till_end(cmd, poller)
    logger.warning("Job '{}' is created successfully.".format(name))
    return job_get(cmd, client, resource_group, service, name)


def job_update(cmd, client, resource_group, service, name,
               envs=None,
               secret_envs=None,
               args=None,
               ):
    '''job_update
    Update job with configuration
    '''
    job_resource = client.job.get(resource_group, service, name)
    existing_secrets = client.job.list_env_secrets(resource_group, service, name)
    if existing_secrets is not None:
        job_resource.properties.template.environment_variables.secrets = existing_secrets
    job_resource.properties = _update_job_properties(job_resource.properties, envs, secret_envs, args)

    logger.warning("Start to update job '{}'..".format(name))
    poller = client.job.begin_create_or_update(resource_group, service, name, job_resource)
    wait_till_end(cmd, poller)
    logger.warning("Job '{}' is updated successfully.".format(name))
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
              wait_until_finished=False
              ):
    properties = models.JobExecutionProperties(
        template = models.JobExecutionTemplate(
            environment_variables=_update_envs(None, envs, secret_envs),
            args=_convert_args(args)
        ),
        resource_requests = _update_resource_requests(None, cpu, memory)
    )

    if wait_until_finished == False:
        return client.job.begin_start(resource_group, service, name, properties)
    else:
        poller = sdk_no_wait(False, client.job.begin_start,
                             resource_group, service, name, properties)
        execution_name = poller.result().name
        return _poll_until_job_end(cmd, client, resource_group, service, name, execution_name)


def job_log_stream(cmd, client, resource_group, service, name, execution, all_instances=None, instance=None,
                   follow=None, max_log_requests=5, lines=50, since=None, limit=2048):
    # TODO(jiec): add logics here in the future.
    # return '[{"line1": "logs_1"},{"line2": "logs_2"}]'

    queryOptions = LogStreamBaseQueryOptions(follow=follow, lines=lines, since=since, limit=limit)
    url_dict = _get_log_stream_urls(cmd, client, resource_group, service, name, execution, all_instances,
                                    instance, queryOptions)
    validate_thread_number(len(url_dict), max_log_requests)
    auth = get_bearer_auth(cmd.cli_ctx)
    exceptions = []
    threads = _get_log_threads(all_instances, url_dict, auth, exceptions)

    if follow and len(threads) > 1:
        _parallel_start_threads(threads)
    else:
        _sequential_start_threads(threads)

    if exceptions:
        raise exceptions[0]


def job_execution_cancel(cmd, client,
             resource_group,
             service,
             job,
             name,
             no_wait=False):
    return sdk_no_wait(no_wait, client.job_execution.begin_cancel,
                       resource_group, service, job, name)


def job_execution_get(cmd, client, resource_group, service, job, name):
    return client.job_execution.get(resource_group, service, job, name)


def job_execution_list(cmd, client, resource_group, service, job):
    return client.job_executions.list(resource_group, service, job)


def job_execution_instance_list(cmd, client, resource_group, service, job, execution):
    return _list_job_execution_instances(cmd, client, resource_group, service, job, execution)


def _ensure_job_not_exist(client, resource_group, service, name):
    job = None
    try:
        job = client.job.get(resource_group, service, name)
    except Exception:
        # ignore
        return
    if job:
        raise ValidationError('Job {} already exist, cannot create.'.format(job.id))


def _update_job_properties(properties, envs, secret_envs, args):
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
        build_result_id = deployable_path,
        version = version
    )
    return properties


def _update_job_properties_template(template, envs, secret_envs, args):
    if (template is None):
        template = models.JobExecutionTemplate()
    template.environment_variables = _update_envs(template.environment_variables, envs, secret_envs)
    template.args = _update_args(template.args, args)
    return template


def _update_envs(envs, envs_dict, secrets_dict):
    if envs is None:
        envs = models.JobExecutionTemplateEnvironmentVariables()
    if envs_dict is not None:
        envs.properties = envs_dict
    if secrets_dict is not None:
        envs.secrets = secrets_dict
    return envs


def _update_resource_requests(existing, cpu, memory):
    existing = existing if existing is not None else models.ResourceRequests()
    resource_requests = models.ResourceRequests(
        cpu = cpu or existing.cpu,
        memory = memory or existing.memory
    )
    return resource_requests


def _update_args(existing, args):
    args = _convert_args(args)
    if args is not None:
        return args
    return existing


def _convert_args(args):
    if args is not None:
        return shlex.split(args)
    return args


def _poll_until_job_end(cmd, client, resource_group, service, job_name, job_execution_name):
    while True:
        execution = client.job_execution.get(resource_group, service, job_name, job_execution_name)
        status = execution.status
        if status == "Completed" or status == "Failed" or status == "Cancelled":
            logger.warning("Job execution '{}' is in final status '{}'. Exiting polling loop.".format(job_execution_name, status))
            return execution
        else:
            logger.warning("Job execution '{}' is in status '{}'. Polling again in 10 second...".format(job_execution_name, status))
        time.sleep(10)


def _list_job_execution_instances(cmd, client, resource_group, service, job, execution) -> [JobExecutionInstance]:
    auth = get_bearer_auth(cmd.cli_ctx)
    url = _get_list_job_execution_instances_url(cmd, client, resource_group, service, job, execution)
    connect_timeout_in_seconds = 30
    read_timeout_in_seconds = 60
    timeout = (connect_timeout_in_seconds, read_timeout_in_seconds)
    with requests.get(url, stream=False, auth=auth, timeout=timeout) as response:
        if response.status_code != 200:
            _handle_and_raise_list_job_execution_instance_error(url, response)
        return _parse_job_execution_instances(response.json())


def _get_list_job_execution_instances_url(cmd, client, resource_group, service, job, execution):
    hostname = get_hostname(cmd, client, resource_group, service)
    return f"https://{hostname}/api/jobs/{job}/executions/{execution}/instances";


def _handle_and_raise_list_job_execution_instance_error(url, response):
    failure_reason = response.reason
    if response.content:
        if isinstance(response.content, bytes):
            failure_reason = f"{failure_reason}:{response.content.decode('utf-8')}"
        else:
            failure_reason = f"{failure_reason}:{response.content}"
    msg = f"Failed to access the url '{url}' with status code '{response.status_code}' and reason '{failure_reason}'"
    raise CLIError(msg)


def _parse_job_execution_instances(response_json) -> [JobExecutionInstance]:
    p = JobExecutionInstanceCollection.deserialize(response_json)
    if p.value is None:
        raise CLIError("Failed to parse the response '{}'".format(response_json))

    return p.value


def _get_log_stream_urls(cmd, client, resource_group, service, job_name, execution_name,
                         all_instances, instance, queryOptions: LogStreamBaseQueryOptions):
    hostname = get_hostname(cmd.cli_ctx, client, resource_group, service)
    url_dict = {}

    if not all_instances and not instance:
        logger.warning("No `-i/--instance` or `--all-instances` parameters specified.")
        instances: [JobExecutionInstance] = _list_job_execution_instances(cmd, client, resource_group, service,
                                                                          job_name, execution_name)
        if instances is None or len(instances) == 0:
            logger.warning(f"No instances found for job execution: '{job_name}/{execution_name}'.")
            return url_dict
        elif instances is not None and len(instances) > 1:
            logger.warning("Multiple instances found:")
            for temp_instance in instances:
                logger.warning("{}".format(temp_instance.name))
            logger.warning("Please use '-i/--instance' parameter to specify the instance name, "
                           "or use `--all-instance` parameter to get logs for all instances.")
            return url_dict
        elif instances is not None and len(instances) == 1:
            logger.warning("Exact one instance found, will get logs for it:")
            logger.warning('{}'.format(instances[0].name))
            # Make it as if user has specified exact instance name
            instance = instances[0].name

    if all_instances is True:
        instances: [JobExecutionInstance] = _list_job_execution_instances(cmd, client, resource_group, service,
                                                                          job_name, execution_name)
        if instances is None or len(instances) == 0:
            logger.warning(f"No instances found for job execution: '{job_name}/{execution_name}'.")
            return url_dict
        for i in instances:
            url = _get_log_stream_url(hostname, job_name, execution_name, i.name, queryOptions)
            url_dict[url] = JobExecutionInstance(name=i.name)
    elif instance:
        url = _get_log_stream_url(hostname, job_name, execution_name, instance, queryOptions)
        url_dict[url] = JobExecutionInstance(name=instance)

    return url_dict


def _get_log_stream_url(hostname, job_name, execution_name, job_execution_instance_name,
                        queryOptions: LogStreamBaseQueryOptions):
    url_template = "https://{}/api/jobs/{}/executions/{}/instances/{}/logstream"
    url = url_template.format(hostname, job_name, execution_name, job_execution_instance_name)
    url = attach_logs_query_options(url, queryOptions)
    return url


def _get_log_threads(all_instances, url_dict, auth, exceptions):
    threads = []
    need_prefix = all_instances is True
    for url in url_dict.keys():
        writer = _get_default_writer()
        if need_prefix:
            instance_info = url_dict[url]
            prefix = "[{}]".format(instance_info.name)
            writer = _get_prefix_writer(prefix)
        threads.append(Thread(target=log_stream_from_url, args=(url, auth, None, exceptions, writer)))
    return threads


def _get_prefix_writer(prefix):
    """
    Define this method, so that we can mock this method in scenario test to test output
    """
    return PrefixWriter(prefix)


def _get_default_writer():
    """
    Define this method, so that we can mock this method in scenario test to test output
    """
    return DefaultWriter()


def _parallel_start_threads(threads: [Thread]):
    for t in threads:
        t.daemon = True
        t.start()

    while _contains_alive_thread(threads):
        sleep(1)
        # so that ctrl+c can stop the command


def _sequential_start_threads(threads: [Thread]):
    for idx, t in enumerate(threads):
        t.daemon = True
        t.start()

        while t.is_alive():
            sleep(1)
            # so that ctrl+c can stop the command
