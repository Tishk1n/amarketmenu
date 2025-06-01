from database import Database

async def setup_database():
    """Initialize database and create default menu if needed."""
    db = Database()
    
    # Create tables if they don't exist
    await db.create_tables()
    
    # Initialize default menu items if none exist
    await db.initialize_default_menu()
    
    return db
