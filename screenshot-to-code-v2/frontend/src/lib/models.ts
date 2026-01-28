// Keep in sync with backend (llm.py)
// Order here matches dropdown order
export enum CodeGenerationModel {
  CLAUDE_4_5_SONNET_2025_09_29 = "claude-sonnet-4-5-20250929",
  GPT_4O_2024_05_13 = "gpt-4o-2024-05-13",
  GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09",
  GPT_4_VISION = "gpt_4_vision",
  CLAUDE_3_SONNET = "claude_3_sonnet",
  GEMMA_3_27B = "gemma-3-27b-it",
  GEMINI_3_FLASH_PREVIEW_HIGH = "gemini-3-flash-preview (high thinking)",
  GEMINI_2_5_FLASH = "gemini-2.5-flash",
  GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite",
}

// Will generate a static error if a model in the enum above is not in the descriptions
export const CODE_GENERATION_MODEL_DESCRIPTIONS: {
  [key in CodeGenerationModel]: { name: string; inBeta: boolean };
} = {
  "gpt-4o-2024-05-13": { name: "GPT-4o", inBeta: false },
  "claude-sonnet-4-5-20250929": { name: "Claude Sonnet 4.5", inBeta: false },
  "gpt-4-turbo-2024-04-09": { name: "GPT-4 Turbo (deprecated)", inBeta: false },
  gpt_4_vision: { name: "GPT-4 Vision (deprecated)", inBeta: false },
  claude_3_sonnet: { name: "Claude 3 (deprecated)", inBeta: false },
  "gemma-3-27b-it": { name: "Gemma 3 27b (Unavailable)", inBeta: false },
  "gemini-3-flash-preview (high thinking)": { name: "Gemini 3 Flash", inBeta: true },
  "gemini-2.5-flash": { name: "Gemini 2.5 Flash", inBeta: false },
  "gemini-2.5-flash-lite": { name: "Gemini 2.5 Flash Lite", inBeta: false },
};
