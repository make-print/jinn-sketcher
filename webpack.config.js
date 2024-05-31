const path = require('path');
const webpack = require('webpack');
const dotenv = require('dotenv');
const fs = require('fs');
const generateCSSScopedName = require('./build/cssScoopeGenerator')();
const libAssets = require('./build/libAssets');

// Load .env file and set process.env variables
dotenv.config();

const WEB_APP = path.join(__dirname, 'web/app');
const MODULES = path.join(__dirname, 'modules');
const NODE_MODULES = path.join(__dirname, 'node_modules');
const INTEGRATION_TESTS = path.join(__dirname, 'web/test');
const GLOBAL_CSS = path.join(__dirname, 'web/css');

module.exports = {
  mode: 'development',
  devtool: 'source-map',
  entry: {
    index: ['babel-polyfill', './web/app/index'],
    sketcher: ['babel-polyfill', './web/app/sketcher']
  },
  output: {
    path: path.join(__dirname, 'dist/static'),
    filename: '[name].bundle.js',
    chunkFilename: '[id].bundle.js',
    publicPath: '/static/'
  },
  externals: {
    'verb-nurbs': 'verb',
    'node-forge': 'commonjs node-forge',
    'node-pre-gyp': 'commonjs node-pre-gyp'
  },
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    modules: [MODULES, 'node_modules', WEB_APP],
    fallback: {
      'crypto': require.resolve('crypto-browserify'),
      'stream': require.resolve('stream-browserify'),
      'assert': require.resolve('assert'),
      'querystring': require.resolve('querystring-es3'),
      'url': require.resolve('url'),
      'buffer': require.resolve('buffer'),
      'process': require.resolve('process'),
      'os': require.resolve('os-browserify/browser'),
      'https': require.resolve('https-browserify'),
      'path': require.resolve('path-browserify'),
      'vm': require.resolve('vm-browserify'),
      'http': require.resolve('stream-http'),
      'net': require.resolve('net-browserify'),
      'zlib': require.resolve('browserify-zlib'),
      'tls': require.resolve('https-browserify'),
      'util': require.resolve('util/'),
      'fs': false, // Set 'fs' to false since it's not used directly
      'child_process': false // Set 'child_process' to false since it's not used directly
    }
  },
  devServer: {
    hot: false,
    liveReload: false,
    client: false,
    compress: true,
    allowedHosts: 'all',
    static: [
      path.join(__dirname, 'web'),
    ],
    setupMiddlewares(middlewares, devServer) {
      libAssets.forEach(asset => {
        devServer.app.get(`/lib-assets/${asset}`, function (req, res) {
          res.sendFile(path.join(NODE_MODULES, asset));
        });
      });
      return middlewares;
    }
  },
  module: {
    rules: [
      {
        test: /\.json$/,
        loader: 'json-loader',
        type: 'javascript/auto'
      },
      {
        test: /\.(js|jsx|ts|tsx)$/,
        loader: 'babel-loader',
        include: [MODULES, WEB_APP, INTEGRATION_TESTS]
      },
      // {
      //   test: /\.(ts|tsx)$/,
      //   loader: 'ts-loader',
      //   include: [MODULES, WEB_APP, path.resolve(__dirname, 'primitives/TypeScript')],
      //   exclude: /node_modules/
      // },
      {
        test: /\.(less|css)$/,
        include: [GLOBAL_CSS, INTEGRATION_TESTS],
        use: [
          'style-loader',
          'css-loader',
          'less-loader',
        ]
      },
      {
        test: /\.(css)$/,
        include: [NODE_MODULES],
        use: [
          'style-loader',
          'css-loader',
        ]
      },
      {
        oneOf: [
          {
            test: /\.(less|css)$/,
            include: [path.resolve(MODULES, 'ui/styles/global')],
            use: [
              'style-loader',
              'css-loader',
              'less-loader'
            ]
          },
          {
            test: /\.(less|css)$/,
            include: [MODULES, WEB_APP],
            use: [
              'style-loader',
              {
                loader: 'css-loader',
                options: {
                  modules: {
                    mode: 'local',
                    getLocalIdent: (context, localIdentName, localName) => generateCSSScopedName(localName, context.resourcePath),
                  },
                  url: false
                }
              },
              'less-loader'
            ]
          }
        ],
      },
      {
        test: /\.wasm$/,
        type: 'javascript/auto',
        loader: 'file-loader'
      },
      {
        test: /\.svg$/,
        loader: 'raw-loader'
      },
      {
        test: /\.(png|jpg|gif)$/i,
        use: [
          {
            loader: 'url-loader'
          },
        ],
      },
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      process: 'process/browser',
      Buffer: ['buffer', 'Buffer']
    }),
    new webpack.DefinePlugin({
      'process.env': JSON.stringify(process.env)
    })
  ],
  node: {
    __dirname: true
  }
};
