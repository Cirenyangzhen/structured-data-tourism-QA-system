# Scrapy settings for tourism_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from shutil import which
from selenium import webdriver
from selenium.webdriver.edge.service import Service  # 导入 Edge 的 Service 类
BOT_NAME = "tourism_scraper"

SPIDER_MODULES = ["tourism_scraper.spiders"]
NEWSPIDER_MODULE = "tourism_scraper.spiders"

# Selenium 配置（Edge 浏览器）
SELENIUM_DRIVER_NAME = 'edge'  # 使用 Edge 浏览器
SELENIUM_DRIVER_EXECUTABLE_PATH = "C:/Users/DZ/micro/msedgedriver.exe" # Edge 驱动路径
SELENIUM_DRIVER_ARGUMENTS = ['--headless', '--disable-gpu', '--no-sandbox']
# 使用 Service 类初始化驱动
SELENIUM_SERVICE = Service(executable_path=SELENIUM_DRIVER_EXECUTABLE_PATH)

# Selenium 中间件配置
DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800,  # 确保中间件启用
}

# 添加 WebDriver 初始化配置
SELENIUM_DRIVER_CLASS = webdriver.Edge  # 使用 Edge 驱动


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False  # 反爬虫设置，禁止遵循 robots.txt

# 代理设置
PROXY_LIST = [
    'http://user:pass@proxy1:port',
    'http://user:pass@proxy2:port',
]

# 配置最大并发请求数（默认：16）
#CONCURRENT_REQUESTS = 32

# 配置相同网站的请求延迟（默认：0）
#DOWNLOAD_DELAY = 3

# 禁用 cookies（默认启用）
#COOKIES_ENABLED = False

# 禁用 Telnet 控制台（默认启用）
#TELNETCONSOLE_ENABLED = False

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "tourism_scraper.middlewares.TourismScraperSpiderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'tourism_scraper.pipelines.MySQLPipeline': 1,  # 使用 MySQL pipeline
}

# Enable and configure the AutoThrottle extension (disabled by default)
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# 反爬配置
DOWNLOAD_DELAY = 7  # 设置下载延迟
ROBOTSTXT_OBEY = False  # 反爬虫设置，禁用 robots.txt

# 数据库配置
MYSQL_HOST = 'localhost'  # 数据库地址
MYSQL_DATABASE = 'tourism_db'  # 数据库名称
MYSQL_USER = 'root'  # 数据库用户名
MYSQL_PASSWORD = '123456'  # 数据库密码
