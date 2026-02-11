import scrapy
from decimal import Decimal
import re
import mysql.connector
from scrapy.exceptions import IgnoreRequest
from scrapy_selenium import SeleniumRequest

class FoodSpider(scrapy.Spider):
    name = "food"
    # 在爬虫类修改 custom_settings
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # 基础延迟
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 随机化延迟（实际延迟为 2.5~7.5 秒）
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.dianping.com/',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
        },
        'COOKIES_ENABLED': True,  # 启用Cookie
    }
    
    start_urls = [
        "https://www.dianping.com/shop/GaMmWAdSi5uUx6BI",
        "https://www.dianping.com/shop/l8EyOmdyL5u1CkDj",
        "https://www.dianping.com/shop/H1XmtBP5PIHd1lsn",
    
        
    ]
    def start_requests(self):
        cookies = {
             "GSI": "#rf_syztwlb@210720a#sl_zdjlwxbdsb@211011l#rf_tsmbyrk@220309b#rf_syjgwlb@220829a",
            "HMACCOUNT": "58DD111B0500AC8A",
            "WEBDFPID": "x9884wx20vuv5vzx0wyx2765vvyz2z98804202zw56097958x2080306-...",
            "_hc.v": "ddecb6df-d80a-aa71-cae8-e4a043f32643.1741499844",
            "_lxsdk": "195797abdffc8-0083ebdf9176a9-4c657b58-102660-195797abdffc8",
            "_lxsdk_cuid": "195797abdffc8-0083ebdf9176a9-4c657b58-102660-195797abdffc8",
            "dper": "0202c82684e5fdce440f61b8702ad574c8a714698d989a2e409b7ac2b8df6b80...",
            "dplet": "68843cb624f63198d1be4d4d7ad7a8e6",
            "ll": "7fd06e815b796be3df069dec7836c3df",
            "s_ViewType": "10",
            "ua": "%E5%B0%8F%E5%A7%9A%E6%9C%80%E7%88%B1%E5%90%AC%E5%B9%BF%E6%92%AD",
        }
        for url in self.start_urls:
            yield SeleniumRequest(  # 使用 SeleniumRequest 发起请求
                url=url,
                cookies=cookies,
                callback=self.parse,
                wait_time=10
            )
    

    def parse(self, response):
        print(response.text)

    def parse(self, response):
        item = {}
        # 提取字段
        item['name'] = self.extract_name(response)
        item['address'] = self.extract_address(response)
        item['opening_hours'] = self.extract_opening_hours(response)
        item['type'] = self.extract_type(response)
        item['rating'] = self.extract_rating(response)
        item['price'] = self.extract_price(response)
       
        yield item

    def extract_name(self, response):
        return response.css('span.shopName::text').get(default='N/A').strip()

    def extract_address(self, response):
        address = response.css('span.addressText::text').get()
        return address.strip() if address else 'N/A'

    def extract_opening_hours(self, response):
        return response.css('span.biz-time::text').get(default='N/A').strip()

    def extract_type(self, response):
        return response.css('span.category::text').get(default='N/A').strip()

    def extract_rating(self, response):
        rating = response.css('div.star-score::text').get()
        try:
            return Decimal(rating.strip()) if rating else None
        except:
            return None

    def extract_price(self, response):
        price_text = response.css('div.price::text').get()
        if price_text:
            return re.search(r'¥(\d+)', price_text).group(1)  # 提取纯数字
        return 'N/A'

    def save_to_mysql(self, item):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                database='tourism_db',
                user='root',
                password='123456'
            )
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO Food (name, address, opening_hours, type, rating, price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                item['name'],
                item['address'],
                item['opening_hours'],
                item['type'],
                item['rating'],
                item['price']
            ))
            conn.commit()
        except Exception as e:
            self.logger.error(f"数据库插入失败: {str(e)}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
class CaptchaMiddleware:
    def process_response(self, request, response, spider):
        if 'verify.meituan.com' in response.url:
            spider.logger.warning('触发验证码，需人工处理！')
            raise IgnoreRequest  # 停止当前请求
        return response