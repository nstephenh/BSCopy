import os

from book_reader.book import Book

if __name__ == '__main__':
    epub_path = ""
    for file in os.listdir("."):
        if file.endswith('epub'):
            epub_path = file
            break
    print(epub_path)
    Book(epub_path)
