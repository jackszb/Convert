#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 sing-box 源规则文件 (rules1/*.json) 转换为 Shadowrocket RULE-SET 文件 (rules2/*.list)

支持的 sing-box 规则键（可以只出现其中一个或几个，不要求四个键同时存在）：
    - domain            -> DOMAIN,xxx
    - domain_suffix      -> DOMAIN-SUFFIX,xxx
    - domain_keyword     -> DOMAIN-KEYWORD,xxx
    - ip_cidr            -> IP-CIDR,xxx,no-resolve  (IPv6 统一写成 IP-CIDR，Shadowrocket 会自动识别)

用法：
    python3 convert.py <输入目录:rules1> <输出目录:rules2>

脚本会遍历输入目录下所有 .json 文件，逐一转换并写出同名（后缀改为 .list）的
Shadowrocket 规则文件到输出目录。如果某个 json 文件解析失败或没有任何可识别
的键，会打印警告并跳过，不会中断整体流程。
"""

import json
import os
import sys
from pathlib import Path

# sing-box 键 -> shadowrocket 规则前缀 的映射，按照输出顺序排列
KEY_MAPPING = [
    ("domain", "DOMAIN"),
    ("domain_suffix", "DOMAIN-SUFFIX"),
    ("domain_keyword", "DOMAIN-KEYWORD"),
    ("ip_cidr", "IP-CIDR"),
]


def convert_ruleset(rule_obj: dict) -> list:
    """将单个 sing-box rule 对象转换为 shadowrocket 规则行列表"""
    lines = []
    for key, prefix in KEY_MAPPING:
        values = rule_obj.get(key)
        if not values:
            # 键不存在，或者是空列表 —— 直接跳过，兼容"只有一种或几种键"的情况
            continue
        if not isinstance(values, list):
            print(f"    [警告] 键 '{key}' 的值不是列表，已跳过：{values!r}")
            continue
        for v in values:
            if prefix == "IP-CIDR":
                lines.append(f"{prefix},{v},no-resolve")
            else:
                lines.append(f"{prefix},{v}")
    return lines


def convert_file(src_path: Path, dst_path: Path) -> bool:
    """转换单个 json 文件，返回是否成功"""
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[错误] 无法解析 {src_path.name}：{e}")
        return False

    rules = data.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        print(f"[警告] {src_path.name} 中没有找到有效的 'rules' 数组，已跳过")
        return False

    all_lines = []
    for rule_obj in rules:
        if not isinstance(rule_obj, dict):
            continue
        all_lines.extend(convert_ruleset(rule_obj))

    if not all_lines:
        print(f"[警告] {src_path.name} 未识别出任何可转换的规则（domain/domain_suffix/domain_keyword/ip_cidr），已跳过")
        return False

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dst_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"[成功] {src_path.name} -> {dst_path.name} （共 {len(all_lines)} 条规则）")
    return True


def main():
    if len(sys.argv) != 3:
        print("用法: python3 convert.py <rules1目录> <rules2目录>")
        sys.exit(1)

    src_dir = Path(sys.argv[1])
    dst_dir = Path(sys.argv[2])

    if not src_dir.is_dir():
        print(f"[错误] 输入目录不存在：{src_dir}")
        sys.exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(src_dir.glob("*.json"))
    if not json_files:
        print(f"[信息] {src_dir} 中没有找到任何 .json 文件，无需处理")
        return

    ok_count = 0
    for src_file in json_files:
        dst_file = dst_dir / (src_file.stem + ".list")
        if convert_file(src_file, dst_file):
            ok_count += 1

    print(f"\n处理完成：共 {len(json_files)} 个文件，成功转换 {ok_count} 个")


if __name__ == "__main__":
    main()
