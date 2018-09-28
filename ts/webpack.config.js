const path = require('path');

module.exports = {
    mode: "production",
    entry: './expenses.ts',
    output: {
        path: path.resolve(__dirname, '..', 'expenses', 'static', 'expenses'),
        filename: 'expenses.js'
    },
    resolve: {
        // Add '.ts' and '.tsx' as a resolvable extension.
        extensions: [".ts", ".tsx", ".js"]
    },
    module: {
        rules: [
            // all files with a '.ts' or '.tsx' extension will be handled by 'ts-loader'
            { test: /\.tsx?$/, loader: "ts-loader" }
        ]
    }
};
