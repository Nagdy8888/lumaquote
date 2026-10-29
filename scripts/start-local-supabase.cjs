// Keep this project's development services on loopback, including on Windows.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const { execFileSync, spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const project = "quotation-local-dev";
const names = ["db", "kong", "studio", "inbucket"].map(
  (service) => `supabase_${service}_${project}`,
);
const databaseClients = ["auth", "rest", "storage", "pg_meta"].map(
  (service) => `supabase_${service}_${project}`,
);
const privateDir = path.join(root, "supabase", ".temp");
fs.mkdirSync(privateDir, { recursive: true });

const context = JSON.parse(
  execFileSync("docker", ["context", "inspect"], { encoding: "utf8" }),
)[0];
const host = process.env.DOCKER_HOST || context.Endpoints.docker.Host;
const socketPath = host.startsWith("npipe://")
  ? host.slice("npipe://".length)
  : host.startsWith("unix://")
    ? host.slice("unix://".length)
    : null;
if (!socketPath) throw new Error("Expected a local Docker socket.");

/** Call the local Docker socket with a bounded deadline; return parsed metadata without exposing private container configuration. */
function api(method, route, body) {
  return new Promise((resolve, reject) => {
    const encoded = body === undefined ? null : JSON.stringify(body);
    const req = http.request(
      {
        socketPath,
        path: route,
        method,
        headers: encoded
          ? { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(encoded) }
          : {},
      },
      (res) => {
        let text = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => (text += chunk));
        res.on("end", () => {
          if (res.statusCode >= 400) return reject(new Error(`Docker ${method} ${route}: HTTP ${res.statusCode}`));
          resolve(text ? JSON.parse(text) : null);
        });
      },
    );
    req.on("error", reject);
    req.setTimeout(60000, () => req.destroy(new Error("Docker request timed out")));
    req.end(encoded);
  });
}

/** Restrict only this project's published services to loopback, preserving named volumes and Kong's required runtime files. */
async function restrictPorts() {
  let databaseRecreated = false;
  for (const name of names) {
    const container = await api("GET", `/containers/${name}/json`);
    if (container.Name !== `/${name}`) throw new Error("Unexpected container identity");
    const bindings = container.HostConfig.PortBindings || {};
    const needsChange = Object.values(bindings).some((items) =>
      items.some((item) => item.HostIp !== "127.0.0.1"),
    );
    if (!needsChange) continue;
    if (container.Mounts.some((mount) => mount.Type !== "volume" && mount.Type !== "bind")) {
      throw new Error("Unexpected mount; refusing to recreate container.");
    }
    // Preserve config and named/bind volumes. Never pass v=true or delete volumes.
    const payload = {
      ...container.Config,
      HostConfig: structuredClone(container.HostConfig),
      NetworkingConfig: {
        EndpointsConfig: Object.fromEntries(
          Object.entries(container.NetworkSettings.Networks).map(([network, endpoint]) => [
            network, { Aliases: endpoint.Aliases || [] },
          ]),
        ),
      },
    };
    fs.writeFileSync(path.join(privateDir, `${name}.restore.json`), JSON.stringify(payload), { mode: 0o600 });
    // The CLI injects TLS/config files into Kong's writable layer at startup.
    // Preserve those files as well as mounts when recreating the gateway.
    const gatewayArchive = path.join(privateDir, "gateway-runtime.tar");
    if (name === `supabase_kong_${project}`) {
      const archive = execFileSync("docker", ["cp", `${name}:/home/kong/.`, "-"], { maxBuffer: 10 * 1024 * 1024 });
      fs.writeFileSync(gatewayArchive, archive, { mode: 0o600 });
    }
    await api("POST", `/containers/${name}/stop?t=30`);
    await api("DELETE", `/containers/${name}?v=false`);
    for (const items of Object.values(payload.HostConfig.PortBindings)) {
      for (const item of items) item.HostIp = "127.0.0.1";
    }
    try {
      await api("POST", `/containers/create?name=${name}`, payload);
      if (name === `supabase_kong_${project}`) {
        execFileSync("docker", ["cp", "--archive", "-", `${name}:/home/kong/`],
          { input: fs.readFileSync(gatewayArchive), stdio: ["pipe", "pipe", "pipe"] });
      }
      await api("POST", `/containers/${name}/start`);
      if (name === `supabase_db_${project}`) databaseRecreated = true;
    } catch {
      throw new Error(`Could not recreate ${name}; volumes preserved and private restore config saved.`);
    }
    console.log(`${name}: restricted published ports to 127.0.0.1`);
  }
  if (databaseRecreated) {
    // These processes may retain sockets to the old database container even
    // while their liveness probes remain green. Reconnect only this project's
    // database clients before reporting the restarted stack ready.
    for (const name of databaseClients) {
      await api("POST", `/containers/${name}/restart?t=10`);
    }
    console.log("This project's database clients restarted after loopback port rebinding.");
  }
}

(async () => {
  if (!process.argv.includes("--restrict-only")) {
    // The network option is insufficient on some Docker Desktop versions.
    const network = spawnSync("docker", ["network", "inspect", project], { encoding: "utf8" });
    if (network.status !== 0) {
      execFileSync("docker", ["network", "create", "--driver", "bridge", "--opt",
        "com.docker.network.bridge.host_binding_ipv4=127.0.0.1", project]);
    }
    const entrypoint = path.join(root, "node_modules", "supabase", "dist", "supabase.js");
    const result = spawnSync(process.execPath, [entrypoint, "start", "--network-id", project, "--exclude",
      "realtime,logflare,vector,supavisor,edge-runtime"], { cwd: root, encoding: "utf8", maxBuffer: 20 * 1024 * 1024 });
    // CLI summaries contain keys; keep the output in ignored local storage.
    fs.writeFileSync(path.join(privateDir, "start.log"), (result.stdout || "") + (result.stderr || ""), { mode: 0o600 });
    if (result.status !== 0) throw new Error("Supabase startup failed; inspect ignored supabase/.temp/start.log locally.");
  }
  await restrictPorts();
  const deadline = Date.now() + 90000;
  for (;;) {
    const states = await Promise.all([...names,...databaseClients].map((name) => api("GET", `/containers/${name}/json`)));
    if (states.every((item) => item.State.Running && (!item.State.Health || item.State.Health.Status === "healthy"))) break;
    if (Date.now() > deadline) throw new Error("Local Supabase did not become healthy after port restriction.");
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  console.log("Local Supabase is started; run db:status locally for connection details.");
})().catch((error) => { console.error(error.message); process.exitCode = 1; });
