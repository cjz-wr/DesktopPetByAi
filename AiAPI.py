import json
import asyncio
import os
import re
import threading
import subprocess
import html
from typing import Optional, Dict, Any, Callable, List
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

        # MCP 相关（线程安全版）
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_enabled = False
        self.mcp_loop: Optional[asyncio.AbstractEventLoop] = None
        self.mcp_thread: Optional[threading.Thread] = None
        self._mcp_ready = asyncio.Event()  # 用于等待MCP初始化完成
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

    # ---------- MCP 初始化（线程安全版）----------
    def initialize_mcp(self):
        """在后台线程中初始化MCP管理器并运行事件循环"""
        if not MCP_ENABLED:
            self.logger.info("MCP功能未启用")
            self._mcp_ready.set()  # 标记完成（无MCP）
            return

        def run_mcp_loop():
            asyncio.set_event_loop(self.mcp_loop)
            try:
                # 在MCP循环中创建管理器
                self.mcp_manager = self.mcp_loop.run_until_complete(create_mcp_manager())
                self.mcp_enabled = True
                self.logger.info("MCP管理器初始化成功")
                self.mcp_loop.call_soon_threadsafe(self._mcp_ready.set)
                # 保持循环运行，等待后续任务
                self.mcp_loop.run_forever()
            except Exception as e:
                self.logger.error(f"MCP管理器初始化失败: {e}")
                self.mcp_loop.call_soon_threadsafe(self._mcp_ready.set)
            finally:
                self.mcp_loop.close()

        self.mcp_loop = asyncio.new_event_loop()
        self.mcp_thread = threading.Thread(target=run_mcp_loop, daemon=True)
        self.mcp_thread.start()

    async def wait_for_mcp_ready(self, timeout: float = 5.0) -> bool:
        """等待MCP初始化完成，超时返回False"""
        if not MCP_ENABLED:
            return False
        try:
            await asyncio.wait_for(self._mcp_ready.wait(), timeout)
            return self.mcp_enabled
        except asyncio.TimeoutError:
            return False

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """跨线程调用MCP工具（异步安全）"""
        if not self.mcp_enabled or not self.mcp_manager:
            return None
        # 将调用提交到MCP事件循环，并返回一个可等待的Future
        future = asyncio.run_coroutine_threadsafe(
            self.mcp_manager.call_tool(tool_name, arguments),
            self.mcp_loop
        )
        # 将concurrent.futures.Future转换为asyncio.Future
        return await asyncio.wrap_future(future)

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

    # ---------- 核心AI回复方法（支持MCP工具调用 + 自定义命令）----------
    async def get_ai_reply_with_mcp(self, messages: List[dict], callback: Optional[Callable[[str], None]] = None) -> str:
        """
        支持MCP工具调用的流式AI回复方法，同时处理自定义命令（[USE_cmd:], [Weather:], [USESKILLS:]）
        :param messages: 对话历史
        :param callback: 可选回调，用于实时输出内容块
        :return: 最终回复字符串
        """
        # 等待MCP初始化完成
        if not await self.wait_for_mcp_ready():
            self.logger.warning("MCP未就绪，回退到普通模式（无工具调用）")
            # 如果没有MCP，仍然可以继续，只是没有tools参数
            openai_tools = []
        else:
            openai_tools = self.mcp_manager.get_tools_for_openai() if self.mcp_enabled else []

        # 复制消息列表，避免修改外部
        working_messages = messages.copy()

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

            # 如果没有工具调用，则跳出循环，准备处理自定义命令
            if not assistant_msg.get("tool_calls"):
                final_reply = collected_content
                break

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
                        # 使用跨线程安全的 call_mcp_tool
                        result = await self.call_mcp_tool(func_name, func_args)
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

        # ---------- 处理自定义命令（[USE_cmd:], [Weather:], [USESKILLS:]）----------
        # 这些命令可能出现在 final_reply 中，需要递归执行
        # 使用正则检测所有可能的命令
        combined_pattern = r'\[(USE_cmd|Weather|USESKILLS):(.*?)\]'
        matches = re.findall(combined_pattern, final_reply)
        if not matches:
            # 没有命令，直接后处理并返回
            return self._post_process_reply(final_reply)

        # 有命令，逐个处理（通常一次只会有一个命令，但以防万一）
        for cmd_type, cmd_content in matches:
            if cmd_type == "USE_cmd":
                # 处理 [USE_cmd:...]
                result = await self._handle_use_cmd(cmd_content.strip(), working_messages)
            elif cmd_type == "Weather":
                # 处理 [Weather:...]
                result = await self._handle_weather(cmd_content.strip())
            elif cmd_type == "USESKILLS":
                # 处理 [USESKILLS:...]
                result = await self._handle_skills(cmd_content.strip(), working_messages)
            else:
                continue

            # 将结果作为用户消息加入历史，并重新调用AI
            working_messages.append({"role": "user", "content": result})
            # 递归调用自身（异步），注意 callback 需要继续传递
            return await self.get_ai_reply_with_mcp(working_messages, callback)

        # 如果没有匹配到命令（理论上不会走到这里）
        return self._post_process_reply(final_reply)

    # ---------- 自定义命令处理辅助方法（异步）----------
    async def _handle_use_cmd(self, cmd_text: str, messages: List[dict]) -> str:
        """处理 [USE_cmd:] 命令，返回需要追加到对话的结果文本"""
        # 检查是否是 write_code 指令
        write_code_match = re.match(r"^write_code\s+([^\s]+)\s+([\s\S]+)$", cmd_text)
        if write_code_match:
            file_name = write_code_match.group(1)
            code_content = write_code_match.group(2)
            if not code_content.strip():
                return "[USE_cmd:write_code]结果：未检测到有效代码内容"
            # 处理转义字符
            try:
                code_content = code_content.encode('utf-8').decode('unicode_escape')
            except Exception:
                code_content = code_content.replace('\\n', '\n').replace('\\t', '\t')
            # 写文件（同步I/O放到线程池）
            result = await asyncio.to_thread(self.write_code_file, file_name, code_content)
            return f"[USE_cmd:write_code]结果：{result}"

        # 检查 echo 指令
        echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", cmd_text)
        echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", cmd_text)
        if echo_single_match or echo_append_match:
            # 使用一个类级别的缓存（注意线程安全，但这里是异步函数，需用 asyncio.Lock）
            if not hasattr(self, '_echo_cache'):
                self._echo_cache = {}
                self._echo_lock = asyncio.Lock()
            async with self._echo_lock:
                if echo_single_match:
                    file_name = echo_single_match.group(2)
                    code_content = echo_single_match.group(1)
                    self._echo_cache[file_name] = [code_content]
                    result = f"准备写入: {file_name}"
                else:  # append
                    file_name = echo_append_match.group(2)
                    code_content = echo_append_match.group(1)
                    if file_name not in self._echo_cache:
                        self._echo_cache[file_name] = []
                    self._echo_cache[file_name].append(code_content)
                    result = f"追加内容: {file_name}"

                # 判断下一条是否还是echo（从messages中看）
                next_is_echo = False
                if len(messages) > 0 and isinstance(messages[-1], dict):
                    last_content = messages[-1].get('content', '')
                    if re.match(r"\[USE_cmd:echo", last_content):
                        next_is_echo = True
                if not next_is_echo:
                    # 组装最终内容并写入
                    code_content_fixed = '\n'.join(self._echo_cache[file_name])
                    code_content_fixed = html.unescape(code_content_fixed)
                    code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                    code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                    write_result = await asyncio.to_thread(self.write_code_file, file_name, code_content_fixed)
                    return f"[USE_cmd:echo]结果：{write_result}"
                else:
                    # 等待下一条命令合并
                    return result

        # 普通命令执行（PowerShell）
        try:
            # 使用 asyncio.create_subprocess_shell 或 to_thread
            # 这里用 to_thread 简化
            def run_powershell(cmd):
                result = subprocess.run(
                    ["powershell", "-Command", cmd],
                    capture_output=True, text=True
                )
                stdout = result.stdout.strip().encode('utf-8', errors='replace').decode('utf-8')
                stderr = result.stderr.strip().encode('utf-8', errors='replace').decode('utf-8')
                output = ""
                if stdout:
                    output += f"STDOUT:\n{stdout}\n"
                if stderr:
                    output += f"STDERR:\n{stderr}\n"
                return output.strip() or "命令执行完成（无输出）"

            cmd_output = await asyncio.to_thread(run_powershell, cmd_text)
            return f"[USE_cmd:{cmd_text}]结果：{cmd_output}"
        except Exception as e:
            return f"[USE_cmd:{cmd_text}]结果：命令执行失败: {e}"

    async def _handle_weather(self, location: str) -> str:
        """处理 [Weather:] 命令"""
        if location == "LocalWeather":
            user_address = await asyncio.to_thread(UserIP().sendAddress)
            self.logger.info(f"获取用户地址: {user_address}")
            weather_info = await asyncio.to_thread(MSWeather(user_address).return_to_ai)
        else:
            weather_info = await asyncio.to_thread(MSWeather(location).return_to_ai)
        return weather_info

    async def _handle_skills(self, skill_input: str, messages: List[dict]) -> str:
        """处理 [USESKILLS:] 命令"""
        self.logger.info(f"检测到技能调用指令: {skill_input}")
        # 假设 UESkills 是同步类
        skill_result = await asyncio.to_thread(UESkills(skill_input).analyze_skill)
        # 注意：原代码中处理技能后还会检查是否有插件，这里简化，但可以扩展
        return f"[System]技能返回的结果为: {skill_result}"

    # ---------- 同步包装 ----------
    def get_ai_reply_sync_with_mcp(self, messages: List[dict], callback: Optional[Callable[[str], None]] = None) -> str:
        """同步方式获取AI回复（支持MCP）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_ai_reply_with_mcp(messages, callback))
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
        """对话循环（使用支持MCP的回复方法）"""
        try:
            while True:
                user_input = input("\n你：").strip()
                if user_input:
                    break
                print("输入不能为空,请重新输入")
            messages.append({"role": "user", "content": user_input})
            # 使用支持MCP的同步方法
            reply = self.get_ai_reply_sync_with_mcp(messages)
            messages.append({"role": "assistant", "content": reply})
            print(f"\n助手：{reply}")
        except Exception as e:
            print(f"对话出错: {e}")

    # 保留旧方法以防其他地方调用（但内部可重定向到新方法）
    def get_ai_reply_stream(self, messages, callback=None):
        """旧方法：重定向到支持MCP的同步方法"""
        self.logger.warning("get_ai_reply_stream 已弃用，请使用 get_ai_reply_sync_with_mcp")
        return self.get_ai_reply_sync_with_mcp(messages, callback)

    def get_ai_reply_sync(self, messages):
        """旧方法：重定向到支持MCP的同步方法"""
        self.logger.warning("get_ai_reply_sync 已弃用，请使用 get_ai_reply_sync_with_mcp")
        return self.get_ai_reply_sync_with_mcp(messages)