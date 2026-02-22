import json
import asyncio
import os
import re
import threading
import subprocess
import html
from typing import Optional, Dict, Any, Callable
from openai import OpenAI
from stegano import tools
import lib.LogManager as LogManager
import logging
from lib.getWeather import MSWeather
from lib.user_ip import UserIP
from plugins_manage import PluginManager
from lib.ues_skills import UESkills

# MCP 相关导入
try:
    from lib.mcp_manager import MCPManager, create_mcp_manager
    MCP_ENABLED = True
except ImportError:
    MCP_ENABLED = False
    logging.warning("MCP管理器未找到，MCP功能将不可用")


class AiAPI:
    """
    AiAPI类
    描述：处理与AI相关的功能，如获取AI回复、保存会话等。
    支持MCP工具调用功能。
    """

    def __init__(self):
        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)
        self.gif_folder = None
        self.MODEL = ''
        self.API_KEY = ''
        self.BASE_URL = ''
        self._save_locks = {}
        self.config = {}
        self.LoadSetting()
        self.selectAi()

        # MCP 相关
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_enabled = False
        self._mcp_initialized_event = threading.Event()  # 用于等待MCP初始化完成
        self.initialize_mcp()

    # ---------- 配置加载 ----------
    def LoadSetting(self):
        """加载配置文件，兼容旧格式并强制使用OpenAI模式"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)

                # 智能配置迁移：自动将旧格式转换为OpenAI格式
                migrated = False
                if "ai_key" in self.config and "openai_key" not in self.config:
                    self.config["openai_key"] = self.config["ai_key"]
                    self.config["openai_base_url"] = self.config.get("base_url", "https://open.bigmodel.cn/api/paas/v4/")
                    self.config["openai_model"] = self.config.get("model", "glm-4-flash")
                    migrated = True
                    self.logger.info("检测到旧配置格式，已自动迁移到OpenAI兼容格式")

                if "api_provider" in self.config:
                    del self.config["api_provider"]
                    migrated = True
                    self.logger.info("已移除旧的 api_provider 字段")

                # 强制使用OpenAI模式
                self.which_ai = "openai"
                self.API_KEY = self.config.get("openai_key", "")
                self.BASE_URL = self.config.get("openai_base_url", "https://api.openai.com/v1")
                self.MODEL = self.config.get("openai_model", "gpt-3.5-turbo")

                if migrated:
                    with open("demo_setting.json", "w", encoding="utf-8") as f_out:
                        json.dump(self.config, f_out, ensure_ascii=False, indent=2)
                    self.logger.info("配置文件已更新并保存")

        except FileNotFoundError:
            self.logger.warning("未找到demo_setting.json文件，正在创建默认配置文件...")
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
            try:
                with open("demo_setting.json", "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                self.logger.info("默认配置文件已创建")
            except Exception as e:
                self.logger.error(f"创建配置文件失败: {e}")

            self.which_ai = "openai"
            self.API_KEY = ""
            self.BASE_URL = "https://api.openai.com/v1"
            self.MODEL = "gpt-3.5-turbo"
            self.logger.info("程序将在无AI功能模式下运行，请在设置中配置API密钥")

    def selectAi(self):
        """初始化OpenAI客户端"""
        self.client = OpenAI(
            api_key=self.API_KEY,
            base_url=self.BASE_URL
        )
        return "openai"

    # ---------- MCP 初始化 ----------
    def initialize_mcp(self):
        """在后台线程中初始化MCP管理器"""
        if not MCP_ENABLED:
            self.logger.info("MCP功能未启用")
            self._mcp_initialized_event.set()  # 标记完成（无MCP）
            return

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
                self._mcp_initialized_event.set()
                loop.close()

        mcp_thread = threading.Thread(target=init_mcp_sync, daemon=True)
        mcp_thread.start()

    def _wait_for_mcp_initialized(self, timeout: float = 5.0) -> bool:
        """等待MCP初始化完成，超时返回False"""
        if not MCP_ENABLED:
            return False
        return self._mcp_initialized_event.wait(timeout)

    # ---------- 工具调用辅助 ----------
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """调用MCP工具（异步）"""
        if not self.mcp_enabled or not self.mcp_manager:
            return None
        return await self.mcp_manager.call_tool(tool_name, arguments)

    # ---------- 会话管理 ----------
    def _get_lock(self, identity):
        if identity not in self._save_locks:
            self._save_locks[identity] = threading.Lock()
        return self._save_locks[identity]

    def load_gif(self, gif_folder=None, dir_name="蜡笔小新组"):
        """加载GIF文件列表，添加文件存在性验证"""
        if gif_folder is None:
            if not hasattr(self, 'config'):
                self.config = {}
            try:
                gif_folder = self.config.get("gif_folder", f"gif/{dir_name}")
            except Exception:
                gif_folder = f"gif/{dir_name}"

        folder_path = gif_folder
        GifList = []
        try:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                with os.scandir(folder_path) as entries:
                    for entry in entries:
                        if entry.is_file() and entry.name.lower().endswith('.gif'):
                            GifList.append({"name": entry.name})
            else:
                self.logger.warning(f"GIF文件夹 '{folder_path}' 不存在或不是目录")
        except PermissionError:
            self.logger.error(f"没有权限访问文件夹 '{folder_path}'")
        return GifList

    def load_img(self):
        """加载图片文件列表，改进路径查找逻辑"""
        folder_path = "imgs"
        current_dir = os.getcwd()
        self.logger.debug(f"当前工作目录: {current_dir}")

        # 尝试多种路径组合，包括项目根目录
        possible_paths = [
            folder_path,
            os.path.join(current_dir, folder_path),
            os.path.join(os.path.dirname(__file__), folder_path),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), folder_path),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), folder_path),
        ]

        found_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                found_path = path
                break

        ImgList = []
        if found_path:
            self.logger.debug(f"找到 IMG 文件夹: {found_path}")
            try:
                with os.scandir(found_path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            ImgList.append({"name": entry.name})
            except PermissionError:
                self.logger.error(f"没有权限访问文件夹 '{found_path}'。")
        else:
            self.logger.warning(f"IMG 文件夹 '{folder_path}' 不存在，正在创建该文件夹...")
            os.makedirs(folder_path, exist_ok=True)
        return ImgList

    def save_prompt(self, prompt):
        if prompt == "":
            prompt = "你叫丫丫，18岁女生，是个人,性格有趣且是否热情，回复要简短自然带点幽默"
        with open("prompt.txt", "w+", encoding="utf-8") as f:
            f.write(prompt)
        return prompt

    def update_prompt_from_file(self):
        if not os.path.exists("prompt.txt"):
            self.save_prompt("")
        try:
            prompt = open("prompt.txt", "r", encoding="utf-8").read()
            return prompt
        except FileNotFoundError:
            self.logger.error("未找到prompt.txt文件，请检查文件是否存在")
            return ""

    def _format_file_list(self, file_list):
        """格式化文件列表为可读字符串"""
        if not file_list:
            return "无"
        return ", ".join([item["name"] for item in file_list])

    
    def load_skills(self):
        with open("yyskills/SKILL.md", "r", encoding="utf-8") as f:
            skills = f.read()
            return skills
        
    def load_skills_json(self):
        with open("yyskills/skill_list.json", "r", encoding="utf-8") as f:
            skills_json = json.load(f)
            return skills_json

    def load_conversation(self, identity="default"):
        """加载指定标识符的会话记录"""
        GifList = self.load_gif()
        ImgList = self.load_img()
        skills = self.load_skills()
        skills_json = self.load_skills_json()

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
        tools_mcp = "你可以使用外部工具查询实时信息，例如高铁票、天气等。如果需要，请直接调用相关工具。"

        if not os.path.exists(filename):
            return [{"role": "system", "content": f"{respon},{sendGif},{HowUseGif},可用的gif有{self._format_file_list(GifList)};{HowSendImg},可用的图片有{self._format_file_list(ImgList)},仅能发送里面有的图片;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。;\n{skills}\n{skills_json}"}]

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                messages[0]["content"] = f"{respon},{sendGif},{HowUseGif},可用的gif有{self._format_file_list(GifList)};{HowSendImg},可用的图片有{self._format_file_list(ImgList)},仅能发送里面有的图片;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。;\n{skills}\n{skills_json}"
                return messages
        except (json.JSONDecodeError, IOError) as e:
            self.logger.critical(f"加载历史记录失败: {e}")
            return [{"role": "system", "content": f"{respon},{sendGif},{HowUseGif},可用的gif有{self._format_file_list(GifList)};{HowSendImg},可用的图片有{self._format_file_list(ImgList)},仅能发送里面有的图片;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。;\n{skills}\n{skills_json}"}]

    def save_conversation(self, identity, messages):
        filename = f"ai_memory/memory_{identity}.json"
        lock = self._get_lock(identity)
        with lock:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2)
            except IOError as e:
                self.logger.critical(f"保存对话失败: {e}")

    # ---------- 文件写入 ----------
    def write_code_file(self, file_path, code_content):
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
        
    

    # ---------- 普通AI回复（带文本命令处理）----------
    def get_ai_reply_stream(self, messages, callback=None):
        """流式获取AI回复，支持回调函数处理每部分输出，并处理 [USE_cmd:] 命令"""
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                stream=True
            )

            reply = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_part = chunk.choices[0].delta.content
                    reply += content_part
                    if callback:
                        callback(content_part)
                    else:
                        print(content_part, end='', flush=True)

            print()  # 换行

            
                    
                    


            # 提取GIF
            pattern_filename = r'\[GIF:([^\]]+)\]'
            matches_filename = re.findall(pattern_filename, reply)
            if not matches_filename:
                self.logger.warning("未找到GIF文件名")
                matches_filename = ["走路"]
            # 规范化GIF文件名，避免重复扩展名
            gif_filename = matches_filename[0]
            if gif_filename.endswith('.gif'):
                gif_name = gif_filename
            else:
                gif_name = gif_filename + ".gif"
            reply = reply.replace(f"[GIF:{matches_filename[0]}]", "").strip()

            # 保存GIF到配置
            self._save_gif_to_config(gif_name)

            # 检查是否包含 [USE_cmd:xxx]
            use_cmd_pattern = r"\[USE_cmd:(.+?)\]"
            match = re.search(use_cmd_pattern, reply)

            if match:
                keyword = match.group(1).strip()

                # 处理 write_code 指令
                write_code_match = re.match(r"^write_code\s+([^\s]+)\s+([\s\S]+)$", keyword)
                if write_code_match:
                    file_name = write_code_match.group(1)
                    code_content = write_code_match.group(2)
                    if not code_content.strip():
                        result = "未检测到有效代码内容，请用 write_code 指令并附上完整代码。"
                    else:
                        # 处理转义字符
                        try:
                            code_content = code_content.encode('utf-8').decode('unicode_escape')
                        except Exception:
                            code_content = code_content.replace('\\n', '\n').replace('\\t', '\t')
                        result = self.write_code_file(file_name, code_content)
                    messages.append({"role": "user", "content": f"[USE_cmd:write_code]结果：{result}"})
                else:
                    # 处理 echo 指令
                    echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", keyword)
                    echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", keyword)
                    if echo_single_match or echo_append_match:
                        if not hasattr(self.get_ai_reply_stream, '_echo_cache'):
                            self.get_ai_reply_stream._echo_cache = {}
                        echo_cache = self.get_ai_reply_stream._echo_cache
                        if echo_single_match:
                            file_name = echo_single_match.group(2)
                            code_content = echo_single_match.group(1)
                            echo_cache[file_name] = [code_content]
                            result = f"准备写入: {file_name}"
                        else:  # append
                            file_name = echo_append_match.group(2)
                            code_content = echo_append_match.group(1)
                            if file_name not in echo_cache:
                                echo_cache[file_name] = []
                            echo_cache[file_name].append(code_content)
                            result = f"追加内容: {file_name}"

                        # 判断下一条是否还是echo
                        next_is_echo = False
                        if len(messages) > 0 and isinstance(messages[-1], dict):
                            last_content = messages[-1].get('content', '')
                            if re.match(r"\[USE_cmd:echo", last_content):
                                next_is_echo = True
                        if not next_is_echo:
                            code_content_fixed = '\n'.join(echo_cache[file_name])
                            code_content_fixed = html.unescape(code_content_fixed)
                            code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                            code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                            result = self.write_code_file(file_name, code_content_fixed)
                            messages.append({"role": "user", "content": f"[USE_cmd:echo]结果：{result}"})
                    else:
                        # 普通命令执行
                        try:
                            result = subprocess.run(
                                ["powershell", "-Command", keyword],
                                capture_output=True, text=True)
                            stdout = result.stdout.strip()
                            stderr = result.stderr.strip()
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
                    stream=False
                )
                if hasattr(response2, "choices") and response2.choices:
                    return response2.choices[0].message.content
                return "AI接口无有效回复(二次)"
            
            Weather_get = r'\[Weather:([^\]]*)\]'
            matches_weather = re.findall(Weather_get, reply)
            if matches_weather:
                self.logger.info(f"检测到天气查询指令: {matches_weather[0]}")
                if matches_weather[0] == "LocalWeather":
                    user_address = UserIP().sendAddress()
                    self.logger.info(f"获取用户地址: {user_address}")
                    reply = MSWeather(user_address).return_to_ai()
                    # MSWeather_msg = [{"role": "system", "content": "总结后输出"},{"role": "user", "content": reply}]
                    # reply = self.get_ai_reply_stream(MSWeather_msg, callback=callback)

                else:
                    self.logger.info(f"获取{matches_weather[0]}的天气信息")
                    reply = MSWeather(matches_weather[0]).return_to_ai()

            skills_get = r'\[USESKILLS:([^\]]*)\]'
            matches_skills = re.findall(skills_get, reply)
            if matches_skills:
                self.logger.info(f"检测到技能调用指令: {matches_skills[0]}")
                reply = UESkills(matches_skills[0]).analyze_skill()
                messages.append({"role": "user", "content": f"[System]技能返回的结果为: {reply}"})
                reply = self.get_ai_reply_stream(messages)
                # skills_ls = matches_skills[0].split(":")

                # #面对调用技能没有参数的情况
                # if skills_ls[0] == skills_ls[1]:
                #     skills_json = self.load_skills_json()

                #     #面对有外部插件的情况
                #     if skills_json[skills_ls[0]]["have_plugin"]:
                #         plugins = PluginManager.load_plugins()
                #         plugin_response = PluginManager.call_plugin(plugins, skills_ls[0])
                #         messages.append({"role": "user", "content": f"[System]插件返回的结果为: {plugin_response}"})
                #         reply = self.get_ai_reply_stream(messages)


            return reply
        except Exception as e:
            return f"AI请求失败: {e}"

    def get_ai_reply_sync(self, messages):
        """同步获取AI回复，处理 [USE_cmd:] 命令"""
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages
            )
            if hasattr(response, "choices") and response.choices:
                reply = response.choices[0].message.content
                self.logger.debug(f"AI回复: {reply}")

                # 提取GIF
                pattern_filename = r'\[GIF:([^\]]+)\]'
                matches_filename = re.findall(pattern_filename, reply)
                if not matches_filename:
                    self.logger.warning("未找到GIF文件名")
                    matches_filename = ["走路"]
                # 规范化GIF文件名，避免重复扩展名
                gif_filename = matches_filename[0]
                if gif_filename.endswith('.gif'):
                    gif_name = gif_filename
                else:
                    gif_name = gif_filename + ".gif"
                reply = reply.replace(f"[GIF:{matches_filename[0]}]", "").strip()
                self._save_gif_to_config(gif_name)

                # 检查 [USE_cmd:]
                use_cmd_pattern = r"\[USE_cmd:(.+?)\]"
                match = re.search(use_cmd_pattern, reply)

                if match:
                    keyword = match.group(1).strip()

                    # 处理 write_code
                    write_code_match = re.match(r"^write_code\s+([^\s]+)\s+([\s\S]+)$", keyword)
                    if write_code_match:
                        file_name = write_code_match.group(1)
                        code_content = write_code_match.group(2)
                        if not code_content.strip():
                            result = "未检测到有效代码内容，请用 write_code 指令并附上完整代码。"
                        else:
                            try:
                                code_content = code_content.encode('utf-8').decode('unicode_escape')
                            except Exception:
                                code_content = code_content.replace('\\n', '\n').replace('\\t', '\t')
                            result = self.write_code_file(file_name, code_content)
                        messages.append({"role": "user", "content": f"[USE_cmd:write_code]结果：{result}"})
                    else:
                        # 处理 echo
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
                            else:
                                file_name = echo_append_match.group(2)
                                code_content = echo_append_match.group(1)
                                if file_name not in echo_cache:
                                    echo_cache[file_name] = []
                                echo_cache[file_name].append(code_content)
                                result = f"追加内容: {file_name}"

                            next_is_echo = False
                            if len(messages) > 0 and isinstance(messages[-1], dict):
                                last_content = messages[-1].get('content', '')
                                if re.match(r"\[USE_cmd:echo", last_content):
                                    next_is_echo = True
                            if not next_is_echo:
                                code_content_fixed = '\n'.join(echo_cache[file_name])
                                code_content_fixed = html.unescape(code_content_fixed)
                                code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                                code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                                result = self.write_code_file(file_name, code_content_fixed)
                                messages.append({"role": "user", "content": f"[USE_cmd:echo]结果：{result}"})
                        else:
                            # 普通命令
                            try:
                                result = subprocess.run(
                                    ["powershell", "-Command", keyword],
                                    capture_output=True, text=True)
                                stdout = result.stdout.strip()
                                stderr = result.stderr.strip()
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
            return "AI接口无有效回复"
        except Exception as e:
            return f"AI请求失败: {e}"

    # ---------- MCP AI回复（工具调用）----------
    async def get_ai_reply_with_mcp(self, messages: list, callback: Optional[Callable[[str], None]] = None) -> str:
        """
        支持MCP工具调用的流式AI回复方法
        :param messages: 对话历史
        :param callback: 可选回调，用于实时输出内容块
        :return: 最终回复字符串
        """
        # 等待MCP初始化完成（最多5秒）
        if not self._wait_for_mcp_initialized():
            self.logger.warning("MCP未就绪，回退到普通模式")
            return self.get_ai_reply_stream(messages, callback)

        # 复制消息列表，避免修改外部
        working_messages = messages.copy()
        openai_tools = self.mcp_manager.get_tools_for_openai() if self.mcp_enabled else []

        while True:
            request_params = {
                "model": self.MODEL,
                "messages": working_messages,
                "stream": True
            }
            if openai_tools:
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"

            try:
                response = self.client.chat.completions.create(**request_params)
            except Exception as e:
                self.logger.error(f"AI请求失败: {e}")
                return f"AI请求失败: {e}"

            collected_content = ""
            collected_tool_calls = {}  # index -> {id, function: {name, arguments}}
            finish_reason = None

            # 处理流式响应
            for chunk in response:
                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason

                if delta.content:
                    collected_content += delta.content
                    if callback:
                        callback(delta.content)

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

                if finish_reason:
                    break

            # 构建本轮助手消息
            assistant_msg = {"role": "assistant", "content": collected_content}
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

            working_messages.append(assistant_msg)

            # 如果没有工具调用，结束循环
            if not assistant_msg.get("tool_calls"):
                # 后处理（提取GIF等）
                return self._post_process_reply(collected_content)

            # 处理工具调用
            for tool_call in assistant_msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    self.logger.error(f"工具参数解析失败: {e}")
                    content = f"参数解析失败: {e}"
                else:
                    self.logger.info(f"调用MCP工具 {func_name} 参数: {func_args}")
                    try:
                        result = await self.mcp_manager.call_tool(func_name, func_args)
                        content = str(result) if result is not None else "工具未返回结果"
                    except Exception as e:
                        content = f"工具调用失败: {e}"
                        self.logger.error(f"MCP工具调用失败: {e}")

                # 将工具结果加入消息历史
                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": content
                })

            # 继续循环，让AI基于工具结果再次生成

    def get_ai_reply_sync_with_mcp(self, messages: list) -> str:
        """同步方式获取AI回复（支持MCP）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_ai_reply_with_mcp(messages))
        finally:
            loop.close()

    # ---------- 后处理辅助 ----------
    def _post_process_reply(self, reply: str) -> str:
        """后处理AI回复：提取GIF并保存到配置文件"""
        pattern = r'\[GIF:([^\]]+)\]'
        matches = re.findall(pattern, reply)
        # 规范化GIF文件名，避免重复扩展名
        if matches:
            gif_filename = matches[0]
            if gif_filename.endswith('.gif'):
                gif_name = gif_filename
            else:
                gif_name = gif_filename + '.gif'
        else:
            gif_name = "走路.gif"
        reply = re.sub(pattern, '', reply).strip()
        self._save_gif_to_config(gif_name)
        return reply

    def _save_gif_to_config(self, gif_name: str):
        """将GIF文件名保存到demo_setting.json，保持其他配置不变"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                demo_setting = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            demo_setting = {}
        
        # 只更新gif字段，保留其他配置
        demo_setting["gif"] = gif_name
        
        try:
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(demo_setting, f, ensure_ascii=False, indent=2)
            self.logger.info(f"GIF已保存: {gif_name}")
        except Exception as e:
            self.logger.error(f"保存GIF配置失败: {e}")

    # ---------- 交互循环 ----------
    def chat_round(self, messages):
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