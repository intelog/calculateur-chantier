const { chromium } = require("playwright");

async function main() {
  const launchOptions = { headless: true };
  if (process.env.BROWSER_EXE) {
    launchOptions.executablePath = process.env.BROWSER_EXE;
  }

  const browser = await chromium.launch(launchOptions);
  const messages = [];
  const checks = [];

  async function checkViewport(name, viewport) {
    const page = await browser.newPage({ viewport });

    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        messages.push(`${name}:${message.type()}: ${message.text()}`);
      }
    });
    page.on("pageerror", (error) => messages.push(`${name}:pageerror: ${error.message}`));

    await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });
    const title = await page.locator("h1").textContent();
    const structureTotal = await page.locator("#stud-total").textContent();

    const tabChecks = [
      ["panel-panel", "#panel-total", "panelTotal"],
      ["floor-panel", "#floor-total", "floorTotal"],
      ["paint-panel", "#paint-total", "paintTotal"],
      ["trim-panel", "#trim-total", "trimTotal"],
    ];

    const results = { structureTotal };
    for (const [tabId, resultId, resultKey] of tabChecks) {
      await page.click(`button[data-tab="${tabId}"]`);
      await page.waitForTimeout(150);
      results[resultKey] = await page.locator(resultId).textContent();
    }

    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    const screenshot = process.env.NO_SCREENSHOT ? null : `qa-${name}.png`;
    if (screenshot) {
      await page.screenshot({ path: screenshot, fullPage: true });
    }
    await page.close();

    checks.push({ name, title, ...results, hasHorizontalOverflow, screenshot });
  }

  await checkViewport("desktop", { width: 1365, height: 900 });
  await checkViewport("mobile", { width: 390, height: 844 });
  await browser.close();

  console.log(
    JSON.stringify(
      {
        checks,
        messages,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
