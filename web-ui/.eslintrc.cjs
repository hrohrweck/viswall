module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh', 'jsx-a11y'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    // TODO(todo-30): re-enable during a11y sweep — 93 violations across pages/forms
    'jsx-a11y/label-has-associated-control': 'off',
    // TODO(todo-30): re-enable during a11y sweep — 4 violations (ConfirmDialog, Modal, FirewallTestSuite)
    'jsx-a11y/click-events-have-key-events': 'off',
    // TODO(todo-30): re-enable during a11y sweep — 4 violations (ConfirmDialog, Modal, FirewallTestSuite)
    'jsx-a11y/no-static-element-interactions': 'off',
  },
}
