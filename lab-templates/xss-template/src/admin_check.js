const puppeteer = require('puppeteer-core');

async function checkAdmin() {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/chromium'
    });
    
    try {
        const page = await browser.newPage();
        const baseUrl = 'http://localhost';
        
        // Đăng nhập admin
        await page.goto(`${baseUrl}/login.php`);
        await page.type('input[name="username"]', 'admin');
        await page.type('input[name="password"]', 'qwertyuiop');
        await page.click('button[type="submit"]');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('✅ Admin đăng nhập thành công!');
        
        // Kiểm tra các sản phẩm
        let xssFound = false;
        for (let productId = 1; productId <= 4; productId++) {
            console.log(`🔗 Admin truy cập: ${baseUrl}/product.php?id=${productId}`);
            
            await page.goto(`${baseUrl}/product.php?id=${productId}`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const currentUrl = page.url();
            if (currentUrl.includes('webhook.site')) {
                console.log(`🚨 XSS THÀNH CÔNG tại sản phẩm ${productId}!`);
                console.log(`💀 Cookie admin đã bị cướp: ${currentUrl}`);
                xssFound = true;
            } else {
                console.log(`✅ Sản phẩm ${productId}: An toàn`);
            }
        }
        
        // Kiểm tra admin panel
        console.log(`🔗 Admin truy cập: ${baseUrl}/admin.php`);
        await page.goto(`${baseUrl}/admin.php`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const adminUrl = page.url();
        if (adminUrl.includes('webhook.site')) {
            console.log('🚨 XSS TRONG ADMIN PANEL!');
            console.log(`💀 Cookie admin đã bị cướp: ${adminUrl}`);
            xssFound = true;
        } else {
            console.log('✅ Admin panel: An toàn');
        }
        
        if (xssFound) {
            console.log('💀 CẢNH BÁO: Admin đã bị tấn công XSS!');
        } else {
            console.log('✅ Tất cả trang đều an toàn');
        }
        
    } catch (error) {
        console.log(`❌ Lỗi: ${error.message}`);
    } finally {
        await browser.close();
    }
}

checkAdmin();
