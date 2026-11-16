const playwrightModule = process.env.PLAYWRIGHT_MODULE || "playwright";
const { chromium } = await import(playwrightModule);

const target = process.argv[2] || "http://127.0.0.1:8000";
const output = process.argv[3] || "docs/assets/dashboard-demo.webm";
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: "/tmp/retail-planner-video", size: { width: 1440, height: 900 } },
});
const page = await context.newPage();
const pause = milliseconds => page.waitForTimeout(milliseconds);
const caption = async text => {
  await page.evaluate(value => {
    let element = document.getElementById("demo-caption");
    if (!element) {
      element = document.createElement("div");
      element.id = "demo-caption";
      Object.assign(element.style, {
        position: "fixed", left: "50%", bottom: "24px", transform: "translateX(-50%)",
        zIndex: "9999", maxWidth: "1100px", padding: "14px 22px",
        borderRadius: "8px", background: "rgba(10, 39, 33, .94)", color: "white",
        font: "600 20px/1.35 system-ui, sans-serif", textAlign: "center",
        boxShadow: "0 8px 30px rgba(0,0,0,.24)",
      });
      document.body.append(element);
    }
    element.textContent = value;
  }, text);
};

await page.goto(target, { waitUntil: "networkidle" });
await caption("Retail Demand Planner: 28-day SKU-store forecasts translated into a transparent stock-review decision.");
await pause(9000);
await caption("The committed study covers 1,000 deterministic M5 item-store histories. It is a subset study, not an official leaderboard score.");
await pause(9000);
await page.selectOption("#store-select", "TX_2");
await page.selectOption("#series-select", { index: 2 });
await caption("A planner can select a store and product; history, forecasts, intervals, assumed stock, and the suggested order update together.");
await pause(10000);
await page.locator("#chart").scrollIntoViewIfNeeded();
await caption("Sales-derived features stop before the origin. The shaded band is an empirically calibrated 80% interval, not a guarantee.");
await pause(10000);
await page.selectOption("#service", "0.95");
await caption("Changing the uncertainty cushion changes the proposed order. It never changes the underlying demand forecast.");
await pause(9000);
await page.locator("#performance").scrollIntoViewIfNeeded();
await caption("On the untouched holdout, tuned LightGBM reduced subset-hierarchy WRMSSE 23.2% versus the 28-day seasonal baseline.");
await pause(10000);
await page.getByText("Compare the forecasting methods").click();
await caption("Seven methods are compared over three expanding-window folds. The strong weekday blend remains close, limiting the claim of added ML value.");
await pause(11000);
await page.getByText("Explore inventory costs").click();
await page.locator("#cost-scenario").scrollIntoViewIfNeeded();
await caption("The inventory layer compares shortage and leftover costs under explicit assumptions; the numbers are arbitrary scenario units.");
await pause(10000);
await page.fill("#shortage-cost", "8");
await page.fill("#excess-cost", "2");
await caption("Cost assumptions change the retrospective decision comparison, not the forecast or future order rule.");
await pause(9000);
await page.getByText("Review stores and categories").click();
await caption("Store and category WAPE, bias, interval coverage, and monitoring flags expose where aggregate improvement hides weak segments.");
await pause(11000);
await page.locator("#guide").scrollIntoViewIfNeeded();
await caption("The API serves saved forecasts only. Training, SQL exports, provenance, tests, and monitoring run as separate reproducible workflows.");
await pause(10000);
await caption("Operational use still requires live inventory, lead times, access controls, staged validation, and ongoing champion/challenger monitoring.");
await pause(11000);

const video = page.video();
await context.close();
await video.saveAs(output);
await browser.close();
console.log(`saved: ${output}`);
