const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://localhost:8001';
const UPLOAD_SERVICE_URL = process.env.UPLOAD_SERVICE_URL || 'http://localhost:8002';

app.use(cors());

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


