# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from ..log_stream.log_stream_validators import validate_all_instances_and_instance_are_mutually_exclusive
from ..log_stream.log_stream_validators import (validate_log_limit, validate_log_lines, validate_log_since,
                                                validate_max_log_requests)

logger = get_logger(__name__)

# TODO(jiec): examine the validation logic here again and add unit test to protect from changes.
def validate_job_log_stream(cmd, namespace):
    _validate_mutual_exclusive_param(namespace)
    _validate_required_param(namespace)
    validate_log_lines(namespace)
    validate_log_since(namespace)
    validate_log_limit(namespace)
    validate_max_log_requests(namespace)


def _validate_mutual_exclusive_param(namespace):
    validate_all_instances_and_instance_are_mutually_exclusive(namespace)


def _validate_required_param(namespace):
    if namespace.execution is None and namespace.instance:
        raise InvalidArgumentValueError("When --instance/-i is set, --execution is required.")
    if namespace.execution is None and namespace.instance is None:
        logger.warning("--execution and --instance/-i are not set, will try to get logs for the last job execution.")
