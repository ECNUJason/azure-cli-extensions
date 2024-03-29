# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import InvalidArgumentValueError
from knack.log import get_logger

from ..log_stream.log_stream_validators import validate_all_instances_and_instance_are_mutually_exclusive
from ..log_stream.log_stream_validators import (validate_log_limit, validate_log_lines, validate_log_since,
                                                validate_max_log_requests)

logger = get_logger(__name__)


def validate_job_log_stream(namespace):
    _validate_mutual_exclusive_param(namespace)
    _validate_execution_name_param(namespace)
    validate_log_lines(namespace)
    validate_log_since(namespace)
    validate_log_limit(namespace)
    validate_max_log_requests(namespace)


def _validate_mutual_exclusive_param(namespace):
    validate_all_instances_and_instance_are_mutually_exclusive(namespace)


def _validate_execution_name_param(namespace):
    if namespace.execution is None:
        if namespace.instance is not None:
            raise InvalidArgumentValueError("When --instance/-i is set, --execution is required.")
        else:
            logger.warning("--execution is not specified, will try to get logs for the latest job execution.")
