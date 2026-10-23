import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

function capabilities(chat: string) {
  return ["chat", "translation", "dictionary", "knowledge", "asr", "tts"].map((name) => ({
    name,
    status: name === "chat" ? chat : "not_available",
    note: "",
  }));
}

async function setup(page: Page, chat = "experimental") {
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({ json: capabilities(chat) }),
  );
}

const input = (page: Page) => page.getByLabel("Votre message");

test("assistant non configuré : pas de champ de saisie", async ({ page }) => {
  await setup(page, "not_available");
  await page.goto("/chat");
  await expect(page.getByText("L'assistant n'est pas activé sur ce serveur.")).toBeVisible();
  await expect(input(page)).toHaveCount(0);
});

test("conversation : historique envoyé, réponse marquée non vérifiée", async ({ page }) => {
  await setup(page);
  const bodies: unknown[] = [];
  await page.route("**/api/v1/chat", async (route) => {
    const body = route.request().postDataJSON() as { messages: unknown[] };
    bodies.push(body);
    await route.fulfill({
      json: {
        reply: `réponse ${body.messages.length}`,
        provider: "fake",
        model: "modele-test",
        truncated: false,
        status: "experimental",
        verified: false,
      },
    });
  });
  await page.goto("/chat");
  await expect(page.getByText("Expérimental.")).toBeVisible();

  await input(page).fill("Première question");
  await page.getByRole("button", { name: "Envoyer" }).click();
  await expect(page.getByText("réponse 1")).toBeVisible();
  await expect(page.getByText("Réponse générée par modele-test, non vérifiée.")).toBeVisible();

  await input(page).fill("Deuxième question");
  await input(page).press("Control+Enter");
  await expect(page.getByText("réponse 3")).toBeVisible();
  expect(bodies[1]).toEqual({
    messages: [
      { role: "user", content: "Première question" },
      { role: "assistant", content: "réponse 1" },
      { role: "user", content: "Deuxième question" },
    ],
  });

  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);

  await page.getByRole("button", { name: "Nouvelle conversation" }).click();
  await expect(page.locator("li[data-role]")).toHaveCount(0);
});

test("erreur : message conservé dans le champ et explication affichée", async ({ page }) => {
  await setup(page);
  await page.route("**/api/v1/chat", (route) =>
    route.fulfill({ status: 429, json: { detail: { code: "rate_limited", message: "" } } }),
  );
  await page.goto("/chat");
  await input(page).fill("Bonjour");
  await page.getByRole("button", { name: "Envoyer" }).click();
  await expect(
    page.getByRole("alert").getByText("Trop de requêtes en peu de temps. Réessayez dans une minute."),
  ).toBeVisible();
  await expect(input(page)).toHaveValue("Bonjour");
  await expect(page.locator("li[data-role]")).toHaveCount(0);
});
