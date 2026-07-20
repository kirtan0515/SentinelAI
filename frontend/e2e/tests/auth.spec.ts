import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("landing page loads successfully", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/SentinelAI/i);
    await expect(page.locator("body")).toBeVisible();
  });

  test("navigate to login page", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href*="login"], button:has-text("Login"), a:has-text("Sign in")');
    await expect(page).toHaveURL(/.*login.*/);
  });

  test("login form validates empty fields", async ({ page }) => {
    await page.goto("/login");

    // Submit empty form
    await page.click('button[type="submit"]');

    // Expect validation errors
    const errorMessages = page.locator(
      '[role="alert"], .error, [data-testid="error-message"]'
    );
    await expect(errorMessages.first()).toBeVisible();
  });

  test("login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");

    // Fill in invalid credentials
    await page.fill('input[name="email"], input[type="email"]', "invalid@example.com");
    await page.fill('input[name="password"], input[type="password"]', "wrongpassword");

    // Submit form
    await page.click('button[type="submit"]');

    // Expect error message
    const errorMessage = page.locator(
      '[role="alert"], .error, .toast-error, [data-testid="error-message"]'
    );
    await expect(errorMessage.first()).toBeVisible({ timeout: 10000 });
  });

  test("registration page is accessible", async ({ page }) => {
    await page.goto("/register");
    await expect(page).toHaveURL(/.*register.*/);

    // Verify registration form elements exist
    const emailInput = page.locator('input[name="email"], input[type="email"]');
    const passwordInput = page.locator('input[name="password"], input[type="password"]');

    await expect(emailInput.first()).toBeVisible();
    await expect(passwordInput.first()).toBeVisible();
  });
});
