import json

from fastapi import HTTPException, status
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.schemas.structured import ProtocolParseResponse, StructuredProtocol

SYSTEM_PROMPT = """
你是实验室 Protocol 步骤化整理器。你的任务是把用户提供的实验记录转换成严格 JSON 结构。
必须遵守：
1. 只做提取和格式转化，严禁修改、补充或编造任何实验参数。
2. 不再单独拆分试剂、耗材、备注等模块，所有实验信息都必须归入步骤。
3. 每一步按逻辑顺序组织；title 只写该步骤的简短概括，不要写“第一步/第二步/step1/step2”等编号；如果原文里试剂或准备事项没有明确步骤，也要作为准备步骤表达。
4. 保留原文中的浓度、时间、温度、体积、转速、细胞数、抗体稀释比例等参数表达。
5. 原文没有提到的字段返回空字符串、空数组或空对象。
6. 不提供实验建议，不优化步骤，不推断缺失条件。
7. 只返回 JSON 对象，不要返回 Markdown、解释文字或代码块。
JSON 对象必须符合如下结构：
{
  "experiment_name": "",
  "experiment_type": "细胞实验/体外实验/动物实验/数据处理",
  "experiment_subtype": "该一级实验类型下的二级分类，例如免疫荧光、Western blot、动物建模或图像分析",
  "steps": [
    {"order": 1, "title": "步骤概括", "content": "主要内容", "parameters": {}}
  ]
}
""".strip()

DOCUMENT_FORMAT_PROMPT = """
你是实验室 Protocol 文档整理助手。用户会提供从 Word 或 PDF 中提取出的原始文字，可能存在标题不准确、摘要缺失、换行错乱、表格行被压平等问题。
你的任务只允许做格式整理和标题/摘要提炼，必须遵守：
1. 严禁改写、优化、补充、推断或编造任何实验内容、参数和步骤。
2. 正文必须完整保留原文中出现的实验信息、数值、单位、时间、温度、体积、浓度、转速、细胞数、抗体比例等。
3. 可以修复明显的换行错乱、段落断裂、标题层级和列表格式。
4. 可以把原文中用 | 分隔的表格行转换成 HTML 表格，但不得增删单元格内容。
5. title 只根据原文提炼简洁标题；abstract 只根据原文提炼 1-3 句摘要。
6. content_html 只能使用基础 HTML 标签：p、br、strong、em、ul、ol、li、table、tbody、tr、td、th、h3、h4。
7. 只返回 JSON 对象，不要返回 Markdown、解释文字或代码块。
JSON 对象必须符合：
{
  "title": "",
  "abstract": "",
  "content_html": ""
}
""".strip()


class DocumentFormatResult(BaseModel):
    title: str = ""
    abstract: str = ""
    content_html: str = ""


def _ai_client() -> AsyncOpenAI:
    kwargs = dict(
        api_key=settings.ai_api_key,
        default_headers={"User-Agent": "ProtoTree/0.1"},
    )
    if settings.ai_base_url:
        kwargs["base_url"] = settings.ai_base_url
    return AsyncOpenAI(**kwargs)


async def assist_format_uploaded_protocol(raw_text: str, title_hint: str = "") -> ProtocolParseResponse:
    if not settings.ai_api_key or not settings.ai_model or settings.ai_api_key in {"your-api-key", "example-api-key"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置AI_API_KEY或AI_MODEL，无法进行AI辅助整理。",
        )
    try:
        client = _ai_client()
        completion = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": DOCUMENT_FORMAT_PROMPT},
                {"role": "user", "content": f"标题线索：{title_hint.strip()}\n\n原始提取文本：\n{raw_text.strip()}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = completion.choices[0].message.content or "{}"
        data = DocumentFormatResult.model_validate(json.loads(content))
        structured = StructuredProtocol(
            experiment_name=data.title.strip() or title_hint.strip() or _derive_title(raw_text, StructuredProtocol()),
            content=data.content_html.strip() or _plain_text_to_html(raw_text),
            content_format="html",
            steps=[],
        )
        return ProtocolParseResponse(
            title=structured.experiment_name,
            abstract=data.abstract.strip() or _derive_abstract(raw_text),
            structured=structured,
            parser=f"{settings.ai_provider}-format",
            warnings=["AI仅用于标题、摘要和格式整理；请在保存前核对原始实验内容。"],
        )
    except HTTPException:
        raise
    except (ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI辅助整理返回内容不符合格式要求。") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI辅助整理失败：{exc.__class__.__name__}") from exc


async def parse_protocol_text(raw_text: str) -> ProtocolParseResponse:
    if not settings.ai_api_key or not settings.ai_model or settings.ai_api_key in {"your-api-key", "example-api-key"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置AI_API_KEY或AI_MODEL，无法进行AI结构化解析。",
        )

    try:
        return await _parse_with_ai(raw_text.strip())
    except HTTPException:
        raise
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI返回内容不符合结构化Schema：{exc.__class__.__name__}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI返回内容不是合法JSON。",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI结构化解析失败：{exc.__class__.__name__}",
        ) from exc


async def _parse_with_ai(raw_text: str) -> ProtocolParseResponse:
    client = _ai_client()
    completion = await client.chat.completions.create(
        model=settings.ai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        response_format=_response_format(),
        temperature=0,
    )
    content = completion.choices[0].message.content or "{}"
    data = json.loads(content)
    structured = StructuredProtocol.model_validate(data)
    return ProtocolParseResponse(
        title=_derive_title(raw_text, structured),
        abstract=_derive_abstract(raw_text),
        structured=structured,
        parser=settings.ai_provider,
        warnings=[],
    )


def _response_format() -> dict:
    if settings.ai_provider.lower() == "openai":
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_protocol",
                "schema": StructuredProtocol.model_json_schema(),
                "strict": True,
            },
        }
    return {"type": "json_object"}


def _derive_title(raw_text: str, structured: StructuredProtocol) -> str:
    if structured.experiment_name:
        return f"{structured.experiment_name} Protocol"
    first_line = raw_text.strip().splitlines()[0].strip() if raw_text.strip() else ""
    return first_line[:60] or "未命名 Protocol"


def _derive_abstract(raw_text: str) -> str:
    compact = " ".join(raw_text.split())
    return compact[:160]


def _plain_text_to_html(raw_text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "".join(f"<p>{paragraph or '<br>'}</p>" for paragraph in paragraphs)
