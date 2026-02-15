# generate_image.py
import os
import json
import requests
from pathlib import Path
from zhipuai import ZhipuAI
import logging
# import time
from datetime import datetime

# 注意：此处假设你已通过 `pip install zhipuai` 安装了官方SDK

def get_api_key_from_settings():
    """
    从 demo_setting.json 文件中读取 API 密钥
    """
    settings_file = Path("demo_setting.json")
    if not settings_file.exists():
        # 如果当前目录没有找到配置文件，尝试在上级目录或其他常见位置查找
        possible_paths = [
            Path("../demo_setting.json"),
            Path("../../demo_setting.json"),
            Path("settings/demo_setting.json"),
            Path("config/demo_setting.json")
        ]
        for path in possible_paths:
            if path.exists():
                settings_file = path
                break

    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("ai_key")
        except Exception as e:
            logging.warning(f"读取配置文件失败: {e}")
            return None
    else:
        return None

def generate_image_with_cogview(prompt, api_key=None, size="1024x1024", n=1, quality="standard", save_path=None, show_preview=False, auto_rename=True):
    """
    使用 CogView 模型生成图像并保存到本地。
    
    Args:
        prompt (str): 生成图像的提示词
        api_key (str, optional): 智谱AI的API密钥，如果未提供则从环境变量获取
        size (str): 图像尺寸，默认为"1024x1024"
        n (int): 生成图片数量，默认为1
        quality (str): 图像质量，"standard"或"high"，默认为"standard"
        save_path (str or Path, optional): 保存路径，如果未指定则自动生成
        show_preview (bool): 是否显示预览，默认为False
        auto_rename (bool): 当文件已存在时是否自动重命名，默认为True
    
    Returns:
        dict: 包含生成结果的字典，包含success(bool), image_path(str), url(str)等信息
    """
    # 1. 初始化客户端 - 如果未传入api_key，则尝试从demo_setting.json读取，最后从环境变量读取
    if api_key is None:
        api_key = get_api_key_from_settings()
    
    if not api_key:
        api_key = os.getenv("ZHIPUAI_API_KEY")
    
    if not api_key:
        logging.warning("⚠️  未检测到API Key，请设置环境变量 ZHIPUAI_API_KEY 或通过参数传递，或者检查 demo_setting.json 文件中是否包含 ai_key 字段。")
        return {"success": False, "error": "Missing API Key"}

    client = ZhipuAI(api_key=api_key)

    # 2. 准备生成参数
    model = "cogview-3-flash"  # 指定使用的模型
    
    print(f"🎨 正在使用模型 [{model}] 生成图像...")
    print(f"📝 提示词: {prompt}")

    try:
        # 3. 调用API生成图像
        response = client.images.generations(
            model=model,
            prompt=prompt,
            size=size,  # 支持其他比例，如 "768x1344"
            n=n,  # 生成图片的数量，默认为1
            quality=quality,  # 质量选项：standard / high
        )

        # 4. 从响应中获取图片URL
        image_url = response.data[0].url
        print(f"✅ 图像生成成功！")
        print(f"🔗 图片临时URL: {image_url}")

        # 5. 下载并保存图片到本地
        image_data = requests.get(image_url).content
        
        # 处理保存路径
        if save_path is None:
            # 如果没有指定保存路径，则生成一个唯一的文件名
            img_dir = Path("./images")
            img_dir.mkdir(exist_ok=True)
            
            # 根据提示词生成文件名
            safe_prompt = "".join(c for c in prompt if c.isalnum() or c in "-_ .")
            safe_prompt = safe_prompt.strip()[:50]  # 限制长度
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = img_dir / f"{safe_prompt.replace(' ', '_')}_{timestamp}.png"
        else:
            save_path = Path(save_path)
            # 如果指定了保存路径但不存在，则创建父目录
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查文件是否存在，如果存在且auto_rename为True，则自动重命名
            if auto_rename and save_path.exists():
                stem = save_path.stem
                suffix = save_path.suffix
                parent = save_path.parent
                counter = 1
                while save_path.exists():
                    new_filename = f"{stem}_{counter}{suffix}"
                    save_path = parent / new_filename
                    counter += 1
        
        with open(save_path, 'wb') as f:
            f.write(image_data)

        print(f"💾 图片已保存至: {save_path.absolute()}")

        # 6. （可选）尝试用PIL展示图片（需要GUI环境）
        if show_preview:
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_data))
                img.show()
                print("🖼️  已在默认图片查看器中打开图像。")
            except ImportError:
                print("ℹ️  如需直接显示图片，请确保已安装Pillow库 (`pip install pillow`)。")
            except Exception as e:
                print(f"ℹ️  图片预览未启用: {e}")
        
        return {
            "success": True,
            "image_path": str(save_path.absolute()),
            "url": image_url,
            "prompt": prompt,
            "size": size
        }

    except Exception as e:
        error_msg = f"❌ 图像生成失败: {e}"
        print(error_msg)
        logging.error(error_msg)
        return {"success": False, "error": str(e)}

def generate_image_with_cogview3_flash(prompt, save_path=None, api_key=None, show_preview=False, auto_rename=True):
    """
    使用 CogView-3-Flash 模型生成图像并保存到本地（保持向后兼容）。
    
    Args:
        prompt (str): 生成图像的提示词
        save_path (str or Path, optional): 保存路径
        api_key (str, optional): 智谱AI的API密钥
        show_preview (bool): 是否显示预览
        auto_rename (bool): 当文件已存在时是否自动重命名
    
    Returns:
        dict: 包含生成结果的字典
    """
    return generate_image_with_cogview(
        prompt=prompt,
        api_key=api_key,
        size="1024x1024",
        n=1,
        quality="standard",
        save_path=save_path,
        show_preview=show_preview,
        auto_rename=auto_rename
    )


def batch_generate_images(prompts, api_key=None, size="1024x1024", save_dir=None, quality="standard", auto_rename=True):
    """
    批量生成图像
    
    Args:
        prompts (list): 提示词列表
        api_key (str, optional): 智谱AI的API密钥
        size (str): 图像尺寸
        save_dir (str or Path, optional): 保存目录
        quality (str): 图像质量
        auto_rename (bool): 当文件已存在时是否自动重命名
    
    Returns:
        list: 生成结果列表
    """
    if save_dir is None:
        save_dir = Path("./batch_images")
        save_dir.mkdir(exist_ok=True)
    else:
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
    
    results = []
    for i, prompt in enumerate(prompts):
        print(f"\n--- 正在生成第 {i+1}/{len(prompts)} 张图片 ---")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒的时间戳
        save_path = save_dir / f"image_{i+1:03d}_{timestamp}.png"
        result = generate_image_with_cogview(
            prompt=prompt,
            api_key=api_key,
            size=size,
            quality=quality,
            save_path=save_path,
            auto_rename=auto_rename
        )
        results.append(result)
    
    return results


def generate_with_custom_path(prompt, folder_path, file_name=None, api_key=None, size="1024x1024", quality="standard"):
    """
    使用自定义路径和文件名生成图像
    
    Args:
        prompt (str): 生成图像的提示词
        folder_path (str or Path): 自定义保存文件夹路径
        file_name (str, optional): 自定义文件名，如果不提供则根据提示词生成
        api_key (str, optional): 智谱AI的API密钥
        size (str): 图像尺寸
        quality (str): 图像质量
    
    Returns:
        dict: 包含生成结果的字典
    """
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    if file_name:
        save_path = folder_path / file_name
    else:
        # 根据提示词生成文件名
        safe_prompt = "".join(c for c in prompt if c.isalnum() or c in "-_ .")
        safe_prompt = safe_prompt.strip()[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = folder_path / f"{safe_prompt.replace(' ', '_')}_{timestamp}.png"
    
    return generate_image_with_cogview(
        prompt=prompt,
        api_key=api_key,
        size=size,
        quality=quality,
        save_path=save_path
    )


if __name__ == "__main__":
    # 示例：生成一张图片
    sample_prompt = "一只戴着潜水镜、在热带珊瑚礁中阅读古籍的橘猫，画面细腻，光影斑驳，水下摄影风格。"
    result = generate_image_with_cogview3_flash(sample_prompt, show_preview=True)
    
    if result["success"]:
        print(f"✅ 图像生成成功！保存在: {result['image_path']}")
    else:
        print(f"❌ 图像生成失败: {result['error']}")
    
    # 示例：使用自定义路径
    custom_result = generate_with_custom_path(
        prompt="一个发光的蓝色机器人",
        folder_path="./my_custom_images",
        file_name="robot_image.png",
        size="1024x1024"
    )
    
    if custom_result["success"]:
        print(f"✅ 自定义路径图像生成成功！保存在: {custom_result['image_path']}")
    else:
        print(f"❌ 自定义路径图像生成失败: {custom_result['error']}")
