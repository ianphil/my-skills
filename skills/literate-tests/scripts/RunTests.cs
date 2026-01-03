#!/usr/bin/env dotnet-script
/*
 * Literate Test Runner for C#
 * Parses markdown test files and validates assertions.
 *
 * Requirements: dotnet-script (`dotnet tool install -g dotnet-script`)
 *
 * Copy this file to your project's tests/ directory:
 *     cp RunTests.cs /path/to/project/tests/
 *
 * Run from project root:
 *     dotnet script tests/RunTests.cs
 *
 * Or with standard dotnet:
 *     dotnet run --project tests/RunTests.csproj
 */

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

class TestCase
{
    public string Name { get; set; } = "";
    public string Section { get; set; } = "";
    public string Code { get; set; } = "";
    public List<Assertion> Assertions { get; set; } = new();
}

abstract class Assertion { }

class ExpectAssertion : Assertion
{
    public string Expression { get; set; } = "";
    public string Expected { get; set; } = "";
}

class ErrorAssertion : Assertion
{
    public string Expression { get; set; } = "";
    public string ErrorCode { get; set; } = "";
}

class TestResult
{
    public bool Passed { get; set; }
    public string Message { get; set; } = "";
}

class LiterateTestRunner
{
    private int _totalPassed = 0;
    private int _totalFailed = 0;

    static int Main(string[] args)
    {
        var runner = new LiterateTestRunner();
        return runner.Run();
    }

    int Run()
    {
        // Determine tests directory
        var scriptDir = AppContext.BaseDirectory;
        string testsDir;

        if (Path.GetFileName(scriptDir.TrimEnd(Path.DirectorySeparatorChar)) == "tests")
        {
            testsDir = scriptDir;
        }
        else
        {
            testsDir = Path.Combine(scriptDir, "tests");
        }

        // Also check current directory
        if (!Directory.Exists(testsDir))
        {
            testsDir = Path.Combine(Directory.GetCurrentDirectory(), "tests");
        }

        if (!Directory.Exists(testsDir))
        {
            Console.WriteLine("No tests/ directory found");
            return 1;
        }

        var testFiles = Directory.GetFiles(testsDir, "*.md").OrderBy(f => f).ToList();

        if (testFiles.Count == 0)
        {
            Console.WriteLine("No .md test files found in tests/");
            return 1;
        }

        foreach (var file in testFiles)
        {
            ProcessFile(file);
        }

        Console.WriteLine();
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"  Summary: {_totalPassed} passed, {_totalFailed} failed");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine();

        return _totalFailed > 0 ? 1 : 0;
    }

    Dictionary<string, string> ParseFrontmatter(string content)
    {
        var config = new Dictionary<string, string>();
        var match = Regex.Match(content, @"^```toml\s*\n(.*?)^```", RegexOptions.Multiline | RegexOptions.Singleline);

        if (match.Success)
        {
            foreach (var line in match.Groups[1].Value.Split('\n'))
            {
                var trimmed = line.Trim();
                if (trimmed.StartsWith("#") || string.IsNullOrEmpty(trimmed)) continue;

                var eqIndex = trimmed.IndexOf('=');
                if (eqIndex > 0)
                {
                    var key = trimmed.Substring(0, eqIndex).Trim();
                    var value = trimmed.Substring(eqIndex + 1).Trim().Trim('"', '\'');
                    config[key] = value;
                }
            }
        }

        return config;
    }

    List<TestCase> ExtractTests(string content)
    {
        var tests = new List<TestCase>();
        var currentSection = "";
        var currentTest = "";
        var inCodeBlock = false;
        var codeLines = new List<string>();
        var assertions = new List<Assertion>();
        var lineNumber = 0;
        var blockStartLine = 0;

        var sectionRe = new Regex(@"^## (.+)$");
        var testRe = new Regex(@"^### (.+)$");
        var codeStartRe = new Regex(@"^```(cs|csharp)$");
        var expectRe = new Regex(@"//\s*expect:\s*(.+)$");
        var errorRe = new Regex(@"//\s*error:\s*(.+)$");

        foreach (var line in content.Split('\n'))
        {
            lineNumber++;

            var sectionMatch = sectionRe.Match(line);
            if (sectionMatch.Success)
            {
                currentSection = sectionMatch.Groups[1].Value;
                continue;
            }

            var testMatch = testRe.Match(line);
            if (testMatch.Success)
            {
                currentTest = testMatch.Groups[1].Value;
                continue;
            }

            if (codeStartRe.IsMatch(line) && !inCodeBlock)
            {
                inCodeBlock = true;
                blockStartLine = lineNumber;
                codeLines.Clear();
                assertions.Clear();
                continue;
            }

            if (line.Trim() == "```" && inCodeBlock)
            {
                inCodeBlock = false;
                if (assertions.Count > 0)
                {
                    tests.Add(new TestCase
                    {
                        Name = string.IsNullOrEmpty(currentTest) ? $"Test at line {blockStartLine}" : currentTest,
                        Section = currentSection,
                        Code = string.Join("\n", codeLines),
                        Assertions = new List<Assertion>(assertions)
                    });
                }
                continue;
            }

            if (inCodeBlock)
            {
                var expectMatch = expectRe.Match(line);
                if (expectMatch.Success)
                {
                    var expr = line.Split("//")[0].Trim();
                    assertions.Add(new ExpectAssertion
                    {
                        Expression = expr,
                        Expected = expectMatch.Groups[1].Value.Trim()
                    });
                    continue;
                }

                var errorMatch = errorRe.Match(line);
                if (errorMatch.Success)
                {
                    var expr = line.Split("//")[0].Trim();
                    var errorCode = errorMatch.Groups[1].Value.Trim();
                    if (errorCode.StartsWith("[") && errorCode.EndsWith("]"))
                    {
                        errorCode = errorCode.Substring(1, errorCode.Length - 2);
                    }
                    assertions.Add(new ErrorAssertion
                    {
                        Expression = expr,
                        ErrorCode = errorCode
                    });
                    continue;
                }

                codeLines.Add(line);
            }
        }

        return tests;
    }

    TestResult RunTest(TestCase test, string namespaceName, string[] usings)
    {
        // Build complete C# program
        var sb = new StringBuilder();

        // Add usings
        sb.AppendLine("using System;");
        foreach (var u in usings)
        {
            sb.AppendLine($"using {u};");
        }

        sb.AppendLine();
        sb.AppendLine("class LiterateTest {");
        sb.AppendLine("    static int Main() {");
        sb.AppendLine("        try {");

        // Add test code
        foreach (var line in test.Code.Split('\n'))
        {
            sb.AppendLine($"            {line}");
        }

        // Add assertion checks
        foreach (var assertion in test.Assertions)
        {
            if (assertion is ExpectAssertion expect)
            {
                if (expect.Expected.StartsWith("approx("))
                {
                    var match = Regex.Match(expect.Expected, @"approx\(([^,]+),\s*tol=([^)]+)\)");
                    if (match.Success)
                    {
                        var target = match.Groups[1].Value;
                        var tol = match.Groups[2].Value;
                        sb.AppendLine($"            if (Math.Abs({expect.Expression} - {target}) > {tol}) {{");
                        sb.AppendLine($"                Console.Error.WriteLine(\"Expected approx {expect.Expected}, got \" + {expect.Expression});");
                        sb.AppendLine("                return 1;");
                        sb.AppendLine("            }");
                    }
                }
                else if (expect.Expected.StartsWith("contains("))
                {
                    var match = Regex.Match(expect.Expected, @"contains\(""([^""]+)""\)");
                    if (match.Success)
                    {
                        var substring = match.Groups[1].Value;
                        sb.AppendLine($"            if (!{expect.Expression}.Contains(\"{substring}\")) {{");
                        sb.AppendLine($"                Console.Error.WriteLine(\"Expected to contain '{substring}'\");");
                        sb.AppendLine("                return 1;");
                        sb.AppendLine("            }");
                    }
                }
                else
                {
                    sb.AppendLine($"            if (!object.Equals({expect.Expression}, {expect.Expected})) {{");
                    sb.AppendLine($"                Console.Error.WriteLine(\"Expected {expect.Expected}, got \" + {expect.Expression});");
                    sb.AppendLine("                return 1;");
                    sb.AppendLine("            }");
                }
            }
            else if (assertion is ErrorAssertion error)
            {
                // For error assertions, we need to wrap in try-catch
                sb.AppendLine("            try {");
                sb.AppendLine($"                {error.Expression};");
                sb.AppendLine($"                Console.Error.WriteLine(\"Expected error [{error.ErrorCode}] but none was thrown\");");
                sb.AppendLine("                return 1;");
                sb.AppendLine("            } catch (Exception ex) {");
                sb.AppendLine($"                var code = ex.GetType().GetProperty(\"Code\")?.GetValue(ex)?.ToString() ?? ex.GetType().Name;");
                sb.AppendLine($"                if (code != \"{error.ErrorCode}\") {{");
                sb.AppendLine($"                    Console.Error.WriteLine(\"Expected error [{error.ErrorCode}], got [\" + code + \"]\");");
                sb.AppendLine("                    return 1;");
                sb.AppendLine("                }");
                sb.AppendLine("            }");
            }
        }

        sb.AppendLine("        } catch (Exception ex) {");
        sb.AppendLine("            Console.Error.WriteLine(\"Unhandled exception: \" + ex.Message);");
        sb.AppendLine("            return 1;");
        sb.AppendLine("        }");
        sb.AppendLine("        return 0;");
        sb.AppendLine("    }");
        sb.AppendLine("}");

        var fullCode = sb.ToString();

        // Write to temp file
        var tempDir = Path.GetTempPath();
        var tempFile = Path.Combine(tempDir, "LiterateTest.cs");
        var tempBin = Path.Combine(tempDir, "LiterateTest");

        try
        {
            File.WriteAllText(tempFile, fullCode);
        }
        catch (Exception ex)
        {
            return new TestResult { Passed = false, Message = $"Failed to write temp file: {ex.Message}" };
        }

        // Compile with dotnet
        var compileProcess = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "dotnet",
                Arguments = $"build \"{tempFile}\" -o \"{tempDir}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            }
        };

        // Use csc directly for simpler compilation
        compileProcess.StartInfo.FileName = "csc";
        compileProcess.StartInfo.Arguments = $"/nologo /out:\"{tempBin}.exe\" \"{tempFile}\"";

        try
        {
            compileProcess.Start();
            var stderr = compileProcess.StandardError.ReadToEnd();
            compileProcess.WaitForExit();

            if (compileProcess.ExitCode != 0)
            {
                File.Delete(tempFile);
                return new TestResult { Passed = false, Message = $"Compilation failed: {stderr}" };
            }
        }
        catch (Exception ex)
        {
            // Try with dotnet instead
            try
            {
                var runProcess = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "dotnet",
                        Arguments = $"script \"{tempFile}\"",
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    }
                };

                runProcess.Start();
                var stdout = runProcess.StandardOutput.ReadToEnd();
                var stderr = runProcess.StandardError.ReadToEnd();
                runProcess.WaitForExit();

                File.Delete(tempFile);

                if (runProcess.ExitCode == 0)
                {
                    return new TestResult { Passed = true, Message = "OK" };
                }
                else
                {
                    return new TestResult { Passed = false, Message = $"Test failed: {stderr}" };
                }
            }
            catch
            {
                File.Delete(tempFile);
                return new TestResult { Passed = false, Message = $"Failed to compile: {ex.Message}" };
            }
        }

        // Run the compiled binary
        try
        {
            var runProcess = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = $"{tempBin}.exe",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };

            runProcess.Start();
            var stderr = runProcess.StandardError.ReadToEnd();
            runProcess.WaitForExit();

            File.Delete(tempFile);
            File.Delete($"{tempBin}.exe");

            if (runProcess.ExitCode == 0)
            {
                return new TestResult { Passed = true, Message = "OK" };
            }
            else
            {
                return new TestResult { Passed = false, Message = stderr.Trim() };
            }
        }
        catch (Exception ex)
        {
            File.Delete(tempFile);
            return new TestResult { Passed = false, Message = $"Failed to run: {ex.Message}" };
        }
    }

    void ProcessFile(string path)
    {
        var content = File.ReadAllText(path);
        var config = ParseFrontmatter(content);
        var tests = ExtractTests(content);

        Console.WriteLine();
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"  {Path.GetFileName(path)}");
        Console.WriteLine(new string('=', 60));

        if (tests.Count == 0)
        {
            Console.WriteLine("  No tests found");
            return;
        }

        var namespaceName = config.GetValueOrDefault("namespace", "");
        var usingsStr = config.GetValueOrDefault("using", "");
        var usings = string.IsNullOrEmpty(usingsStr)
            ? Array.Empty<string>()
            : usingsStr.Split(',').Select(u => u.Trim()).ToArray();

        var currentSection = "";

        foreach (var test in tests)
        {
            if (test.Section != currentSection)
            {
                currentSection = test.Section;
                Console.WriteLine();
                Console.WriteLine($"  {currentSection}");
                Console.WriteLine($"  {new string('-', currentSection.Length)}");
            }

            var result = RunTest(test, namespaceName, usings);

            if (result.Passed)
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.Write("  ✓ ");
                Console.ResetColor();
                Console.WriteLine(test.Name);
                _totalPassed++;
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.Write("  ✗ ");
                Console.ResetColor();
                Console.WriteLine(test.Name);
                Console.WriteLine($"      {result.Message}");
                _totalFailed++;
            }
        }
    }
}

// Entry point for dotnet-script
var runner = new LiterateTestRunner();
return runner.Run();
