import os

from book_reader.book import Book

if __name__ == '__main__':
    epub_path = ""
    for file in os.listdir("."):
        if file.endswith('epub'):
            epub_path = file
            break
    print(epub_path)
    book = Book(epub_path, settings={
        'first_paragraph_is_flavor': True
    })
    for page in book.pages:
        pass
