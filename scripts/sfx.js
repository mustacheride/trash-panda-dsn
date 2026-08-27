const LOG_PREFIX = "[trash-panda-dsn]";
const DSN_API_PATH = "/modules/dice-so-nice/api.js";
const OVERLAY_ID = "trash-panda-dsn-sfx-overlay";
const TEXTURE_GREEN = "#3D5C4A";

const SFX = {
  clap: {
    id: "PlayTrashPandaClap",
    specialEffectName: "Trash Panda Clap",
    url: "/modules/trash-panda-dsn/assets/sfx/raccoon-clap.gif",
    caption: "Nice",
    durationMs: 3500
  },
  dumpster: {
    id: "PlayTrashPandaDumpster",
    specialEffectName: "Trash Panda Dumpster Dive",
    url: "/modules/trash-panda-dsn/assets/sfx/jump-falling.gif",
    caption: "Fail",
    durationMs: 4000
  }
};

let overlayGeneration = 0;

function warn(...args) {
  console.warn(LOG_PREFIX, ...args);
}

function hideGifOverlay() {
  document.getElementById(OVERLAY_ID)?.remove();
}

function showGifOverlay(url, caption, durationMs, onDone) {
  overlayGeneration += 1;
  const generation = overlayGeneration;
  hideGifOverlay();

  const wrap = document.createElement("div");
  wrap.id = OVERLAY_ID;
  wrap.style.cssText = [
    "position:fixed",
    "inset:0",
    "z-index:10000",
    "pointer-events:none",
    "display:flex",
    "align-items:center",
    "justify-content:center"
  ].join(";");

  const box = document.createElement("div");
  box.style.cssText = [
    `background:${TEXTURE_GREEN}`,
    "padding:40px 56px 32px",
    "border-radius:18px",
    "box-shadow:0 12px 40px rgba(0,0,0,0.6)",
    "display:flex",
    "flex-direction:column",
    "align-items:center",
    "gap:20px"
  ].join(";");

  const img = document.createElement("img");
  img.alt = caption;
  img.src = url;
  img.style.cssText = [
    "display:block",
    "max-width:min(480px,70vw)",
    "max-height:min(480px,70vh)",
    "border-radius:8px"
  ].join(";");

  const label = document.createElement("div");
  label.textContent = caption;
  label.style.cssText = [
    "color:#F5F0E6",
    "font-family:Arial,sans-serif",
    "font-size:48px",
    "font-weight:700",
    "letter-spacing:0.04em"
  ].join(";");

  box.appendChild(img);
  box.appendChild(label);
  wrap.appendChild(box);
  document.body.appendChild(wrap);

  window.setTimeout(() => {
    if (generation !== overlayGeneration) {
      return;
    }
    hideGifOverlay();
    onDone?.();
  }, durationMs);

  return generation;
}

function createGifSfxClass(DiceSFX, config) {
  return class extends DiceSFX {
    static id = config.id;
    static specialEffectName = config.specialEffectName;
    static gifUrl = config.url;
    static caption = config.caption;
    static durationMs = config.durationMs;
    static PLAY_ONLY_ONCE_PER_MESH = true;

    constructor(box, dicemesh, options) {
      super(box, dicemesh, options);
      this.enableGC = true;
      this.overlayGeneration = 0;
    }

    static async init() {
      return true;
    }

    async play() {
      this.overlayGeneration = showGifOverlay(
        this.constructor.gifUrl,
        this.constructor.caption,
        this.constructor.durationMs,
        () => {
          this.destroyed = true;
        }
      );
    }

    destroy() {
      if (this.overlayGeneration === overlayGeneration) {
        hideGifOverlay();
      }
      this.destroyed = true;
    }
  };
}

async function registerSfx(api) {
  let DiceSFX;
  try {
    ({ DiceSFX } = await import(DSN_API_PATH));
  } catch (err) {
    warn("Could not import DiceSFX; skipping GIF special effects.", err);
    return;
  }

  if (typeof DiceSFX !== "function") {
    warn("DiceSFX export is missing; skipping GIF special effects.");
    return;
  }

  api.addSFXMode(createGifSfxClass(DiceSFX, SFX.clap));
  api.addSFXMode(createGifSfxClass(DiceSFX, SFX.dumpster));
  console.log(LOG_PREFIX, `Registered SFX ${SFX.clap.id} and ${SFX.dumpster.id}`);
}

export { registerSfx, SFX };
