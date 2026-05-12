const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const PROVIDER_PORT = process.env.PROVIDER_PORT || '3000';
const PROVIDER_URL = `http://${process.env.PROVIDER_HOST || 'oauth-provider'}:${PROVIDER_PORT}`;
const CLIENT_URL = process.env.CLIENT_URL || `http://${process.env.CLIENT_HOST || 'oauth-client'}:80`;
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin_secret';

async function visitUrl(targetUrl) {
    console.log(`[Bot] Visiting: ${targetUrl}`);
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors'
            ],
            dumpio: true,
            timeout: 60000
        });
        const page = await browser.newPage();


        // 1. Determine Login URL based on Target URL
        // If target is the Provider (contains /auth), we must login to that specific origin
        // to have the correct cookies.
        let loginUrl = `${PROVIDER_URL}/login`;
        try {
            const urlObj = new URL(targetUrl);
            // Heuristic: If target has port 3000 (Provider port), use its origin
            if (urlObj.port === '${webTestPort}' || targetUrl.includes('/auth')) {
                loginUrl = `${urlObj.origin}/login`;
                console.log(`[Bot] Detected Provider link. Logging in to: ${loginUrl}`);
            }
        } catch (e) {
            console.log('[Bot] Could not parse target URL for login origin, using default.');
        }

        // 2. Log in
        console.log(`[Bot] Logging in to ${loginUrl}...`);
        try {
            await page.goto(loginUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });

            // Check if we are actually on a login page (we might already be logged in or error)
            const isLoginPage = await page.$('input[name="username"]');
            if (isLoginPage) {
                await page.type('input[name="username"]', ADMIN_USERNAME);
                await page.type('input[name="password"]', ADMIN_PASSWORD);
                await Promise.all([
                    page.click('button[type="submit"]'),
                    page.waitForNavigation({ waitUntil: 'networkidle0' })
                ]);
                console.log('[Bot] Logged in successfully.');
            } else {
                console.log('[Bot] Already logged in or not a login page.');
            }
        } catch (err) {
            console.log(`[Bot] Login failed (might be unreachable): ${err.message}`);
            // Continue anyway, maybe the target doesn't require login or is external
        }

        // 2. Visit the malicious URL
        console.log(`[Bot] Navigating to target URL: ${targetUrl}`);
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
        console.log(`[Bot] Current URL after target load: ${page.url()}`);

        // If the exploit works, the bot will be redirected to the attacker's site,
        // and the attacker will get the code.
        // If the link is a valid OAuth flow, the bot might see the "Authorize" page.
        // We should handle the "Authorize" page if it appears (auto-approve).

        let approveButton = null;
        try {
            approveButton = await page.waitForSelector('button[value="yes"]', { timeout: 2000 });
        } catch (e) {
            // No approve button found within timeout
        }

        if (approveButton || page.url().includes('/auth')) {
            console.log('[Bot] On Authorize page. Auto-approving...');
            try {
                await Promise.all([
                    approveButton ? approveButton.click() : page.click('button[value="yes"]'),
                    page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 10000 })
                ]);
                console.log('[Bot] Approved.');
            } catch (e) {
                console.log('[Bot] No authorize button found or already approved.');
            }
        }

        console.log(`[Bot] Finished visiting ${targetUrl}`);

    } catch (error) {
        console.error('[Bot] Error:', error.message);
    } finally {
        if (browser) await browser.close();
    }
}

app.post('/visit', async (req, res) => {
    const { url } = req.body;
    if (!url) {
        return res.status(400).send('Missing URL');
    }

    // Non-blocking visit
    visitUrl(url);

    res.send('Admin is visiting your URL...');
});

app.listen(PORT, () => {
    console.log(`Admin Bot listening on port ${PORT}`);
});
