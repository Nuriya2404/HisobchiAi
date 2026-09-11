import base64
import mimetypes

from docx import Document as DocxDocument

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def prepare_content_blocks(file_path: str, filename: str) -> list[dict]:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        with open(file_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        return [
            {
                "type": "input_file",
                "filename": filename,
                "file_data": f"data:application/pdf;base64,{data}",
            }
        ]

    if ext in IMAGE_EXTENSIONS:
        with open(file_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        media_type = mimetypes.guess_type(filename)[0] or f"image/{ext}"
        return [
            {
                "type": "input_image",
                "image_url": f"data:{media_type};base64,{data}",
            }
        ]

    if ext == "docx":
        document = DocxDocument(file_path)
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        if not text.strip():
            raise ValueError("Hujjat matni topilmadi yoki bo'sh.")
        return [{"type": "input_text", "text": text}]

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return [{"type": "input_text", "text": text}]

    raise ValueError(
        f"Qo'llab-quvvatlanmaydigan fayl turi: .{ext or '?'}. "
        f"PDF, rasm (jpg/png), Word (.docx) yoki matn (.txt) fayl yuboring."
    )
