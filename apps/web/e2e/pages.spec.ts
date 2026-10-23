import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

const ROUTES = [
  "/",
  "/chat",
  "/translate",
  "/dictionary",
  "/knowledge",
  "/voice",
  "/contribute",
  "/admin",
  "/about",
];

const CAPABILITIES = [
  "chat",
  "translation",
  "dictionary",
  "knowledge",
  "knowledge_qa",
  "asr",
  "tts",
].map(
  (name) => ({ name, status: "not_available", note: "" }),
);

async function mockApi(page: Page, body: unknown = CAPABILITIES, status = 200) {
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) }),
  );
  await page.route("**/api/v1/dictionary?*", (route) => route.fulfill({ json: { items: [] } }));
  await page.route("**/api/v1/knowledge?*", (route) => route.fulfill({ json: [] }));
}

for (const route of ROUTES) {
  test(`${route} : rendu, accessibilité, pas de défilement horizontal`, async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => msg.type() === "error" && errors.push(msg.text()));
    page.on("pageerror", (error) => errors.push(error.message));
    await mockApi(page);
    // Préférences non par défaut : vérifie l'absence d'erreur d'hydratation dans ce cas aussi.
    await page.addInitScript(() => {
      localStorage.setItem("tamasheq.lang", "en");
      localStorage.setItem("tamasheq.script", "tfng");
    });
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page.locator("h1")).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    expect(errors).toEqual([]);
  });
}

test("l'état des modules vient de l'API", async ({ page }) => {
  await mockApi(page, [{ name: "chat", status: "experimental", note: "" }]);
  await page.goto("/chat");
  const badge = page.locator('[data-capability="chat"]');
  await expect(badge.getByText("Expérimental, non validé", { exact: true })).toBeVisible();
  await expect(badge).toHaveAttribute("data-status", "experimental");
});

test("serveur injoignable : état inconnu, jamais « disponible »", async ({ page }) => {
  await mockApi(page, { detail: "erreur" }, 503);
  await page.goto("/translate");
  const badge = page.locator('[data-capability="translation"]');
  await expect(badge.getByText("État inconnu (serveur injoignable)", { exact: true })).toBeVisible();
  await expect(badge).toHaveAttribute("data-status", "error");
});

test("la langue d'interface change et persiste", async ({ page, isMobile }) => {
  await mockApi(page);
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "fr");
  if (isMobile) await page.getByRole("button", { name: "Menu" }).click();
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { name: "Modules" })).toBeVisible();
  await expect(page.getByText("The project is under construction.", { exact: false })).toBeVisible();
  await expect(page.getByText("Le projet est en construction.", { exact: false })).toBeHidden();

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByText("The project is under construction.", { exact: false })).toBeVisible();
});

test("la préférence d'écriture est enregistrée", async ({ page, isMobile }) => {
  await mockApi(page);
  await page.goto("/about");
  if (isMobile) await page.getByRole("button", { name: "Menu" }).click();
  const tifinagh = page.getByRole("button", { name: "Tifinagh" });
  await tifinagh.click();
  await expect(tifinagh).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("html")).toHaveAttribute("data-script", "tfng");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-script", "tfng");
});

test("le tifinagh s'affiche avec la police auto-hébergée", async ({ page }) => {
  await mockApi(page);
  await page.goto("/about");
  await expect(page.getByTestId("tifinagh-block").locator("li")).toHaveCount(59);
  const loaded = await page.evaluate(async () => {
    await document.fonts.load('24px "Noto Sans Tifinagh"', "ⵜ");
    return document.fonts.check('24px "Noto Sans Tifinagh"', "ⵜ");
  });
  expect(loaded).toBe(true);
});

test("navigation au clavier : lien d'évitement vers le contenu", async ({ page, isMobile }) => {
  test.skip(isMobile, "pas de clavier physique sur mobile");
  await mockApi(page);
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Aller au contenu" });
  await expect(skip).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main$/);
});
