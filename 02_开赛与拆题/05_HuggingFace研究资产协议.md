# Hugging Face 研究资产协议 v1.0

本协议用于数学建模任务中涉及机器学习、预训练模型、公开外部数据、论文对应资产或远程计算资产时的研究与 provenance 管理。

## 1. 定位

`HF Research Lane` 是**条件触发**的研究加速器，**不得作为默认必经步骤**，也不得因为 Hugging Face 上存在现成模型就反向替代题意分析、Atlas、学术原型、EDA、baseline 或本题验证。

正常主线仍为：

`官方题面/附件 → Atlas/学术原型 → EDA → baseline → targeted upgrade → validation`

只有当 Hugging Face 资产能解决一个已经被定义的具体缺口时才进入该 Lane。

## 2. 触发条件

满足至少一项时可触发：

- 当前问题包含 ML / DL / pretrained model；
- 需要建立预测、分类、视觉、NLP、Embedding 等 challenger；
- 赛题规则允许且确实需要公开外部数据；
- 已找到论文，需要定位对应 Model / Dataset / Space / GitHub 实现；
- 需要核对 checkpoint、量化格式、framework、license、hardware compatibility；
- 本地算力不足，且团队已明确批准外部云端计算。

对 LP / MILP / CP-SAT、纯统计推断、传统评价、解析几何、ODE/PDE、纯运筹优化等任务默认不触发，除非其中确有 ML proxy、外部数据或预训练资产需求。

## 3. 证据链

推荐研究链：

`Paper → Model → Dataset → Space → GitHub → Local Benchmark`

证据等级：

1. 原始论文 / DOI / arXiv / 作者正式页面：方法与数学依据；
2. 官方 Model Card / Dataset Card：资产版本、字段、license、适用范围；
3. 作者或官方 GitHub：实现与复现依据；
4. 官方/作者 Space：Demo 与接口线索；
5. 第三方模型、量化、社区 Space：候选线索，只能进入待验证池。

Model Card、Dataset Card、Space 展示指标或第三方 benchmark **不得替代本题 local benchmark / challenger comparison**。

## 4. HF Asset Provenance

凡进入正式代码、实验、图表或论文结论的 Hugging Face 资产，至少记录：

```text
asset_type: model | dataset | space
repo_id:
revision / commit SHA:
author:
license:
model_card / dataset_card:
framework / task:
download_date:
relevant_files:
critical_file_sha256:
upstream_paper:
upstream_github:
hardware:
local_wrapper_version:
local benchmark:
```

禁止仅记录 `latest`、`main`、`最新版`、`当前热门模型` 作为可复现版本依据。

## 5. 数据与远程计算安全

未经明确批准，禁止把以下内容上传到公开或第三方 Hugging Face Dataset、Space、Job 或其他远程资产：

- 官方赛题附件原始数据；
- 团队私有数据；
- 未公开中间结果；
- 含敏感信息或尚未确认许可的数据。

远程 Job 需要读取非公开比赛数据时，必须先取得：

`DATA_EXTERNAL_COMPUTE_APPROVED=true`

否则仅允许使用公开数据、synthetic data、明确脱敏且获批的数据，或在本地完成实验。

## 6. 可用性与降级

Hugging Face 插件、Hub、Jobs 或网络不可用时：

`HF_UNAVAILABLE → 继续使用原论文 + Web/学术检索 + GitHub + 本地 baseline/challenger`

HF 不可用不得阻塞比赛主线，也不得降低 Evidence Gate。

## 7. 输出要求

一次正式 HF Research Lane 至少输出：

- 触发原因与研究问题；
- 候选资产及淘汰理由；
- authority / license / revision；
- hardware 与实现可行性；
- 本题 local benchmark 计划与结果；
- 是否进入主模型、challenger、screening/proxy 或仅作实现参考；
- provenance 与 limitation。

只有本题证据通过后，HF 资产才能进入 Frozen Source of Truth。
