import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app


class AssignmentStorageError(Exception):
    pass


def _client_and_bucket():
    config = current_app.config
    endpoint_url = config.get("R2_ENDPOINT_URL")

    if not endpoint_url and config.get("R2_ACCOUNT_ID"):
        endpoint_url = (
            f"https://{config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
        )

    access_key_id = config.get("R2_ACCESS_KEY_ID")
    secret_access_key = config.get("R2_SECRET_ACCESS_KEY")
    bucket_name = config.get("R2_BUCKET_NAME")

    if not all((endpoint_url, access_key_id, secret_access_key, bucket_name)):
        raise AssignmentStorageError(
            "Cloudflare R2 storage is not fully configured."
        )

    try:
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )
    except BotoCoreError as exc:
        raise AssignmentStorageError(
            "Could not initialize Cloudflare R2 storage."
        ) from exc

    return client, bucket_name


def store_pdf(object_key, content):
    client, bucket_name = _client_and_bucket()

    try:
        client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=content,
            ContentType="application/pdf",
            ContentDisposition="attachment",
        )
    except (BotoCoreError, ClientError) as exc:
        raise AssignmentStorageError(
            "Could not store the assignment PDF."
        ) from exc


def create_pdf_download_url(object_key, filename):
    client, bucket_name = _client_and_bucket()

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
                "ResponseContentType": "application/pdf",
                "ResponseContentDisposition": (
                    f'attachment; filename="{filename}"'
                ),
            },
            ExpiresIn=current_app.config[
                "R2_SIGNED_URL_TTL_SECONDS"
            ],
        )
    except (BotoCoreError, ClientError) as exc:
        raise AssignmentStorageError(
            "Could not create an assignment PDF download link."
        ) from exc


def delete_pdf(object_key):
    client, bucket_name = _client_and_bucket()

    try:
        client.delete_object(
            Bucket=bucket_name,
            Key=object_key,
        )
    except (BotoCoreError, ClientError) as exc:
        raise AssignmentStorageError(
            "Could not remove the previous assignment PDF."
        ) from exc
