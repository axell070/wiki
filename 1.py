import sys
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from collections import deque

# === Настройки ===
MAX_LINKS_PER_PAGE = 10   # Максимум ссылок с одной страницы
MAX_DEPTH = 5             # Глубина поиска

def normalize_url(url):
    if not url.startswith("http"):
        return "https://"  + url
    return url

def is_valid_link(url, base_netloc):
    parsed = urlparse(url)
    if parsed.netloc != base_netloc:
        return False
    path = parsed.path
    if not path.startswith("/wiki/"):
        return False
    if ':' in path or '#' in path or '?' in path:
        return False
    if any(keyword in path for keyword in ["Main_Page", "Special:", "Wikipedia:", "Help:", "Category:", "Portal:"]):
        return False
    return True

def get_links_from_references(url, base_netloc):
    try:
        headers = {"User-Agent": "Wiki6DegreesBot/1.0"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            print(f"[ERROR] Failed to load {url}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        references = soup.find_all('div', {'class': 'reflist'})

        links = set()
        for ref in references:
            for a_tag in ref.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                full_url = normalize_url(full_url)

                if is_valid_link(full_url, base_netloc):
                    links.add(full_url)
                    if len(links) >= MAX_LINKS_PER_PAGE:
                        break  # Ограничиваем число ссылок

        print(f"[INFO] Found {len(links)} links on {url}")
        return list(links)

    except Exception as e:
        print(f"[ERROR] Error fetching {url}: {e}")
        return []

def bfs(start_url, end_url, base_netloc, rate_limit):
    delay = 1.0 / rate_limit
    visited = {start_url}
    queue = deque([(start_url, 0, [start_url])])

    while queue:
        current_url, depth, path = queue.popleft()

        if depth >= MAX_DEPTH:
            continue

        if current_url == end_url:
            print(f"[SUCCESS] Path found with length {depth}: {' => '.join(path)}")
            return path

        print(f"[INFO] Visiting {current_url}, depth: {depth}")
        for link in get_links_from_references(current_url, base_netloc):
            if link not in visited:
                visited.add(link)
                queue.append((link, depth + 1, path + [link]))
                time.sleep(delay)

    print("[FAILURE] No path found within 5 steps")
    return None

def main():
    if len(sys.argv) != 4:
        print("Usage: python main.py <url1> <url2> <rate_limit>")
        return

    url1 = normalize_url(sys.argv[1].strip('/'))
    url2 = normalize_url(sys.argv[2].strip('/'))

    try:
        rate_limit = int(sys.argv[3])
    except:
        print("Rate limit must be an integer")
        return

    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    if parsed1.netloc != parsed2.netloc:
        print("Error: URLs must be on the same Wikipedia language version")
        return

    base_netloc = parsed1.netloc

    print("[PROCESS] Searching from url1 to url2...")
    path1 = bfs(url1, url2, base_netloc, rate_limit)

    print("[PROCESS] Searching from url2 to url1...")
    path2 = bfs(url2, url1, base_netloc, rate_limit)

    # === Вывод результата в консоль ===
    if path2:
        print("url2 =>[" + "]=>[".join(path2[1:-1]) + "]=>" + "url1")
    else:
        print("No path found from url2 to url1 within 5 steps")

    if path1:
        print("url1 =>[" + "]=>[".join(path1[1:-1]) + "]=>" + "url2")
    else:
        print("No path found from url1 to url2 within 5 steps")

if __name__ == "__main__":
    main()