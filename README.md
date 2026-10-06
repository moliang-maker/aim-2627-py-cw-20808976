# AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块

> **全部题目、规范、评分、提交见 [题面.pdf](题面.pdf)。** 本 README 只讲怎么把环境跑起来；没在这里出现的规格细节，一律以题面为准。

## 1. 环境要求

- Python 3.8+，仅标准库（不允许第三方运行时依赖）；
- 开发工具只需 `pytest`（测试）与 `autopep8`（风格，CI 会检查）；
- VS Code 打开仓库会推荐安装 `ms-python.autopep8` 插件（`.vscode/extensions.json`），保存即格式化即可过风格检查。

## 2. 快速开始

```bash
# 1. 用 GitHub 的 Use this template 创建你自己的仓库，然后 clone
git clone https://github.com/<你的用户名>/<你的仓库>.git
cd <你的仓库>   # 直接在 main 分支上开发

# 创建虚拟环境

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 装依赖
python -m pip install pytest autopep8

# 3. 启用 AI 会话归档钩子（课程要求，见下方第 3 节）
python -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit   # 交互选择你的 AI 助手与会话目录

# 4. 跑测试（刚到手：全部 skip，CI 是绿的）
python -m pytest

# 5. 看演示
python main.py

# 6. 打开 题面.pdf 读题，开始实现 src/main/__init__.py 里的 TODO
```

## 3. AI 会话归档（pre-commit）

本课程允许使用 AI，提交的 commit 需要携带 AI 会话归档作为透明化记录：每次 `git commit` 后，钩子会把新增会话自动 amend 进同一个提交（`.agent-sessions/bundles/`），不产生额外的归档提交。支持 Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Qoder、ZCode、Trae、Tencent CodeBuddy 等（完整名单见 [AgentLedger](https://github.com/Gentle-Lijie/AgentLedger)）。

- 配置是仓库本地的：每个 clone 运行一次 `agent-session-commit install --pre-commit`，方向键选择 agent、确认其会话目录即可；
- 不想用 TUI 可手动配置：`git config --local agent-session.agent claude`、`git config --local agent-session.source "<会话目录>"`，然后 `python -m pip install 'pre-commit>=3.2.0' && pre-commit install`；
- 归档是普通 Git 内容且会推送到公开仓库——不要在 AI 会话里粘贴令牌等敏感信息；
- 换了 agent 或目录就重跑一次安装命令；卸载：从 `.pre-commit-config.yaml` 移除该条目后重跑 `pre-commit install`。

## 4. 本地开发循环

- **写代码**：全部作业在 `src/main/__init__.py`，按题面各题规范补全每个标有 TODO 的函数；注释里标注了对应的题面主题，推荐顺序 Q1 → Q6。
- **跑测试**：`python -m pytest` —— 可见测试是规格书的一部分，未实现的函数自动 skip，实现一个、对应测试亮一个。本地全绿 ≠ 满分（见题面）。
- **看演示**：`python main.py`（等价于 `PYTHONPATH=src python -m main`），随实现进度逐段点亮，不进测试。
- **Q6 自测**：`python tools/run_seeds.py --q6`（200 张固定地图统计），单 seed 渲染 `python tools/run_seeds.py --q6 --seed <N> --render`，Bonus 模式 `python tools/run_seeds.py --bonus`。

## 5. 仓库结构（哪些能改）

| 路径 | 说明 | 能否修改 |
|---|---|---|
| `src/main/__init__.py` | 你的全部作业（TODO 所在） | ✅ |
| `README.md` | 仅末尾两个"你来写"小节 | ✅ |
| `题面.pdf` | 题面（唯一规格说明） | ❌ 勿改 |
| `src/main/legacy_patrol.py` | Q7 模块（与主体同步发布，修复其缺陷） | Q7 时 ✅ |
| `.pre-commit-config.yaml` | AI 会话归档钩子配置 | ❌ 勿改 |
| `src/tests/`、`tools/`、`.github/`、`conftest.py`、`pytest.ini`、`main.py` | 测试与基础设施 | ❌ 勿改 |

CI 只允许修改 `src/main/**`、`README.md` 与 `.agent-sessions/**`（AI 会话归档）——其余文件改了直接红；autopep8 `--diff` 非空即败。提交方式（push、问卷、commit 粒度）见题面"提交与验收"一节。


## 6. Q7 Debug 修复分析

Q7 的六处缺陷均以 `src/main/legacy_patrol.py` 中各函数 docstring 为契约修复：

1. **路线长度单位错误。** 症状：`total_route_meters([(0, 0), (3, 0), (3, 4)])` 返回 700 而不是 7。根因：函数把 `segment_length_cm` 的厘米结果直接累加到“米”。定位方式：对照 `segment_length_cm` 与 `total_route_meters` 的 docstring，并用可见测试 `test_route_meters` 最小复现。修复：每段先按 1 格 = 1 米 = 100 厘米换算为米再累加。验证：非模拟测试和完整 Q7 测试均通过。
2. **无正样本时基线未处理。** 症状：`calibrate([-1, -2])` 抛出 `TypeError`。根因：`first_positive` 合法返回 `None`，但循环仍执行 `s - baseline`。定位方式：按 docstring 的“没有正样本时漂移为 0”检查空样本和全负样本，最小复现 `[-1, -2]`。修复：基线为 `None` 时直接返回 0。验证：`test_calibrate_no_positive` 通过。
3. **`max_id` 边界被排除。** 症状：事件 `id == max_id` 没有被统计，`summarize_events(events, 2)` 少计一项。根因：条件误写成 `< max_id`，与 docstring 的“id 不超过 max_id”不符。定位方式：用边界事件 `id=2`、`max_id=2` 做最小复现，并对照 `test_summarize_includes_max_id`。修复：条件改为 `<= max_id`。验证：完整 Q7 测试通过。
4. **默认历史被跨调用共享。** 症状：连续调用 `log("a")`、`log("b")` 返回同一历史。根因：可变默认参数 `history=[]` 在函数定义时创建一次。定位方式：查看函数签名和连续两次默认调用，最小复现返回 `["a","b"]`。修复：默认值改为 `None`，每次调用时创建新列表。验证：`test_log_default_history_independent` 通过。
5. **低体力停止条件方向错误。** 症状：`run_legacy_sim(2, 28)` 继续执行到第二轮，而契约要求第一轮结束后体力为 20 时立即停止。根因：条件写成 `stamina > 20` 才停止，边界值 20 未停止。定位方式：按 docstring 的“`<=20` 立即终止”检查边界，最小复现 `(2, 28)`。修复：改为 `stamina <= 20`。验证：`test_sim_stops_at_threshold` 通过。
6. **轮号未递增导致额外消耗提前生效。** 症状：第 4 轮额外消耗从第 0 轮开始生效，轮号和 trace 不符。根因：循环修改了体力但没有执行 `round_ += 1`。定位方式：检查 `trace` 中轮号，用 `run_legacy_sim(10, 100)` 对照第 4 轮体力；修复 A 后暴露该配对缺陷。修复：每轮记录后递增 `round_`。验证：`test_sim_basic_run` 和完整 Q7 测试通过。

验证命令：

- `.\.venv\Scripts\python.exe -m pytest src\tests\test_legacy.py -q -k "not sim_basic_run and not sim_stops_at_threshold"`：5 passed；
- `.\.venv\Scripts\python.exe -m pytest src\tests\test_legacy.py -q`：7 passed。

## Bonus 排行榜

- Bonus 只实现 `bfs_path_length`，使用四邻域 BFS 返回全局最短路步数。
- `tools/run_seeds.py --bonus` 中的 `run_bonus` 在独立验证循环中使用 `bfs_path_length`，不修改学生 `run_patrol`。
- Q6 的学生 `run_patrol` 仍使用 Q4 贪心导航和沿墙脱困，不改成 BFS。
- 本地验证命令：`python tools/run_seeds.py --bonus`。
- 排行榜按成功率、平均步数、平均碰撞排序；批改时仍以固定 200 张地图重跑为准。


## 7. Q1 边界自检记录

Q1 的实现已按题面候选口径处理以下边界：`max_hp <= 0`、负 HP、超过最大 HP、无法转换或非有限数值返回 `0`；电量在 `19/20/59/60` 处分别落入 `LOW/WARNING/WARNING/OK`，非法或非有限电量按 `0` 处理并夹到 `0..100`。报告格式使用题面的逐字段宽度，名称和机型通过 `str(...)` 规范化。针对性探针覆盖负数、超界、零分母、NaN/Infinity、非法电量和格式对齐，Q1/Q5 可见测试均通过。


## 8. Q2 边界自检记录

Q2 已按候选口径区分 JSON 行与传感器行：JSON 的 `armor` 仅接受三个部位，`damage` 必须是严格正整数；传感器段必须是 `F/L/R:正整数`，同一行重复字母按脏行处理；带 `id` 的 JSON 按稳定 JSON 表示去重，不可序列化或不可哈希的 ID 不抛异常。`avg` 使用去重后的有效事件数，`most_hit` 平局按 `front,left,right` 固定顺序。探针覆盖非法 JSON、缺字段、布尔/零/负 damage、重复 ID、不可哈希 ID、重复传感器段、平局和迭代器异常；Q2 可见测试通过。
