#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟的text2image服务，用于演示MCP功能
"""
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse
import os
import sys

# 模拟生成图像的函数
def generate_image(prompt, width=512, height=512, negative_prompt=""):
    # 模拟图像生成时间
    time.sleep(2)
    
    # 返回模拟的图像生成结果
    return {
        "success": True,
        "image_url": f"https://example.com/generated_image_{int(time.time())}.png",
        "prompt": prompt,
        "width": width,
        "height": height,
        "negative_prompt": negative_prompt,
        "generation_time": 2.0
    }


class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 解析URL
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/mcp":
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request = json.loads(post_data)
                
                # 处理MCP协议
                response = self.handle_mcp_request(request)
                
                # 发送响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_error(400, f"Error processing request: {str(e)}")
        else:
            self.send_error(404)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/health":
            # 健康检查端点
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_error(404)

    def handle_mcp_request(self, request):
        """处理MCP请求"""
        if request.get("method") == "initialize":
            # 初始化请求
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": True
                    },
                    "serverInfo": {
                        "name": "text2image-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif request.get("method") == "notifications/initialized":
            # initialized通知
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {}
            }
        
        elif request.get("method") == "tools/list":
            # 工具列表
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "tool",
                            "name": "text-to-image",
                            "description": "Generate an image from text prompt",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "prompt": {"type": "string", "description": "The text prompt for image generation"},
                                    "width": {"type": "integer", "description": "Image width", "default": 512},
                                    "height": {"type": "integer", "description": "Image height", "default": 512},
                                    "negative_prompt": {"type": "string", "description": "Negative prompt to avoid certain elements", "default": ""}
                                },
                                "required": ["prompt"]
                            }
                        }
                    ]
                }
            }
        
        elif request.get("method") == "tools/call":
            # 工具调用
            params = request.get("params", {})
            tool_name = params.get("name")
            
            if tool_name == "text-to-image":
                args = params.get("arguments", {})
                prompt = args.get("prompt", "")
                width = args.get("width", 512)
                height = args.get("height", 512)
                negative_prompt = args.get("negative_prompt", "")
                
                # 生成图像
                result = generate_image(prompt, width, height, negative_prompt)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "image",
                                "url": result["image_url"],
                                "alt": prompt
                            },
                            {
                                "type": "text",
                                "text": f"Generated image with prompt: '{prompt}', size: {width}x{height}"
                            }
                        ]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request.get('method')}"
                }
            }


def run_server(port=8888):
    """启动服务器"""
    server = HTTPServer(('127.0.0.1', port), MCPHandler)
    print(f"Text2Image MCP Server running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Text to Image MCP Server')
    parser.add_argument('--port', type=int, default=8888, help='Port to run the server on')
    
    args = parser.parse_args()
    
    try:
        run_server(args.port)
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)