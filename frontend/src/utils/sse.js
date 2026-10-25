/**
 * 解析 SSE 流。因为 EventSource 只支持 GET，我们用 fetch + ReadableStream。
 */
export async function streamSSE(url, body, { onMessage, onReferences, onDone, onError }) {
  try {
    const token = localStorage.getItem("token");

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    if (response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
      return;
    }

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop();

      for (const part of parts) {
        const lines = part.split("\n");
        let event = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) event = line.slice(7).trim();
          else if (line.startsWith("data: ")) data += line.slice(6);
        }

        if (event === "done") {
          onDone && onDone();
          return;
        }

        // ← 新增
        if (event === "references") {
          try {
            const parsed = JSON.parse(data);
            onReferences && onReferences(parsed.references || []);
          } catch (e) {
            console.error("references 解析失败:", e);
          }
          continue;
        }

        if (event === "message" && data) {
          try {
            onMessage && onMessage(JSON.parse(data));
          } catch (e) {
            console.error("SSE 解析失败:", e);
          }
        }
      }
    }
    onDone && onDone();
  } catch (e) {
    onError && onError(e);
  }
}