import json
import asyncio,os,re
import threading,subprocess,html
from openai import OpenAI 
import lib.LogManager as LogManager
import logging
from typing import Optional, Dict, Any
# MCP相关导入
from lib.mcp_manager import MCPManager
'''
AiAPI类
描述：AiAPI类用于处理与AI相关的功能，如获取AI回复、保存会话等。
支持MCP工具调用功能
'''

try:
    from lib.mcp_manager import MCPManager, create_mcp_manager
    MCP_ENABLED = True
except ImportError:
    MCP_ENABLED = False
    logging.warning("MCP管理器未找到，MCP功能将不可用")


class AiAPI:

    
    def __init__(self):
        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)
        self.gif_folder = None
        # self.which_ai = which_ai
        self.MODEL=''
        self.API_KEY=''
        # self.config = 
        self.BASE_URL = ''
        self._save_locks = {}
        self.LoadSetting()
        self.selectAi()
        
        # 初始化MCP管理器
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_enabled = False
        self.initialize_mcp()
        
        

    #用于加载配置文件
    def LoadSetting(self):
        try:
            with open("demo_setting.json","r",encoding="utf-8") as f:
                self.config = json.load(f)
                
                # 智能配置迁移：自动将旧格式转换为OpenAI格式
                migrated = False
                if "ai_key" in self.config and "openai_key" not in self.config:
                    self.config["openai_key"] = self.config["ai_key"]
                    self.config["openai_base_url"] = self.config.get("base_url", "https://open.bigmodel.cn/api/paas/v4/")
                    self.config["openai_model"] = self.config.get("model", "glm-4-flash")
                    migrated = True
                    self.logger.info("检测到旧配置格式，已自动迁移到OpenAI兼容格式")
                
                # 处理 api_provider 字段
                if "api_provider" in self.config:
                    del self.config["api_provider"]
                    migrated = True
                    self.logger.info("已移除旧的 api_provider 字段")
                
                # 强制使用OpenAI模式，移除智谱AI支持
                self.which_ai = "openai"
                self.API_KEY = self.config.get("openai_key", "")  # 使用openai_key字段
                self.BASE_URL = self.config.get("openai_base_url", "https://api.openai.com/v1")  # 支持自定义base_url
                self.MODEL = self.config.get("openai_model", "gpt-3.5-turbo")  # 使用openai_model字段
                
                # 如果进行了迁移，保存更新后的配置
                if migrated:
                    with open("demo_setting.json", "w", encoding="utf-8") as f_out:
                        json.dump(self.config, f_out, ensure_ascii=False, indent=2)
                    self.logger.info("配置文件已更新并保存")
                    
        except FileNotFoundError:
            self.logger.warning("未找到demo_setting.json文件，正在创建默认配置文件...")
            # 创建默认配置
            self.config = {
                "model": "gpt-3.5-turbo",
                "background_path": "",
                "transparency_img": 1.0,
                "luminance_img": 128,
                "gif_folder": "gif/猫",
                "openai_key": "",
                "openai_base_url": "https://api.openai.com/v1",
                "openai_model": "gpt-3.5-turbo",
                "api_type": "openai"
            }
            
            # 保存默认配置文件
            try:
                with open("demo_setting.json", "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                self.logger.info("默认配置文件已创建")
            except Exception as e:
                self.logger.error(f"创建配置文件失败: {e}")
            
            # 设置默认值
            self.which_ai = "openai"
            self.API_KEY = ""
            self.BASE_URL = "https://api.openai.com/v1"
            self.MODEL = "gpt-3.5-turbo"
            self.logger.info("程序将在无AI功能模式下运行，请在设置中配置API密钥")
    
    


    def initialize_mcp(self):
        """初始化MCP功能"""
        if not MCP_ENABLED:
            self.logger.info("MCP功能未启用")
            return
            
        try:
            # 在后台初始化MCP管理器
            def init_mcp_sync():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    self.mcp_manager = loop.run_until_complete(create_mcp_manager())
                    self.mcp_enabled = True
                    self.logger.info("MCP管理器初始化成功")
                except Exception as e:
                    self.logger.error(f"MCP管理器初始化失败: {e}")
                finally:
                    loop.close()
            
            # 使用线程避免阻塞主线程
            mcp_thread = threading.Thread(target=init_mcp_sync, daemon=True)
            mcp_thread.start()
            
        except Exception as e:
            self.logger.error(f"MCP初始化异常: {e}")
    
    def get_mcp_tools(self) -> list:
        """获取MCP工具列表（用于OpenAI工具调用）"""
        if not self.mcp_enabled or not self.mcp_manager:
            return []
        return self.mcp_manager.get_tools_for_openai()
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """调用MCP工具"""
        if not self.mcp_enabled or not self.mcp_manager:
            return None
        return await self.mcp_manager.call_tool(tool_name, arguments)
    def selectAi(self):
        """选择AI提供商"""
        # 只支持OpenAI模式
        self.client = OpenAI(
            api_key=self.API_KEY,
            base_url=self.BASE_URL
        )
        return "openai"
        
    async def init_mcp_connections(self):
        """初始化MCP连接"""
        return await self.mcp_manager.initialize()
    
    async def close_mcp_connections(self):
        """关闭MCP连接"""
        await self.mcp_manager.close()
        
    
    def _get_lock(self,identity):
        """
        获取指定标识符的线程锁对象
        
        该函数实现了一个锁的缓存机制，确保同一个标识符总是返回相同的锁对象，
        避免重复创建锁实例。
        
        Args:
            identity: 锁的唯一标识符，用于区分不同的锁
            
        Returns:
            threading.Lock: 对应标识符的线程锁对象
        """
        if identity not in self._save_locks:
            self._save_locks[identity] = threading.Lock()
        return self._save_locks[identity]

    def load_gif(self,gif_folder=None,dir_name="蜡笔小新组"):
        '''
        load_gif 的 Docstring
        
        :param gif_folder: GIF 文件夹路径
        :param dir_name: 文件夹名字

        '''
        # 从配置中获取GIF文件夹路径，如果没有指定则使用默认值
        if gif_folder is None:
            # 确保config属性存在
            if not hasattr(self, 'config'):
                self.config = {}
            
            try:
                gif_folder = self.config.get("gif_folder", f"gif/{dir_name}")
            except Exception:
                gif_folder = f"gif/{dir_name}"

        folder_path = gif_folder
        GifList = []
        try:
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        GifList.append({
                            "name": entry.name,
                            #注释掉是为了提高ai的识别率
                            # "path": os.path.join(folder_path, entry.name)
                        })
        except FileNotFoundError:
            # print(f"文件夹 '{folder_path}' 不存在。")
            self.logger.error(f"文件夹 '{folder_path}' 不存在。")
        except PermissionError:
            # print(f"没有权限访问文件夹 '{folder_path}'。")
            self.logger.error(f"没有权限访问文件夹 '{folder_path}'")
        return GifList 
    



    def load_img(self):
        folder_path = "imgs"
        ImgList = []
        
        # 检查当前工作目录
        current_dir = os.getcwd()
        # print(f"当前工作目录: {current_dir}")
        self.logger.debug(f"当前工作目录: {current_dir}")
        
        # 尝试不同的路径组合
        possible_paths = [
            folder_path,  # 相对路径
            os.path.join(current_dir, folder_path),  # 绝对路径
            os.path.join(os.path.dirname(__file__), folder_path),  # 相对于脚本位置
        ]
        
        found_path = None
        for path in possible_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            # print(f"找到 IMG 文件夹: {found_path}")
            self.logger.debug(f"找到 IMG 文件夹: {found_path}")
            try:
                with os.scandir(found_path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            ImgList.append({
                                "name": entry.name,
                            })
            except PermissionError:
                # print(f"没有权限访问文件夹 '{found_path}'。")
                self.logger.error(f"没有权限访问文件夹 '{found_path}'。")
        else:
            # print(f"IMG 文件夹 '{folder_path}' 不存在，正在创建该文件夹...")
            self.logger.warning(f"IMG 文件夹 '{folder_path}' 不存在，正在创建该文件夹...")
            # 创建文件夹（如果不存在）
            os.makedirs(folder_path, exist_ok=True)
            
        return ImgList
    


    def save_prompt(self,prompt):
        if prompt=="":
            prompt = "你叫丫丫，18岁女生，是个人,性格有趣且是否热情，回复要简短自然带点幽默"
        with open("prompt.txt", "w+", encoding="utf-8") as f:
            f.write(prompt)
            return prompt
        

    def update_prompt_from_file(self):
        '''
        解释: 从文件中更新提示
        '''
        if not os.path.exists("prompt.txt"):
            self.save_prompt("")
        try:
            prompt = open("prompt.txt", "r", encoding="utf-8").read()      
            return prompt
        except FileNotFoundError:
            # print("未找到prompt.txt文件，请检查文件是否存在")
            self.logger.error("未找到prompt.txt文件，请检查文件是否存在")
            return ""
        
    def load_conversation(self,identity="default"):
        '''
        load_conversation 的 Docstring
        
        解释: 加载指定标识符的会话记录
        '''

        GifList = self.load_gif()
        ImgList = self.load_img()
        filename = f"ai_memory/memory_{identity}.json"
        
        
        use_cmd = (
        "如果需要让助手执行Windows命令，必须严格用如下格式输出：[USE_cmd:你的命令]，"
        "中括号和冒号都不能省略，命令内容不能有多余内容。"
        "例如：[USE_cmd:dir] 或 [USE_cmd:py a.py]。"
        "不要用其它格式，否则命令不会被执行。"
        )
        open_app = (
            "如果需要打开程序,直接在桌面的路径下找软件的快捷方式，并打开指定的软件"
            '例如 C:\\\\path\\\\to\\\\your\\\\shortcut.lnk'
            "要严格尊守格式：[USE_cmd: C:\\\\path\\\\to\\\\your\\\\shortcut.lnk]"
            "注意:1.用户默认的用户名是Administrator,如果没有找到就询问,以上内容都要严格遵守"
            "2.对于中国软件商开发的软件，默认在公共用户的桌面下找"
            "3.对于微信则根据用户语言确定微信名,例如是中文的话就是微信，英文则是WeChat"
            "4.如果没有找到，就在公共用户的桌面这个路径下找，即用户再次询问打开某个软件时"
            

        )
        if os.path.exists("prompt.txt"):
            respon = self.update_prompt_from_file()
        else:
            respon = self.save_prompt("")
        sendGif = "你可以使用gif表达情感。注意：你所有的回答中都必须包含一个gif文件，且只能有这个。你还须了解你可以使用的gif文件。不能仅有gif文件，而没有文字"
        HowUseGif = "使用gif的格式为[GIF:文件名],例如[GIF:走路]"
        HowSendImg = "如果你需要发送表情包，请严格使用如下格式输出：[IMAGE_NAME: 图片文件名]，中括号和冒号都不能省略，图片文件名必须是存在于图片目录下的文件，否则无法发送图片。表情包并非必须每次都发送，只有在合适的情况下才发送。"
        DrawImg = "如果你需要生成图片，请严格使用如下格式输出：[DRAW: 你想要生成的图片内容描述]，中括号和冒号都不能省略，内容描述必须清晰，否则无法生成你想要的图片。绘画图片时仅能生成图片，不能生成文字。"

        if not os.path.exists(filename):
            return [{"role": "system", "content": f"{respon},{sendGif},{use_cmd},{open_app},{HowUseGif},可用的gif有{GifList};{HowSendImg},可用的图片有{ImgList},仅能发送里面有的图片;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。;{DrawImg}"}]
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                messages[0]["content"] = f"{respon},{sendGif},{use_cmd},{open_app},{HowUseGif},可用的gif有{GifList};{HowSendImg},可用的图片有{ImgList},仅能发送里面有的图片;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。;{DrawImg}"
                return messages
        except (json.JSONDecodeError, IOError) as e:
            # print(f"加载历史记录失败: {e}")
            self.logger.critical(f"加载历史记录失败: {e}")

    
    
    def save_conversation(self,identity, messages):
        '''
        save_conversation 的 Docstring
        
        :param identity: 表示对话的标识符，用于保存对话记录
        :param messages: 表示对话记录，是一个列表，每个元素是一个字典，包含"role"和"content"字段
        解释: 保存对话记录
        '''
        filename = f"ai_memory/memory_{identity}.json"
        lock = self._get_lock(identity)
        with lock:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2)
            except IOError as e:
                # print(f"保存对话失败: {e}")
                self.logger.critical(f"保存对话失败: {e}")

    
    def write_code_file(self,file_path, code_content):
        """将给定的内容写入指定文件路径，使用UTF-8编码"""
        try:
            # 验证内容是否可编码为UTF-8
            code_content.encode('utf-8').decode('utf-8')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            return f"文件已成功写入: {file_path}"
        except UnicodeError:
            return "检测到非法字符，请检查输入内容是否包含特殊符号（如\\uXXX）"
        except Exception as e:
            return f"写入文件失败: {e}"
        
    
    def get_ai_reply_stream(self,messages, callback=None):
        """流式获取AI回复，支持回调函数处理每部分输出"""
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                stream=True  # 启用流式输出
            )
            
            reply = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_part = chunk.choices[0].delta.content
                    reply += content_part
                    if callback:
                        callback(content_part)
                    else:
                        print(content_part, end='', flush=True)  # 实时打印流式输出
            
            print()  # 换行
            
            #提取gif
            pattern_filename = r'\[GIF:([^\]]+)\]'
            matches_filename = re.findall(pattern_filename,reply)

            #判断matches_filename是否为空
            if  not matches_filename:
                # print("未找到GIF文件名")
                self.logger.warning("未找到GIF文件名")
                matches_filename = ["走路"]

            # print("仅文件名:", matches_filename[0].replace(".gif", ""))
            self.logger.warning(f"仅文件名:{matches_filename[0].replace('.gif', '')}")

            

            # 移除GIF标记
            reply = reply.replace(f"[GIF:{matches_filename[0]}]", "")

            #去除空格
            reply = reply.strip()

            #读取demo_setting.json
            try:
                with open("demo_setting.json", "r", encoding="utf-8") as f:
                    demo_setting = json.load(f)
                    # print("读取到的demo_setting:", demo_setting)
                    self.logger.debug(f"读取到的demo_setting:{demo_setting}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # print(f"读取demo_setting.json失败: {e}")
                self.logger.error(f"读取demo_setting.json失败: {e}")

            #往读取到的demo_setting里添加gif键值对
            demo_setting["gif"] = matches_filename[0].replace(".gif", "")+".gif"

            #保存到demo_setting.json
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(demo_setting, f, ensure_ascii=False, indent=2)
                # print("已保存到demo_setting.json")
                self.logger.info("已保存到demo_setting.json")

            # 检查是否包含 [USE_cmd:xxx]
            use_cmd_pattern = r"\[USE_cmd:(.+?)\]"
            match = re.search(use_cmd_pattern, reply)


            
            if match:
                keyword = match.group(1).strip()
                
                # 匹配写入代码文件的特殊指令
                write_code_match = re.match(r"^write_code\s+([^\s]+)\s+([\s\S]+)$", keyword)
                if write_code_match:
                    file_name = write_code_match.group(1)
                    code_content = write_code_match.group(2)
                    if not code_content.strip():
                        result = f"未检测到有效代码内容，请用 write_code 指令并附上完整代码。"
                    else:
                        # 处理转义字符（如\u4e16 -> 世）
                        try:
                            code_content = code_content.encode('utf-8').decode('unicode_escape')
                        except Exception:
                            code_content = code_content.replace('\\n', '\n').replace('\\t', '\t')
                        result = self.write_code_file(file_name, code_content)
                    messages.append({"role": "user", "content": f"[USE_cmd:write_code]结果：{result}"})
                else:
                    # 新增：支持多条 echo >/>> 写入同一文件时自动合并内容
                    echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", keyword)
                    echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", keyword)
                    if echo_single_match or echo_append_match:
                        if not hasattr(self.get_ai_reply_sync, '_echo_cache'):
                            self.get_ai_reply_sync._echo_cache = {}
                        echo_cache = self.get_ai_reply_sync._echo_cache
                        if echo_single_match:
                            file_name = echo_single_match.group(2)
                            code_content = echo_single_match.group(1)
                            echo_cache[file_name] = [code_content]
                            result = f"准备写入: {file_name}"
                        elif echo_append_match:
                            file_name = echo_append_match.group(2)
                            code_content = echo_append_match.group(1)
                            if file_name not in echo_cache:
                                echo_cache[file_name] = []
                            echo_cache[file_name].append(code_content)
                            result = f"追加内容: {file_name}"
                        
                        # 立即写入（或等待下一条非echo命令）
                        next_is_echo = False
                        if len(messages) > 0 and isinstance(messages[-1], dict):
                            last_content = messages[-1].get('content', '')
                            if re.match(r"\[USE_cmd:echo", last_content):
                                next_is_echo = True
                        if not next_is_echo:
                            code_content_fixed = '\n'.join(echo_cache[file_name])
                            # 处理HTML实体和Unicode转义
                            code_content_fixed = html.unescape(code_content_fixed)
                            code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                            code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                            result = self.write_code_file(file_name, code_content_fixed)
                            messages.append({"role": "user", "content": f"[USE_cmd:echo]结果：{result}"})
                    else:
                        try:
                            # 执行系统命令并强制使用UTF-8编码
                            result = subprocess.run(
                                ["powershell", "-Command", keyword],
                                capture_output=True, text=True)
                            stdout = result.stdout.strip()
                            stderr = result.stderr.strip()
                            # 强制转换为UTF-8
                            stdout = stdout.encode('utf-8', errors='replace').decode('utf-8')
                            stderr = stderr.encode('utf-8', errors='replace').decode('utf-8')
                            cmd_result = ""
                            if stdout:
                                cmd_result += f"STDOUT:\n{stdout}\n"
                            if stderr:
                                cmd_result += f"STDERR:\n{stderr}\n"
                            cmd_result = cmd_result.strip()
                            final_result = f"命令执行完成: {keyword}\n{cmd_result}"
                        except Exception as e:
                            final_result = f"命令执行失败: {e}"
                        
                        messages.append({"role": "user", "content": f"[USE_cmd:{keyword}]结果：{final_result}"})
                
                # 再次请求AI
                response2 = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    stream=False  # 第二次请求不使用流式输出
                )
                if hasattr(response2, "choices") and response2.choices:
                    return response2.choices[0].message.content
                return "AI接口无有效回复(二次)"
            return reply
        except Exception as e:
            return f"AI请求失败: {e}"
            




    def _handle_tool_calls(self, messages: list, tool_calls, initial_reply: str) -> str:
        """处理工具调用"""
        # 添加初始回复到消息历史
        if initial_reply:
            messages.append({
                "role": "assistant", 
                "content": initial_reply
            })
        
        # 处理每个工具调用
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}
            
            self.logger.info(f"调用工具: {func_name} 参数: {func_args}")
            
            # 调用MCP工具
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tool_result = loop.run_until_complete(
                    self.call_mcp_tool(func_name, func_args)
                )
            finally:
                loop.close()
            
            if tool_result is None:
                tool_result = f"工具 {func_name} 调用失败"
            
            # 将工具结果添加到消息历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })
        
        # 再次请求AI，让其基于工具结果生成回复
        try:
            response2 = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                stream=False
            )
            if hasattr(response2, "choices") and response2.choices:
                final_reply = response2.choices[0].message.content
                return self._post_process_reply(final_reply or "")
            return "AI接口无有效回复(工具调用后)"
        except Exception as e:
            return f"AI请求失败(工具调用后): {e}"
    
    def _post_process_reply(self, reply: str) -> str:
        """后处理AI回复"""
        #提取gif
        pattern_filename = r'\[GIF:([^\]]+)\]'
        matches_filename = re.findall(pattern_filename, reply)

        #判断matches_filename是否为空
        if not matches_filename:
            self.logger.warning("未找到GIF文件名")
            matches_filename = ["走路"]

        self.logger.warning(f"仅文件名: {matches_filename[0].replace('.gif', '')}")

        # 移除GIF标记
        reply = reply.replace(f"[GIF:{matches_filename[0]}]", "")

        #去除空格
        reply = reply.strip()

        #读取demo_setting.json
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                demo_setting = json.load(f)
                self.logger.debug(f"读取到的demo_setting:{demo_setting}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"读取demo_setting.json失败: {e}")

        #往读取到的demo_setting里添加gif键值对
        demo_setting["gif"] = matches_filename[0].replace(".gif", "")+".gif"

        #保存到demo_setting.json
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(demo_setting, f, ensure_ascii=False, indent=2)
            self.logger.info("已保存到demo_setting.json")
        
        return reply

    def get_ai_reply_sync(self,messages):
        """同步方式获取AI回复,返回字符串。自动处理[SEARCH_MCP:xxx]指令"""
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages
            )
            if hasattr(response, "choices") and response.choices:
                reply = response.choices[0].message.content
                # print(reply)
                self.logger.debug(f"{reply}")

                #提取gif
                pattern_filename = r'\[GIF:([^\]]+)\]'
                matches_filename = re.findall(pattern_filename,reply)

                #判断matches_filename是否为空
                if  not matches_filename:
                    # print("未找到GIF文件名")
                    self.logger.warning("未找到GIF文件名")
                    matches_filename = ["走路"]

                # print("仅文件名:", matches_filename[0].replace(".gif", ""))
                self.logger.warning(f"仅文件名: {matches_filename[0].replace('.gif', '')}")

                

                # 移除GIF标记
                reply = reply.replace(f"[GIF:{matches_filename[0]}]", "")

                #读取demo_setting.json
                try:
                    with open("demo_setting.json", "r", encoding="utf-8") as f:
                        demo_setting = json.load(f)
                        # print("读取到的demo_setting:", demo_setting)
                        self.logger.debug(f"读取到的demo_setting:{demo_setting}")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    # print(f"读取demo_setting.json失败: {e}")
                    self.logger.error(f"读取demo_setting.json失败: {e}")

                #往读取到的demo_setting里添加gif键值对
                demo_setting["gif"] = matches_filename[0].replace(".gif", "")+".gif"

                #保存到demo_setting.json
                with open("demo_setting.json", "w", encoding="utf-8") as f:
                    json.dump(demo_setting, f, ensure_ascii=False, indent=2)

                # 检查是否包含 [USE_cmd:xxx]
                use_cmd_pattern = r"\[USE_cmd:(.+?)\]"
                match = re.search(use_cmd_pattern, reply)


                
                if match:
                    keyword = match.group(1).strip()
                    
                    # 匹配写入代码文件的特殊指令
                    write_code_match = re.match(r"^write_code\s+([^\s]+)\s+([\s\S]+)$", keyword)
                    if write_code_match:
                        file_name = write_code_match.group(1)
                        code_content = write_code_match.group(2)
                        if not code_content.strip():
                            result = f"未检测到有效代码内容，请用 write_code 指令并附上完整代码。"
                        else:
                            # 处理转义字符（如\u4e16 -> 世）
                            try:
                                code_content = code_content.encode('utf-8').decode('unicode_escape')
                            except Exception:
                                code_content = code_content.replace('\\n', '\n').replace('\\t', '\t')
                            result = self.write_code_file(file_name, code_content)
                        messages.append({"role": "user", "content": f"[USE_cmd:write_code]结果：{result}"})
                    else:
                        # 新增：支持多条 echo >/>> 写入同一文件时自动合并内容
                        echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", keyword)
                        echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", keyword)
                        if echo_single_match or echo_append_match:
                            if not hasattr(self.get_ai_reply_sync, '_echo_cache'):
                                self.get_ai_reply_sync._echo_cache = {}
                            echo_cache = self.get_ai_reply_sync._echo_cache
                            if echo_single_match:
                                file_name = echo_single_match.group(2)
                                code_content = echo_single_match.group(1)
                                echo_cache[file_name] = [code_content]
                                result = f"准备写入: {file_name}"
                            elif echo_append_match:
                                file_name = echo_append_match.group(2)
                                code_content = echo_append_match.group(1)
                                if file_name not in echo_cache:
                                    echo_cache[file_name] = []
                                echo_cache[file_name].append(code_content)
                                result = f"追加内容: {file_name}"
                            
                            # 立即写入（或等待下一条非echo命令）
                            next_is_echo = False
                            if len(messages) > 0 and isinstance(messages[-1], dict):
                                last_content = messages[-1].get('content', '')
                                if re.match(r"\[USE_cmd:echo", last_content):
                                    next_is_echo = True
                            if not next_is_echo:
                                code_content_fixed = '\n'.join(echo_cache[file_name])
                                # 处理HTML实体和Unicode转义
                                code_content_fixed = html.unescape(code_content_fixed)
                                code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                                code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                                result = self.write_code_file(file_name, code_content_fixed)
                                messages.append({"role": "user", "content": f"[USE_cmd:echo]结果：{result}"})
                        else:
                            try:
                                # 执行系统命令并强制使用UTF-8编码
                                result = subprocess.run(
                                    ["powershell", "-Command", keyword],
                                    capture_output=True, text=True)
                                stdout = result.stdout.strip()
                                stderr = result.stderr.strip()
                                # 强制转换为UTF-8
                                stdout = stdout.encode('utf-8', errors='replace').decode('utf-8')
                                stderr = stderr.encode('utf-8', errors='replace').decode('utf-8')
                                cmd_result = ""
                                if stdout:
                                    cmd_result += f"STDOUT:\n{stdout}\n"
                                if stderr:
                                    cmd_result += f"STDERR:\n{stderr}\n"
                                cmd_result = cmd_result.strip()
                                final_result = f"命令执行完成: {keyword}\n{cmd_result}"
                            except Exception as e:
                                final_result = f"命令执行失败: {e}"
                            
                            messages.append({"role": "user", "content": f"[USE_cmd:{keyword}]结果：{final_result}"})
                    
                    # 再次请求AI
                    response2 = self.client.chat.completions.create(
                        model=self.MODEL,
                        messages=messages
                    )
                    if hasattr(response2, "choices") and response2.choices:
                        return response2.choices[0].message.content
                    return "AI接口无有效回复(二次)"
                return reply
                return reply
            return "AI接口无有效回复"
        except Exception as e:
            return f"AI请求失败: {e}"

    
    async def get_ai_reply_with_mcp(self, messages):
        """支持MCP工具调用的AI回复方法"""
        # 确保MCP连接已初始化
        if not self.mcp_manager.is_initialized():
            initialized = await self.init_mcp_connections()
            if not initialized:
                # MCP不可用时回退到普通模式
                return await self.get_ai_reply(messages)
        
        try:
            # 构造包含MCP工具的请求
            request_params = {
                "model": self.MODEL,
                "messages": messages,
                "stream": True
            }
            
            # 如果有MCP工具，添加到请求中
            openai_tools = self.mcp_manager.get_openai_tools()
            if openai_tools:
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
            
            # 发起流式请求
            response = self.client.chat.completions.create(**request_params)
            
            collected_content = ""
            collected_tool_calls = {}
            finish_reason = None
            
            async for chunk in response:
                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason
                
                # 处理普通内容
                if delta.content:
                    collected_content += delta.content
                    
                # 处理工具调用
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in collected_tool_calls:
                            collected_tool_calls[idx] = {
                                "id": None,
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc_delta.id:
                            collected_tool_calls[idx]["id"] = tc_delta.id
                        if tc_delta.function.name:
                            collected_tool_calls[idx]["function"]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            collected_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments
                            
                # 遇到finish_reason表示本轮生成结束
                if finish_reason:
                    break
            
            # 构建本轮助手消息
            assistant_msg = {
                "role": "assistant",
                "content": collected_content
            }
            
            # 处理工具调用
            if collected_tool_calls:
                tool_calls_list = []
                for idx in sorted(collected_tool_calls.keys()):
                    tc = collected_tool_calls[idx]
                    tool_calls_list.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    })
                assistant_msg["tool_calls"] = tool_calls_list
                
                # 执行工具调用
                for tool_call in tool_calls_list:
                    func_name = tool_call["function"]["name"]
                    try:
                        func_args = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError as e:
                        self.logger.error(f"工具参数解析失败: {e}")
                        continue
                        
                    self.logger.info(f"调用MCP工具 {func_name} 参数: {func_args}")
                    
                    try:
                        result = await self.mcp_manager.call_tool(func_name, func_args)
                        content = result
                    except Exception as e:
                        content = f"工具调用失败: {e}"
                        self.logger.error(f"MCP工具调用失败: {e}")
                    
                    # 将工具结果加入消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": content
                    })
                
                # 让AI根据工具结果进一步回应
                return await self.get_ai_reply_with_mcp(messages)
            
            return collected_content
            
        except Exception as e:
            self.logger.error(f"AI请求失败: {e}")
            return f"AI请求失败: {e}"
    

    def chat_round(self,messages):
        try:
            while True:
                user_input = input("\n你：").strip()
                if user_input:
                    break
                print("输入不能为空,请重新输入")
            messages.append({"role": "user", "content": user_input})
            reply = self.get_ai_reply_sync(messages)
            messages.append({"role": "assistant", "content": reply})
            print(f"\n助手：{reply}")
        except Exception as e:
            print(f"对话出错: {e}")


    def write_code_file(self,file_path, code_content):
        """将给定的内容写入指定文件路径，使用UTF-8编码"""
        try:
            # 验证内容是否可编码为UTF-8
            code_content.encode('utf-8').decode('utf-8')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            return f"文件已成功写入: {file_path}"
        except UnicodeError:
            return "检测到非法字符，请检查输入内容是否包含特殊符号（如\\uXXX）"
        except Exception as e:
            return f"写入文件失败: {e}"

    def get_ai_reply_sync_with_mcp(self, messages):
        """同步方式获取AI回复（支持MCP），返回字符串"""
        try:
            # 尝试异步调用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reply = loop.run_until_complete(self.get_ai_reply_with_mcp(messages))
                return reply
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"同步MCP调用失败: {e}")
            # 回退到普通同步调用
            return self.get_ai_reply_sync(messages)


'''
不想写
'''
# def main():
#     ai_api = AiAPI()
#     print("=== 对话开始 (输入q退出) ===")
#     identity = input("请输入身份标识（或直接回车使用默认身份）: ").strip() or "default"
#     messages = ai_api.load_conversation(identity)
#     ai_api.update_prompt_from_file()
#     ai_api.load_gif()
#     ai_api.load_img()
#     ai_api.chat_round(messages)