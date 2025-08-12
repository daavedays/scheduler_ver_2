module.exports = function override(config) {
  // Workaround for MUI X date-fns deep ESM imports under CRA5/Webpack 5
  // Ensure extension-less deep imports resolve
  if (!config.resolve) config.resolve = {};
  if (!config.resolve.extensionAlias) config.resolve.extensionAlias = {};
  // No-op; main fix is to disable fullySpecified for date-fns deep imports via module rules
  config.module.rules.push({
    test: /node_modules\/date-fns\/.*\.js$/,
    resolve: { fullySpecified: false },
  });
  config.module.rules.push({
    test: /node_modules\/@mui\/(x-date-pickers|x-date-pickers-pro)\/esm\/AdapterDateFns\/.*\.js$/,
    resolve: { fullySpecified: false },
  });
  return config;
}


