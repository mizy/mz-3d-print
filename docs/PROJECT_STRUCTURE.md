# 统一项目结构

项目根统一为 `models/`；原 `projects/dog-bow/` 已搬至 `models/dog-bowl-shared/`，只作为共享设计资料，不生成打印模型卡片。

品牌目录和当前STEP路径保持不变。每品牌使用 Models、Design、Notes、Source 四个平级子目录。历史审计中的旧路径维持原文，便于按当时的提交追溯；映射规则为 `projects/dog-bow/<path>` → `models/dog-bowl-shared/<path>`。

本次整理未复原或纳入提交此前本地删除的三张共享设计图；这些待处理工作树改动随目录搬迁，不改变用户删除意图。
