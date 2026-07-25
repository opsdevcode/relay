/*
 * Copyright 2020 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { test, expect } from '@playwright/test';

async function enterAsGuest(page: import('@playwright/test').Page) {
  await page.goto('/');
  const enterButton = page.getByRole('button', { name: 'Enter' });
  await expect(enterButton).toBeVisible();
  await enterButton.click();
}

test('Relay Assistant nav opens embedded chat iframe', async ({ page }) => {
  await enterAsGuest(page);

  const nav = page.getByRole('navigation', { name: 'sidebar nav' });
  await nav.getByRole('link', { name: 'Relay Assistant' }).click();

  await expect(page).toHaveURL(/\/relay/);

  const frame = page.locator('iframe[title="Relay Assistant"]');
  await expect(frame).toBeVisible();
  await expect(frame).toHaveAttribute('src', 'http://localhost:3000');
});
