# 香港分支说明

本分支保留上游 PPT Master，并加上香港工作默认：繁体中文搭配英文、结论先行，以及一套海军蓝配暖白纸的专业身份。它**不是**香港品牌（Brand Hong Kong），也不是任何政府标志。

本文是 `docs/hong-kong.md` 的中文译本。幻灯片正文仍跟随用户语言和来源，不由本文锁定。

## 原先缺了什么

上游目录偏全球咨询品牌和内地国企模板（`中国电信`、`中汽研`、`中国电建`）。语言别名把单独的「中文」当成简体（`zh-Hans`）；单独的 `zh-Hant` 在 Office 里会落成 `zh-TW`。对上游项目这没问题，对香港会议室则不是合适的默认。

2025–2026 年香港专业 PPT 常见做法：

- **两文三语**：书面繁体中文与英文；现场粤语、英语或普通话。
- **规划上结论先行**（BLUF）：先给关键信息，再用 1–3 个支撑，而不是长铺垫。这是组页方法，不是可印上幻灯片的标题或正文。
- **时间盒**：30 分钟的会先问能 cover 哪几件事，而不是塞 60 页。
- **一种语言主导**：第二种语言做较小的副标题、标签或注释，而不是左右各半翻译。
- **商务蓝、深灰、白底**。内地政府 / 国企红金模板在港式场合会显得不对口径。
- 中文用繁体安全字体（`Microsoft JhengHei`、`PingFang HK`），英文单独成框，或统一用 CJK 安全字体。
- 结尾是**有负责人的行动项**和真正的 Q&A，而不是谢谢观看。
- **中英口吻都跟香港上市公司公告走**：港式英式商务英文和港式书面语，而不是美式咨询英文、口语粤语、台湾用词或内地政策口号中文。汇丰香港、国泰、香港赛马会的公开新闻稿是语域参照：一个主体、一项具名行动、一个数字或日期。本分支不复制这些机构的品牌规范、标志或口号。

香港品牌飞龙、丝带色谱、「亚洲国际都会」以及区旗区徽均受保护。本分支不复制它们。

## 本分支新增

| 类型 | ID | 工作区 | 适用 |
|---|---|---|---|
| Brand | `harbour-professional` | `skills/ppt-master/templates/brands/harbour-professional/` | 没有客户品牌、需要港式专业身份时 |
| Style | `hk-bilingual-board` | `skills/ppt-master/templates/styles/hk-bilingual-board/` | 董事会文件、IR / 业绩、委员会决策、经营回顾 |
| Style | `hk-client-pitch` | `skills/ppt-master/templates/styles/hk-client-pitch/` | 客户提案和 30–45 分钟现场汇报 |

客户提供的品牌、官方手册或现有 PPTX 身份一律优先于 Harbour Professional。需要 Master/Layout 结构时，可把上述 Style 与 [`report_core`](../../skills/ppt-master/templates/layouts/report_core/) 搭配；否则 Brand + Style 保持幻灯片本地（`flat`）。

`Cantonese`、`港式中文`、`香港中文` 等别名会规范成 `zh-HK`，以便 Office 校对、东亚字体（`Microsoft JhengHei`）和粤语神经网络语音对齐。

## 怎么提出生成请求

必须给精确工作区路径，不能只报品牌或风格名称。路由不会把名称当成选定。

董事会 / IR：

```text
Make a board paper from <sources>.
Primary language: zh-HK.
Brand workspace: skills/ppt-master/templates/brands/harbour-professional/
Style workspace: skills/ppt-master/templates/styles/hk-bilingual-board/
```

客户提案：

```text
Make a client pitch from <sources>.
Primary language: zh-HK.
Brand workspace: skills/ppt-master/templates/brands/harbour-professional/
Style workspace: skills/ppt-master/templates/styles/hk-client-pitch/
```

已有 PPTX（备注、美化或局部改页）仍走原有路由：必须保留原貌时用 Edit Native PPTX；内容冻结、版式重做时用 Beautify；论点是新的时用 Generate。

受众在内地时请明确说出来，改用简体和相应客户品牌，而不要沿用本默认。

## 口吻

Harbour Professional 的 Voice & Tone 是**中英两种语言**的正文合同。每一种语言都应能单独当作香港上市公司新闻稿标题发出：主体 + 行动 + 数字或日期。不要把一种语言机翻成另一种。Style 的 Argument Flow、BLUF、时间盒、「港式会议室要结论先行」是规划说明，不是幻灯片正文。具名主体写 `the Board` / `the Committee` / `本港` / `委員會`，不要在页上自称 `港式`。

**英文**是港式英式商务英文（`organisation`、`programme`、`the Group today announced`，IR 正文里写 `per cent`），不是美式拼写，也不是硅谷腔。

| 不要（美式 / AI 英文） | 要（港式英文） |
|---|---|
| We're excited to roll out the program | The Group today announced the programme for eligible customers |
| Reach out to users to unlock value | Please contact eligible customers with effect from 28 October 2026 |
| Unlock a seamless digital journey | Launch the service for eligible corporate clients in Hong Kong on 23 October 2026 |
| Key message first / HK rooms want the answer first | Recommend the Committee adopt editable PPTX as the paper format with effect from 28 October 2026 |

**中文**是港式书面语：繁体、规范书面中文加香港专业用词（`今天宣布`、`本集團`、`本港`、`客戶`、`港元`、`較去年同期`、`行政總裁`、`溢利`、`數碼化`、`軟件`）。幻灯片正文不是口语粤语，不是台湾用词（`軟體`、`網路`、`執行長`），也不是内地口号中文。

| 不要（内地 / 台湾 / 口语） | 要（港式书面语） |
|---|---|
| `賦能數字化轉型，打造一站式生態` | `建議批准九十萬港元，於九十日內完成試點` |
| `我們很高興推出軟體給用戶` | `本集團今天公布有關軟件，供合資格客戶使用` |
| `而家我哋好興奮宣布` | `本集團今天宣布` |
| `開啟智能新篇章` | `本季旅客量較去年同期升百分之十二` |
| `結論先行` / `先給答案，再用一至三個支撐` / `長鋪墊在港式會議室是延遲` | `建議委員會於下次會議前批准可編輯 PPTX 為文件格式` |

口语粤语用在粤语旁白，不写进幻灯片正文。去掉堆叠的英文加强词（`leverage`、`empower`、`our journey`）和内地口号中文（`賦能`、`抓手`、`落地`、`閉環`、`打造生態`），除非来源本身在引用具名产品或政策。
