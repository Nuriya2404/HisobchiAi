import json
import logging
from datetime import date
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

CATEGORY_GUIDE = """Chiqim kategoriyalari: Oziq-ovqat, Transport, Kommunal to'lovlar, Kiyim-kechak, Sog'liqni saqlash, Ta'lim, \
Ko'ngilochar/Dam olish, Aloqa va internet, Uy-joy, Boshqa xarajat.
Daromad kategoriyalari: Ish haqi, Biznes daromadi, Frilanser/qo'shimcha ish, Sovg'a, Boshqa daromad."""

FINANCE_SYSTEM_PROMPT = f"""Siz "Hisobchi AI" - shaxsiy moliyaviy yordamchisiz. Foydalanuvchi yuborgan xabarni \
tahlil qiling va agar unda daromad yoki xarajat haqida ma'lumot bo'lsa, faqat quyidagi JSON formatida javob \
qaytaring. Javobingizda JSON'dan tashqari hech qanday matn, izoh yoki markdown belgilari (masalan ```) bo'lmasin.

JSON formati:
{{
  "is_financial": true yoki false,
  "type": "Kirim" yoki "Chiqim",
  "category": "kategoriya nomi",
  "product": "mahsulot yoki xizmat nomi (agar xabarda aytilgan bo'lsa, aks holda bo'sh qoldiring)",
  "quantity": raqam (miqdor, agar aytilgan bo'lsa, aks holda bo'sh qoldiring),
  "unit_price": raqam (bitta dona/birlik narxi, agar aytilgan bo'lsa, aks holda bo'sh qoldiring),
  "amount": raqam (jami summa, valyuta belgisisiz; agar to'g'ridan-to'g'ri aytilmagan bo'lsa-yu, miqdor va \
birlik narxi berilgan bo'lsa, ularni ko'paytirib hisoblang; hech qanday summa aniqlab bo'lmasa bo'sh qoldiring),
  "currency": "so'm" yoki "$" yoki "€" va hokazo,
  "description": "qisqa va lo'nda izoh",
  "date": "YYYY-MM-DD" (agar matnda aniq sana ko'rsatilmagan bo'lsa, bo'sh satr qoldiring)
}}

{CATEGORY_GUIDE}

Eng mos kategoriyani tanlang. Agar xabar moliyaviy mazmunga ega bo'lmasa (salomlashish, savol, umuman \
aloqasi yo'q gap va h.k.), faqat {{"is_financial": false}} qaytaring."""

RECEIPT_SYSTEM_PROMPT = f"""Siz "Hisobchi AI" - foydalanuvchi yuborgan chek, hisob-varaq yoki boshqa moliyaviy \
hujjat rasmini tahlil qiluvchi tizimsiz. Rasmni diqqat bilan o'qib, undagi HAR BIR mahsulot/xizmat qatorini \
alohida yozuv sifatida ajrating.

Faqat quyidagi JSON formatida javob qaytaring, boshqa hech qanday matn yoki markdown belgilarisiz:

{{
  "is_financial": true yoki false,
  "items": [
    {{
      "type": "Kirim" yoki "Chiqim",
      "category": "kategoriya nomi",
      "product": "mahsulot yoki xizmat nomi",
      "quantity": raqam (miqdor; aniqlanmasa 1),
      "unit_price": raqam (bitta dona narxi; aniqlanmasa shu qatorning jami summasiga teng),
      "amount": raqam (shu qatorning jami summasi = miqdor x birlik narxi),
      "currency": "so'm" yoki boshqa valyuta,
      "description": "qisqa izoh",
      "date": "YYYY-MM-DD" (chekda ko'rsatilgan sana, aks holda bo'sh qoldiring)
    }}
  ]
}}

{CATEGORY_GUIDE}

Agar chekda mahsulotlar alohida-alohida ko'rsatilmagan, faqat umumiy summa bo'lsa, "items" massivida bitta \
yozuv qaytaring (bunda "product" maydoniga chekning umumiy nomini yozing, masalan "Xarid").
Agar rasmda umuman moliyaviy ma'lumot bo'lmasa (masalan tabiat manzarasi yoki tanish odam rasmi), faqat \
{{"is_financial": false, "items": []}} qaytaring."""

ADVISOR_SYSTEM_PROMPT = """Siz professional moliyaviy va biznes tahlilchisiz, 15 yillik tajribaga ega. Sizga \
yuklangan hujjatni chuqur va tanqidiy tahlil qiling. Javobingizni quyidagi tuzilishda, o'zbek tilida, aniq va \
professional uslubda yozing:

1. Qisqacha mazmun - hujjat nima haqida
2. Asosiy topilmalar va ko'rsatkichlar (agar moliyaviy hujjat bo'lsa - raqamlar, tendensiyalar)
3. Kuchli tomonlari
4. Zaif tomonlari, xatarlar yoki nomuvofiqliklar
5. Aniq va amaliy tavsiyalar

Faktlarga tayaning, hujjatda yo'q narsani o'ylab topmang. Agar biror qism noaniq yoki yetishmasa, buni ochiq \
ayting."""


class AIService:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze_finance_text(self, text: str) -> Optional[dict]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FINANCE_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content.strip()
        data = _parse_json(raw)
        if data is None:
            logger.warning("Moliyaviy tahlil JSON emas: %s", raw)
            return None
        if not data.get("is_financial", False):
            return None
        if not data.get("date"):
            data["date"] = date.today().isoformat()
        return data

    def analyze_finance_receipt(self, content_blocks: list, filename: str) -> Optional[list[dict]]:
        response = self.client.responses.create(
            model=self.model,
            instructions=RECEIPT_SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": content_blocks
                    + [
                        {
                            "type": "input_text",
                            "text": f'"{filename}" rasmidagi moliyaviy ma\'lumotlarni yuqoridagi JSON '
                            f"formatida ajrating.",
                        }
                    ],
                }
            ],
        )
        raw = response.output_text.strip()
        data = _parse_json(raw)
        if data is None:
            logger.warning("Chek tahlili JSON emas: %s", raw)
            return None
        if not data.get("is_financial", False):
            return None

        today = date.today().isoformat()
        records = []
        for item in data.get("items") or []:
            if not item.get("date"):
                item["date"] = today
            records.append(item)
        return records or None

    def analyze_document(self, content_blocks: list, filename: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=ADVISOR_SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": content_blocks
                    + [
                        {
                            "type": "input_text",
                            "text": f'Yuqoridagi "{filename}" nomli hujjatni professional tahlilchi '
                            f"sifatida chuqur tahlil qiling.",
                        }
                    ],
                }
            ],
        )
        return response.output_text.strip()


def _parse_json(raw: str) -> Optional[dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
