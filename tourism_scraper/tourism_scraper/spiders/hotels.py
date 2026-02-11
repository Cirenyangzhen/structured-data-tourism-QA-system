import scrapy
from decimal import Decimal
import re
import mysql.connector

class HotelsSpider(scrapy.Spider):
    name = 'hotels'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'FEED_EXPORT_ENCODING': 'utf-8'
    }


    start_urls = [
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=60623608&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=117485927&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=110425271&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=95765350&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=2727250&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120292195&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=116493227&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=109495360&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=111542853&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=95300794&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=95230908&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=91321860&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=106317676&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=8362389&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120878636&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120092947&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=92358056&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=72592336&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=90382598&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=113000538&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=70540463&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=85540689&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=106755228&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=808488&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=117764571&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=117007844&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=117849899&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=43579652&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120820487&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=126891141&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=119068516&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=100412527&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=108779794&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=126698869&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=106019279&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=97715723&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120462820&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=119117793&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=43132036&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=88774221&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=92659510&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=116575678&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=7514474&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=80289464&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=126734450&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=123340498&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=60623608&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=120292195&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=75437529&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=106395242&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=110614198&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=97291882&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1', 
        'https://hotels.ctrip.com/hotels/detail/?cityId=108&checkIn=2025-03-09&checkOut=2025-03-10&hotelId=106362009&adult=1&crn=1&children=0&highprice=-1&lowprice=0&listfilter=1',

        # 添加更多酒店详情页URL
    ]

    def parse(self, response):
        item = {}
        
        # 提取核心字段
        item['name'] = self.extract_text(response, 'h1.detail-headline_name::text')
        item['rating'] = self.extract_rating(response)
        item['address'] = self.extract_address(response)
        item['introduction'] = self.extract_introduction(response)
        
        
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

    def extract_introduction(self, response):
        intro_list = response.css('span.detail-headline_desc_text ::text').getall()
        # 将文本列表拼接为一个字符串，并过滤掉空白项
        introduction = ' '.join(text.strip() for text in intro_list if text.strip())
        return introduction if introduction else 'N/A'
    

    def save_to_mysql(self, item):
        conn = mysql.connector.connect(
            host='localhost',
            database='tourism_db',
            user='root',
            password='123456'
        )
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO Hotels (name, rating, address, introduction)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            item['name'],
            item['rating'],
            item['address'],
            item['introduction']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        