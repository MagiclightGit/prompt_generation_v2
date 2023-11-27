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
        self.header = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }


    def run(self, inputs):
        projectId, chapterId, paraId, localChapterId, localParaId, image_url, idx = inputs

        if not image_url:
            logging.error(f"generate img failed! msg: img url is empty.")
            return
        
        # up to db
        requset_body = []
        for item in image_url:
            body = {
                "projectId": projectId,
                "chapterId": chapterId,
                "paraId": paraId,
                "localChapterId": localChapterId,
                "localParaId": localParaId,
                "url": item,
                "selectedLayoutId": idx,
                # "envPrompt": prompt,
                # "imgId": image_id,
                # "type": 1 if image_id else 0,  #类型，0： 段落，1： 图片
                # "data": json.dumps(item, ensure_ascii = False)
            }
            requset_body.append(body)
            # logging.info(f"body: {body}")
        response = requests.post(self.request_url, headers=self.header, json=requset_body)
        # logging.info(f"db upload result: {response}")
        # sleep?

        return 
