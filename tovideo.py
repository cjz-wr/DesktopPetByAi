# cogvideox_demo.py - 智谱AI CogVideoX-Flash 视频生成完整示例
import os
import time
import requests
from pathlib import Path
from zhipuai import ZhipuAI

def generate_video_with_cogvideox(api_key, prompt, image_path=None):
    """
    使用CogVideoX-Flash生成并下载视频。

    Args:
        api_key (str): 智谱AI平台的API Key。
        prompt (str): 视频描述，建议使用详细、结构化的英文。
        image_path (str, optional): 图生视频模式下，本地图片的路径。如为None，则执行文生视频。
    """
    # 1. 初始化客户端
    client = ZhipuAI(api_key=api_key)

    print("🚀 开始提交视频生成任务...")
    print(f"📝 提示词: {prompt}")

    try:
        # 2. 准备请求参数（共通部分）
        # 注意：参数名和可选值请以智谱AI官方最新文档为准[citation:6]
        request_params = {
            "model": "CogVideoX-Flash",  # 指定模型
            "prompt": prompt,
            "size": "1080x1920",          # 视频分辨率，支持"720x1280", "1920x1080"等[citation:2]
            "duration": 5,                # 视频时长（秒），通常支持5或10秒
            "fps": 30,                    # 帧率，例如30或60[citation:2]
            "quality": "quality",         # 质量选项：'quality'（质量优先）或'speed'（速度优先）[citation:1]
            "with_audio": False,          # 是否生成音频
            # 注意：原 `watermark_enabled` 参数已无效，请勿添加
        }

        # 3. 根据模式添加特定参数
        if image_path and os.path.exists(image_path):
            # === 图生视频模式 ===
            print("🎨 模式: 图生视频")
            # 将本地图片转换为Base64字符串[citation:1]
            import base64
            with open(image_path, 'rb') as img_file:
                base64_data = base64.b64encode(img_file.read()).decode('utf-8')
            # 关键：按API要求格式化Base64数据[citation:1]
            request_params["image_url"] = f"data:image/jpeg;base64,{base64_data}"
        else:
            # === 文生视频模式 ===
            if image_path:
                print(f"⚠️  未找到图片文件 {image_path}，将切换到文生视频模式。")
            else:
                print("✍️ 模式: 文生视频")

        # 4. 提交异步生成任务
        print("⏳ 正在向API提交任务...")
        response = client.videos.generations(**request_params)
        task_id = response.id
        print(f"✅ 任务提交成功！任务ID: {task_id}")

        # 5. 轮询查询任务状态
        print("⏳ 视频生成中，请耐心等待（通常需要几十秒到几分钟）...")
        max_attempts = 60  # 最大轮询次数（假设每次间隔5秒，总时长5分钟）
        for attempt in range(max_attempts):
            result = client.videos.retrieve_videos_result(id=task_id)
            
            if result.task_status == 'SUCCESS':
                print("🎉 视频生成成功！")
                # 获取视频URL
                video_url = result.video_result[0].url
                # 尝试获取封面图URL
                cover_url = getattr(result.video_result[0], 'cover_image_url', None)
                break
            elif result.task_status == 'PROCESSING':
                print(f"  轮询中... ({attempt + 1}/{max_attempts})")
                time.sleep(5)  # 等待5秒后再次查询
            else:
                # 处理失败或其它状态
                print(f"❌ 任务失败或异常，状态: {result.task_status}")
                if hasattr(result, 'message'):
                    print(f"   错误信息: {result.message}")
                return
        else:
            print("❌ 轮询超时，视频可能仍在生成中，请稍后通过任务ID手动查询。")
            return

        # 6. 下载视频到本地
        print("💾 开始下载视频文件...")
        video_data = requests.get(video_url).content
        # 生成保存文件名（包含时间戳和模式）
        prefix = "img2vid" if image_path and os.path.exists(image_path) else "txt2vid"
        timestamp = int(time.time())
        save_path = Path(f"./{prefix}_video_{timestamp}.mp4")
        
        with open(save_path, 'wb') as f:
            f.write(video_data)
        print(f"✅ 视频已保存至: {save_path.absolute()}")

        # 7. （可选）下载封面图
        if cover_url:
            try:
                cover_data = requests.get(cover_url).content
                cover_path = Path(f"./{prefix}_cover_{timestamp}.jpg")
                with open(cover_path, 'wb') as f:
                    f.write(cover_data)
                print(f"🖼️  封面图已保存至: {cover_path.absolute()}")
            except Exception as e:
                print(f"⚠️  封面图下载失败: {e}")

        print("\n✨ 所有流程已完成！")

    except KeyError as e:
        print(f"❌ API响应结构可能已更新，缺少键: {e}")
        print("   建议查阅最新的官方API文档。")
    except Exception as e:
        print(f"❌ 程序执行过程中出现错误: {type(e).__name__}")
        print(f"   错误详情: {e}")
        # 调试时可打印请求参数（注意隐藏敏感信息）
        # import json
        # safe_params = request_params.copy()
        # if 'image_url' in safe_params:
        #     safe_params['image_url'] = '[BASE64_DATA_HIDDEN]'
        # print(f"   请求参数: {json.dumps(safe_params, indent=2, ensure_ascii=False)}")

def main():
    """主函数，用于演示两种生成模式。"""
    # === 重要：请在此处配置你的API Key ===
    # 安全提示：最佳实践是将API Key设置为系统环境变量，例如 `ZHIPUAI_API_KEY`

    #key已经失效，请自行申请替换
    YOUR_API_KEY = os.getenv("a805cdc6d6e848d4a180360daa037a3a.yueKhq5poWrpZw9a", "a805cdc6d6e848d4a180360daa037a3a.yueKhq5poWrpZw9a")  # 请替换
    
    # if YOUR_API_KEY == "a805cdc6d6e848d4a180360daa037a3a.yueKhq5poWrpZw9a":
    #     print("⚠️  请先修改代码中的 `YOUR_API_KEY` 为你的真实API Key。")
    #     print("   或设置系统环境变量 `ZHIPUAI_API_KEY`。")
    #     return

    # === 示例1: 文生视频 (Text-to-Video) ===
    print("=" * 50)
    print("示例1: 测试文生视频")
    print("=" * 50)
    text_prompt = (
        "一只毛茸茸的柴犬在山顶上看日出"
    )
    generate_video_with_cogvideox(api_key=YOUR_API_KEY, prompt=text_prompt)

    # === 示例2: 图生视频 (Image-to-Video) ===
    # 取消以下注释，并确保 `your_image.jpg` 图片存在，即可测试图生视频
    """
    print("\n" + "=" * 50)
    print("示例2: 测试图生视频")
    print("=" * 50)
    image_file_path = "path/to/your/image.jpg"  # 请替换为你的图片路径
    image_prompt = "The character in the picture starts to dance gracefully."  # 描述动作
    generate_video_with_cogvideox(
        api_key=YOUR_API_KEY,
        prompt=image_prompt,
        image_path=image_file_path
    )
    """

if __name__ == "__main__":
    main()