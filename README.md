# divination-skills

独立占卜 skills 的集合。每种术数单独维护自己的输入、排盘约定、参考规则和验证工具，按需要安装，不互相混用流派。

| Skill | 当前范围 | 入口 |
|---|---|---|
| 六爻 `liuyao` | 增删卜易入门体系；投币纳甲排盘、日月动变与用神分析 | [SKILL.md](skills/liuyao/SKILL.md) · [使用说明](skills/liuyao/README.md) |
| 奇门 `qimen` | 转盘时家奇门；拆补排盘、已有盘解读、用神与类象、感情案例 | [SKILL.md](skills/qimen/SKILL.md) |

目前包含六爻与奇门，均可独立安装。八字、塔罗等以后可在 `skills/` 下并列增加独立目录，尚未实现的技能不放占位入口。六爻迁移来源与旧安装更新说明见 [迁移记录](docs/migration.md)。

```text
skills/
  liuyao/             # 六爻：入口、规则、排盘脚本、离线依赖与许可证
  qimen/
    SKILL.md
    agents/openai.yaml
    references/        # 从本地课程提炼的按需规则与出处
    scripts/           # 排盘与检查
    vendor/            # 离线历法依赖及其许可证
    requirements.txt
docs/liuyao/结构化参考资料/ # 六爻教程整理、校对与待核记录
本地参考文件/          # 作者本地资料，已被 Git 忽略
```

## 六爻使用

按需安装完整的 `skills/liuyao` 目录，使用 `$liuyao` 调用。已有旧版时更新同名安装，不重复安装。输入、示例与离线排盘命令见 [六爻使用说明](skills/liuyao/README.md)。

六爻检查（在仓库根目录，Python 3.9+）：

```sh
python3 -B skills/liuyao/scripts/checks.py
```

六爻原创代码与文档沿用 [MIT 许可证](skills/liuyao/LICENSE)，第三方内容保留各自权利及来源说明。

## 奇门使用

将完整的 `skills/qimen` 目录复制或链接到所用客户端的 skills 目录，保留 `references`、`scripts` 与 `vendor`。本仓库中的创建不自动修改全局安装。

可直接提问：“用奇门，按 2026 年 9 月 13 日上午 10:30 北京时间起局，看看我本月底能否拿到录用通知。”已有盘也可直接提供并说明原排法。

默认：拆补、转盘、五寄坤二、天禽随芮、天盘八神、Asia/Shanghai 民用时间、零点换日。自动程序没有实现置闰、茅山、飞盘或真太阳时。已有盘沿用原排法，不静默改盘。

开发检查（Python 3.9+）：

```sh
python3 -B skills/qimen/scripts/checks.py
```

输入格式见 [输入约定](skills/qimen/references/input.md)，资料覆盖、校订与验证边界见 [来源说明](skills/qimen/references/sources.md)。原始视频转录不随 skill 复制；提炼规则可独立使用。历法依赖 `lunar_python 1.4.8` 随附 MIT 许可证，其他整理文本不代原视频或书籍授予授权。
