import logging.config,os,yaml,datetime

# 默认可存储文件配置
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

class TimedFilenameHandler(logging.FileHandler):
    """自定义文件处理器，文件名包含时间戳"""
    
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        # 在文件名中插入当前日期戳
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        base_name, ext = os.path.splitext(filename)
        timed_filename = f"{base_name}_{timestamp}{ext}"
        
        # 确保目录存在
        log_dir = os.path.dirname(timed_filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        super().__init__(timed_filename, mode, encoding, delay)

def init_logging(config_path="log.yaml"):
    dir_name = 'logs'
    os.makedirs(dir_name, exist_ok=True)
    
    # 首先尝试使用自定义的时间戳文件名处理器
    try:
        # 创建带日期戳的日志文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        log_filename = f"logs/desktopPet_{timestamp}.log"
        
        # 配置根日志器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器（带颜色）
        try:
            import colorlog
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)-8s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white'
                }
            )
        except ImportError:
            # 如果没有colorlog，使用普通格式
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            print("警告: 未安装colorlog，控制台日志将不带颜色")
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)
        
        # 设置文件处理器格式
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        print(f"日志已初始化，文件: {log_filename}")
        return
        
    except Exception as e:
        print(f"自定义日志初始化失败: {e}")
    
    # 如果自定义方式失败，回退到原有配置文件方式
    if os.path.exists(config_path):
        try:
            with open(config_path,'r',encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
                print("日志配置已从文件中加载成功")
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                handlers=[
                    logging.FileHandler('logs/desktopPet.log', encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            print("使用基础配置初始化日志")
    else:
        print("未找到配置文件，使用基础配置初始化日志")
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('logs/desktopPet.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

# init_logging()
# logging.info("日志初始化成功")