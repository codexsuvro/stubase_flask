from app.assignments.storage import (
    AssignmentStorageError,
    create_pdf_download_url,
    delete_pdf,
    store_pdf,
)


class InvoiceStorageError(Exception):
    pass


def store_invoice_pdf(object_key, content):
    try:
        store_pdf(object_key, content)
    except AssignmentStorageError as exc:
        raise InvoiceStorageError(
            "Could not store the invoice PDF."
        ) from exc


def create_invoice_pdf_url(object_key, filename):
    try:
        return create_pdf_download_url(object_key, filename)
    except AssignmentStorageError as exc:
        raise InvoiceStorageError(
            "Could not create an invoice PDF download link."
        ) from exc


def delete_invoice_pdf(object_key):
    try:
        delete_pdf(object_key)
    except AssignmentStorageError as exc:
        raise InvoiceStorageError(
            "Could not remove the invoice PDF."
        ) from exc
