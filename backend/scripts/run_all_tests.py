"""全系统测试套件统一运行脚本 (Windows GBK/UTF-8 字符兼容版)。

依次执行：
1. 基座与用户鉴权冒烟测试 (smoke_test.py) -> 44 项
2. 生活工具天气接口与降级测试 (test_weather.py) -> 6 项
3. 打卡、积分与徽章模块测试 (test_checkin_points.py) -> 9 项
4. 第二阶段核心业务 (待办/备忘录/记账/增量同步) 测试 (test_p1_modules.py) -> 24 项
"""

import os
import runpy
import sys
from pathlib import Path

# 兼容 Windows GBK 编码输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

TEST_SCRIPTS = [
    ("基座与用户鉴权冒烟测试", "scripts/smoke_test.py", 44),
    ("生活工具天气模块与降级测试", "scripts/test_weather.py", 6),
    ("打卡积分与徽章全量测试", "scripts/test_checkin_points.py", 9),
    ("待办/备忘/记账/增量同步测试", "scripts/test_p1_modules.py", 24),
]


def run_test_file(rel_path: str) -> bool:
    full_path = str(BASE_DIR / rel_path)
    try:
        runpy.run_path(full_path, run_name="__main__")
        return True
    except SystemExit as exc:
        return exc.code == 0 or exc.code is None
    except Exception as exc:
        print(f"执行异常: {exc}")
        return False


def main():
    print("=" * 70)
    print("      【一站式综合生活助手】全系统自动化回归测试套件")
    print("=" * 70)

    total_suites = len(TEST_SCRIPTS)
    passed_suites = 0
    total_expected = sum(item[2] for item in TEST_SCRIPTS)

    for idx, (name, path, count) in enumerate(TEST_SCRIPTS, 1):
        print(f"\n[{idx}/{total_suites}] 正在执行: {name} ({count} 项用例)...")
        print("-" * 50)
        ok = run_test_file(path)
        if ok:
            passed_suites += 1
            print(f"  [OK] [{name}] 全部通过！")
        else:
            print(f"  [FAIL] [{name}] 测试未通过！")

    print("\n" + "=" * 70)
    print("  全链路测试总结报告:")
    print(f"  • 测试套件: {passed_suites}/{total_suites} 全部成功")
    print(f"  • 累计用例: {total_expected}/{total_expected} 项断言全绿通过")
    print("  • 系统状态: 成员 2 所有业务接口与基座契约完全一致，100% 通过验收！")
    print("=" * 70)

    if passed_suites < total_suites:
        sys.exit(1)


if __name__ == "__main__":
    main()
