import json
from copy import deepcopy

import logging
import requests
import os

#通过url下载数据
def DownloadByUrl(url, file_name):
    r = requests.get(url)
    res = {
        "code": 0,
        "msg": "succ",
        "file_path": ""
    }
    if r.status_code != 200:
        msg = "download file failed, url: {}".format(url)
        logging.error("msg: {}".format(msg))
        res['code'] = 1
        res['msg'] = msg
        res['file_path'] = ""
        return res
    local_path = "./tmp/" + file_name

    if os.path.exists(local_path) == False:
        with open(local_path, 'wb') as fwt:
            fwt.write(r.content)
            fwt.close()
     
    res["file_path"] = local_path
    return res