from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_channel_menu_keyboard(menu_items):
    """
    Create channel menu keyboard from menu items.
    
    Args:
        menu_items: List of menu item dictionaries from the database
    
    Returns:
        InlineKeyboardMarkup: Formatted menu keyboard
    """
    # Group items by type to organize them
    price_items = []
    info_items = []
    contact_items = []
    
    for item in menu_items:
        if item['type'] == 'price':
            price_items.append(item)
        elif item['type'] == 'info':
            info_items.append(item)
        elif item['type'] == 'contact':
            contact_items.append(item)
    
    # Prepare the keyboard buttons
    buttons = []
    
    # Add price items (always 1 per row)
    for item in price_items:
        url = item['url']
        # For dynamic items, we'll use the URL from price_posts table
        # This is handled in the handler function
        if url:
            buttons.append([InlineKeyboardButton(text=item['title'], url=url)])
        else:
            # Placeholder for items that don't have URLs yet
            buttons.append([InlineKeyboardButton(text=item['title'], callback_data=f"menu_item:{item['id']}")])
    
    # Add info items (2 per row when possible)
    info_row = []
    for item in info_items:
        # Если у пункта есть URL, используем его для перехода на пост в канале
        if item['url']:
            info_row.append(InlineKeyboardButton(text=item['title'], url=item['url']))
        else:
            # Если URL нет, используем callback как раньше
            info_row.append(InlineKeyboardButton(text=item['title'], callback_data=f"menu_item:{item['id']}"))
        
        if len(info_row) == 2:
            buttons.append(info_row)
            info_row = []
    
    # Add any remaining info items
    if info_row:
        buttons.append(info_row)
    
    # Add contact items (always 1 per row)
    for item in contact_items:
        if item['url'] and item['url'].startswith('@'):
            # This is a username link
            buttons.append([InlineKeyboardButton(text=item['title'], url=f"https://t.me/{item['url'][1:]}")])
        elif item['url']:
            # This is a regular URL
            buttons.append([InlineKeyboardButton(text=item['title'], url=item['url'])])
        else:
            buttons.append([InlineKeyboardButton(text=item['title'], callback_data=f"menu_item:{item['id']}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
