# Blocked Rule：禁止纯等待

团队允许“主线 blocked”，不允许“人 blocked”。

## 触发

如果主任务因为上游结果、solver、接口或外部条件超过约 15–30 分钟无法继续：

立即切 Secondary Queue。

---

# CYQ Secondary Queue

- 已确定章节写作
- 论文结构优化
- 文献
- 摘要骨架
- Figure Registry
- 图题/表题
- 结果解释框架
- 页数预审
- 语言统一

# FYQ Secondary Queue

- validator
- tests
- mock
- interface
- clean replay
- manifest
- Skill
- Prompt
- baseline
- figure data pipeline
- repo 清理

# XXT Secondary Queue

- 另一问数学审核
- 推导
- 模型比较
- sensitivity 设计
- validator specification
- 极端情形分析
- baseline 合理性
- 参数数量级检查

---

# 禁止的状态

```text
“我在等他跑完。”
```

正确表述应是：

```text
“我的 Primary Task 被 X 阻塞，我已切换 Secondary Task Y。”
```

每次阶段同步时只需报告：
- Primary
- Blocker
- Secondary
- ETA
