'''
@date    : 2023-11-22 16:53:27
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-27 16:29:30
Modified By: yangel(fflyangel@foxmail.com)
-----
@history :
================================================================================
   Date   	 By 	(version) 	                    Comments
----------	----	---------    ----------------------------------------------
================================================================================
Copyright (c) 2023 - 2023 All Right Reserved, MagicLight
'''

import requests
import json
import logging

class OPUpDb(object):
    def __init__(
            self
        ):
        self.request_url = "http://test.magiclight.ai/api/image"
        self.request_img_info_url = "https://test.magiclight.ai/api/image-info"
        self.header = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def img_info_run(self, inputs):
        projectId, data = inputs
        # up to db
        requset_body = []
        for item in data:
            body = {
                "projectId": projectId,
                "imageId": item[0],
                "data": item[1],
            }
            requset_body.append(body)
        # logging.info(f"requset_body: {requset_body}")
        response = requests.post(self.request_img_info_url, headers=self.header, json=requset_body)
        # logging.info(f"db upload result: {response}")
        try:
            response_msg = json.loads(response.text).get("msg", "")
        except Exception as err:
            response_msg = "get response msg error"
        logging.info(f"db upload prompt info code: {response.status_code}, response msg: {response_msg}")

        return 

    def run(self, inputs):
        projectId, chapterId, paraId, localChapterId, localParaId, image_url, idx, image_id = inputs

        if not image_url:
            logging.error(f"generate img failed! msg: img url is empty.")
            return
        
        # up to db
        requset_body = []

        if image_id: #PUT
            for item in image_url:
                body = {
                    "projectId": projectId,
                    "chapterId": chapterId,
                    "paraId": paraId,
                    "localChapterId": localChapterId,
                    "localParaId": localParaId,
                    "url": item,
                    "selectedLayoutId": idx,
                    "id": image_id,
                    "taskType": 0,
                }
                requset_body.append(body)
            response = requests.put(self.request_url, headers=self.header, json=requset_body)
            try:
                response_msg = json.loads(response.text).get("msg", "")
            except Exception as err:
                response_msg = "get response msg error"
            logging.info(f"db upload result code: {response.status_code}, response msg: {response_msg}")
        else:
            for item in image_url:
                body = {
                    "projectId": projectId,
                    "chapterId": chapterId,
                    "paraId": paraId,
                    "localChapterId": localChapterId,
                    "localParaId": localParaId,
                    "url": item,
                    "selectedLayoutId": idx,
                    # "taskType": 0,
                    # "envPrompt": prompt,
                    # "imgId": image_id,
                    # "type": 1 if image_id else 0,  #类型，0： 段落，1： 图片
                    # "data": json.dumps(item, ensure_ascii = False)
                }
                requset_body.append(body)
                logging.info(f"body: {body}")
            response = requests.post(self.request_url, headers=self.header, json=requset_body)
            try:
                response_msg = json.loads(response.text).get("msg", "")
            except Exception as err:
                response_msg = "get response msg error"
            logging.info(f"db upload result code: {response.status_code}, response msg: {response_msg}")
        # sleep?

        return 
