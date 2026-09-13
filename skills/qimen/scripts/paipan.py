#!/usr/bin/env python3
"""转盘时家奇门：拆补定局或手动定局。仅生成盘面事实，不自动占断。"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
CYCLE = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]
YI = "戊己庚辛壬癸丁丙乙"
RING = [1, 8, 3, 4, 9, 2, 7, 6]
NAMES = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
ELEMENTS = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
DIRECTIONS = {1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中央", 6: "西北", 7: "西", 8: "东北", 9: "南"}
PALACE_BRANCHES = {1: "子", 2: "未申", 3: "卯", 4: "辰巳", 5: "", 6: "戌亥", 7: "酉", 8: "丑寅", 9: "午"}
STARS = dict(zip(RING, ["天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"]))
DOORS = dict(zip(RING, ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]))
GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
STEM_ELEMENTS = dict(zip(STEMS, "木木火火土土金金水水"))
BRANCH_ELEMENTS = dict(zip(BRANCHES, "水土木木土火火土金金土水"))
GENERATES = dict(zip("木火土金水", "火土金水木"))
CONTROLS = dict(zip("木土水火金", "土水火金木"))
STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
LONG_LIFE = dict(zip(STEMS, "亥午寅酉寅酉巳子申卯"))
PUNISH = {"戊": 3, "己": 2, "庚": 8, "辛": 9, "壬": 4, "癸": 4}
# 按 Q02 起数规律展开，并以 E01《奇门旨归》起例表核对。
TERM_NAMES = "冬至 小寒 大寒 立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪".split()
TERM_NUMBERS = "174 285 396 852 963 174 396 417 528 417 528 639 936 825 714 258 147 936 714 693 582 693 582 471".split()
TERMS = {name: {"dun": "yang" if i < 12 else "yin", "ju": list(map(int, TERM_NUMBERS[i]))} for i, name in enumerate(TERM_NAMES)}


class InputError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise InputError(message)


def fields(obj, allowed, label):
    require(isinstance(obj, dict), f"{label} 必须是对象。")
    require(not (set(obj) - set(allowed)), f"{label} 含不支持的字段：{sorted(set(obj) - set(allowed))}")


def ganzhi_index(value):
    require(isinstance(value, str) and value in CYCLE, f"无效的六十甲子：{value!r}")
    return CYCLE.index(value)


def alias(ganzhi):
    idx = ganzhi_index(ganzhi)
    return YI[idx // 10] if ganzhi[0] == "甲" else ganzhi[0]


def relation(a, b):
    """a 对 b 的关系，a/b 是五行。"""
    if a == b:
        return "比和"
    if GENERATES[a] == b:
        return "生"
    if GENERATES[b] == a:
        return "被生"
    if CONTROLS[a] == b:
        return "克"
    return "被克"


def season_state(element, month_element, star=False):
    r = relation(element, month_element)
    return ({"比和": "相", "生": "旺", "被生": "废", "克": "休", "被克": "囚"} if star else
            {"比和": "旺", "生": "休", "被生": "相", "克": "囚", "被克": "死"})[r]


def stage(stem, branch):
    sign = 1 if STEMS.index(stem) % 2 == 0 else -1
    return STAGES[((BRANCHES.index(branch) - BRANCHES.index(LONG_LIFE[stem])) * sign) % 12]


def yuan_for(day):
    idx = ganzhi_index(day)
    head = CYCLE[idx - idx % 5]
    yuan = 0 if head[1] in "子午卯酉" else 1 if head[1] in "寅申巳亥" else 2
    return head, yuan


def calendar(spec):
    require(isinstance(spec, dict), "time 必须是对象，提供原起局时间或手动干支。")
    kind = spec.get("kind")
    require(kind in ("civil", "now", "manual"), "time.kind 仅支持 civil、now、manual。")
    if kind == "manual":
        fields(spec, ["kind", "year_ganzhi", "month_ganzhi", "day_ganzhi", "hour_ganzhi", "solar_term", "source"], "time")
        require(isinstance(spec.get("source"), str) and spec["source"].strip(), "手动干支须注明来源。")
        for key in ("day_ganzhi", "hour_ganzhi"):
            ganzhi_index(spec.get(key))
        for key in ("year_ganzhi", "month_ganzhi"):
            if key in spec:
                ganzhi_index(spec[key])
        if "solar_term" in spec:
            require(spec["solar_term"] in TERMS, "solar_term 必须是二十四节气名称。")
        day, hour = spec["day_ganzhi"], spec["hour_ganzhi"]
        hi = BRANCHES.index(hour[1])
        expected = STEMS[(STEMS.index(day[0]) % 5 * 2 + hi) % 10]
        require(hour[0] == expected, "日干与时干不符合五鼠遁；请核对来源及晚子时换日约定。")
        if spec.get("month_ganzhi") and spec.get("solar_term"):
            month = "子丑丑寅寅卯卯辰辰巳巳午午未未申申酉酉戌戌亥亥子"[TERM_NAMES.index(spec["solar_term"])]
            require(spec["month_ganzhi"][1] == month, "月支与节气不一致，请核对原盘。")
        return dict(spec, status="user_supplied", notes=["按注明来源录入；未由公历复核。"])
    allowed = ["kind", "timezone", "day_boundary"] + (["at"] if kind == "civil" else [])
    fields(spec, allowed, "time")
    zone_name = spec.get("timezone", "Asia/Shanghai")
    require(isinstance(zone_name, str), "timezone 必须是 IANA 时区名称。")
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise InputError("无法识别时区，请使用 Asia/Shanghai 等 IANA 名称。") from e
    boundary = spec.get("day_boundary", "midnight")
    require(boundary in ("midnight", "zi23"), "day_boundary 仅支持 midnight 或 zi23。")
    if kind == "now":
        local = datetime.now(zone).replace(microsecond=0)
    else:
        raw = spec.get("at")
        require(isinstance(raw, str) and re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", raw), "请提供含时分的公历时间；不能只有日期。")
        try:
            local = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as e:
            raise InputError("公历日期或时间格式无效。") from e
        if local.tzinfo is None:
            first, second = local.replace(tzinfo=zone, fold=0), local.replace(tzinfo=zone, fold=1)
            require(first.utcoffset() == second.utcoffset(), "当地时间处于夏令时重复或跳过区间，请补充 UTC 偏移。")
            require(first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == local, "当地时间不存在，请核对夏令时。")
            local = first
        else:
            local = local.astimezone(zone)
    require(1900 <= local.year <= 2100, "自动历法范围为 1900—2100；其他年代请用已核验的手动干支。")
    try:
        from lunar_python import Solar
    except ImportError as e:
        raise InputError("缺少 vendor/lunar_python 1.4.8，请恢复依赖。") from e

    def lunar_at(dt):
        return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar()

    local_lunar = lunar_at(local)
    # 库的节气以 UTC+8 表示；海外墙上时间只用来算本地日、时柱。
    bj = local.astimezone(timezone(timedelta(hours=8)))
    term_lunar = lunar_at(bj)
    term = term_lunar.getPrevJieQi(False)
    day = local_lunar.getDayInGanZhiExact2() if boundary == "midnight" else local_lunar.getDayInGanZhiExact()
    hi = ((local.hour + 1) // 2) % 12
    hour = STEMS[(STEMS.index(day[0]) % 5 * 2 + hi) % 10] + BRANCHES[hi]
    return {"kind": kind, "status": "calculated", "at": local.isoformat(timespec="seconds"),
            "timezone": zone_name, "day_boundary": boundary,
            "year_ganzhi": term_lunar.getYearInGanZhiExact(), "month_ganzhi": term_lunar.getMonthInGanZhiExact(),
            "day_ganzhi": day, "hour_ganzhi": hour, "solar_term": term.getName(),
            "solar_term_start_utc8": term.getSolar().toYmdHms() + "+08:00", "engine": "lunar_python 1.4.8",
            "notes": ["按节气交接时刻换年、月及节气；日时按所选当地民用时间与换日约定。", "未作真太阳时校正；时干按所选日干作五鼠遁。"]}


def host(p):
    return 2 if p == 5 else p


def build(data):
    fields(data, ["question", "time", "method", "dun", "ju"], "input")
    require(isinstance(data.get("question", ""), str), "question 必须是文字。")
    cal = calendar(data.get("time"))
    method = data.get("method", "chaibu")
    require(method in ("chaibu", "manual"), "本程序仅支持拆补 chaibu 或手动定局 manual；不能冒充置闰、茅山或飞盘。")
    futo, yuan = yuan_for(cal["day_ganzhi"])
    if method == "chaibu":
        require("dun" not in data and "ju" not in data, "拆补自动定局不能同时手填 dun/ju；请明确选择 manual。")
        require(cal.get("solar_term") in TERMS, "拆补定局需当前节气；手动时间请提供 solar_term 或改用手动定局。")
        t = TERMS[cal["solar_term"]]
        dun, ju = t["dun"], t["ju"][yuan]
    else:
        dun, ju = data.get("dun"), data.get("ju")
        require(dun in ("yang", "yin"), "dun 仅支持 yang 或 yin。")
        require(type(ju) is int and 1 <= ju <= 9, "ju 必须是 1—9 的整数。")
    sign = 1 if dun == "yang" else -1
    earth = {(ju - 1 + sign * i) % 9 + 1: s for i, s in enumerate(YI)}
    locations = {s: p for p, s in earth.items()}
    hidx = ganzhi_index(cal["hour_ganzhi"])
    xun = CYCLE[hidx - hidx % 10]
    xun_yi = YI[hidx // 10]
    origin = locations[xun_yi]
    star_origin = host(origin)
    hour_stem = alias(cal["hour_ganzhi"])
    target = host(locations[hour_stem])
    star_shift = (RING.index(target) - RING.index(star_origin)) % 8
    # 值使按九宫飞数，从原始宫（含五宫）起算，到终点后才寄宫。
    door_raw = (origin - 1 + sign * (hidx % 10)) % 9 + 1
    door_target = host(door_raw)
    door_shift = (RING.index(door_target) - RING.index(star_origin)) % 8
    void = [BRANCHES[(BRANCHES.index(xun[1]) - 2) % 12], BRANCHES[(BRANCHES.index(xun[1]) - 1) % 12]]
    hb = cal["hour_ganzhi"][1]
    horse = "申" if hb in "寅午戌" else "巳" if hb in "亥卯未" else "亥" if hb in "巳酉丑" else "寅"
    month = BRANCH_ELEMENTS[cal["month_ganzhi"][1]] if cal.get("month_ganzhi") else None
    palaces = {p: {"number": p, "name": NAMES[p], "direction": DIRECTIONS[p], "element": ELEMENTS[p],
                   "branches": list(PALACE_BRANCHES[p]), "earth_stems": [earth[p]] + ([earth[5]] if p == 2 else []),
                   "earth_hosted_stem": earth[5] if p == 2 else None,
                   "heaven_stems": [], "heaven_hosted_stem": None, "stars": [], "door": None, "god": None,
                   "void_branches": [b for b in PALACE_BRANCHES[p] if b in void], "horse": horse in PALACE_BRANCHES[p],
                   "inner": (p in ([1, 8, 3, 4] if dun == "yang" else [9, 2, 7, 6])) if p != 5 else None,
                   "facts": []} for p in range(1, 10)}
    for i, p in enumerate(RING):
        dest = RING[(i + star_shift) % 8]
        cell = palaces[dest]
        cell["stars"] = [STARS[p]] + (["天禽"] if p == 2 else [])
        cell["heaven_stems"] = [earth[p]] + ([earth[5]] if p == 2 else [])
        cell["heaven_hosted_stem"] = earth[5] if p == 2 else None
        palaces[RING[(i + door_shift) % 8]]["door"] = DOORS[p]
        palaces[RING[(RING.index(target) + sign * i) % 8]]["god"] = GODS[i]
    for p in RING:
        cell = palaces[p]
        door = cell["door"]
        de = ELEMENTS[next(o for o in RING if DOORS[o] == door)]
        dr = relation(de, ELEMENTS[p])
        cell["door_palace_relation"] = {"比和": "门宫比和", "生": "门生宫", "被生": "宫生门", "克": "门克宫（门迫／门破）", "被克": "宫克门（门受制）"}[dr]
        cell["stem_stages"] = {s: {b: stage(s, b) for b in PALACE_BRANCHES[p]} for s in dict.fromkeys(cell["heaven_stems"] + cell["earth_stems"])}
        cell["stem_pairs"] = [{"heaven": a, "earth": b, "heaven_hosted": a == cell["heaven_hosted_stem"],
                               "earth_hosted": b == cell["earth_hosted_stem"], "element_relation": relation(STEM_ELEMENTS[a], STEM_ELEMENTS[b])}
                              for a in cell["heaven_stems"] for b in cell["earth_stems"]]
        cell["facts"] = [f"天盘{s}六仪击刑" for s in cell["heaven_stems"] if PUNISH.get(s) == p]
        for s in cell["heaven_stems"]:
            for b in PALACE_BRANCHES[p]:
                if stage(s, b) == "墓":
                    cell["facts"].append(f"天盘{s}于{b}为天干墓")
        if month:
            cell["palace_season"] = season_state(ELEMENTS[p], month)
            cell["door_season"] = season_state(de, month)
            cell["star_season"] = {s: season_state("土" if s == "天禽" else ELEMENTS[next(o for o in RING if STARS[o] == s)], month, True) for s in cell["stars"]}
    roles = {}
    for label, key in (("日干（求测者）", "day_ganzhi"), ("时干（事情）", "hour_ganzhi")):
        s = alias(cal[key])
        roles[label] = {"ganzhi": cal[key], "mapped_stem": s, "heaven_palace": next(p for p in RING if s in palaces[p]["heaven_stems"])}
    rp, hp = [r["heaven_palace"] for r in roles.values()]
    return {"schema_version": 1, "question": data.get("question", ""), "calendar": cal,
            "conventions": {"pan": "转盘时家奇门", "method": method, "center": "五寄坤二；天禽随天芮；值使自原始宫飞数", "star_season": "我生为旺，同我为相，生我为废，我克为休，克我为囚", "stem_stages": "阳顺阴逆；戊随丙、己随丁", "gods": "天盘八神"},
            "dun": dun, "ju": ju, "day_futou": futo, "day_yuan": ["上元", "中元", "下元"][yuan],
            "xun_head": xun, "xun_yi": xun_yi, "xun_original_palace": origin,
            "zhifu_star": "天禽" if origin == 5 else STARS[origin], "zhifu_carrier_star": STARS[star_origin], "zhifu_palace": target,
            "zhishi_door": DOORS[star_origin], "zhishi_raw_palace": door_raw, "zhishi_palace": door_target,
            "hour_void": void, "hour_horse": horse,
            "global_facts": {"星伏吟": star_shift == 0, "门伏吟": door_shift == 0, "星反吟": star_shift == 4, "门反吟": door_shift == 4,
                             "五不遇时": CONTROLS[STEM_ELEMENTS[cal["hour_ganzhi"][0]]] == STEM_ELEMENTS[cal["day_ganzhi"][0]] and STEMS.index(cal["hour_ganzhi"][0]) % 2 == STEMS.index(cal["day_ganzhi"][0]) % 2},
            "roles": roles, "day_to_hour_palace_relation": {"from": rp, "to": hp, "relation": relation(ELEMENTS[rp], ELEMENTS[hp]), "opposite": rp != hp and rp + hp == 10},
            "palaces": [palaces[p] for p in range(1, 10)],
            "notes": ["格局标记是盘面事实，不是自动吉凶结论。", "五宫保留地盘原干；二宫另列其寄干。天盘寄干随天禽、天芮一起转。", "转录未给出的完整克应表、暗干、地盘八神不生成。"]}


def markdown(chart):
    cal = chart["calendar"]
    method_label = "拆补" if chart['conventions']['method'] == 'chaibu' else "手动定局"
    boundary_label = {'midnight': '零点换日', 'zi23': '23点换日'}.get(cal.get('day_boundary'), '沿用输入干支')
    carrier_label = '（随天芮）' if chart['zhifu_star'] == '天禽' else ''
    lines = ["# 奇门盘面", "", f"占问：{chart['question'] or '仅排盘'}", "",
             f"时间：{cal.get('at', '手动干支')}；来源：{cal.get('source', cal.get('engine', ''))}",
             f"四柱：{' '.join(cal.get(k, '未提供') for k in ('year_ganzhi', 'month_ganzhi', 'day_ganzhi', 'hour_ganzhi'))}",
             f"约定：{cal.get('timezone', '来源未注明时区')}；{boundary_label}；未校正真太阳时",
             f"转盘／{method_label}／{'阳' if chart['dun'] == 'yang' else '阴'}遁{chart['ju']}局；五寄坤二",
             f"节气：{cal.get('solar_term', '未提供')}；日符头：{chart['day_futou']} {chart['day_yuan']}；时旬首：{chart['xun_head']}{chart['xun_yi']}",
             f"值符星：{chart['zhifu_star']}{carrier_label}落{chart['zhifu_palace']}宫；值使：{chart['zhishi_door']}落{chart['zhishi_palace']}宫",
             f"时旬空：{''.join(chart['hour_void'])}；时马：{chart['hour_horse']}", "", "上南下北、左东右西；格内列星、门、神、天盘干／地盘干。带 * 为寄干。", ""]
    cells = {}
    for c in chart["palaces"]:
        p = c["number"]
        def stems(key, hosted):
            return ' '.join(s + ('*' if s == c[hosted] else '') for s in c[key]) or '—'
        if p == 5:
            cells[p] = f"中五（土）<br>地盘{c['earth_stems'][0]}<br>寄坤二"
        else:
            cells[p] = f"{c['name']}{p}（{c['direction']}）<br>{'、'.join(c['stars'])} · {c['door']} · {c['god']}<br>天 {stems('heaven_stems', 'heaven_hosted_stem')}／地 {stems('earth_stems', 'earth_hosted_stem')}"
            if c['void_branches'] or c['horse']:
                cells[p] += '<br>' + ('空' + ''.join(c['void_branches']) if c['void_branches'] else '') + (' 马' if c['horse'] else '')
    lines += ['| 东南 | 南 | 西南 |', '|---|---|---|']
    for row in ((4, 9, 2), (3, 5, 7), (8, 1, 6)):
        lines.append('| ' + ' | '.join(cells[p] for p in row) + ' |')
    lines += ['', '| 宫 | 门宫关系 | 时空／马 | 条件标记 |', '|---|---|---|---|']
    for c in chart['palaces']:
        if c['number'] == 5:
            continue
        flags = c['facts'][:]
        if c.get('palace_season'):
            flags.append('宫' + c['palace_season'] + '、门' + c['door_season'])
            flags.extend(s + v for s, v in c['star_season'].items())
        lines.append(f"| {c['name']}{c['number']} | {c['door_palace_relation']} | {''.join(c['void_branches']) or '—'}{'／马' if c['horse'] else ''} | {'；'.join(flags) or '—'} |")
    lines += ['', '全盘标记：' + ('、'.join(k for k, v in chart['global_facts'].items() if v) or '无所列全盘标记'), '', '此文件是排盘底稿；完整占断须结合问题、用神和参考规则另写。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        chart = build(data)
        chart['chart_markdown'] = markdown(chart)
        payload = json.dumps(chart, ensure_ascii=False, indent=2)
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=False)
            (args.output_dir / 'input.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            (args.output_dir / 'chart.json').write_text(payload + '\n', encoding='utf-8')
            (args.output_dir / 'chart.md').write_text(chart['chart_markdown'], encoding='utf-8')
        print(payload)
        return 0
    except (InputError, OSError, ValueError, TypeError) as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
