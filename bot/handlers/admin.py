from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import (
    get_admin_main_keyboard, 
    get_price_update_keyboard, 
    get_menu_settings_keyboard, 
    get_confirmation_keyboard, 
    get_back_keyboard, 
    get_static_items_keyboard,
    get_channel_menu_keyboard
)
from database import Database
from config import ADMIN_IDS, CHANNEL_ID

# Initialize router
router = Router()

# States for admin actions
class AdminStates(StatesGroup):
    waiting_for_price_url = State()
    waiting_for_static_url = State()
    waiting_for_confirmation = State()


# Middleware to check admin permissions
@router.message.middleware()
@router.callback_query.middleware()
async def admin_middleware(handler, event, data):
    user_id = event.from_user.id
    
    if user_id not in ADMIN_IDS:
        if isinstance(event, Message):
            await event.answer("⛔ У вас нет доступа к этой команде.")
        elif isinstance(event, CallbackQuery):
            await event.answer("⛔ У вас нет доступа к этой функции.", show_alert=True)
        return
    
    return await handler(event, data)


# Command handlers
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command to show admin panel."""
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_admin_main_keyboard()
    )


# Callback query handlers
@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Handle back button to return to admin panel."""
    await callback.message.edit_text(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "publish_menu")
async def publish_menu(callback: CallbackQuery):
    """Handle menu publication request."""
    db = Database()
    
    # Get all menu items
    menu_items = await db.get_menu_items()
    
    if not menu_items:
        await callback.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Меню пусто. Необходимо сначала настроить элементы меню.",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    # Update dynamic price URLs
    menu_items = [dict(item) for item in menu_items]  # Convert all rows to dicts first
    for item in menu_items:
        if item['is_dynamic']:
            price_post = await db.get_price_post(item['id'])
            if price_post:
                # Convert price_post to dict before accessing it
                price_post_dict = dict(price_post)
                item['url'] = price_post_dict['post_url']
    
    # Generate preview text
    preview_text = "📋 <b>Предпросмотр меню</b>\n\n"
    
    # Add price items
    price_items = [item for item in menu_items if item['type'] == 'price']
    if price_items:
        for item in price_items:
            url_status = "✅ URL установлен" if item['url'] else "❌ URL не установлен"
            preview_text += f"• {item['title']} - {url_status}\n"
    
    preview_text += "\n<i>Остальные пункты меню будут добавлены автоматически.</i>\n\n"
    preview_text += "Опубликовать это меню в канал?"
    
    await callback.message.edit_text(
        preview_text,
        reply_markup=get_confirmation_keyboard("publish")
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_publish")
async def confirm_publish(callback: CallbackQuery, state: FSMContext):
    """Handle confirmation of menu publication."""
    db = Database()
    
    try:
        # Get all menu items
        menu_items = await db.get_menu_items()
        
        # Update dynamic price URLs
        menu_items = [dict(item) for item in menu_items]  # Convert all rows to dicts first
        for item in menu_items:
            if item['is_dynamic']:
                price_post = await db.get_price_post(item['id'])
                if price_post:
                    # Convert price_post to dict before accessing it
                    price_post_dict = dict(price_post)
                    item['url'] = price_post_dict['post_url']
        
        # Generate menu text
        menu_text = "🛍️ <b>АКТУАЛЬНЫЕ ЦЕНЫ</b> 🛍️\n\n"
        menu_text += "Выберите интересующий вас раздел:"
        
        # Create inline keyboard
        keyboard = await get_channel_menu_keyboard(menu_items)
        
        # Get existing menu config
        config = await db.get_menu_config()
        
        # Send or edit message in channel
        bot = callback.bot
        
        if config and config['menu_message_id']:
            try:
                # Try to edit existing message
                message = await bot.edit_message_text(
                    chat_id=config['channel_id'] or CHANNEL_ID,
                    message_id=config['menu_message_id'],
                    text=menu_text,
                    reply_markup=keyboard
                )
                is_new = False
            except Exception:
                # If edit fails, send new message
                message = await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=menu_text,
                    reply_markup=keyboard
                )
                is_new = True
        else:
            # Send new message
            message = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=menu_text,
                reply_markup=keyboard
            )
            is_new = True
        
        # Pin message if needed
        is_pinned = config['is_pinned'] if config else True
        if is_pinned and is_new:
            await bot.pin_chat_message(
                chat_id=CHANNEL_ID,
                message_id=message.message_id,
                disable_notification=True
            )
        
        # Update config in database
        await db.update_menu_config(
            message_id=message.message_id,
            channel_id=CHANNEL_ID,
            is_pinned=is_pinned
        )
        
        # Notify admin
        await callback.message.edit_text(
            "✅ <b>Успешно!</b>\n\n"
            f"Меню {'обновлено' if not is_new else 'опубликовано'} в канале "
            f"и {'закреплено' if is_pinned else 'не закреплено'}.",
            reply_markup=get_back_keyboard()
        )
    
    except Exception as e:
        # Handle errors
        await callback.message.edit_text(
            f"❌ <b>Ошибка при публикации меню</b>\n\n"
            f"Детали: {str(e)}",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "update_prices")
async def update_prices(callback: CallbackQuery):
    """Handle price update request."""
    await callback.message.edit_text(
        "💰 <b>Обновление прайс-листов</b>\n\n"
        "Выберите прайс-лист для обновления:",
        reply_markup=get_price_update_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("update_price:"))
async def select_price_to_update(callback: CallbackQuery, state: FSMContext):
    """Handle selection of price list to update."""
    price_type = callback.data.split(":")[1]
    
    # Map price type to database item
    price_type_map = {
        "new_iphone": ("📱 Прайс на НОВЫЕ iPhone 📱", 1),
        "used_iphone": ("📱 Прайс на Б/У iPhone 📱", 2),
        "airpods_watch": ("🎧 Прайс на AirPods и Apple Watch ⌚", 3)
    }
    
    title, position = price_type_map.get(price_type, ("Неизвестный прайс", 0))
    
    # Store the selected price type in state
    await state.update_data(price_type=price_type, position=position, title=title)
    
    # Set state to waiting for URL
    await state.set_state(AdminStates.waiting_for_price_url)
    
    # Get current URL if exists
    db = Database()
    menu_items = await db.get_menu_items(dynamic_only=True)
    
    current_url = "Не установлен"
    for item in menu_items:
        if item['title'] == title:
            price_post = await db.get_price_post(item['id'])
            if price_post and price_post['post_url']:
                current_url = price_post['post_url']
            break
    
    await callback.message.edit_text(
        f"🔄 <b>Обновление прайс-листа</b>\n\n"
        f"Выбран: <b>{title}</b>\n\n"
        f"Текущая ссылка: <code>{current_url}</code>\n\n"
        f"Пришлите новую ссылку на пост с прайс-листом.\n"
        f"Ссылка должна быть в формате: <code>https://t.me/channel/123</code>",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_price_url)
async def process_price_url(message: Message, state: FSMContext):
    """Process the price URL provided by admin."""
    url = message.text.strip()
    
    # Basic URL validation
    if not (url.startswith('https://t.me/') or url.startswith('http://t.me/')):
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Ссылка должна быть в формате: <code>https://t.me/channel/123</code>\n"
            "Пожалуйста, пришлите корректную ссылку или нажмите 'Назад' для отмены.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Get data from state
    data = await state.get_data()
    title = data.get('title')
    
    # Show confirmation
    await message.answer(
        f"🔄 <b>Подтверждение обновления</b>\n\n"
        f"Прайс-лист: <b>{title}</b>\n"
        f"Новая ссылка: <code>{url}</code>\n\n"
        f"Подтвердите обновление:",
        reply_markup=get_confirmation_keyboard("update_url")
    )
    
    # Update state with URL
    await state.update_data(url=url)
    await state.set_state(AdminStates.waiting_for_confirmation)


@router.callback_query(AdminStates.waiting_for_confirmation, F.data == "confirm_update_url")
async def confirm_update_url(callback: CallbackQuery, state: FSMContext):
    """Handle confirmation of price URL update."""
    # Get data from state
    data = await state.get_data()
    title = data.get('title')
    url = data.get('url')
    
    db = Database()
    
    try:
        # Find the menu item by title
        menu_items = await db.get_menu_items(dynamic_only=True)
        item_id = None
        
        for item in menu_items:
            if item['title'] == title:
                item_id = item['id']
                break
        
        if not item_id:
            # Item not found, create it
            item_id = await db.add_menu_item(
                type='price',
                title=title,
                url=None,
                position=data.get('position', 0),
                is_dynamic=True
            )
        
        # Update price post
        await db.update_price_post(item_id, url)
        
        # Clear state
        await state.clear()
        
        # Show success message
        await callback.message.edit_text(
            "✅ <b>Успешно!</b>\n\n"
            f"Прайс-лист <b>{title}</b> обновлен.\n\n"
            "Не забудьте опубликовать меню в канал, чтобы изменения вступили в силу.",
            reply_markup=get_admin_main_keyboard()
        )
    
    except Exception as e:
        # Handle errors
        await callback.message.edit_text(
            f"❌ <b>Ошибка при обновлении прайс-листа</b>\n\n"
            f"Детали: {str(e)}",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "menu_settings")
async def menu_settings(callback: CallbackQuery):
    """Handle menu settings request."""
    await callback.message.edit_text(
        "⚙️ <b>Настройки меню</b>\n\n"
        "Выберите действие:",
        reply_markup=get_menu_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_pin")
async def toggle_pin(callback: CallbackQuery):
    """Handle pin/unpin toggle request."""
    db = Database()
    config = await db.get_menu_config()
    
    if not config or not config['menu_message_id']:
        await callback.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Меню еще не опубликовано в канале.",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    # Toggle pin status
    new_pin_status = not config['is_pinned']
    
    try:
        bot = callback.bot
        
        if new_pin_status:
            # Pin message
            await bot.pin_chat_message(
                chat_id=config['channel_id'] or CHANNEL_ID,
                message_id=config['menu_message_id'],
                disable_notification=True
            )
            pin_text = "закреплено"
        else:
            # Unpin message
            await bot.unpin_chat_message(
                chat_id=config['channel_id'] or CHANNEL_ID,
                message_id=config['menu_message_id']
            )
            pin_text = "откреплено"
        
        # Update config in database
        await db.update_menu_config(
            message_id=config['menu_message_id'],
            channel_id=config['channel_id'] or CHANNEL_ID,
            is_pinned=new_pin_status
        )
        
        # Show success message
        await callback.message.edit_text(
            f"✅ <b>Успешно!</b>\n\n"
            f"Меню {pin_text} в канале.",
            reply_markup=get_menu_settings_keyboard()
        )
    
    except Exception as e:
        # Handle errors
        await callback.message.edit_text(
            f"❌ <b>Ошибка при изменении статуса закрепления</b>\n\n"
            f"Детали: {str(e)}",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "refresh_menu")
async def refresh_menu(callback: CallbackQuery):
    """Handle menu refresh request."""
    await callback.message.edit_text(
        "🔄 <b>Обновление меню</b>\n\n"
        "Вы уверены, что хотите обновить меню в канале?",
        reply_markup=get_confirmation_keyboard("publish")
    )
    await callback.answer()


@router.callback_query(F.data == "static_items")
async def static_items(callback: CallbackQuery):
    """Handle static items management request."""
    db = Database()
    
    # Получаем все статические пункты меню (тип 'info')
    menu_items = await db.get_menu_items()
    static_items = [dict(item) for item in menu_items if item['type'] == 'info']
    
    if not static_items:
        await callback.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Статические пункты меню не найдены.",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📄 <b>Управление статическими пунктами меню</b>\n\n"
        "Выберите пункт для настройки URL:\n"
        "✅ - URL установлен\n"
        "❌ - URL не установлен",
        reply_markup=get_static_items_keyboard(static_items)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("update_static:"))
async def select_static_to_update(callback: CallbackQuery, state: FSMContext):
    """Handle selection of static item to update."""
    item_id = int(callback.data.split(":")[1])
    
    # Получаем информацию о выбранном пункте меню
    db = Database()
    item = await db.get_menu_item(item_id)
    
    if not item:
        await callback.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Пункт меню не найден.",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    # Сохраняем ID пункта меню в состоянии
    await state.update_data(item_id=item_id, title=item['title'])
    
    # Устанавливаем состояние ожидания URL
    await state.set_state(AdminStates.waiting_for_static_url)
    
    current_url = "Не установлен" if not item['url'] else item['url']
    
    await callback.message.edit_text(
        f"🔄 <b>Обновление URL для статического пункта</b>\n\n"
        f"Выбран: <b>{item['title']}</b>\n\n"
        f"Текущая ссылка: <code>{current_url}</code>\n\n"
        f"Пришлите новую ссылку на пост в канале.\n"
        f"Ссылка должна быть в формате: <code>https://t.me/channel/123</code>\n\n"
        f"Для удаления URL отправьте сообщение 'удалить'",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_static_url)
async def process_static_url(message: Message, state: FSMContext):
    """Process the static item URL provided by admin."""
    url = message.text.strip()
    
    # Проверяем, если пользователь хочет удалить URL
    if url.lower() in ["удалить", "delete", "remove", "clear"]:
        url = ""
    # Базовая валидация URL
    elif not (url.startswith('https://t.me/') or url.startswith('http://t.me/')):
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Ссылка должна быть в формате: <code>https://t.me/channel/123</code>\n"
            "Пожалуйста, пришлите корректную ссылку или отправьте 'удалить' для удаления URL.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    title = data.get('title')
    
    # Показываем подтверждение
    if url:
        confirm_text = (
            f"🔄 <b>Подтверждение обновления</b>\n\n"
            f"Пункт меню: <b>{title}</b>\n"
            f"Новая ссылка: <code>{url}</code>\n\n"
            f"Подтвердите обновление:"
        )
    else:
        confirm_text = (
            f"🔄 <b>Подтверждение удаления URL</b>\n\n"
            f"Пункт меню: <b>{title}</b>\n"
            f"URL будет удален.\n\n"
            f"Подтвердите удаление:"
        )
    
    await message.answer(
        confirm_text,
        reply_markup=get_confirmation_keyboard("update_static_url")
    )
    
    # Обновляем состояние с URL
    await state.update_data(url=url)
    await state.set_state(AdminStates.waiting_for_confirmation)


@router.callback_query(AdminStates.waiting_for_confirmation, F.data == "confirm_update_static_url")
async def confirm_update_static_url(callback: CallbackQuery, state: FSMContext):
    """Handle confirmation of static item URL update."""
    # Получаем данные из состояния
    data = await state.get_data()
    item_id = data.get('item_id')
    title = data.get('title')
    url = data.get('url')
    
    # Обновляем URL в базе данных
    db = Database()
    success = await db.update_menu_item(item_id, url=url)
    
    if success:
        # Очищаем состояние
        await state.clear()
        
        # Показываем сообщение об успехе
        if url:
            success_text = (
                f"✅ <b>URL успешно обновлен</b>\n\n"
                f"Пункт меню: <b>{title}</b>\n"
                f"Новая ссылка: <code>{url}</code>"
            )
        else:
            success_text = (
                f"✅ <b>URL успешно удален</b>\n\n"
                f"Пункт меню: <b>{title}</b>"
            )
        
        # Получаем обновленный список статических пунктов
        menu_items = await db.get_menu_items()
        static_items = [dict(item) for item in menu_items if item['type'] == 'info']
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_static_items_keyboard(static_items)
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка при обновлении URL</b>\n\n"
            f"Не удалось обновить URL для пункта меню.",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery):
    """Handle statistics request."""
    db = Database()
    
    try:
        # Get menu config
        config = await db.get_menu_config()
        
        # Get menu items count
        menu_items = await db.get_menu_items()
        dynamic_items = [item for item in menu_items if item['is_dynamic']]
        
        # Prepare statistics text
        stats_text = "📊 <b>Статистика</b>\n\n"
        
        if config and config['menu_message_id']:
            stats_text += f"• Меню опубликовано в канале: ✅\n"
            stats_text += f"• ID сообщения: <code>{config['menu_message_id']}</code>\n"
            stats_text += f"• Статус закрепления: {'✅ Закреплено' if config['is_pinned'] else '❌ Не закреплено'}\n"
        else:
            stats_text += "• Меню не опубликовано в канале: ❌\n"
        
        stats_text += f"\n• Всего пунктов меню: {len(menu_items)}\n"
        stats_text += f"• Динамических прайс-листов: {len(dynamic_items)}\n"
        
        # Add dynamic items status
        if dynamic_items:
            stats_text += "\n<b>Статус прайс-листов:</b>\n"
            
            for item in dynamic_items:
                price_post = await db.get_price_post(item['id'])
                url_status = "✅" if price_post and price_post['post_url'] else "❌"
                stats_text += f"• {item['title']}: {url_status}\n"
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_back_keyboard()
        )
    
    except Exception as e:
        # Handle errors
        await callback.message.edit_text(
            f"❌ <b>Ошибка при получении статистики</b>\n\n"
            f"Детали: {str(e)}",
            reply_markup=get_back_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Handle cancellation of any action."""
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
    
    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>\n\n"
        "Вернуться в главное меню администратора?",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
