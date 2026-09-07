# GUIデザイン設計書：カウンセラー検索AIデモ

## 1. デザインコンセプト・トーン&マナー

| 要素 | 方針 |
|------|------|
| **コンセプト** | 「相談しやすさ」を最優先。無機質な検索フォームではなく、人と話すような安心感のあるチャット体験 |
| **トーン** | 優しい・信頼感・落ち着き・専門的すぎない |
| **キーワード** | 寄り添う・シンプル・迷わない・安心 |

---

## 2. カラーパレット

### 2.1 メインカラー

| 役割 | カラー | HEX | 用途 |
|------|--------|-----|------|
| Primary | 青緑系 | `#2A9D8F` | ヘッダー・送信ボタン・リンク・アクセント |
| Primary Dark | 濃い青緑 | `#1E7D71` | ホバー・アクティブ状態 |
| Primary Light | 薄い青緑 | `#E0F4F1` | AIメッセージ背景・バッジ背景 |

### 2.2 セマンティックカラー

| 役割 | カラー | HEX | 用途 |
|------|--------|-----|------|
| Background | オフホワイト | `#FAFAFA` | 画面全体背景 |
| Surface | 白 | `#FFFFFF` | メッセージバブル・カード・入力エリア |
| Text Primary | 濃いグレー | `#1F2937` | 本文・ユーザーメッセージテキスト |
| Text Secondary | 中グレー | `#6B7280` | タイムスタンプ・補助説明・プレースホルダー |
| Text Muted | 薄グレー | `#9CA3AF` | システムメッセージ・ヒント |
| Border | 薄グレー | `#E5E7EB` | 区切り線・入力枠 |
| User Bubble | 青緑 | `#2A9D8F` | ユーザーメッセージ背景 |
| User Text | 白 | `#FFFFFF` | ユーザーメッセージテキスト |
| AI Bubble | 薄青緑 | `#E0F4F1` | AIメッセージ背景 |
| AI Text | 濃いグレー | `#1F2937` | AIメッセージテキスト |
| Error | 赤系 | `#EF4444` | エラーメッセージ・送信失敗 |
| Warning | 琥珀 | `#F59E0B` | 注意喚起・リトライ表示 |
| Success | 緑系 | `#10B981` | 完了・成功ステータス |

### 2.3 ダークモード対応（将来拡張・現状はライトのみ）

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111827;
    --surface: #1F2937;
    --text-primary: #F9FAFB;
    --text-secondary: #D1D5DB;
    --border: #374151;
    --user-bubble: #2A9D8F;
    --ai-bubble: #064E3B;
  }
}
```

---

## 3. タイポグラフィ

| 要素 | フォント | サイズ | 行高 | 太さ | 色 |
|------|----------|--------|------|------|-----|
| ヘッダータイトル | Inter / Noto Sans JP | 1.125rem (18px) | 1.4 | 600 | Primary |
| メッセージ本文 | Inter / Noto Sans JP | 1rem (16px) | 1.6 | 400 | Text Primary |
| タイムスタンプ | Inter / Noto Sans JP | 0.75rem (12px) | 1.4 | 400 | Text Muted |
| 入力欄 | Inter / Noto Sans JP | 1rem (16px) | 1.5 | 400 | Text Primary |
| プレースホルダー | Inter / Noto Sans JP | 1rem (16px) | 1.5 | 400 | Text Secondary |
| ボタン | Inter / Noto Sans JP | 0.875rem (14px) | 1.4 | 500 | White / Primary |
| ラベル・キャプション | Inter / Noto Sans JP | 0.875rem (14px) | 1.4 | 400 | Text Secondary |

**フォント読み込み:**
```html
<!-- Google Fonts: Inter + Noto Sans JP -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
```

---

## 4. スペーシング・グリッド

| 単位 | 値 | 用途 |
|------|-----|------|
| `--space-xs` | 4px | アイコンとテキストの間隔 |
| `--space-sm` | 8px | コンポーネント内パディング |
| `--space-md` | 16px | 標準マージン・パディング |
| `--space-lg` | 24px | セクション間・カードパディング |
| `--space-xl` | 32px | 画面左右マージン・大間隔 |

**グリッド:** 4pxベースのスペーシングシステム。コンテナ最大幅 720px（チャット幅最適化）。

---

## 5. コンポーネント仕様

### 5.1 ヘッダー

```vue
<header class="chat-header">
  <h1 class="chat-header__title">カウンセラーを探す</h1>
  <div class="chat-header__status" v-if="isLoading">AIが考え中...</div>
</header>
```

| プロパティ | 値 |
|-----------|-----|
| 高さ | 64px |
| 背景 | Surface (#FFFFFF) |
| ボーダー | Bottom 1px Border |
| パディング | 0 24px |
| タイトル | 18px / 600 / Primary |
| ステータス | 12px / 400 / Text Secondary / アニメーション付きドット |

### 5.2 メッセージバブル（共通）

```vue
<div class="message-bubble" :class="[role]">
  <div class="message-bubble__content" v-html="renderMarkdown(content)"></div>
  <time class="message-bubble__time">{{ formatTime(timestamp) }}</time>
</div>
```

| プロパティ | ユーザー | AI |
|-----------|---------|-----|
| 配置 | 右寄せ (margin-left: auto) | 左寄せ |
| 最大幅 | 85% | 85% |
| 背景 | Primary (#2A9D8F) | Primary Light (#E0F4F1) |
| テキスト色 | White | Text Primary |
| ボーダー半径 | 18px 18px 4px 18px | 18px 18px 18px 4px |
| シャドウ | 0 1px 2px rgba(0,0,0,0.05) | 同左 |
| パディング | 12px 16px | 同左 |

### 5.3 メッセージリスト

```vue
<div class="message-list" ref="listRef">
  <MessageBubble v-for="msg in messages" :key="msg.id" :message="msg" />
  <LoadingIndicator v-if="isLoading" />
</div>
```

| プロパティ | 値 |
|-----------|-----|
| フレックス方向 | column |
| ギャップ | 12px |
| パディング | 24px 16px |
| スクロール | 自動スクロール（新着時） |
| 仮想化 | 50件以上で検討 |

### 5.4 入力エリア

```vue
<div class="input-area">
  <textarea
    class="input-area__field"
    v-model="inputText"
    @keydown.enter.exact="send"
    @keydown.enter.shift="newLine"
    placeholder="メッセージを入力..."
    :disabled="isLoading"
    rows="1"
  ></textarea>
  <button
    class="input-area__send"
    @click="send"
    :disabled="!inputText.trim() || isLoading"
    aria-label="送信"
  >
    <SendIcon />
  </button>
</div>
```

| プロパティ | 値 |
|-----------|-----|
| 高さ | 最小 56px / 最大 140px (自動拡張) |
| 背景 | Surface |
| ボーダー | Top 1px Border |
| パディング | 12px 16px |
| テキストエリア | ボーダーなし・リサイズなし・アウトラインなし |
| 送信ボタン | 40×40px / 丸角 50% / Primary背景 / Whiteアイコン |
| 送信ボタン(無効) | Text Muted背景 / ポインター無効 |

### 5.5 ローディングインジケーター

```vue
<div class="loading-indicator">
  <div class="loading-indicator__dots">
    <span></span><span></span><span></span>
  </div>
  <span class="loading-indicator__text">AIが検索しています...</span>
</div>
```

- 3つのドットが順次フェードイン/アウト（0.4s周期）
- テキスト: 12px / Text Secondary

### 5.6 エラートースト

```vue
<Transition name="toast">
  <div class="toast toast--error" v-if="error">
    <AlertIcon />
    <span>{{ error }}</span>
    <button @click="dismissError" aria-label="閉じる"><CloseIcon /></button>
  </div>
</Transition>
```

- 画面下部固定・自動消滅なし（手動クローズ）
- 背景: Error / テキスト: White

---

## 6. レイアウト・レスポンシブ対応

### 6.1 ブレークポイント

| ブレークポイント | 幅 | 対応 |
|-----------------|-----|------|
| Mobile | < 640px | フルスクリーン・ヘッダー固定・入力固定 |
| Tablet | 640px - 1023px | 中央寄せ・最大幅 600px |
| Desktop | ≥ 1024px | 中央寄せ・最大幅 720px |

### 6.2 レイアウト構造

```html
<div class="app">
  <header class="chat-header">...</header>
  <main class="chat-main">
    <div class="message-list-wrapper">
      <MessageList />
    </div>
  </main>
  <footer class="input-area-wrapper">
    <InputArea />
  </footer>
  <ToastContainer />
</div>
```

**CSS Grid / Flexbox:**
```css
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh; /* モバイルアドレスバー対応 */
  max-width: 720px;
  margin: 0 auto;
  background: var(--bg);
}

.chat-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.message-list-wrapper {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
```

---

## 7. 画面デザイン・ワイヤフレーム

### 7.1 初期状態（メッセージなし）

```
┌────────────────────────────────────┐
│ カウンセラーを探す        🤔 AIが考え中 │
├────────────────────────────────────┤
│                                    │
│    💬 どのような条件でカウンセラー   │
│       を探したいですか？            │
│                                    │
│                                    │
│                                    │
│                                    │
├────────────────────────────────────┤
│ メッセージを入力...            ◀ │
└────────────────────────────────────┘
```

### 7.2 会話中（ユーザー入力→AI質問→ユーザー回答→検索→結果）

```
┌────────────────────────────────────┐
│ カウンセラーを探す                   │
├────────────────────────────────────┤
│                                    │
│  💬 どのような条件で...             │
│                                    │
│  ┌────────────────────────────┐   │
│  │ 新宿駅で女性、オンライン、   │   │ ← ユーザー (右寄せ・青緑)
│  │ 土曜の14時ごろ             │   │
│  │                    10:30   │   │
│  └────────────────────────────┘   │
│                                    │
│  ┌────────────────────────────┐   │
│  │ 承知しました。              │   │ ← AI (左寄せ・薄青緑)
│  │ 土曜14時ごろですね。        │   │
│  │ 相談したい内容（専門領域）  │   │
│  │ はありますか？              │   │
│  │                    10:31   │   │
│  └────────────────────────────┘   │
│                                    │
│  ┌────────────────────────────┐   │
│  │ 仕事のストレスと不安です    │   │
│  │                    10:32   │   │
│  └────────────────────────────┘   │
│                                    │
│  ┌────────────────────────────┐   │
│  │ 🔍 検索中...               │   │ ← システム/ローディング
│  │                    10:32   │   │
│  └────────────────────────────┘   │
│                                    │
│  ┌────────────────────────────┐   │
│  │ 条件に合うオフィスが2件見つ │   │ ← AI結果説明
│  │ かりました。                │   │
│  │                             │   │
│  │ 1. メンタルサポート新宿     │   │
│  │    最寄り: 代々木駅、参宮橋駅 │   │
│  │    鈴木美咲さん(女性/30代)  │   │
│  │    対応: オンライン・電話   │   │
│  │    専門: 不安/緊張、抑うつ   │   │
│  │                             │   │
│  │ 2. こころの相談室代々木     │   │
│  │    最寄り: 代々木駅         │   │
│  │    田中優子さん(女性/40代)  │   │
│  │    対応: オンライン・対面   │   │
│  │    専門: 対人関係、ストレス │   │
│  │                             │   │
│  │ 詳細を知りたいオフィスが    │   │
│  │ あれば教えてください。      │   │
│  │                    10:33   │   │
│  └────────────────────────────┘   │
├────────────────────────────────────┤
│ メッセージを入力...            ◀ │
└────────────────────────────────────┘
```

### 7.3 0件時の応答

```
┌────────────────────────────────────┐
│ ご希望の条件（新宿駅・女性・オンライン│
│ ・土曜14時）では該当するオフィスが   │
│ 見つかりませんでした。              │
│                                    │
│ 土曜日以外の曜日も含めて探しますか？│
│ あるいは、オンライン以外の方法も    │
│ 検討されますか？                    │
└────────────────────────────────────┘
```

---

## 8. アクセシビリティ方針

| 観点 | 対応 |
|------|------|
| **コントラスト比** | WCAG AA準拠 (テキスト 4.5:1、大文字 3:1) |
| **キーボード操作** | Tab順序・Enter送信・Shift+Enter改行・Escで入力クリア |
| **スクリーンリーダー** | `role="log" aria-live="polite"` メッセージリスト・`aria-label` ボタン |
| **フォーカス表示** | 明確なアウトライン (2px Primary / offset 2px) |
| **動きの軽減** | `prefers-reduced-motion` 対応・ローディングアニメーション無効化 |
| **言語指定** | `<html lang="ja">` |
| **文字拡大** | リサイズ対応・相対単位(rem)使用 |

---

## 9. マークダウンレンダリング仕様

AI応答内のMarkdownを安全にレンダリング：

| 要素 | 対応 |
|------|------|
| 段落・改行 | `<p>` / `<br>` |
| 強調 | `<strong>` / `<em>` |
| リスト | `<ul>` / `<ol>` / `<li>` |
| インラインコード | `<code>` |
| コードブロック | `<pre><code>` (シンタックスハイライトなし) |
| リンク | `<a target="_blank" rel="noopener noreferrer">` |
| 絵文字 | ネイティブ絵文字対応 |

**セキュリティ:** `DOMPurify` でサニタイズ後、`v-html` で描画。

---

## 10. アセット・アイコン

| アイコン | 用途 | ソース |
|---------|------|--------|
| Send | 送信ボタン | Lucide / Heroicons |
| AlertCircle | エラートースト | 同上 |
| X | トースト閉じる | 同上 |
| Loader2 | ローディング | 同上 |
| MessageSquare | ヘッダー装飾(任意) | 同上 |

**実装:** `unplugin-icons` + `Iconify` でオンデマンド読み込み。

---

## 11. 状態遷移・インタラクション

| トリガー | 現在状態 | 次状態 | UIフィードバック |
|---------|---------|--------|-----------------|
| 入力開始 | アイドル | 入力中 | 送信ボタン有効化 |
| Enter送信 | 入力中 | 送信中 | ボタン無効化・ローディング表示 |
| Agent応答受信 | 送信中 | アイドル | 新メッセージ追加・自動スクロール |
| ネットワークエラー | 送信中 | エラー | トースト表示・リトライボタン |
| 0件結果 | 検索完了 | 結果表示 | AIメッセージで代替案提示 |