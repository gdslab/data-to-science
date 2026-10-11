const {
    defineConfig,
    globalIgnores,
} = require("eslint/config");

const globals = require("globals");

const {
    fixupConfigRules,
} = require("@eslint/compat");

const tsParser = require("@typescript-eslint/parser");
const reactRefresh = require("eslint-plugin-react-refresh");
const js = require("@eslint/js");

const {
    FlatCompat,
} = require("@eslint/eslintrc");

const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

module.exports = defineConfig([{
    languageOptions: {
        globals: {
            ...globals.browser,
        },

        parser: tsParser,
    },

    extends: fixupConfigRules(compat.extends(
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:react-hooks/recommended",
    )),

    plugins: {
        "react-refresh": reactRefresh,
    },

    rules: {
        // Disable overly aggressive React Compiler rules (not using compiler yet)
        "react-refresh/only-export-components": "off",
        "react-hooks/set-state-in-effect": "off",
        "react-hooks/immutability": "off",
        "react-hooks/incompatible-library": "off",

        // Keep useful rules that catch real bugs
        "@typescript-eslint/no-unused-vars": ["error", {
            "argsIgnorePattern": "^_",
            "varsIgnorePattern": "^_",
            "destructuredArrayIgnorePattern": "^_"
        }],
    },
}, globalIgnores([
    "**/dist",
    "**/public",
    "**/src/vendor",
    "**/.eslintrc.cjs",
    "eslint.config.cjs"
])]);
