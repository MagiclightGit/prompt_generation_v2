import os
import os.path as osp
import sys
import logging
import json
import requests
import yaml
import boto3
import pathlib

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path)

# from op_sql_operator import SQLOperator
from custom_ops.utils.sql_operator import SQLOperator

#函数名：sqs队列
#输入参数1: 队列url
#输入参数2: 类型
#输入参数3: 队列区域
#输入参数4: 取队列数量
def SqsQueue(
    url = "https://sqs.us-east-1.amazonaws.com/647854334008/LoraTrain-TaskDeque-Normal", 
    region_name_str = "us-east-1",
    max_number_of_mess = 3,
    operator_type = "get",
    mess = ''):
    sqs = boto3.client("sqs", region_name= region_name_str)
    #url = 'https://sqs.us-east-1.amazonaws.com/647854334008/IPBible_TaskQueue_Normal'
    '''
    message = {"key" : "value"}
    reponse = sqs.send_message(
        QueueUrl = url,
        MessageBody=json.dumps(message)
    )
    print("发送信息: {}".format(reponse))
    '''

    inputs = []
    if operator_type == "get":
        reponse = sqs.receive_message(
            QueueUrl = url,
            MaxNumberOfMessages = 3,
            WaitTimeSeconds=10,
        )
        #print("接收信息: {}".format(reponse))
        try:
            msg = reponse['Messages']
            for info in msg:
                #获取数据
                receipt_handle = info['ReceiptHandle']
                body = info['Body']
                inputs.append(body)
                #删除数据
                response = sqs.delete_message(
                    QueueUrl = url,
                    ReceiptHandle=receipt_handle,
                )
                #print("删除队列: {}".format(response))
        except:
            logging.info("sqs queue len equal to 0")
    elif operator_type == "put":
        try:
            reponse = sqs.send_message(
                QueueUrl = url,
                MessageBody= mess
            )
            inputs.append(reponse)
            #print("发送信息: {}".format(reponse))
        except Exception as err:
            logging.error("发送信息失败, mess: {}, err: {}".format(mess, err))
    return inputs

#解析配置文件
def YamlParse(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    server_conf = data['server_config']

    src_deque_conf = server_conf['src_deque_conf']
    sql_conf = server_conf['sql_conf']
    dst_deque_conf = server_conf['dst_deque_conf']
    return src_deque_conf, sql_conf, dst_deque_conf

#sql配置
def SQLConfig(sql_type):
    sql_type = "amazon"
    if sql_type == "azure":
        host= 'mysqldb01.mysql.database.azure.com'
        user = 'azure_admin'
        password = '28#uEQ3z496K'
        database= 'script-light'
    elif sql_type == "amazon":
        host = "prototype.cdtoyz6oo1ls.rds.cn-north-1.amazonaws.com.cn"
        #host = "script-light.cluster-cdtoyz6oo1ls.rds.cn-north-1.amazonaws.com.cn"
        user = "admin"
        #password = "dream-big1000"
        password = "dreambigger234"
        database = "prototype"

    sql = SQLOperator(host, user, password, database)
    return sql

def DownloadByUrl(ipbible_url, type):
    r = requests.get(ipbible_url)
    res = {
        "code": 0,
        "msg": "succ",
        "file_path": ""
    }
    
    if r.status_code != 200:
        msg = "download file failed, fic_path: {}".format(ipbible_url)
        logging.error("msg: {}".format(msg))
        res['code'] = 1
        res['msg'] = msg
        res['file_path'] = ""
        return res
    pathlib.Path('./tmp/').mkdir(exist_ok=True)
    if type == 1:
        fic_path = "./tmp/ipbible_" + ipbible_url.split('/')[-1]
    elif type == 2:
        fic_path = "./tmp/layout_" + ipbible_url.split('/')[-1]
    if os.path.exists(fic_path) == False:
        with open(fic_path, 'wb') as fwt:
            fwt.write(r.content)
            fwt.close()
     
    res["file_path"] = fic_path
    return res

def GetInputInfo(project_id, fid, chid, para_id, flow_id, sql ,sql_type):
    ipbible_url = "https://testdocsplitblobtrigger.blob.core.windows.net/layout-in/fiction_{}_{}_{}.json".format(fid, chid, flow_id)

    try_cnt = 3

    #get para_id model info
    ipbible_download_res = DownloadByUrl(ipbible_url, 1)
    if ipbible_download_res['code'] == 0:
        ipbible_path = ipbible_download_res['file_path']
    else:
        ipbible_path = ''
    logging.info("ipbible_path: {}".format(ipbible_path))
    
    with open(ipbible_path,'r') as frd:
        data = json.load(frd)
    chapter_info = data.get("chapter_info",'{}')
    paras = chapter_info.get("paras",'[]')

    model_info = {}
    for para in paras:
        id = para['para_id']
        if id != para_id:
            continue
        roles = para['roles']
        for role in roles:
            role_id = role['id']
            if sql_type == "azure":
                lora_sql_cmd = "select lora_id from world_view \
                    where fiction_id = '{}' and entity_id='{}' \
                    order by update_time desc limit 1".format(
                        fid, role_id)
            elif sql_type == "amazon":
                lora_sql_cmd = "select lora_id from t_world_building \
                    where fid = '{}' and entity_id='{}' \
                    order by update_time desc limit 1".format(
                        fid, role_id)
            logging.info("lora_sql_cmd: {}".format(lora_sql_cmd))
     
            flag, query_res = sql.ReadFromTable(lora_sql_cmd)
            if flag == True and len(query_res) >0:
                lora_id = query_res[0][0]
            else:
                lora_id = ''
            
            if sql_type == "azure":
                model_info_sql_cmd = "select lora_model_info,lora_model_url, config_url, demo_url \
                    from roles_lora where lora_id = '{}' \
                    order by update_time desc limit 1;".format(lora_id)
            elif sql_type == "amazon":
                model_info_sql_cmd = "select lora_model_info,lora_model_url, configs_url, demo_url \
                    from t_roles_lora where lora_id = '{}' \
                    order by update_time desc limit 1;".format(lora_id)

            #增加重试
            logging.info("model_info_sql_cmd: {}".format(model_info_sql_cmd))   
            flag, query_res = sql.ReadFromTable(model_info_sql_cmd)
            
            if flag == True and len(query_res) >0:
                lora_model_info = query_res[0][0]
                lora_model_url = query_res[0][1]
                config_url = query_res[0][2]
                demo_url = query_res[0][3]
            else:
                lora_model_info = '{}'
                lora_model_url = ''
                config_url = ''
                demo_url = ''
            '''
            if id not in model_info:
                model_info[id] = json.dumps(lora_model_info, ensure_ascii = False)
            '''
            if role_id not in model_info: 
                model_info[role_id] = json.dumps(lora_model_info, ensure_ascii = False)
    logging.info("\t\t model_info: {}".format(model_info))
    return ipbible_path, json.dumps(model_info, ensure_ascii = False)


def get_magiclight_api(paraId, chapterId, projectId, imgId, type_="0", db="layout"):
    url = "http://test.magiclight.ai/api/"
    header = {
            'accept': 'application/json',
        }
    
    params = {
        'type': type_,
        'paraId': paraId,
        'chapterId': chapterId,
        'projectId': projectId,
    }

    response = requests.get(f"{url}{db}", params=params, headers=header)
    res = [] 
    if response.status_code != 200:
        logging.error(f"msg: get api failed. projectId: {projectId}, chapterId: {chapterId}, paraId: {paraId}")
        return res
    
    # response.content
    try:
        data = json.loads(response.content)
        msg = data['data']
        for info in msg:
            #获取数据
            item = info['data']
            res.append(item)

    except:
        logging.info("db data len equal to 0")

    return res
