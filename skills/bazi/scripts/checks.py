#!/usr/bin/env python3
"""行为与计算不变量检查；不验证预测准确率。"""
import copy
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from paipan import (BE, BRANCHES, CYCLE, HIDDEN, STEMS, InputError, Solar,
                    LunarUtil, build_chart, season, shishen, stage)


def sample(dt='2000-06-01T12:00:00+08:00', **extra):
    return dict({'mode': 'birth', 'birth': {'datetime': dt, 'place': '北京', 'basis': 'standard_utc8'}}, **extra)


def pillars(chart):
    return [p['ganzhi'] for p in chart['pillars']]


def rejects(data):
    try:
        build_chart(data)
    except InputError:
        return
    raise AssertionError(f'未拒绝非法输入：{data}')


def main():
    for d in STEMS:
        for g in STEMS:
            assert shishen(d, g) == LunarUtil.SHI_SHEN[d + g]
    for b in BRANCHES:
        assert set(HIDDEN[b]) == set(LunarUtil.ZHI_HIDE_GAN[b])
    assert stage('甲', '亥') == '长生'
    assert stage('乙', '午') == '长生'
    assert stage('乙', '卯') == '临官'
    assert stage('戊', '寅') == stage('丙', '寅') == '长生'
    assert season('木', '寅') == '旺'
    assert season('火', '寅') == '相'
    assert season('水', '辰') == '死'
    a = build_chart(sample())
    assert pillars(a) == ['庚辰', '辛巳', '庚寅', '壬午'], pillars(a)
    assert a['yun'] is None
    assert sum(a['visible_element_counts'].values()) == 8
    # 两种日界与时干由五鼠遁绑定，不只改日柱标签。
    pre = build_chart(sample('2000-06-01T22:59:59+08:00'))
    late = build_chart(sample('2000-06-01T23:00:00+08:00'))
    mid = build_chart(sample('2000-06-01T23:00:00+08:00', day_boundary='midnight'))
    next_day = build_chart(sample('2000-06-02T00:00:00+08:00'))
    assert pillars(pre)[2] == pillars(mid)[2] == '庚寅'
    assert pillars(late)[2:] == pillars(next_day)[2:] == ['辛卯', '戊子']
    assert pillars(mid)[3] == '丙子'
    # 年月用精确交节：前一秒与交节时刻。
    terms = Solar.fromYmdHms(2024, 6, 1, 12, 0, 0).getLunar().getJieQiTable()
    for name, expected_before, expected_after in [('立春', ['癸卯', '乙丑'], ['甲辰', '丙寅']),
                                                   ('惊蛰', ['甲辰', '丙寅'], ['甲辰', '丁卯'])]:
        dt = datetime.strptime(terms[name].toYmdHms(), '%Y-%m-%d %H:%M:%S')
        before = build_chart(sample((dt - timedelta(seconds=1)).isoformat() + '+08:00'))
        after = build_chart(sample(dt.isoformat() + '+08:00'))
        assert pillars(before)[:2] == expected_before
        assert pillars(after)[:2] == expected_after
    # 时区偏移含夏令调整，等价瞬间不重复修正。
    assert pillars(build_chart(sample('1990-05-17T10:30:00+09:00'))) == pillars(build_chart(sample('1990-05-17T09:30:00+08:00')))
    assert pillars(build_chart(sample('2000-06-01T04:00:00Z'))) == pillars(a)
    true = sample()
    true['birth'].update(basis='provided_true_solar', solar_datetime='2000-06-01T10:59:00', solar_source='测试夹具，不是实际天文换算')
    corrected = build_chart(true)
    assert pillars(corrected)[:3] == pillars(a)[:3]
    assert pillars(corrected)[3] == '辛巳'
    male = build_chart(sample(gender='male'))
    female = build_chart(sample(gender='female'))
    assert male['yun']['direction'] == '顺排' and female['yun']['direction'] == '逆排'
    assert male['yun']['dayun'][0]['ganzhi'] == '壬午'
    assert female['yun']['dayun'][0]['ganzhi'] == '庚辰'
    for gender, direction in [('male', '逆排'), ('female', '顺排')]:
        assert build_chart(sample('2001-06-01T12:00:00+08:00', gender=gender))['yun']['direction'] == direction
    # 独立由出生至下一节的分钟数验证折算，不能把中气拿来起运。
    current = datetime(2000, 6, 1, 12)
    end = datetime.strptime(male['time']['next_jie']['datetime'], '%Y-%m-%d %H:%M:%S')
    minutes = int((end.replace(second=0) - current).total_seconds() // 60)
    yy, rem = divmod(minutes, 4320)
    mm, rem = divmod(rem, 360)
    dd, rem = divmod(rem, 12)
    assert male['yun']['start_offset'] == dict(years=yy, months=mm, days=dd, hours=rem * 2)
    runs = male['yun']['dayun']
    assert len(runs) == 8 and runs[0]['index'] == 1
    assert runs[0]['start_inclusive_utc8'] == male['yun']['start_utc8']
    assert all(x['end_exclusive_utc8'] == y['start_inclusive_utc8'] for x, y in zip(runs, runs[1:]))
    true['gender'] = 'male'
    assert build_chart(true)['yun']['start_utc8'] == male['yun']['start_utc8']
    f = build_chart(sample(flow_years=[2024]))['flow_years'][0]
    assert f['ganzhi'] == '甲辰' and f['start_inclusive_utc8'] == terms['立春'].toYmdHms()
    assert f['end_exclusive_utc8'].startswith('2025-02-')
    manual = {'mode': 'manual', 'pillars': ['甲子', '丙寅', '甲子', None], 'source': '测试三柱'}
    m = build_chart(manual)
    assert m['pillars'][3]['ganzhi'] is None and m['yun'] is None
    assert sum(m['visible_element_counts'].values()) == 6
    for key, val in [('day_boundary', 'guess'), ('gender', 'guess'), ('flow_years', [True]), ('flow_years', [2100]), ('unknown', 1)]:
        bad = sample(); bad[key] = val; rejects(bad)
    for key, val in [('datetime', '2000-06-01'), ('datetime', '2000-02-30T12:00+08:00'), ('basis', 'auto'), ('place', '')]:
        bad = sample(); bad['birth'][key] = val; rejects(bad)
    bad = sample(); bad['birth']['solar_datetime'] = '2000-06-01T12:00'; rejects(bad)
    for pp in [['甲子', '甲寅', '甲子', None], ['甲子', '丙寅', '甲子', '丙子'], ['甲子', '丙寅', '甲子', '乙子']]:
        rejects(dict(manual, pillars=pp))
    # CLI 保存、解析失败与不覆盖已有文件。
    script = Path(__file__).with_name('paipan.py')
    with tempfile.TemporaryDirectory() as tmp:
        inp = Path(tmp) / 'input.json'
        inp.write_text(json.dumps(sample(), ensure_ascii=False), encoding='utf-8')
        out = Path(tmp) / 'chart'
        command = [sys.executable, '-B', str(script), '--input', str(inp), '--output-dir', str(out)]
        first = subprocess.run(command, capture_output=True, text=True)
        assert first.returncode == 0, first.stderr
        saved = (out / 'chart.json').read_bytes()
        assert json.loads(saved)['chart_markdown'] == (out / 'chart.md').read_text(encoding='utf-8')
        second = subprocess.run(command, capture_output=True, text=True)
        assert second.returncode != 0 and (out / 'chart.json').read_bytes() == saved
        inp.write_text('{bad json', encoding='utf-8')
        assert subprocess.run(command, capture_output=True).returncode != 0
    print('PASS: 十神/藏干、四柱、子时、节气、时间口径、起运、流年、非法输入与 CLI 保存检查')


if __name__ == '__main__':
    main()
