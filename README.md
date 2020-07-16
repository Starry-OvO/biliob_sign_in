# BiliOB 签到脚本
## 特点
+ 功能简单，但脚本非常pythonic，值得分享学习
## 准备工作
+ 把签到请求的**消息头**从你的浏览器复制到同一文件夹下的**headers.txt**（命令行参数默认指定的位置），**不需要做任何修改**，脚本会自动将其读取为dict。当然你也可以指定其他位置的headers.txt
+ 每8小时运行一次脚本
+ crontab设置示例 0 */8 * * * . /etc/profile; python biliob_sign.py
