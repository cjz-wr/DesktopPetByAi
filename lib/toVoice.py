import asyncio
import warnings
import sys
import threading
import tempfile
import os
import lib.LogManager as LogManager
import logging


# 忽略Windows平台上与asyncio相关的ResourceWarning
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)


class TextToSpeech:
    def __init__(self, voice="zh-CN-XiaoyiNeural"):
        """
        初始化TTS引擎
        
        Args:
            voice (str): 语音模型名称，默认为"zh-CN-XiaoyiNeural"
        """

        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)

        self.voice = voice
        self._check_dependencies()
        
    
    def _check_dependencies(self):
        """检查并导入所需的依赖"""
        # 尝试导入edge_tts，如果未安装则提示用户
        try:
            import edge_tts
            self.edge_tts = edge_tts
        except ImportError:
            self.logger.error("未找到 edge-tts 库")
            self.logger.error("请先运行以下命令安装：")
            self.logger.error("pip install edge-tts")
            # print("错误：未找到 edge-tts 库")
            # print("请先运行以下命令安装：")
            # print("pip install edge-tts")
            sys.exit(1)

        # 尝试导入playsound，如果未安装则提示用户
        try:
            from playsound3 import playsound
            self.playsound = playsound
        except ImportError:
            self.logger.warning("警告：未找到 playsound 库，将只生成文件而不播放")
            self.logger.warning("如需播放音频，请运行以下命令安装：")
            self.logger.warning("pip install playsound")
            # print("警告：未找到 playsound 库，将只生成文件而不播放")
            # print("如需播放音频，请运行以下命令安装：")
            # print("pip install playsound")
            self.playsound = None
    
    async def generate_speech(self, text, output_file=None) -> None:
        """
        将文本转换为语音并保存为文件
        
        Args:
            text (str): 要转换为语音的文本
            output_file (str): 输出文件名，默认为None表示自动生成临时文件
        """
        # 如果没有提供输出文件名，则生成一个临时文件
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            output_file = temp_file.name
            temp_file.close()
        
        tts = self.edge_tts.Communicate(text=text, voice=self.voice)
        await tts.save(output_file)
        # print(f"语音文件 '{output_file}' 已生成！")
        self.logger.info(f"语音文件 '{output_file}' 已生成！")
        
        # 播放生成的音频文件
        if self.playsound:
            try:
                import pygame

                pygame.mixer.init()
                pygame.mixer.music.load(output_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
                # 播放完成后删除临时文件
                if 'temp_file' in locals():
                    try:
                        os.unlink(output_file)
                    except:
                        pass
            except Exception as e:
                # print(f"播放音频时出错: {e}")
                self.logger.error(f"播放音频时出错: {e}")
                # 出错时也尝试删除临时文件
                if 'temp_file' in locals():
                    try:
                        os.unlink(output_file)
                    except:
                        pass
        else:
            # print("未安装playsound库，跳过播放步骤。")
            self.logger.warning("未安装playsound库，跳过播放步骤。")
            # 不播放时删除临时文件
            if 'temp_file' in locals():
                try:
                    os.unlink(output_file)
                except:
                    pass
    
    def speak(self, text, output_file=None) -> None:
        """
        文本转语音并播放的同步接口
        
        Args:
            text (str): 要转换为语音的文本
            output_file (str): 输出文件名，默认为None表示自动生成临时文件
        """
        # 在Windows上避免Proactor事件循环关闭时的警告
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        try:
            asyncio.run(self.generate_speech(text, output_file))
        except KeyboardInterrupt:
            pass
    
    def speak_async(self, text, output_file=None) -> None:
        """
        文本转语音并播放的异步接口（在后台线程中运行）
        
        Args:
            text (str): 要转换为语音的文本
            output_file (str): 输出文件名，默认为None表示自动生成临时文件
        """
        def _speak_thread():
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.generate_speech(text, output_file))
            except Exception as e:
                # print(f"异步播放出错: {e}")
                self.logger.error(f"异步播放出错: {e}")
            finally:
                loop.close()
        
        # 启动后台线程执行异步任务
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
    
    def demo(self):
        """运行一个简单的示例程序"""
        self.speak("这是一个示例程序，请输入要转换成语音的文本：")
        text = "这是一个示例程序，请输入要转换成语音的文本："
        self.speak(text)
    
if __name__ == "__main__":
    tts = TextToSpeech()
    tts.demo()