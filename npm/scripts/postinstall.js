"use strict";

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

const pkg = require("../package.json");
const VERSION = pkg.version;

const REPO = pkg.repository.url
  .replace("git+https://github.com/", "")
  .replace(".git", "");

const PLATFORM_MAP = {
  "darwin-arm64": "olostep-darwin-arm64",
  "darwin-x64": "olostep-darwin-x64",
  "linux-x64": "olostep-linux-x64",
  "win32-x64": "olostep-win32-x64.exe",
};

const key = `${process.platform}-${process.arch}`;
const binaryName = PLATFORM_MAP[key];

if (!binaryName) {
  console.error(
    `Unsupported platform: ${process.platform}-${process.arch}\n` +
      `Supported: ${Object.keys(PLATFORM_MAP).join(", ")}`
  );
  process.exit(1);
}

const url = `https://github.com/${REPO}/releases/download/v${VERSION}/${binaryName}`;
const binDir = path.join(__dirname, "..", "bin");
const destName = process.platform === "win32" ? "olostep.exe" : "olostep";
const dest = path.join(binDir, destName);

function fetch(url) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith("https") ? https : http;
    proto
      .get(url, { headers: { "User-Agent": "olostep-cli" } }, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          fetch(res.headers.location).then(resolve).catch(reject);
          return;
        }
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode} from ${url}`));
          return;
        }
        resolve(res);
      })
      .on("error", reject);
  });
}

async function main() {
  if (!fs.existsSync(binDir)) {
    fs.mkdirSync(binDir, { recursive: true });
  }

  console.log(`Downloading olostep ${VERSION} for ${key}...`);

  const res = await fetch(url);
  const file = fs.createWriteStream(dest);
  await new Promise((resolve, reject) => {
    res.pipe(file);
    file.on("finish", () => file.close(resolve));
    file.on("error", reject);
  });

  if (process.platform !== "win32") {
    fs.chmodSync(dest, 0o755);
  }

  console.log("olostep binary installed successfully.");
}

main().catch((err) => {
  console.error(`Failed to install olostep binary: ${err.message}`);
  console.error(`Download URL: ${url}`);
  process.exit(1);
});
