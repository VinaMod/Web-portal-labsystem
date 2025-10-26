async function loadCourses() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const coursesList = document.getElementById('courses-list');

    try {
        const response = await fetch('/courses');
        
        if (!response.ok) {
            throw new Error('Failed to load courses');
        }

        const data = await response.json();
        
        loading.style.display = 'none';
        coursesList.style.display = 'block';
        
        renderCoursesList(data.courses);
        
    } catch (err) {
        loading.style.display = 'none';
        error.textContent = 'Failed to load courses: ' + err.message;
        error.style.display = 'block';
    }
}

function renderCoursesList(courses) {
    const container = document.getElementById('courses-list');
    
    container.innerHTML = courses.map(course => `
        <div class="course-card-action">
            <h3>${course.name}</h3>
            <p>${course.description || 'No description available'}</p>
            <button class="btn btn-primary" onclick="registerForCourse(${course.id}, '${course.name}')">
                Register for Lab
            </button>
        </div>
    `).join('');
}

async function registerForCourse(courseId, courseName) {
    const error = document.getElementById('error');
    const success = document.getElementById('success');
    
    error.style.display = 'none';
    success.style.display = 'none';

    if (!AuthManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await AuthManager.fetchWithAuth('/register-lab', {
            method: 'POST',
            body: JSON.stringify({ course_id: courseId })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Registration failed');
        }

        const data = await response.json();
        
        success.textContent = `Successfully registered for ${courseName}! Lab "${data.lab.lab_name}" has been created.`;
        success.style.display = 'block';
        
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
        
    } catch (err) {
        error.textContent = 'Registration failed: ' + err.message;
        error.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (!AuthManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    loadCourses();
});
