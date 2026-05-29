#!/usr/bin/env node
const { spawnSync } = require("node:child_process");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");

function printHelp() {
  process.stdout.write(`Usage: my-ai-skills <command> [options]

Commands:
  install      Install or prepare skills for an AI coding tool.
  convert      Convert skills into tool-specific instruction packages.
  list-tools   Print supported tool names.
  help         Show this help.

Examples:
  my-ai-skills install
  my-ai-skills install --tool codex
  my-ai-skills install --tool copilot --install-dir /path/to/project
  my-ai-skills convert --tool cursor
  my-ai-skills list-tools

If the first argument is an option, it is treated as:
  my-ai-skills install <options>
`);
}

function runScript(scriptName, args) {
  const scriptPath = path.join(repoRoot, "scripts", scriptName);
  const result = spawnSync(scriptPath, args, {
    cwd: process.cwd(),
    stdio: "inherit",
    env: process.env,
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  process.exit(result.status == null ? 1 : result.status);
}

const args = process.argv.slice(2);
const command = args[0];

if (!command || command === "help" || command === "-h" || command === "--help") {
  printHelp();
  process.exit(0);
}

if (command.startsWith("-")) {
  runScript("install.sh", args);
}

switch (command) {
  case "install":
    runScript("install.sh", args.slice(1));
    break;
  case "convert":
    runScript("convert.sh", args.slice(1));
    break;
  case "list-tools":
    runScript("install.sh", ["--list-tools"]);
    break;
  default:
    console.error(`Unknown command: ${command}`);
    printHelp();
    process.exit(2);
}
