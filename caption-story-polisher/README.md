# Caption Story Polisher

一个用于整理中文口播字幕文本的小工具。它会把 DownSub 之类导出的逐行字幕重新排版成更适合阅读的稿件，并同时输出 `.txt` 和 `.docx`。

## 功能

- 自动补充基础中文标点
- 将连续字幕合并成约 200 字左右的段落
- 识别常见故事切换语句，并插入 `------------`
- 生成 UTF-8 文本文件
- 生成 Word `.docx` 文件
- 不依赖第三方 Python 包

## 使用方法

```powershell
python .\caption_story_polisher.py "C:\path\to\subtitle.txt" -o "C:\path\to\output" --stem polished_story
```

输出：

```text
polished_story.txt
polished_story.docx
```

## 示例

```powershell
python .\caption_story_polisher.py "C:\Users\Administrator\Downloads\[Chinese Simplified] ###### [DownSub.com].txt" -o ".\output" --stem horror_ghost_reformatted
```

## 说明

这个工具主要面向中文恐怖故事、灵异电台、口播类字幕。它只做轻量排版和标点补充，不主动改写故事内容。

故事分隔依赖内置关键词，例如：

- `今儿的这个第一个故事咱就到这了`
- `欢迎继续收听灵异电台`
- `马上给您说第二个`
- `接下来马上给您说第三个事`

如果你的字幕里有新的固定切换语句，可以在 `BOUNDARY_KEYWORDS` 中添加。
