# Work Log

用于记录项目后续的实际改动、问题定位、验证结果和待办事项。
`PLAN.md` 负责规划，本文档负责过程日志。

## 2026-03-16
- Topic: 日志文档初始化
- Changes: 新建 `WORKLOG.md`，作为后续开发过程日志
- Files: `WORKLOG.md`
- Reason: 为接下来的模型升级、测试验证和问题追踪提供统一记录位置
- Verification: 文件已创建，模板可用于持续追加记录
- Follow-up: 后续每次实质性改动后追加一条日志

## 2026-03-16 15:10
- Topic: Phase 1 首轮传播模型升级
- Changes: 在 `config.py` 中新增个体异质性、平台推荐曝光和局部传播影响参数；在 `model.py` 中为每个单元生成活跃度、兴趣匹配度、影响力和疲劳阈值，拆分社交曝光与平台推荐曝光，并记录相关统计指标
- Files: `config.py`, `model.py`, `WORKLOG.md`
- Reason: 按 `PLAN.md` 的 Phase 1 路线，先在不改变整体使用方式的前提下提高传播模型拟真度
- Verification: 已通过源码编译检查；实际运行仍受当前 mac 环境缺少 `numpy` 依赖阻塞
- Follow-up: 在目标解释器中补齐 `numpy`/`matplotlib` 后执行完整运行验证，并决定是否把新增统计项接入可视化

## 2026-03-16 15:28
- Topic: 新增统计项接入可视化
- Changes: 扩展 `visualize.py` 的统计图布局，将社交曝光、推荐曝光、双重曝光、平均邻居传播强度和平均邻居影响力纳入展示
- Files: `visualize.py`, `WORKLOG.md`, `markdown.md`
- Reason: 让 Phase 1 新增的统计指标能够直接被观察和解释，避免模型升级后信息只保留在内部数据结构中
- Verification: 已通过源码编译检查，并在 `first_pyenv` 环境下完成入口运行验证；新增图表字段未出现键名或绘图错误
- Follow-up: 后续如需提升展示效果，可进一步调整子图配色、线型和布局密度

## Template
- Topic:
- Changes:
- Files:
- Reason:
- Verification:
- Follow-up:
