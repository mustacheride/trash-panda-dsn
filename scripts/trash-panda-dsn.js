import { registerSfx } from "./sfx.js";

const MODULE_ID = "trash-panda-dsn";
const DSN_MODULE_ID = "dice-so-nice";
const DSN_API_PATH = "/modules/dice-so-nice/api.js";
const LOG_PREFIX = `[${MODULE_ID}]`;

const SYSTEM = {
  id: "trash-panda",
  name: "Trash Panda Faces",
  mode: "default",
  group: "Trash Panda"
};

const ASSETS = {
  textures: {
    dumpster: {
      source: `/modules/${MODULE_ID}/assets/textures/trash-panda-dumpster.webp`,
      bump: `/modules/${MODULE_ID}/assets/textures/trash-panda-dumpster-bump.webp`
    }
  }
};

const TEXTURES = [
  {
    id: "trash-panda-dumpster",
    name: "Trash Panda Dumpster",
    composite: "source-over",
    source: ASSETS.textures.dumpster.source,
    bump: ASSETS.textures.dumpster.bump
  }
];

const COLORSETS = [
  {
    name: "trash-panda-classic",
    description: "Trash Panda Classic",
    category: "Trash Panda",
    foreground: "#F5F0E6",
    background: "#4A4A4A",
    outline: "#111111",
    edge: "#1A1A1A",
    texture: "trash-panda-dumpster",
    material: "stone",
    font: "Arial Black",
    fontScale: {
      d4: 1.15,
      d6: 1.3,
      d8: 1.1,
      d10: 1,
      d12: 1.1,
      d20: 1,
      d100: 0.75
    },
    visibility: "visible"
  },
  {
    name: "trash-panda-dumpster",
    description: "Trash Panda Dumpster",
    category: "Trash Panda",
    foreground: "#F5F0E6",
    background: "#3D5C4A",
    outline: "#111111",
    edge: "#C45C26",
    texture: "trash-panda-dumpster",
    material: "plastic",
    font: "Arial Black",
    fontScale: {
      d4: 1.15,
      d6: 1.3,
      d8: 1.1,
      d10: 1,
      d12: 1.1,
      d20: 1,
      d100: 0.75
    },
    visibility: "visible"
  }
];

function faceLabels(dieType, count) {
  return Array.from({ length: count }, (_, index) => {
    const face = String(index + 1).padStart(2, "0");
    return `/modules/${MODULE_ID}/assets/faces/${dieType}/${face}.png`;
  });
}

// Icon-only faces. Min = trash-can, max = raccoon-head.
// DSN 5.2.3 and 6.2.9 order: d10 is 1-9 then 0; d100 is 10-90 then 00.
const FACESETS = [
  { type: "d20", labels: faceLabels("d20", 20) },
  { type: "d12", labels: faceLabels("d12", 12) },
  { type: "d10", labels: faceLabels("d10", 10) },
  { type: "d100", labels: faceLabels("d100", 10) },
  { type: "d8", labels: faceLabels("d8", 8) },
  { type: "d6", labels: faceLabels("d6", 6) },
  { type: "d4", labels: faceLabels("d4", 4) }
];

function log(...args) {
  console.log(LOG_PREFIX, ...args);
}

function warn(...args) {
  console.warn(LOG_PREFIX, ...args);
}

function error(...args) {
  console.error(LOG_PREFIX, ...args);
}

function isDiceSoNiceActive() {
  return Boolean(globalThis.game?.modules?.get(DSN_MODULE_ID)?.active);
}

function getDiceSoNiceApi(dice3d) {
  const api = dice3d ?? globalThis.game?.dice3d ?? null;
  if (!api) {
    return null;
  }

  const required = ["addSystem", "addTexture", "addColorset", "addDicePreset"];
  for (const method of required) {
    if (typeof api[method] !== "function") {
      warn(`API is missing ${method}`);
      return null;
    }
  }

  return api;
}

async function createDiceSystem() {
  try {
    const { DiceSystem } = await import(DSN_API_PATH);
    return new DiceSystem(SYSTEM.id, SYSTEM.name, SYSTEM.mode, SYSTEM.group);
  } catch (err) {
    warn("Could not import DiceSystem; falling back to the legacy addSystem object.", err);
    return { id: SYSTEM.id, name: SYSTEM.name, group: SYSTEM.group };
  }
}

async function registerSystem(api) {
  const system = await createDiceSystem();
  if (system.constructor?.name === "DiceSystem") {
    api.addSystem(system);
  } else {
    api.addSystem(system, SYSTEM.mode);
  }
  log(`Registered system ${SYSTEM.id} in group ${SYSTEM.group}`);
}

async function registerTextures(api) {
  for (const texture of TEXTURES) {
    await api.addTexture(texture.id, {
      name: texture.name,
      composite: texture.composite,
      source: texture.source,
      bump: texture.bump
    });
    log(`Registered texture ${texture.id}`);
  }
}

async function registerColorsets(api) {
  for (const colorset of COLORSETS) {
    await api.addColorset(colorset, "default");
    log(`Registered colorset ${colorset.name}`);
  }
}

function registerFaces(api) {
  for (const faceset of FACESETS) {
    api.addDicePreset({
      type: faceset.type,
      labels: faceset.labels,
      system: SYSTEM.id
    });
    log(`Registered ${faceset.type} faces for ${SYSTEM.id}`);
  }
}

async function initModule() {
  log("Module script loaded");
  const dsnModule = globalThis.game?.modules?.get(DSN_MODULE_ID);
  if (dsnModule) {
    log(`Dice So Nice ${dsnModule.version ?? "unknown"} detected`);
  }

  if (!isDiceSoNiceActive()) {
    log("Dice So Nice is inactive; skipping customization registration");
    return;
  }

  Hooks.once("diceSoNiceReady", async (dice3d) => {
    const api = getDiceSoNiceApi(dice3d);
    if (!api) {
      warn("diceSoNiceReady fired but the Dice So Nice API is not usable");
      return;
    }

    try {
      await registerSystem(api);
      await registerTextures(api);
      await registerColorsets(api);
      registerFaces(api);
      try {
        if (typeof api.addSFXMode === "function") {
          await registerSfx(api);
        } else {
          warn("addSFXMode is missing; skipping GIF special effects");
        }
      } catch (err) {
        warn("SFX registration failed; dice faces are still registered.", err);
      }
      if (typeof api.preloadPresets === "function") {
        await api.preloadPresets(SYSTEM.id);
      }
      log("Registration complete");
    } catch (err) {
      error("Registration failed. The Dice So Nice API may have changed.", err);
    }
  });
}

Hooks.once("init", initModule);
