#!/usr/bin/env python3
"""子平八字：离线四柱、十神、根气与大运。只生成事实，不自动定喜忌。"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
from lunar_python import Solar
from lunar_python.util import LunarUtil

STEMS = '甲乙丙丁戊己庚辛壬癸'
BRANCHES = '子丑寅卯辰巳午未申酉戌亥'
ELEMENTS = '木火土金水'
SE = dict(zip(STEMS, '木木火火土土金金水水'))
BE = dict(zip(BRANCHES, '水土木木土火火土金金土水'))
CYCLE = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]
HIDDEN = dict(zip(BRANCHES, ['癸', '己癸辛', '甲丙戊', '乙', '戊乙癸', '丙戊庚', '丁己', '己丁乙', '庚壬戊', '辛', '戊辛丁', '壬甲']))
STAGES = '长生 沐浴 冠带 临官 帝旺 衰 病 死 墓 绝 胎 养'.split()
START = dict(zip(STEMS, '亥午寅酉寅酉巳子申卯'))
LABELS = ['年', '月', '日', '时']
UTC8 = timezone(timedelta(hours=8))


class InputError(ValueError):
    pass


def require(test, message):
    if not test:
        raise InputError(message)


def fields(value, allowed, label):
    require(isinstance(value, dict), f'{label} 必须为对象')
    require(not set(value) - set(allowed), f'{label} 含不支持的字段：{set(value) - set(allowed)}')


def shishen(day, other):
    delta = (ELEMENTS.index(SE[other]) - ELEMENTS.index(SE[day])) % 5
    same = STEMS.index(day) % 2 == STEMS.index(other) % 2
    return [('比肩', '劫财'), ('食神', '伤官'), ('偏财', '正财'), ('七杀', '正官'), ('偏印', '正印')][delta][0 if same else 1]


def stage(stem, branch):
    sign = 1 if STEMS.index(stem) % 2 == 0 else -1
    return STAGES[((BRANCHES.index(branch) - BRANCHES.index(START[stem])) * sign) % 12]


def season(element, month):
    return ['旺', '相', '死', '囚', '休'][(ELEMENTS.index(element) - ELEMENTS.index(BE[month])) % 5]


def parse_time(value, aware=True):
    require(isinstance(value, str), '时间必须是 ISO 字符串')
    pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?'
    pattern += r'(Z|[+-]\d{2}:\d{2})' if aware else ''
    require(re.fullmatch(pattern, value) is not None, '出生时间须含明确 UTC 偏移；真太阳时须为无偏移的年月日时分')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise InputError('无效日期或时间') from exc
    require(1901 <= dt.year <= 2099, '本版自动排盘范围为 1901—2099 年')
    return dt


def solar(dt):
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def relations(pillars):
    result = []
    for i, j in combinations(range(4), 2):
        if not pillars[i] or not pillars[j]:
            continue
        a, b = pillars[i], pillars[j]
        kinds = []
        for name, pairs in [('天干五合', ['甲己', '乙庚', '丙辛', '丁壬', '戊癸']),
                            ('地支六合', ['子丑', '寅亥', '卯戌', '辰酉', '巳申', '午未']),
                            ('地支六冲', ['子午', '丑未', '寅申', '卯酉', '辰戌', '巳亥']),
                            ('子卯刑', ['子卯'])]:
            symbols = a[0] + b[0] if name.startswith('天干') else a[1] + b[1]
            if symbols in pairs or symbols[::-1] in pairs:
                kinds.append(name)
        if a[1] == b[1] and a[1] in '辰午酉亥':
            kinds.append('自刑候选')
        if kinds:
            result.append({'positions': [LABELS[i], LABELS[j]], 'pillars': [a, b], 'kinds': kinds, 'adjacent': j - i == 1})
    branches = {p[1] for p in pillars if p}
    for name, groups in [('三合齐支', ['申子辰', '亥卯未', '寅午戌', '巳酉丑']),
                         ('三会齐支', ['寅卯辰', '巳午未', '申酉戌', '亥子丑']),
                         ('三刑齐支候选', ['寅巳申', '丑戌未'])]:
        for group in groups:
            if set(group) <= branches:
                result.append({'kind': name, 'branches': group})
    return result


def build_chart(data):
    fields(data, ['question', 'mode', 'birth', 'pillars', 'source', 'day_boundary', 'gender', 'flow_years'], '输入')
    require(isinstance(data.get('question', ''), str), 'question 必须为文字')
    mode = data.get('mode', 'birth')
    boundary = data.get('day_boundary', 'zi23')
    require(boundary in ('zi23', 'midnight'), 'day_boundary 仅支持 zi23 / midnight')
    gender = data.get('gender')
    require(gender is None or gender in ('male', 'female'), 'gender 使用 male / female，或省略')
    yun = None
    if mode == 'birth':
        require('pillars' not in data and 'source' not in data, '出生模式不接受手动四柱字段')
        birth = data.get('birth')
        fields(birth, ['datetime', 'place', 'basis', 'solar_datetime', 'solar_source'], 'birth')
        require(isinstance(birth.get('place'), str) and birth['place'].strip(), '需要出生地点以核对时间口径')
        raw = parse_time(birth.get('datetime'))
        standard = raw.astimezone(UTC8).replace(tzinfo=None)
        basis = birth.get('basis')
        require(basis in ('standard_utc8', 'provided_true_solar'), '须明确采用 standard_utc8 或 provided_true_solar')
        if basis == 'provided_true_solar':
            require(isinstance(birth.get('solar_source'), str) and birth['solar_source'].strip(), '真太阳时须注明换算来源')
            clock = parse_time(birth.get('solar_datetime'), aware=False)
            require(abs((clock - standard).total_seconds()) <= 86400, '真太阳时与出生瞬间相差超过一天，请核对')
        else:
            require('solar_datetime' not in birth and 'solar_source' not in birth, '标准时间模式不接受真太阳时字段')
            clock = standard
        base_lunar = solar(standard).getLunar()
        base = base_lunar.getEightChar()
        clock_lunar = solar(clock).getLunar()
        clock_eight = clock_lunar.getEightChar()
        clock_eight.setSect(1 if boundary == 'zi23' else 2)
        day = clock_eight.getDay()
        # 五鼠遁严格从所选日干起时；不混用依赖库的晚子时另一日干。
        time_branch = ((clock.hour + 1) // 2) % 12
        time_stem = ((STEMS.index(day[0]) % 5) * 2 + time_branch) % 10
        pillars = [base.getYear(), base.getMonth(), day, STEMS[time_stem] + BRANCHES[time_branch]]
        time_info = {'input_datetime': birth['datetime'], 'place': birth['place'], 'basis': basis,
                     'standard_utc8': standard.isoformat(), 'day_hour_clock': clock.isoformat(),
                     'day_boundary': boundary, 'solar_source': birth.get('solar_source'),
                     'year_month_basis': '出生瞬间与北京时间节气交接比较；立春换年、交节换月',
                     'prev_jie': {'name': base_lunar.getPrevJie().getName(), 'datetime': base_lunar.getPrevJie().getSolar().toYmdHms()},
                     'next_jie': {'name': base_lunar.getNextJie().getName(), 'datetime': base_lunar.getNextJie().getSolar().toYmdHms()}}
        if gender:
            y = base.getYun(1 if gender == 'male' else 0, 2)
            start = y.getStartSolar()
            runs = []
            for d in y.getDaYun(9)[1:]:
                begin = start.nextYear((d.getIndex() - 1) * 10)
                end = start.nextYear(d.getIndex() * 10)
                runs.append({'index': d.getIndex(), 'ganzhi': d.getGanZhi(),
                             'start_inclusive_utc8': begin.toYmdHms(), 'end_exclusive_utc8': end.toYmdHms(),
                             'stem_shishen': shishen(day[0], d.getGanZhi()[0])})
            yun = {'direction': '顺排' if y.isForward() else '逆排', 'sect': 2,
                   'start_offset': {'years': y.getStartYear(), 'months': y.getStartMonth(), 'days': y.getStartDay(), 'hours': y.getStartHour()},
                   'start_utc8': start.toYmdHms(), 'dayun': runs}
    elif mode == 'manual':
        require('birth' not in data and gender is None, '手动四柱不能凭空计算出生时间与起运；请省略 birth/gender')
        pillars = data.get('pillars')
        require(isinstance(pillars, list) and len(pillars) == 4, 'pillars 按年、月、日、时给四项，未知时柱填 null')
        require(all(isinstance(p, str) and p in CYCLE for p in pillars[:3]) and (pillars[3] is None or isinstance(pillars[3], str) and pillars[3] in CYCLE), '四柱须为有效六十甲子；仅时柱可为 null')
        require(isinstance(data.get('source'), str) and data['source'].strip(), '手动盘须注明来源')
        month_index = (BRANCHES.index(pillars[1][1]) - 2) % 12
        require(pillars[1][0] == STEMS[((STEMS.index(pillars[0][0]) % 5) * 2 + 2 + month_index) % 10], '年月柱不符五虎遁，请核对原盘')
        if pillars[3]:
            require(pillars[3][0] == STEMS[((STEMS.index(pillars[2][0]) % 5) * 2 + BRANCHES.index(pillars[3][1])) % 10], '日时柱不符本版五鼠遁；核对原盘换日规则，不要擅改原盘')
        time_info = {'source': data['source'], 'day_boundary': '沿用原盘；仅检查干支与遁法，不核验出生日期'}
    else:
        raise InputError('mode 仅支持 birth / manual')
    day_stem = pillars[2][0]
    rows = []
    for i, p in enumerate(pillars):
        if p is None:
            rows.append({'position': LABELS[i], 'ganzhi': None})
            continue
        hidden = [{'stem': g, 'element': SE[g], 'shishen': shishen(day_stem, g)} for g in HIDDEN[p[1]]]
        roots = [{'position': LABELS[j], 'branch': q[1], 'hidden_stem': g, 'same_stem': g == p[0], 'main_qi': g == HIDDEN[q[1]][0]}
                 for j, q in enumerate(pillars) if q for g in HIDDEN[q[1]] if SE[g] == SE[p[0]]]
        rows.append({'position': LABELS[i], 'ganzhi': p, 'stem_element': SE[p[0]], 'branch_element': BE[p[1]],
                     'stem_shishen': '日主' if i == 2 else shishen(day_stem, p[0]), 'hidden': hidden,
                     'day_stem_stage': stage(day_stem, p[1]), 'own_stem_stage': stage(p[0], p[1]),
                     'season_state': season(SE[p[0]], pillars[1][1]), 'roots': roots,
                     'xunkong': LunarUtil.getXunKong(p)})
    counts = {e: sum((SE[p[0]] == e) + (BE[p[1]] == e) for p in pillars if p) for e in ELEMENTS}
    candidates = [{'hidden_stem': g, 'shishen': shishen(day_stem, g),
                   'visible_positions': [LABELS[i] for i, p in enumerate(pillars) if p and p[0] == g]}
                  for g in HIDDEN[pillars[1][1]]]
    years = data.get('flow_years', [])
    require(isinstance(years, list) and len(years) <= 30 and all(type(y) is int and 1901 <= y <= 2098 for y in years), 'flow_years 最多 30 个 1901—2098 年整数')
    flows = []
    for year in years:
        begin = Solar.fromYmdHms(year, 6, 1, 12, 0, 0).getLunar().getJieQiTable()['立春']
        end = Solar.fromYmdHms(year + 1, 6, 1, 12, 0, 0).getLunar().getJieQiTable()['立春']
        gz = CYCLE[(year - 4) % 60]
        flows.append({'year_label': year, 'ganzhi': gz, 'stem_shishen': shishen(day_stem, gz[0]),
                      'start_inclusive_utc8': begin.toYmdHms(), 'end_exclusive_utc8': end.toYmdHms()})
    chart = {'question': data.get('question', ''), 'mode': mode, 'time': time_info,
             'day_master': day_stem, 'pillars': rows, 'visible_element_counts': counts,
             'month_hidden_candidates': candidates, 'relations': relations(pillars),
             'yun': yun, 'flow_years': flows,
             'notes': ['关系条目只表示符号出现，不自动判合化、刑伤、身强弱、格局或喜忌。',
                       '五行计数仅数已知明干与支本五行，不计藏干权重；缺项不等于需要补。',
                       '未提供传统顺逆排运所用性别，或采用手动盘时，不计算起运。']}
    chart['chart_markdown'] = markdown(chart)
    return chart


def markdown(chart):
    t = chart['time']
    lines = ['# 八字排盘', '', f"日主：{chart['day_master']}；换日：{t['day_boundary']}。"]
    if chart['mode'] == 'birth':
        lines += [f"原始时间：{t['input_datetime']}；地点：{t['place']}。", f"时间口径：{t['basis']}；日时计算钟面：{t['day_hour_clock']}。", f"年/月柱与起运使用 UTC+08:00：{t['standard_utc8']}。"]
    else:
        lines += [f"来源：{t['source']}。"]
    lines += ['', '| 柱 | 干支 | 天干十神 | 藏干（十神） | 日主十二长生 | 天干得令状态 |', '|---|---|---|---|---|---|']
    for p in chart['pillars']:
        if p['ganzhi'] is None:
            lines.append('| 时 | 未知 | — | — | — | — |')
            continue
        h = '、'.join(f"{x['stem']}（{x['shishen']}）" for x in p['hidden'])
        lines.append(f"| {p['position']} | {p['ganzhi']} | {p['stem_shishen']} | {h} | {p['day_stem_stage']} | {p['season_state']} |")
    if chart['yun']:
        y = chart['yun']
        lines += ['', f"大运：{y['direction']}；起运 UTC+08:00：{y['start_utc8']}。起运前不列为第一步大运。", '', '| 大运 | 起始（含）UTC+08:00 | 结束（不含）UTC+08:00 |', '|---|---|---|']
        lines += [f"| {d['ganzhi']} | {d['start_inclusive_utc8']} | {d['end_exclusive_utc8']} |" for d in y['dayun']]
    if chart['flow_years']:
        lines += ['', '| 流年 | 干支 | 起始立春（含）UTC+08:00 | 结束立春（不含）UTC+08:00 |', '|---|---|---|---|']
        lines += [f"| {f['year_label']} | {f['ganzhi']} | {f['start_inclusive_utc8']} | {f['end_exclusive_utc8']} |" for f in chart['flow_years']]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir')
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
        chart = build_chart(data)
        result = json.dumps(chart, ensure_ascii=False, indent=2)
        if args.output_dir:
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=False)
            (out / 'input.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            (out / 'chart.json').write_text(result + '\n', encoding='utf-8')
            (out / 'chart.md').write_text(chart['chart_markdown'], encoding='utf-8')
        print(result)
    except (InputError, ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
