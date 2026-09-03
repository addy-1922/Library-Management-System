from django import forms
from .models import Book, Author, Category, Publisher, BorrowRecord
from accounts.models import MemberProfile


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'author', 'category', 'publisher',
            'publication_date', 'description', 'cover_image',
            'total_copies', 'available_copies', 'shelf_location',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9780134685991'}),
            'author': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-control'}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'shelf_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A-3-12'}),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn'].replace('-', '').replace(' ', '')
        if len(isbn) not in (10, 13):
            raise forms.ValidationError('ISBN must be 10 or 13 digits.')
        if not isbn.isdigit():
            raise forms.ValidationError('ISBN must contain only digits.')
        return isbn

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies', 0)
        available = cleaned_data.get('available_copies', 0)
        if available is not None and total is not None and available > total:
            raise forms.ValidationError('Available copies cannot exceed total copies.')
        return cleaned_data


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography', 'date_of_birth', 'nationality']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class IssueBookForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=MemberProfile.objects.filter(is_active_member=True).select_related('user'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'member-select'}),
        empty_label='-- Select Member --',
        required=False,
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0).select_related('author'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'book-select'}),
        empty_label='-- Select Book --',
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        self.for_member = kwargs.pop('for_member', None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        self.fields['issue_date'].initial = timezone.now().date()
        if self.for_member is not None:
            del self.fields['member']


class BookSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, ISBN, author...',
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        required=False,
        empty_label='All Authors',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    availability = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('available', 'Available'),
            ('limited', 'Limited'),
            ('unavailable', 'Unavailable'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
