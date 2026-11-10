const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = ({ checkoutController }) => express.Router()
    .post('/api/checkout', asyncHandler(checkoutController.checkout));
