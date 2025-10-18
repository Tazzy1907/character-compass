"""
Utility script to query and view character profiles from the database.
"""

import database
import json


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def view_all_books():
    """Display all books in the database."""
    print("📚 ALL BOOKS:")
    print_separator()
    
    books = database.get_all_books()
    
    if not books:
        print("No books found in database.")
        return
    
    for book in books:
        print(f"Title: {book['name']}")
        print(f"URL: {book['url']}")
        print(f"Icon: {book['icon']}")
        print("-" * 40)


def view_all_characters():
    """Display all characters across all books."""
    print("👥 ALL CHARACTERS:")
    print_separator()
    
    characters = database.get_all_characters()
    
    if not characters:
        print("No characters found in database.")
        return
    
    for char in characters:
        print(f"Name: {char['name']} ({char['character_type'].upper()})")
        print(f"Book: {char['book_url']}")
        if char['age']:
            print(f"Age: {char['age']}")
        if char['gender']:
            print(f"Gender: {char['gender']}")
        if char['occupation']:
            print(f"Occupation: {char['occupation']}")
        if char['personality']:
            print(f"Personality: {char['personality'][:100]}...")
        print(f"Created: {char['created_at']}")
        print(f"Updated: {char['updated_at']}")
        print("-" * 40)


def view_characters_by_book(book_url: str):
    """Display all characters for a specific book."""
    print(f"👥 CHARACTERS FOR BOOK: {book_url}")
    print_separator()
    
    characters = database.get_characters_by_book(book_url)
    
    if not characters:
        print(f"No characters found for book: {book_url}")
        return
    
    # Separate main and side characters
    main_chars = [c for c in characters if c['character_type'] == 'main']
    side_chars = [c for c in characters if c['character_type'] == 'side']
    
    if main_chars:
        print("🌟 MAIN CHARACTERS:")
        for char in main_chars:
            print(f"\n  • {char['name']}")
            if char['age']:
                print(f"    Age: {char['age']}")
            if char['occupation']:
                print(f"    Occupation: {char['occupation']}")
            if char['personality']:
                print(f"    Personality: {char['personality'][:150]}...")
    
    if side_chars:
        print("\n\n⭐ SIDE CHARACTERS:")
        for char in side_chars:
            print(f"\n  • {char['name']}")
            if char['occupation']:
                print(f"    Occupation: {char['occupation']}")


def view_character_detail(name: str, book_url: str):
    """Display detailed information for a specific character."""
    print(f"🔍 CHARACTER DETAIL: {name}")
    print_separator()
    
    char = database.get_character(name, book_url)
    
    if not char:
        print(f"Character '{name}' not found in book '{book_url}'")
        return
    
    print(f"Name: {char['name']}")
    print(f"Type: {char['character_type'].upper()}")
    print(f"Book: {char['book_url']}")
    print()
    
    if char['age']:
        print(f"Age: {char['age']}")
    if char['gender']:
        print(f"Gender: {char['gender']}")
    if char['sex']:
        print(f"Sex: {char['sex']}")
    if char['race']:
        print(f"Race: {char['race']}")
    if char['occupation']:
        print(f"Occupation: {char['occupation']}")
    
    print()
    
    if char['personality']:
        print(f"Personality:\n{char['personality']}")
        print()
    
    if char['appearance']:
        print(f"Appearance:\n{char['appearance']}")
        print()
    
    if char['backstory']:
        print(f"Backstory:\n{char['backstory']}")
        print()
    
    if char['relationships']:
        print("Relationships:")
        for rel in char['relationships']:
            print(f"  • {rel}")
        print()
    
    if char['goals']:
        print("Goals:")
        for goal in char['goals']:
            print(f"  • {goal}")
        print()
    
    if char['motivations']:
        print("Motivations:")
        for mot in char['motivations']:
            print(f"  • {mot}")
        print()
    
    print(f"Created: {char['created_at']}")
    print(f"Updated: {char['updated_at']}")


def get_statistics():
    """Display database statistics."""
    print("📊 DATABASE STATISTICS:")
    print_separator()
    
    books = database.get_all_books()
    all_characters = database.get_all_characters()
    
    print(f"Total Books: {len(books)}")
    print(f"Total Characters: {len(all_characters)}")
    
    print("\nCharacters by Book:")
    for book in books:
        count = database.get_character_count_by_book(book['url'])
        main_count = len(database.get_main_characters(book['url']))
        side_count = len(database.get_side_characters(book['url']))
        print(f"  • {book['name']}: {count} total ({main_count} main, {side_count} side)")


if __name__ == "__main__":
    print("🗄️  Character Compass Database Query Tool")
    print_separator()
    
    # Display menu
    print("Options:")
    print("  1. View all books")
    print("  2. View all characters")
    print("  3. View characters by book")
    print("  4. View character detail")
    print("  5. View statistics")
    print()
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        view_all_books()
    elif choice == "2":
        view_all_characters()
    elif choice == "3":
        book_url = input("Enter book URL/ID: ").strip()
        view_characters_by_book(book_url)
    elif choice == "4":
        name = input("Enter character name: ").strip()
        book_url = input("Enter book URL/ID: ").strip()
        view_character_detail(name, book_url)
    elif choice == "5":
        get_statistics()
    else:
        print("Invalid choice!")
    
    print_separator()

