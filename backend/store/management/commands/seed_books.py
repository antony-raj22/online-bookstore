from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Book


BOOKS = [
    {
        "title": "The Midnight Library",
        "author": "Matt Haig",
        "genre": "fiction",
        "price": "399.00",
        "stock": 18,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780525559474-L.jpg",
        "description": "A moving novel about choices, regret, and the many lives a reader can imagine.",
    },
    {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "genre": "nonfiction",
        "price": "599.00",
        "stock": 15,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780062316097-L.jpg",
        "description": "A wide-ranging history of humankind, from early humans to modern society.",
    },
    {
        "title": "The Silent Patient",
        "author": "Alex Michaelides",
        "genre": "thriller",
        "price": "349.00",
        "stock": 20,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781250301697-L.jpg",
        "description": "A psychological thriller about silence, obsession, and a shocking final reveal.",
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "genre": "scifi",
        "price": "499.00",
        "stock": 16,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780441172719-L.jpg",
        "description": "A landmark science fiction epic of politics, ecology, prophecy, and power.",
    },
    {
        "title": "Book Lovers",
        "author": "Emily Henry",
        "genre": "romance",
        "price": "329.00",
        "stock": 14,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780593334836-L.jpg",
        "description": "A smart romantic comedy about rival publishing professionals and second chances.",
    },
    {
        "title": "Becoming",
        "author": "Michelle Obama",
        "genre": "biography",
        "price": "650.00",
        "stock": 12,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781524763138-L.jpg",
        "description": "A personal memoir about identity, public life, family, and purpose.",
    },
    {
        "title": "Charlotte's Web",
        "author": "E. B. White",
        "genre": "children",
        "price": "249.00",
        "stock": 25,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780061124952-L.jpg",
        "description": "A beloved children's classic about friendship, kindness, and courage.",
    },
    {
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen",
        "genre": "academic",
        "price": "1200.00",
        "stock": 8,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780262046305-L.jpg",
        "description": "A comprehensive academic reference for algorithms and data structures.",
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "genre": "selfhelp",
        "price": "450.00",
        "stock": 22,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780735211292-L.jpg",
        "description": "A practical guide to building better habits through small, repeatable changes.",
    },
    {
        "title": "Ways of Seeing",
        "author": "John Berger",
        "genre": "art",
        "price": "299.00",
        "stock": 11,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780141035796-L.jpg",
        "description": "A concise classic on visual culture, art, images, and how we interpret them.",
    },
    {
        "title": "Salt, Fat, Acid, Heat",
        "author": "Samin Nosrat",
        "genre": "cooking",
        "price": "799.00",
        "stock": 9,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781476753836-L.jpg",
        "description": "An approachable cooking guide built around four essential elements of flavor.",
    },
    {
        "title": "The Alchemist",
        "author": "Paulo Coelho",
        "genre": "travel",
        "price": "299.00",
        "stock": 19,
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780061122415-L.jpg",
        "description": "A journey story about dreams, destiny, travel, and listening to one's heart.",
    },
]


class Command(BaseCommand):
    help = "Seed useful books across every storefront category."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for item in BOOKS:
            _, created = Book.objects.update_or_create(
                title=item["title"],
                author=item["author"],
                defaults={
                    "genre": item["genre"],
                    "price": Decimal(item["price"]),
                    "stock": item["stock"],
                    "cover_url": item["cover_url"],
                    "description": item["description"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded books complete: {created_count} created, {updated_count} updated."
            )
        )
