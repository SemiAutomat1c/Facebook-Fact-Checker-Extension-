console.log("[VerifiAI] ✅ content script loaded");

const BTN_CLASS = "fb-click-me-btn";

// Expand "See More" in post
function expandSeeMore(post) {
  const textContainer =
    post.querySelector('[data-ad-rendering-role="story_message"]') ||
    post.querySelector('[data-ad-preview="message"]') ||
    post;

  const allElements = textContainer.querySelectorAll("*");
  let clicked = false;

  for (const el of allElements) {
    const text = (el.textContent || el.innerText || "").trim();
    const ariaLabel = (el.getAttribute("aria-label") || "").trim();

    const hasSeeMore =
      (text.toLowerCase().startsWith("see more") ||
        text.toLowerCase() === "see more" ||
        ariaLabel.toLowerCase().includes("see more")) &&
      text.length < 50;

    if (!hasSeeMore) continue;

    const role = el.getAttribute("role");
    const computedStyle = window.getComputedStyle(el);

    const isClickable =
      role === "button" ||
      el.tagName === "BUTTON" ||
      el.tagName === "A" ||
      (el.tagName === "DIV" && role === "button") ||
      (el.tagName === "SPAN" && el.closest('[role="button"]')) ||
      computedStyle.cursor === "pointer";

    if (!isClickable) continue;

    const visible =
      computedStyle.display !== "none" &&
      computedStyle.visibility !== "hidden" &&
      computedStyle.opacity !== "0";

    if (!visible) continue;

    try {
      const clickTarget =
        el.tagName === "SPAN" && el.closest('[role="button"]')
          ? el.closest('[role="button"]')
          : el;
      clickTarget.click();
      clicked = true;
      return new Promise((resolve) => setTimeout(resolve, 500));
    } catch (e) {
      console.log("Could not click see more:", e);
    }
  }

  return clicked ? Promise.resolve() : Promise.resolve();
}

// Extract post text
async function extractPostText(post) {
  await expandSeeMore(post);

  const textEl =
    post.querySelector('[data-ad-rendering-role="story_message"]') ||
    post.querySelector('[data-ad-preview="message"]');

  if (textEl && textEl.innerText.trim()) return textEl.innerText.trim();

  let collected = "";
  post.querySelectorAll("span").forEach((span) => {
    const t = span.innerText && span.innerText.trim();
    if (t && t.length > 20) collected += t + "\n";
  });
  if (collected.trim()) return collected.trim();

  if (post.innerText && post.innerText.trim().length > 30)
    return post.innerText.trim();

  return "NO POST FOUND";
}

// Create Fact Check button
function createFactCheckButton(postElement) {
  const wrapper = document.createElement("div");
  wrapper.style.cssText = `display: inline-flex; align-items: center; margin-left: 6px;`;

  const button = document.createElement("button");
  button.textContent = "Fact Check";
  button.className = BTN_CLASS;
  button.style.cssText = `
    padding: 6px 12px;
    background-color: #1877F2;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    line-height: 1;
  `;

  button.addEventListener("click", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const text = await extractPostText(postElement);
    console.log("📌 Extracted post text:", text);
    showModal(text);
  });

  wrapper.appendChild(button);
  return wrapper;
}

// Add buttons to posts
function addButtons() {
  let added = 0;
  const xButtons = document.querySelectorAll('[aria-label="hide post"]');

  xButtons.forEach((xButton) => {
    const container = xButton.parentElement;
    const grandparent = container?.parentElement;
    if (!container || !grandparent) return;
    if (grandparent.querySelector(`.${BTN_CLASS}`)) return;

    let postElement = grandparent;
    while (postElement && postElement !== document.body) {
      if (
        postElement.getAttribute("role") === "article" ||
        postElement.tagName === "ARTICLE" ||
        postElement.querySelector('[data-ad-rendering-role="story_message"]')
      ) break;
      postElement = postElement.parentElement;
    }
    if (!postElement) postElement = grandparent;

    const wrapper = createFactCheckButton(postElement);
    if (container.nextSibling) grandparent.insertBefore(wrapper, container.nextSibling);
    else grandparent.appendChild(wrapper);

    added++;
  });

  return added;
}

createModal();
addButtons();

let timeout = null;
const observer = new MutationObserver(() => {
  if (timeout) clearTimeout(timeout);
  timeout = setTimeout(() => {
    addButtons();
  }, 100);
});
observer.observe(document.body, { childList: true, subtree: true });

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "INJECT_NOW") {
    const n = addButtons();
    sendResponse({ message: `Re-injected (${n})` });
    return true;
  }
});