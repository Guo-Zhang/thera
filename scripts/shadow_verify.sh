#!/bin/bash
# 影子模式验证脚本
# 用法: ./scripts/shadow_verify.sh [repo_path]
# 
# 在真实环境中并行运行新旧代码，仅报警不阻断

set -e

REPO="${1:-.}"

echo "=========================================="
echo "影子模式验证"
echo "仓库: $REPO"
echo "=========================================="
echo ""

cd "$REPO"

echo ">>> 1. 旧引擎: doc-check"
OLD_DOC_CHECK=$(python -m thera doc-check 2>&1 || true)
echo "$OLD_DOC_CHECK"
echo ""

echo ">>> 2. 新引擎: doc-check --new-engine"
NEW_DOC_CHECK=$(python -m thera doc-check --new-engine 2>&1 || true)
echo "$NEW_DOC_CHECK"
echo ""

echo ">>> 对比结果"
if [ "$OLD_DOC_CHECK" = "$NEW_DOC_CHECK" ]; then
    echo "✓ 结果一致"
    DOC_MATCH=1
else
    echo "✗ 结果不一致（需人工确认）"
    DOC_MATCH=0
fi
echo ""

echo ">>> 3. 旧引擎: submodule-sync --check"
OLD_SUBMODULE=$(python -m thera submodule-sync --check 2>&1 || true)
echo "$OLD_SUBMODULE"
echo ""

echo ">>> 4. 新引擎: submodule-sync --check --new-engine"
NEW_SUBMODULE=$(python -m thera submodule-sync --check --new-engine 2>&1 || true)
echo "$NEW_SUBMODULE"
echo ""

echo ">>> 对比结果"
if [ "$OLD_SUBMODULE" = "$NEW_SUBMODULE" ]; then
    echo "✓ 结果一致"
    SUBMODULE_MATCH=1
else
    echo "✗ 结果不一致（需人工确认）"
    SUBMODULE_MATCH=0
fi
echo ""

echo ">>> 5. 旧引擎: auto-commit --dry-run"
OLD_AUTO_COMMIT=$(python -m thera auto-commit --dry-run 2>&1 || true)
echo "$OLD_AUTO_COMMIT"
echo ""

echo ">>> 6. 新引擎: auto-commit --dry-run --new-engine"
NEW_AUTO_COMMIT=$(python -m thera auto-commit --dry-run --new-engine 2>&1 || true)
echo "$NEW_AUTO_COMMIT"
echo ""

echo ">>> 对比结果"
if [ "$OLD_AUTO_COMMIT" = "$NEW_AUTO_COMMIT" ]; then
    echo "✓ 结果一致"
    AUTO_COMMIT_MATCH=1
else
    echo "✗ 结果不一致（需人工确认）"
    AUTO_COMMIT_MATCH=0
fi
echo ""

echo "=========================================="
echo "验证总结"
echo "=========================================="
echo "doc-check:       $([ $DOC_MATCH -eq 1 ] && echo '✓ 一致' || echo '✗ 不一致')"
echo "submodule-sync:  $([ $SUBMODULE_MATCH -eq 1 ] && echo '✓ 一致' || echo '✗ 不一致')"
echo "auto-commit:     $([ $AUTO_COMMIT_MATCH -eq 1 ] && echo '✓ 一致' || echo '✗ 不一致')"
echo ""

if [ $DOC_MATCH -eq 1 ] && [ $SUBMODULE_MATCH -eq 1 ] && [ $AUTO_COMMIT_MATCH -eq 1 ]; then
    echo "✓ 所有验证通过，可以进入下一阶段"
    exit 0
else
    echo "✗ 存在不一致，请人工确认后继续"
    exit 1
fi
