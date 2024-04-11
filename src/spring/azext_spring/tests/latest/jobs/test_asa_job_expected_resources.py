# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

EXPECTED_CREATE_JOB_PAYLOAD = r'''
{"properties": {"source": {"type": "BuildResult", "buildResultId": "<default>"}, "triggerConfig": {"triggerType": "Manual"}}}
'''