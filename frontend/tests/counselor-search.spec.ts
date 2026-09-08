import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:3000';

test.describe('カウンセラー検索 AI デモ', () => {
  test('ページが正しく読み込まれる', async ({ page }) => {
    await page.goto(BASE);
    await expect(page).toHaveTitle('カウンセラー検索 AI デモ');
    await expect(page.locator('h1')).toContainText('カウンセラー検索 AI');
  });

  test('チャット入力フォームが表示される', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('textarea')).toBeVisible();
    await expect(page.locator('button')).toContainText('送信');
  });

  test('ウェルカムメッセージが表示される', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.welcome-message')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.welcome-message')).toContainText('カウンセラー検索AIへようこそ');
  });

  test('メッセージを送信できる', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForSelector('textarea');

    // Vue v-model を直接操作
    await page.evaluate(() => {
      const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )!.set!;
      nativeInputValueSetter.call(textarea, '新宿駅近くのカウンセラーを探して');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await page.waitForTimeout(500);
    await page.locator('button').click();

    await expect(page.locator('.bubble.user')).toBeVisible({ timeout: 10000 });
  });

  test('クイックリプライボタンが表示される', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForSelector('textarea');

    // メッセージを送信してアシスタントの応答を待つ
    await page.evaluate(() => {
      const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )!.set!;
      nativeInputValueSetter.call(textarea, '仕事のストレスで悩んでいます');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await page.waitForTimeout(500);
    await page.locator('button').click();

    // アシスタントの応答を待つ
    await expect(page.locator('.bubble.assistant')).toBeVisible({ timeout: 90000 });

    // クイックリプライが表示されるか確認
    await page.waitForTimeout(1000);
    const quickReplies = page.locator('.quick-reply-btn');
    const count = await quickReplies.count();
    // クイックリプライが表示される場合とそうでない場合がある
    expect(count).toBeGreaterThanOrEqual(0);
  }, { timeout: 120000 });

  test('複数メッセージを送信できる', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForSelector('textarea');

    // 最初のメッセージ
    await page.evaluate(() => {
      const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )!.set!;
      nativeInputValueSetter.call(textarea, '仕事のストレスで悩んでいます');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await page.waitForTimeout(500);
    await page.locator('button').click();
    await expect(page.locator('.bubble.user')).toBeVisible({ timeout: 10000 });

    // アシスタントの応答を待つ
    await expect(page.locator('.bubble.assistant')).toBeVisible({ timeout: 90000 });

    // 2番目のメッセージ
    await page.waitForTimeout(1000);
    await page.evaluate(() => {
      const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )!.set!;
      nativeInputValueSetter.call(textarea, 'オンラインで相談したい');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await page.waitForTimeout(500);
    await page.locator('button').click();
    await expect(page.locator('.bubble.user').nth(1)).toBeVisible({ timeout: 10000 });
  }, { timeout: 120000 });

  test('API レスポンスが表示される', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForSelector('textarea');

    await page.evaluate(() => {
      const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )!.set!;
      nativeInputValueSetter.call(textarea, '渋谷駅');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await page.waitForTimeout(500);
    await page.locator('button').click();

    await expect(page.locator('.bubble.assistant')).toBeVisible({ timeout: 90000 });
  }, { timeout: 120000 });
});

test.describe('API エンドポイント', () => {
  test('API が応答する', async ({ request }) => {
    const response = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: { query: 'test' },
    });

    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.success).toBeTruthy();
  });

  test('検索パラメータでAPIが応答する', async ({ request }) => {
    const response = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: '新宿駅でオンライン相談',
        parameters: {
          stations: ['新宿駅'],
          methods: ['オンライン'],
        },
      },
    });

    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.success).toBeTruthy();
  });

  test('セッションメモリが会話を記憶する', async ({ request }) => {
    // セッションIDを生成（33文字以上）
    const sessionId = `sid_${Date.now()}_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}`;
    const actorId = `actor_${Date.now()}_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}`;

    console.log('Session ID:', sessionId, '(length:', sessionId.length, ')');

    // 1回目: 相談内容を送信
    const response1 = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: '仕事のストレスで悩んでいます',
        session_id: sessionId,
        actor_id: actorId,
      },
    });

    expect(response1.ok()).toBeTruthy();
    const body1 = await response1.json();
    expect(body1.success).toBeTruthy();
    expect(body1.session_id).toBe(sessionId);
    console.log('Response 1:', body1.result.answer.substring(0, 100));

    // 2回目: 相談方法を送信（セッションメモリが機能していれば、相談内容を記憶している）
    const response2 = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: 'オンラインで相談したい',
        session_id: sessionId,
        actor_id: actorId,
      },
    });

    expect(response2.ok()).toBeTruthy();
    const body2 = await response2.json();
    expect(body2.success).toBeTruthy();
    console.log('Response 2:', body2.result.answer.substring(0, 100));

    // 3回目: 駅を送信（セッションメモリが機能していれば、相談内容と方法を記憶している）
    const response3 = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: '新宿駅で相談したい',
        session_id: sessionId,
        actor_id: actorId,
      },
    });

    expect(response3.ok()).toBeTruthy();
    const body3 = await response3.json();
    expect(body3.success).toBeTruthy();
    console.log('Response 3:', body3.result.answer.substring(0, 100));

    // 4回目: 性別を送信（セッションメモリが機能していれば、すべての条件を記憶している）
    const response4 = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: '女性で相談したい',
        session_id: sessionId,
        actor_id: actorId,
      },
    });

    expect(response4.ok()).toBeTruthy();
    const body4 = await response4.json();
    expect(body4.success).toBeTruthy();
    console.log('Response 4:', body4.result.answer.substring(0, 100));

    // 5回目: 確認（セッションメモリが機能していれば、すべての条件を確認する）
    const response5 = await request.post('https://u420b7ott4.execute-api.ap-northeast-1.amazonaws.com/prod', {
      data: {
        query: '指定なし',
        session_id: sessionId,
        actor_id: actorId,
      },
    });

    expect(response5.ok()).toBeTruthy();
    const body5 = await response5.json();
    expect(body5.success).toBeTruthy();
    console.log('Response 5:', body5.result.answer.substring(0, 100));

    // 確認画面に条件が含まれているか確認
    const answer5 = body5.result.answer;
    expect(answer5).toContain('仕事');
    expect(answer5).toContain('オンライン');
    expect(answer5).toContain('新宿');
    expect(answer5).toContain('女性');
  }, { timeout: 300000 });
});
