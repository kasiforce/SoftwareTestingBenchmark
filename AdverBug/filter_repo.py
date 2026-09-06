import requests
import time
import os
import json

# 从环境变量读取 GitHub Token（避免硬编码）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("请先设置环境变量 GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

# 搜索条件（第一阶段；第二阶段逐仓库筛查见 screen_java_repo.py / screen_py_repo.py）
# language 由 main() 里按 --language 参数拼接
QUERY_TMPL = (
    "stars:1000..5000 "
    "pushed:2026-01-01..2026-12-31 "
    "size:1024..102400 "          # 10MB = 10240KB, 100MB = 102400KB
    "language:{language} "
    "fork:false archived:false "  # 排除 fork 和已归档仓库
    "-topic:android "             # 排除 Android 应用（多为 Gradle/非服务端项目）
)
# license 用客户端过滤（Search API 的 q= 不支持 license:(a OR b) 组合语法）：
# 只保留宽松许可，允许再分发抽取的代码片段
ALLOWED_LICENSES = {"apache-2.0", "mit", "bsd-3-clause"}

BASE_URL = "https://api.github.com/search/repositories"

def search_repositories(query, max_pages=1):
    """
    使用 GitHub Search API 分页获取所有匹配仓库。
    注意：未认证请求每分钟10次，认证后每分钟30次，这里做了简单限速处理。
    """
    repos = []
    page = 1
    while page <= max_pages:
        params = {
            "q": query,
            "per_page": 100,   # 最大100
            "page": page,
            "sort": "stars",       # 按 star 降序，后续筛查可从高 star 开始优先
            "order": "desc",
        }
        print(f"正在请求第 {page} 页...")
        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 403:
            # 速率限制，读取 X-RateLimit-Reset 头并等待
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = reset_time - time.time() + 1
            print(f"触发速率限制，等待 {wait:.0f} 秒...")
            time.sleep(wait)
            continue

        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        repos.extend(items)
        print(f"本页获取 {len(items)} 个仓库，累计 {len(repos)} 个")

        # 检查是否还有下一页
        total_count = data.get("total_count", 0)
        if len(repos) >= total_count:
            break

        page += 1
        time.sleep(2)  # 礼貌性延迟，避免触发速率限制

    return repos

def save_to_csv(repos, filename="github_repos_java.csv"):
    import csv
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "full_name", "html_url", "stargazers_count", "size_kb", "pushed_at", "language",
            "created_at", "license", "forks_count", "default_branch", "description",
        ])
        for repo in repos:
            writer.writerow([
                repo["full_name"],
                repo["html_url"],
                repo["stargazers_count"],
                repo["size"],
                repo["pushed_at"],
                repo.get("language", ""),
                repo.get("created_at", ""),
                (repo.get("license") or {}).get("spdx_id", ""),
                repo.get("forks_count", ""),
                repo.get("default_branch", ""),
                (repo.get("description") or "").replace("\n", " ")[:200],
            ])
    print(f"结果已保存到 {filename}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="第一阶段：GitHub 搜索候选仓库")
    parser.add_argument("--language", default="Java", choices=["Java", "Python", "JavaScript"],
                        help="仓库语言（Java→screen_java_repo.py，Python→screen_py_repo.py，"
                             "JavaScript→screen_js_repo.py）")
    parser.add_argument("--max-pages", type=int, default=10, help="最多抓取的页数（每页100条）")
    parser.add_argument("--output", default=None,
                        help="结果 CSV 路径（默认 github_repos_<language小写>.csv）")
    args = parser.parse_args()

    query = QUERY_TMPL.format(language=args.language)
    output = args.output or f"github_repos_{args.language.lower()}.csv"
    repos = search_repositories(query, max_pages=args.max_pages)
    before = len(repos)
    repos = [r for r in repos
             if (r.get("license") or {}).get("spdx_id", "").lower() in ALLOWED_LICENSES]
    print(f"\n共获取 {before} 个仓库，license 过滤后剩 {len(repos)} 个")
    if repos:
        save_to_csv(repos, output)
        print("前几个仓库示例：")
        for repo in repos[:5]:
            print(f"  - {repo['full_name']} | ★{repo['stargazers_count']} | {repo['size']}KB | pushed: {repo['pushed_at']}")

if __name__ == "__main__":
    main()