# -*- coding: utf-8 -*-
"""
测试代理连接
"""
from config import USE_PROXY, PROXY_HOST, PROXY_PORT

print("="*80)
print("代理配置检查")
print("="*80)

print(f"\n代理启用：{'是' if USE_PROXY else '否'}")
print(f"代理地址：{PROXY_HOST}")
print(f"代理端口：{PROXY_PORT}")

# 测试代理连接
if USE_PROXY:
    print("\n测试代理连接...")
    try:
        import urllib.request
        
        # 设置代理处理器
        proxy = urllib.request.ProxyHandler({
            'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
            'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
        })
        opener = urllib.request.build_opener(proxy)
        urllib.request.install_opener(opener)
        
        # 测试 Google
        try:
            response = opener.open('https://www.google.com', timeout=5)
            print(f"✓ Google 连接成功 (状态码：{response.getcode()})")
        except Exception as e:
            print(f"✗ Google 连接失败：{e}")
        
        # 测试 Telegram 官网
        try:
            response = opener.open('https://telegram.org', timeout=5)
            print(f"✓ Telegram.org 连接成功 (状态码：{response.getcode()})")
        except Exception as e:
            print(f"✗ Telegram.org 连接失败：{e}")
            
    except ImportError:
        print("⚠ 无法导入 urllib.request，跳过网络测试")
    
    print("\n提示：如果代理测试失败，请检查：")
    print("1. 代理软件是否运行")
    print("2. 代理端口是否正确")
    print("3. 防火墙设置")
else:
    print("\n⚠ 代理未启用，如果需要连接 Telegram，建议启用代理")
    print("\n启用方法：")
    print("1. 编辑 .env 文件")
    print("2. 设置 USE_PROXY=true")
    print("3. 设置 PROXY_HOST=127.0.0.1")
    print("4. 设置 PROXY_PORT=7890")

print("\n" + "="*80)
