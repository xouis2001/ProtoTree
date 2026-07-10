import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import ProtocolCategory, ProtocolTag, ProtocolTagGroup, TaxonomySource, TaxonomyStatus


TAXONOMY_SEED = [
    {
        "name": "细胞与组织实验",
        "description": "细胞培养、处理、染色、组织切片和细胞功能检测",
        "color": "#2563eb",
        "groups": [
            {"name": "细胞 / 样本类型", "description": "细胞类型、来源或分化体系", "tags": ["通用 / 不限定细胞类型", "293T", "HeLa", "PC12", "Daoy", "小鼠原代神经元", "iPSC", "神经元分化", "原代神经元培养", "脑类器官"]},
            {"name": "实验方法", "description": "细胞和组织相关实验方法", "tags": ["细胞培养", "细胞传代", "细胞冻存", "细胞复苏", "细胞转染", "稳转细胞系构建", "核质分离", "PFF处理", "α-synuclein", "免疫荧光", "免疫组化", "流式细胞术", "细胞活力"]},
            {"name": "检测指标 / 读出方式", "description": "实验检测指标和结果读出方式", "tags": ["细胞死亡", "凋亡", "线粒体自噬"]},
            {"name": "组织处理", "description": "组织样本处理流程", "tags": ["冰冻切片", "抗原修复"]},
        ],
    },
    {
        "name": "分子生物学实验",
        "description": "核酸提取、扩增定量、克隆构建、基因编辑和测序建库",
        "color": "#7c3aed",
        "groups": [
            {"name": "核酸提取与质控", "description": "DNA/RNA 提取、纯化和质量控制", "tags": ["DNA 提取", "RNA 提取", "凝胶电泳"]},
            {"name": "扩增与定量", "description": "PCR 及核酸定量相关实验", "tags": ["PCR", "RT-PCR", "qPCR", "扩增效率", "逆转录"]},
            {"name": "克隆构建", "description": "质粒构建、连接、转化、突变和验证", "tags": ["分子克隆", "限制性酶切", "DNA连接", "细菌转化", "质粒提取", "定点突变", "DpnI切割"]},
            {"name": "基因编辑", "description": "CRISPR/Cas 等基因编辑实验", "tags": ["CRISPR/Cas9", "基因编辑"]},
            {"name": "分子互作 / 分子结合", "description": "DNA、RNA、蛋白等分子互作检测", "tags": ["pull-down", "SPR", "BLI"]},
            {"name": "表达调控与报告实验", "description": "基因表达调控和报告基因实验", "tags": ["siRNA", "shRNA"]},
            {"name": "测序与建库", "description": "不同类型测序文库构建", "tags": ["RNA-seq"]},
        ],
    },
    {
        "name": "蛋白与免疫实验",
        "description": "蛋白提取、检测、纯化、互作和免疫相关实验",
        "color": "#db2777",
        "groups": [
            {"name": "蛋白检测", "description": "蛋白表达、聚集和定量检测", "tags": ["Western blot", "BCA", "蛋白提取", "SDS-PAGE", "转膜", "Dot blot", "Filter trap", "蛋白聚集体检测"]},
            {"name": "蛋白互作", "description": "蛋白互作和复合物分析", "tags": ["Co-IP", "pull-down", "免疫沉淀"]},
            {"name": "蛋白制备", "description": "蛋白表达、纯化和保存", "tags": ["蛋白浓缩", "原核表达", "Ni-NTA纯化", "蛋白纯化"]},
            {"name": "酶活检测", "description": "激酶等酶活性和反应读出检测", "tags": ["激酶活性检测", "ADP-Glo"]},
        ],
    },
    {
        "name": "动物实验",
        "description": "动物模型、给药、手术、行为学和取材",
        "color": "#16a34a",
        "groups": [
            {"name": "实验操作", "description": "动物实验操作", "tags": ["尾静脉注射", "腹腔注射", "灌胃", "灌流固定", "安乐死", "脑立体定位注射", "手术"]},
            {"name": "行为与评估", "description": "动物行为学和表型评估", "tags": ["旷场实验", "水迷宫", "体重监测", "生存曲线", "小鼠模型", "行为学", "基因分型"]},
            {"name": "模式动物", "description": "常见模式动物和相关操作", "tags": ["果蝇实验", "斑马鱼实验", "显微注射"]},
        ],
    },
    {
        "name": "微生物与病毒实验",
        "description": "细菌、病毒、感染模型和生物安全相关实验",
        "color": "#0891b2",
        "groups": [
            {"name": "培养与感染", "description": "微生物培养、病毒包装和感染操作", "tags": ["细菌培养", "病毒包装", "病毒感染", "慢病毒包装", "AAV包装"]},
        ],
    },
    {
        "name": "成像与仪器操作",
        "description": "显微成像、仪器 SOP 和图像采集",
        "color": "#4f46e5",
        "groups": [
            {"name": "仪器平台", "description": "仪器使用和设置", "tags": ["荧光显微镜", "流式细胞仪", "酶标仪", "活细胞成像", "透射电镜", "冷冻电镜", "Cryo-EM"]},
            {"name": "成像方法", "description": "基于显微成像的实验读出方法", "tags": ["BiFC"]},
        ],
    },
    {
        "name": "样本处理与试剂配制",
        "description": "样本前处理、保存运输和常用试剂配方",
        "color": "#64748b",
        "groups": [
            {"name": "样本与试剂", "description": "样本处理和试剂配制", "tags": ["血液样本"]},
        ],
    },
    {
        "name": "分子互作与生物物理",
        "description": "分子结合、热稳定性、RNA 互作和生物物理特殊读出",
        "color": "#0f766e",
        "groups": [
            {"name": "分子结合", "description": "蛋白、核酸、小分子等分子结合检测", "tags": ["MST", "微量热泳动", "ITC", "等温滴定量热", "BLI", "SPR"]},
            {"name": "热稳定性", "description": "蛋白热稳定性和配体结合稳定性检测", "tags": ["nanoDSF", "CETSA"]},
            {"name": "RNA互作", "description": "RNA 与蛋白或核酸的互作检测", "tags": ["RNA-EMSA", "RNA-IP", "RIP"]},
        ],
    },
    {
        "name": "高通量筛选",
        "description": "高通量筛选平台、板式检测和小分子筛选",
        "color": "#ea580c",
        "groups": [
            {"name": "检测读出", "description": "筛选读出体系和板式检测", "tags": ["HTRF", "384孔板筛选"]},
            {"name": "筛选平台", "description": "高通量或芯片化筛选平台", "tags": ["小分子芯片筛选", "SMM"]},
        ],
    },
    {
        "name": "组学分析",
        "description": "转录组、脂质组、质谱组学和翻译组学分析",
        "color": "#9333ea",
        "groups": [
            {"name": "测序与组学", "description": "测序和组学数据分析", "tags": ["RNA-seq", "转录组分析"]},
            {"name": "质谱组学", "description": "质谱相关组学分析", "tags": ["脂质组学", "LC-MS/MS"]},
            {"name": "翻译组学", "description": "翻译状态和核糖体相关组学分析", "tags": ["多聚核糖体分析"]},
        ],
    },
    {
        "name": "特殊技术",
        "description": "跨学科、专门化或暂不适合归入常规分类的实验技术",
        "color": "#be123c",
        "groups": [
            {"name": "生物物理特殊技术", "description": "相分离等特殊生物物理实验", "tags": ["LLPS", "相分离"]},
            {"name": "光控技术", "description": "光遗传和光控实验", "tags": ["光遗传"]},
            {"name": "翻译监测", "description": "蛋白翻译状态监测", "tags": ["SunSET", "SunRiSE", "翻译监测"]},
            {"name": "化学生物学", "description": "点击化学和生物正交标记", "tags": ["Click Chemistry", "生物正交标记"]},
            {"name": "化学合成", "description": "化合物合成、纯化和表征", "tags": ["化合物合成", "HPLC", "LC-MS", "NMR"]},
        ],
    },
]


def normalize_taxonomy_name(value: str) -> str:
    return re.sub(r"[\s\-_　]+", "", value.strip().lower())


async def seed_taxonomy(session: AsyncSession) -> None:
    seen_category_ids: set[int] = set()
    seen_group_ids: set[int] = set()
    seen_tag_ids: set[int] = set()

    for category_index, category_data in enumerate(TAXONOMY_SEED):
        category = await session.scalar(select(ProtocolCategory).where(ProtocolCategory.name == category_data["name"]))
        if category is None:
            category = ProtocolCategory(name=category_data["name"])
            session.add(category)
            await session.flush()
        category.description = category_data["description"]
        category.color = category_data["color"]
        category.source = TaxonomySource.official
        category.status = TaxonomyStatus.active
        category.sort_order = category_index
        seen_category_ids.add(category.id)

        for group_index, group_data in enumerate(category_data["groups"]):
            normalized_group_name = normalize_taxonomy_name(group_data["name"])
            group = await session.scalar(select(ProtocolTagGroup).where(ProtocolTagGroup.category_id == category.id, ProtocolTagGroup.normalized_name == normalized_group_name))
            if group is None:
                group = ProtocolTagGroup(category_id=category.id, name=group_data["name"], normalized_name=normalized_group_name)
                session.add(group)
                await session.flush()
            group.name = group_data["name"]
            group.description = group_data["description"]
            group.source = TaxonomySource.official
            group.status = TaxonomyStatus.active
            group.sort_order = group_index
            seen_group_ids.add(group.id)

            for tag_index, tag_name in enumerate(group_data["tags"]):
                normalized_tag_name = normalize_taxonomy_name(tag_name)
                tag = await session.scalar(select(ProtocolTag).where(ProtocolTag.category_id == category.id, ProtocolTag.tag_group_id == group.id, ProtocolTag.normalized_name == normalized_tag_name))
                if tag is None:
                    tag = ProtocolTag(category_id=category.id, tag_group_id=group.id, name=tag_name, normalized_name=normalized_tag_name)
                    session.add(tag)
                    await session.flush()
                tag.name = tag_name
                tag.source = TaxonomySource.official
                tag.status = TaxonomyStatus.active
                tag.sort_order = tag_index
                seen_tag_ids.add(tag.id)

    official_categories = (await session.scalars(select(ProtocolCategory).where(ProtocolCategory.source == TaxonomySource.official))).all()
    for category in official_categories:
        if category.id not in seen_category_ids:
            category.status = TaxonomyStatus.disabled

    official_groups = (await session.scalars(select(ProtocolTagGroup).where(ProtocolTagGroup.source == TaxonomySource.official))).all()
    for group in official_groups:
        if group.id not in seen_group_ids:
            group.status = TaxonomyStatus.disabled

    official_tags = (await session.scalars(select(ProtocolTag).where(ProtocolTag.source == TaxonomySource.official))).all()
    for tag in official_tags:
        if tag.id not in seen_tag_ids:
            tag.status = TaxonomyStatus.disabled

    await session.commit()
