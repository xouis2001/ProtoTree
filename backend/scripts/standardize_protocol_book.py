from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


CHAPTER_RE = re.compile(r"^第\s*\d+\s*章\b")
TITLE_SPLIT_RE = re.compile(r"\s*/\s*")
STEP_TITLE_RE = re.compile(r"^\s*(\d+)[.、]\s*(.+)")


@dataclass(frozen=True)
class TaxonomySuggestion:
    category: str
    tag_groups: tuple[str, ...]
    tags: tuple[str, ...]


CATEGORY_BY_CHAPTER = {
    "Molecular Biology": "分子生物学实验",
    "分子生物学": "分子生物学实验",
    "Protein Technology": "蛋白与免疫实验",
    "蛋白质技术": "蛋白与免疫实验",
    "Cell Biology": "细胞与组织实验",
    "细胞生物学": "细胞与组织实验",
    "Detection & Imaging": "成像与仪器操作",
    "检测与成像": "成像与仪器操作",
    "Molecular Interaction": "分子互作与生物物理",
    "分子互作与生物物理": "分子互作与生物物理",
    "High-Throughput Screening": "高通量筛选",
    "高通量筛选": "高通量筛选",
    "Animal Models": "动物实验",
    "动物模型": "动物实验",
    "Omics": "组学分析",
    "组学分析": "组学分析",
    "Specialized Techniques": "特殊技术",
    "特殊技术": "特殊技术",
}

KNOWN_CATEGORIES = {
    "细胞与组织实验",
    "分子生物学实验",
    "蛋白与免疫实验",
    "动物实验",
    "微生物与病毒实验",
    "成像与仪器操作",
    "样本处理与试剂配制",
    "分子互作与生物物理",
    "高通量筛选",
    "组学分析",
    "特殊技术",
}

TAXONOMY_BY_TITLE: dict[str, TaxonomySuggestion] = {
    "分子克隆": TaxonomySuggestion("分子生物学实验", ("克隆构建",), ("分子克隆", "PCR", "限制性酶切", "DNA连接", "细菌转化", "质粒提取")),
    "定点突变": TaxonomySuggestion("分子生物学实验", ("克隆构建",), ("定点突变", "PCR", "DpnI切割", "细菌转化")),
    "RNA提取与qRT-PCR": TaxonomySuggestion("分子生物学实验", ("扩增与定量",), ("RNA 提取", "逆转录", "qPCR")),
    "蛋白质提取与BCA定量": TaxonomySuggestion("蛋白与免疫实验", ("蛋白检测",), ("蛋白提取", "BCA")),
    "Western印迹法": TaxonomySuggestion("蛋白与免疫实验", ("蛋白检测",), ("Western blot", "SDS-PAGE", "转膜", "BCA")),
    "Dot印迹法": TaxonomySuggestion("蛋白与免疫实验", ("蛋白检测",), ("Dot blot",)),
    "免疫共沉淀": TaxonomySuggestion("蛋白与免疫实验", ("蛋白互作",), ("Co-IP", "免疫沉淀")),
    "Pull-Down检测": TaxonomySuggestion("蛋白与免疫实验", ("蛋白互作",), ("pull-down",)),
    "原核蛋白表达与纯化": TaxonomySuggestion("蛋白与免疫实验", ("蛋白制备",), ("原核表达", "Ni-NTA纯化", "蛋白纯化")),
    "过滤捕获实验": TaxonomySuggestion("蛋白与免疫实验", ("蛋白检测",), ("Filter trap", "蛋白聚集体检测")),
    "细胞培养": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("细胞培养", "细胞传代", "细胞冻存", "细胞复苏")),
    "细胞转染": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("细胞转染",)),
    "慢病毒包装": TaxonomySuggestion("微生物与病毒实验", ("培养与感染",), ("病毒包装", "慢病毒包装", "病毒感染")),
    "AAV包装": TaxonomySuggestion("微生物与病毒实验", ("培养与感染",), ("AAV包装", "病毒包装")),
    "CRISPR": TaxonomySuggestion("分子生物学实验", ("基因编辑",), ("CRISPR/Cas9", "基因编辑")),
    "稳转细胞系构建": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("稳转细胞系构建",)),
    "iPSC与神经元分化": TaxonomySuggestion("细胞与组织实验", ("细胞 / 样本类型",), ("iPSC", "神经元分化")),
    "原代神经元培养": TaxonomySuggestion("细胞与组织实验", ("细胞 / 样本类型",), ("小鼠原代神经元", "原代神经元培养")),
    "脑类器官培养": TaxonomySuggestion("细胞与组织实验", ("细胞 / 样本类型",), ("脑类器官",)),
    "核质分离": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("核质分离",)),
    "α-synuclein PFF处理": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("PFF处理", "α-synuclein")),
    "免疫荧光": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("免疫荧光",)),
    "HTRF检测": TaxonomySuggestion("高通量筛选", ("检测读出",), ("HTRF", "384孔板筛选")),
    "流式细胞术": TaxonomySuggestion("细胞与组织实验", ("实验方法",), ("流式细胞术",)),
    "活细胞成像": TaxonomySuggestion("成像与仪器操作", ("仪器平台",), ("活细胞成像", "荧光显微镜")),
    "BiFC - 双分子荧光互补": TaxonomySuggestion("成像与仪器操作", ("成像方法",), ("BiFC",)),
    "线粒体自噬检测": TaxonomySuggestion("细胞与组织实验", ("检测指标 / 读出方式",), ("线粒体自噬",)),
    "细胞活力与凋亡检测": TaxonomySuggestion("细胞与组织实验", ("检测指标 / 读出方式",), ("细胞活力", "凋亡", "细胞死亡")),
    "透射电镜": TaxonomySuggestion("成像与仪器操作", ("仪器平台",), ("透射电镜",)),
    "微量热泳动": TaxonomySuggestion("分子互作与生物物理", ("分子结合",), ("MST", "微量热泳动")),
    "等温滴定量热": TaxonomySuggestion("分子互作与生物物理", ("分子结合",), ("ITC", "等温滴定量热")),
    "生物膜层干涉": TaxonomySuggestion("分子互作与生物物理", ("分子结合",), ("BLI",)),
    "表面等离子共振": TaxonomySuggestion("分子互作与生物物理", ("分子结合",), ("SPR",)),
    "nanoDSF 与 CETSA": TaxonomySuggestion("分子互作与生物物理", ("热稳定性",), ("nanoDSF", "CETSA")),
    "RNA 结合分析": TaxonomySuggestion("分子互作与生物物理", ("RNA互作",), ("RNA-EMSA", "RNA-IP", "RIP")),
    "小分子芯片筛选": TaxonomySuggestion("高通量筛选", ("筛选平台",), ("小分子芯片筛选", "SMM")),
    "HTRF 384孔板筛选": TaxonomySuggestion("高通量筛选", ("检测读出",), ("HTRF", "384孔板筛选")),
    "果蝇实验": TaxonomySuggestion("动物实验", ("模式动物",), ("果蝇实验", "行为学")),
    "小鼠模型与行为学测试": TaxonomySuggestion("动物实验", ("行为与评估",), ("小鼠模型", "行为学", "基因分型")),
    "脑立体定位注射": TaxonomySuggestion("动物实验", ("实验操作",), ("脑立体定位注射", "手术")),
    "斑马鱼实验": TaxonomySuggestion("动物实验", ("模式动物",), ("斑马鱼实验", "显微注射")),
    "转录组分析": TaxonomySuggestion("组学分析", ("测序与组学",), ("RNA-seq", "转录组分析")),
    "脂质组学": TaxonomySuggestion("组学分析", ("质谱组学",), ("脂质组学", "LC-MS/MS")),
    "多聚核糖体分析": TaxonomySuggestion("组学分析", ("翻译组学",), ("多聚核糖体分析",)),
    "相分离实验": TaxonomySuggestion("特殊技术", ("生物物理特殊技术",), ("LLPS", "相分离")),
    "光遗传": TaxonomySuggestion("特殊技术", ("光控技术",), ("光遗传",)),
    "翻译监测": TaxonomySuggestion("特殊技术", ("翻译监测",), ("SunSET", "SunRiSE", "翻译监测")),
    "Click Chemistry生物正交反应": TaxonomySuggestion("特殊技术", ("化学生物学",), ("Click Chemistry", "生物正交标记")),
    "冷冻电子显微镜": TaxonomySuggestion("成像与仪器操作", ("仪器平台",), ("冷冻电镜", "Cryo-EM")),
    "激酶活性检测": TaxonomySuggestion("蛋白与免疫实验", ("酶活检测",), ("激酶活性检测", "ADP-Glo")),
    "化合物合成": TaxonomySuggestion("特殊技术", ("化学合成",), ("化合物合成", "HPLC", "LC-MS", "NMR")),
}


@dataclass
class DocBlock:
    kind: str
    text: str = ""
    style: str = ""
    level: int | None = None
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class ProtocolBlock:
    title: str
    chapter: str
    blocks: list[DocBlock] = field(default_factory=list)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def get_text(self) -> str:
        return "\n".join(self.parts)


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").strip().split())


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def split_title(title: str) -> tuple[str, str]:
    parts = TITLE_SPLIT_RE.split(title, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


def category_from_chapter(chapter: str) -> str:
    for key, category in CATEGORY_BY_CHAPTER.items():
        if key in chapter:
            return category
    return ""


def is_heading(style: str, level: int | None = None) -> bool:
    if level is None:
        return style.startswith("Heading") or style.startswith("标题")
    return style == f"Heading {level}" or style == f"标题 {level}"


def paragraph_level(style: str) -> int | None:
    match = re.search(r"(?:Heading|标题)\s+(\d+)", style)
    return int(match.group(1)) if match else None


def iter_body_blocks(document: Document) -> Iterable[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def table_rows(table: Table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        rows.append([normalize_text(cell.text) for cell in row.cells])
    return rows


def read_blocks(docx_path: Path) -> tuple[list[ProtocolBlock], list[str]]:
    document = Document(docx_path)
    current_chapter = ""
    current: ProtocolBlock | None = None
    protocols: list[ProtocolBlock] = []
    chapters: list[str] = []

    for item in iter_body_blocks(document):
        if isinstance(item, Table):
            if current is not None:
                current.blocks.append(DocBlock(kind="table", rows=table_rows(item)))
            continue

        text = normalize_text(item.text)
        if not text:
            continue
        style = item.style.name if item.style else ""
        level = paragraph_level(style)
        if is_heading(style, 1):
            if CHAPTER_RE.match(text):
                current_chapter = text
                chapters.append(text)
                current = None
                continue
            current = ProtocolBlock(title=text, chapter=current_chapter)
            protocols.append(current)
            continue
        if current is not None:
            current.blocks.append(DocBlock(kind="paragraph", text=text, style=style, level=level))

    return protocols, chapters


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    output = ["<table><tbody>"]
    for row_index, row in enumerate(rows):
        output.append("<tr>")
        tag = "th" if row_index == 0 else "td"
        for cell in row:
            output.append(f"<{tag}>{escape(cell)}</{tag}>")
        output.append("</tr>")
    output.append("</tbody></table>")
    return "".join(output)


def markdown_heading(text: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{2,6})\s*(.+)$", text)
    if not match:
        return None
    level = min(max(len(match.group(1)), 3), 4)
    return level, match.group(2).strip()


def blocks_to_html(blocks: list[DocBlock]) -> str:
    parts: list[str] = []
    list_mode: str | None = None
    in_code = False
    code_lines: list[str] = []

    def close_list() -> None:
        nonlocal list_mode
        if list_mode:
            parts.append(f"</{list_mode}>")
            list_mode = None

    def close_code() -> None:
        nonlocal in_code, code_lines
        if in_code:
            parts.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
            in_code = False
            code_lines = []

    for block in blocks:
        if block.kind == "table":
            close_code()
            close_list()
            html = render_table(block.rows)
            if html:
                parts.append(html)
            continue

        text = block.text.strip()
        if text == "```":
            close_list()
            if in_code:
                close_code()
            else:
                in_code = True
                code_lines = []
            continue
        if in_code:
            code_lines.append(text)
            continue

        heading = markdown_heading(text)
        if heading:
            close_list()
            level, heading_text = heading
            parts.append(f"<h{level}>{escape(heading_text)}</h{level}>")
            continue

        if is_heading(block.style):
            close_list()
            tag = "h3" if (block.level or 3) <= 2 else "h4"
            parts.append(f"<{tag}>{escape(text)}</{tag}>")
            continue

        lower_style = block.style.lower()
        if "list bullet" in lower_style or lower_style.startswith("项目符号"):
            if list_mode != "ul":
                close_list()
                parts.append("<ul>")
                list_mode = "ul"
            parts.append(f"<li>{escape(text)}</li>")
            continue
        if "list number" in lower_style or lower_style.startswith("编号"):
            if list_mode != "ol":
                close_list()
                parts.append("<ol>")
                list_mode = "ol"
            clean = re.sub(r"^\d+[.、]\s*", "", text).strip()
            parts.append(f"<li>{escape(clean or text)}</li>")
            continue

        close_list()
        parts.append(f"<p>{escape(text)}</p>")

    close_code()
    close_list()
    return "\n".join(parts).strip()


def html_to_text(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def build_sections(blocks: list[DocBlock]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for block in blocks:
        if block.kind != "paragraph":
            if current is not None and block.kind == "table":
                current["content"] = (current["content"] + "\n" + table_rows_text(block.rows)).strip()
            continue
        if block.text.strip() == "```":
            continue
        heading = markdown_heading(block.text)
        if is_heading(block.style) or heading:
            title = heading[1] if heading else block.text
            current = {"title": title, "content": ""}
            sections.append(current)
        elif current is not None:
            text = markdown_heading(block.text)[1] if markdown_heading(block.text) else block.text
            current["content"] = (current["content"] + "\n" + text).strip()
    return sections


def table_rows_text(rows: list[list[str]]) -> str:
    return "\n".join(" | ".join(cell for cell in row if cell) for row in rows)


def build_steps(sections: list[dict[str, str]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for section in sections:
        match = STEP_TITLE_RE.match(section["title"])
        if not match or not section["content"].strip():
            continue
        steps.append(
            {
                "order": int(match.group(1)),
                "title": match.group(2).strip(),
                "content": section["content"].strip(),
                "parameters": {},
            }
        )
    return steps


def make_abstract(sections: list[dict[str, str]], raw_text: str) -> str:
    for section in sections:
        if section["title"] in {"概述", "原理"} and section["content"].strip():
            return " ".join(section["content"].split())[:260]
    return " ".join(raw_text.split())[:260]


def suggest_taxonomy(title_cn: str, chapter: str) -> TaxonomySuggestion:
    if title_cn in TAXONOMY_BY_TITLE:
        return TAXONOMY_BY_TITLE[title_cn]
    category = category_from_chapter(chapter)
    return TaxonomySuggestion(category=category, tag_groups=(), tags=())


def standardize_block(block: ProtocolBlock, source_doc: Path, version_label: str) -> dict[str, Any]:
    title_cn, title_en = split_title(block.title)
    html_content = blocks_to_html(block.blocks)
    raw_text = html_to_text(html_content)
    sections = build_sections(block.blocks)
    steps = build_steps(sections)
    taxonomy = suggest_taxonomy(title_cn, block.chapter)

    warnings: list[str] = []
    if not block.chapter:
        warnings.append("missing_chapter")
    if not taxonomy.category:
        warnings.append("missing_category")
    if taxonomy.category and taxonomy.category not in KNOWN_CATEGORIES:
        warnings.append("new_category_candidate")
    if not html_content.strip() or not raw_text.strip():
        warnings.append("empty_content")
    if not steps:
        warnings.append("no_numbered_steps_detected")

    tag_groups = list(taxonomy.tag_groups)
    tags = list(taxonomy.tags)
    structured = {
        "experiment_name": block.title,
        "experiment_type": taxonomy.category,
        "experiment_subtype": tags[0] if tags else "",
        "experiment_category": taxonomy.category,
        "tag_groups": tag_groups,
        "tags": tags,
        "content": html_content,
        "content_format": "html",
        "steps": steps,
    }
    abstract = make_abstract(sections, raw_text)
    return {
        "source_document": source_doc.name,
        "chapter_title": block.chapter,
        "title": block.title,
        "title_cn": title_cn,
        "title_en": title_en,
        "abstract": abstract,
        "raw_text": raw_text,
        "sections": sections,
        "suggested_category": taxonomy.category,
        "suggested_tag_groups": tag_groups,
        "suggested_tags": tags,
        "warnings": warnings,
        "structured": structured,
        "import_payload_preview": {
            "title": block.title,
            "abstract": abstract,
            "raw_text": raw_text,
            "structured": structured,
            "version_label": version_label,
            "source": "base",
        },
    }


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "chapter",
                "title",
                "title_cn",
                "title_en",
                "suggested_category",
                "suggested_tag_groups",
                "suggested_tags",
                "content_length",
                "section_count",
                "step_count",
                "warnings",
            ],
        )
        writer.writeheader()
        for index, record in enumerate(records, start=1):
            writer.writerow(
                {
                    "index": index,
                    "chapter": record["chapter_title"],
                    "title": record["title"],
                    "title_cn": record["title_cn"],
                    "title_en": record["title_en"],
                    "suggested_category": record["suggested_category"],
                    "suggested_tag_groups": "; ".join(record["suggested_tag_groups"]),
                    "suggested_tags": "; ".join(record["suggested_tags"]),
                    "content_length": len(record["raw_text"]),
                    "section_count": len(record["sections"]),
                    "step_count": len(record["structured"]["steps"]),
                    "warnings": "; ".join(record["warnings"]),
                }
            )


def summarize(records: list[dict[str, Any]], chapters: list[str]) -> dict[str, Any]:
    category_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    for record in records:
        category = record["suggested_category"] or "未分类"
        category_counts[category] = category_counts.get(category, 0) + 1
        for warning in record["warnings"]:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
        for tag in record["suggested_tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for group in record["suggested_tag_groups"]:
            group_counts[group] = group_counts.get(group, 0) + 1
    return {
        "chapter_count": len(chapters),
        "chapters": chapters,
        "protocol_count": len(records),
        "category_counts": dict(sorted(category_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "tag_counts": dict(sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))),
        "tag_group_counts": dict(sorted(group_counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Standardize Protocol Book DOCX into reviewed import artifacts.")
    parser.add_argument("--input", default="Protocol_Book.docx")
    parser.add_argument("--output-dir", default=r"backend\generated")
    parser.add_argument("--version-label", default="v2.0")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    blocks, chapters = read_blocks(input_path)
    records = [standardize_block(block, input_path, args.version_label) for block in blocks]
    summary = summarize(records, chapters)

    json_path = output_dir / "protocol_book_v2_protocols.json"
    csv_path = output_dir / "protocol_book_v2_review.csv"
    summary_path = output_dir / "protocol_book_v2_summary.json"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(records, csv_path)

    print(
        json.dumps(
            {
                "protocol_count": len(records),
                "chapter_count": len(chapters),
                "json": str(json_path),
                "csv": str(csv_path),
                "summary": str(summary_path),
                "category_counts": summary["category_counts"],
                "warning_counts": summary["warning_counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
