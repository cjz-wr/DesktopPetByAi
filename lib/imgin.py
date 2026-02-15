import os
import base64
from zhipuai import ZhipuAI
import lib.LogManager
import logging,json

async def analyze_image_with_ai(image_path, api_key=None, model="glm-4v-flash", prompt_text="请描述这张图片的内容"):
    """
    使用AI分析图片内容
    :param image_path: 图片文件路径
    :param api_key: 智谱AI的API密钥，如果为None则使用默认密钥
    :param model: 使用的模型名称，默认为glm-4v-flash
    :param prompt_text: 提供给AI的提示文本
    :return: AI对图片的分析结果，如果出错则返回错误信息
    """
    lib.LogManager.init_logging()
    logger = logging.getLogger(__name__)

    with open("demo_setting.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        api_key = config.get("ai_key", None)
    if api_key is None:
        logger.critical("请提供有效的API密钥")
        return "错误：请提供有效的API密钥"

    client = ZhipuAI(api_key=api_key)

    # 检查文件是否存在
    if not os.path.exists(image_path):
        return f"错误：找不到图片文件，请检查路径：{image_path}"

    try:
        # 读取图片并转换为Base64
        with open(image_path, "rb") as img_file:
            file_data = img_file.read()
            # 根据文件扩展名确定MIME类型
            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith(".gif"):
                mime_type = "image/gif"
            img_base64 = base64.b64encode(file_data).decode("utf-8")
            # 构造正确的 data URL
            data_url = f"data:{mime_type};base64,{img_base64}"

        # 调用视觉模型
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url  # 传递完整的 data URL
                            }
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"API调用失败: {e}"


def analyze_local_image(image_path, api_key="2f9aa59b1c404314833c10bff0d71f8b.r18TsE7fFcL8CSqz", 
                      model="glm-4v-flash", prompt_text="请详细描述这张图片的内容"):
    """
    使用智谱AI分析本地图像文件
    这是一个兼容旧版本的函数
    :param image_path: 本地图像文件路径
    :param api_key: 智谱AI的API密钥
    :param model: 使用的模型名称
    :param prompt_text: 提示文本
    :return: API响应结果
    """
    return analyze_image_with_ai(image_path, api_key, model, prompt_text)


if __name__ == "__main__":
    # 示例：使用本地图片路径
    local_image_path = r"D:\code\python\desktop_pet\main\img\3.png"
    
    result = analyze_image_with_ai(local_image_path)
    print(result)