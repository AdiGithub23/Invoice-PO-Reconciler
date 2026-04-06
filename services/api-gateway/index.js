const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
const os = require('os');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://127.0.0.1:8001';
const UPLOAD_SERVICE_URL = process.env.UPLOAD_SERVICE_URL || 'http://127.0.0.1:8002';

// 1. Global Logger (Before CORS) to verify if requests even reach the Gateway
app.use((req, res, next) => {
    console.log(`[Gateway] Incoming ${req.method} ${req.url}`);
    next();
});

// 2. Explicit CORS handling for complex UI requests
app.use(cors({
    origin: '*', 
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
    optionsSuccessStatus: 204
}));

app.get('/health', (req, res) => {
    res.json({ status: 'API Gateway is healthy' });
});

app.use('/auth', createProxyMiddleware({
    target: AUTH_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/auth': '',
    },
}));

app.use('/upload', createProxyMiddleware({
    target: UPLOAD_SERVICE_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/upload': '',
    },
    onProxyReq: (proxyReq, req, res) => {
        console.log(`[Proxy] Routing ${req.method} ${req.url} -> ${UPLOAD_SERVICE_URL}${req.url}`);
    },
    onError: (err, req, res) => {
        console.error(`[Proxy Error] ${err.message}`);
        res.status(500).json({ error: 'Proxy error', message: err.message });
    }
}));

app.listen(PORT, () => {
    // console.log(`√ API Gateway running on http://localhost:${PORT}`);

    const hostname = process.env.HOSTNAME || os.hostname() || 'localhost';
    const protocol = process.env.NODE_ENV === 'production' ? 'https' : 'http';

    console.log(`=================================================`);
    console.log(`🚀 API Gateway is running on: ${protocol}://${hostname}:${PORT}`);
    console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`👉 Routing /auth   -> ${AUTH_SERVICE_URL}`);
    console.log(`👉 Routing /upload -> ${UPLOAD_SERVICE_URL}`);
    console.log(`=================================================`);
});


