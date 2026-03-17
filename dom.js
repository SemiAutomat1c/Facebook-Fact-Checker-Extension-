console.log("[VerifiAI] ✅ content script loaded");

const BTN_CLASS = "fb-click-me-btn";


function expandSeeMore(post) {
  const textContainer =
    post.querySelector('[data-ad-rendering-role="story_message"]') ||
    post.querySelector('[data-ad-preview="message"]') ||
    post;

  const allElements = textContainer.querySelectorAll("*");

  for (const el of allElements) {
    const text = (el.textContent || "").toLowerCase().trim();
    const ariaLabel = (el.getAttribute("aria-label") || "").toLowerCase();

    const hasSeeMore =
      (text === "see more" || text.startsWith("see more") || ariaLabel.includes("see more")) &&
      text.length < 50;

    if (!hasSeeMore) continue;

    const role = el.getAttribute("role");
    const computedStyle = window.getComputedStyle(el);

    const isClickable =
      role === "button" ||
      el.tagName === "BUTTON" ||
      el.tagName === "A" ||
      computedStyle.cursor === "pointer";

    if (!isClickable) continue;

    try {
      el.click();
      return new Promise((resolve) => setTimeout(resolve, 400));
    } catch (e) {}
  }

  return Promise.resolve();
}

/* =========================
   EXTRACT POST TEXT
========================= */
async function extractPostText(post) {
  await expandSeeMore(post);

  // Primary selectors
  const textEl =
    post.querySelector('[data-ad-rendering-role="story_message"]') ||
    post.querySelector('[data-ad-preview="message"]');

  if (textEl && textEl.innerText.trim()) {
    return textEl.innerText.trim();
  }

  // Profile/Page fallback
  const altText =
    post.querySelector('[dir="auto"]') ||
    post.querySelector('div[style*="text"]');

  if (altText && altText.innerText.trim().length > 30) {
    return altText.innerText.trim();
  }

  // Generic fallback
  if (post.innerText && post.innerText.trim().length > 50) {
    return post.innerText.trim();
  }

  return "NO POST FOUND";
}

/* =========================
   CREATE BUTTON
========================= */
function createFactCheckButton(postElement) {
  const wrapper = document.createElement("div");
  wrapper.style.cssText = `
    display: inline-flex;
    align-items: center;
    margin-left: 6px;
  `;

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
    height: 32px;
  `;

  button.addEventListener("click", async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const text = await extractPostText(postElement);
    console.log("📌 Extracted post text:", text);

    showModal(text); // your existing modal
  });

  wrapper.appendChild(button);
  return wrapper;
}

/* =========================
   FIND POSTS + INJECT BUTTON
========================= */
function addButtons() {
  let added = 0;

  // 🔥 UNIVERSAL SELECTOR
  const xButtons = document.querySelectorAll(`
    [aria-label="Actions for this post"],
    [aria-label="More options"],
    [aria-label*="post"]
  `);

  xButtons.forEach((xButton) => {
    const container = xButton.parentElement;
    const grandparent = container?.parentElement;
    if (!container || !grandparent) return;

    // Prevent duplicate buttons
    if (grandparent.querySelector(`.${BTN_CLASS}`)) return;

    let postElement = grandparent;

    // 🔥 SMART POST DETECTION
    while (postElement && postElement !== document.body) {
      if (
        postElement.getAttribute("role") === "article" ||
        postElement.tagName === "ARTICLE" ||
        postElement.querySelector('[data-ad-rendering-role="story_message"]') ||
        postElement.innerText.length > 100
      ) break;

      postElement = postElement.parentElement;
    }

    if (!postElement) postElement = grandparent;

    const wrapper = createFactCheckButton(postElement);

    if (container.nextSibling) {
      grandparent.insertBefore(wrapper, container.nextSibling);
    } else {
      grandparent.appendChild(wrapper);
    }

    added++;
  });

  return added;
}

/* =========================
   i adjust rani kay nasobraan ra s  a padding
========================= */
function createModal() {
  if (document.getElementById("fact-modal")) return;

  const modal = document.createElement("div");
  modal.id = "fact-modal";

  modal.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 20px;
    z-index: 999999;
    border-radius: 10px;
    width: 400px;
    max-height: 70vh;
    overflow-y: auto;
    display: none;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3);
  `;

  modal.innerHTML = `
    <h3>🧠 Fact Check Result</h3>
    <pre id="fact-content" style="white-space: pre-wrap;"></pre>
    <button id="close-modal">Close</button>
  `;

  document.body.appendChild(modal);

  document.getElementById("close-modal").onclick = () => {
    modal.style.display = "none";
  };
}

function showModal(text) {
  const modal = document.getElementById("fact-modal");
  const content = document.getElementById("fact-content");

  content.textContent = text;
  modal.style.display = "block";
}


createModal();
addButtons();


let timeout = null;

const observer = new MutationObserver(() => {
  if (timeout) clearTimeout(timeout);

  timeout = setTimeout(() => {
    addButtons();
  }, 200);
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "INJECT_NOW") {
    const n = addButtons();
    sendResponse({ message: `Re-injected (${n})` });
    return true;
  }
});
