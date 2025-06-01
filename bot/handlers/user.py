from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

from bot.keyboards import get_admin_main_keyboard
from database import Database
from config import ADMIN_IDS

# Initialize router
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    greeting = (
        f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
        f"Я бот для управления меню в Telegram-канале."
    )
    
    if is_admin:
        greeting += (
            "\n\n✅ У вас есть права администратора.\n"
            "Используйте команду /admin для доступа к панели управления."
        )
        await message.answer(greeting)
    else:
        greeting += (
            "\n\nℹ️ Этот бот предназначен только для администраторов канала."
        )
        await message.answer(greeting)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    help_text = (
        "📚 <b>Справка по командам</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
    )
    
    if is_admin:
        help_text += (
            "\n<b>Команды администратора:</b>\n"
            "/admin - Открыть панель администратора\n"
            "\n<b>В панели администратора вы можете:</b>\n"
            "• Публиковать меню в канал\n"
            "• Обновлять прайс-листы\n"
            "• Управлять настройками меню\n"
            "• Просматривать статистику\n"
        )
    
    await message.answer(help_text)


@router.callback_query(F.data.startswith("menu_item:"))
async def handle_menu_item_click(callback: CallbackQuery):
    """Handle clicks on menu items from users."""
    # This would be triggered if users click on menu items in the channel
    # For most cases, we'll use URL buttons that open directly
    # This handler is for items that don't have URLs
    
    item_id = int(callback.data.split(":")[1])
    
    db = Database()
    item = await db.get_menu_item(item_id)
    
    if not item:
        await callback.answer("Информация не найдена", show_alert=True)
        return
    
    # Different responses based on item type
    if item['type'] == 'info':
        # These would typically have content stored in the database
        # For now, we'll use placeholder responses
        responses = {
            "✅ Гарантия": (
                "🔹 На все новые устройства гарантия 1 год\n"
                "🔹 На б/у устройства гарантия 1 месяц\n"
                "🔹 Гарантия распространяется на заводские дефекты"
            ),
            "🏠 Адрес / Как нас найти?": (
                "🏢 Наш адрес: г. Орск, пр. Ленина, 21\n"
                "🕙 Режим работы: Пн-Пт с 10:00 до 19:00, Сб-Вс с 10:00 до 17:00\n"
                "📍 Ориентир: ТЦ «Яблочный Спас», 2 этаж"
            ),
            "💳 Рассрочка / Кредит от 1%": (
                "💳 Предлагаем рассрочку и кредит от 1%\n"
                "📝 Для оформления необходим только паспорт\n"
                "⏱ Решение принимается за 15 минут"
            ),
            "🚚 Доставка": (
                "🚚 Доставка по городу - бесплатно\n"
                "🌍 Доставка в другие города - по тарифам транспортных компаний\n"
                "⏱ Срок доставки: 1-2 дня"
            ),
            "💰 Оплата": (
                "💵 Наличными при получении\n"
                "💳 Банковской картой\n"
                "📱 Переводом на карту"
            ),
            "‼ Ответы на часто задаваемые вопросы": (
                "❓ <b>Можно ли проверить устройство перед покупкой?</b>\n"
                "✅ Да, мы предоставляем возможность полной проверки\n\n"
                "❓ <b>Есть ли у вас рассрочка без переплаты?</b>\n"
                "✅ Да, предлагаем рассрочку 0% на 3 месяца\n\n"
                "❓ <b>Работаете ли вы с регионами?</b>\n"
                "✅ Да, отправляем товары по всей России"
            )
        }
        
        response = responses.get(item['title'], "Информация будет добавлена позже")
        await callback.answer(response, show_alert=True)
    
    elif item['type'] == 'price' and item['is_dynamic']:
        # For dynamic price items without URLs yet
        await callback.answer("Прайс-лист еще не добавлен", show_alert=True)
    
    else:
        # Generic response for other items
        await callback.answer("Информация будет добавлена позже", show_alert=True)
