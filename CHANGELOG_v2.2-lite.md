# v2.2-lite — Conditional Gates & Red Team

本次只迁移旧 `workflow/conditional-gates-red-team-v2.2` 中仍有独立价值的机制，不整支合并旧分支。

- 新增轻量 Conditional Gate Registry，并将其从“算法→固定检查”改成“结构/Claim→失败假设→风险判断→选择验证”的风险雷达；
- 算法名和模型名只作为风险线索，不作为机械触发器；一个模型可同时触发多个风险，同一种风险也可来自不同算法；
- 新增轻量 Red-Team 协议：先自由攻击核心 Claim，再把已发现的问题归入风险 Gate；CG1–CG10 不是固定题单；
- `CUSTOM_RISK` 允许承接现有十类之外的重要问题，避免为套模板硬塞分类；
- Dispatcher 仅增加风险扫描与 Red-Team 路由，不把详细规则继续复制到 Shared Core/Profile；
- 具体实验方法仍由 Evidence Gate / 专属 validator 负责，避免 Skill 继续膨胀。
