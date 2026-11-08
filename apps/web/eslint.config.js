import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import hooks from 'eslint-plugin-react-hooks'
import globals from 'globals'
export default tseslint.config(js.configs.recommended, ...tseslint.configs.recommended, {files:['src/**/*.js'],languageOptions:{globals:globals.worker}}, {
  files: ['src/**/*.{ts,tsx}'], languageOptions: { globals: {...globals.browser,...globals.worker} },
  plugins: { 'react-hooks': hooks }, rules: { ...hooks.configs.recommended.rules, 'react-hooks/set-state-in-effect': 'off', 'react-hooks/refs': 'off', 'react-hooks/exhaustive-deps': 'off' }
})
