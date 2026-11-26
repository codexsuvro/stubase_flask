from app.assignments.storage import (
    AssignmentStorageError,
    create_pdf_download_url,
    delete_pdf,
    store_pdf,
)


class FinanceStorageError(Exception):
    pass


def store_invoice_pdf(object_key, content):
    try:
        store_pdf(object_key, content)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not store the invoice PDF."
        ) from exc


def create_invoice_pdf_url(object_key, filename):
    try:
        return create_pdf_download_url(object_key, filename)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not create an invoice PDF download link."
        ) from exc


def delete_invoice_pdf(object_key):
    try:
        delete_pdf(object_key)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not remove the invoice PDF."
        ) from exc


def store_receipt_pdf(object_key, content):
    try:
        store_pdf(object_key, content)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not store the payment receipt PDF."
        ) from exc


def create_receipt_pdf_url(object_key, filename):
    try:
        return create_pdf_download_url(object_key, filename)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not create a payment receipt download link."
        ) from exc


def delete_receipt_pdf(object_key):
    try:
        delete_pdf(object_key)
    except AssignmentStorageError as exc:
        raise FinanceStorageError(
            "Could not remove the payment receipt PDF."
        ) from exc
