# 双 Coding Agent 与故障演练

## 目标

Technical Lead 不得把关键工作绑定在单一 coding agent 上。

推荐赛前至少准备：

- Primary：Codex
- Secondary：第二套 coding agent（例如 Claude Code，或当时可用的其他等价工具）

这里强调的是 **双工具冗余**，不是绑定某个具体厂商。

---

# Secondary Agent 必须提前完成的测试

- [ ] 安装
- [ ] 登录/认证
- [ ] 读取 Git 仓库
- [ ] 修改一个测试项目
- [ ] 运行 Python
- [ ] 运行 tests
- [ ] Git diff / commit
- [ ] 中文路径
- [ ] Excel/CSV
- [ ] ZIP/文件操作
- [ ] 能读取团队 Prompt / Skill
- [ ] 能读取 project_state

如果这些没有赛前跑通，不能把它称为 Plan B。

---

# 赛前故障演练

模拟：

> 比赛第 15 小时，Primary Coding Agent 完全不可用。

要求 Technical Lead 在约 15 分钟内：

1. 切换 Secondary Agent；
2. 打开同一仓库；
3. 读取 `project_state.yaml`；
4. 读取当前任务单；
5. 读取平台无关 Skill；
6. 完成一个小 patch；
7. 跑测试；
8. 输出 diff；
9. commit；
10. 写 HANDOFF。

如果演练失败，继续完善容灾，而不是等正式比赛再处理。
