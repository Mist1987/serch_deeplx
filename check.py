import asyncio
import json
import aiofiles
from aiohttp import ClientSession, ClientTimeout

async def check_url(session: ClientSession, url: str, max_retries=3):
    """
    检查 URL 并翻译文本，如果满足条件则返回URL和响应时间。
    """
    payload = json.dumps({
        "text": "hello world",
        "source_lang": "EN",
        "target_lang": "ZH"
    })
    headers = {'Content-Type': 'application/json'}
    
    for attempt in range(1, max_retries + 1):
        start_time = asyncio.get_event_loop().time()
        try:
            async with session.post(url, headers=headers, data=payload) as response:
                response_json = await response.json()
                # 优化判断逻辑
                if response.status == 200 and 'data' in response_json and len(str(response_json.get("data"))) > 0:
                    latency = asyncio.get_event_loop().time() - start_time
                    return (url, latency)
        except Exception as e:
            print(f"Error for URL {url} (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                await asyncio.sleep(1)
    
    return (None, None)

async def process_urls(file_path):
    """
    处理文件中的URL列表，验证每个URL，只保留有效的URL，并按延迟排序后覆盖写入原文件。
    处理重复的URL，确保每个URL只被检查一次。
    """
    timeout = ClientTimeout(total=5)
    async with aiofiles.open(file_path, 'r') as file:
        urls = {line.strip() async for line in file}  # 使用集合去重
    
    async with ClientSession(timeout=timeout) as session:
        tasks = [check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    # 移除无效结果，并按延迟排序
    valid_results = sorted((url for url in results if url[0] is not None), key=lambda x: x[1])
    
    # 清空并更新文件
    async with aiofiles.open(file_path, 'w') as file:
        for url, _ in valid_results:
            await file.write(url + '\n')

def list_file(input_file, output_file):
    """
    将输入文件中的 URL 按行写入输出文件
    :param input_file: 输入文件
    :param output_file: 输出文件
    """
    with open(input_file, 'r') as input_file_content:
        lines = input_file_content.readlines()

    flattened_lines = ','.join(line.strip() for line in lines)

    with open(output_file, 'w') as result_file:
        result_file.write(flattened_lines)


asyncio.run(process_urls('API.txt'))
list_file('API.txt', 'success_result.txt')
print("All done.")