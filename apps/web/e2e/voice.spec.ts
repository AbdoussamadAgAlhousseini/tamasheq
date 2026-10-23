import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Données factices : la phrase à lire est une chaîne de test, pas du tamasheq.
async function setup(page: Page) {
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({
      json: ["chat", "translation", "dictionary", "knowledge", "knowledge_qa", "asr", "tts"].map(
        (name) => ({ name, status: "not_available", note: "" }),
      ),
    }),
  );
  await page.route("**/api/v1/me", (route) =>
    route.request().headers()["authorization"] === "Bearer bon-jeton"
      ? route.fulfill({ json: { pseudonym: "voix-test", role: "contributor" } })
      : route.fulfill({ status: 401, json: { detail: "Jeton invalide ou révoqué." } }),
  );
  await page.route("**/api/v1/voice/prompts?*", (route) =>
    route.fulfill({ json: [{ id: "p1", text: "zz phrase à lire", script: "Latn" }] }),
  );
}

test("sans compte : formulaire de connexion, jeton invalide refusé", async ({ page }) => {
  await setup(page);
  await page.goto("/voice");
  await page.getByLabel("Jeton d'accès").fill("mauvais");
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page.getByText("Jeton invalide ou révoqué.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enregistrer" })).toHaveCount(0);
});

test("enregistrer, réécouter et envoyer avec les consentements choisis", async ({ page }) => {
  await setup(page);
  let request: { auth?: string; body: string; type?: string } | null = null;
  await page.route("**/api/v1/voice/recordings", async (route) => {
    request = {
      auth: route.request().headers()["authorization"],
      type: route.request().headers()["content-type"],
      body: route.request().postDataBuffer()?.toString("latin1") ?? "",
    };
    await route.fulfill({ status: 201, json: { id: "r1", status: "pending" } });
  });

  await page.goto("/voice");
  await page.getByLabel("Jeton d'accès").fill("bon-jeton");
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page.getByText("voix-test")).toBeVisible();
  await expect(page.getByTestId("prompt")).toHaveText("zz phrase à lire");

  const consents = page.getByRole("checkbox");
  await expect(consents).toHaveCount(3);
  for (const box of await consents.all()) await expect(box).not.toBeChecked();
  await page.getByLabel("J'accepte qu'il serve à entraîner", { exact: false }).check();

  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(axe.violations.map((v) => v.id)).toEqual([]);

  await page.getByRole("button", { name: "Enregistrer" }).click();
  await expect(page.getByText("Enregistrement en cours", { exact: false })).toBeVisible();
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: "Arrêter" }).click();
  await expect(page.locator("audio")).toBeVisible();
  await page.getByRole("button", { name: "Envoyer" }).click();
  await expect(page.getByText("Enregistrement reçu, en attente de relecture.", { exact: false })).toBeVisible();

  expect(request).not.toBeNull();
  const sent = request as unknown as { auth?: string; body: string; type?: string };
  expect(sent.auth).toBe("Bearer bon-jeton");
  expect(sent.type).toContain("multipart/form-data");
  expect(sent.body).toContain('name="audio"; filename="recording.');
  const metadata = JSON.parse(sent.body.split('name="metadata"\r\n\r\n')[1].split("\r\n--")[0]);
  expect(metadata).toMatchObject({
    allow_publication: false,
    allow_training: true,
    allow_voice_synthesis: false,
    prompt_text_id: "p1",
    license: "CC-BY-4.0",
  });
});
