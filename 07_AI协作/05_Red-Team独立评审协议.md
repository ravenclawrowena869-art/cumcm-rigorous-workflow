# Red-Team 独立评审协议 v2.2-lite

Red Team 的任务不是继续优化模型，而是站在评委/反方角度主动找：**哪条 Claim 最容易被攻击，哪项证据最薄。**

## 什么时候做

至少在单问 Freeze 前做一次；全文锁稿前可再做一次压缩版。

Reviewer 不应是该问 Model Owner。若由 AI 执行，应先看官方题面、当前模型、结果和 Gate Evidence，再看作者解释。

## 固定攻击问题

1. 哪个关键假设一放松，最可能改变结论？
2. 哪个参数、权重、阈值最像经验设定？
3. 哪个算法最可能依赖顺序、tie-breaker、seed 或初值？
4. 有没有 small-scale truth / bound / exact anchor 可以检验方案质量？
5. 哪个结果虽然可行，但离 hard constraint 太近？
6. 哪个中间信号的数学含义被默认相信，却没独立验证？
7. 哪个“收敛、稳健、最优、显著改善”类 Claim 证据最薄？
8. 有没有异常漂亮、接近零、负值或数量级反常的数字？
9. 哪个终端、峰值、切换点、不可行点值得局部复算或解释？
10. 对照是否同口径，还是某个 baseline 被人为削弱？
11. 换成一个合理但更难的场景，模型最先在哪里失效？
12. 如果我是评委，只问三个扣分问题，会问什么？

## 输出格式

| ID | 攻击点 | 严重度 | 证据 | 建议动作 | 阻断 Freeze |
|---|---|---|---|---|---|
| RT-01 |  | HIGH/MEDIUM/LOW |  | 补实验/复算/缩 Claim/解释 | YES/NO |

严重度：
- `HIGH`：可能改变主要结论、可行性或模型合法性；
- `MEDIUM`：明显影响可信度、稳健性或研究深度；
- `LOW`：主要影响表达、图表或次要解释。

## 关闭方式

只允许：
- `CLOSED_BY_EXPERIMENT`
- `CLOSED_BY_RECOMPUTE`
- `CLOSED_BY_MODEL_CHANGE`
- `CLOSED_BY_CLAIM_REDUCTION`
- `CLOSED_BY_OFFICIAL_RULE`
- `OPEN_BLOCKING`

HIGH 问题不能用“时间不够”“应该没事”关闭。

## 与 Conditional Gate 的关系

Red Team 只负责发现攻击点，不重复定义验证实验。发现问题后映射到 `04_验收冻结/06_条件触发Gate与证据协议.md`：假设→CG1，顺序→CG2，最优性→CG3，余量→CG4，反馈→CG5，派生信号→CG6，收敛→CG7，边界→CG8，对照→CG9，数量级→CG10。没有对应项时记录 `CUSTOM_GATE`。