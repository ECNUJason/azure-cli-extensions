# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json


class JobExecutionInstanceProperties:
    name: str

    def __init__(self, name):
        self.name = name


class JobExecutionInstance:
    properties: JobExecutionInstanceProperties

    def __init__(self, properties):
        self.properties = properties


class JobExecutionInstanceCollection:
    value: list[JobExecutionInstance] = []

    def __init__(self, value):
        self.value = value

    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
