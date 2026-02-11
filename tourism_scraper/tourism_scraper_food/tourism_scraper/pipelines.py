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
        
        # 创建 Food 表（如果不存在），包括餐馆名称、地址、营业时间、菜品类型、评分、人均价格
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Food (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255),
                opening_hours VARCHAR(50),
                type VARCHAR(100),
                rating DECIMAL(3,1),
                price VARCHAR(50)
            )
        """)
    
    def process_item(self, item, spider):
        # 构建插入语句，只插入餐馆名称、地址、营业时间、菜品类型、评分、人均价格
        sql = """
            INSERT INTO Food (
                name, address, opening_hours, type, rating, price
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            item.get('name', 'N/A'),
            item.get('address', 'N/A'),
            item.get('opening_hours', 'N/A'),
            item.get('type', 'N/A'),
            item.get('rating', None),
            item.get('price', 'N/A')
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



