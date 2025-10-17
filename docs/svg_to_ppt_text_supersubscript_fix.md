# SVG → PPT 文本上/下标异常清理（VBA 宏）

当把 SVG 导入 PowerPoint 时，某些包含 `<tspan>` 且带基线偏移（baseline-shift）的文本在 PPT 中会被识别为“上标/下标”，导致行高错乱、字符位置抬高或下沉。无需改动 SVG，本页提供一个简单的 VBA 宏，可一键清除整份演示文稿中所有文本段的上标与下标属性，让排版恢复正常。

## 适用场景

- 导入/复制粘贴 SVG 后出现文字“悬空/下沉”、行距异常。
- 将 SVG 转为可编辑对象后，个别字符被自动设置为上标或下标。
- 需要批量恢复所有文本为正常基线、避免逐段手改。

提示：运行前请先备份当前 PPT；该宏仅清理文本的上标/下标属性，不改动字体、字号、颜色与段落样式。

## 使用步骤（Windows/macOS 版 PowerPoint 均可）

1. 打开 PowerPoint，按 `Alt + F11`（Mac 为 `Option + F11`）进入 VBA 编辑器。
2. 在“工程”窗格中选中当前演示文稿，插入一个“模块”（Insert → Module）。
3. 将下方“代码”完整复制并粘贴到该模块中（不要改动代码）。
4. 关闭 VBA 编辑器，回到 PowerPoint。
5. 通过“开发工具 → 宏”（或按 `Alt + F8`），选择并运行 `ClearSuperscriptAndSubscript`。
6. 完成后会有提示弹窗。建议抽样检查包含公式/化学式的文本，确认无误。

## 代码（请勿改动）

```visual basic
Sub ClearSuperscriptAndSubscript()
    Dim sld As Slide
    Dim shp As Shape
    Dim txtRng As TextRange
    Dim i As Long

    For Each sld In ActivePresentation.Slides
        For Each shp In sld.Shapes
            If shp.HasTextFrame Then
                If shp.TextFrame.HasText Then
                    Set txtRng = shp.TextFrame.TextRange
                    For i = 1 To txtRng.Runs.Count
                        With txtRng.Runs(i).Font
                            .Superscript = msoFalse
                            .Subscript = msoFalse
                        End With
                    Next i
                End If
            End If
        Next shp
    Next sld

    MsgBox "��ȡ�������ϱ���±��ʽ��"
End Sub

```

## 常见问题（FAQ）

- 宏安全吗？仅遍历当前文件的形状文本并清除上标/下标标记，不触碰其他属性。
- 只对部分页面生效？请确认这些页面的文本确为“文本框/形状内文字”，而非被转为图片或嵌入对象。
- 运行后依然有错位？可能是原 SVG 的字距/行距或换行方式导致，可在 PPT 中微调段落行距与字符间距。

如需将此步骤加入到你的导入流程中，建议在完成 SVG 放置与基本排版后再运行宏，以避免后续编辑再次引入上/下标属性。

