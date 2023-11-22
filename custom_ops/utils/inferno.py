'''
Description: API for Inferno services
Author: guoping
Date: 2022-06-13 20:05:10
Acknowledgements: https://iwiki.woa.com/pages/viewpage.action?pageId=800787143
'''

import os
import json
import time

from google.protobuf.json_format import MessageToDict

from inferno.logger import logger
from inferno.servers.trpc.trpc_client import InfernoTrpcClient


class InfernoService(InfernoTrpcClient):
    def __init__(self, service_name, flow_name=None, namespace=None, timeout=10000, test_host=None, **kwargs):
        self.flow_name = flow_name
        namespace = namespace or ('Production' if os.getenv('SUMERU_ENV', 'devnet') == 'formal' else 'Development')
        pb_module_dir = self.find_exists(
            [
                '/usr/local/trpc/bin/inferno_pb',
                '/usr/local/lib/python3.8/site-packages/trpc_weishi_vu_inferno',
                '/data/miniconda3/envs/env-3.8.8/lib/python3.8/site-packages/trpc_weishi_vu_inferno',
                '/cfs/cfs-0s927vn5/jackieysong/python_env/default/lib/python3.8/site-packages/trpc_weishi_vu_inferno',
            ]
        )
        super(InfernoService, self).__init__(pb_module_dir)
        self.set_options(
            service_target=f'polaris://{service_name}' if test_host is None else f'ip://{test_host}',
            service_namespace=namespace,
            caller_service_name=service_name,
            caller_namespace=namespace,
            caller_envname='formal',
            timeout=timeout,
        )
        logger.info(f'Successfully connected to {service_name}')

    def find_exists(self, paths):
        for path in paths:
            if os.path.exists(path):
                return path
        raise ModuleNotFoundError(f'Failed to find inferno pb in {paths}')

    def run(self, flow_name=None, log_id=None, **input_data):
        flow_name = flow_name or self.flow_name
        assert flow_name is not None, 'flow_name is None'
        log_id = log_id or input_data.get('flow_id', None) or f'log_{int(time.time() * 1000)}'
        req = self.create_request()
        req.flow_name = flow_name
        req.log_id = log_id
        req = add_data_item(req, input_data)
        rsp = self.serve(req)
        return rsp, MessageToDict(req, preserving_proto_field_name=True)

    def post_process(self, rsp):
        assert rsp.code == 0, rsp.message
        keys = list(rsp.outputs.keys())
        res_key = 'result' if 'result' in keys else keys[0]
        res = rsp.outputs[res_key]
        if res.type == 'json':
            ret = json.loads(res.data_ref.str_data)
        else:
            ret = res.data_ref.str_data
        return ret


def add_data_item(req, data_dict):
    for k, v in data_dict.items():
        if isinstance(v, bytes):
            req.inputs[k].name = k
            req.inputs[k].type = 'raw_data'
            req.inputs[k].data_ref.bytes_data = v
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], bytes):
            req.inputs[k].name = k
            req.inputs[k].type = 'raw_data'
            req.inputs[k].data_ref.bytes_array_data.extend(v)
        elif isinstance(v, str):
            req.inputs[k].name = k
            req.inputs[k].type = 'str'
            req.inputs[k].data_ref.str_data = v
        elif isinstance(v, int):
            req.inputs[k].name = k
            req.inputs[k].type = 'int'
            req.inputs[k].data_ref.int_data = v
        elif isinstance(v, float):
            req.inputs[k].name = k
            req.inputs[k].type = 'float'
            req.inputs[k].data_ref.float_data = v
        else:
            req.inputs[k].name = k
            req.inputs[k].type = 'json'
            req.inputs[k].data_ref.str_data = json.dumps(v, ensure_ascii=False)
    return req
