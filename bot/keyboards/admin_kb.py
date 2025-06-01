from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard():
    """
    Create main admin keyboard.
    """
    buttons = [
        [InlineKeyboardButton(text="📝 Опубликовать меню в канал", callback_data="publish_menu")],
        [InlineKeyboardButton(text="📊 Обновить прайс-листы", callback_data="update_prices")],
        [InlineKeyboardButton(text="⚙️ Настройки меню", callback_data="menu_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_price_update_keyboard():
    """
    Create keyboard for updating price posts.
    """
    buttons = [
        [InlineKeyboardButton(text="📱 Новые iPhone", callback_data="update_price:new_iphone")],
        [InlineKeyboardButton(text="📱 Б/У iPhone", callback_data="update_price:used_iphone")],
        [InlineKeyboardButton(text="🎧 AirPods и Apple Watch", callback_data="update_price:airpods_watch")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_menu_settings_keyboard():
    """
    Create keyboard for menu settings.
    """
    buttons = [
        [InlineKeyboardButton(text="📌 Закрепить/Открепить сообщение", callback_data="toggle_pin")],
        [InlineKeyboardButton(text="🔄 Обновить меню", callback_data="refresh_menu")],
        [InlineKeyboardButton(text="📄 Настроить статические пункты", callback_data="static_items")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard(action, item_id=None):
    """
    Create confirmation keyboard.
    
    Args:
        action: Action to confirm (e.g., 'publish', 'update')
        item_id: Optional item ID for context
    """
    confirm_data = f"confirm_{action}"
    cancel_data = "cancel"
    
    if item_id:
        confirm_data += f":{item_id}"
    
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    """
    Create a simple back button keyboard.
    """
    buttons = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_static_items_keyboard(items):
    """
    Create keyboard for managing static menu items.
    
    Args:
        items: List of static menu items from the database
    """
    buttons = []
    
    # Добавляем кнопки для каждого статического пункта меню
    for item in items:
        # Показываем статус URL для каждого пункта
        url_status = "✅" if item['url'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{url_status} {item['title']}", 
            callback_data=f"update_static:{item['id']}"
        )])
    
    # Добавляем кнопку возврата
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_settings")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
