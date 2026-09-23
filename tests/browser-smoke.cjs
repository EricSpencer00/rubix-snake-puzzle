// Real-browser checks for local previews or the deployed page.
// npm run test:browser -- [https://ericspencer.us/rubix-snake-puzzle/]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const {chromium} = require('playwright');

(async () => {
  const docs = path.resolve(__dirname, '../docs');
  const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'snake-browser-'));
  let server, browser;
  try {
    let url = process.argv[2];
    if (!url) {
      server = http.createServer((request, response) => {
        const pathname = new URL(request.url, 'http://localhost').pathname;
        const file = path.resolve(docs, '.' + (pathname === '/' ? '/index.html' : pathname));
        if (!file.startsWith(docs + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
          response.writeHead(404).end();
          return;
        }
        response.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : 'text/html');
        fs.createReadStream(file).pipe(response);
      });
      await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
      url = `http://127.0.0.1:${server.address().port}/`;
    }
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage({viewport: {width: 1280, height: 900}, reducedMotion: 'no-preference'});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url, {waitUntil: 'networkidle'});
    await page.locator('#joint-controls button').last().waitFor();
    assert.equal(await page.locator('#joint-controls button').count(), 92);
    assert.equal(await page.evaluate(() => builderGroup.children.length), 24);
    const hero = page.locator('#snake-canvas');
    const beforeHero = await hero.screenshot();
    await page.waitForTimeout(500);
    assert.ok(!beforeHero.equals(await hero.screenshot()), 'the hero animates');
    await page.screenshot({path: path.join(artifacts, 'desktop-hero.png')});

    const canvas = page.locator('#builder-canvas');
    const ballButton = page.getByRole('button', {name: 'Ball shape', exact: true});
    const overlapSwitch = page.getByRole('switch', {name: /Prevent overlaps/});
    const collisions = () => page.evaluate(() => detectCollisions(24, builderConfig).size);
    await ballButton.click();
    assert.equal(await collisions(), 0);
    await canvas.screenshot({path: path.join(artifacts, 'desktop-ball.png')});
    const ballConfig = await page.evaluate(() => builderConfig.slice());
    await page.getByRole('button', {name: 'Joint 1: 0 degrees', exact: true}).click();
    assert.deepEqual(await page.evaluate(() => builderConfig.slice()), ballConfig);
    assert.match(await page.locator('#builder-status').innerText(), /Turn skipped/);
    await overlapSwitch.uncheck();
    await page.getByRole('button', {name: 'Joint 1: 0 degrees', exact: true}).click();
    assert.ok(await collisions() > 0, 'the same turn overlaps when prevention is off');
    await overlapSwitch.check();
    assert.equal(await collisions(), 0, 'enabling prevention repairs existing overlap');
    for (let i = 0; i < 3; i++) {
      await page.getByRole('button', {name: 'Random valid', exact: true}).click();
      assert.equal(await collisions(), 0);
    }
    await ballButton.click();
    await page.getByRole('button', {name: 'Spin view', exact: true}).click();
    const beforeSpin = await canvas.screenshot();
    await page.waitForTimeout(500);
    assert.ok(!beforeSpin.equals(await canvas.screenshot()), 'the builder spins');
    await page.getByRole('button', {name: 'Pause view', exact: true}).click();
    const yaw = await page.evaluate(() => builderRotY);
    await canvas.press('ArrowRight');
    assert.ok(await page.evaluate(() => builderRotY) > yaw, 'keyboard rotation works');

    for (const width of [1280, 768, 390]) {
      await page.setViewportSize({width, height: 900});
      await page.evaluate(() => window.scrollTo({top: 0, behavior: 'instant'}));
      await page.waitForTimeout(250);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `page fits at ${width}px`);
      const clipped = await page.locator('.big-num-cell .value').evaluateAll(values => values.filter(value => {
        const range = document.createRange();
        range.selectNodeContents(value);
        return range.getBoundingClientRect().width > value.getBoundingClientRect().width + 1;
      }).map(value => value.textContent));
      assert.deepEqual(clipped, [], `number labels fit at ${width}px`);
      await page.screenshot({path: path.join(artifacts, `hero-${width}.png`)});
      await page.locator('.big-numbers').screenshot({path: path.join(artifacts, `counts-${width}.png`)});
      await canvas.screenshot({path: path.join(artifacts, `builder-${width}.png`)});
    }
    assert.deepEqual(errors, [], 'no runtime errors');
    console.log(JSON.stringify({url, passed: true, artifacts, checks: 'startup, 24 prisms, hero motion, ball, overlap switch, random shapes, spin, keyboard, desktop/tablet/mobile layout'}));
  } finally {
    await browser?.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
