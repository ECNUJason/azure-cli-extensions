# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class JobExecutionInstanceProperties:
    _name: str

    def __init__(self, name, **kwargs):
        self.name = kwargs.get('name', None)

    def name(self):
        return self._name


class JobExecutionInstance:
    _properties: JobExecutionInstanceProperties

    def __init__(self, properties, **_):
        if properties is None:
            raise CLIError("`properties` is a required field for JobExecutionInstance.")

        self._properties = JobExecutionInstanceProperties(**properties)

    def properties(self):
        return self._properties

# TODO(jiec): Refer to C:\Users\jiec\devops\projects\public\AzureCLI\20240207-python-3.11\show-acs-configs\azure-cli-extensions\src\spring\azext_spring\vendored_sdks\appplatform\_serialization.py
class JobExecutionInstanceCollection:
    _value: list[JobExecutionInstance] = []

    def __init__(self, value, **_):
        if value is None:
            self._value = None
            return

        if isinstance(value, list):
            for instance_response in value:
                self.value.append(JobExecutionInstance(**instance_response))

    def value(self):
        return self._value