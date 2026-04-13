import scrapy
from decimal import Decimal
import re
import mysql.connector

class HotelsSpider(scrapy.Spider):
    name = 'hotels_spider'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    start_urls = [
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=95300794&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        
       
    ]

    def parse(self, response):
        item = {}
        
        # 提取核心字段
        item['name'] = self.extract_text(response, 'h1.detail-headline_name::text')
        item['rating'] = self.extract_rating(response)
        item['address'] = self.extract_address(response)
        item['phone'] = self.extract_phone(response)
        item['opening_year'] = self.extract_opening_year(response)
        
        # 保存到数据库
        self.save_to_mysql(item)
        
        yield item

    def extract_text(self, response, selector):
        return response.css(selector).get(default='N/A').strip()

    def extract_rating(self, response):
        rating = response.css('b.detail-headreview_score_value::text').get()
        try:
            return Decimal(rating) if rating else None
        except:
            return None

    def extract_address(self, response):
        address = response.css('span.detail-headline_position_text::text').get()
        return address.strip() if address else 'N/A'

    def extract_phone(self, response):
        # 从描述文本中提取电话号码
        desc_text = response.css('div.detail-headline_desc_text::text').get()
        if desc_text:
            phone_match = re.search(r'(\d{3,4}-\d{7,8})', desc_text)
            return phone_match.group(0) if phone_match else 'N/A'
        return 'N/A'

    def extract_opening_year(self, response):
        opening_text = response.css('span.detail-headline_desc_ky::text').get()
        if opening_text:
            year_match = re.search(r'开业：(\d{4})', opening_text)
            return year_match.group(1) if year_match else 'N/A'
        return 'N/A'

    def save_to_mysql(self, item):
        conn = mysql.connector.connect(
            host='localhost',
            database='tourism_db',
            user='root',
            password='123456'
        )
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO Hotels (name, rating, address, phone)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            item['name'],
            item['rating'],
            item['address'],
            item['phone']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()