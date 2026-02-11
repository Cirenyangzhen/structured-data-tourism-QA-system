
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# pipelines.py
# pipelines.py

from scrapy.exceptions import DropItem

import pymysql
from itemadapter import ItemAdapter

class MySQLPipeline:
    def __init__(self, mysql_settings):
        self.mysql_settings = mysql_settings
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_settings={
                'host': crawler.settings.get('MYSQL_HOST'),
                'db': crawler.settings.get('MYSQL_DATABASE'),
                'user': crawler.settings.get('MYSQL_USER'),
                'password': crawler.settings.get('MYSQL_PASSWORD'),
                'charset': 'utf8mb4'
            }
        )
    
    def open_spider(self, spider):
        self.conn = pymysql.connect(**self.mysql_settings)
        self.cursor = self.conn.cursor()
        
        # 创建表（如果不存在），这里只保留爬虫中的字段
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Hotels (
                hotel_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                rating DECIMAL(3,2),
                address VARCHAR(255),
                introduction TEXT
            )
        """)
    
    def process_item(self, item, spider):
        # 构建插入语句，只插入 name, rating, address, introduction
        sql = """
            INSERT INTO Hotels (
                name, rating, address, introduction
            ) VALUES (%s, %s, %s, %s)
        """
        values = (
            item.get('name', 'N/A'),
            item.get('rating', None),
            item.get('address', 'N/A'),
            item.get('introduction', 'N/A')
        )
        
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DropItem(f"Error inserting item: {e}")
        
        return item
    
    def close_spider(self, spider):
        self.conn.close()




