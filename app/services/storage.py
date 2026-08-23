"""Serviço de armazenamento de arquivos (S3-compatível — Magalu Objects).

Responsável por enviar/remover arquivos (imagens e PDFs) das cifras no bucket.
Quando o bucket não está configurado, mantém o comportamento legado de gravar
o data URI completo no banco.
"""

import base64
import io
import json
import uuid

import boto3

from app.core.config import BUCKET_NAME, BUCKET_REGION, settings

FOLDER = "chord_sheets"


def _s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.BUCKET_ACCESS_KEY_ID,
        aws_secret_access_key=settings.BUCKET_SECRET_ACCESS_KEY,
        endpoint_url=settings.bucket_endpoint or None,
        region_name=BUCKET_REGION or None,
    )


def _extension_for_content_type(content_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "application/pdf": ".pdf",
    }
    return mapping.get(content_type.lower().strip(), ".bin")


def upload_data_uri(data_uri: str) -> str:
    """Envia um data URI (imagem/PDF) para o bucket e retorna a chave (caminho) do objeto."""
    if "," not in data_uri:
        raise ValueError("data URI inválida")
    header, payload = data_uri.split(",", 1)
    content_type = header.split(";")[0].replace("data:", "").strip() or "application/octet-stream"
    raw = base64.b64decode(payload)
    object_key = f"{FOLDER}/{uuid.uuid4().hex}{_extension_for_content_type(content_type)}"

    _s3_client().upload_fileobj(
        io.BytesIO(raw),
        BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return object_key


def delete_file(object_key: str) -> None:
    """Remove um objeto do bucket pelo caminho (chave)."""
    if not settings.bucket_configured:
        return
    _s3_client().delete_object(Bucket=BUCKET_NAME, Key=object_key)


def process_image_data(image_data: list[str] | None) -> tuple[str | None, bool]:
    """Normaliza o `image_data` recebido no payload.

    Retorna uma tupla ``(json_string | None, is_bucket_storage)``:
    - Itens que são data URIs (data:image/... ou data:application/pdf) são
      enviados ao bucket e substituídos pelo caminho do objeto.
    - Itens que já são caminhos do bucket (chaves) são mantidos como estão
      (caso de edição de cifras já armazenadas no bucket).
    - Se o bucket não estiver configurado, mantém os data URIs (compatibilidade
      com o comportamento anterior).
    """
    if not image_data:
        return None, False

    items: list[str] = []
    uses_bucket = False

    for item in image_data:
        item = (item or "").strip()
        if not item:
            continue

        if item.startswith("data:"):
            if settings.bucket_configured:
                items.append(upload_data_uri(item))
                uses_bucket = True
            else:
                # Legado: grava o data URI completo no banco
                items.append(item)
        else:
            # Já é um caminho no bucket (chave) — mantém
            items.append(item)
            uses_bucket = True

    if not items:
        return None, False
    return json.dumps(items), uses_bucket


def parse_image_data_keys(image_data: str | list | None) -> list[str]:
    """Extrai as chaves do bucket a partir do valor de `image_data` salvo no banco."""
    if not image_data:
        return []
    if isinstance(image_data, str):
        try:
            parsed = json.loads(image_data)
        except json.JSONDecodeError:
            parsed = [image_data]
    else:
        parsed = image_data
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, str) and not item.startswith("data:")]
