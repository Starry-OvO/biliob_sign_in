#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Author: Starry
@License: MIT

Copy your headers to [./headers.txt] from your browser
Run this script every 8 hours
Enjoy :)
"""


import os
import time
import logging

from functools import wraps

import requests as req


def read_headers_file(filepath:str):
    """
    Read headers.txt and return the dict of headers.
    read_headers_file(filepath)

    Parameters:
        filepath:str Path of the headers.txt
    """
    try:
        with open(filepath,'r',encoding='utf-8') as header_file:
            rd_lines = header_file.readlines()
            header_textlist = [text.replace('\n','').split(':',1) for text in rd_lines]
            return {text[0].strip():text[1].strip() for text in header_textlist}
    except(FileExistsError):
        raise(FileExistsError('headers.txt not exist! Please create it from browser!'))


def create_logger():
    recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    log_filepath = '{path}/biliob_sign_{time}.log'.format(path=PATH,time=recent_time)

    try:
        file_handler = logging.FileHandler(log_filepath,encoding='utf-8')
    except(PermissionError):
        try:
            os.remove(log_filepath)
        except(OSError):
            raise(OSError('''Can't write and remove {path}'''.format(path=log_filepath)))
        else:
            file_handler = logging.FileHandler(log_filepath,encoding='utf-8')

    formatter = logging.Formatter("<%(asctime)s> [%(levelname)s]  %(message)s","%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)

    log = logging.getLogger(__name__)
    log.addHandler(file_handler)
    log.setLevel(logging.INFO)

    return log


def retry(func,_retry_times,sleep_time):
    """
    Decorator to retry a function
    @retry(_retry_times,sleep_time)

    Parameters:
        _retry_times:int How much times to retry
        sleep_time:int How much time to sleep
    """
    @wraps(func)
    def wrap_func(*args,**kwargs):

        retry_times = _retry_times
        while retry_times:
            flag,res = func(*args,**kwargs)
            if flag:
                break
            else:
                retry_times-=1
                time.sleep(sleep_time)

        return flag,res

    return wrap_func


@retry(20,10)
def sign(headers:dict):
    """
    Get sign in BiliOB
    sign(headers)

    Parameters:
        headers:dict How much times to retry
    """
    try:
        res = req.post('https://www.biliob.com/api/user/check-in',headers=headers)
    except(req.exceptions.RequestException):
        return False,''
    else:
        if res.status_code == 200:
            return True,res.text
        else:
            return False,res.text


if __name__=='__main__':
    PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

    import argparse
    parser = argparse.ArgumentParser(description='Sign in BiliOB')
    parser.add_argument('--header_filepath', '-hp',type=str,default= PATH + '/headers.txt', help='path of the headers txt | default value is ./headers.txt')
    kwargs = vars(parser.parse_args())

    headers = read_headers_file(kwargs['header_filepath'])

    log = create_logger()

    flag,res = sign(headers)

    if flag:
        log.info(res)
    else:
        log.error(res)