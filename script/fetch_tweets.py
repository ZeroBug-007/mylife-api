import feedparser
import json
import os
import re
from datetime import datetime

# 这里填你 Zeabur 生成的那个 RSSHub 地址
# 格式：https://你的域名.zeabur.app/twitter/user/你的用户名
# 建议：为了安全，这个地址最好通过环境变量传进来，下面代码里我会写两种方式
RSS_URL = os.environ.get('RSS_URL')

def clean_html(raw_html):
    """
    因为 RSSHub 返回的是带 HTML 标签的内容，我们需要把 <br> 换成换行，
    把其他标签去掉，只留纯文本，方便前端自己写样式。
    """
    # 1. 把 <br> 换成换行符
    text = re.sub(r'<br\s*/*>', '\n', raw_html)
    # 2. 去掉所有 HTML 标签 (<p>, <div>, <img> 等)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def fetch_tweets():
    if not RSS_URL:
        print("❌ 错误：没有找到 RSS_URL 环境变量，请检查 GitHub Actions 设置！")
        return

    print(f"📡 正在连接 RSS 源: {RSS_URL} ...")
    feed = feedparser.parse(RSS_URL)

    if feed.bozo:
        print("⚠️  解析 RSS 时遇到了一些小问题，但我们将尝试继续...")

    if len(feed.entries) == 0:
        print("📭  没有获取到推文，可能是 Cookie 过期了，或者你最近没发推。")
        return

    tweets_data = []

    for entry in feed.entries:
        # 提取图片：RSSHub 通常把图片放在 description 里的 <img src="...">
        # 或者 enclosure 属性里，这里做一个简单的提取逻辑
        images = []

        # 尝试从 description 中提取图片链接
        img_urls = re.findall(r'<img src="([^"]+)"', entry.description)
        # RSSHub 的图片通常是 https://pbs.twimg.com/...
        # 为了防盗链，有时你前端可能需要用 images.weserv.nl 这种服务代理一下，或者直接用
        images.extend(img_urls)

        # 清洗正文
        content_text = clean_html(entry.description)

        # 格式化时间 (RSS 的时间格式比较乱，这里转成标准的 YYYY-MM-DD HH:mm)
        try:
            # entry.published_parsed 是一个时间元组
            dt = datetime(*entry.published_parsed[:6])
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = entry.published

        tweet = {
            "id": entry.guid,  # 推文唯一ID
            "link": entry.link, # 推文原链接
            "date": date_str,   # 发布时间
            "content": content_text, # 纯文本内容
            "images": images    # 图片列表
        }
        tweets_data.append(tweet)

    # 保存到文件
    # 假设我们要存到 public/data/tweets.json (根据你的项目结构调整)
    # 如果文件夹不存在，先创建
    output_dir = 'public/data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'tweets.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tweets_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 成功抓取了 {len(tweets_data)} 条推文，已保存到 {output_path}")

if __name__ == "__main__":
    fetch_tweets()
