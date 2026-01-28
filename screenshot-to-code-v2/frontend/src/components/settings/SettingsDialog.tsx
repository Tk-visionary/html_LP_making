import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FaCog, FaSave, FaFolderOpen } from "react-icons/fa";
import { EditorTheme, Settings } from "../../types";
import { Switch } from "../ui/switch";
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { capitalize } from "../../lib/utils";
import { IS_RUNNING_ON_CLOUD, HTTP_BACKEND_URL } from "../../config";
import toast from "react-hot-toast";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import TemplateCreatorDialog from "../TemplateCreatorDialog";

interface Props {
  settings: Settings;
  setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}

function SettingsDialog({ settings, setSettings }: Props) {
  const [templates, setTemplates] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [newTemplateName, setNewTemplateName] = useState<string>("");

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${HTTP_BACKEND_URL}/templates`);
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error("Failed to fetch templates", error);
    }
  };

  useEffect(() => {
    if (settings.isTemplateEnabled) {
      fetchTemplates();
    }
  }, [settings.isTemplateEnabled]);

  const loadTemplate = async () => {
    if (!selectedTemplate) return;
    try {
      const response = await fetch(`${HTTP_BACKEND_URL}/templates/${selectedTemplate}`);
      if (response.ok) {
        const data = await response.json();
        setSettings((s) => ({
          ...s,
          templateContent: data.content,
        }));
        toast.success("Template loaded");
      }
    } catch (error) {
      toast.error("Failed to load template");
    }
  };

  const saveTemplate = async () => {
    if (!newTemplateName || !settings.templateContent) {
      toast.error("Please enter a name and content");
      return;
    }
    try {
      const response = await fetch(`${HTTP_BACKEND_URL}/templates`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newTemplateName,
          content: settings.templateContent,
        }),
      });
      if (response.ok) {
        toast.success("Template saved");
        fetchTemplates();
        setNewTemplateName("");
      } else {
        toast.error("Failed to save template");
      }
    } catch (error) {
      toast.error("Failed to save template");
    }
  };

  const handleThemeChange = (theme: EditorTheme) => {
    setSettings((s) => ({
      ...s,
      editorTheme: theme,
    }));
  };

  return (
    <Dialog>
      <DialogTrigger>
        <FaCog />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="mb-4">Settings</DialogTitle>
        </DialogHeader>

        <div className="flex items-center space-x-2">
          <Label htmlFor="image-generation">
            <div>DALL-E Placeholder Image Generation</div>
            <div className="font-light mt-2 text-xs">
              More fun with it but if you want to save money, turn it off.
            </div>
          </Label>
          <Switch
            id="image-generation"
            checked={settings.isImageGenerationEnabled}
            onCheckedChange={() =>
              setSettings((s) => ({
                ...s,
                isImageGenerationEnabled: !s.isImageGenerationEnabled,
              }))
            }
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Label htmlFor="template-enabled">
            <div>Enable Code Template</div>
            <div className="font-light mt-2 text-xs">
              Use a custom HTML/CSS template as a base for generation.
            </div>
          </Label>
          <Switch
            id="template-enabled"
            checked={settings.isTemplateEnabled}
            onCheckedChange={() =>
              setSettings((s) => ({
                ...s,
                isTemplateEnabled: !s.isTemplateEnabled,
              }))
            }
          />
        </div>

        {settings.isTemplateEnabled && (
          <div className="space-y-3 border p-3 rounded-md bg-slate-50 dark:bg-slate-900">
             <div className="flex flex-col space-y-2">
                <div className="flex justify-between items-center">
                    <Label>Template Manager</Label>
                    <TemplateCreatorDialog onTemplateSaved={fetchTemplates} />
                </div>
                <div className="flex space-x-2">
                  <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select a template" />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.map((t) => (
                        <SelectItem key={t} value={t}>
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <button
                    onClick={loadTemplate}
                    disabled={!selectedTemplate}
                    className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    <FaFolderOpen /> <span>Load</span>
                  </button>
                </div>
             </div>

             <div>
                <Label htmlFor="template-content">
                  <div>Template Content</div>
                  <div className="font-light mt-1 mb-2 text-xs leading-relaxed">
                    Paste your HTML/CSS template here, or load one from the library.
                  </div>
                </Label>

                <Textarea
                  id="template-content"
                  placeholder="<div class='my-template'>...</div>"
                  value={settings.templateContent || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      templateContent: e.target.value,
                    }))
                  }
                  className="h-32 font-mono text-xs"
                />
             </div>

             <div className="flex space-x-2 items-end">
                <div className="flex-1">
                  <Label htmlFor="new-template-name" className="text-xs">Save as new template</Label>
                  <Input 
                    id="new-template-name" 
                    placeholder="template-name" 
                    value={newTemplateName}
                    onChange={(e) => setNewTemplateName(e.target.value)}
                  />
                </div>
                <button
                  onClick={saveTemplate}
                  className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 h-10"
                >
                  <FaSave /> <span>Save</span>
                </button>
             </div>
          </div>
        )}

        <div className="flex flex-col space-y-6">
          <div>
            <Label htmlFor="openai-api-key">
              <div>OpenAI API key</div>
              <div className="font-light mt-1 mb-2 text-xs leading-relaxed">
                Only stored in your browser. Never stored on servers. Overrides
                your .env config.
              </div>
            </Label>

            <Input
              id="openai-api-key"
              placeholder="OpenAI API key"
              value={settings.openAiApiKey || ""}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  openAiApiKey: e.target.value,
                }))
              }
            />
          </div>

          {!IS_RUNNING_ON_CLOUD && (
            <div>
              <Label htmlFor="openai-api-key">
                <div>OpenAI Base URL (optional)</div>
                <div className="font-light mt-2 leading-relaxed">
                  Replace with a proxy URL if you don't want to use the default.
                </div>
              </Label>

              <Input
                id="openai-base-url"
                placeholder="OpenAI Base URL"
                value={settings.openAiBaseURL || ""}
                onChange={(e) =>
                  setSettings((s) => ({
                    ...s,
                    openAiBaseURL: e.target.value,
                  }))
                }
              />
            </div>
          )}

          <div>
            <Label htmlFor="anthropic-api-key">
              <div>Anthropic API key</div>
              <div className="font-light mt-1 text-xs leading-relaxed">
                Only stored in your browser. Never stored on servers. Overrides
                your .env config.
              </div>
            </Label>

            <Input
              id="anthropic-api-key"
              placeholder="Anthropic API key"
              value={settings.anthropicApiKey || ""}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  anthropicApiKey: e.target.value,
                }))
              }
            />
          </div>

          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>Screenshot by URL Config</AccordionTrigger>
              <AccordionContent>
                <Label htmlFor="screenshot-one-api-key">
                  <div className="leading-normal font-normal text-xs">
                    If you want to use URLs directly instead of taking the
                    screenshot yourself, add a ScreenshotOne API key.{" "}
                    <a
                      href="https://screenshotone.com?via=screenshot-to-code"
                      className="underline"
                      target="_blank"
                    >
                      Get 100 screenshots/mo for free.
                    </a>
                  </div>
                </Label>

                <Input
                  id="screenshot-one-api-key"
                  className="mt-2"
                  placeholder="ScreenshotOne API key"
                  value={settings.screenshotOneApiKey || ""}
                  onChange={(e) =>
                    setSettings((s) => ({
                      ...s,
                      screenshotOneApiKey: e.target.value,
                    }))
                  }
                />
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>Theme Settings</AccordionTrigger>
              <AccordionContent className="space-y-4 flex flex-col">
                <div className="flex items-center justify-between">
                  <Label htmlFor="app-theme">
                    <div>App Theme</div>
                  </Label>
                  <div>
                    <button
                      className="flex rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50t"
                      onClick={() => {
                        document
                          .querySelector("div.mt-2")
                          ?.classList.toggle("dark"); // enable dark mode for sidebar
                        document.body.classList.toggle("dark");
                        document
                          .querySelector('div[role="presentation"]')
                          ?.classList.toggle("dark"); // enable dark mode for upload container
                      }}
                    >
                      Toggle dark mode
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="editor-theme">
                    <div>
                      Code Editor Theme - requires page refresh to update
                    </div>
                  </Label>
                  <div>
                    <Select // Use the custom Select component here
                      name="editor-theme"
                      value={settings.editorTheme}
                      onValueChange={(value) =>
                        handleThemeChange(value as EditorTheme)
                      }
                    >
                      <SelectTrigger className="w-[180px]">
                        {capitalize(settings.editorTheme)}
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cobalt">Cobalt</SelectItem>
                        <SelectItem value="espresso">Espresso</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        <DialogFooter>
          <DialogClose>Save</DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default SettingsDialog;
