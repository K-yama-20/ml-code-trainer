import { spawnSync } from 'node:child_process'
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','browser-content','--output','test-results-browser','--reporter','list'],{stdio:'inherit',env:{...process.env,RUN_BROWSER_CONTENT:'1'}})
process.exit(result.status??1)
