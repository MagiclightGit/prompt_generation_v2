'''
@date    : 2023-11-20 08:46:30
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-22 16:18:34
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

from custom_ops.utils.server_util import SqsQueue,YamlParse,SQLConfig,GetInputInfo,get_magiclight_api
from custom_ops.op_construct_request import OpConstructRequest
from custom_ops.op_get_fiction_info import OPIpBibleObtain

import time

pathlib.Path('./logs/').mkdir(exist_ok=True)
logging.basicConfig(level= logging.INFO, filename='./logs/construct_request.log', filemode= 'a', format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def parse_option():
    parser = argparse.ArgumentParser('construct request server', add_help=False)
    parser.add_argument("--yaml_config", type=str, default="server_config_construct.yaml", help="yaml config")
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
            #{"project_id": "2158043", "flow_id": "db2udswkdtc", "fid": "0d5xjvdjyak", "chid": "1", "para_id": "0", "img_id": ""}
            # try:
            if True:
                project_id = input["project_id"]
                fid = input["fid"]
                chid = input["chid"]
                para_id = input["para_id"]
                flow_id = input["flow_id"]
                img_id = input["img_id"]

                # TODO 
                # 1.get layout info from layout-select
                reponse = get_magiclight_api(para_id, chid, project_id, img_id)

                # logging.info(f"reponse: {reponse}")
                layout = reponse[0]

                # layout = {
                #     "layout_type": "bbox",
                #     "para_id": "0",
                #     "idx": "0",
                #     "layout_scene": "close_scene",
                #     "layout_view": "side_view",
                #     "urls": ["https://testdocsplitblobtrigger.blob.core.windows.net/layout-bbox/mzc002004jdjcy4_m0044k9yexc_1828320.jpg"],
                #     "bounding_box_info": [{
                #         "role_id": "",
                #         "bounding_box": [0.655671, 0.591564, 0.33912, 0.812757]
                #     }],
                #     "env_prompt": "market, outdoor, daytime, China modern, sunny, bustlingmarketplace, sunnyday, colorfulfruits, wooden carts, shoutingvendors, attractcustomers",
                #     "person_prompt": [{
                #         "index": 0,
                #         "gender": "女",
                #         "look": "左向",
                #         "pose": "蹲",
                #         "role_id": "0",
                #         "prompt": "best quality, ultra_detailed, anime, detailed_face, (solo:2.0), gdr5, 1boy, solo, green_suit,, gdr5_v1, (happy:1.2), (decided to start a fruit business.:1.2), side view"
                #     }],
                #     "sub_prompt": {
                #         "object": "best quality, ultra_detailed, anime(The fruit knife in Xiao Lin's hand.), (close_up), no people, market, outdoor, daytime, China modern, sunny",
                #         "scenery": "best quality, ultra_detailed, anime(Xie Xiaolin stood in front of the fruit stall.), (scenery), no people, market, outdoor, daytime, China modern, sunny"
                #     },
                #     "neg_prompt": "EasyNegative, (same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,bad hand,extra hands,extra fingers, too many fingers,fused fingers,bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head(2people:2.0), (duplicate:1.2), tiling, multiple people, multiple face"
                # }
                # layout = json.dumps(layout, ensure_ascii=False)

                common_request_info = json.dumps({"common_info":"json str","lora_name":"","depth_img_urls":[""]})
                batch_size = 4

                #2. get model info
                fiction_path, model_info = GetInputInfo(project_id, fid, chid, para_id, flow_id, sql, sql_type)
                fiction_parser = OPIpBibleObtain(fid, chid, para_id)
                ipbible, pompts_layout, ret_msg = fiction_parser.run([fiction_path, fid, chid, para_id, flow_id])

                op_construct_request = OpConstructRequest()
                op_construct_request.init()

                input_data, ret_call_dict, role_id, debug_dict = op_construct_request.run(flow_id, fid, chid, para_id, ipbible, model_info, batch_size, layout, common_request_info)
                logging.info(f"input_data: {input_data}\nret_call_dict: {ret_call_dict}\ndebug_dict: {debug_dict}")

                # res:

                # res_req = {
                #     "project_id":  project_id,
                #     "fid": fid,
                #     "chid": chid,
                #     "para_id": para_id,
                #     "flow_id": flow_id,
                # }
                # operator_type = "put"
                # res = SqsQueue(dst_deque_conf['url'], dst_deque_conf['region_name'], dst_deque_conf['max_number_of_mess'], operator_type, json.dumps(res_req, ensure_ascii=False))
                # logging.info(f"fid: {fid}, chid: {chid}, para_id: {para_id} sqs add task: {res}")

            # except Exception as err:
            #     logging.error("construct request failed, error: {}".format(err))