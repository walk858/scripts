from __future__ import annotations

import argparse
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


PUNCTUATION = set("，。！？；：、,.!?;:…》”）)】]")
QUESTION_ENDINGS = (
    "吗", "谁", "干嘛", "怎么了", "是不是", "对不对", "为什么",
    "什么事", "咋了", "干什么",
)
QUESTION_SHORT = {"谁呀", "谁啊", "为什么呢", "什么呢"}
COMMA_ENDINGS = ("呢", "啊", "呀", "嘛", "呗", "吧")
PERIOD_ENDINGS = ("哟", "哎呀", "我去", "卧槽", "完了", "哈哈哈", "哈哈", "得了")

BOUNDARY_KEYWORDS = (
    "今儿的这个第一个故事咱就到这了",
    "第一个故事咱说完了",
    "今儿的这第一个故事咱就说到这了",
    "第一个故事就说到这",
    "欢迎继续收听灵异电台马上我给您说第二个",
    "马上给您说第二个",
    "接下来马上给您说他第三个事",
    "接下来马上给您说第三个事",
    "欢迎继续收听灵异电台",
    "灵异电台精彩继续",
)

MERGE_REPLACEMENTS = {
    "欢迎继续收听。灵异电台。马上我给您说第二个。": "欢迎继续收听灵异电台，马上我给您说第二个。",
    "欢迎继续收听灵异电台。马上我给您说第二个。": "欢迎继续收听灵异电台，马上我给您说第二个。",
    "欢迎继续收听。灵异电台 精彩继续。": "欢迎继续收听灵异电台。精彩继续。",
}


def punctuate(line: str) -> str:
    text = line.strip()
    if not text or text[-1] in PUNCTUATION:
        return text
    if any(text.endswith(end) for end in QUESTION_ENDINGS) or text in QUESTION_SHORT:
        return text + "？"
    if text.endswith(COMMA_ENDINGS):
        return text + "，"
    if text.endswith(PERIOD_ENDINGS):
        return text + "。"
    return text + "。"


def normalize(text: str) -> str:
    return re.sub(r"[\s，。！？；：、,.!?;:“”\"'（）()…]+", "", text)


def split_units(text: str) -> list[str]:
    return re.findall(r".+?[。！？；：]|.+$", text)


def polish_text(raw_text: str, target_min: int = 160, target_max: int = 220) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    text = "".join(punctuate(line) for line in lines)

    for old, new in MERGE_REPLACEMENTS.items():
        text = text.replace(old, new)

    paragraphs: list[str] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer:
            paragraphs.append(buffer)
            buffer = ""

    for unit in split_units(text):
        is_boundary = any(keyword in normalize(unit) for keyword in BOUNDARY_KEYWORDS)
        if is_boundary:
            flush()
            paragraphs.append(unit)
            paragraphs.append("------------")
            continue

        if len(buffer) + len(unit) > target_max and len(buffer) >= target_min:
            flush()
        buffer += unit

    flush()

    cleaned: list[str] = []
    for paragraph in paragraphs:
        if paragraph == "------------" and cleaned and cleaned[-1] == "------------":
            continue
        cleaned.append(paragraph)
    if cleaned and cleaned[-1] == "------------":
        cleaned.pop()

    return "\n\n".join(cleaned) + "\n"


def word_run(text: str) -> str:
    return (
        '<w:r><w:rPr><w:rFonts w:ascii="Microsoft YaHei" '
        'w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/>'
        '<w:sz w:val="24"/></w:rPr>'
        f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
    )


def write_docx(text: str, output_path: Path) -> None:
    body: list[str] = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph == "------------":
            body.append(
                '<w:p><w:pPr><w:jc w:val="center"/>'
                '<w:spacing w:before="120" w:after="120"/></w:pPr>'
                + word_run(paragraph)
                + "</w:p>"
            )
        else:
            body.append(
                '<w:p><w:pPr><w:ind w:firstLineChars="200"/>'
                '<w:spacing w:line="360" w:lineRule="auto" w:after="120"/>'
                '</w:pPr>'
                + word_run(paragraph)
                + "</w:p>"
            )

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14"><w:body>'
        + "".join(body)
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" '
        'w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        '</w:sectPr></w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    word_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", word_rels)


def convert_file(input_path: Path, output_dir: Path | None = None, stem: str | None = None) -> tuple[Path, Path]:
    output_dir = output_dir or input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = stem or f"{input_path.stem}_polished"

    raw_text = input_path.read_text(encoding="utf-8-sig")
    polished = polish_text(raw_text)

    txt_path = output_dir / f"{stem}.txt"
    docx_path = output_dir / f"{stem}.docx"
    txt_path.write_text(polished, encoding="utf-8-sig")
    write_docx(polished, docx_path)
    return txt_path, docx_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Polish Chinese story captions into readable text and Word files.")
    parser.add_argument("input", type=Path, help="Input .txt subtitle/transcript file")
    parser.add_argument("-o", "--output-dir", type=Path, default=None, help="Directory for generated files")
    parser.add_argument("--stem", default=None, help="Output file stem without extension")
    args = parser.parse_args()

    txt_path, docx_path = convert_file(args.input, args.output_dir, args.stem)
    print(f"txt={txt_path}")
    print(f"docx={docx_path}")


if __name__ == "__main__":
    main()
