const fs = require("fs");
const path = require("path");

const playwrightModule = process.env.PLAYWRIGHT_CORE_PATH || "playwright-core";
const { chromium } = require(playwrightModule);

const root = path.resolve(__dirname, "..");
const baseUrl = process.env.ATLAS_URL || "http://127.0.0.1:8000";
const chromePath = process.env.PLAYWRIGHT_CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

async function testViewport(browser, viewport, screenshotName) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator("#loading-state").waitFor({ state: "hidden", timeout: 60000 });
  await page.locator("#latitude").fill("45.0757395");
  await page.locator("#longitude").fill("7.6785426");
  await page.locator("#find-button").click();
  await page.locator("#category-title").waitFor({ state: "visible" });

  const category = (await page.locator("#category-title").textContent()).trim();
  if (category !== "C · Tall/dense") throw new Error(`Unexpected Consolata result: ${category}`);

  const disclosure = (await page.locator(".model-disclosure").textContent()).trim();
  if (!disclosure.includes("not measured local UHI")) {
    throw new Error(`Missing modeled-UHI disclosure: ${disclosure}`);
  }

  const dataLicenseHref = await page.locator('.sidebar-footer a[href="DATA_LICENSE.md"]').getAttribute("href");
  const dataLicenseResponse = await page.request.get(new URL(dataLicenseHref, baseUrl).href);
  if (!dataLicenseResponse.ok()) throw new Error(`Data license returned HTTP ${dataLicenseResponse.status()}`);

  await page.locator("#about-button").click();
  await page.locator("#about-dialog").waitFor({ state: "visible" });
  const aboutText = (await page.locator("#about-dialog").textContent()).trim();
  if (!aboutText.includes("Ali JahaniRahaei") || !aboutText.includes("Giacomo Chiesa")) {
    throw new Error(`Missing atlas authorship in About dialog: ${aboutText}`);
  }
  const repositoryHref = await page.locator('#about-dialog a[href="https://github.com/alijahanirahaei/torino-urban-epw-atlas"]').getAttribute("href");
  if (repositoryHref !== "https://github.com/alijahanirahaei/torino-urban-epw-atlas") {
    throw new Error(`Unexpected source repository link: ${repositoryHref}`);
  }
  const guideHref = await page.locator('#about-dialog a[href="docs/repository-guide.html"]').getAttribute("href");
  const guideResponse = await page.request.get(new URL(guideHref, baseUrl).href);
  if (!guideResponse.ok()) throw new Error(`Repository guide returned HTTP ${guideResponse.status()}`);
  await page.locator("#close-about").click();

  await page.locator('[data-mode="k7"]').click();
  const legendTitle = (await page.locator(".legend-title").textContent()).trim();
  if (legendTitle !== "k=7 morphology classes") throw new Error(`Unexpected legend: ${legendTitle}`);

  const downloadHref = await page.locator("#epw-download").getAttribute("href");
  const response = await page.request.get(new URL(downloadHref, baseUrl).href);
  if (!response.ok()) throw new Error(`EPW download returned HTTP ${response.status()}`);

  const configHref = await page.locator("#config-download").getAttribute("href");
  const configResponse = await page.request.get(new URL(configHref, baseUrl).href);
  if (!configResponse.ok()) throw new Error(`UWG configuration download returned HTTP ${configResponse.status()}`);

  const layout = await page.evaluate(() => ({
    bodyWidth: document.body.scrollWidth,
    viewportWidth: window.innerWidth,
    mapRect: document.querySelector("#map").getBoundingClientRect().toJSON(),
    panelRect: document.querySelector(".sidebar").getBoundingClientRect().toJSON(),
    visibleGridPaths: document.querySelectorAll(".leaflet-overlay-pane path").length,
    canvasCount: document.querySelectorAll(".leaflet-overlay-pane canvas").length,
  }));
  if (layout.bodyWidth > layout.viewportWidth + 1) throw new Error(`Horizontal overflow: ${JSON.stringify(layout)}`);
  if (layout.mapRect.width < 280 || layout.mapRect.height < 250) throw new Error(`Map too small: ${JSON.stringify(layout.mapRect)}`);
  if (layout.visibleGridPaths + layout.canvasCount === 0) throw new Error("No rendered grid paths or canvas found");

  await page.screenshot({ path: path.join(root, "docs", screenshotName), fullPage: true });
  await page.close();
  return {
    viewport,
    category,
    legendTitle,
    downloadHref,
    configHref,
    disclosure,
    dataLicenseHref,
    guideHref,
    repositoryHref,
    authorsVerified: true,
    layout,
    consoleErrors,
    pageErrors,
  };
}

async function testGuide(browser, viewport) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto(`${baseUrl.replace(/\/$/, "")}/docs/repository-guide.html`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  const heading = (await page.locator("h1").textContent()).trim();
  if (heading !== "Use, data, and repository structure") {
    throw new Error(`Unexpected repository-guide heading: ${heading}`);
  }
  const text = (await page.locator("main").textContent()).trim();
  for (const expected of ["Ali JahaniRahaei", "Giacomo Chiesa", "python3 -m http.server 8000", "GitHub Actions"]) {
    if (!text.includes(expected)) throw new Error(`Repository guide is missing: ${expected}`);
  }
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  if (bodyWidth > viewport.width + 1) {
    throw new Error(`Repository-guide horizontal overflow: ${bodyWidth} > ${viewport.width}`);
  }
  await page.close();
  return { viewport, heading, bodyWidth, consoleErrors, pageErrors };
}

(async () => {
  if (!fs.existsSync(chromePath)) throw new Error(`Chrome executable not found: ${chromePath}`);
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  try {
    const desktop = await testViewport(browser, { width: 1440, height: 900 }, "atlas-preview.png");
    const mobile = await testViewport(browser, { width: 390, height: 844 }, "atlas-mobile.png");
    const guideDesktop = await testGuide(browser, { width: 1200, height: 900 });
    const guideMobile = await testGuide(browser, { width: 390, height: 844 });
    const failures = [
      ...desktop.consoleErrors,
      ...desktop.pageErrors,
      ...mobile.consoleErrors,
      ...mobile.pageErrors,
      ...guideDesktop.consoleErrors,
      ...guideDesktop.pageErrors,
      ...guideMobile.consoleErrors,
      ...guideMobile.pageErrors,
    ]
      .filter((message) => !message.includes("tile.openstreetmap.org"));
    if (failures.length) throw new Error(`Browser errors: ${failures.join(" | ")}`);
    const report = { status: "PASS", baseUrl, desktop, mobile, guideDesktop, guideMobile };
    fs.writeFileSync(path.join(root, "browser_qa_report.json"), `${JSON.stringify(report, null, 2)}\n`);
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exit(1);
});
