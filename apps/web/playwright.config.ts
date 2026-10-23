import { defineConfig, devices } from "@playwright/test";

// Navigateur : celui installé par `npx playwright install chromium` (CI), ou un Chromium
// existant indiqué par PW_CHROMIUM_PATH.
const executablePath = process.env.PW_CHROMIUM_PATH;

export default defineConfig({
  testDir: "e2e",
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3100",
    launchOptions: {
      ...(executablePath ? { executablePath } : {}),
      // Micro factice : permet de tester l'enregistrement sans matériel ni autorisation manuelle.
      args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
    },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"], viewport: { width: 360, height: 780 } } },
  ],
  webServer: {
    command: "npm run start -- --port 3100",
    url: "http://localhost:3100",
    reuseExistingServer: !process.env.CI,
  },
});
