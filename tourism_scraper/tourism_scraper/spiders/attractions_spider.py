import scrapy 
from decimal import Decimal
from itemadapter import ItemAdapter
import re
import mysql.connector

class AttractionsSpider(scrapy.Spider):
    name = 'attractions_spider'

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    start_urls = [
        'https://you.ctrip.com/sight/126/4620.html', 'https://you.ctrip.com/sight/nyingchi126/5712897.html?scene=online', 
        'https://you.ctrip.com/sight/gongbogyamda120396/1696477.html?scene=online', 'https://you.ctrip.com/sight/bome2436/1837467.html?scene=online', 
        'https://you.ctrip.com/sight/nyingchi126/77603.html?scene=online', 'https://you.ctrip.com/sight/nyingchi126/5132025.html?scene=online', 
        'https://you.ctrip.com/sight/nyingchi126/1696531.html?scene=online', 'https://you.ctrip.com/sight/gongbogyamda120396/128971.html?scene=online', 
        'https://you.ctrip.com/sight/gongbogyamda120396/1493308.html?scene=online', 'https://you.ctrip.com/sight/nyingchi126/128994.html?renderPlatform=',
        'https://you.ctrip.com/sight/nyingchi126/128994.html?renderPlatform=', 'https://you.ctrip.com/sight/nyingchi126/135615.html?renderPlatform=', 
        'https://you.ctrip.com/sight/nyingchi126/1409721.html?renderPlatform=',
        'https://you.ctrip.com/sight/nyingchi126/4615.html?renderPlatform=', 'https://you.ctrip.com/sight/126/128988.html',
        'https://you.ctrip.com/sight/nyingchi126/128988.html?renderPlatform=', 'https://you.ctrip.com/sight/nyingchi126/1696911.html?renderPlatform=', 'https://you.ctrip.com/sight/nyingchi126/5069534.html?renderPlatform=', 
    ]

    def parse(self, response):
        item = {}

        item['name'] = self.clean_text(self.extract_text(response, 'div.title h1::text'))
        item['rating'] = self.extract_rating(response)
        item['address'] = self.clean_text(self.extract_text(response, 'div.baseInfoItem p.baseInfoText::text'))
        item['opening_hours'] = self.clean_text(self.extract_opening_hours(response))
        item['official_phone'] = self.clean_text(self.extract_text(response, 'div.baseInfoItem p.baseInfoText::text'))
        item['description'] = self.clean_text(self.extract_description(response))
        item['level'] = self.clean_text(self.extract_level(response))
        item['nearby_attractions'] = self.extract_nearby_attractions(response)
        item['nearby_food'] = self.extract_nearby_food(response)

        # 存入数据库前做去重判断
        self.save_to_mysql(item)

        yield item

    def extract_text(self, response, css_selector):
        return response.css(css_selector).get(default='N/A').strip()

    def clean_text(self, text):
        text = re.sub(r'<[^>]+>', '', text)  # 去除HTML标签
        text = re.sub(r'[\r\n\t\xa0]', ' ', text)  # 替换特殊字符
        text = re.sub(r'\s{2,}', ' ', text)  # 多空格合并为一个
        return text.strip()
  
    def extract_rating(self, response):
        rating = response.css('div.commentScore p.commentScoreNum::text').get(default='0').strip()
        try:
            return Decimal(rating)
        except:
            return None

    def extract_opening_hours(self, response):
        return response.css('p.baseInfoText.cursor.openTimeText::text').get(default='N/A').strip()

    def extract_description(self, response):
        description = response.css('div.moduleContent div.LimitHeightText p::text').getall()
        return ' '.join([p.strip() for p in description]) if description else 'N/A'

    def extract_level(self, response):
        return response.css('div.titleTips span::text').get(default='N/A').strip()

    def extract_nearby_attractions(self, response):
        attractions = []
        attraction_section = response.css('div.moduleitem')
        for attraction in attraction_section:
            name = self.clean_text(attraction.css('div.contentTitle::text').get(default='N/A'))
            distance = self.clean_text(attraction.css('div.distanceDes::text').get(default='N/A'))
            attractions.append({'name': name, 'distance': distance})
        return attractions if attractions else 'N/A'

    def extract_nearby_food(self, response):
        foods = []
        food_section = response.css('div.moduleitem')
        for food in food_section:
            name = self.clean_text(food.css('div.contentTitle::text').get(default='N/A'))
            score = self.clean_text(food.css('span.commentScore::text').get(default='N/A'))
            distance = self.clean_text(food.css('div.distanceDes::text').get(default='N/A'))
            foods.append({'name': name, 'score': score, 'distance': distance})
        return foods if foods else 'N/A'

    def is_duplicate(self, cursor, name, address):
        query = "SELECT COUNT(*) FROM Attractions WHERE name = %s AND address = %s"
        cursor.execute(query, (name, address))
        return cursor.fetchone()[0] > 0

    def save_to_mysql(self, item):
        conn = mysql.connector.connect(
            host='localhost', database='tourism_db', user='root', password='123456'
        )
        cursor = conn.cursor()

        if self.is_duplicate(cursor, item['name'], item['address']):
            print(f"重复数据：{item['name']}，已跳过存储")
            cursor.close()
            conn.close()
            return

        insert_query = """
        INSERT INTO Attractions (name, rating, address, opening_hours, official_phone, description, nearby_attractions, nearby_food, level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            item['name'], item['rating'], item['address'], item['opening_hours'], item['official_phone'],
            item['description'], str(item['nearby_attractions']), str(item['nearby_food']), item['level']
        ))
        conn.commit()
        cursor.close()
        conn.close()
