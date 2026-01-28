import React from "react";
import { useAppStore } from "../../store/app-store";
import { AppState, Settings } from "../../types";
import OutputSettingsSection from "./OutputSettingsSection";
import { Stack } from "../../lib/stacks";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Badge } from "../ui/badge";
import {
  CodeGenerationModel,
  CODE_GENERATION_MODEL_DESCRIPTIONS,
} from "../../lib/models";

interface GenerationSettingsProps {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}

export const GenerationSettings: React.FC<GenerationSettingsProps> = ({
  settings,
  setSettings,
}) => {
  const { appState } = useAppStore();

  function setStack(stack: Stack) {
    setSettings((prev: Settings) => ({
      ...prev,
      generatedCodeConfig: stack,
    }));
  }

  function setModel(model: CodeGenerationModel) {
    setSettings((prev: Settings) => ({
      ...prev,
      codeGenerationModel: model,
    }));
  }

  const shouldDisableUpdates =
    appState === AppState.CODING || appState === AppState.CODE_READY;

  return (
    <div className="flex flex-col gap-y-4">
      <OutputSettingsSection
        stack={settings.generatedCodeConfig}
        setStack={setStack}
        shouldDisableUpdates={shouldDisableUpdates}
      />

      <div className="flex flex-col gap-y-2 justify-between text-sm">
        <div className="grid grid-cols-3 items-center gap-4">
          <span>Model:</span>
          <Select
            value={settings.codeGenerationModel}
            onValueChange={(value: string) =>
              setModel(value as CodeGenerationModel)
            }
            disabled={shouldDisableUpdates}
          >
            <SelectTrigger className="col-span-2">
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {[
                  CodeGenerationModel.GEMINI_3_FLASH_PREVIEW_HIGH,
                  CodeGenerationModel.GEMMA_3_27B,
                  CodeGenerationModel.GEMINI_2_5_FLASH,
                  CodeGenerationModel.GEMINI_2_5_FLASH_LITE,
                ].map((model) => (
                  <SelectItem key={model} value={model}>
                    <div className="flex items-center">
                      <span>{CODE_GENERATION_MODEL_DESCRIPTIONS[model].name}</span>
                      {CODE_GENERATION_MODEL_DESCRIPTIONS[model].inBeta && (
                        <Badge className="ml-2" variant="secondary">
                          Beta
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
};
