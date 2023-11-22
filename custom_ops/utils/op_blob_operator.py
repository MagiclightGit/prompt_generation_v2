import logging
import os
import sys

import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient,ContentSettings

import json
import threading
import yaml
import traceback
import re
import time
from copy import deepcopy as copy
from tqdm import tqdm
from threading import Thread
from enum import IntFlag, Enum, auto
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path)


class AzureBlobOperator(object):
    def __init__(self, connection_str):
        self.connection_str = connection_str
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_str)

    def up_blob_storage(self, container_name, blob_name, content):
        flag = True
        try:
            # Get the container
            container_client = self.blob_service_client.get_container_client(container_name)
            # Get or create the blob
            blob_client = container_client.get_blob_client(blob_name)

            #print("upload file to blob storage: ", blob_name)
            if "png" in blob_name or "jpg" in blob_name:
                self.cnt_settings = ContentSettings(content_type="image/jpeg")
                blob_client.upload_blob(content,  content_settings= self.cnt_settings, overwrite=True)

            else:
                blob_client.upload_blob(content, overwrite=True)
            flag = True
        except Exception as e:
            logging.error(str(e))
            print("upload blob storage failed")
            flag = False
        return flag
            

    def download_blob_storage(self, container_name, blob_name):
        flag = True
        content = ''
        try:
            src_container_client = self.blob_service_client.get_container_client(container_name)
            #Read Config file from Blob Storage 
            config_blob_client = src_container_client.get_blob_client(blob_name)
            print("download config file from blob storage: pipeline.yaml")
            config_stream = config_blob_client.download_blob()
            
            for chunk in config_stream.chunks():
                content += str(chunk,'UTF-8')
            flag = True

        except Exception as e:
            logging.error(str(e))
            content = ''
            flag = False
        return flag, content