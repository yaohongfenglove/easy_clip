import json
import logging
import os
from logging.handlers import RotatingFileHandler


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ########## 加载配置
def load_config():
    config_path = os.path.join(BASE_DIR, "conf/config.json")
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')

    with open(config_path, mode='r', encoding='utf-8') as f:
        config_str = f.read()

    # 将json字符串反序列化为dict类型
    conf = json.loads(config_str)

    return conf


config = load_config()


# 如果输出文件夹不存在，则创建
output_dir_path = os.path.join(BASE_DIR, "output")
if not os.path.isdir(output_dir_path):
    os.makedirs(output_dir_path)


# ########## 日志配置
# 如果日志文件夹不存在，则创建
log_dir_path = os.path.join(BASE_DIR, "logs")
if not os.path.isdir(log_dir_path):
    os.makedirs(log_dir_path)

MAX_BYTES = 1024 * 1024 * 250  # 每个日志文件最大250M
BACKUP_COUNT = 4  # 最多4个日志文件

# 1.默认的logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Log等级总开关 CRITICAL > ERROR > WARNING > INFO > DEBUG

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")

# 打印到文件
file_handler = RotatingFileHandler(filename=os.path.join(log_dir_path, "log.log"), mode="a",
                                   maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
file_handler.setLevel(logging.INFO)  # 输出到file的log等级的开关
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 打印到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
if config["environment"] == "debug":
    logger.addHandler(console_handler)

# 2.sql的logger
# 预留


if __name__ == '__main__':
    print(config)
