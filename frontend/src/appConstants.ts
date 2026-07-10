import type { ContributionProfileLeaderboardMetric, StructuredProtocol } from './types'

export const defaultRawText = '免疫荧光\n第一步：准备 PBS 1x，BSA 5%，一抗 1:1000 200 μL。\n第二步：PBS 清洗细胞 3 次，每次 5 分钟。\n第三步：加入 BSA 室温封闭 30 分钟。\n第四步：加入一抗 4°C overnight。'

export const avatarColors = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#dc2626', '#ea580c', '#d97706',
  '#ca8a04', '#65a30d', '#16a34a', '#059669', '#0d9488', '#0891b2', '#0284c7', '#2563eb', '#4f46e5', '#7c3aed',
  '#9333ea', '#c026d3', '#db2777', '#e11d48', '#991b1b', '#9a3412', '#92400e', '#854d0e', '#3f6212', '#166534',
  '#047857', '#115e59', '#155e75', '#075985', '#1d4ed8', '#3730a3', '#5b21b6', '#6b21a8', '#9d174d', '#be123c',
  '#7f1d1d', '#7c2d12', '#78350f', '#713f12', '#365314', '#14532d', '#064e3b', '#134e4a', '#164e63', '#0c4a6e',
  '#1e3a8a', '#312e81', '#4c1d95', '#581c87', '#831843', '#881337'
]

export const defaultStructured: StructuredProtocol = {
  experiment_name: '免疫荧光 Protocol',
  experiment_type: '细胞实验',
  experiment_subtype: '免疫荧光',
  steps: [
    { order: 1, title: '准备试剂', content: '准备 PBS 1x，BSA 5%，一抗 1:1000 200 μL。', parameters: { PBS: '1x', BSA: '5%', 一抗: '1:1000 200 μL' } },
    { order: 2, title: 'PBS 清洗', content: 'PBS 清洗细胞 3 次。', parameters: { duration: '每次 5 分钟' } },
    { order: 3, title: '封闭', content: '加入 BSA 室温封闭。', parameters: { duration: '30 分钟' } },
    { order: 4, title: '一抗孵育', content: '加入一抗孵育。', parameters: { duration: '4°C overnight' } },
  ],
}

export const experimentTypeOptions = ['细胞实验', '体外实验', '动物实验', '数据处理']

export const experimentSubtypeOptions: Record<string, string[]> = {
  细胞实验: ['细胞培养', '流式细胞术', '细胞转染'],
  体外实验: ['免疫荧光', 'Western blot', 'qPCR', 'ELISA', 'PCR'],
  动物实验: ['动物建模', '给药实验', '组织取材', '行为学实验'],
  数据处理: ['ImageJ', '转录组分析', '蛋白组分析', '统计分析', '图像分析'],
}

export const contributionProfileLeaderboardMetrics: { key: ContributionProfileLeaderboardMetric; label: string; unit: string }[] = [
  { key: 'protocol_count', label: '发布 Protocol 总数', unit: '个' },
  { key: 'update_count', label: '更新 Protocol 次数', unit: '次' },
  { key: 'comment_count', label: '评论总数', unit: '条' },
  { key: 'star_received_count', label: '收获 star 总数', unit: '个' },
  { key: 'forked_count', label: '被 fork 总次数', unit: '次' },
  { key: 'commercial_protocol_count', label: '上传商品化试剂 Protocol 数量', unit: '个' },
  { key: 'image_macro_count', label: '上传 ImageJ macro 数量', unit: '个' },
  { key: 'analysis_tool_count', label: '上传原创分析工具数量', unit: '个' },
  { key: 'agent_skill_count', label: '上传 Agent Skill 数量', unit: '个' },
]

