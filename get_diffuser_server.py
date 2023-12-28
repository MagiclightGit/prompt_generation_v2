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

import pathlib
import json
import logging
import argparse

from custom_ops.utils.server_util import SqsQueue, YamlParse, SQLConfig

from custom_ops.op_up_db import OPUpDb

import time

pathlib.Path('./logs/').mkdir(exist_ok=True)
logging.basicConfig(level= logging.INFO, filename='./logs/get_diffuser_server.log', filemode= 'a', format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def parse_option():
    parser = argparse.ArgumentParser('get diffuser server', add_help=False)
    parser.add_argument("--yaml_config", type=str, default="server_config_result.yaml", help="yaml config")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_option()
    #main()

    yaml_file = args.yaml_config
    logging.info("yaml_file: {}".format(yaml_file))
    src_deque_conf, sql_conf, _, _ = YamlParse(yaml_file)
    logging.info("yaml: {}, sqs_deque_conf: {}, sql_conf: {}".format(yaml_file, src_deque_conf, sql_conf))
    
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
            # param = input["param"]
            # input = json.loads(param)
            # logging.info(f"input param: {input}")
            #input:
            # {"project_id": "64769811011586", "flow_id": "64769811011585", "task_key": "64769811011585_64769811011586_1_2_multi-ctrl_lo1", "task_type": "text2img", "url_list": ["https://testdocsplitblobtrigger.blob.core.windows.net/diffuser-generation-image/64769811011585_64769811011586_1_2_multi-ctrl_lo1_0.jpg"], "code": 0, "msg": "success", "costtime": 36.66875433921814}
            try:
                project_id = input.get("project_id", "")
                chapter_id = input.get("chapter_id", "")
                para_id = input.get("para_id", "")
                global_chapter_id = input.get("global_chapter_id", "")
                global_para_id = input.get("global_para_id", "")
                flow_id = input.get("flow_id", "")
                layout_id = input.get("layout_id", "")
                image_id = input.get("image_id", "")
                url_list = input.get("url_list", [])

                if not global_chapter_id:
                    continue

                # TODO 
                op_up_db = OPUpDb()
                op_up_db.run([project_id, global_chapter_id, global_para_id, chapter_id, para_id, url_list, layout_id, image_id])


            except Exception as err:
                logging.error("get diffuser result failed, error: {}".format(err))