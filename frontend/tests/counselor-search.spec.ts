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
    await expect(page.locator('button')).toContainText('検索実行');
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
});
