# 苹果备忘录模块开发经验

## 概述

实现苹果备忘录（Apple Notes）数据导入功能，存入 `data/infra/apple/` 目录。

## 踩坑记录

### 1. 直接读取 SQLite 数据库失败

**尝试方案：** 直接读取 `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`

**问题：** `authorization denied` - macOS 限制了直接访问

**结论：** 此路不通

### 2. AppleScript 获取所有备忘录超时

**尝试方案：** 使用 `repeat with n in every note` 获取全部备忘录

**问题：** 超时（timeout），备忘录数量太多（1289条），AppleScript 执行太慢

**结论：** 需要限制数量

### 3. AppleScript 多行参数问题

**尝试方案：** 将 AppleScript 写成单行字符串

**问题：** 语法错误，特别是 `notes 1 thru 100` 这样的范围语法

**解决：** 使用多行 `-e` 参数方式：
```python
script_lines = [
    'tell application "Notes"',
    'set n to notes 1 thru 10',
    'set names to {}',
    'repeat with x in n',
    'set end of names to name of x',
    'end repeat',
    'return names',
    'end tell',
]
args = ["osascript"]
for line in script_lines:
    args.extend(["-e", line])
subprocess.run(args, ...)
```

### 4. Python 模块中调用 osascript 行为不一致

**问题：** 直接在命令行运行 `osascript` 正常，但在 Python subprocess 中调用同一函数时返回空结果

**调试方法：** 逐步打印每个步骤的返回值，定位问题

**结论：** 需要仔细检查 subprocess 参数和返回值处理

### 5. 路径计算问题

**问题：** `Path(__file__).parent.parent.parent` 的层级计算错误

**解决：** 
- infra/apple.py 位于 `src/thera/infra/apple.py`
- parent = `src/thera/infra`
- parent.parent = `src/thera`
- parent.parent.parent = `src`
- parent.parent.parent.parent = 项目根目录

最终正确路径：`Path(__file__).parent.parent.parent.parent / "data" / "infra" / "apple"`

**建议：** 先用测试脚本验证路径是否正确

## 经验总结

1. **macOS 系统应用交互优先考虑 AppleScript** - 系统原生支持，权限控制相对宽松

2. **AppleScript 操作大量数据会超时** - 需要分批获取或使用 Shortcut

3. **调试 subprocess 时分段打印** - 特别是在复杂环境下，先验证单步执行再集成

4. **路径计算务必验证** - 不同项目结构层级不同，写完代码后实际运行检查

5. **Shortcut 是更优方案** - 创建「获取所有备忘录」Shortcut 可一次性获取完整数据，性能更好

6. **AppleScript 输出格式解析问题**

**问题：** AppleScript 返回的列表格式不便于解析

**解决：** 使用特殊分隔符（如 "###"）连接标题和内容
```python
set noteText to "###" & noteTitle & "###" & noteBody
```
然后在 Python 中按分隔符拆分：
```python
items = output.split(", ###")
for item in items:
    if "###" in item:
        title, body = item.split("###", 1)
```

7. **获取指定文件夹的备忘录**

**需求：** 只需要"思考"文件夹的数据

**解决：** 使用 `folder "文件夹名"` 语法指定文件夹
```applescript
set targetFolder to folder "思考"
repeat with n in every note in targetFolder
    ...
end repeat
```

**最终导出结果：**
- 32 条"思考"文件夹备忘录
- 包含标题和完整内容
- 保存到 `data/infra/apple/notes.json`

8. **删除冗余的 summary.json**

**经验：** summary.json 内容和 notes.json 重复，直接从 notes.json 读取即可

**解决：** 删除 summary.json，简化逻辑
