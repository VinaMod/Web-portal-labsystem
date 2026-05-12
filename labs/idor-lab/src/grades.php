<?php
session_start();
require 'db.php';

if (!isset($_SESSION['user_id'])) {
    header("Location: index.php");
    exit;
}

$user_id = $_SESSION['user_id'];
$username = $_SESSION['username'];

// Parameters
$req_student_id = $_GET['student_id'] ?? '';
$req_class_id = $_GET['class_id'] ?? '';
$req_semester_id = $_GET['semester_id'] ?? '';

if (!$req_student_id || !$req_class_id || !$req_semester_id) {
    die("Missing parameters! Please provide student_id, class_id, and semester_id.");
}

// Get Vulnerability Mode from Environment Variable
$vuln_mode = getenv('ENV'); // 'student_id' or 'class_id'

// --- ACCESS CONTROL CHECKS ---
$access_denied = false;
$denial_reason = '';

// 1. Check Student Ownership (Can I view this student_id?)
// VULNERABILITY: If ENV=student_id, we SKIP this check.
if ($vuln_mode !== 'student_id') {
    if ($req_student_id != $user_id) {
        $access_denied = true;
        $denial_reason = "You are not authorized to view grades for student ID: {$req_student_id}";
    }
}

// 2. Check Class Enrollment (Am I enrolled in this class_id?)
// VULNERABILITY: If ENV=class_id, we SKIP this check.
// Note: This check is about whether the *current user* is allowed to access the class.
if (!$access_denied && $vuln_mode !== 'class_id') {
    // Normal behavior: Check if the logged-in user is enrolled in the requested class
    $stmt = $pdo->prepare("SELECT * FROM enrollments WHERE student_id = ? AND class_id = ?");
    $stmt->execute([$user_id, $req_class_id]);
    if (!$stmt->fetch()) {
        $access_denied = true;
        $denial_reason = "You are not enrolled in class ID: {$req_class_id}";
    }
}

// --- FETCH DATA ---
$grades = [];
$student_info = null;

if (!$access_denied) {
    // Query Logic:
    if ($vuln_mode === 'student_id') {
        // IDOR student_id: We allow finding the student's grades regardless of class_id
        // This makes exploitation easier (just change student_id)
        $stmt = $pdo->prepare("SELECT * FROM grades WHERE student_id = ? AND semester_id = ?");
        $stmt->execute([$req_student_id, $req_semester_id]);
    } else {
        // IDOR class_id: We enforce class_id check in the query
        // User must find the correct class_id to see data
        $stmt = $pdo->prepare("SELECT * FROM grades WHERE student_id = ? AND class_id = ? AND semester_id = ?");
        $stmt->execute([$req_student_id, $req_class_id, $req_semester_id]);
    }
    
    $grades = $stmt->fetchAll();
    
    // Get student info
    $stmt = $pdo->prepare("SELECT username FROM users WHERE id = ?");
    $stmt->execute([$req_student_id]);
    $student_info = $stmt->fetch();
}

// Calculate average
$average = 0;
if (!empty($grades)) {
    $total = array_sum(array_column($grades, 'score'));
    $average = round($total / count($grades), 1);
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grade Report - Student Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f0f4f8;
            color: #2d3748;
            min-height: 100vh;
        }

        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.25rem 2rem;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .navbar-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .navbar-logo {
            font-size: 24px;
        }

        .navbar-title {
            font-size: 18px;
            font-weight: 600;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: rgba(255, 255, 255, 0.15);
            padding: 0.5rem 1rem;
            border-radius: 12px;
        }

        .logout-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            padding: 0.5rem 1.25rem;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }

        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }

        .alert {
            background: linear-gradient(135deg, #fc5c7d 0%, #6a82fb 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 24px rgba(252, 92, 125, 0.3);
            animation: slideDown 0.5s ease-out;
        }

        .alert h2 {
            font-size: 22px;
            margin-bottom: 0.5rem;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
        }

        .stat-label {
            font-size: 13px;
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-icon {
            font-size: 32px;
            margin-bottom: 0.5rem;
        }

        .vuln-badge {
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
        }

        .main-content {
            background: white;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
            overflow: hidden;
        }

        .content-header {
            background: linear-gradient(135deg, #f6f8fb 0%, #e9ecf3 100%);
            padding: 2rem;
            border-bottom: 1px solid #e2e8f0;
        }

        .content-header h2 {
            font-size: 26px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .content-body {
            padding: 2rem;
        }

        .grade-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }

        .grade-table thead th {
            background: #f7fafc;
            padding: 1rem;
            text-align: left;
            font-weight: 700;
            color: #4a5568;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #e2e8f0;
        }

        .grade-table tbody tr {
            transition: all 0.2s;
        }

        .grade-table tbody tr:hover {
            background: #f8fafc;
        }

        .grade-table tbody td {
            padding: 1.25rem 1rem;
            border-bottom: 1px solid #edf2f7;
        }

        .subject-name {
            font-weight: 600;
            color: #2d3748;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .score-badge {
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 15px;
            min-width: 60px;
            text-align: center;
        }

        .score-excellent {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #065f46;
        }

        .score-good {
            background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
            color: #1e40af;
        }

        .score-average {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            color: #92400e;
        }

        .score-poor {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #991b1b;
        }

        .comment-text {
            color: #718096;
            font-size: 14px;
        }

        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: #a0aec0;
        }

        .empty-icon {
            font-size: 64px;
            margin-bottom: 1rem;
        }

        .mission-box {
            margin-top: 2rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, #fff5e6 0%, #ffe8cc 100%);
            border-radius: 16px;
            border-left: 4px solid #f59e0b;
        }

        .mission-box h3 {
            color: #92400e;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .mission-box ul {
            margin-left: 1.5rem;
            color: #78350f;
        }

        .mission-box li {
            margin-bottom: 0.5rem;
            line-height: 1.6;
        }

        .mission-box code {
            background: rgba(0, 0, 0, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="navbar-left">
                <div class="navbar-logo">🎓</div>
                <div class="navbar-title">Student Portal</div>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div class="user-info">
                    <span>👤 <?= htmlspecialchars($username) ?></span>
                    <span style="opacity: 0.7;">|</span>
                    <span style="opacity: 0.9;">ID: <?= $user_id ?></span>
                </div>
                <a href="logout.php" class="logout-btn">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <?php if ($access_denied): ?>
            <div class="alert">
                <h2>🚫 Access Denied</h2>
                <p><?= htmlspecialchars($denial_reason) ?></p>
            </div>
        <?php else: ?>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">👤</div>
                    <div class="stat-label">Student ID</div>
                    <div class="stat-value"><?= htmlspecialchars($req_student_id) ?></div>
                    <?php if ($student_info): ?>
                        <div style="margin-top: 0.5rem; color: #718096; font-size: 14px;">
                            <?= htmlspecialchars($student_info['username']) ?>
                        </div>
                    <?php endif; ?>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">📚</div>
                    <div class="stat-label">Class ID</div>
                    <div class="stat-value"><?= htmlspecialchars($req_class_id) ?></div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">📅</div>
                    <div class="stat-label">Semester</div>
                    <div class="stat-value"><?= htmlspecialchars($req_semester_id) ?></div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-label">Average Score</div>
                    <div class="stat-value"><?= $average ?></div>
                </div>
            </div>

            <div style="margin-bottom: 1.5rem; text-align: center;">
                <span style="color: #718096; margin-right: 0.5rem;">Vulnerable Parameter:</span>
                <span class="vuln-badge"><?= htmlspecialchars($vuln_mode) ?></span>
            </div>

            <div class="main-content">
                <div class="content-header">
                    <h2>
                        📋 Grade Report
                    </h2>
                    <p style="color: #718096; margin-top: 0.5rem;">
                        Detailed academic performance for the current semester
                    </p>
                </div>

                <div class="content-body">
                    <?php if (empty($grades)): ?>
                        <div class="empty-state">
                            <div class="empty-icon">📭</div>
                            <h3>No Grades Found</h3>
                            <p>There are no grades recorded for this combination of parameters.</p>
                        </div>
                    <?php else: ?>
                        <table class="grade-table">
                            <thead>
                                <tr>
                                    <th>Subject</th>
                                    <th>Score</th>
                                    <th>Teacher's Comments</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($grades as $grade): ?>
                                <?php
                                $score = $grade['score'];
                                $scoreClass = 'score-poor';
                                if ($score >= 85) $scoreClass = 'score-excellent';
                                elseif ($score >= 70) $scoreClass = 'score-good';
                                elseif ($score >= 50) $scoreClass = 'score-average';
                                ?>
                                <tr>
                                    <td>
                                        <div class="subject-name">
                                            📖 <?= htmlspecialchars($grade['subject_name']) ?>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="score-badge <?= $scoreClass ?>">
                                            <?= htmlspecialchars($score) ?>
                                        </span>
                                    </td>
                                    <td>
                                        <div class="comment-text">
                                            <?= htmlspecialchars($grade['comments']) ?>
                                        </div>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php endif; ?>

                    
                </div>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
