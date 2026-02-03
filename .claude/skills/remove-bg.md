# Skill: 抠图 (Remove Background)

使用 Stability AI API 对图片进行抠图处理，去除背景生成透明 PNG。

## 触发方式
用户说"帮我抠图"、"抠一下"、"/remove-bg" 或提供图片并要求去除背景时触发。

## 执行步骤

1. **获取图片路径**：从用户消息中获取图片路径，或询问用户图片位置
2. **调用 API 抠图**：使用以下 Python 代码执行抠图

```python
import requests
import os
from datetime import datetime

API_KEY = 'sk-dqQck8SkRIYfb4bFnzMHwxRkagbbRhaHXMD84BADAJFQKOY0'
OUTPUT_DIR = '/Users/liuyishou/usr/projects/inbox/zimeiti-fabu/素材库Inbox/'

def remove_background(input_path):
    """抠图并保存到指定目录"""
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{original_name}_nobg_{timestamp}.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    print(f'处理中: {input_path}')

    response = requests.post(
        'https://api.stability.ai/v2beta/stable-image/edit/remove-background',
        headers={
            'authorization': f'Bearer {API_KEY}',
            'accept': 'image/*'
        },
        files={
            'image': open(input_path, 'rb')
        },
    )

    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f'成功! 输出: {output_path}')
        return output_path
    else:
        print(f'失败: {response.text}')
        return None

# 使用方法：
# remove_background('/path/to/your/image.png')
```

3. **展示结果**：读取并展示抠图后的图片给用户
4. **报告积分消耗**：每次抠图消耗 2 积分

## 输出目录
所有抠图结果保存到：
```
/Users/liuyishou/usr/projects/inbox/zimeiti-fabu/素材库Inbox/
```

## 文件命名规则
```
{原文件名}_nobg_{时间戳}.png
```
例如：`car_nobg_20260115_170500.png`

## 注意事项
- API Key 已内置，无需用户提供
- 输出为透明背景 PNG 格式
- 如果用户在对话中直接发送图片，需要获取图片的本地路径才能处理
