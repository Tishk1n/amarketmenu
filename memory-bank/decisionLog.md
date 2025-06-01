# Decision Log

## Technical Decisions

[2025-06-01 11:41] - **Framework Selection: Aiogram**
- Decision: Use Aiogram for Telegram bot development
- Rationale: Modern, asynchronous framework with good support for Telegram Bot API
- Implications: Requires Python 3.7+ and asyncio knowledge

[2025-06-01 11:41] - **Database Selection: SQLite**
- Decision: Use SQLite for data storage
- Rationale: Lightweight, serverless database that's easy to set up and maintain
- Implications: Good for single-user access patterns, may need to consider alternatives if scaling becomes necessary

[2025-06-01 11:41] - **UI Approach: Inline Keyboards Only**
- Decision: Use only inline keyboards (no Reply keyboards)
- Rationale: More modern approach, better user experience, and specifically requested
- Implications: Need to design clear navigation paths within inline keyboard limitations

[2025-06-01 12:21] - **Статические пункты меню: Переход от всплывающих окон к прямым ссылкам**
- Decision: Изменить поведение статических пунктов меню, чтобы они перенаправляли на посты в канале вместо показа всплывающих окон
- Rationale: Улучшение пользовательского опыта, более удобный доступ к информации, возможность использовать форматирование Telegram в постах
- Implications: Необходимость создания и поддержания отдельных постов в канале для каждого статического пункта меню
- Implementation: Добавлена возможность администратору устанавливать URL для каждого статического пункта меню
