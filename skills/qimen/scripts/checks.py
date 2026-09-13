#!/usr/bin/env python3
"""检查结构、已知课例及历法边界；不测试占断的预测有效性。"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import paipan as q


def manual(ju=2, dun="yang", day="乙酉", hour="辛巳"):
    return {"method": "manual", "ju": ju, "dun": dun,
            "time": {"kind": "manual", "day_ganzhi": day, "hour_ganzhi": hour, "source": "测试夹具"}}


def civil(at, **kwargs):
    return {"time": {"kind": "civil", "at": at, **kwargs}}


def cells(chart):
    return {c["number"]: c for c in chart["palaces"]}


class ChartChecks(unittest.TestCase):
    def test_course_worked_chart(self):
        c = q.build(manual())
        self.assertEqual((c['xun_head'], c['xun_yi'], c['zhifu_star'], c['zhifu_palace'], c['zhishi_door'], c['zhishi_palace']),
                         ('甲戌', '己', '天冲', 2, '伤门', 1))
        self.assertEqual(c['hour_void'], ['申', '酉'])
        self.assertEqual(c['hour_horse'], '亥')
        # 手工按课例转步展开的各宫真值，非由生产函数生成期望值。
        expected = {
            1: ('乙', ['戊', '辛'], ['天芮', '天禽'], '伤门', '六合'),
            2: ('戊', ['己'], ['天冲'], '开门', '值符'),
            3: ('己', ['壬'], ['天心'], '景门', '玄武'),
            4: ('庚', ['乙'], ['天蓬'], '死门', '九地'),
            6: ('壬', ['丙'], ['天英'], '生门', '太阴'),
            7: ('癸', ['庚'], ['天辅'], '休门', '螣蛇'),
            8: ('丁', ['癸'], ['天柱'], '杜门', '白虎'),
            9: ('丙', ['丁'], ['天任'], '惊门', '九天'),
        }
        for p, value in expected.items():
            x = cells(c)[p]
            self.assertEqual((x['earth_stems'][0], x['heaven_stems'], x['stars'], x['door'], x['god']), value)
        self.assertEqual(cells(c)[5]['earth_stems'], ['辛'])
        self.assertEqual(cells(c)[2]['earth_stems'], ['戊', '辛'])

    def test_yin_chart_and_gods(self):
        c = q.build(manual(1, 'yin'))
        self.assertEqual((c['zhifu_star'], c['zhifu_palace'], c['zhishi_door'], c['zhishi_palace']), ('天英', 7, '景门', 2))
        x = cells(c)
        self.assertEqual([x[p]['god'] for p in [7, 2, 9, 4, 3, 8, 1, 6]], q.GODS)
        self.assertEqual(x[6]['heaven_stems'], ['乙', '癸'])
        self.assertEqual(x[6]['stars'], ['天芮', '天禽'])
        self.assertEqual(x[1]['door'], '开门')

    def test_center_origin_kept_for_door_count(self):
        c = q.build(manual(5, 'yang', '甲子', '乙丑'))
        self.assertEqual(c['xun_original_palace'], 5)
        self.assertEqual(c['zhifu_star'], '天禽')
        self.assertEqual(c['zhishi_door'], '死门')
        self.assertEqual(c['zhishi_raw_palace'], 6)
        self.assertEqual(c['zhishi_palace'], 6)
        c = q.build(manual(5, 'yin', '甲子', '乙丑'))
        self.assertEqual(c['zhishi_raw_palace'], 4)
        c = q.build(manual(5, 'yang', '甲子', '甲子'))
        self.assertEqual(c['zhishi_raw_palace'], 5)
        self.assertEqual(c['zhishi_palace'], 2)

    def test_all_18_by_60_structures(self):
        for dun in ('yang', 'yin'):
            for ju in range(1, 10):
                for i, hour in enumerate(q.CYCLE):
                    # 每个合法时干支选择符合五鼠遁的日干支。
                    hi = q.BRANCHES.index(hour[1])
                    di = next(d for d in range(5) if (d * 2 + hi) % 10 == i % 10)
                    c = q.build(manual(ju, dun, q.CYCLE[di], hour))
                    x = cells(c)
                    outer = [x[p] for p in q.RING]
                    self.assertEqual(sorted(s for cell in outer for s in cell['heaven_stems']), sorted(q.YI))
                    self.assertEqual(len({cell['door'] for cell in outer}), 8)
                    self.assertEqual(len({cell['god'] for cell in outer}), 8)
                    self.assertEqual(len({s for cell in outer for s in cell['stars']}), 9)
                    self.assertEqual(x[ju]['earth_stems'][0], '戊')
                    self.assertEqual(x[5]['heaven_stems'], [])
                    self.assertEqual(x[2]['earth_hosted_stem'], x[5]['earth_stems'][0])
                    for cell in outer:
                        self.assertEqual('天禽' in cell['stars'], '天芮' in cell['stars'])
                    self.assertIn(c['xun_yi'], x[c['zhifu_palace']]['heaven_stems'])
                    self.assertEqual(x[c['zhifu_palace']]['god'], '值符')
                    self.assertEqual(x[c['zhishi_palace']]['door'], c['zhishi_door'])
                    self.assertEqual(sum(cell['horse'] for cell in outer), 1)
                    self.assertEqual(sorted(b for cell in outer for b in cell['void_branches']), sorted(c['hour_void']))
                    self.assertEqual(len(c['hour_void']), 2)
                    self.assertFalse(c['global_facts']['星伏吟'] and c['global_facts']['星反吟'])
                    if hour[0] == '甲':
                        self.assertTrue(c['global_facts']['星伏吟'])
                        self.assertTrue(c['global_facts']['门伏吟'])

    def test_yuan_and_full_cycle(self):
        self.assertEqual(q.yuan_for('壬辰'), ('己丑', 2))
        self.assertEqual(q.yuan_for('丙寅'), ('甲子', 0))
        self.assertEqual(q.yuan_for('乙酉'), ('甲申', 1))
        for start in range(0, 60, 5):
            self.assertEqual(len({q.yuan_for(q.CYCLE[start + j]) for j in range(5)}), 1)
        # 八节所在宫起数；上中下各差三；独立检查表的结构而不是匹配文件文字。
        self.assertEqual([q.TERMS[t]['ju'][0] for t in ['冬至', '立春', '春分', '立夏', '夏至', '立秋', '秋分', '立冬']], [1, 8, 3, 4, 9, 2, 7, 6])
        # E01 起例表独立抄录：覆盖容易颠倒的中、下元顺序。
        expected = [('冬至惊蛰', [1, 7, 4]), ('小寒', [2, 8, 5]), ('大寒春分', [3, 9, 6]),
                    ('立春', [8, 5, 2]), ('雨水', [9, 6, 3]), ('清明立夏', [4, 1, 7]), ('谷雨小满', [5, 2, 8]), ('芒种', [6, 3, 9]),
                    ('夏至白露', [9, 3, 6]), ('小暑', [8, 2, 5]), ('大暑秋分', [7, 1, 4]), ('立秋', [2, 5, 8]),
                    ('处暑', [1, 4, 7]), ('寒露立冬', [6, 9, 3]), ('霜降小雪', [5, 8, 2]), ('大雪', [4, 7, 1])]
        for names, value in expected:
            for offset in range(0, len(names), 2):
                self.assertEqual(q.TERMS[names[offset:offset + 2]]['ju'], value)
        for t in q.TERMS.values():
            step = -3 if t['dun'] == 'yang' else 3
            self.assertEqual(t['ju'][1], (t['ju'][0] - 1 + step) % 9 + 1)
            self.assertEqual(t['ju'][2], (t['ju'][1] - 1 + step) % 9 + 1)

    def test_relations_and_states(self):
        self.assertEqual(q.relation('水', '木'), '生')
        self.assertEqual(q.relation('火', '水'), '被克')
        self.assertEqual(q.season_state('水', '水'), '旺')
        self.assertEqual(q.season_state('水', '水', True), '相')
        self.assertEqual(q.season_state('水', '木', True), '旺')
        self.assertEqual(q.stage('乙', '戌'), '墓')
        self.assertEqual(q.stage('乙', '亥'), '死')
        self.assertEqual(q.stage('戊', '戌'), '墓')
        self.assertEqual(q.stage('己', '丑'), '墓')
        self.assertEqual(q.alias('甲戌'), '己')
        self.assertEqual(q.alias('甲辰'), '壬')
        self.assertEqual(q.build(manual(day='甲子', hour='庚午'))['global_facts']['五不遇时'], True)
        self.assertEqual(q.build(manual(day='甲子', hour='辛未'))['global_facts']['五不遇时'], False)

    def test_civil_reconstructs_course_chart(self):
        c = q.build(civil('2022-06-01T09:11:00'))
        self.assertEqual([c['calendar'][k] for k in ['year_ganzhi', 'month_ganzhi', 'day_ganzhi', 'hour_ganzhi']], ['壬寅', '乙巳', '乙酉', '辛巳'])
        self.assertEqual((c['dun'], c['ju'], c['day_futou'], c['day_yuan']), ('yang', 2, '甲申', '中元'))
        self.assertEqual(c['palaces'], q.build(dict(manual(), time={'kind':'manual', 'year_ganzhi':'壬寅', 'month_ganzhi':'乙巳', 'day_ganzhi':'乙酉', 'hour_ganzhi':'辛巳', 'source':'夹具'}))['palaces'])
        c = q.build(civil('1995-01-01T12:00:00'))
        self.assertEqual(c['calendar']['day_ganzhi'], '壬辰')
        self.assertEqual((c['dun'], c['ju'], c['day_yuan']), ('yang', 4, '下元'))

    def test_day_boundary(self):
        a = q.build(civil('2026-09-13T23:30:00', day_boundary='midnight'))
        b = q.build(civil('2026-09-13T23:30:00', day_boundary='zi23'))
        self.assertEqual(q.ganzhi_index(b['calendar']['day_ganzhi']), (q.ganzhi_index(a['calendar']['day_ganzhi']) + 1) % 60)
        self.assertNotEqual(a['calendar']['hour_ganzhi'], b['calendar']['hour_ganzhi'])
        midnight = q.build(civil('2026-09-14T00:00:00'))
        self.assertEqual(midnight['calendar']['day_ganzhi'], b['calendar']['day_ganzhi'])
        self.assertEqual(midnight['calendar']['hour_ganzhi'], b['calendar']['hour_ganzhi'])

    def test_solar_term_instant_and_timezone(self):
        from lunar_python import Solar
        jq = Solar.fromYmdHms(2026, 7, 1, 12, 0, 0).getLunar().getJieQiTable()
        for term, prev, new_dun in [('夏至', '芒种', 'yin'), ('冬至', '大雪', 'yang'), ('立春', '大寒', 'yang')]:
            at = datetime.fromisoformat(jq[term].toYmdHms())
            before = q.build(civil((at - timedelta(seconds=1)).isoformat()))
            after = q.build(civil(at.isoformat()))
            self.assertEqual(before['calendar']['solar_term'], prev)
            self.assertEqual(after['calendar']['solar_term'], term)
            self.assertEqual(after['dun'], new_dun)
            if term == '立春':
                self.assertNotEqual(before['calendar']['year_ganzhi'], after['calendar']['year_ganzhi'])
                self.assertNotEqual(before['calendar']['month_ganzhi'], after['calendar']['month_ganzhi'])
            # 同一时刻在上海和纽约都必须使用同一节气，日时柱仍可不同。
            ny = q.build(civil(at.isoformat() + '+08:00', timezone='America/New_York'))
            self.assertEqual(ny['calendar']['solar_term'], term)
        c = q.build(civil('2022-06-01T01:11:00Z'))
        self.assertEqual(c['palaces'], q.build(civil('2022-06-01T09:11:00'))['palaces'])

    def test_invalid_inputs(self):
        bad = [civil('2026-09-13'), civil('2026-02-30T12:00:00'), civil('2026-09-13T12:00:00', day_boundary='guess'),
               civil('2026-03-08T02:30:00', timezone='America/New_York'), civil('2026-11-01T01:30:00', timezone='America/New_York'),
               civil('2026-09-13T12:00:00', timezone='No/Such_Zone'), manual(0), manual(True), manual(dun='random'),
               manual(day='甲丑'), manual(day='己酉', hour='辛巳'), dict(manual(), method='zhirun'), dict(manual(), method='chaibu')]
        no_source = manual()
        del no_source['time']['source']
        bad.append(no_source)
        bad.append(dict(manual(), unknown=True))
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(q.InputError):
                q.build(inp)
        # 显式偏移可消歧。
        q.build(civil('2026-11-01T01:30:00-04:00', timezone='America/New_York'))

    def test_cli_saves_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='qimen-check-') as tmp:
            root = Path(tmp)
            inp = root / 'input.json'
            data = manual()
            data['question'] = '保留原问题：合同能成吗？'
            inp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            output = root / 'result'
            args = [sys.executable, '-B', str(Path(q.__file__)), '--input', str(inp), '--output-dir', str(output)]
            a = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(json.loads((output / 'input.json').read_text()), data)
            saved = (output / 'chart.json').read_bytes()
            self.assertEqual(json.loads(saved)['chart_markdown'], (output / 'chart.md').read_text())
            b = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(b.returncode, 2)
            self.assertIn('error', json.loads(b.stderr))
            self.assertEqual((output / 'chart.json').read_bytes(), saved)


if __name__ == '__main__':
    unittest.main(verbosity=2)
