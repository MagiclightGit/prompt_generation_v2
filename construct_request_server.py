'''
@date    : 2023-11-20 08:46:30
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-28 02:36:13
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

from custom_ops.utils.server_util import SqsQueue,YamlParse,SQLConfig,GetInputInfo,get_magiclight_api,TaskCallback

from custom_ops.op_construct_request import OpConstructRequest
from custom_ops.op_get_fiction_info import OPIpBibleObtain
from custom_ops.op_up_db import OPUpDb

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
            param = input["param"]
            input = json.loads(param)
            # logging.info(f"input param: {input}")
            #input:
            #{"project_id": "5484043911170", "flow_id": "105945625601", "chapter_id": "1", "para_id": "0", "image_id": ""}
            #{"project_id":"105945625602","flow_id":"2291183289344","user_id":"0","task_id":"0","param":"{\"project_id\":\"105945625602\",\"global_chapter_id\":\"1405903041536\",\"global_para_id\":\"1420612465664\",\"chapter_id\":\"1\",\"para_id\":\"2\",\"img_id\":\"\",\"flow_id\":\"105945625601\"}"}
            try:
                project_id = input.get("project_id", "")
                chapter_id = input.get("chapter_id", "")
                para_id = input.get("para_id", "")
                global_chapter_id = input.get("global_chapter_id", "")
                global_para_id = input.get("global_para_id", "")
                flow_id = input.get("flow_id", "")
                image_id = input.get("image_id", "")

                # TODO 
                # 1.get layout info from layout-select
                reponse_list = get_magiclight_api(global_para_id, global_chapter_id, project_id, image_id)
                if not reponse_list:
                    logging.error(f"get layout info failed")        
                for reponse in reponse_list:
                    layout = reponse["data"]
                    global_layout_id = reponse["id"]

                    # layout = {"layout_type":"bbox","para_id":"0","idx":"0","layout_scene":"middle_scene","layout_view":"front_view","urls":"https://testdocsplitblobtrigger.blob.core.windows.net/layout-bbox/mzc00200qosiwxm_g0045e2ttim_2476320.jpg","bounding_box_info":[{"role_id":"","bounding_box":[0.469329,0.624486,0.179398,0.746914]},{"role_id":"","bounding_box":[0.351273,0.601852,0.179398,0.792181]}],"env_prompt":["best quality, ultra_detailed, 2people, , city park, outdoor, daytime, Can't determine, sunny, sunnyafternoon, bustlingcitypark, colorfulplayground, lushgreentrees, bloomingflowers, childrenplaying"],"person_prompt":[{"index":0,"gender":"男","look":"右向","pose":"用手拿（道具）","entity_id":"1","prompt":"1girl,gracefulandgentle,melonface,slender,theonlydaughterofateaowner,longhair,darkbluehair,purpleeyes, familytravelgameartwivside view"},{"index":1,"gender":"男","look":"正向","pose":"站","entity_id":"0","prompt":"1girl,gracefulandgentle,melonface,slender,theonlydaughterofateaowner,longhair,darkbluehair,purpleeyes, familytravelgameartwivlook at viewer"}],"sub_prompt":{"object":"best quality, ultra_detailed, anime(Kids having fun on a colorful playground), (close_up), no people, city park, outdoor, daytime, Can't determine, sunny","scenery":"best quality, ultra_detailed, anime(A bustling city park), (scenery), no people, city park, outdoor, daytime, Can't determine, sunny"},"neg_prompt":"EasyNegative, (same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,bad hand,extra hands,extra fingers, too many fingers,fused fingers,bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head","prompts_data":{"conversation_id":"c_-1","project_id":"5484043911170","chapter_id":"1","para_id":"0","para_content":["Zhang San and Li Si are good friends","two man "],"style":"无法确定","location":"室外","num_person":"2","person_id":[["1","male"],["0","male"]],"pose":["[]","[]"],"gender":{"male":2,"female":0}}}
                    
                    # layout = json.dumps(layout, ensure_ascii=False)

                    common_request_info = json.dumps({"common_info":"json str","lora_name":"","depth_img_urls":[""]})
                    batch_size = 4

                    #2. get model info
                    # TODO user add roles should get new model info
                    roles_list = []
                    if image_id:
                        tmp = json.loads(layout)
                        person_prompt = tmp.get("person_prompt", [])
                        for item in person_prompt:
                            roles = {"id": item["entity_id"]} 
                            roles_list.append(roles)
                    
                    fiction_path, model_info = GetInputInfo(project_id, chapter_id, para_id, flow_id, sql, roles_list)
                    fiction_parser = OPIpBibleObtain(project_id, chapter_id, para_id)
                    ipbible, pompts_layout, ret_msg = fiction_parser.run([fiction_path, project_id, chapter_id, para_id, flow_id])
                    logging.info(f"ipbible: {ipbible}\pompts_layout: {pompts_layout}\ret_msg: {ret_msg}")

                    op_construct_request = OpConstructRequest()
                    op_construct_request.init()

                    # input_data, ret_call_dict, role_id, debug_dict = op_construct_request.run(flow_id, project_id, chapter_id, para_id, ipbible, model_info, batch_size, layout, common_request_info)
                    # 场景、单人和多人
                    input_data_list = op_construct_request.run(flow_id, project_id, chapter_id, para_id, ipbible, model_info, batch_size, layout, common_request_info)

                    # logging.info(f"input_data: {input_data_list}\n")
                    res_list = []
                    for item in input_data_list:
                        input_data = item['input_data']
                        task_key = item.get("task_key", "")
                        if  task_key[-10:]=="object_lo2" or task_key[-11:] == "scenery_lo2":
                            layout_id = ""
                        else:
                            layout_id = global_layout_id

                        input_data["global_chapter_id"] = global_chapter_id
                        input_data["global_para_id"] = global_para_id
                        input_data["para_id"] = para_id
                        input_data["chapter_id"] = chapter_id
                        input_data["layout_id"] = layout_id
                        input_data["image_id"] = image_id

                        operator_type = "put"
                        req_data = {'input_data': json.dumps(input_data)}
                        logging.info(f"input_data: {req_data}\n")
                        res = SqsQueue(dst_deque_conf['url'], dst_deque_conf['region_name'], dst_deque_conf['max_number_of_mess'], operator_type, json.dumps(req_data, ensure_ascii=False))

                    #     # 回调结果查询
                    #     # TODO batch 生成结果获取
                    #     task_key = input_data["task_key"]
                    #     batch_size = 1
                    #     res = TaskCallback(key=task_key)
                    #     res_list.extend(res)
                    #     logging.info(f"diffuser res: {res}")

                    # # write to db
                    # op_up_db = OPUpDb()
                    # for item in res_list:
                    #     item = json.loads(item)
                    #     url_list = item.get("url_list", [])
                    #     task_key = item.get("task_key", "")
                    #     if  task_key[-10:]=="object_lo2" or task_key[-11:] == "scenery_lo2":
                    #         layout_id = ""
                    #     else:
                    #         layout_id = global_layout_id
                        
                    #     op_up_db.run([project_id, global_chapter_id, global_para_id, chapter_id, para_id, url_list, layout_id, image_id])
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


            except Exception as err:
                logging.error("construct request failed, error: {}".format(err))