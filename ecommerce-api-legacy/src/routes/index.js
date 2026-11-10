const checkoutRoutes = require('./checkoutRoutes');
const reportRoutes = require('./reportRoutes');
const userRoutes = require('./userRoutes');

module.exports = (deps) => [checkoutRoutes(deps), reportRoutes(deps), userRoutes(deps)];
