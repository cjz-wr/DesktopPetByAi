# -*- coding: utf-8 -*-
from zhipuai import ZhipuAI
import asyncio
import os
import json
import threading
import re
import subprocess
import html  # 用于处理HTML实体转义

try:
    # 从demo_setting.json加载配置
    with open("demo_setting.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        API_KEY = config.get("ai_key", "")
        MODEL = config.get("model", "glm-4-flash-250414")
except FileNotFoundError:
    print("未找到demo_setting.json文件，请检查文件是否存在")
    API_KEY = ""
    MODEL = "glm-4-flash-250414"


# 注意：API_KEY和MODEL现在从demo_setting.json加载
# 如果需要手动设置，请修改demo_setting.json文件



client = ZhipuAI(api_key=API_KEY)

_save_locks = {}
def _get_lock(identity):
    if identity not in _save_locks:
        _save_locks[identity] = threading.Lock()
    return _save_locks[identity]


def load_gif():
    folder_path = "gif/蜡笔小新组"
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
        print(f"文件夹 '{folder_path}' 不存在。")
    except PermissionError:
        print(f"没有权限访问文件夹 '{folder_path}'。")
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
                        #注释掉是为了提高ai的识别率
                        # "path": os.path.join(folder_path, entry.name)
                    })
    except FileNotFoundError:
        print(f"文件夹 '{folder_path}' 不存在。")
    except PermissionError:
        print(f"没有权限访问文件夹 '{folder_path}'。")
    return ImgList

def load_conversation(identity="default"):

    GifList = load_gif()
    ImgList = load_img()
    filename = f"ai_memory/memory_{identity}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"加载历史记录失败: {e}")
    
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
    HowUseGif = "使用gif的格式为[GIF:文件名],例如[GIF:走路]"
    HowSendImg = "如果你需要发送表情包，请严格使用如下格式输出：[IMAGE_NAME: 图片文件名]，中括号和冒号都不能省略，图片文件名必须是存在于图片目录下的文件，否则无法发送图片。表情包并非必须每次都发送，只有在合适的情况下才发送。"
    return [{"role": "system", "content": f"{respon},{use_cmd},{open_app},{HowUseGif},可用的gif有{GifList},{HowSendImg},可用的图片有{ImgList}。;注意:包含*SEND*标识的消息是用户发送给你的图片，请根据图片内容进行回复。"}]

def save_conversation(identity, messages):
    filename = f"ai_memory/memory_{identity}.json"
    lock = _get_lock(identity)
    with lock:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存对话失败: {e}")

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

def get_ai_reply_sync(messages):
    """同步方式获取AI回复,返回字符串。自动处理[SEARCH_MCP:xxx]指令"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        if hasattr(response, "choices") and response.choices:
            reply = response.choices[0].message.content
            print(reply)

            #提取gif
            pattern_filename = r'\[GIF:([^\]]+)\]'
            matches_filename = re.findall(pattern_filename,reply)

            #判断matches_filename是否为空
            if  not matches_filename:
                print("未找到GIF文件名")
                matches_filename = ["走路"]

            print("仅文件名:", matches_filename[0].replace(".gif", ""))

            

            # 移除GIF标记
            reply = reply.replace(f"[GIF:{matches_filename[0]}]", "")

            #读取demo_setting.json
            try:
                with open("demo_setting.json", "r", encoding="utf-8") as f:
                    demo_setting = json.load(f)
                    print("读取到的demo_setting:", demo_setting)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"读取demo_setting.json失败: {e}")

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
                        result = write_code_file(file_name, code_content)
                    messages.append({"role": "user", "content": f"[USE_cmd:write_code]结果：{result}"})
                else:
                    # 新增：支持多条 echo >/>> 写入同一文件时自动合并内容
                    echo_single_match = re.match(r"^echo\s+'([\s\S]+)'\s+>\s*([^\s]+)$", keyword)
                    echo_append_match = re.match(r"^echo\s+'([\s\S]+)'\s+>>\s*([^\s]+)$", keyword)
                    if echo_single_match or echo_append_match:
                        if not hasattr(get_ai_reply_sync, '_echo_cache'):
                            get_ai_reply_sync._echo_cache = {}
                        echo_cache = get_ai_reply_sync._echo_cache
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
                            result = write_code_file(file_name, code_content_fixed)
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
                response2 = client.chat.completions.create(
                    model=MODEL,
                    messages=messages
                )
                if hasattr(response2, "choices") and response2.choices:
                    return response2.choices[0].message.content
                return "AI接口无有效回复(二次)"
            return reply
        return "AI接口无有效回复"
    except Exception as e:
        return f"AI请求失败: {e}"

async def get_ai_reply(messages):
    """异步方式获取AI回复,返回字符串"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_ai_reply_sync, messages)

def chat_round(messages):
    try:
        while True:
            user_input = input("\n你：").strip()
            if user_input:
                break
            print("输入不能为空,请重新输入")
        messages.append({"role": "user", "content": user_input})
        reply = get_ai_reply_sync(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"\n助手：{reply}")
    except Exception as e:
        print(f"对话出错: {e}")

def main():
    print("=== 对话开始 (输入q退出) ===")
    identity = input("请输入身份标识（或直接回车使用默认身份）: ").strip() or "default"
    messages = load_conversation(identity)
    if len(messages) > 1:
        print(f"\n[加载了{len(messages) - 1}条历史记录]")
    try:
        while True:
            chat_round(messages)
            save_conversation(identity, messages)
    except KeyboardInterrupt:
        print("\n对话已保存,下次继续")
    finally:
        save_conversation(identity, messages)

if __name__ == "__main__":
    main()