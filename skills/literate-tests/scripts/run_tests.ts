#!/usr/bin/env npx tsx
/**
 * Literate Test Runner for TypeScript
 * Parses markdown test files and validates assertions.
 *
 * Requirements: tsx (`npm install -D tsx`)
 *
 * Copy this file to your project's tests/ directory:
 *     cp run_tests.ts /path/to/project/tests/
 *
 * Run from project root:
 *     npx tsx tests/run_tests.ts
 *
 * Or with ts-node:
 *     npx ts-node tests/run_tests.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import * as vm from 'vm';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let totalPassed = 0;
let totalFailed = 0;

interface TestCase {
    name: string;
    section: string;
    code: string;
    assertions: Assertion[];
}

interface Assertion {
    type: 'expect' | 'error' | 'throws';
    expression: string;
    expected?: string;
    errorCode?: string;
    errorType?: string;
}

interface TestResult {
    passed: boolean;
    message: string;
}

interface Config {
    module?: string;
    import?: string[];
    [key: string]: string | string[] | undefined;
}

/**
 * Parse TOML-like frontmatter from markdown content
 */
function parseFrontmatter(content: string): Config {
    const config: Config = {};
    const match = content.match(/^```toml\n([\s\S]*?)```/m);

    if (match) {
        for (const line of match[1].split('\n')) {
            const trimmed = line.trim();
            if (trimmed.startsWith('#') || !trimmed) continue;

            const eqIndex = trimmed.indexOf('=');
            if (eqIndex > 0) {
                const key = trimmed.slice(0, eqIndex).trim();
                let value: string | string[] = trimmed.slice(eqIndex + 1).trim();

                // Remove quotes
                value = value.replace(/^["']|["']$/g, '');

                // Parse arrays
                if (value.startsWith('[') && value.endsWith(']')) {
                    value = value.slice(1, -1).split(',')
                        .map(v => v.trim().replace(/^["']|["']$/g, ''))
                        .filter(v => v);
                }

                config[key] = value;
            }
        }
    }

    return config;
}

/**
 * Extract test cases from markdown content
 */
function extractTests(content: string): TestCase[] {
    const tests: TestCase[] = [];
    let currentSection = '';
    let currentTest = '';
    let inCodeBlock = false;
    let codeLines: string[] = [];
    let assertions: Assertion[] = [];
    let lineNumber = 0;
    let blockStartLine = 0;

    const lines = content.split('\n');

    for (const line of lines) {
        lineNumber++;

        // Track section headers
        const sectionMatch = line.match(/^## (.+)$/);
        if (sectionMatch) {
            currentSection = sectionMatch[1];
            continue;
        }

        const testMatch = line.match(/^### (.+)$/);
        if (testMatch) {
            currentTest = testMatch[1];
            continue;
        }

        // Start of code block
        const codeStartMatch = line.match(/^```(ts|typescript)$/);
        if (codeStartMatch && !inCodeBlock) {
            inCodeBlock = true;
            blockStartLine = lineNumber;
            codeLines = [];
            assertions = [];
            continue;
        }

        // End of code block
        if (line === '```' && inCodeBlock) {
            inCodeBlock = false;
            if (assertions.length > 0) {
                tests.push({
                    name: currentTest || `Test at line ${blockStartLine}`,
                    section: currentSection,
                    code: codeLines.join('\n'),
                    assertions: [...assertions]
                });
            }
            continue;
        }

        // Inside code block
        if (inCodeBlock) {
            const expectMatch = line.match(/\/\/\s*expect:\s*(.+)$/);
            const errorMatch = line.match(/\/\/\s*error:\s*(.+)$/);
            const throwsMatch = line.match(/\/\/\s*throws:\s*(.+)$/);

            if (expectMatch) {
                const expr = line.split('//')[0].trim();
                assertions.push({
                    type: 'expect',
                    expression: expr,
                    expected: expectMatch[1].trim()
                });
            } else if (errorMatch) {
                const expr = line.split('//')[0].trim();
                let errorCode = errorMatch[1].trim();
                if (errorCode.startsWith('[') && errorCode.endsWith(']')) {
                    errorCode = errorCode.slice(1, -1);
                }
                assertions.push({
                    type: 'error',
                    expression: expr,
                    errorCode
                });
            } else if (throwsMatch) {
                const expr = line.split('//')[0].trim();
                assertions.push({
                    type: 'throws',
                    expression: expr,
                    errorType: throwsMatch[1].trim()
                });
            } else {
                codeLines.push(line);
            }
        }
    }

    return tests;
}

/**
 * Parse expected value and compare with actual
 */
function checkExpected(expected: string, actual: unknown): boolean {
    expected = expected.trim();

    // Handle approx() matcher
    const approxMatch = expected.match(/^approx\(([^,]+),\s*tol=([^)]+)\)$/);
    if (approxMatch) {
        const target = parseFloat(approxMatch[1]);
        const tolerance = parseFloat(approxMatch[2]);
        return typeof actual === 'number' && Math.abs(actual - target) <= tolerance;
    }

    // Handle contains() matcher
    const containsMatch = expected.match(/^contains\("([^"]+)"\)$/);
    if (containsMatch) {
        return String(actual).includes(containsMatch[1]);
    }

    // Handle matches() matcher
    const matchesMatch = expected.match(/^matches\(\/([^/]+)\/\)$/);
    if (matchesMatch) {
        return new RegExp(matchesMatch[1]).test(String(actual));
    }

    // Handle arrays
    if (expected.startsWith('[') && expected.endsWith(']')) {
        try {
            const expectedArr = JSON.parse(expected);
            return JSON.stringify(actual) === JSON.stringify(expectedArr);
        } catch {
            return String(actual) === expected;
        }
    }

    // Handle strings
    if (expected.startsWith('"') && expected.endsWith('"')) {
        return actual === expected.slice(1, -1);
    }

    // Handle numbers
    if (!isNaN(Number(expected))) {
        return actual === parseFloat(expected);
    }

    // Handle booleans
    if (expected === 'true') return actual === true;
    if (expected === 'false') return actual === false;
    if (expected === 'null') return actual === null;
    if (expected === 'undefined') return actual === undefined;

    // String comparison
    return String(actual) === expected;
}

/**
 * Run a single test case
 */
function runTest(test: TestCase, moduleExports: Record<string, unknown>): TestResult {
    // Build context with module exports
    const context: Record<string, unknown> = {
        ...moduleExports,
        console,
        setTimeout,
        setInterval,
        clearTimeout,
        clearInterval,
        Buffer,
        process
    };

    vm.createContext(context);

    // Run setup code
    try {
        vm.runInContext(test.code, context);
    } catch (err) {
        return { passed: false, message: `Setup failed: ${(err as Error).message}` };
    }

    // Check assertions
    for (const assertion of test.assertions) {
        if (assertion.type === 'expect') {
            try {
                const actual = vm.runInContext(assertion.expression, context);
                if (!checkExpected(assertion.expected!, actual)) {
                    return {
                        passed: false,
                        message: `Expected ${assertion.expected}, got ${JSON.stringify(actual)}`
                    };
                }
            } catch (err) {
                return {
                    passed: false,
                    message: `Expression failed: ${(err as Error).message}`
                };
            }
        } else if (assertion.type === 'error') {
            try {
                vm.runInContext(assertion.expression, context);
                return {
                    passed: false,
                    message: `Expected error [${assertion.errorCode}] but none was thrown`
                };
            } catch (err) {
                const error = err as Error & { code?: string };
                const code = error.code || error.name;
                if (code !== assertion.errorCode) {
                    return {
                        passed: false,
                        message: `Expected error [${assertion.errorCode}], got [${code}]: ${error.message}`
                    };
                }
            }
        } else if (assertion.type === 'throws') {
            try {
                vm.runInContext(assertion.expression, context);
                return {
                    passed: false,
                    message: `Expected ${assertion.errorType} to be thrown but nothing was thrown`
                };
            } catch (err) {
                const error = err as Error;
                if (error.name !== assertion.errorType && error.constructor.name !== assertion.errorType) {
                    return {
                        passed: false,
                        message: `Expected ${assertion.errorType}, got ${error.name}: ${error.message}`
                    };
                }
            }
        }
    }

    return { passed: true, message: 'OK' };
}

/**
 * Load module exports based on config
 */
async function loadModuleExports(config: Config): Promise<Record<string, unknown>> {
    const exports: Record<string, unknown> = {};
    const modulePath = config.module;
    const importNames = config.import || [];

    if (!modulePath) return exports;

    try {
        // Resolve relative to tests directory parent (project root)
        const fullPath = path.resolve(process.cwd(), '..', modulePath);
        const mod = await import(fullPath);

        for (const name of importNames) {
            if (name in mod) {
                exports[name] = mod[name];
            } else if (mod.default && name in mod.default) {
                exports[name] = mod.default[name];
            } else {
                console.log(`  Warning: ${name} not found in ${modulePath}`);
            }
        }
    } catch (err) {
        console.log(`  Warning: Could not import ${modulePath}: ${(err as Error).message}`);
    }

    return exports;
}

/**
 * Process a single markdown test file
 */
async function processFile(filePath: string): Promise<void> {
    const content = fs.readFileSync(filePath, 'utf-8');
    const config = parseFrontmatter(content);
    const tests = extractTests(content);

    console.log();
    console.log('='.repeat(60));
    console.log(`  ${path.basename(filePath)}`);
    console.log('='.repeat(60));

    if (tests.length === 0) {
        console.log('  No tests found');
        return;
    }

    const moduleExports = await loadModuleExports(config);
    let currentSection = '';

    for (const test of tests) {
        if (test.section !== currentSection) {
            currentSection = test.section;
            console.log();
            console.log(`  ${currentSection}`);
            console.log(`  ${'-'.repeat(currentSection.length)}`);
        }

        const result = runTest(test, moduleExports);

        if (result.passed) {
            console.log(`  \x1b[32m✓\x1b[0m ${test.name}`);
            totalPassed++;
        } else {
            console.log(`  \x1b[31m✗\x1b[0m ${test.name}`);
            console.log(`      ${result.message}`);
            totalFailed++;
        }
    }
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
    const scriptDir = __dirname;
    let testsDir: string;

    if (path.basename(scriptDir) === 'tests') {
        testsDir = scriptDir;
    } else {
        testsDir = path.join(scriptDir, 'tests');
    }

    if (!fs.existsSync(testsDir)) {
        console.log('No tests/ directory found');
        process.exit(1);
    }

    const testFiles = fs.readdirSync(testsDir)
        .filter(f => f.endsWith('.md'))
        .map(f => path.join(testsDir, f))
        .sort();

    if (testFiles.length === 0) {
        console.log('No .md test files found in tests/');
        process.exit(1);
    }

    for (const file of testFiles) {
        await processFile(file);
    }

    console.log();
    console.log('='.repeat(60));
    console.log(`  Summary: ${totalPassed} passed, ${totalFailed} failed`);
    console.log('='.repeat(60));
    console.log();

    process.exit(totalFailed > 0 ? 1 : 0);
}

main();
