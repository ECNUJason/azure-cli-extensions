# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import json

from azext_spring.vendored_sdks.appplatform.v2024_05_01_preview.models import (JobResource)

sample_job_resource_json_str = r'''
{
  "properties": {
    "provisioningState": "Succeeded",
    "triggerConfig": {
      "triggerType": "Manual"
    },
    "source": {
      "type": "BuildResult",
      "buildResultId": "<default>"
    },
    "template": {
      "environmentVariables": [
        {
          "name": "key1",
          "value": "value1"
        },
        {
          "name": "env2",
          "value": "value2"
        },
        {
          "name": "secretKey1"
        }
      ],
      "args": [
        "arg1",
        "arg2"
      ]
    }
  },
  "systemData": {
    "createdBy": "sample-user",
    "createdByType": "User",
    "createdAt": "2021-08-11T03:16:03.944Z",
    "lastModifiedBy": "sample-user",
    "lastModifiedByType": "User",
    "lastModifiedAt": "2021-08-11T03:17:03.944Z"
  },
  "type": "Microsoft.AppPlatform/Spring/jobs",
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.AppPlatform/Spring/myservice/jobs/test-job",
  "name": "test-job"
}
'''

sample_job_resource = JobResource.deserialize(json.loads(sample_job_resource_json_str))

sample_job_resource_after_update_json_str = r'''
{
  "properties": {
    "provisioningState": "Succeeded",
    "triggerConfig": {
      "triggerType": "Manual"
    },
    "source": {
      "type": "BuildResult",
      "buildResultId": "<default>"
    },
    "template": {
      "environmentVariables": [
        {
          "name": "prop1",
          "value": "v_prop1"
        },
        {
          "name": "secretKey1"
        }
      ],
      "args": [
        "arg1",
        "arg2"
      ]
    }
  },
  "systemData": {
    "createdBy": "sample-user",
    "createdByType": "User",
    "createdAt": "2021-08-11T03:16:03.944Z",
    "lastModifiedBy": "sample-user",
    "lastModifiedByType": "User",
    "lastModifiedAt": "2021-08-11T03:17:03.944Z"
  },
  "type": "Microsoft.AppPlatform/Spring/jobs",
  "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.AppPlatform/Spring/myservice/jobs/test-job",
  "name": "test-job"
}
'''
sample_job_resource_after_update = json.loads(sample_job_resource_after_update_json_str)

expected_create_job_payload = '''
{
  "properties": {
    "source": {
      "type": "BuildResult",
      "buildResultId": "<default>"
    },
    "triggerConfig": {
      "triggerType": "Manual"
    }
  }
}
'''

expected_update_job_payload = '''
{
  "properties": {
    "template": {
      "environmentVariables": [
        {
          "name": "prop1",
          "value": "v_prop1"
        },
        {
          "name": "secretKey1",
          "secretValue": "secretValue1"
        }
      ],
      "args": [
        "arg1",
        "arg2"
      ]
    },
    "source": {
      "type": "BuildResult",
      "buildResultId": "<default>"
    },
    "triggerConfig": {
      "triggerType": "Manual"
    }
  }
}
'''
