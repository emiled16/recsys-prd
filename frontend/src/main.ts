import "./style.css";

import type { RecommendationResponse } from "./contracts";
import { createApiClient } from "./api/client";

const client = createApiClient();

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

app.innerHTML = `
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Local Vite Workflow</p>
      <h1>Fashion recommendations through the public API surface.</h1>
      <p class="lede">
        This workspace runs outside Docker Compose and talks to the backend over HTTP using a thin
        fetch client. Shared services still start from infra-owned runtime assets.
      </p>
    </section>
    <section class="panel">
      <form id="recommendation-form" class="query-form">
        <label>
          Customer ID
          <input id="customer-id" name="customer_id" value="0001" />
        </label>
        <label>
          Session ID
          <input id="session-id" name="session_id" value="session-local-001" />
        </label>
        <label>
          Query text
          <input id="query-text" name="query_text" value="summer dress" />
        </label>
        <button type="submit">Fetch recommendations</button>
      </form>
      <div class="status-grid">
        <article>
          <h2>Readiness</h2>
          <pre id="readyz-output">Loading...</pre>
        </article>
        <article>
          <h2>Diagnostics</h2>
          <pre id="diagnostics-output">Loading...</pre>
        </article>
      </div>
      <article>
        <h2>Recommendations</h2>
        <pre id="recommendations-output">Submit the form to call /recommendations.</pre>
      </article>
    </section>
  </main>
`;

const form = document.querySelector<HTMLFormElement>("#recommendation-form");
const readinessOutput = document.querySelector<HTMLPreElement>("#readyz-output");
const diagnosticsOutput = document.querySelector<HTMLPreElement>("#diagnostics-output");
const recommendationsOutput = document.querySelector<HTMLPreElement>("#recommendations-output");

if (!form || !readinessOutput || !diagnosticsOutput || !recommendationsOutput) {
  throw new Error("The frontend view failed to initialize.");
}

void Promise.all([client.readiness(), client.diagnostics()])
  .then(([readiness, diagnostics]) => {
    readinessOutput.textContent = JSON.stringify(readiness, null, 2);
    diagnosticsOutput.textContent = JSON.stringify(diagnostics, null, 2);
  })
  .catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    readinessOutput.textContent = message;
    diagnosticsOutput.textContent = message;
  });

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const customerId = String(formData.get("customer_id") ?? "").trim();
  const sessionId = String(formData.get("session_id") ?? "").trim();
  const queryText = String(formData.get("query_text") ?? "").trim();
  recommendationsOutput.textContent = "Loading...";
  void client
    .recommend({
      customer_id: customerId,
      session_id: sessionId,
      query_text: queryText,
      limit: 6,
      timeout_ms: 300,
    })
    .then(async (response: RecommendationResponse) => {
      recommendationsOutput.textContent = JSON.stringify(response, null, 2);
      if (response.recommendations.length > 0) {
        await client.emitEvent({
          event_type: "product_view",
          customer_id: customerId,
          session_id: sessionId,
          article_id: response.recommendations[0].article_id,
          source: "frontend_demo",
        });
      }
    })
    .catch((error: unknown) => {
      recommendationsOutput.textContent =
        error instanceof Error ? error.message : String(error);
    });
});
