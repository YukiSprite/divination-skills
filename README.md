# divination-skills

独立占卜 skills 的集合。每种术数单独维护自己的输入、排盘约定、参考规则和验证工具，按需要安装，不互相混用流派。

| Skill | 当前范围 | 入口 |
|---|---|---|
| 奇门 `qimen` | 转盘时家奇门；拆补排盘、已有盘解读、用神与类象、感情案例 | [SKILL.md](skills/qimen/SKILL.md) |
| 八字 `bazi` | 子平八字；四柱十神、旺衰与取用、格局候选、大运流年趋势 | [SKILL.md](skills/bazi/SKILL.md) |
| 六爻 `liuyao` | 增删卜易入门体系；六次投币纳甲排盘、取用、生克动变、旬空与生旺墓绝 | [SKILL.md](skills/liuyao/SKILL.md) · [使用说明](skills/liuyao/README.md) |

六爻迁移来源与旧安装更新说明见[迁移记录](docs/migration.md)。

## 知识来源

### 奇门

主要资料整理自**云野卦馆的[哔哩哔哩奇门系列视频（BV1La4y1y7Qg）](https://www.bilibili.com/video/BV1La4y1y7Qg)**，依据本地保存的 10 篇课程转录提炼。

- **基础与排盘：** 六十甲子、旬空、五行、后天九宫，以及地盘、天盘、九星、八门、八神、时空时马；梳理拆补、置闰、茅山的差异，自动排盘采用拆补转盘。
- **解读方法：** 八宫、天干、星门神类象，主客与十二长生，部分十干克应、击刑入墓、伏吟反吟，日时取用、宫内组合与宫间关系，以及感情课例。
- **古籍补充：** 对照[《奇门旨归》卷一起例歌](https://www.shidianguji.com/mid-page/7531869976861933618)核对二十四节气的三元定局表，包括小寒 285、大寒与春分 396。

逐课出处、转录校订和实现约定见[奇门来源说明](skills/qimen/references/sources.md)。

### 八字

主要资料整理自**云野卦馆的[哔哩哔哩八字五讲（BV1frxZenE74）](https://www.bilibili.com/video/BV1frxZenE74)**，依据本地新增的五篇课程转录提炼。

- **基础与排盘：** 阴阳五行、干支节气、五虎遁与五鼠遁、藏干十神、两套十二长生、大运顺逆和起运换算。
- **解读方法：** 月令与根气判断旺衰、月令格局候选、扶抑、病药、通关、调候及原局与运年的关系。
- **时间约定：** 课程推荐真太阳时、23 点换日；本版默认 23 点换日，时间口径须明确选择。支持 UTC+8 标准时间或有来源的已换算真太阳时，尚不自动换算真太阳时。出生偏移需包含实际夏令时；农历先可靠转为公历。

逐讲出处、转录校订与实现范围见[八字来源说明](skills/bazi/references/sources.md)，时间与输入格式见[八字输入约定](skills/bazi/references/input.md)。

### 六爻

主要资料整理自**云野卦馆的[哔哩哔哩六爻系列视频（BV12bzpBuEuG）](https://www.bilibili.com/video/BV12bzpBuEuG/)**，采用《增删卜易》入门体系，依据本地保存的基础篇、排盘篇、用神篇和第 8 集共四份教程转录提炼。

- **基础与排盘：** 五行、干支、六亲、投币计数与爻序，纳甲、八宫、世应、六神、伏神，以及动爻变化和变爻六亲的归属。
- **解读方法：** 用神、元神、忌神、仇神的取用与作用方向，日月旺衰、动变、生扶克制，旬空、生旺墓绝，以及游魂归魂的辅助判断。
- **古籍补充：** 对照[《增删卜易》公开整理本](https://zh.wikisource.org/zh-hans/增刪卜易)中的《浑天甲子章》《八宫图》《用神章》《元神忌神衰旺章》《暗动章》《旬空章》《生旺墓绝章》《各门类题头总注》《归魂游魂章》及整理者增订的纳甲表，补齐固定表和条件规则；用[《周易·颐》](https://ctext.org/book-of-changes/yi4/zh)校正卦名录入错误。

逐篇出处、纳甲表和转录校订见[六爻来源说明](skills/liuyao/references/sources.md)；课程整理见[结构化参考资料目录](docs/liuyao/结构化参考资料/00-资料目录与整理说明.md)。

三份 skill 均随附 [lunar-python 1.4.8](https://github.com/6tail/lunar-python) 用于历法与干支计算；术数排盘和解读规则分别维护。原始视频转录保留在本地，发布内容为提炼后的规则、程序与出处记录。

## 目录

```text
skills/
  bazi/
    SKILL.md
    agents/openai.yaml
    references/        # 输入、旺衰、取用、关系与逐讲出处
    scripts/           # 四柱排盘、大运流年与检查
    vendor/            # 离线历法依赖及其许可证
    requirements.txt
  qimen/
    SKILL.md
    agents/openai.yaml
    references/        # 从本地课程提炼的按需规则与出处
    scripts/           # 排盘与检查
    vendor/            # 离线历法依赖及其许可证
    requirements.txt
  liuyao/
    SKILL.md
    agents/openai.yaml
    references/        # 输入、取用、生克及专项规则与出处
    scripts/           # 纳甲排盘、固定表与检查
    vendor/            # 离线历法依赖及其许可证
    requirements.txt
docs/liuyao/结构化参考资料/ # 六爻教程整理、校对与待核记录
本地参考文件/          # 作者本地资料，已被 Git 忽略
```

## 使用

将所需的完整目录 `skills/qimen`、`skills/liuyao` 或 `skills/bazi` 复制或链接到所用客户端的 skills 目录，保留 `references`、`scripts` 与 `vendor`。三份 skill 可分别安装，也可同时安装；已有旧版六爻时更新同名安装。

### 奇门

奇门遁甲把时间、方位与人物、事情的关系放入九宫盘中分析。本技能采用转盘时家奇门，观察所问对象之间的支持、阻力与变化，判断局势和推进方向，适合围绕具体问题起局，也支持已有盘面解读。

提供具体问题和起局时间，例如：

> 用奇门，按 2026 年 9 月 13 日上午 10:30 北京时间起局，看看我本月底能否拿到录用通知。

已有盘可直接提供，并说明原排法。自动排盘默认拆补、转盘、五寄坤二、天禽随芮、天盘八神，采用 Asia/Shanghai 民用时间、零点换日。详细格式见[奇门输入约定](skills/qimen/references/input.md)。

### 八字

八字以出生年、月、日、时组成四柱，以日干为主，结合月令、根气、十神与大运流年，解释人生和阶段趋势。本技能采用子平入门框架，适合分析事业财运的阶段变化，也支持已有四柱解读。

提供出生日期、时分、地点和时间口径；排大运时另需传统顺逆算法使用的性别。例如：

> 用八字，男，公历 2000 年 6 月 1 日 12:00，北京出生，按北京时间标准时、23 点换日，看 2026 和 2027 年的事业财运趋势。

请替换成自己的资料，注明公历或农历；已有四柱也可直接提供。默认 23 点换日，时间口径须明确选择；真太阳时目前需提供有来源的已换算结果。详细格式见[八字输入约定](skills/bazi/references/input.md)。

### 六爻

六爻是一种围绕具体问题起卦、解卦的传统占卜方法。用三枚硬币连续投掷六次，从下往上组成六个爻，再结合动爻变化、起卦时间和各爻之间的关系，判断事情的进展与成败倾向。本技能采用《增删卜易》入门体系。

提供具体问题、六次真实投币结果和起卦时间，例如：

> 用六爻，问本月底能否拿到录用通知。六次投币按先后顺序，每次背面数是 1、1、0、2、1、3，起卦时间为 2026 年 9 月 13 日上午 10:30，北京时间。

请替换成自己的真实投币结果、问题和起卦时间。第一次投掷对应最下方初爻，背面数 0／1／2／3 对应老阴／少阳／少阴／老阳。默认 Asia/Shanghai 民用时间、零点换日。详细格式见[六爻输入约定](skills/liuyao/references/input.md)。

## 开发检查

Python 3.9+：

```sh
python3 -B skills/qimen/scripts/checks.py
python3 -B skills/liuyao/scripts/checks.py
python3 -B skills/bazi/scripts/checks.py
```

## 许可证

本仓库原创代码与文档采用 [MIT License](LICENSE)，版权归 YukiSprite 所有。第三方依赖保留各自的版权声明与许可证；原视频、书籍及其他来源材料的权利归原权利人所有。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=YukiSprite/divination-skills&type=Date)](https://www.star-history.com/#YukiSprite/divination-skills&Date)
