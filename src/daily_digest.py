from datetime import datetime
import os
import requests
import json


def send_to_coze_dodigest():
    api_url = os.getenv('COZE_API_DIGEST_WEBHOOK')  # Must set this secret in GitHub
    if not api_url:
        raise ValueError("COZEWEBHOOK environment variable not set!")
    headers = {
        "Authorization": os.getenv('COZE_API_DIGEST_WEBHOOK_AUTHORIZATION'),
        "Content-Type": "application/json"
    }
    try:
        # paper = (title, link, github_links, abstract, authors)
        paper_data = {
            "paper_class": paper[0]
        }

        response = requests.post(
            api_url,
            data=json.dumps(paper_data),
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"成功发送论文到COZE: {paper_data['title']}")
        else:
            print(f"发送COZE失败: {paper_data['title']}, 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
        # 避免频繁请求，可以添加延迟
        import time
        time.sleep(1)  # 1秒间隔
        
    except Exception as e:
        print(f"发送论文到COZE时出错 {paper_data['title']}: {str(e)}")

if __name__ == '__main__':