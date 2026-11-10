const { spawn, execSync } = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";

// Apply pending migrations before starting the backend, so a fresh pull or a
// new schema change never breaks the dev server with "no such column".
const migrateCmd = isWin
  ? `".venv\\Scripts\\python.exe" backend/manage.py migrate --noinput`
  : `.venv/bin/python backend/manage.py migrate --noinput`;

try {
  execSync(migrateCmd, { cwd: root, stdio: "inherit", env: process.env });
} catch (e) {
  console.error("[dev] migrate falló — revisá la salida de arriba");
}

const backendPython = isWin
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

const backendCmd = isWin
  ? `".venv\\Scripts\\python.exe" backend/manage.py runserver 8000`
  : `.venv/bin/python backend/manage.py runserver 8000`;

const backend = spawn(backendCmd, {
  cwd: root,
  stdio: "inherit",
  shell: true,
  env: process.env,
});

const npmCmd = isWin ? "npm.cmd" : "npm";
const frontend = spawn(`${npmCmd} run dev`, {
  cwd: path.join(root, "frontend"),
  stdio: "inherit",
  shell: true,
  env: process.env,
});

function shutdown(signal) {
  console.log(`\n[dev] ${signal} — apagando backend + frontend...`);
  try {
    backend.kill(signal);
  } catch {}
  try {
    frontend.kill(signal);
  } catch {}
}

for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => shutdown(sig));

let exited = 0;
function onExit(name, code) {
  console.log(`[dev] ${name} terminó con código ${code}`);
  exited += 1;
  if (exited >= 1) {
    try {
      backend.kill("SIGTERM");
    } catch {}
    try {
      frontend.kill("SIGTERM");
    } catch {}
    process.exit(code ?? 0);
  }
}

backend.on("exit", (code) => onExit("backend :8000", code));
frontend.on("exit", (code) => onExit("frontend", code));

console.log(
  "[dev] backend :8000 + frontend corriendo. Ctrl+C para cortar.",
);
