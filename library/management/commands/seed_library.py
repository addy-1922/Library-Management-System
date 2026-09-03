from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, date

from library.models import Author, Category, Publisher, Book, BorrowRecord
from accounts.models import MemberProfile


class Command(BaseCommand):
    help = 'Populate the database with realistic demo data for the library system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['force']:
            self.stdout.write(self.style.WARNING('Clearing existing library data...'))
            BorrowRecord.objects.all().delete()
            Book.objects.all().delete()
            Author.objects.all().delete()
            Category.objects.all().delete()
            Publisher.objects.all().delete()

        if Book.objects.exists() or Author.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Library data already exists. Use --force to reseed.'
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING('Creating categories...'))
        categories = {}
        cat_data = {
            'Fiction': 'Fiction and literary works',
            'Computer Science': 'Programming, computer science and technology',
            'Mathematics': 'Mathematics and statistics',
            'Science': 'Physics, chemistry, biology and general science',
            'History': 'Historical works and biographies',
            'Business': 'Business, economics and management',
            'Engineering': 'Engineering and applied sciences',
        }
        for name, desc in cat_data.items():
            categories[name.lower()] = Category.objects.create(name=name, description=desc)

        self.stdout.write(self.style.MIGRATE_HEADING('Creating publishers...'))
        publishers = {}
        pub_data = [
            ('Pearson', 'contact@pearson.com', '+91-1140000001', 'Chennai, India'),
            ('O\'Reilly Media', 'info@oreilly.com', '+1-800-998-9938', 'Sebastopol, California'),
            ('McGraw Hill', 'support@mheducation.com', '+91-1140000002', 'New Delhi, India'),
            ('Penguin Random House', 'info@penguin.com', '+91-1140000003', 'London, UK'),
            ('Oxford University Press', 'ouk@oup.com', '+44-1865-556767', 'Oxford, UK'),
            ('Apress', 'contact@apress.com', '+1-800-935-0043', 'New York, USA'),
            ('Wiley', 'info@wiley.com', '+91-1140000004', 'Hoboken, USA'),
            ('Tata McGraw-Hill', 'info@tatamcgrawhill.com', '+91-1140000005', 'Mumbai, India'),
            ('Cambridge University Press', 'info@cambridge.org', '+44-1223-358331', 'Cambridge, UK'),
            ('CRC Press', 'info@crcpress.com', '+1-800-272-7737', 'Boca Raton, USA'),
            ('PHI Learning', 'info@phindia.com', '+91-1140000006', 'New Delhi, India'),
            ('Springer', 'info@springer.com', '+49-6221-3450', 'Berlin, Germany'),
            ('Cengage', 'info@cengage.com', '+91-1140000007', 'Mumbai, India'),
        ]
        for name, email, phone, addr in pub_data:
            publishers[name] = Publisher.objects.create(name=name, email=email, phone=phone, address=addr)

        self.stdout.write(self.style.MIGRATE_HEADING('Creating authors...'))
        authors = {}
        author_data = [
            ('Robert C. Martin', 'American software engineer, author of several best-selling books on software craftsmanship.', date(1952, 12, 5), 'American'),
            ('Andrew Hunt', 'Co-author of The Pragmatic Programmer, a pioneer in the agile movement.', date(1964, 6, 29), 'British'),
            ('David Thomas', 'Programmer and author, co-founder of the Pragmatic Bookshelf.', date(1956, 10, 16), 'British'),
            ('Yuval Noah Harari', 'Israeli historian and author of Sapiens.', date(1976, 2, 24), 'Israeli'),
            ('J.K. Rowling', 'British author best known for the Harry Potter series.', date(1965, 7, 31), 'British'),
            ('Harper Lee', 'American novelist best known for To Kill a Mockingbird.', date(1926, 4, 28), 'American'),
            ('George Orwell', 'English novelist, essayist, journalist and critic.', date(1903, 6, 25), 'British'),
            ('Charles Dickens', 'English writer and social critic.', date(1812, 2, 7), 'British'),
            ('Stephen Hawking', 'English theoretical physicist, cosmologist, and author.', date(1942, 1, 8), 'British'),
            ('Mikhail Bakhtin', 'Russian philosopher, literary critic and scholar.', date(1895, 11, 17), 'Russian'),
            ('Bjarne Stroustrup', 'Danish computer scientist, creator of C++.', date(1950, 12, 30), 'Danish'),
            ('Eric Freeman', 'Computer scientist and author of Head First design patterns.', date(1965, 7, 13), 'American'),
            ('Andy Oram', 'Writer, editor and programmer based in Massachusetts.', date(1954, 11, 11), 'American'),
            ('Peter Norvig', 'American computer scientist and Director of Research at Google.', date(1956, 12, 14), 'American'),
            ('Stuart Russell', 'British computer scientist, co-author of the standard AI textbook.', date(1962, 10, 28), 'British'),
            ('Elon Musk', 'Entrepreneur and business magnate (book about him).', date(1971, 6, 28), 'South African'),
            ('R. C. Hibbeler', 'American civil engineer and author of widely used engineering textbooks.', date(1940, 6, 1), 'American'),
            ('J. P. Holman', 'Professor of mechanical engineering, author of Heat Transfer.', date(1936, 3, 1), 'American'),
            ('Theodore Wildi', 'Professor of electrical engineering, author of Electrical Machines.', date(1923, 1, 1), 'Canadian'),
            ('Angela Yu', 'Developer and author of popular programming and engineering courses.', date(1988, 5, 4), 'British'),
            ('Erwin Kreyszig', 'German-Canadian mathematician, author of Advanced Engineering Mathematics.', date(1922, 5, 9), 'German'),
            ('Gilbert Strang', 'American mathematician and professor at MIT, author of Linear Algebra texts.', date(1934, 11, 27), 'American'),
            ('Seymour Lipschutz', 'American mathematician and author of Schaum\'s outline series.', date(1930, 8, 21), 'American'),
            ('G. S. N. Raju', 'Professor of electronics and communication engineering.', date(1960, 1, 1), 'Indian'),
            ('S. K. Kataria', 'Publisher and compiler of engineering reference books.', date(1965, 1, 1), 'Indian'),
            ('James Stewart', 'Canadian mathematician, author of the widely used Calculus textbook.', date(1941, 3, 29), 'Canadian'),
        ]
        for name, bio, dob, nat in author_data:
            authors[name] = Author.objects.create(name=name, biography=bio, date_of_birth=dob, nationality=nat)

        self.stdout.write(self.style.MIGRATE_HEADING('Creating books...'))
        book_data = [
            ('Clean Code', '9780132350884', 'Robert C. Martin', 'computer science', 'Pearson', date(2008, 8, 1), 'A handbook of agile software craftsmanship. This book presents a revolutionary view of software craftsmanship.', 5, 'A-1-01'),
            ('The Pragmatic Programmer', '9780201616224', 'Andrew Hunt', 'computer science', 'Pearson', date(1999, 10, 30), 'Your journey to mastery starts here. Learn the fundamentals of software development from two masters.', 4, 'A-1-02'),
            ('Clean Architecture', '9780134494166', 'Robert C. Martin', 'computer science', 'Pearson', date(2017, 9, 10), 'A craftsman\'s guide to software structure and design. Explore the principles of software architecture.', 3, 'A-1-03'),
            ('Sapiens: A Brief History of Humankind', '9780062316097', 'Yuval Noah Harari', 'history', 'Penguin Random House', date(2015, 2, 10), 'A sweeping narrative of humanity\'s creation and evolution that explores how biology and history have defined us.', 6, 'B-2-01'),
            ('Harry Potter and the Sorcerer\'s Stone', '9780590353427', 'J.K. Rowling', 'fiction', 'Penguin Random House', date(1998, 10, 1), 'The first book in the Harry Potter series following a young wizard\'s journey.', 7, 'C-1-01'),
            ('To Kill a Mockingbird', '9780061120084', 'Harper Lee', 'fiction', 'Penguin Random House', date(2006, 10, 11), 'A gripping, heart-wrenching, and wholly remarkable tale of coming-of-age in a South poisoned by virulent prejudice.', 5, 'C-1-02'),
            ('1984', '9780451524935', 'George Orwell', 'fiction', 'Penguin Random House', date(1950, 6, 1), 'The classic dystopian novel about a totalitarian regime and the price of individuality.', 4, 'C-1-03'),
            ('A Tale of Two Cities', '9780141439600', 'Charles Dickens', 'fiction', 'Penguin Random House', date(2003, 1, 30), 'The French Revolution comes to life in Dickens\'s masterpiece.', 3, 'C-1-04'),
            ('A Brief History of Time', '9780553380163', 'Stephen Hawking', 'science', 'Penguin Random House', date(1998, 9, 1), 'From the big bang to black holes, Hawking explores the mysteries of the universe.', 4, 'D-3-01'),
            ('The C++ Programming Language', '9780321958327', 'Bjarne Stroustrup', 'computer science', 'McGraw Hill', date(2013, 7, 2), 'The definitive reference for the C++ programming language from its creator.', 2, 'A-1-04'),
            ('Head First Design Patterns', '9780596007126', 'Eric Freeman', 'computer science', 'O\'Reilly Media', date(2004, 10, 25), 'With this book you will learn design patterns in a fun and engaging way.', 5, 'A-1-05'),
            ('Programming with UNIX', '9781565928996', 'Andy Oram', 'computer science', 'O\'Reilly Media', date(2001, 12, 1), 'Learn the fundamentals of programming in the Unix environment.', 3, 'A-1-06'),
            ('Artificial Intelligence: A Modern Approach', '9780134610993', 'Peter Norvig', 'computer science', 'Pearson', date(2015, 3, 11), 'The leading textbook on artificial intelligence, covering everything from search to machine learning.', 8, 'A-1-07'),
            ('Elon Musk: Tesla, SpaceX, and the Quest for a Fantastic Future', '9780062301239', 'Elon Musk', 'business', 'McGraw Hill', date(2015, 5, 19), 'The story of the entrepreneur who changed the world.', 3, 'E-1-01'),
            ('Engineering Mechanics: Statics', '9780133918922', 'R. C. Hibbeler', 'engineering', 'Pearson', date(2015, 1, 8), 'A comprehensive introduction to statics covering force systems, equilibrium, trusses and friction.', 5, 'F-1-01'),
            ('Heat Transfer', '9780073529264', 'J. P. Holman', 'engineering', 'McGraw Hill', date(2009, 1, 1), 'The classic textbook on conduction, convection and radiation heat transfer.', 4, 'F-1-02'),
            ('Electrical Machines, Drives and Power Systems', '9780130930835', 'Theodore Wildi', 'engineering', 'Pearson', date(2005, 7, 15), 'A practical introduction to electrical machines, motors, generators and power systems.', 4, 'F-1-03'),
            ('Digital Circuits and Logic Design', '9789332518133', 'G. S. N. Raju', 'engineering', 'PHI Learning', date(2014, 4, 1), 'Covers digital electronics, logic gates, combinational and sequential circuits.', 5, 'F-1-04'),
            ('Basic Electrical Engineering', '9788121921929', 'S. K. Kataria', 'engineering', 'Tata McGraw-Hill', date(2012, 1, 1), 'Foundational textbook on electrical engineering for undergraduate students.', 4, 'F-1-05'),
            ('Advanced Engineering Mathematics', '9780470458365', 'Erwin Kreyszig', 'mathematics', 'Wiley', date(2011, 1, 1), 'The standard reference for engineering mathematics covering ODEs, linear algebra, Fourier analysis and complex analysis.', 6, 'G-1-01'),
            ('Linear Algebra and Its Applications', '9780030105678', 'Gilbert Strang', 'mathematics', 'Cambridge University Press', date(2005, 7, 19), 'An introduction to linear algebra with emphasis on applications and computational methods.', 5, 'G-1-02'),
            ('Schaum\'s Outline of Discrete Mathematics', '9780071615860', 'Seymour Lipschutz', 'mathematics', 'McGraw Hill', date(2007, 6, 1), 'A solved-problems approach to sets, logic, combinatorics, graph theory and Boolean algebra.', 4, 'G-1-03'),
            ('Differential Equations with Boundary-Value Problems', '9781305965799', 'Erwin Kreyszig', 'mathematics', 'Cengage', date(2017, 1, 1), 'A comprehensive treatment of ordinary and partial differential equations.', 4, 'G-1-04'),
            ('Calculus: Early Transcendentals', '9781285741550', 'James Stewart', 'mathematics', 'Cengage', date(2015, 1, 1), 'The classic calculus textbook covering limits, derivatives, integrals and series.', 5, 'G-1-05'),
        ]

        for title, isbn, author_name, cat_key, pub_name, pub_date, desc, copies, shelf in book_data:
            Book.objects.create(
                title=title,
                isbn=isbn,
                author=authors[author_name],
                category=categories[cat_key],
                publisher=publishers[pub_name],
                publication_date=pub_date,
                description=desc,
                total_copies=copies,
                available_copies=copies,
                shelf_location=shelf,
            )

        self.stdout.write(self.style.MIGRATE_HEADING('Creating demo users...'))
        admin_user = User.objects.create_user(
            username='admin', email='admin@library.com',
            password='admin123', first_name='System', last_name='Administrator',
            is_staff=True, is_superuser=True
        )
        admin_profile = admin_user.member_profile
        admin_profile.phone = '+91-9800000000'
        admin_profile.department = 'Administration'
        admin_profile.address = 'Library HQ'
        admin_profile.save()

        librarian = User.objects.create_user(
            username='librarian', email='librarian@library.com',
            password='librarian123', first_name='Librarian', last_name='Official',
            is_staff=True
        )
        lib_profile = librarian.member_profile
        lib_profile.phone = '+91-9800000001'
        lib_profile.department = 'Library Management'
        lib_profile.save()

        member_names = [
            ('Aarav', 'Sharma', 'aarav', 'Computer Science'),
            ('Priya', 'Patel', 'priya', 'Mechanical Engineering'),
            ('Rohan', 'Gupta', 'rohan', 'Electrical Engineering'),
            ('Sneha', 'Reddy', 'sneha', 'Civil Engineering'),
            ('Vikram', 'Singh', 'vikram', 'Mathematics'),
            ('Ananya', 'Iyer', 'ananya', 'Physics'),
            ('Karthik', 'Nair', 'karthik', 'Business'),
            ('Meera', 'Joshi', 'meera', 'Chemistry'),
            ('Aditya', 'Kulkarni', 'aditya', 'Computer Science'),
            ('Ishita', 'Bose', 'ishita', 'History'),
        ]
        members = []
        for i, (first, last, username, dept) in enumerate(member_names, start=1):
            user = User.objects.create_user(
                username=username, email=f'{username}@library.com',
                password='member123', first_name=first, last_name=last
            )
            profile = user.member_profile
            profile.phone = f'+91-98{10000000 + i}00000'
            profile.department = dept
            profile.address = f'{i} Campus Hostel, University Road'
            profile.save()
            members.append(user)

        self.stdout.write(self.style.MIGRATE_HEADING('Creating borrowing records...'))
        books = list(Book.objects.all())
        today = timezone.now().date()

        issued_records = [
            (members[0], books[0], 10, 3),
            (members[1], books[2], 5, 8),
            (members[2], books[3], 12, 2),
            (members[3], books[8], 2, 12),
            (members[4], books[1], 6, 6),
            (members[0], books[5], 3, 4),
        ]
        for member, book, days_ago, period in issued_records:
            issued = today - timedelta(days=days_ago)
            due = issued + timedelta(days=period)
            BorrowRecord.objects.create(
                member=member, book=book,
                issue_date=issued, due_date=due,
                status='issued', issued_by=librarian,
            )
            book.available_copies = max(0, book.available_copies - 1)
            book.borrow_count += 1
            book.save(update_fields=['available_copies', 'borrow_count'])

        returned_records = [
            (members[5], books[4], 20, 14, 6),
            (members[6], books[6], 30, 14, 16),
            (members[7], books[9], 25, 14, 11),
            (members[8], books[0], 15, 14, 1),
            (members[9], books[10], 8, 7, 1),
        ]
        from library.services import calculate_fine
        for member, book, days_ago, period, days_late in returned_records:
            issued = today - timedelta(days=days_ago)
            due = issued + timedelta(days=period)
            returned = due + timedelta(days=days_late)
            fine = calculate_fine(due, returned)
            BorrowRecord.objects.create(
                member=member, book=book,
                issue_date=issued, due_date=due, return_date=returned,
                status='returned', fine_amount=fine,
                issued_by=librarian, returned_to=librarian,
            )
            if days_late > 0:
                book.borrow_count += 1
                book.save(update_fields=['borrow_count'])

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Seeded:\n'
            f'  - {Category.objects.count()} categories\n'
            f'  - {Author.objects.count()} authors\n'
            f'  - {Publisher.objects.count()} publishers\n'
            f'  - {Book.objects.count()} books\n'
            f'  - {User.objects.count()} users\n'
            f'  - {BorrowRecord.objects.count()} borrowing records\n\n'
            f'Login users:\n'
            f'  Admin:     admin / admin123\n'
            f'  Librarian: librarian / librarian123\n'
            f'  Member:    aarav / member123\n'
        ))
