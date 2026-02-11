from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import random

class TourismScraperSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)



class TourismScraperDownloaderMiddleware:
    @classmethod
    def _init_driver(cls, spider):
        # 确保路径格式正确
        driver_path = spider.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        
        if not os.path.isfile(driver_path):
            spider.logger.error(f"驱动程序路径不存在或错误: {driver_path}")
            raise Exception(f"驱动程序路径不存在: {driver_path}")

        # 配置浏览器的选项
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')  # 根据需要添加其他参数

        # 使用 Service 代替 executable_path 来设置驱动路径
        service = Service(executable_path=driver_path)  # 使用正确的路径初始化Service
        cls.driver = webdriver.Edge(service=service, options=options)  # 使用Edge驱动

    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # 执行 Selenium 请求
        self.driver.get(request.url)
        body = self.driver.page_source
        return spider._handle_selenium_response(request, body)


    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

    def close(self):
        # 确保关闭 driver
        if hasattr(self, 'driver'):
            self.driver.quit()

class ProxyMiddleware:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_list=crawler.settings.get('PROXY_LIST')
        )

    def process_request(self, request, spider):
        proxy = random.choice(self.proxy_list)
        request.meta['proxy'] = proxy


class CaptchaMiddleware:
    def process_response(self, request, response, spider):
        if 'verify.meituan.com' in response.url:
            spider.logger.error('触发验证码，需人工处理！')
            raise IgnoreRequest()
        return response
