# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    try:
        current = float(hp)
        maximum = float(max_hp)
    except (TypeError, ValueError):
        return 0
    if maximum <= 0:
        return 0
    return max(0, min(100, round(current / maximum * 100)))


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    try:
        battery_value = int(battery)
    except (TypeError, ValueError):
        battery_value = 0
    battery_value = max(0, min(100, battery_value))
    if battery_value >= 60:
        tier = "OK"
    elif battery_value >= 20:
        tier = "WARNING"
    else:
        tier = "LOW"
    return "{:<10}|{:^10}|HP {:>3}%|BAT {:>3}%|{}".format(
        str(name), str(robot_type), hp_ratio(hp, max_hp), battery_value, tier)


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """TODO(Q2)：解析混合格式伤害日志，返回固定契约的统计 dict；
    行格式、去重与统计口径见题面 Q2 规范。"""
    armor_totals = {"front": 0, "left": 0, "right": 0}
    seen_ids = set()
    counted_events = 0
    armor_names = {"F": "front", "L": "left", "R": "right"}
    try:
        source_lines = iter(lines)
    except TypeError:
        source_lines = iter(())

    for raw_line in source_lines:
        try:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("{"):
                event = json.loads(line)
                if not isinstance(event, dict):
                    continue
                armor = event.get("armor")
                if armor not in armor_totals:
                    continue
                damage = event.get("damage")
                if type(damage) is not int or damage <= 0:
                    continue
                if "id" in event:
                    try:
                        id_key = json.dumps(
                            event["id"], sort_keys=True,
                            separators=(",", ":"), ensure_ascii=False,
                            allow_nan=False)
                    except (TypeError, ValueError):
                        continue
                    if id_key in seen_ids:
                        continue
                    seen_ids.add(id_key)
            else:
                segments = line.split(",")
                event_damage = {}
                for segment in segments:
                    if ":" not in segment:
                        raise ValueError("invalid sensor segment")
                    letter, raw_value = segment.split(":", 1)
                    if letter not in armor_names or letter in event_damage:
                        raise ValueError("invalid sensor letter")
                    if not raw_value.isdigit():
                        raise ValueError("invalid sensor damage")
                    value = int(raw_value)
                    if value <= 0:
                        raise ValueError("invalid sensor damage")
                    event_damage[letter] = value
                if not event_damage:
                    raise ValueError("empty sensor event")
                armor = None
                damage = sum(event_damage.values())
                for letter, value in event_damage.items():
                    event_armor = armor_names[letter]
                    armor_totals[event_armor] += value
                counted_events += 1
                continue

            armor_totals[armor] += damage
            counted_events += 1
        except Exception:
            continue

    total = sum(armor_totals.values())
    most_hit = None
    if total:
        most_hit = max(
            ("front", "left", "right"),
            key=lambda item: armor_totals[item])
    avg = round(total / counted_events, 2) if counted_events else 0.0
    return {
        "total": total,
        "by_armor": armor_totals,
        "most_hit": most_hit,
        "avg": avg,
    }


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """TODO(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("current_pos 需要长度为 2 的 tuple/list")
        self._pos = self._clamp_cell(value)

    def move_forward(self):
        """TODO(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        if self._fuel <= 0:
            return self._pos
        dx, dy = self._facing.delta
        next_pos = (self._pos[0] + dx, self._pos[1] + dy)
        self._fuel -= 1
        if self.is_blocked(*next_pos):
            self._collision_count += 1
        else:
            self._pos = next_pos
        return self._pos

    def turn_left(self):
        """TODO(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        self._facing = {
            Facing.UP: Facing.LEFT,
            Facing.LEFT: Facing.DOWN,
            Facing.DOWN: Facing.RIGHT,
            Facing.RIGHT: Facing.UP,
        }[self._facing]
        return self._facing

    def turn_right(self):
        """TODO(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        self._facing = {
            Facing.UP: Facing.RIGHT,
            Facing.RIGHT: Facing.DOWN,
            Facing.DOWN: Facing.LEFT,
            Facing.LEFT: Facing.UP,
        }[self._facing]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """TODO(Q4)：返回下一步应朝向的 Facing；
    候选判定、优先级与回退规则见题面 Q4 规范。"""
    pos_x, pos_y = pos
    target_x, target_y = target
    current_distance = abs(pos_x - target_x) + abs(pos_y - target_y)
    axis_gap = abs(target_x - pos_x) - abs(target_y - pos_y)
    directions = (Facing.RIGHT, Facing.LEFT, Facing.UP, Facing.DOWN)
    candidates = []
    for direction in directions:
        dx, dy = direction.delta
        next_pos = (pos_x + dx, pos_y + dy)
        if next_pos in obstacles:
            continue
        next_distance = (
            abs(next_pos[0] - target_x) + abs(next_pos[1] - target_y))
        if next_distance < current_distance:
            candidates.append(direction)
    if not candidates:
        return current_facing
    if axis_gap > 0:
        preferred = {Facing.RIGHT, Facing.LEFT}
    elif axis_gap < 0:
        preferred = {Facing.UP, Facing.DOWN}
    else:
        preferred = set(directions)
    for direction in directions:
        if direction in preferred and direction in candidates:
            return direction
    return candidates[0]


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def _decide_legacy(sensor, state, hp, heat):
    """TODO(Q5)：纯函数决策，返回 (action: str, new_state: SentryState)；
    sensor 字段契约、R1-R7 规则表与非法输入处理见题面 Q5 规范。"""
    raise NotImplementedError("Q5 decide：题面 Q5·决策规则表 R1-R7")


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    """TODO(Q6)：sense → decide → act 主循环；
    循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    steps = 0
    visited = {grid.current_pos}
    state = SentryState.PATROL
    enemy_frames = []
    wall = False
    hand = "L"
    wall_steps = 0
    wall_limit = grid.width + grid.height
    wall_entry_distance = 0
    left_of = {
        Facing.UP: Facing.LEFT,
        Facing.LEFT: Facing.DOWN,
        Facing.DOWN: Facing.RIGHT,
        Facing.RIGHT: Facing.UP,
    }
    right_of = {value: key for key, value in left_of.items()}

    def manhattan(position):
        return (
            abs(position[0] - grid.enemy_pos[0])
            + abs(position[1] - grid.enemy_pos[1])
        )

    def has_candidate():
        position = grid.current_pos
        distance = manhattan(position)
        return any(
            not grid.is_blocked(position[0] + direction.delta[0],
                                position[1] + direction.delta[1])
            and manhattan((
                position[0] + direction.delta[0],
                position[1] + direction.delta[1],
            )) < distance
            for direction in (Facing.UP, Facing.DOWN, Facing.LEFT, Facing.RIGHT)
        )

    while steps < max_steps and grid.fuel > 0 and not grid.found_enemy:
        position = grid.current_pos
        enemy_frames.append(grid.current_pos == grid.enemy_pos)
        if len(enemy_frames) > 6:
            enemy_frames.pop(0)
        sensor = {
            "enemy_frames": tuple(enemy_frames),
            "enemy_dist": (
                manhattan(position)
                if grid.current_pos != grid.enemy_pos
                else 0
            ),
            "robot_type": "INFANTRY",
            "max_hp": 100,
        }
        _, state = decide(sensor, state, 100, 0)

        if not wall and not has_candidate():
            wall = True
            hand = "L"
            wall_steps = 0
            wall_entry_distance = manhattan(position)

        if wall:
            side = left_of[grid.facing] if hand == "L" else right_of[grid.facing]
            opposite = (
                right_of[grid.facing]
                if hand == "L"
                else left_of[grid.facing]
            )

            def cell(direction):
                return (
                    grid.current_pos[0] + direction.delta[0],
                    grid.current_pos[1] + direction.delta[1],
                )

            if not grid.is_blocked(*cell(side)):
                if hand == "L":
                    grid.turn_left()
                else:
                    grid.turn_right()
            elif grid.is_blocked(*cell(grid.facing)):
                if not grid.is_blocked(*cell(opposite)):
                    if hand == "L":
                        grid.turn_right()
                    else:
                        grid.turn_left()
                else:
                    grid.turn_right()
                    grid.turn_right()
        else:
            direction = next_step_toward(
                grid.current_pos,
                grid.enemy_pos,
                grid.obstacles,
                grid.facing,
            )
            order = (Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT)
            difference = (
                order.index(direction) - order.index(grid.facing)
            ) % 4
            if difference == 3:
                grid.turn_left()
            else:
                for _ in range(difference):
                    grid.turn_right()

        before = grid.current_pos
        grid.move_forward()
        steps += 1
        if grid.current_pos != before:
            visited.add(grid.current_pos)

        if wall:
            wall_steps += 1
            if wall_steps > wall_limit and hand == "L":
                hand = "R"
                wall_steps = 0
            elif wall_steps > 2 * wall_limit:
                wall = False
            elif has_candidate() and manhattan(grid.current_pos) <= wall_entry_distance:
                wall = False

    found_enemy = grid.found_enemy
    return {
        "steps": steps,
        "collisions": grid.collision_count,
        "visited_count": len(visited),
        "found_enemy": found_enemy,
        "success": found_enemy,
    }


def decide(sensor, state, hp, heat):
    required_fields = {"enemy_frames", "enemy_dist", "robot_type", "max_hp"}
    if not isinstance(sensor, dict) or not required_fields.issubset(sensor):
        raise ValueError("sensor fields missing")
    if not isinstance(state, SentryState):
        raise ValueError("invalid state")

    raw_frames = sensor["enemy_frames"]
    if isinstance(raw_frames, (tuple, list)):
        enemy_frames = tuple(bool(value) for value in raw_frames)
    else:
        enemy_frames = (bool(raw_frames),)
    if not enemy_frames or len(enemy_frames) > 6:
        raise ValueError("invalid enemy_frames")

    raw_distance = sensor["enemy_dist"]
    if type(raw_distance) is int and raw_distance >= 0:
        enemy_dist = raw_distance
    else:
        enemy_dist = None

    raw_robot_type = sensor["robot_type"]
    if isinstance(raw_robot_type, str) and raw_robot_type.upper() == "HERO":
        robot_type = "HERO"
    else:
        robot_type = "INFANTRY"

    raw_max_hp = sensor["max_hp"]
    if type(raw_max_hp) is int and raw_max_hp > 0:
        max_hp = raw_max_hp
    else:
        max_hp = 1

    if isinstance(hp, (int, float)) and not isinstance(hp, bool):
        normalized_hp = hp
    else:
        normalized_hp = 0
    if isinstance(heat, (int, float)) and not isinstance(heat, bool):
        normalized_heat = int(heat)
    else:
        normalized_heat = 0

    hp_pct = hp_ratio(normalized_hp, max_hp)
    visible = enemy_frames[-1]
    sustained_loss = (
        len(enemy_frames) >= 2
        and not enemy_frames[-1]
        and not enemy_frames[-2]
    )
    sustained_sight = (
        len(enemy_frames) >= 2
        and enemy_frames[-1]
        and enemy_frames[-2]
    )

    if hp_pct <= 30:
        return "RETREAT", SentryState.RETREAT
    if state is SentryState.RETREAT:
        if hp_pct > 30:
            return "RETURN", SentryState.RETURN
        return "RETREAT", SentryState.RETREAT
    if state is SentryState.RETURN:
        return "MOVE_BASE", SentryState.PATROL
    if state is SentryState.ENGAGE:
        if visible:
            if enemy_dist is not None and enemy_dist <= 3:
                return "SHOOT", SentryState.ENGAGE
            if robot_type == "HERO":
                return "MOVE_RIGHT", SentryState.ENGAGE
            return "MOVE_LEFT", SentryState.ENGAGE
        if sustained_loss:
            return "SCAN", SentryState.SUSPECT
        return "HOLD_FIRE", SentryState.ENGAGE
    if state in (SentryState.PATROL, SentryState.SUSPECT):
        if visible:
            if sustained_sight:
                if enemy_dist is not None and enemy_dist <= 3:
                    return "SHOOT", SentryState.ENGAGE
                if robot_type == "HERO":
                    return "MOVE_RIGHT", SentryState.ENGAGE
                return "MOVE_LEFT", SentryState.ENGAGE
            return "SCAN", SentryState.SUSPECT
        if state is SentryState.PATROL:
            return "PATROL_MOVE", SentryState.PATROL
        return "SCAN", SentryState.SUSPECT
    return "SCAN", SentryState.SUSPECT


def report_to_json(stats):
    """TODO(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    return json.dumps(
        stats,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    raise NotImplementedError("Bonus bfs_path_length")


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
