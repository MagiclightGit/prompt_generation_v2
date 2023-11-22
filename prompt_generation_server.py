'''
@date    : 2023-11-16 10:04:37
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-22 15:44:43
Modified By: yangel(fflyangel@foxmail.com)
-----
@history :
================================================================================
   Date   	 By 	(version) 	                    Comments
----------	----	---------    ----------------------------------------------
================================================================================
Copyright (c) 2023 - 2023 All Right Reserved, MagicLight
'''


import os
import pathlib
import sys
import json
import logging
import argparse

from custom_ops.utils.server_util import SqsQueue,YamlParse,SQLConfig,GetInputInfo
from custom_ops.op_prompt_generate import OpPromptGenerate
from custom_ops.op_get_fiction_info import OPIpBibleObtain

import time

pathlib.Path('./logs/').mkdir(exist_ok=True)
logging.basicConfig(level= logging.INFO, filename='./logs/prompt_generate.log', filemode= 'a', format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')

def parse_option():
    parser = argparse.ArgumentParser('prompt generation server', add_help=False)
    parser.add_argument("--yaml_config", type=str, default="server_config.yaml", help="yaml config")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_option()
    #main()
    
    yaml_file = args.yaml_config
    logging.info("yaml_file: {}".format(yaml_file))
    src_deque_conf, sql_conf, dst_deque_conf = YamlParse(yaml_file)
    logging.info("yaml: {}, sqs_deque_conf: {}, sql_conf: {}, dst_deque_conf: {}".format(yaml_file, src_deque_conf, sql_conf, dst_deque_conf))
    
    # init sql
    sql_type = sql_conf["sql_type"]
    sql = SQLConfig(sql_type)
    while True:
        operator_type = "get"
        request = SqsQueue(src_deque_conf['url'], src_deque_conf['region_name'], src_deque_conf['max_number_of_mess'], operator_type)
        if len(request) == 0:
            logging.info("sqs queue len equal to 0")
            time.sleep(1)
            continue

        logging.info("get deque input: {}".format(request))
        for req in request:
            input = json.loads(req)
            #input:
            #{"project_id": "2158043", "flow_id": "db2udswkdtc", "fid": "0d5xjvdjyak", "chid": "1", "para_id": "0", "rtx": "_common"}
            try:
                project_id = input["project_id"]
                fid = input["fid"]
                chid = input["chid"]
                para_id = input["para_id"]
                flow_id = input["flow_id"]

                fiction_path, model_info = GetInputInfo(project_id, fid, chid, para_id, flow_id, sql, sql_type)
                fiction_parser = OPIpBibleObtain(fid, chid, para_id)
                ipbible, pompts_layout, ret_msg = fiction_parser.run([fiction_path, fid, chid, para_id, flow_id])

                logging.info(f"pompts_layout: {pompts_layout}")
                # TODO 
                # 1.get layout prompt_data
                # 2.write to sql 

                op_prompt_generate = OpPromptGenerate()
                op_prompt_generate.init()
                pos_prompts, neg_prompts, sub_pos_prompts = op_prompt_generate.run(flow_id, fid, chid, para_id, ipbible, model_info)
                logging.info(f"pos_prompts: {pos_prompts}\nneg_prompts: {neg_prompts}\nsub_pos_prompts: {sub_pos_prompts}")
                # res:
                # {"project_id": "2158043", "flow_id": "db2udswkdtc", "fid": "0d5xjvdjyak", "chid": "1", "para_id": "0", "rtx": "_common", "prompt": ""}

                res_req = {
                    "project_id":  project_id,
                    "fid": fid,
                    "chid": chid,
                    "para_id": para_id,
                    "flow_id": flow_id,
                    "gpt_prompt": {
                        "pos_prompts": pos_prompts,
                        "neg_prompts": neg_prompts,
                        "sub_pos_prompts": sub_pos_prompts
                    },
                    "layout_prompt": pompts_layout
                }
                operator_type = "put"
                res = SqsQueue(dst_deque_conf['url'], dst_deque_conf['region_name'], dst_deque_conf['max_number_of_mess'], operator_type, json.dumps(res_req, ensure_ascii=False))
                logging.info(f"fid: {fid}, chid: {chid}, para_id: {para_id} sqs add task: {res}")

            except Exception as err:
                logging.error("prompt generate failed, error: {}".format(err))