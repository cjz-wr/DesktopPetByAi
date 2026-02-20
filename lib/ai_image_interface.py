# -*- coding: utf-8 -*-
"""
用于支持智谱AI视觉模型的接口文件
支持文本+图像的混合输入模式
"""
from zhipuai import ZhipuAI
import asyncio
import os
import json
import threading
import re
import subprocess
import base64
import html  # 用于处理HTML实体转义
import logging
import lib.LogManager

lib.LogManager.init_logging()
logger = logging.getLogger(__name__)

try:
    # 从demo_setting.json加载配置
    with open("demo_setting.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        API_KEY = config.get("ai_key", "")
        MODEL = config.get("model", "glm-4.6v")  # 默认使用视觉模型
except FileNotFoundError:
    logger.warning("未找到demo_setting.json文件，请检查文件是否存在")
    API_KEY = ""
    MODEL = "glm-4.6v"


client = ZhipuAI(api_key=API_KEY)

_save_locks = {}
def _get_lock(identity):
    if identity not in _save_locks:
        _save_locks[identity] = threading.Lock()
    return _save_locks[identity]


def load_gif(gif_folder=None):
    # 从配置中获取GIF文件夹路径，如果没有指定则使用默认值
    if gif_folder is None:
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                gif_folder = config.get("gif_folder", "gif/蜡笔小新组")
        except FileNotFoundError:
            gif_folder = "gif/蜡笔小新组"
    
    folder_path = gif_folder
    GifList = []
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file():
                    GifList.append({
                        "name": entry.name,
                        # 注释掉是为了提高ai的识别率
                        # "path": os.path.join(folder_path, entry.name)
                    })
    except FileNotFoundError:
        logger.error(f"文件夹 '{folder_path}' 不存在。")
    except PermissionError:
        logger.error("没有权限访问文件夹")
    return GifList

def load_img():
    folder_path = "imgs"
    ImgList = []
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file():
                    ImgList.append({
                        "name": entry.name,
                        # 注释掉是为了提高ai的识别率
                        # "path": os.path.join(folder_path, entry.name)
                    })
    except FileNotFoundError:
        logger.error(f"文件夹 '{folder_path}' 不存在。")
    except PermissionError:
        logger.error(f"没有权限访问文件夹 '{folder_path}'")
    return ImgList

def encode_image(image_path):
    """
    将图像文件编码为base64字符串
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"图像编码失败: {e}")
        return None

def load_conversation_with_image(identity="default"):
    """
    加载对话历史，包含图像支持
    """
    GifList = load_gif()
    ImgList = load_img()
    filename = f"ai_memory/memory_{identity}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"加载历史记录失败: {e}")
    
    use_cmd = (
        "如果需要让助手执行Windows命令，必须严格用如下格式输出：[USE_cmd:你的命令]，"
        "中括号和冒号都不能省略，命令内容不能有多余内容。"
        "例如：[USE_cmd:dir] 或 [USE_cmd:py a.py]。"
        "不要用其它格式，否则命令不会被执行。"
    )
    open_app = (
        "如果需要打开程序,直接在桌面的路径下找软件的快捷方式，并打开指定的软件"
        '例如 C:\path\to\your\shortcut.lnk'
        "要严格尊守格式：[USE_cmd: C:\path\to\your\shortcut.lnk]"
        "注意:1.用户默认的用户名是Administrator,如果没有找到就询问,以上内容都要严格遵守"
        "2.对于中国软件商开发的软件，默认在公共用户的桌面下找"
        "3.对于微信则根据用户语言确定微信名,例如是中文的话就是微信，英文则是WeChat"
        "4.如果没有找到，就在公共用户的桌面这个路径下找，即用户再次询问打开某个软件时"
    )
    respon = "你叫丫丫，18岁女生，是个人,性格有趣且是否热情，回复要简短自然带点幽默。你在windows聊天,是一个windows系统助手。你可以使用gif表达情感。注意：你所有的回答中都必须包含一个gif文件，且只能有这个。你还须了解你可以使用的gif文件。不能仅有gif文件，而没有文字"
    HowUseGif = "使用gif的格式为[GIF:文件名],例如[GIF:闭眼]"
    HowSendImg = "如果你需要发送表情包，请严格使用如下格式输出：[IMAGE_NAME: 图片文件名]，中括号和冒号都不能省略，图片文件名必须是存在于图片目录下的文件，否则无法发送图片。表情包并非必须每次都发送，只有在合适的情况下才发送。"
    return [{"role": "system", "content": f"{respon},{use_cmd},{open_app},{HowUseGif},可用的gif有{GifList},{HowSendImg},可用的图片有{ImgList}。"}]

def save_conversation(identity, messages):
    filename = f"ai_memory/memory_{identity}.json"
    lock = _get_lock(identity)
    with lock:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"保存对话失败: {e}")

def write_code_file(file_path, code_content):
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

def get_ai_vision_reply_stream(text_content, image_path=None, callback=None):
    """
    流式获取AI视觉模型回复，支持文本+图像输入
    
    Args:
        text_content (str): 文本内容
        image_path (str, optional): 图像文件路径
        callback (callable, optional): 回调函数，用于处理流式输出的每部分
    
    Returns:
        str: 完整的AI回复内容
    """
    try:
        # 构建消息内容
        content = [{"type": "text", "text": text_content}]
        
        if image_path and os.path.exists(image_path):
            encoded_image = encode_image(image_path)
            if encoded_image:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                })
        
        # 创建流式请求
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
            stream=True  # 启用流式输出
        )
        
        # 逐步收集流式响应
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
        
        # 提取gif
        pattern_filename = r'\[GIF:([^\]]+)\]'
        matches_filename = re.findall(pattern_filename, reply)

        # 判断matches_filename是否为空
        if not matches_filename:
            logger.warning("未找到GIF文件名")
            matches_filename = ["闭眼"]

        logger.warning("GIF文件名:", matches_filename[0].replace(".gif", ""))

        # 移除GIF标记
        reply_without_gif = reply.replace(f"[GIF:{matches_filename[0]}]", "")

        # 读取demo_setting.json
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                demo_setting = json.load(f)
                logger.info("读取到的demo_setting:", demo_setting)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"读取demo_setting.json失败: {e}")

        # 往读取到的demo_setting里添加gif键值对
        demo_setting["gif"] = matches_filename[0].replace(".gif", "") + ".gif"

        # 保存到demo_setting.json
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(demo_setting, f, ensure_ascii=False, indent=2)

        # 检查是否包含 [USE_cmd:xxx]
        use_cmd_pattern = r"\[USE_cmd:(.+?)\]"
        match = re.search(use_cmd_pattern, reply_without_gif)

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
                    result = write_code_file(file_name, code_content)
                
                # 再次请求AI
                content_with_result = content + [{"type": "text", "text": f"[USE_cmd:write_code]结果：{result}"}]
                response2 = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": content_with_result}],
                    stream=True
                )
                
                # 处理第二次流式响应
                second_reply = ""
                for chunk in response2:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_part = chunk.choices[0].delta.content
                        second_reply += content_part
                        if callback:
                            callback(content_part)
                        else:
                            print(content_part, end='', flush=True)  # 实时打印流式输出
                print()  # 换行
                
                return second_reply
            else:
                # 新增：支持多条 echo >/>> 写入同一文件时自动合并内容
                echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", keyword)
                echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", keyword)
                if echo_single_match or echo_append_match:
                    if not hasattr(get_ai_vision_reply_stream, '_echo_cache'):
                        get_ai_vision_reply_stream._echo_cache = {}
                    echo_cache = get_ai_vision_reply_stream._echo_cache
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
                    if 'messages' in locals() and len(locals()['messages']) > 0 and isinstance(locals()['messages'][-1], dict):
                        last_content = locals()['messages'][-1].get('content', '')
                        if re.match(r"\[USE_cmd:echo", last_content):
                            next_is_echo = True
                    if not next_is_echo:
                        code_content_fixed = '\n'.join(echo_cache[file_name])
                        # 处理HTML实体和Unicode转义
                        code_content_fixed = html.unescape(code_content_fixed)
                        code_content_fixed = code_content_fixed.encode('utf-8').decode('unicode_escape')
                        code_content_fixed = code_content_fixed.replace('\\n', '\n').replace('\\t', '\t')
                        result = write_code_file(file_name, code_content_fixed)
                        
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
                    
                # 再次请求AI
                content_with_result = content + [{"type": "text", "text": f"[USE_cmd:{keyword}]结果：{final_result}"}]
                response2 = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": content_with_result}],
                    stream=True
                )
                
                # 处理第二次流式响应
                second_reply = ""
                for chunk in response2:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_part = chunk.choices[0].delta.content
                        second_reply += content_part
                        if callback:
                            callback(content_part)
                        else:
                            print(content_part, end='', flush=True)  # 实时打印流式输出
                print()  # 换行
                
                return second_reply
        return reply
    except Exception as e:
        return f"AI请求失败: {e}"

def get_ai_vision_reply_sync(text_content, image_path=None):
    """
    同步方式获取AI视觉模型回复，支持文本+图像输入
    
    Args:
        text_content (str): 文本内容
        image_path (str, optional): 图像文件路径
    
    Returns:
        str: AI回复内容
    """
    # 调用流式函数，但不使用回调
    return get_ai_vision_reply_stream(text_content, image_path, callback=None)

async def get_ai_vision_reply(text_content, image_path=None):
    """
    异步方式获取AI视觉模型回复
    
    Args:
        text_content (str): 文本内容
        image_path (str, optional): 图像文件路径
    
    Returns:
        str: AI回复内容
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_ai_vision_reply_sync, text_content, image_path)

def chat_with_image_round(messages, image_path=None):
    """
    带图像的对话轮次
    """
    try:
        while True:
            user_input = input("\n你：").strip()
            if user_input:
                break
            print("输入不能为空,请重新输入")
        reply = get_ai_vision_reply_sync(user_input, image_path)
        print(f"\n助手：{reply}")
    except Exception as e:
        print(f"对话出错: {e}")

def test_with_specific_image():
    """
    使用指定图片路径测试流式输出功能
    """
    image_path = r"D:\code\python\desktop_pet\main\imgs\打你.jpg"
    text_content = "请描述这张图片的内容"
    
    print("开始使用指定图片进行测试...")
    print(f"图片路径: {image_path}")
    print(f"文本内容: {text_content}")
    print("AI回复:")
    
    if os.path.exists(image_path):
        reply = get_ai_vision_reply_stream(text_content, image_path)
        print(f"\n最终回复: {reply}")
    else:
        print(f"错误：图片文件不存在于路径 {image_path}")

def main():
    print("=== 视觉AI对话开始 (输入q退出) ===")
    identity = input("请输入身份标识（或直接回车使用默认身份）: ").strip() or "default"
    messages = load_conversation_with_image(identity)
    if len(messages) > 1:
        print(f"\n[加载了{len(messages) - 1}条历史记录]")
    
    image_path = input("请输入图像路径（可选，直接回车跳过）: ").strip()
    if not image_path:
        image_path = None
        
    try:
        while True:
            chat_with_image_round(messages, image_path)
    except KeyboardInterrupt:
        print("\n对话已保存,下次继续")
    finally:
        save_conversation(identity, messages)

if __name__ == "__main__":
    # 提供一个选择：运行常规对话或测试特定图片
    choice = input("选择模式 - 1: 常规对话, 2: 测试指定图片 (D:\\code\\python\\desktop_pet\\main\\imgs\\打你.jpg): ")
    if choice == "2":
        test_with_specific_image()
    else:
        main()