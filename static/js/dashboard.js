async function loadDashboard() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const content = document.getElementById('dashboard-content');

    try {
        const response = await AuthManager.fetchWithAuth('/dashboard');
        
        if (!response.ok) {
            throw new Error('Failed to load dashboard');
        }

        const data = await response.json();
        
        loading.style.display = 'none';
        content.style.display = 'block';
        
        renderStats(data);
        renderCourses(data.courses);
        
    } catch (err) {
        loading.style.display = 'none';
        error.textContent = 'Failed to load dashboard: ' + err.message;
        error.style.display = 'block';
    }
}

function renderStats(data) {
    const totalCourses = data.courses.length;
    let totalLabs = 0;
    let completedLabs = 0;
    let activeLabs = 0;

    data.courses.forEach(course => {
        totalLabs += course.labs.length;
        course.labs.forEach(lab => {
            if (lab.status === 'COMPLETED') completedLabs++;
            if (lab.status === 'STARTED') activeLabs++;
        });
    });

    document.getElementById('total-courses').textContent = totalCourses;
    document.getElementById('total-labs').textContent = totalLabs;
    document.getElementById('completed-labs').textContent = completedLabs;
    document.getElementById('active-labs').textContent = activeLabs;
}

function renderCourses(courses) {
    const container = document.getElementById('courses-container');
    
    if (courses.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-light);">
                <p>You haven't enrolled in any courses yet.</p>
                <a href="/labs" class="btn btn-primary" style="margin-top: 1rem;">Browse Available Labs</a>
            </div>
        `;
        return;
    }

    container.innerHTML = courses.map(course => `
        <div class="course-card">
            <div class="course-header">
                <h3>${course.name}</h3>
                <p>${course.description || ''}</p>
            </div>
            <div class="course-body">
                <div class="labs-list">
                    ${renderLabs(course.labs)}
                </div>
            </div>
        </div>
    `).join('');
}

function renderLabs(labs) {
    if (labs.length === 0) {
        return '<p style="color: var(--text-light);">No labs registered yet.</p>';
    }

    return labs.map(lab => `
        <div class="lab-item">
            <div class="lab-info">
                <h4>${lab.lab_name}</h4>
                <p>Template: ${lab.template_name}</p>
            </div>
            <div>
                <span class="lab-status-badge status-${lab.status.toLowerCase()}">${lab.status}</span>
                ${lab.status !== 'COMPLETED' ? `
                    <a href="/terminal/${lab.id}" class="btn btn-primary" style="margin-left: 1rem;">
                        Open Terminal
                    </a>
                ` : ''}
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    if (!AuthManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    loadDashboard();
});
