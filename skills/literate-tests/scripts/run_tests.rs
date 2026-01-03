#!/usr/bin/env rust-script
//! Literate Test Runner for Rust
//! Parses markdown test files and validates assertions.
//!
//! Requirements: rust-script (`cargo install rust-script`)
//!
//! Copy this file to your project's tests/ directory:
//!     cp run_tests.rs /path/to/project/tests/
//!
//! Run from project root:
//!     rust-script tests/run_tests.rs
//!
//! Or compile and run:
//!     rustc tests/run_tests.rs -o tests/run_tests && ./tests/run_tests
//!
//! ```cargo
//! [dependencies]
//! regex = "1"
//! ```

use regex::Regex;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

struct TestCase {
    name: String,
    section: String,
    code: String,
    assertions: Vec<Assertion>,
}

#[derive(Debug)]
enum Assertion {
    Expect { expression: String, expected: String },
    Error { expression: String, error_code: String },
    Compiles,
    CompileFails { error_code: String },
}

struct TestResult {
    passed: bool,
    message: String,
}

static mut TOTAL_PASSED: usize = 0;
static mut TOTAL_FAILED: usize = 0;

fn parse_frontmatter(content: &str) -> std::collections::HashMap<String, String> {
    let mut config = std::collections::HashMap::new();
    let re = Regex::new(r"(?ms)^```toml\n(.*?)^```").unwrap();

    if let Some(cap) = re.captures(content) {
        for line in cap[1].lines() {
            let line = line.trim();
            if line.starts_with('#') || line.is_empty() {
                continue;
            }
            if let Some((key, value)) = line.split_once('=') {
                let key = key.trim().to_string();
                let value = value.trim().trim_matches('"').trim_matches('\'').to_string();
                config.insert(key, value);
            }
        }
    }
    config
}

fn extract_tests(content: &str) -> Vec<TestCase> {
    let mut tests = Vec::new();
    let mut current_section = String::new();
    let mut current_test = String::new();
    let mut in_code_block = false;
    let mut code_lines = Vec::new();
    let mut assertions = Vec::new();
    let mut line_number = 0;
    let mut block_start_line = 0;

    let section_re = Regex::new(r"^## (.+)$").unwrap();
    let test_re = Regex::new(r"^### (.+)$").unwrap();
    let code_start_re = Regex::new(r"^```(rs|rust)$").unwrap();
    let expect_re = Regex::new(r"//\s*expect:\s*(.+)$").unwrap();
    let error_re = Regex::new(r"//\s*error:\s*(.+)$").unwrap();
    let compiles_re = Regex::new(r"//\s*compiles$").unwrap();
    let compile_fails_re = Regex::new(r"//\s*compile_fails:\s*(.+)$").unwrap();

    for line in content.lines() {
        line_number += 1;

        if let Some(cap) = section_re.captures(line) {
            current_section = cap[1].to_string();
        } else if let Some(cap) = test_re.captures(line) {
            current_test = cap[1].to_string();
        } else if code_start_re.is_match(line) && !in_code_block {
            in_code_block = true;
            block_start_line = line_number;
            code_lines.clear();
            assertions.clear();
        } else if line == "```" && in_code_block {
            in_code_block = false;
            if !assertions.is_empty() {
                tests.push(TestCase {
                    name: if current_test.is_empty() {
                        format!("Test at line {}", block_start_line)
                    } else {
                        current_test.clone()
                    },
                    section: current_section.clone(),
                    code: code_lines.join("\n"),
                    assertions: assertions.clone(),
                });
            }
        } else if in_code_block {
            if let Some(cap) = expect_re.captures(line) {
                let expr = line.split("//").next().unwrap_or("").trim().to_string();
                assertions.push(Assertion::Expect {
                    expression: expr,
                    expected: cap[1].trim().to_string(),
                });
            } else if let Some(cap) = error_re.captures(line) {
                let expr = line.split("//").next().unwrap_or("").trim().to_string();
                let error_code = cap[1].trim().to_string();
                let code = if error_code.starts_with('[') && error_code.ends_with(']') {
                    error_code[1..error_code.len() - 1].to_string()
                } else {
                    error_code
                };
                assertions.push(Assertion::Error {
                    expression: expr,
                    error_code: code,
                });
            } else if compiles_re.is_match(line) {
                assertions.push(Assertion::Compiles);
            } else if let Some(cap) = compile_fails_re.captures(line) {
                assertions.push(Assertion::CompileFails {
                    error_code: cap[1].trim().to_string(),
                });
            } else {
                code_lines.push(line.to_string());
            }
        }
    }

    tests
}

fn run_test(test: &TestCase, crate_name: &str) -> TestResult {
    // Build a complete Rust program
    let mut full_code = String::new();

    // Add crate import if specified
    if !crate_name.is_empty() {
        full_code.push_str(&format!("use {}::*;\n", crate_name));
    }

    full_code.push_str(&test.code);
    full_code.push_str("\n\nfn main() {\n");

    // Add assertion checks
    for assertion in &test.assertions {
        match assertion {
            Assertion::Expect { expression, expected } => {
                // Generate assertion code
                if expected.starts_with("approx(") {
                    // Handle approx matcher
                    let re = Regex::new(r"approx\(([^,]+),\s*tol=([^)]+)\)").unwrap();
                    if let Some(cap) = re.captures(expected) {
                        let target: f64 = cap[1].parse().unwrap_or(0.0);
                        let tol: f64 = cap[2].parse().unwrap_or(0.001);
                        full_code.push_str(&format!(
                            "    assert!(({} - {:.10}).abs() <= {:.10}, \"Expected approx {}, got {{}}\", {});\n",
                            expression, target, tol, expected, expression
                        ));
                    }
                } else if expected.starts_with("contains(") {
                    let re = Regex::new(r#"contains\("([^"]+)"\)"#).unwrap();
                    if let Some(cap) = re.captures(expected) {
                        full_code.push_str(&format!(
                            "    assert!({}.contains(\"{}\"), \"Expected to contain '{}'\");\n",
                            expression, &cap[1], &cap[1]
                        ));
                    }
                } else {
                    full_code.push_str(&format!(
                        "    assert_eq!({}, {}, \"Expected {}, got {{}}\", {});\n",
                        expression, expected, expected, expression
                    ));
                }
            }
            Assertion::Error { expression, error_code } => {
                full_code.push_str(&format!(
                    "    match std::panic::catch_unwind(|| {{ {} }}) {{\n",
                    expression
                ));
                full_code.push_str(&format!(
                    "        Ok(_) => panic!(\"Expected error [{}] but none occurred\"),\n",
                    error_code
                ));
                full_code.push_str("        Err(_) => {}\n");
                full_code.push_str("    }\n");
            }
            Assertion::Compiles | Assertion::CompileFails { .. } => {
                // These are checked at compile time
            }
        }
    }

    full_code.push_str("}\n");

    // Write to temp file
    let temp_dir = env::temp_dir();
    let temp_file = temp_dir.join("literate_test.rs");
    let temp_bin = temp_dir.join("literate_test");

    if let Err(e) = fs::write(&temp_file, &full_code) {
        return TestResult {
            passed: false,
            message: format!("Failed to write temp file: {}", e),
        };
    }

    // Check for compile_fails assertion
    let should_fail = test.assertions.iter().any(|a| matches!(a, Assertion::CompileFails { .. }));

    // Compile
    let compile_result = Command::new("rustc")
        .args(["--edition", "2021", "-o"])
        .arg(&temp_bin)
        .arg(&temp_file)
        .stderr(Stdio::piped())
        .output();

    match compile_result {
        Ok(output) => {
            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                if should_fail {
                    // Check if the expected error is in the output
                    if let Some(Assertion::CompileFails { error_code }) =
                        test.assertions.iter().find(|a| matches!(a, Assertion::CompileFails { .. }))
                    {
                        if stderr.contains(error_code) {
                            return TestResult {
                                passed: true,
                                message: "OK (compile failed as expected)".to_string(),
                            };
                        } else {
                            return TestResult {
                                passed: false,
                                message: format!("Expected compile error '{}', got: {}", error_code, stderr),
                            };
                        }
                    }
                }
                return TestResult {
                    passed: false,
                    message: format!("Compilation failed: {}", stderr),
                };
            } else if should_fail {
                return TestResult {
                    passed: false,
                    message: "Expected compilation to fail but it succeeded".to_string(),
                };
            }
        }
        Err(e) => {
            return TestResult {
                passed: false,
                message: format!("Failed to run rustc: {}", e),
            };
        }
    }

    // Run the compiled binary
    let run_result = Command::new(&temp_bin)
        .stderr(Stdio::piped())
        .stdout(Stdio::piped())
        .output();

    // Cleanup
    let _ = fs::remove_file(&temp_file);
    let _ = fs::remove_file(&temp_bin);

    match run_result {
        Ok(output) => {
            if output.status.success() {
                TestResult {
                    passed: true,
                    message: "OK".to_string(),
                }
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                TestResult {
                    passed: false,
                    message: format!("Test failed: {}", stderr),
                }
            }
        }
        Err(e) => TestResult {
            passed: false,
            message: format!("Failed to run test: {}", e),
        },
    }
}

fn process_file(path: &Path) {
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Failed to read {}: {}", path.display(), e);
            return;
        }
    };

    let config = parse_frontmatter(&content);
    let tests = extract_tests(&content);

    println!();
    println!("{}", "=".repeat(60));
    println!("  {}", path.file_name().unwrap().to_string_lossy());
    println!("{}", "=".repeat(60));

    if tests.is_empty() {
        println!("  No tests found");
        return;
    }

    let crate_name = config.get("crate").cloned().unwrap_or_default();
    let mut current_section = String::new();

    for test in &tests {
        if test.section != current_section {
            current_section = test.section.clone();
            println!();
            println!("  {}", current_section);
            println!("  {}", "-".repeat(current_section.len()));
        }

        let result = run_test(test, &crate_name);

        if result.passed {
            println!("  \x1b[32m✓\x1b[0m {}", test.name);
            unsafe { TOTAL_PASSED += 1; }
        } else {
            println!("  \x1b[31m✗\x1b[0m {}", test.name);
            println!("      {}", result.message);
            unsafe { TOTAL_FAILED += 1; }
        }
    }
}

fn main() {
    let exe_path = env::current_exe().unwrap_or_else(|_| PathBuf::from("."));
    let script_dir = exe_path.parent().unwrap_or(Path::new("."));

    let tests_dir = if script_dir.file_name().map(|n| n == "tests").unwrap_or(false) {
        script_dir.to_path_buf()
    } else {
        script_dir.join("tests")
    };

    if !tests_dir.exists() {
        eprintln!("No tests/ directory found");
        std::process::exit(1);
    }

    let test_files: Vec<_> = fs::read_dir(&tests_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().map(|e| e == "md").unwrap_or(false))
        .collect();

    if test_files.is_empty() {
        eprintln!("No .md test files found in tests/");
        std::process::exit(1);
    }

    for path in test_files {
        process_file(&path);
    }

    println!();
    println!("{}", "=".repeat(60));
    unsafe {
        println!("  Summary: {} passed, {} failed", TOTAL_PASSED, TOTAL_FAILED);
    }
    println!("{}", "=".repeat(60));
    println!();

    unsafe {
        if TOTAL_FAILED > 0 {
            std::process::exit(1);
        }
    }
}
