import React, { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { FaPlus, FaMagic, FaSave, FaSpinner, FaTimes } from "react-icons/fa";
import { HTTP_BACKEND_URL } from "../config";
import toast from "react-hot-toast";

interface Props {
  onTemplateSaved: () => void;
}

export default function TemplateCreatorDialog({ onTemplateSaved }: Props) {
  const [open, setOpen] = useState(false);
  const [images, setImages] = useState<string[]>([]);
  const [generatedCode, setGeneratedCode] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        if (result) {
          setImages((prev) => [...prev, result]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const generateTemplate = async () => {
    if (images.length === 0) {
      toast.error("Please upload at least one image");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch(`${HTTP_BACKEND_URL}/templates/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ images }),
      });

      if (!response.ok) throw new Error("Generation failed");

      const data = await response.json();
      setGeneratedCode(data.content);
      toast.success("Template generated!");
    } catch (error) {
        console.error(error);
      toast.error("Failed to generate template");
    } finally {
      setIsGenerating(false);
    }
  };

  const saveTemplate = async () => {
    if (!templateName || !generatedCode) {
      toast.error("Please provide a name and generate code first");
      return;
    }

    try {
      const response = await fetch(`${HTTP_BACKEND_URL}/templates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: templateName, content: generatedCode }),
      });

      if (response.ok) {
        toast.success("Template saved!");
        onTemplateSaved();
        setOpen(false);
        // Reset state
        setImages([]);
        setGeneratedCode("");
        setTemplateName("");
      } else {
        toast.error("Failed to save template");
      }
    } catch (error) {
      toast.error("Failed to save template");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full">
          <FaPlus className="mr-2" /> Create New Template
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Template Creator</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Image Upload Section */}
          <div className="space-y-2">
            <Label>1. Upload Screenshots (Multiple supported)</Label>
            <div className="grid grid-cols-4 gap-2">
              {images.map((img, idx) => (
                <div key={idx} className="relative group aspect-video border rounded overflow-hidden">
                  <img src={img} alt={`Upload ${idx}`} className="object-cover w-full h-full" />
                  <button
                    onClick={() => removeImage(idx)}
                    className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <FaTimes size={10} />
                  </button>
                </div>
              ))}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed rounded flex flex-col items-center justify-center aspect-video cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-900"
              >
                <FaPlus className="text-gray-400 mb-1" />
                <span className="text-xs text-gray-500">Add Image</span>
              </div>
            </div>
            <input
              type="file"
              multiple
              accept="image/*"
              className="hidden"
              ref={fileInputRef}
              onChange={handleImageUpload}
            />
          </div>

          {/* Generator Action */}
          <div className="flex justify-center">
            <Button onClick={generateTemplate} disabled={isGenerating || images.length === 0}>
              {isGenerating ? <FaSpinner className="animate-spin mr-2" /> : <FaMagic className="mr-2" />}
              {isGenerating ? "Analyzing & Generating..." : "Generate Template Framework"}
            </Button>
          </div>

          {/* Result Section */}
          {generatedCode && (
            <div className="space-y-2 animate-in fade-in zoom-in duration-300">
              <Label>2. Generated Template Code</Label>
              <Textarea
                value={generatedCode}
                onChange={(e) => setGeneratedCode(e.target.value)}
                className="font-mono text-xs h-64"
              />
              
              <div className="flex items-end gap-2 pt-2 border-t mt-4">
                <div className="flex-1">
                    <Label htmlFor="save-name">Template Name</Label>
                    <Input 
                        id="save-name" 
                        placeholder="My New Layout" 
                        value={templateName}
                        onChange={(e) => setTemplateName(e.target.value)}
                    />
                </div>
                <Button onClick={saveTemplate} style={{backgroundColor: 'green'}}>
                    <FaSave className="mr-2" /> Save to Library
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
