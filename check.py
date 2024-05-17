import asyncio
import json
import aiofiles
import time
from aiohttp import ClientSession, ClientTimeout

BUFFER_SIZE = 5

async def check_url(session: ClientSession, url: str, max_retries=3):
    """
    检查 URL 并返回响应的 JSON 和延迟，如果条件满足。
    """
    payload = json.dumps({
        "text": "hello world",
        "source_lang": "EN",
        "target_lang": "ZH"
    })
    headers = {'Content-Type': 'application/json'}

    for attempt in range(1, max_retries + 1):
        start_time = time.time()  # 开始计时
        try:
            requests_url = url + "/translate"
            async with session.post(requests_url, headers=headers, data=payload) as response:
                response_json = await response.json()
                if response.status == 200 and response_json.get("data"):
                    # 如果"data"字段存在且为真值
                    latency = time.time() - start_time  # 计算延迟
                    return url, latency
        except Exception as e:
            print(f"Error for URL {url} (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:  # 延迟重试
                await asyncio.sleep(1)

    return None, None  # 返回 None 表示失败

async def process_urls(input_file, success_file):
    """
    处理输入的 URL 列表，收集有效的 URL 及其延迟，并按延迟排序后写入文件。
    """
    unique_urls = set()
    results = []

    try:
        async with aiofiles.open(success_file, 'r') as existing_file:
            existing_urls = {line.strip() async for line in existing_file}
        unique_urls.update(existing_urls)
    except FileNotFoundError:
        pass

    async with aiofiles.open(input_file, 'r') as file:
        urls = [line.strip() async for line in file]

    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        tasks = [check_url(session, url) for url in urls]
        for future in asyncio.as_completed(tasks):
            url, latency = await future
            if url and latency is not None:
                results.append((url, latency))

    # 按延迟排序
    sorted_results = sorted(results, key=lambda x: x[1])

    # 分批写入文件
    for i in range(0, len(sorted_results), BUFFER_SIZE):
        buffer = sorted_results[i:i+BUFFER_SIZE]
        urls_to_write = [url for url, _ in buffer]
        async with aiofiles.open(success_file, 'a') as valid_file:
            await valid_file.write('\n'.join(urls_to_write) + '\n')

asyncio.run(process_urls('input.txt', 'success.txt'))
print("all done")
