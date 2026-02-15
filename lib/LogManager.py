import logging.config,os,yaml

#默认可存储文件配置
default_config = {
    "log_file": "log.log",
    "log_level": "DEBUG",
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    "log_datefmt": "%Y-%m-%d %H:%M:%S",
    "log_dir": "log",
    "log_file_mode": "a",
    "log_file_max_size": 1024 * 1024 * 10,
    "log_file_backup_count": 7 
}

def init_logging(config_path="log.yaml"):
    dir_name = 'logs'
    os.makedirs(dir_name, exist_ok=True)
    if os.path.exists(config_path):
        try:
            with open(config_path,'r',encoding="utf-8") as f:
                config = yaml.safe_load(f) #载配置文件
                logging.config.dictConfig(config)
                print("日志配置已从文件中加载成功")

        except FileNotFoundError:
            print("未找到配置文件，使用默认配置初始化日志")
            logging.config.dictConfig(default_config)
            print("默认日志已初始化成功")
            
    else:
        print("未找到配置文件，使用默认配置初始化日志")
        logging.config.dictConfig(default_config)

# init_logging()
# logging.info("日志初始化成功")