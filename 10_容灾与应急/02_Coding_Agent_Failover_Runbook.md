# Coding Agent Failover Runbook

## Level 0：短暂异常（约 <10–15 min）

- 重试
- 新 session
- 客户端重启
- 网络检查
- 保持 Primary Task

## Level 1：持续不可用（约 15–30 min）

Technical Lead 立即切换 Secondary Coding Agent。

要求：
- 读取同一 repo
- 读取 project_state
- 读取当前 task sheet
- 读取同一 Skill
- 继续原 branch / 明确新 branch
- 先跑 tests
- 再继续修改

**不得因此和 XXT 互换角色。**

## Level 2：两个 Coding Agent 都不可用

降级为：

```text
IDE / Python / Git
        +
普通聊天模型辅助
```

AI负责：
- diagnosis
- code suggestion
- patch proposal

人负责：
- 本地修改
- 运行
- tests
- commit

速度会下降，但组织结构不变。

## Level 3：Technical Lead 本人无法继续

才进入人员级 Deputy 方案。
