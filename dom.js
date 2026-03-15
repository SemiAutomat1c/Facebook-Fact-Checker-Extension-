const OVERLAY_ID = "verifiai-modal-overlay";
const CONTENT_CLASS = "verifiai-modal-content";

function createModal() {
  if (document.getElementById(OVERLAY_ID)) return;

  const overlay = document.createElement("div");
  overlay.id = OVERLAY_ID;
  overlay.style.cssText = `
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.55);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 999999;
    padding: 20px;
    box-sizing: border-box;
  `;

  const modal = document.createElement("div");
  modal.style.cssText = `
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.25);
    max-width: 720px;
    width: 100%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-family: Arial, sans-serif;
  `;

  const header = document.createElement("div");
  header.style.cssText = `
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding: 14px 16px;
    border-bottom: 1px solid #e5e7eb;
    background: #f8fafc;
    font-weight: 700;
    font-size: 14px;
  `;
  header.textContent = "Fact Check Text";

  const close = document.createElement("button");
  close.textContent = "×";
  close.setAttribute("aria-label", "Close");
  close.style.cssText = `background:none;border:none;font-size:20px;cursor:pointer;color:#666;`;

  const body = document.createElement("div");
  body.style.cssText = `padding:16px;overflow:auto;flex:1;background:#fff;`;

  const pre = document.createElement("pre");
  pre.className = CONTENT_CLASS;
  pre.style.cssText = `margin:0;white-space: pre-wrap;word-break: break-word;font-size: 14px;line-height: 1.5;`;

  body.appendChild(pre);
  header.appendChild(close);
  modal.appendChild(header);
  modal.appendChild(body);
  overlay.appendChild(modal);

  close.addEventListener("click", (e) => {
    e.stopPropagation();
    overlay.style.display = "none";
  });

  overlay.addEventListener("click", () => (overlay.style.display = "none"));
  modal.addEventListener("click", (e) => e.stopPropagation());

  document.body.appendChild(overlay);
}

function showModal(text) {
  const overlay = document.getElementById(OVERLAY_ID);
  if (!overlay) return;
  const content = overlay.querySelector(`.${CONTENT_CLASS}`);
  if (content) content.textContent = text || "NO POST FOUND";
  overlay.style.display = "flex";
}

window.createModal = createModal;
window.showModal = showModal;