from app.assignments.storage import (
    AssignmentStorageError,
    create_pdf_download_url,
    store_pdf,
)


class ScholarshipStorageError(Exception):
    pass


def store_scholarship_document(object_key, content):
    try:
        store_pdf(object_key, content)
    except AssignmentStorageError as exc:
        raise ScholarshipStorageError(
            "Could not store the scholarship supporting document."
        ) from exc


def create_scholarship_document_url(object_key, filename):
    try:
        return create_pdf_download_url(object_key, filename)
    except AssignmentStorageError as exc:
        raise ScholarshipStorageError(
            "Could not create a scholarship document download link."
        ) from exc
