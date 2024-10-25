from django.shortcuts import render

from gamedata.models import Publication, PublishedDocument
from gamedata.serializers import PublicationSerializer, PublishedDocumentSerializer, PageSerializer


# Create your views here.


def book_index(request):
    document_list = []
    for book in Publication.objects.all():
        revisions = []
        for revision in book.documents.all():
            revisions.append(PublishedDocumentSerializer(revision).data)
        book = PublicationSerializer(book).data
        book['revisions'] = revisions
        document_list.append(book)
    context = {
        "document_list": document_list
    }
    return render(request, "documents/index.html", context)


def page_index(request, document_id):
    book = PublishedDocument.objects.get(pk=document_id)
    pages = []
    for page in book.pages.all().order_by("file_page_number"):
        page_data = PageSerializer(page).data
        errata = []
        for e in page.find_errata():
            print(e)
            errata.append(e)
        page_data.update({"errata": errata})
        pages.append(page_data)
    context = {
        "book": PublishedDocumentSerializer(book).data,
        "pages": pages,
    }
    return render(request, "documents/document_details.html", context)
