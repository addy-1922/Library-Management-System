import os
import random
import json
from io import BytesIO
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from library.models import Book

COLOR_PALETTES = [
    ((79, 70, 229), (30, 27, 75)),
    ((22, 163, 74), (6, 78, 32)),
    ((217, 119, 6), (69, 26, 3)),
    ((37, 99, 235), (30, 58, 138)),
    ((124, 58, 237), (46, 16, 101)),
    ((220, 38, 38), (69, 10, 10)),
    ((14, 165, 233), (12, 74, 110)),
    ((168, 85, 247), (88, 28, 135)),
    ((236, 72, 153), (131, 24, 67)),
    ((16, 185, 129), (6, 78, 59)),
]

OPEN_LIBRARY_URL = 'https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg'
OPEN_LIBRARY_SEARCH = 'https://openlibrary.org/search.json?q={query}&limit=5&fields=key,title,cover_i,isbn'
OPEN_LIBRARY_COVER_ID = 'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg'


class Command(BaseCommand):
    help = 'Fetch real book cover images from Open Library, falling back to generated covers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Replace existing cover images',
        )
        parser.add_argument(
            '--local',
            action='store_true',
            help='Skip Open Library download, regenerate all covers locally',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        local_only = options['local']
        books = Book.objects.all()
        if not books.exists():
            self.stdout.write(self.style.WARNING('No books found. Run seed_library first.'))
            return

        updated = 0
        downloaded = 0
        generated = 0
        for book in books:
            if book.cover_image and not overwrite:
                continue

            image_data = None
            if not local_only:
                image_data = self._fetch_cover(book.isbn, book.title)

            if image_data:
                filename = f'{self._slug(book.title)}_{book.pk}.jpg'
                book.cover_image.save(filename, ContentFile(image_data), save=False)
                book.save(update_fields=['cover_image'])
                updated += 1
                downloaded += 1
                self.stdout.write(f'  downloaded: {book.title}')
            else:
                image = self._make_cover(book)
                buffer = BytesIO()
                image.save(buffer, format='JPEG', quality=88)
                filename = f'{self._slug(book.title)}_{book.pk}.jpg'
                book.cover_image.save(filename, ContentFile(buffer.getvalue()), save=False)
                buffer.close()
                book.save(update_fields=['cover_image'])
                updated += 1
                generated += 1
                self.stdout.write(f'  generated: {book.title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {updated} covers updated — {downloaded} downloaded, {generated} generated locally.'
        ))

    def _fetch_cover(self, isbn, title=''):
        if isbn:
            image_data = self._fetch_by_isbn(isbn)
            if image_data:
                return image_data
        if title:
            image_data = self._fetch_by_title(title)
            if image_data:
                return image_data
        return None

    def _fetch_by_isbn(self, isbn):
        url = OPEN_LIBRARY_URL.format(isbn=isbn)
        try:
            req = Request(url, headers={'User-Agent': 'LibManage/1.0'})
            with urlopen(req, timeout=10) as resp:
                data = resp.read()
                if len(data) < 1000:
                    return None
                return self._process_image(data)
        except (URLError, HTTPError, OSError, ValueError):
            return None

    def _fetch_by_title(self, title):
        query = title.replace('&', 'and')
        url = OPEN_LIBRARY_SEARCH.format(query=query.replace(' ', '+'))
        try:
            req = Request(url, headers={'User-Agent': 'LibManage/1.0'})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            for doc in data.get('docs', []):
                cover_id = doc.get('cover_i')
                if not cover_id:
                    continue
                cover_url = OPEN_LIBRARY_COVER_ID.format(cover_id=cover_id)
                creq = Request(cover_url, headers={'User-Agent': 'LibManage/1.0'})
                with urlopen(creq, timeout=10) as cresp:
                    cdata = cresp.read()
                    if len(cdata) > 1000:
                        return self._process_image(cdata)
        except (URLError, HTTPError, OSError, ValueError):
            pass
        return None

    def _process_image(self, data):
        img = Image.open(BytesIO(data))
        img = img.convert('RGB')
        img = img.resize((600, 850), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=88)
        return buf.getvalue()

    def _slug(self, text):
        result = ''.join(c.lower() if c.isalnum() else '-' for c in text)
        result = '-'.join(result.split('-'))
        return result.strip('-')[:50] or 'book'

    def _load_font(self, size):
        candidates = [
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
            'C:/Windows/Fonts/segoeuib.ttf',
            'C:/Windows/Fonts/georgia.ttf',
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _make_cover(self, book):
        width, height = 600, 850
        palette = COLOR_PALETTES[book.pk % len(COLOR_PALETTES)]
        top_color, bottom_color = palette
        img = Image.new('RGB', (width, height), top_color)
        draw = ImageDraw.Draw(img)

        for y in range(height):
            ratio = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        margin = 24
        draw.rectangle(
            [margin, margin, width - margin, height - margin],
            outline=(255, 255, 255), width=3
        )
        inner = 12
        draw.rectangle(
            [margin + inner, margin + inner, width - margin - inner, height - margin - inner],
            outline=(255, 255, 255), width=1
        )

        self._draw_book_icon(draw, width // 2, 150)

        title_lines = self._wrap_text(book.title, width - 120, self._load_font(44))
        title_font = self._load_font(44)
        y = 320
        draw.text(
            (width // 2, 250), 'LIBRARY',
            fill=(255, 255, 255), font=self._load_font(28), anchor='mm'
        )
        for i, line in enumerate(title_lines):
            draw.text(
                (width // 2, y), line,
                fill=(255, 255, 255), font=title_font, anchor='ma'
            )
            y += 56

        author_text = book.author.name if book.author else ''
        draw.text(
            (width // 2, height - 150), author_text,
            fill=(230, 230, 250), font=self._load_font(30), anchor='mm'
        )
        return img

    def _draw_book_icon(self, draw, cx, cy):
        w, h = 90, 60
        left = cx - w
        right = cx + w
        top = cy - h
        bottom = cy + h
        draw.polygon(
            [(left, top), (cx, top + 18), (right, top),
             (right, bottom - 18), (cx, bottom), (left, bottom - 18)],
            fill=(255, 255, 255)
        )

    def _wrap_text(self, text, max_width, font):
        words = text.split()
        lines = []
        current = ''
        for word in words:
            test = f'{current} {word}'.strip()
            if font.getbbox(test)[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines[:4]
