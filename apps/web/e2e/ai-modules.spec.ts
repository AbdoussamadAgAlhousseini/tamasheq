import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Données factices : aucun texte tamasheq ni savoir réel.
const ALL = ["chat", "translation", "dictionary", "knowledge", "knowledge_qa", "asr", "tts"];

async function capabilities(page: Page, active: string[]) {
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({
      json: ALL.map((name) => ({
        name,
        status: active.includes(name) ? "experimental" : "not_available",
        note: "",
      })),
    }),
  );
}

test("traduction non configurée : pas de formulaire", async ({ page }) => {
  await capabilities(page, []);
  await page.goto("/translate");
  await expect(page.getByText("Cette fonction n'est pas activée sur ce serveur.")).toBeVisible();
  await expect(page.getByLabel("Texte à traduire")).toHaveCount(0);
});

test("traduction : résultat marqué non vérifié, ambiguïtés et glossaire", async ({ page }) => {
  await capabilities(page, ["translation"]);
  let sent: unknown = null;
  await page.route("**/api/v1/translate", async (route) => {
    sent = route.request().postDataJSON();
    await route.fulfill({
      json: {
        translation: "zztraduction",
        alternatives: ["zzautre"],
        ambiguities: ["« maison » : sens ambigu (test)"],
        notes: "Note de test.",
        glossary: [{ id: "g1", headword: "zzmot" }],
        provider: "fake",
        model: "modele-test",
        truncated: false,
        status: "experimental",
        verified: false,
      },
    });
  });
  await page.goto("/translate");
  await page.getByLabel("Direction").selectOption({ label: "Tamasheq → anglais" });
  await page.getByLabel("Texte à traduire").fill("zzsource");
  await page.getByRole("button", { name: "Traduire" }).click();
  const result = page.getByTestId("translation");
  await expect(result.getByText("zztraduction")).toBeVisible();
  await expect(result.getByText("Générée par modele-test, non vérifiée.")).toBeVisible();
  await expect(result.getByText("zzautre")).toBeVisible();
  await expect(result.getByText("« maison » : sens ambigu (test)")).toBeVisible();
  await expect(result.getByText("zzmot")).toBeVisible();
  await expect(result.locator('p[lang="en"]').first()).toHaveText("zztraduction");
  expect(sent).toEqual({ text: "zzsource", source_lang: "taq", target_lang: "en", variant: null });
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.map((v) => v.id)).toEqual([]);
});

const DOC = {
  id: "d1",
  title: "Document de test",
  theme: "plants",
  access_level: "public",
  language: "fra",
  author_credit: null,
  source: { title: "Source test", citation: null, url: null },
  license: "CC-BY-4.0",
  excerpt: "Extrait de test.",
};

test("bibliothèque : recherche par thème et lecture", async ({ page }) => {
  await capabilities(page, ["knowledge"]);
  const urls: URL[] = [];
  await page.route("**/api/v1/knowledge?*", (route) => {
    urls.push(new URL(route.request().url()));
    return route.fulfill({ json: [DOC] });
  });
  await page.route("**/api/v1/knowledge/d1", (route) =>
    route.fulfill({ json: { ...DOC, body: "Corps complet du document de test." } }),
  );
  await page.goto("/knowledge");
  await expect(page.getByText("Extrait de test.")).toBeVisible();
  await expect(page.getByRole("article").getByText("Plantes et savoirs écologiques")).toBeVisible();
  await page.getByLabel("Thème").selectOption("plants");
  await expect.poll(() => urls.at(-1)?.searchParams.get("theme")).toBe("plants");
  await page.getByRole("button", { name: "Lire le document" }).click();
  await expect(page.getByText("Corps complet du document de test.")).toBeVisible();
  // pas de formulaire de question sans réponses configurées
  await expect(page.getByLabel("Votre question")).toHaveCount(0);
});

test("question : réponse avec passages cités, ou documentation insuffisante", async ({ page }) => {
  await capabilities(page, ["knowledge", "knowledge_qa"]);
  await page.route("**/api/v1/knowledge?*", (route) => route.fulfill({ json: [] }));
  let documented = true;
  await page.route("**/api/v1/knowledge/ask", (route) =>
    route.fulfill({
      json: documented
        ? {
            answer: "Réponse de test.",
            insufficient_documentation: false,
            references: [
              {
                ref: "P1",
                document_id: "d1",
                title: "Document de test",
                source: DOC.source,
                license: "CC-BY-4.0",
                passage: "Passage cité de test.",
              },
            ],
            provider: "fake",
            model: "modele-test",
            status: "experimental",
            verified: false,
          }
        : {
            answer: null,
            insufficient_documentation: true,
            references: [],
            provider: null,
            model: null,
            status: "experimental",
            verified: false,
          },
    }),
  );
  await page.goto("/knowledge");
  await page.getByLabel("Votre question").fill("Question de test ?");
  await page.getByRole("button", { name: "Demander" }).click();
  const answer = page.getByTestId("answer");
  await expect(answer.getByText("Réponse de test.")).toBeVisible();
  await expect(answer.getByText("Passage cité de test.")).toBeVisible();
  await expect(answer.getByText("[P1] Document de test")).toBeVisible();

  documented = false;
  await page.getByRole("button", { name: "Demander" }).click();
  await expect(
    answer.getByText("Les documents disponibles ne permettent pas de répondre", { exact: false }),
  ).toBeVisible();
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.map((v) => v.id)).toEqual([]);
});
