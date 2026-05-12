const puppeteer = require('puppeteer-core');

const BASE_URL =
    process.env.BASE_URL || 'http://localhost';

const ADMIN_USERNAME =
    process.env.ADMIN_USERNAME || 'admin';

const ADMIN_PASSWORD =
    process.env.ADMIN_PASSWORD || 'qwertyuiop';

const CHROMIUM_PATH =
    process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/chromium';


async function checkAdmin() {

    console.log('[Bot] Starting admin bot...');

    let browser;

    try {

        browser = await puppeteer.launch({

            headless: true,

            executablePath: CHROMIUM_PATH,

            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--ignore-certificate-errors'
            ],

            dumpio: true,

            timeout: 60000,

            protocolTimeout: 60000
        });

        console.log('[Bot] Chromium launched successfully.');

        const page = await browser.newPage();

        // =====================================================
        // DEBUG EVENTS
        // =====================================================

        page.on('console', msg => {
            console.log(`[Browser Console] ${msg.text()}`);
        });

        page.on('pageerror', err => {
            console.log(`[Browser Page Error] ${err}`);
        });

        page.on('requestfailed', request => {
            console.log(
                `[Request Failed] ${request.url()} - ${request.failure()?.errorText}`
            );
        });

        // =====================================================
        // LOGIN
        // =====================================================

        const loginUrl = `${BASE_URL}/login.php`;

        console.log(`[Bot] Logging in: ${loginUrl}`);

        try {

            await page.goto(loginUrl, {
                waitUntil: 'domcontentloaded',
                timeout: 15000
            });

            const isLoginPage =
                await page.$('input[name="username"]');

            if (isLoginPage) {

                await page.type(
                    'input[name="username"]',
                    ADMIN_USERNAME
                );

                await page.type(
                    'input[name="password"]',
                    ADMIN_PASSWORD
                );

                await Promise.all([
                    page.click('button[type="submit"]'),
                    page.waitForNavigation({
                        waitUntil: 'networkidle0',
                        timeout: 15000
                    })
                ]);

                console.log('[Bot] Admin logged in successfully.');

            } else {

                console.log(
                    '[Bot] Already logged in or login form not found.'
                );
            }

        } catch (err) {

            console.log(
                `[Bot] Login failed: ${err.message}`
            );
        }

        // =====================================================
        // CHECK PRODUCTS
        // =====================================================

        let xssFound = false;

        for (let productId = 1; productId <= 4; productId++) {

            const targetUrl =
                `${BASE_URL}/product.php?id=${productId}`;

            console.log(
                `[Bot] Visiting product: ${targetUrl}`
            );

            try {

                await page.goto(targetUrl, {
                    waitUntil: 'domcontentloaded',
                    timeout: 15000
                });

                await new Promise(resolve =>
                    setTimeout(resolve, 2000)
                );

                const currentUrl = page.url();

                console.log(
                    `[Bot] Current URL: ${currentUrl}`
                );

                if (
                    currentUrl.includes('webhook.site')
                ) {

                    console.log(
                        `🚨 XSS SUCCESS at product ${productId}`
                    );

                    console.log(
                        `💀 Admin cookie stolen: ${currentUrl}`
                    );

                    xssFound = true;

                } else {

                    console.log(
                        `✅ Product ${productId} safe`
                    );
                }

            } catch (err) {

                console.log(
                    `[Bot] Product ${productId} error: ${err.message}`
                );
            }
        }

        // =====================================================
        // CHECK ADMIN PANEL
        // =====================================================

        const adminUrl =
            `${BASE_URL}/admin.php`;

        console.log(
            `[Bot] Visiting admin panel: ${adminUrl}`
        );

        try {

            await page.goto(adminUrl, {
                waitUntil: 'domcontentloaded',
                timeout: 15000
            });

            await new Promise(resolve =>
                setTimeout(resolve, 2000)
            );

            const currentAdminUrl = page.url();

            console.log(
                `[Bot] Current admin URL: ${currentAdminUrl}`
            );

            if (
                currentAdminUrl.includes('webhook.site')
            ) {

                console.log(
                    '🚨 XSS FOUND IN ADMIN PANEL'
                );

                console.log(
                    `💀 Admin cookie stolen: ${currentAdminUrl}`
                );

                xssFound = true;

            } else {

                console.log(
                    '✅ Admin panel safe'
                );
            }

        } catch (err) {

            console.log(
                `[Bot] Admin panel error: ${err.message}`
            );
        }

        // =====================================================
        // FINAL RESULT
        // =====================================================

        if (xssFound) {

            console.log(
                '💀 WARNING: Admin compromised by XSS'
            );

        } else {

            console.log(
                '✅ All pages appear safe'
            );
        }

    } catch (error) {

        console.error(
            '[Bot] Full Error:',
            error
        );

    } finally {

        if (browser) {

            try {

                await browser.close();

                console.log(
                    '[Bot] Browser closed.'
                );

            } catch (e) {

                console.log(
                    `[Bot] Browser close error: ${e.message}`
                );
            }
        }
    }
}


checkAdmin();
