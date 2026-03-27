import requests
from langchain_core.tools import tool

@tool
def web_fetch(url: str, extract_links: bool = False) -> str:
    """通过URL抓取网页内容。
    参数:
        url: 完整的URL地址，如 https://example.com
        extract_links: 是否同时提取页面中的链接，默认 False
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return "错误：请安装 bs4: pip install beautifulsoup4"

        soup = BeautifulSoup(response.text, "html.parser")

        # 提取链接
        links_text = ""
        if extract_links:
            links = []
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if text and href.startswith("http"):
                    links.append(f"- [{text}]({href})")
            if links:
                links_text = "\n\n## 页面链接\n" + "\n".join(links[:20])

        # 移除无用标签
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        max_length = 4000
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "\n...(已截断)"

        return clean_text + links_text

    except Exception as e:
        return f"错误：{str(e)}"