# v2.2-lite — Conditional Gates & Red Team

本次只迁移旧 `workflow/conditional-gates-red-team-v2.2` 中仍有独立价值的机制，不整支合并旧分支。

- 新增轻量 Conditional Gate Registry：只负责识别模型结构触发器，不重复 Evidence Gate 的实验细节；
- 新增轻量 Red-Team 协议：由非 Owner Reviewer 从评委角度主动攻击核心 Claim；
- Dispatcher 仅增加路由入口，不把 CG1–CG10 的详细规则继续复制到 Shared Core/Profile；
- 目标：保留新能力，同时避免 Skill 继续膨胀。
