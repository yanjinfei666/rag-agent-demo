"""
Day 5：asyncio异步编程
实战：对比同步和异步请求的耗时差异
"""

import asyncio
import time
import httpx  # pip install httpx


# ============ 1. 异步基础 ============
print("=" * 20, "异步基础", "=" * 20)

async def say_hello(name, delay):
    """异步函数示例"""
    print(f"  开始: {name} (等待{delay}秒)")
    await asyncio.sleep(delay)  # 模拟IO操作
    print(f"  完成: {name}")
    return f"{name}完成于{delay}秒后"

async def basic_demo():
    """基础异步演示"""
    print("创建3个异步任务...")
    
    # 并发执行（总耗时是最大值，不是总和）
    results = await asyncio.gather(
        say_hello("任务A", 2),
        say_hello("任务B", 1),
        say_hello("任务C", 3),
    )
    
    print("\n所有结果:", results)

asyncio.run(basic_demo())


# ============ 2. 同步 vs 异步对比 ============
print("\n" + "=" * 20, "同步 vs 异步", "=" * 20)

# 模拟的URL列表
URLS = [
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
]


def sync_fetch(url):
    """同步请求（使用普通requests会阻塞，这里用httpx的同步模式模拟）"""
    with httpx.Client(timeout=10) as client:
        response = client.get(url)
        return response.status_code


async def async_fetch(url):
    """异步请求"""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        return response.status_code


async def compare_sync_vs_async():
    """对比同步和异步的耗时"""
    
    # === 同步版本 ===
    print("【同步请求】")
    print(f"请求 {len(URLS)} 个URL...")
    start = time.time()
    
    results_sync = []
    for url in URLS:
        try:
            status = sync_fetch(url)
            results_sync.append(status)
            print(f"  ✓ {url} → {status}")
        except Exception as e:
            print(f"  ✗ {url} → {e}")
    
    sync_time = time.time() - start
    print(f"同步总耗时: {sync_time:.2f} 秒")
    
    # === 异步版本 ===
    print("\n【异步请求】")
    print(f"请求 {len(URLS)} 个URL...")
    start = time.time()
    
    tasks = [async_fetch(url) for url in URLS]
    results_async = await asyncio.gather(*tasks, return_exceptions=True)
    
    for url, result in zip(URLS, results_async):
        if isinstance(result, Exception):
            print(f"  ✗ {url} → {result}")
        else:
            print(f"  ✓ {url} → {result}")
    
    async_time = time.time() - start
    print(f"异步总耗时: {async_time:.2f} 秒")
    
    # === 结论 ===
    print("\n" + "=" * 40)
    print(f"📊 性能对比:")
    print(f"  同步耗时: {sync_time:.2f}s")
    print(f"  异步耗时: {async_time:.2f}s")
    if async_time > 0:
        print(f"  提速倍数: {sync_time/async_time:.1f}x")
    print("=" * 40)
    print("💡 结论：异步IO可以显著提升IO密集型任务的效率")


# 运行对比（需要网络）
try:
    asyncio.run(compare_sync_vs_async())
except Exception as e:
    print(f"网络请求失败（可能是URL不可达）: {e}")
    print("这是正常现象，重点理解async/await的写法即可")


# ============ 3. 实战：异步文件处理 ============
print("\n" + "=" * 20, "实战：异步文件处理", "=" * 20)

async def async_read_file(file_path):
    """异步读取文件（模拟，实际文件IO在Python中仍是同步的）"""
    print(f"  开始读取: {file_path}")
    # 真实项目中使用 aiofiles 库实现真正的异步文件IO
    await asyncio.sleep(0.5)  # 模拟IO操作
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"  完成读取: {file_path} ({len(content)}字符)")
    return content


async def async_write_file(file_path, content):
    """异步写入文件"""
    print(f"  开始写入: {file_path}")
    await asyncio.sleep(0.5)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  完成写入: {file_path}")


async def batch_file_process():
    """批量处理文件"""
    import os
    
    # 准备测试文件
    os.makedirs("data/async_test", exist_ok=True)
    
    # 创建10个测试文件
    for i in range(10):
        file_path = f"data/async_test/test_{i}.txt"
        await async_write_file(file_path, f"这是测试文件{i}的内容\n" * 1000)
    
    # 并发读取所有文件
    files = [f"data/async_test/test_{i}.txt" for i in range(10)]
    
    start = time.time()
    results = await asyncio.gather(*[async_read_file(f) for f in files])
    elapsed = time.time() - start
    
    total_chars = sum(len(r) for r in results)
    print(f"\n✓ 并发读取10个文件完成")
    print(f"  总字符数: {total_chars:,}")
    print(f"  耗时: {elapsed:.2f}秒")


asyncio.run(batch_file_process())

print("\n🎉 Day 5 完成！")
