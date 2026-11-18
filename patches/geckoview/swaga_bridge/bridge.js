/* Session-scoped JavaScript bridge for GeckoView. Runs in an isolated content script. */
(() => {
  let port;

  try {
    port = browser.runtime.connectNative("swaga_browser");
  } catch (_) {
    return;
  }

  port.onMessage.addListener(async (message) => {
    if (!message || message.type !== "evaluate" ||
        typeof message.id !== "string" || typeof message.script !== "string") {
      return;
    }

    try {
      const value = await Promise.resolve((0, eval)(message.script));
      let result = JSON.stringify(value);
      if (result === undefined) result = "null";
      port.postMessage({ id: message.id, result });
    } catch (error) {
      port.postMessage({
        id: message.id,
        error: String(error && error.message ? error.message : error)
      });
    }
  });
})();
