from datetime import date

from django.core.management.base import BaseCommand

from library.models import Author, Category, Publisher, Book


class Command(BaseCommand):
    help = 'Add engineering and mathematics books to an existing database (idempotent).'

    def handle(self, *args, **options):
        cat_map = {c.name.lower(): c for c in Category.objects.all()}
        books_added = 0
        skipped = 0

        # (title, isbn, author, category_key, publisher, pub_date, desc, copies, shelf)
        book_data = [
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
            if Book.objects.filter(isbn=isbn).exists():
                skipped += 1
                continue

            author, _ = Author.objects.get_or_create(name=author_name, defaults={
                'biography': f'Author of {title}.',
                'nationality': '',
            })
            publisher, _ = Publisher.objects.get_or_create(name=pub_name, defaults={
                'email': f'info@{pub_name.lower().replace(" ", "")}.com',
            })
            category = cat_map.get(cat_key)
            if category is None:
                category, _ = Category.objects.get_or_create(name=cat_key.title())

            Book.objects.create(
                title=title, isbn=isbn, author=author, category=category,
                publisher=publisher, publication_date=pub_date, description=desc,
                total_copies=copies, available_copies=copies, shelf_location=shelf,
            )
            books_added += 1
            self.stdout.write(f'  added: {title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Added {books_added} books, skipped {skipped} existing (by ISBN).'
        ))
