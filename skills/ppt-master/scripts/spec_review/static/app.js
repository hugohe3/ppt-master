'use strict';

const strings = {
  en: {
    first: 'First', prev: 'Prev', next: 'Next', last: 'Last', source: 'View source', rendered: 'Rendered view',
    reload: 'Reload from disk', editor: 'Block Markdown', apply: 'Apply changes', undo: 'Discard draft',
    rebase: 'Use current disk as draft base', annotations: 'Annotations', thisBlock: 'This block', global: 'Global',
    newAnnotation: 'New annotation', saveAnnotation: 'Save annotation', save: 'Update', remove: 'Delete',
    annotationHint: 'Annotations are saved separately from the Design Spec.',
    structureHint: 'Keep section headings and Slide levels/numbers. Part blocks allow title text edits only. Request page additions, deletions, or reordering in annotations.',
    hold: 'AI is editing — Apply is paused.', changed: 'The spec changed on disk. Reload to read the latest version.',
    conflict: 'The spec changed. Drafts are retained; reload and review the current source before choosing a new draft base.',
    pending: 'Unapplied draft', staging: 'Staging…', clean: 'No draft', saved: 'Saved', validation: 'Schema diagnostics (saved)',
    missing: 'This block was removed externally. Its draft is retained for copying or discarding.',
    stale: 'Base differs from current spec', current: 'Base matches current spec', comments: 'Comments', draft: 'Draft',
    blockChanged: 'This block changed since the comment was created', blockUnchanged: 'This block is unchanged since the comment was created',
    blockUnknown: 'Block baseline unknown', blockMissing: 'This block no longer exists',
    exit: 'Exit review', exitConfirm: 'There are unapplied drafts or unsaved comments. Stop review and discard pending work?',
    stopped: 'Spec review has stopped. You can close this tab.',
    disconnected: 'Cannot reach spec review. Local edits are retained.', rebaseConfirm: 'Stage this text against the current disk version, replacing any current staged draft? Review the source first; Apply will replace this block.',
  },
  zh: {
    first: '首块', prev: '上一块', next: '下一块', last: '末块', source: '查看原文', rendered: '渲染视图',
    reload: '重载磁盘原文', editor: '块 Markdown', apply: '应用更改', undo: '撤销草稿', rebase: '以当前磁盘版本为草稿基准',
    annotations: '修改意见', thisBlock: '当前块', global: '全局', newAnnotation: '新增意见', saveAnnotation: '保存意见',
    save: '更新', remove: '删除', annotationHint: '意见独立保存，不写入 Design Spec。',
    structureHint: '保留章节标题及 Slide 层级和编号；Part 块仅可改标题文字。增页、删页、调序请写修改意见。',
    hold: 'AI 正在修改，已暂停应用更改。', changed: '磁盘原文已变化，请重载查看最新版本。',
    conflict: '原文已变化，草稿已保留；请重载并核对最新原文，再选择新的草稿基准。',
    pending: '有未应用草稿', staging: '暂存中…', clean: '无草稿', saved: '已保存', validation: '校验提示（已保存）',
    missing: '该块已被外部删除，草稿仍可复制或撤销。',
    stale: '基准与当前原文不同', current: '基准与当前原文相同', comments: '意见', draft: '草稿',
    blockChanged: '该块自意见创建后已变化', blockUnchanged: '该块自意见创建后未变化',
    blockUnknown: '该块的意见基准未知', blockMissing: '该块已不存在',
    exit: '退出评审', exitConfirm: '存在未应用草稿或未保存意见。是否停止评审并放弃待保存内容？',
    stopped: '评审服务已停止，可以关闭此标签页。',
    disconnected: '无法连接评审服务，本地编辑已保留。', rebaseConfirm: '以当前磁盘版本为基准暂存此内容，替换服务端的当前草稿？请先核对最新原文；应用时将替换该块。',
  },
  'zh-TW': {
    first: '首塊', prev: '上一塊', next: '下一塊', last: '末塊', source: '查看原文', rendered: '算繪檢視',
    reload: '重新載入磁碟原文', editor: '區塊 Markdown', apply: '套用變更', undo: '撤銷草稿', rebase: '以目前磁碟版本為草稿基準',
    annotations: '修改意見', thisBlock: '目前區塊', global: '全域', newAnnotation: '新增意見', saveAnnotation: '儲存意見',
    save: '更新', remove: '刪除', annotationHint: '意見獨立儲存，不寫入 Design Spec。',
    structureHint: '保留章節標題及 Slide 層級和編號；Part 區塊僅可改標題文字。增頁、刪頁、調序請寫修改意見。',
    hold: 'AI 正在修改，已暫停套用變更。', changed: '磁碟原文已變更，請重新載入最新版本。',
    conflict: '原文已變更，草稿已保留；請重新載入並核對原文，再選擇新的草稿基準。',
    pending: '有未套用草稿', staging: '暫存中…', clean: '無草稿', saved: '已儲存', validation: '驗證提示（已儲存）',
    missing: '該區塊已被外部刪除，草稿仍可複製或撤銷。',
    stale: '基準與目前原文不同', current: '基準與目前原文相同', comments: '意見', draft: '草稿',
    blockChanged: '該區塊自意見建立後已變更', blockUnchanged: '該區塊自意見建立後未變更',
    blockUnknown: '該區塊的意見基準未知', blockMissing: '該區塊已不存在',
    exit: '退出評審', exitConfirm: '存在未套用草稿或未儲存意見。是否停止評審並放棄待儲存內容？',
    stopped: '評審服務已停止，可以關閉此分頁。',
    disconnected: '無法連線評審服務，本機編輯已保留。', rebaseConfirm: '以目前磁碟版本為基準暫存此內容，取代伺服器上的目前草稿？請先核對最新原文；套用時將取代該區塊。',
  },
  ja: {
    first: '先頭', prev: '前へ', next: '次へ', last: '末尾', source: '原文を表示', rendered: '表示に戻る',
    reload: 'ディスクから再読込', editor: 'ブロック Markdown', apply: '変更を適用', undo: '下書きを破棄',
    rebase: '現在の原文を下書きの基準にする', annotations: '修正コメント', thisBlock: '現在のブロック', global: '全体',
    newAnnotation: '新しいコメント', saveAnnotation: 'コメントを保存', save: '更新', remove: '削除',
    annotationHint: 'コメントは Design Spec と別に保存されます。',
    structureHint: 'セクション見出しと Slide の階層・番号は固定です。Part は見出しの文字だけ変更できます。追加・削除・並べ替えはコメントで依頼してください。',
    hold: 'AI が編集中です。変更の適用は一時停止中です。', changed: '原文が変更されました。再読込してください。',
    conflict: '原文が変更されました。下書きは保持されています。再読込して原文を確認し、新しい基準を選択してください。',
    pending: '未適用の下書き', staging: '一時保存中…', clean: '下書きなし', saved: '保存済み', validation: '検証結果（保存済み）',
    missing: 'このブロックは外部で削除されました。下書きはコピーまたは破棄できます。',
    stale: '基準が現在の原文と異なります', current: '基準は現在の原文と一致', comments: 'コメント', draft: '下書き',
    blockChanged: 'コメント作成後にこのブロックは変更されています', blockUnchanged: 'コメント作成後にこのブロックは変更されていません',
    blockUnknown: 'ブロックの基準は不明です', blockMissing: 'このブロックは存在しません',
    exit: 'レビューを終了', exitConfirm: '未適用の下書きまたは未保存のコメントがあります。レビューを終了して未保存の内容を破棄しますか？',
    stopped: 'レビューサービスは停止しました。このタブを閉じてください。',
    disconnected: 'サービスに接続できません。編集内容は保持されています。', rebaseConfirm: '現在の原文を基準にこの内容を一時保存し、サーバーの下書きを置き換えますか？原文を先に確認してください。適用でこのブロックを置き換えます。',
  },
};
const $ = id => document.getElementById(id);
const node = (tag, text) => {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  return result;
};
const detected = navigator.language.toLowerCase();
let lang = detected.startsWith('zh') ? (/tw|hk|hant/.test(detected) ? 'zh-TW' : 'zh') :
  (detected.startsWith('ja') ? 'ja' : 'en');
try { lang = localStorage.getItem('spec-review-language') || lang; } catch (_) { /* Optional browser storage. */ }
if (!strings[lang]) lang = 'en';
const t = key => strings[lang][key];

// User Markdown never crosses an HTML parser boundary. Unsupported constructs
// remain literal text; links and image syntax never create active elements.
function inline(parent, text, depth = 0) {
  // Bound regex backtracking even for long runs of unmatched delimiters.
  if (depth > 12 || text.length > 4096) { parent.append(document.createTextNode(text)); return; }
  const pattern = /(`+)(.+?)\1|\*\*(.+?)\*\*|__(.+?)__|\*([^*]+)\*|_([^_]+)_|(\$[^$\n]+\$|\\\([^\n]*?\\\))/g;
  let start = 0;
  for (const match of text.matchAll(pattern)) {
    parent.append(document.createTextNode(text.slice(start, match.index)));
    const tag = match[1] || match[7] ? 'code' : (match[3] || match[4] ? 'strong' : 'em');
    const child = node(tag);
    const value = match[2] || match[3] || match[4] || match[5] || match[6] || match[7];
    if (tag === 'code') child.textContent = value;
    else inline(child, value, depth + 1);
    parent.append(child);
    start = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(start)));
}

const listItem = line => /^( *)([-+*]|\d+[.)])\s+(.*)$/.exec(line);
const fenceLine = line => /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
function tableCells(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split(/(?<!\\)\|/).map(cell => cell.trim());
}

function markdown(text, target, depth = 0) {
  if (depth > 12) { target.append(node('pre', text)); return; }
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  let i = 0;
  function list(indent, nesting = 0) {
    if (nesting > 12) {
      const body = [];
      while (i < lines.length && lines[i].search(/\S/) >= indent) body.push(lines[i++]);
      return node('pre', body.join('\n'));
    }
    const first = listItem(lines[i]);
    const ordered = /^\d/.test(first[2]);
    const container = node(ordered ? 'ol' : 'ul');
    if (ordered) container.start = parseInt(first[2], 10);
    while (i < lines.length) {
      const item = listItem(lines[i]);
      if (!item || item[1].length !== indent || /^\d/.test(item[2]) !== ordered) break;
      const li = node('li'); inline(li, item[3]); container.append(li); i++;
      while (i < lines.length) {
        const next = listItem(lines[i]);
        if (next && next[1].length > indent) { li.append(list(next[1].length, nesting + 1)); continue; }
        if (!next && lines[i].trim() && lines[i].search(/\S/) > indent) {
          li.append(node('pre', lines[i++])); continue;
        }
        break;
      }
    }
    return container;
  }
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    const fence = fenceLine(line);
    if (fence && !(fence[1][0] === '`' && fence[2].includes('`'))) {
      const body = []; i++;
      while (i < lines.length) {
        const closing = fenceLine(lines[i]);
        if (closing && closing[1][0] === fence[1][0] && closing[1].length >= fence[1].length && !closing[2].trim()) {
          i++; break;
        }
        body.push(lines[i++]);
      }
      const pre = node('pre'); pre.append(node('code', body.join('\n'))); target.append(pre); continue;
    }
    if (/^\s*(\$\$|\\\[|\\begin\{)/.test(line)) {
      const body = [line]; i++;
      const end = line.trim().startsWith('$$') ? '$$' : (line.includes('\\[') ? '\\]' : '\\end{');
      if (!line.trim().slice(2).includes(end)) {
        while (i < lines.length) { const part = lines[i++]; body.push(part); if (part.includes(end)) break; }
      }
      target.append(node('pre', body.join('\n'))); continue;
    }
    const heading = /^ {0,3}(#{1,6})\s+(.*)$/.exec(line);
    if (heading) { const h = node('h' + heading[1].length); inline(h, heading[2]); target.append(h); i++; continue; }
    if (/^ {0,3}((\*\s*){3,}|(-\s*){3,}|(_\s*){3,})$/.test(line)) { target.append(node('hr')); i++; continue; }
    if (/^ {0,3}>/.test(line)) {
      const body = [];
      while (i < lines.length && /^ {0,3}>/.test(lines[i])) body.push(lines[i++].replace(/^ {0,3}> ?/, ''));
      const quote = node('blockquote'); markdown(body.join('\n'), quote, depth + 1); target.append(quote); continue;
    }
    if (line.includes('|') && i + 1 < lines.length && tableCells(lines[i + 1]).every(cell => /^:?-{3,}:?$/.test(cell))) {
      const table = node('table'); const head = node('thead'); const row = node('tr');
      tableCells(line).forEach(cell => { const th = node('th'); inline(th, cell); row.append(th); });
      head.append(row); table.append(head); const body = node('tbody'); i += 2;
      while (i < lines.length && lines[i].trim() && lines[i].includes('|')) {
        const tr = node('tr');
        tableCells(lines[i++]).forEach(cell => { const td = node('td'); inline(td, cell); tr.append(td); });
        body.append(tr);
      }
      table.append(body); target.append(table); continue;
    }
    const item = listItem(line);
    if (item) { target.append(list(item[1].length)); continue; }
    if (/^( {4}|\t)|^\s*(<|!\[|\[\^|\[.+\]:|[|]|:::|\\|={3,}\s*$)/.test(line)) {
      target.append(node('pre', line)); i++; continue;
    }
    const body = [line]; i++;
    while (i < lines.length && lines[i].trim() && !listItem(lines[i]) && !fenceLine(lines[i]) &&
           !/^\s*(#|>|\||<|!\[|\[|\\|\$\$|:::|[-*_]{3,}|={3,})|^( {4}|\t)/.test(lines[i]) &&
           !(lines[i].includes('|') && i + 1 < lines.length &&
             tableCells(lines[i + 1]).every(cell => /^:?-{3,}:?$/.test(cell)))) {
      body.push(lines[i++]);
    }
    const paragraph = node('p'); inline(paragraph, body.join('\n')); target.append(paragraph);
  }
}

let metadata = {blocks: [], orphan_drafts: [], draft_keys: [], sha256: '', hold: false, hold_revision: 0};
let current = null;
let source = false;
let stageTimer;
let stopped = false;
let applying = false;
let queue = Promise.resolve();
const drafts = new Map();
const annotationBuffers = new Map();
let comments = [];
const pathKey = key => encodeURIComponent(key);
const hasDrafts = () => drafts.size > 0 || metadata.draft_keys.length > 0;
const annotationKey = () => $('scope').value === 'global' ? 'global' : current?.key;
function navigationBlocks() {
  const blocks = [...metadata.blocks, ...metadata.orphan_drafts];
  for (const [key, draft] of drafts) {
    if (!blocks.some(block => block.key === key)) blocks.push({key, title: draft.title || key, kind: 'missing'});
  }
  return blocks;
}

async function api(path, method = 'GET', data) {
  let response;
  try {
    response = await fetch(path, {method, cache: 'no-store', headers: {'Content-Type': 'application/json'},
      body: data === undefined ? undefined : JSON.stringify(data)});
  } catch (_) { throw new Error(t('disconnected')); }
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(result.error || String(response.status)); error.status = response.status; throw error;
  }
  return result;
}
function showError(error) {
  $('error').textContent = error.message; $('error').hidden = false;
  if (error.status === 409) showConflict(true);
  if (error.status === 423) { metadata.hold = true; renderStatus(); }
}
function run(action) {
  queue = queue.then(() => { if (!stopped) return action(); }).catch(showError);
  return queue;
}
function showConflict(conflict = hasDrafts()) {
  $('conflict').textContent = t(conflict ? 'conflict' : 'changed'); $('conflict').hidden = false;
}
function renderStatus() {
  $('hold').textContent = t('hold'); $('hold').hidden = !metadata.hold;
  const draft = drafts.get(current?.key);
  $('draft-status').textContent = t(draft?.dirty ? 'staging' : (draft ? 'pending' : 'clean'));
  $('editor').disabled = applying || !current;
  $('apply').disabled = applying || !draft || metadata.hold || current?.missing;
  $('undo').disabled = applying || !draft;
  $('rebase').disabled = applying;
  $('rebase').hidden = !draft || current?.missing || (draft.sha256 === current?.sha256 &&
    (draft.version || null) === (current?.draft?.version || null));
  $('fingerprint').textContent = current?.sha256 ?? metadata.sha256;
}
function renderNavigation() {
  $('blocks').replaceChildren();
  const blocks = navigationBlocks();
  blocks.forEach(block => {
    const button = node('button', block.title.replace(/^\s*#+\s*/, ''));
    button.className = [block.kind, block.key === current?.key ? 'selected' : ''].join(' ');
    if (block.key === current?.key) button.setAttribute('aria-current', 'true');
    if (block.has_annotations) button.append(Object.assign(node('span', t('comments')), {className: 'badge'}));
    if (block.has_draft || drafts.has(block.key)) button.append(Object.assign(node('span', t('draft')), {className: 'badge'}));
    button.addEventListener('click', () => navigate(block.key)); $('blocks').append(button);
  });
  const index = blocks.findIndex(block => block.key === current?.key);
  $('position').textContent = blocks.length ? `${index + 1} / ${blocks.length}` : '0 / 0';
  $('first').disabled = $('prev').disabled = index <= 0;
  $('next').disabled = $('last').disabled = index >= blocks.length - 1;
}
function renderPreview() {
  const text = drafts.get(current?.key)?.text ?? current?.text ?? '';
  $('preview').replaceChildren();
  try { markdown(text, $('preview')); }
  catch (_) { $('preview').replaceChildren(node('pre', text)); }
  // Source view always shows the current disk block, so a stale draft can be
  // compared with its replacement before explicitly choosing a new base.
  $('raw').textContent = current?.text || '';
  $('raw').hidden = !source; $('preview').hidden = source;
  $('source').textContent = t(source ? 'rendered' : 'source');
  $('source').setAttribute('aria-pressed', String(source));
}
async function stage(key, text = drafts.get(key)?.text) {
  const draft = drafts.get(key);
  if (!draft) return;
  if (!draft.dirty && draft.text === text) return {...draft};
  const result = await api('/api/drafts/' + pathKey(key), 'PUT', {
    text, sha256: draft.sha256, version: draft.version || null,
  });
  draft.version = result.version;
  draft.dirty = draft.text !== text;
  if (current?.key === key) current.draft = result;
  if (!metadata.draft_keys.includes(key)) metadata.draft_keys.push(key);
  renderStatus(); renderNavigation();
  return result;
}
async function loadComments() {
  comments = (await api('/api/annotations')).annotations; renderComments();
}
function renderComments() {
  $('comments').replaceChildren();
  for (const item of comments.filter(item => item.key === annotationKey())) {
    const card = node('div'); card.className = 'comment';
    card.append(node('small', `${item.id} · ${item.title}`));
    const status = item.key === 'global' ? (item.base_current ? 'current' : 'stale') :
      (item.block_missing ? 'blockMissing' : (item.block_changed === true ? 'blockChanged' :
        (item.block_changed === false ? 'blockUnchanged' : 'blockUnknown')));
    card.append(node('small', t(status)));
    const textarea = node('textarea'); textarea.rows = 4; textarea.value = annotationBuffers.get(item.id) ?? item.body;
    textarea.addEventListener('input', () => annotationBuffers.set(item.id, textarea.value)); card.append(textarea);
    const buttons = node('div'); buttons.className = 'toolbar';
    const save = node('button', t('save')); const remove = node('button', t('remove'));
    save.addEventListener('click', () => {
      const body = textarea.value;
      run(async () => {
        const result = await api('/api/annotations/' + item.id, 'PUT', {body, revision: item.revision});
        Object.assign(item, result);
        if (annotationBuffers.get(item.id) === body) annotationBuffers.delete(item.id);
        await refreshMetadata(); await loadComments();
      });
    });
    remove.addEventListener('click', () => run(async () => {
      await api('/api/annotations/' + item.id, 'DELETE', {revision: item.revision});
      annotationBuffers.delete(item.id); await refreshMetadata(); await loadComments();
    }));
    buttons.append(save, remove); card.append(buttons); $('comments').append(card);
  }
  $('annotation').value = annotationBuffers.get('new:' + annotationKey()) || '';
}
async function refreshMetadata() {
  metadata = await api('/api/blocks');
  if (current && current.sha256 !== metadata.sha256) showConflict();
  renderNavigation(); renderStatus();
}
async function select(key) {
  if (!key) { current = null; $('editor').disabled = true; renderStatus(); return; }
  let block;
  try { block = await api('/api/blocks/' + pathKey(key)); }
  catch (error) {
    if (error.status !== 404 || !drafts.has(key)) throw error;
    block = {key, title: drafts.get(key).title || key, text: '', sha256: metadata.sha256, missing: true};
  }
  current = block;
  if (block.draft && !drafts.has(key)) drafts.set(key, {...block.draft, dirty: false});
  const draft = drafts.get(key);
  if (draft && block.draft && !draft.dirty && draft.version === block.draft.version) {
    draft.sha256 = block.draft.sha256;
  }
  $('title').textContent = block.title;
  $('editor').value = draft?.text ?? block.text; $('editor').disabled = false; $('editor').readOnly = !!block.missing;
  renderPreview(); renderNavigation(); renderStatus(); renderComments();
  if (draft && draft.sha256 !== block.sha256) showConflict(true);
  if (block.missing) { $('conflict').textContent = t('missing'); $('conflict').hidden = false; }
}
function navigate(key) {
  run(async () => {
    clearTimeout(stageTimer);
    if (current) await stage(current.key).catch(showError);
    await select(key);
  });
}
async function reload() {
  const key = current?.key;
  await refreshMetadata();
  $('conflict').hidden = true;
  const blocks = navigationBlocks();
  await select(blocks.some(block => block.key === key) ? key : blocks[0]?.key);
  await loadComments();
  if ([...drafts.values()].some(draft => draft.sha256 !== metadata.sha256)) showConflict(true);
}
function localize() {
  document.documentElement.lang = lang; $('language').value = lang;
  document.querySelectorAll('[data-label]').forEach(element => { element.textContent = t(element.dataset.label); });
  if (stopped) { $('stopped').textContent = t('stopped'); return; }
  renderStatus(); renderNavigation(); renderPreview(); renderComments();
  if (!$('conflict').hidden) showConflict();
}

$('language').addEventListener('change', () => {
  lang = $('language').value;
  try { localStorage.setItem('spec-review-language', lang); } catch (_) { /* Optional browser storage. */ }
  localize();
});
$('source').addEventListener('click', () => { source = !source; renderPreview(); });
$('reload').addEventListener('click', () => run(reload));
$('exit').addEventListener('click', () => run(async () => {
  await refreshMetadata();
  if ((hasDrafts() || [...annotationBuffers.values()].some(Boolean)) && !window.confirm(t('exitConfirm'))) return;
  clearTimeout(stageTimer);
  await api('/api/shutdown', 'POST', {});
  stopped = true; clearInterval(pollTimer);
  document.querySelector('.workspace').hidden = true;
  for (const id of ['hold', 'conflict', 'error', 'exit']) $(id).hidden = true;
  $('fingerprint').textContent = '';
  $('stopped').textContent = t('stopped'); $('stopped').hidden = false;
}));
$('scope').addEventListener('change', renderComments);
$('annotation').addEventListener('input', () => annotationBuffers.set('new:' + annotationKey(), $('annotation').value));
$('editor').addEventListener('input', () => {
  if (!current) return;
  const key = current.key;
  const draft = drafts.get(key) || {sha256: current.sha256, version: null, title: current.title};
  Object.assign(draft, {text: $('editor').value, dirty: true}); drafts.set(key, draft);
  renderPreview(); renderStatus(); renderNavigation();
  clearTimeout(stageTimer); stageTimer = setTimeout(() => run(() => stage(key)), 350);
});
$('apply').addEventListener('click', () => {
  const key = current?.key; const draft = drafts.get(key);
  if (!draft || applying) return;
  const snapshot = {...draft};
  applying = true; clearTimeout(stageTimer); renderStatus();
  run(async () => {
    try {
      if (drafts.get(key) !== draft) { showConflict(true); return; }
      // The queue awaits earlier stages; stage this click's text with their returned version.
      const staged = await stage(key, snapshot.text); const base = staged.sha256;
      const result = await api('/api/apply/' + pathKey(key), 'POST', {sha256: base, version: staged.version});
      if (draft.text === snapshot.text) drafts.delete(key);
      else Object.assign(draft, {version: null, dirty: true});
      for (const other of drafts.values()) if (other.sha256 === base) other.sha256 = result.sha256;
      $('validation-errors').textContent = result.validation_errors.join('\n');
      $('validation').hidden = result.validation_errors.length === 0;
      $('error').hidden = true; await reload();
      if (current?.key === key && !drafts.has(key)) $('draft-status').textContent = t('saved');
    } finally { applying = false; renderStatus(); }
  });
});
$('undo').addEventListener('click', () => run(async () => {
  const key = current.key; const draft = drafts.get(key);
  const latest = current.missing && !draft?.version ? current : await api('/api/blocks/' + pathKey(key));
  if (draft?.version && draft.version === latest.draft?.version) {
    await api('/api/drafts/' + pathKey(key), 'DELETE', {version: draft.version});
  }
  drafts.delete(key); $('error').hidden = true; await reload();
}));
$('rebase').addEventListener('click', () => run(async () => {
  if (!window.confirm(t('rebaseConfirm'))) return;
  const draft = drafts.get(current.key);
  const latest = await api('/api/blocks/' + pathKey(current.key));
  if (latest.sha256 !== current.sha256 || (latest.draft?.version || null) !== (current.draft?.version || null)) {
    await reload(); showConflict(true); return;
  }
  const text = draft.text;
  const result = await api('/api/drafts/' + pathKey(current.key), 'PUT', {
    text, sha256: latest.sha256, version: latest.draft?.version || null,
  });
  Object.assign(draft, {sha256: result.sha256, version: result.version, dirty: draft.text !== text});
  $('error').hidden = true; await reload();
}));
$('add').addEventListener('click', () => {
  const key = annotationKey(); const body = annotationBuffers.get('new:' + key) || '';
  run(async () => {
    await api('/api/annotations', 'POST', {key, body});
    if (annotationBuffers.get('new:' + key) === body) annotationBuffers.delete('new:' + key);
    await refreshMetadata(); await loadComments();
  });
});
function step(direction) {
  const blocks = navigationBlocks();
  const index = blocks.findIndex(block => block.key === current?.key);
  const next = direction === 'first' ? 0 : (direction === 'last' ? blocks.length - 1 : index + direction);
  if (blocks[next]) navigate(blocks[next].key);
}
for (const [id, direction] of [['first', 'first'], ['prev', -1], ['next', 1], ['last', 'last']]) {
  $(id).addEventListener('click', () => step(direction));
}
document.addEventListener('keydown', event => {
  if (stopped) return;
  if (event.target.closest('input, textarea, select, [contenteditable]') || event.ctrlKey || event.metaKey || event.altKey) return;
  const action = {ArrowLeft: -1, ArrowRight: 1, Home: 'first', End: 'last'}[event.key];
  if (action !== undefined) { event.preventDefault(); step(action); }
});
window.addEventListener('beforeunload', event => {
  if (!stopped && (hasDrafts() || [...annotationBuffers.values()].some(Boolean))) {
    event.preventDefault(); event.returnValue = '';
  }
});
let polling = false;
const pollTimer = setInterval(async () => {
  if (polling || stopped) return;
  polling = true;
  try {
    const state = await api('/api/state');
    if (stopped) return;
    const released = !state.hold && state.hold_revision !== metadata.hold_revision;
    metadata.hold = state.hold; metadata.hold_revision = state.hold_revision;
    renderStatus();
    if (released) await run(reload);
    else if (state.sha256 !== (current?.sha256 ?? metadata.sha256)) showConflict();
  } catch (error) { if (!stopped) showError(error); }
  finally { polling = false; }
}, 2000);
localize(); run(reload);
