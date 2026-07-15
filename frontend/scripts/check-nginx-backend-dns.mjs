import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const config = await readFile(new URL('../nginx.conf', import.meta.url), 'utf8')

assert.match(config, /resolver\s+127\.0\.0\.11\b/)
assert.match(config, /set\s+\$backend_upstream\s+backend:8000;/)
assert.match(config, /proxy_pass\s+http:\/\/\$backend_upstream;/)
assert.doesNotMatch(config, /proxy_pass\s+http:\/\/backend:/)
assert.match(config, /location\s+=\s+\/assets\s*\{[\s\S]*?try_files\s+\/index\.html\s+=404;/)

console.log('nginx backend DNS and /assets SPA routing contracts passed')
