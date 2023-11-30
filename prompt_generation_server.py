'''
@date    : 2023-11-16 10:04:37
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-26 13:08:33
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
import requests

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
    src_deque_conf, sql_conf, dst_deque_conf, task_conf = YamlParse(yaml_file)
    logging.info("yaml: {}, sqs_deque_conf: {}, sql_conf: {}, dst_deque_conf: {}".format(yaml_file, src_deque_conf, sql_conf, dst_deque_conf))
    
    # init sql
    sql_type = sql_conf["sql_type"]
    sql = SQLConfig(sql_type)
    while True:
        operator_type = "get"
        request = SqsQueue(src_deque_conf['url'], src_deque_conf['region_name'], src_deque_conf['max_number_of_mess'], operator_type)
        if len(request) == 0:
            # logging.info("sqs queue len equal to 0")
            time.sleep(1)
            continue

        logging.info("get deque input: {}".format(request))
        for req in request:
            input = json.loads(req)
            #input:
            #{"project_id": "5484043911170", "flow_id": "5484043911169", "chapter_id": "1", "para_id": "0", "user_id": "43315623606272"}

            project_id = input.get("project_id", "")
            chapter_id = input.get("local_chapter_id", "")
            para_id = input.get("local_para_id", "")
            global_chapter_id = input.get("global_chapter_id", "")
            global_para_id = input.get("global_para_id", "")
            flow_id = input.get("flow_id", "")
            user_id = input.get("user_id", "")

            task_id = f"{chapter_id}_{para_id}"
            try:
                # 任务监控
                
                # task_data = {"type":"prompt", "project_id": project_id, "flow_id": flow_id, "user_id": user_id, "task_id": task_id, "status":"start"}
                # rsp = requests.post(task_conf["url"], headers = task_conf["headers"], data = json.dumps(task_data), timeout = 20)

                fiction_path, model_info = GetInputInfo(project_id, chapter_id, para_id, flow_id, sql)
                logging.info(f"model_info: {model_info}")
                fiction_parser = OPIpBibleObtain(project_id, chapter_id, para_id)
                ipbible, pompts_layout, ret_msg = fiction_parser.run([fiction_path, project_id, chapter_id, para_id, flow_id])

                logging.info(f"pompts_layout: {pompts_layout}")
                # TODO 
                # 1.get layout prompt_data
                # 2.write to sql 

                op_prompt_generate = OpPromptGenerate()
                op_prompt_generate.init()
                pos_prompts, neg_prompts, sub_pos_prompts = op_prompt_generate.run(flow_id, project_id, chapter_id, para_id, ipbible, model_info)
                logging.info(f"pos_prompts: {pos_prompts}\nneg_prompts: {neg_prompts}\nsub_pos_prompts: {sub_pos_prompts}")
                # res:
                # {"project_id": "2158043", "flow_id": "db2udswkdtc", "fid": "0d5xjvdjyak", "chid": "1", "para_id": "0", "rtx": "_common", "prompt": ""}

                res_req = {
                    "project_id":  project_id,
                    "chapter_id": chapter_id,
                    "para_id": para_id,
                    "global_chapter_id": global_chapter_id,
                    "global_para_id": global_para_id,
                    "flow_id": flow_id,
                    "user_id": user_id,
                    "image_id": "",
                    "gpt_prompt": {
                        "pos_prompts": pos_prompts,
                        "neg_prompts": neg_prompts,
                        "sub_pos_prompts": sub_pos_prompts
                    },
                    "layout_prompt": pompts_layout
                }

                add_task = {"type":"layout", "project_id": project_id, "flow_id": flow_id, "user_id": user_id, "task_id": task_id, "param": json.dumps(res_req, ensure_ascii = False)}
                rsp = requests.post(task_conf["add_url"], headers = task_conf["headers"], data = json.dumps(add_task), timeout = 20)
                # operator_type = "put"
                # res = SqsQueue(dst_deque_conf['url'], dst_deque_conf['region_name'], dst_deque_conf['max_number_of_mess'], operator_type, json.dumps(res_req, ensure_ascii=False))
                logging.info(f"project_id: {project_id}, chid: {chapter_id}, para_id: {para_id}  add task: {rsp}")

                # task_data = {"type":"prompt", "project_id": project_id, "flow_id": flow_id, "user_id": user_id, "task_id": task_id, "status":"finish"}
                # rsp = requests.post(task_conf["url"], headers = task_conf["headers"], data = json.dumps(task_data), timeout = 20)

            except Exception as err:
                logging.error("prompt generate failed, error: {}".format(err))

                # task_data = {"type":"prompt", "project_id": project_id, "flow_id": flow_id, "user_id": user_id, "task_id": task_id, "status":"error"}
                # rsp = requests.post(task_conf["url"], headers = task_conf["headers"], data = json.dumps(task_data), timeout = 20)