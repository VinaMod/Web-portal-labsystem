const AuthManager = {
    getToken() {
        return localStorage.getItem('jwt_token');
    },

    setToken(token) {
        localStorage.setItem('jwt_token', token);
    },

    clearToken() {
        localStorage.removeItem('jwt_token');
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    async fetchWithAuth(url, options = {}) {
        const token = this.getToken();
        
        if (!token) {
            window.location.href = '/login';
            throw new Error('Not authenticated');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            this.clearToken();
            window.location.href = '/login?error=Session expired';
            throw new Error('Unauthorized');
        }

        return response;
    },

    logout() {
        this.clearToken();
        window.location.href = '/login';
    }
};

window.AuthManager = AuthManager;
