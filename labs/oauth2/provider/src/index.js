const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Mock Database
const USERS = {
    'admin': { password: 'SuperSecurePassword_2026!@#', name: 'Administrator', role: 'admin' },
    'user': { password: 'user123', name: 'Regular User', role: 'user' }
};

const CODES = {}; // authorization_code -> { user, client_id, redirect_uri }
const TOKENS = {}; // access_token -> user

// Middleware to check login
const requireLogin = (req, res, next) => {
    const user = req.cookies.user;
    if (!user || !USERS[user]) {
        return res.redirect(`/login?next=${encodeURIComponent(req.originalUrl)}`);
    }
    req.user = USERS[user];
    req.user.username = user;
    next();
};

app.get('/login', (req, res) => {
    res.render('login', { next: req.query.next || '/' });
});

app.post('/login', (req, res) => {
    const { username, password, next } = req.body;
    if (USERS[username] && USERS[username].password === password) {
        res.cookie('user', username);
        return res.redirect(next || '/');
    }
    res.render('login', { error: 'Invalid credentials', next });
});

app.get('/logout', (req, res) => {
    res.clearCookie('user');
    const next = req.query.next || '/login';
    res.redirect(next);
});

// OAuth 2.0 Authorization Endpoint
app.get('/auth', requireLogin, (req, res) => {
    const { client_id, redirect_uri, response_type, state } = req.query;

    // VULNERABILITY: Weak validation of redirect_uri
    // Allows any URL that *contains* "localhost" or just doesn't check strictly enough
    // Ideally, it should be an exact match.
    // Here we will implement a very weak check or no check to simulate the vulnerability.

    // Let's say we allow any redirect_uri for demonstration purposes, 
    // or maybe check if it starts with http/https but don't validate the domain.

    if (!client_id || !redirect_uri) {
        return res.status(400).send('Missing parameters');
    }

    // Vulnerable Logic: Trusting the redirect_uri provided by the client
    // In a real secure app, we would check: if (ALLOWED_REDIRECT_URIS[client_id] !== redirect_uri) ...

    res.render('authorize', { client_id, redirect_uri, state, user: req.user });
});

app.post('/auth/approve', requireLogin, (req, res) => {
    const { client_id, redirect_uri, state, approve } = req.body;

    if (approve === 'yes') {
        const code = Math.random().toString(36).substring(2, 15);
        CODES[code] = { user: req.user, client_id, redirect_uri };

        const redirectUrl = new URL(redirect_uri);
        redirectUrl.searchParams.append('code', code);
        if (state) redirectUrl.searchParams.append('state', state);

        return res.redirect(redirectUrl.toString());
    }

    res.send('Access Denied');
});

// OAuth 2.0 Token Endpoint
app.post('/token', (req, res) => {
    const { code, client_id, client_secret, redirect_uri, grant_type } = req.body;

    if (grant_type !== 'authorization_code') {
        return res.status(400).json({ error: 'unsupported_grant_type' });
    }

    const authData = CODES[code];
    if (!authData) {
        return res.status(400).json({ error: 'invalid_code' });
    }

    // In a real app, we should verify client_secret and redirect_uri here too.
    // For this lab, we skip strict checks to focus on the redirect_uri vulnerability in /auth

    const token = Math.random().toString(36).substring(2, 15);
    TOKENS[token] = authData.user;
    delete CODES[code]; // Consume code

    res.json({ access_token: token, token_type: 'Bearer' });
});

app.get('/userinfo', (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'unauthorized' });
    }

    const token = authHeader.split(' ')[1];
    const user = TOKENS[token];

    if (!user) {
        return res.status(401).json({ error: 'invalid_token' });
    }

    res.json({
        sub: user.username,
        name: user.name,
        role: user.role,
        email: `${user.username}@socialid.local`
    });
});

app.get('/', (req, res) => {
    res.send(`<h1>SocialID Provider</h1><p>Logged in as: ${req.cookies.user || 'Guest'}</p>`);
});

app.listen(PORT, () => {
    console.log(`Provider listening on port ${PORT}`);
});
