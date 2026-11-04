import fs from 'fs';
import path from 'path';

const FORBIDDEN_PATTERNS = [
  { name: 'Old circuit path', pattern: 'M4 6.5h5.25' },
  { name: 'Old circuit arrow', pattern: 'm17.2 14.75' },
  { name: 'Stepped path outside brand', pattern: 'M 36.5 18 L 26.5 18 A 12 12' },
  { name: 'Stepped arrow outside brand', pattern: 'M 43.5 28 L 49.5 34' },
];

const SRC_DIR = path.resolve('src');
const BRAND_DIR = path.resolve('src/components/brand');

const violations = [];

function scanDir(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (fullPath.startsWith(BRAND_DIR)) continue;
      scanDir(fullPath);
    } else if (/\.(tsx|ts|jsx|js|html)$/.test(entry.name)) {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const lines = content.split('\n');
      lines.forEach((line, idx) => {
        for (const { name, pattern } of FORBIDDEN_PATTERNS) {
          if (line.includes(pattern)) {
            violations.push({
              file: path.relative(SRC_DIR, fullPath),
              line: idx + 1,
              name,
              snippet: line.trim().slice(0, 80),
            });
          }
        }
      });
    }
  }
}

scanDir(SRC_DIR);

if (violations.length > 0) {
  console.error('\n❌ LOGO REGRESSION CHECK FAILED!');
  console.error(`Found ${violations.length} inline logo definitions outside src/components/brand/:\n`);
  for (const v of violations) {
    console.error(`  - ${v.file}:${v.line} (${v.name}): ${v.snippet}`);
  }
  process.exit(1);
} else {
  console.log('\n✅ LOGO INTEGRITY CHECK PASSED: Single source of truth enforced in src/components/brand/\n');
  process.exit(0);
}

