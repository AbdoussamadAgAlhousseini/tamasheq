import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Données factices : chaînes de test, pas du tamasheq.
const ENTRY = {
  id: "11111111-1111-1111-1111-111111111111",
  headword: "zzmot",
  script: "Latn",
  language: "taq",
  variant: "variante-test",
  part_of_speech: null,
  status: "validated",
  spellings: [{ form: "ⴰⴱⴲ", script: "Tfng" }],
  senses: [
    {
      definition_fr: "définition-test",
      definition_en: "definition-test",
      translation_fr: "maison-test",
      translation_en: "house-test",
      examples: [],
    },
  ],
  source: { title: "Source test", citation: null, url: null },
  license: "CC-BY-4.0",
  validated_at: "2026-10-23T00:00:00Z",
};

async function setup(page: Page, items: unknown[], requests: URL[] = []) {
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({
      json: ["chat", "translation", "dictionary", "knowledge", "asr", "tts"].map((name) => ({
        name,
        status: name === "dictionary" ? "experimental" : "not_available",
        note: "",
      })),
    }),
  );
  await page.route("**/api/v1/dictionary?*", (route) => {
    requests.push(new URL(route.request().url()));
    return route.fulfill({ json: { items } });
  });
}

test("dictionnaire vide : message explicite", async ({ page }) => {
  await setup(page, []);
  await page.goto("/dictionary");
  await expect(page.getByText("Aucune entrée publiée pour l'instant", { exact: false })).toBeVisible();
});

test("entrée validée, préférence d'écriture et accessibilité", async ({ page, isMobile }) => {
  await setup(page, [ENTRY]);
  await page.goto("/dictionary");
  const card = page.locator(`[data-entry="${ENTRY.id}"]`);
  const heading = card.getByRole("heading");
  await expect(heading.locator('[lang="taq-Latn"]')).toBeVisible();
  await expect(heading.locator('[lang="taq-Tfng"]')).toBeHidden();
  await expect(card.getByText("Validée", { exact: true })).toBeVisible();
  await expect(card.getByText("maison-test", { exact: true })).toBeVisible();
  await expect(card.getByText("house-test", { exact: true })).toBeHidden();

  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);

  if (isMobile) await page.getByRole("button", { name: "Menu" }).click();
  await page.getByRole("button", { name: "Tifinagh" }).click();
  await expect(heading.locator('[lang="taq-Tfng"]')).toBeVisible();
  await expect(heading.locator('[lang="taq-Latn"]')).toBeHidden();
});

test("entrée en attente clairement signalée ; requête transmise", async ({ page }) => {
  const requests: URL[] = [];
  await setup(page, [{ ...ENTRY, status: "pending" }], requests);
  await page.goto("/dictionary");
  await page.getByLabel("Afficher aussi les entrées en attente de validation").check();
  await page.getByLabel("Rechercher un mot", { exact: false }).fill("zz");
  await expect(page.getByText("Non validée : en attente de relecture")).toBeVisible();
  await expect
    .poll(() => requests.at(-1)?.searchParams.toString())
    .toBe("q=zz&include_pending=true");
});
