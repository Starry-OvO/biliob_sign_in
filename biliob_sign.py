#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Author: Starry
@License: MIT

从你的浏览器复制消息头到headers文件夹下的*.txt
或使用-hp指定消息头文本文件所在的文件夹
在headers文件夹内放置多个txt以实现多账号签到

每8小时运行一次该脚本
sched和last success记录可以完美解决服务器延时的问题
示例: 17 */8 * * * . /etc/profile; python biliob_sign.py

Enjoy :)
"""


import os
import sys
import time
import sched
import logging
from functools import wraps
from threading import Timer

import re
import json

import requests as req



def retry(_retry_times,sleep_time):
    """
    Decorator to retry a function
    @retry(_retry_times,sleep_time)

    Parameters:
        _retry_times:int How much times to retry
        sleep_time:int How much time to sleep
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args,**kwargs):

            retry_times = _retry_times
            while retry_times:
                flag,res = func(*args,**kwargs)
                if flag:
                    break
                else:
                    retry_times-=1
                    time.sleep(sleep_time)
                    print(1)

            return flag,res

        return wrapped_func

    return decorator



class _Headers(object):
    """
    消息头
    """


    __slots__ = ('headers','cookies')


    def __init__(self,filepath):
        self.update(filepath)


    def update(self,filepath:str):
        """
        Read headers.txt and return the dict of headers.
        read_headers_file(filepath)

        Parameters:
            filepath:str Path of the headers.txt
        """

        self.headers = {}
        self.cookies = {}
        try:
            with open(filepath,'r',encoding='utf-8') as header_file:
                rd_lines = header_file.readlines()
                for text in rd_lines:
                    if re.match('GET|POST',text):
                        continue
                    else:
                        text = text.replace('\n','').split(':',1)
                        self.headers[text[0].strip().capitalize()] = text[1].strip()
        except(FileExistsError):
            raise(FileExistsError('headers.txt not exist! Please create it from browser!'))

        if self.headers.__contains__('Referer'):
            del self.headers['Referer']
        if self.headers.__contains__('Cookie'):
            for text in self.headers['Cookie'].split(';'):
                text = text.strip().split('=')
                self.cookies[text[0]] = text[1]
        else:
            raise(AttributeError('raw_headers["cookies"] not found!'))


    def _set_host(self,url):
        try:
            self.headers['Host'] = re.search('://(.+?)/',url).group(1)
        except AttributeError:
            return False
        else:
            return True



class Sign(object):


    __slots__ = ('headers_list',
                 'log',
                 'record_dict')


    def __init__(self,filepaths:list):
        self.create_logger()
        self.headers_list = [_Headers(filepath) for filepath in filepaths]

        try:
            with open(PATH + '/log/last_success.json','r',encoding='utf-8') as record_file:
                self.record_dict = json.loads(record_file.read())
        except(FileNotFoundError):
            self.record_dict = {}


    def quit(self):
        with open(PATH + '/log/last_success.json','w',encoding='utf-8') as record_file:
            _str = json.dumps(self.record_dict,ensure_ascii=False,indent=2,separators=(',',':'))
            record_file.write(_str)


    def create_logger(self):
        if not os.path.exists(PATH + '/log'):
            os.mkdir(PATH + '/log')
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        log_filepath = '{path}/log/biliob_sign_{time}.log'.format(path=PATH,time=recent_time)
        try:
            file_handler = logging.FileHandler(log_filepath,encoding='utf-8')
        except(PermissionError):
            try:
                os.remove(log_filepath)
            except(OSError):
                raise(OSError('''Can't write and remove {path}'''.format(path=log_filepath)))
            else:
                file_handler = logging.FileHandler(log_filepath,encoding='utf-8')

        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler.setLevel(logging.INFO)
        stream_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("<%(asctime)s> [%(levelname)s]  %(message)s","%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)

        self.log = logging.getLogger(__name__)
        self.log.addHandler(file_handler)
        self.log.addHandler(stream_handler)
        self.log.setLevel(logging.DEBUG)

        
    def run(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        for index in range(len(self.headers_list)):
            delay = self._get_last_success(index) + 29100 - time.time()  # delay 8h5min
            scheduler.enter(delay, 0, self.sign, (index,))
        scheduler.run()


    def sign(self,index):
        flag,res = self.__sign(index)
        if flag:
            self._record_last_success(index)
            self.log.info(res)
        else:
            self.log.error(res)


    @retry(5,20)
    def __sign(self,index:int):
        """
        Get sign in BiliOB
        sign(headers)

        Parameters:
            headers:dict How much times to retry
        """

        if index > len(self.headers_list) - 1:
            self.log.error('Index out of range!')
            return False,'Index out of range!'

        try:
            res = req.post('https://www.biliob.com/api/user/check-in',
                           headers=self.headers_list[index].headers)
        except(req.exceptions.RequestException):
            return False,''
        else:
            if res.status_code == 200:
                return True,res.text
            else:
                return False,res.text


    def _get_last_success(self,index):
        session = self.headers_list[index].cookies['SESSION']
        return self.record_dict.get(session,0)


    def _record_last_success(self,index):
        if index > len(self.headers_list) - 1:
            self.log.error('Index out of range!')
            return False,'Index out of range!'

        recent_time = time.time()

        session = self.headers_list[index].cookies['SESSION']
        self.record_dict[session] = recent_time


    @staticmethod
    def timestamp2str(timestamp):
        time_local = time.localtime(timestamp)
        _str = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
        return _str


    @staticmethod
    def _str2timestamp(_str):
        timeArray = time.strptime(_str, "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(timeArray)
        return timestamp



if __name__ == '__main__':
    PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

    import argparse
    parser = argparse.ArgumentParser(description='Sign in BiliOB')
    parser.add_argument('--headers_dir', '-hd',type=str,default= PATH + '/headers', help='path of the headers dir | default value is .')
    kwargs = vars(parser.parse_args())

    filenames = os.listdir(kwargs['headers_dir'])
    filepaths = [os.path.join(kwargs['headers_dir'],filename) for filename in filenames if filename.endswith('.txt')]

    sign = Sign(filepaths)
    sign.run()
    sign.quit()