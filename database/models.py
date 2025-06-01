import aiosqlite
import os
from config import DB_PATH

class Database:
    """Database class for managing SQLite operations."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        
    async def create_tables(self):
        """Create necessary tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create menu_config table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS menu_config (
                    id INTEGER PRIMARY KEY,
                    menu_message_id INTEGER,
                    channel_id TEXT,
                    is_pinned BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create menu_items table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    position INTEGER NOT NULL,
                    is_dynamic BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create price_posts table for dynamic content
            await db.execute('''
                CREATE TABLE IF NOT EXISTS price_posts (
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER,
                    post_url TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES menu_items (id) ON DELETE CASCADE
                )
            ''')
            
            await db.commit()
    
    async def get_menu_config(self):
        """Get current menu configuration."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM menu_config LIMIT 1') as cursor:
                return await cursor.fetchone()
    
    async def update_menu_config(self, message_id, channel_id, is_pinned=True):
        """Update menu configuration."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO menu_config (id, menu_message_id, channel_id, is_pinned)
                VALUES (1, ?, ?, ?)
            ''', (message_id, channel_id, is_pinned))
            await db.commit()
    
    async def get_menu_items(self, dynamic_only=False):
        """Get all menu items, optionally filtered by dynamic status."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM menu_items'
            if dynamic_only:
                query += ' WHERE is_dynamic = 1'
            query += ' ORDER BY position'
            
            async with db.execute(query) as cursor:
                return await cursor.fetchall()
    
    async def get_menu_item(self, item_id):
        """Get a specific menu item by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)) as cursor:
                return await cursor.fetchone()
    
    async def add_menu_item(self, type, title, url=None, position=0, is_dynamic=False):
        """Add a new menu item."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO menu_items (type, title, url, position, is_dynamic)
                VALUES (?, ?, ?, ?, ?)
            ''', (type, title, url, position, is_dynamic))
            await db.commit()
            return cursor.lastrowid
    
    async def update_menu_item(self, item_id, **kwargs):
        """Update an existing menu item."""
        allowed_fields = {'type', 'title', 'url', 'position', 'is_dynamic'}
        fields = [f"{k} = ?" for k in kwargs.keys() if k in allowed_fields]
        values = [v for k, v in kwargs.items() if k in allowed_fields]
        
        if not fields:
            return False
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE menu_items SET {', '.join(fields)} WHERE id = ?",
                (*values, item_id)
            )
            await db.commit()
            return True
    
    async def delete_menu_item(self, item_id):
        """Delete a menu item."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
            await db.commit()
    
    async def get_price_post(self, item_id):
        """Get the latest price post for a menu item."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM price_posts WHERE item_id = ? ORDER BY updated_at DESC LIMIT 1',
                (item_id,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def update_price_post(self, item_id, post_url):
        """Update or create a price post for a menu item."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO price_posts (item_id, post_url)
                VALUES (?, ?)
            ''', (item_id, post_url))
            await db.commit()
    
    async def initialize_default_menu(self):
        """Initialize the default menu structure if no items exist."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM menu_items')
            count = await cursor.fetchone()
            
            if count[0] == 0:
                # Add dynamic price items
                new_iphone_id = await self.add_menu_item(
                    'price', '📱 Прайс на НОВЫЕ iPhone 📱', None, 1, True
                )
                used_iphone_id = await self.add_menu_item(
                    'price', '📱 Прайс на Б/У iPhone 📱', None, 2, True
                )
                airpods_watch_id = await self.add_menu_item(
                    'price', '🎧 Прайс на AirPods и Apple Watch ⌚', None, 3, True
                )
                
                # Add static info items
                await self.add_menu_item('info', '✅ Гарантия', None, 4, False)
                await self.add_menu_item('info', '🏠 Адрес / Как нас найти?', None, 5, False)
                await self.add_menu_item('info', '💳 Рассрочка / Кредит от 1%', None, 6, False)
                await self.add_menu_item('info', '🚚 Доставка', None, 7, False)
                await self.add_menu_item('info', '💰 Оплата', None, 8, False)
                await self.add_menu_item('info', '‼ Ответы на часто задаваемые вопросы', None, 9, False)
                await self.add_menu_item('contact', '✍ Написать МЕНЕДЖЕРУ @artem_orsk', '@artem_orsk', 10, False)
                
                # Initialize empty price posts for dynamic items
                await self.update_price_post(new_iphone_id, '')
                await self.update_price_post(used_iphone_id, '')
                await self.update_price_post(airpods_watch_id, '')
