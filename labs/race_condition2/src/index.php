<?php
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

$user_id = $_SESSION['user_id'];
$username = $_SESSION['username'];

// Get user's order
$stmt = $pdo->prepare("SELECT * FROM orders WHERE user_id = ?");
$stmt->execute([$user_id]);
$order = $stmt->fetch();

// If no order exists (shouldn't happen if registered correctly), create one
if (!$order) {
    $stmt = $pdo->prepare("INSERT INTO orders (user_id, total_price, coupon_applied) VALUES (?, 500000, 0)");
    $stmt->execute([$user_id]);
    header("Refresh:0");
    exit;
}

// Generate Dynamic Flag
$flag = "";
if ($order['total_price'] <= 0) {
    $date = new DateTime("now", new DateTimeZone('Asia/Ho_Chi_Minh'));
    $date_str = $date->format('dmY');
    $email = getenv('EMAIL') ?: 'carl@techvision.com';
    $randomKey = getenv('RANDOM_KEY') ?: 'undefined';
    $raw = $date_str . '_' . $email . '_race_condition_2';
    $flag = "FLAG{" . sha1($raw) . "}:" . $randomKey;
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fashion Store</title>
    <link rel="stylesheet" href="style.css?v=6">
</head>
<body>
    <nav class="navbar">
        <a href="#" class="brand">FASHION.</a>
        <div class="nav-right">
            <a href="history.php">Lịch Sử</a>
            <span style="margin: 0 10px; color: #ccc;">|</span>
            <span>Chào, <b><?php echo htmlspecialchars($username); ?></b></span>
            <a href="logout.php">Đăng Xuất</a>
        </div>
    </nav>

    <div class="hero">
        <h1>Summer Collection 2024</h1>
        <p>Phong cách tối giản. Chất lượng thượng hạng.</p>
    </div>

    <div class="container">
        <div class="product-grid">
            <!-- Product 1 -->
            <div class="product-card">
                <div class="product-img" style="background-image: url('images/tshirt.png');"></div>
                <div class="product-details">
                    <div class="p-name">Áo Thun Basic White</div>
                    <div class="p-price">200.000₫</div>
                    <button class="btn-buy" disabled>Hết Hàng</button>
                </div>
            </div>

            <!-- Product 2 -->
            <div class="product-card">
                <div class="product-img" style="background-image: url('images/jeans.png');"></div>
                <div class="product-details">
                    <div class="p-name">Quần Jeans Slimfit</div>
                    <div class="p-price">500.000₫</div>
                    <button class="btn-buy" disabled>Hết Hàng</button>
                </div>
            </div>

            <!-- Product 3 - The Flag Item -->
            <div class="product-card" onclick="openModal()">
                <div class="product-img" style="background-image: url('images/jacket.png');">
                     <span style="position: absolute; top: 10px; right: 10px; background: #000; color: #fff; padding: 5px 10px; font-weight: bold; font-size: 0.8rem;">LIMITED</span>
                </div>
                <div class="product-details">
                    <div class="p-name">Áo Khoác Hacker (Special)</div>
                    <div class="p-price" style="color: var(--danger); font-weight: bold;">
                        Giá: <?php echo number_format($order['total_price'], 0, ',', '.'); ?>₫
                    </div>
                    <button class="btn-buy">MUA NGAY</button>
                </div>
            </div>
            
             <!-- Product 4 -->
            <div class="product-card">
                 <div class="product-img" style="background-image: url('images/hoodie.png');"></div>
                <div class="product-details">
                    <div class="p-name">Hoodie Streetwear</div>
                    <div class="p-price">800.000₫</div>
                    <button class="btn-buy" disabled>Hết Hàng</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Purchase -->
    <div id="modal" class="modal-overlay">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <h2 style="text-transform: uppercase; margin-top: 0;">Thanh Toán</h2>
            
            <div style="background: #f9f9f9; padding: 1rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>Sản phẩm:</span>
                    <strong>Áo Khoác Hacker</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Tổng tiền:</span>
                    <strong style="color: var(--danger); font-size: 1.2rem;">
                        <?php echo number_format($order['total_price'], 0, ',', '.'); ?>₫
                    </strong>
                </div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
                   Trạng thái Coupon: <?php echo $order['coupon_applied'] ? 'Đã áp dụng' : 'Chưa dùng'; ?>
                </div>
            </div>

            <?php if ($flag): ?>
                <div class="flag-display">
                    <div>CHÚC MỪNG! BẠN ĐÃ CHIẾN THẮNG.</div>
                    <div style="font-size: 1.2rem; margin-top: 10px; color: #fff; font-weight: bold;"><?php echo $flag; ?></div>
                    <div style="font-size: 0.8rem; margin-top: 5px; color: #ccc;">(Vui lòng chụp lại Flag này)</div>
                </div>
            <?php else: ?>
                <div style="margin-bottom: 1rem;">
                    <label style="font-weight: bold; font-size: 0.9rem;">Mã Giảm Giá:</label>
                    <div style="display: flex; gap: 10px; margin-top: 5px;">
                        <input type="text" value="DC250" readonly style="margin:0; background: #eee;">
                        <button onclick="applyCoupon()" style="background: var(--text-main); color: #fff; border: none; padding: 0 1rem; font-weight: bold; cursor: pointer;">ÁP DỤNG</button>
                    </div>
                    <small style="color: #666;">Giảm 250.000₫ cho mỗi mã hợp lệ.</small>
                </div>
            <?php endif; ?>

            <div style="text-align: center; margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem;">
                 <?php if ($order['total_price'] <= 0): ?> <!-- Technically allows checkout at 0 only? Or any price? User wants to buy. Let's allow buy anytime but only 0 gets flag. -->
                    <button onclick="purchaseOrder()" style="width: 100%; padding: 15px; background: var(--success); color: white; border: none; font-weight: bold; cursor: pointer; font-size: 1.1rem; margin-bottom: 1rem;">THANH TOÁN NGAY</button>
                 <?php else: ?>
                     <button onclick="purchaseOrder()" style="width: 100%; padding: 15px; background: #000; color: white; border: none; font-weight: bold; cursor: pointer; font-size: 1.1rem; margin-bottom: 1rem;">THANH TOÁN (<?php echo number_format($order['total_price'], 0, ',', '.'); ?>₫)</button>
                 <?php endif; ?>

                <a href="reset.php" style="color: red; font-size: 0.8rem; text-decoration: none;">[ Hủy áp dụng Voucher ]</a>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div id="toast-container" class="toast-container"></div>

    <script>
        function openModal() {
            document.getElementById('modal').classList.add('modal-open');
        }
        function closeModal() {
            document.getElementById('modal').classList.remove('modal-open');
        }
        
        // Close modal when clicking outside
        document.getElementById('modal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });

        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerText = message;
            
            container.appendChild(toast);

            // Remove after 3 seconds
            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.3s ease forwards';
                toast.addEventListener('animationend', () => {
                    toast.remove();
                });
            }, 3000);
        }

        function applyCoupon() {
            const btn = document.querySelector('button[onclick="applyCoupon()"]');
            btn.disabled = true;
            btn.innerText = "Đang xử lý...";

            fetch('apply_coupon.php')
                .then(response => {
                    if (!response.ok) throw new Error("Coupon lỗi hoặc đã dùng!");
                    return response.text();
                })
                .then(data => {
                    showToast("Thành công: " + data, 'success');
                    setTimeout(() => location.reload(), 1500);
                })
                .catch(err => {
                    showToast("Lỗi: " + err.message, 'error');
                    btn.disabled = false;
                    btn.innerText = "ÁP DỤNG";
                });
        }

        function purchaseOrder() {
            if (!confirm("Xác nhận thanh toán đơn hàng?")) return;

            fetch('checkout.php')
                .then(response => {
                    if (!response.ok) throw new Error("Lỗi thanh toán");
                    return response.text();
                })
                .then(data => {
                    showToast(data, 'success');
                    setTimeout(() => window.location.href = 'history.php', 1000);
                })
                .catch(err => {
                    showToast(err.message, 'error');
                });
        }
    </script>
</body>
</html>
