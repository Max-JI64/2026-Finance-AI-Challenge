// Explicit user-operated capture of real deployed GPT notice analysis.
// No credentials, business inputs, local source uploads, or file writes.
const SERVICE = "https://finance-ai-challenge-232883421735.asia-northeast3.run.app";
const TARGETS = ["POL_SEMAS_STABILITY_VOUCHER_2026", "POL_SEOUL_CLOSURE_2026", "POL_SEMAS_RECHALLENGE_2026"];
async function main() {
  const args = process.argv.slice(2);
  if (!args.includes("--confirm-live")) throw new Error("Pass --confirm-live to authorize paid live notice analysis.");
  const filter = args.includes("--policy") ? args[args.indexOf("--policy") + 1] : null;
  const catalogResponse = await fetch(`${SERVICE}/api/v5/catalog/policies`, {signal: AbortSignal.timeout(45000)});
  if (!catalogResponse.ok) throw new Error(`Catalog HTTP ${catalogResponse.status}`);
  const catalog = (await catalogResponse.json()).items;
  if (filter && !TARGETS.includes(filter)) throw new Error("Only the three user-selected notices are in scope");
  const policies = catalog.filter(p => TARGETS.includes(p.policy_id) && (!filter || p.policy_id === filter));
  if (!policies.length) throw new Error("No matching policies");
  let next = 0, completed = 0, failed = 0;
  async function worker() {
    while (next < policies.length) {
      const policy = policies[next++];
      const request = Object.fromEntries(["policy_id", "policy_name", "policy_version", "official_url"].map(key => [key, policy[key]]));
      request.force_refresh = !args.includes("--use-cache");
      try {
        const response = await fetch(`${SERVICE}/api/v5/application/notice-extract`, {
          method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(request),
          signal: AbortSignal.timeout(45000),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        const successful = result.analysis_status === "completed" && result.external_ai_used === true;
        if (!successful) failed++;
        console.log("NOTICE_RESULT " + JSON.stringify({captured_at: new Date().toISOString(), service_url: SERVICE, request, response: result}));
        console.error(`${++completed}/${policies.length} ${policy.policy_id}: ${successful ? `GPT response (${result.cache_status})` : result.fallback_reason}`);
      } catch (error) {
        failed++;
        console.log("NOTICE_RESULT " + JSON.stringify({captured_at: new Date().toISOString(), service_url: SERVICE, request, error: error.message}));
        console.error(`${++completed}/${policies.length} ${policy.policy_id}: ${error.message}`);
      }
    }
  }
  await Promise.all([worker(), worker()]);
  console.error(`DONE ${completed} policies, ${failed} unsuccessful`);
  if (failed) process.exitCode = 1;
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
