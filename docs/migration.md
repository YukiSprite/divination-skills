# 六爻迁移记录

## 来源与维护位置

2026-09-20 将独立仓库 [YukiSprite/liuyao-skill](https://github.com/YukiSprite/liuyao-skill) 的六爻技能迁入本仓库。

- 来源提交：[`c6fa71e91956b8d2f165ec885a4cb1f17a7dde45`](https://github.com/YukiSprite/liuyao-skill/tree/c6fa71e91956b8d2f165ec885a4cb1f17a7dde45)。
- `liuyao/` → `skills/liuyao/`：完整保留技能入口、展示信息、规则、程序、依赖和许可证。
- 原仓库 `README.md` → `skills/liuyao/README.md`：适配安装入口、命令和链接。
- `结构化参考资料/` → `docs/liuyao/结构化参考资料/`：保留六篇整理资料及校对记录，修正跨目录链接。

本次采用快照迁移，原提交历史仍可在来源仓库查询。合并后六爻后续开发在本仓库的 `skills/liuyao/` 进行；此迁移不自动修改或归档来源仓库。

## 已有安装如何更新

技能名称仍为 `liuyao`，调用方式仍为 `$liuyao`，输入格式、排盘输出与规则保持不变。

1. 将更新来源切换为本仓库的 `skills/liuyao`。
2. 复制安装：备份个人改动后，用完整的新目录更新原来的同名安装；保留随附 `vendor` 和许可证。
3. 符号链接安装：将现有 `liuyao` 链接改为新检出仓库的 `skills/liuyao`。
4. 只保留一个有效的同名安装，重新加载技能后运行下列检查。

```sh
python3 -B <已安装的liuyao目录>/scripts/checks.py
```

此仓库迁移本身不会修改使用者本机的全局安装。

## 独立运行与检查

六爻目录保留自己的 `lunar_python 1.4.8`，可以单独复制运行，不依赖奇门目录或仓库外的原稿。结构化参考资料供来源追溯；运行时规则已包含于技能的 `references/`。

在仓库根目录运行：

```sh
python3 -B skills/liuyao/scripts/checks.py
```

六爻自动检查使用独立工作流，涵盖原有排盘测试以及复制到仓库外后的运行。奇门目录不在本次迁移修改范围内。

## 许可与致谢

六爻的原创代码与文档保留 [MIT 许可证](../skills/liuyao/LICENSE) 和原版权署名。随附历法依赖保留其许可证。教程致谢、第三方内容边界和待核记录见 [六爻说明](../skills/liuyao/README.md) 与 [来源记录](../skills/liuyao/references/sources.md)；不将六爻的许可扩展到其他技能。
