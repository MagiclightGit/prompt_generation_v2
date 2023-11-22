import os
import time
import json
import mysql.connector
from mysql.connector import errorcode
import logging

class SQLOperator(object):
    def __init__(self, 
        host: str,
        user: str,
        password: str,
        db_name: str,
    ):
        self.config = {
            'host':host,
            'user':user,
            'password':password,
            'database':db_name
        }
        self.try_count = 3

	
    def WriteToTable(self, sql_cmd):
        flag = True
        for i in range(self.try_count):
            try:
                #建立连接
                self.conn = mysql.connector.connect(**self.config)
                #获取游标
                cursor = self.conn.cursor()
                #执行sql语句
                cursor.execute(sql_cmd)
                #data = cursor.fetchall()
                self.conn.commit()
                flag = True
                logging.info("write to table, sql cmd: {}, cur try_count: {}".format(sql_cmd, i+1))
                #关闭数据库连接
                self.conn.close()
            except Exception as err:
                flag = False
                self.conn.close()
                logging.error("write to sql failed, sql cmd: {}, err: {}, cur try count: {}".format(sql_cmd, str(err), i+1))
            if flag == True:
                break
        return flag

    def ReadFromTable(self, sql_cmd):
        flag = True
        for i in range(self.try_count):
            try:
                #建立连接
                self.conn = mysql.connector.connect(**self.config)
                #获取游标
                cursor = self.conn.cursor()
                #执行sql语句
                cursor.execute(sql_cmd)
                data = cursor.fetchall()
                flag = True
                logging.info("read to table, sql cmd: {}, cur try count: {}".format(sql_cmd, i+1))
                #关闭数据库连接
                self.conn.close()
                #return flag, data
            except Exception as err:
                flag = False
                data = []
                self.conn.close()
                logging.error("read to table failed, sql cmd: {}, err: {}, cur try count: {}".format(sql_cmd, str(err), i+1))
            if flag == True:
                break
        return flag, data
