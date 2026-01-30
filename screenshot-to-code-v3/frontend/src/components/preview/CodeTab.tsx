import { FaCopy, FaSave } from "react-icons/fa";
import CodeMirror from "./CodeMirror";
import { Button } from "../ui/button";
import { Settings } from "../../types";
import copy from "copy-to-clipboard";
import { useCallback, useState, useEffect } from "react";
import toast from "react-hot-toast";

interface Props {
  code: string;
  onSave: (code: string) => void;
  settings: Settings;
}

function CodeTab({ code, onSave, settings }: Props) {
  // Local editing state - separate from the prop to avoid conflicts
  const [localCode, setLocalCode] = useState(code);
  const [hasChanges, setHasChanges] = useState(false);

  // Sync local code when prop changes (e.g., switching variants)
  useEffect(() => {
    setLocalCode(code);
    setHasChanges(false);
  }, [code]);

  const handleCodeChange = useCallback((newCode: string) => {
    setLocalCode(newCode);
    setHasChanges(newCode !== code);
  }, [code]);

  const copyCode = useCallback(() => {
    copy(localCode);
    toast.success("Copied to clipboard");
  }, [localCode]);

  const handleSave = useCallback(() => {
    onSave(localCode);
    setHasChanges(false);
    toast.success("Code saved!");
  }, [localCode, onSave]);

  return (
    <div className="relative">
      <div className="flex justify-start items-center px-4 mb-2">
        <span
          title="Copy Code"
          className="bg-black text-white flex items-center justify-center hover:text-black hover:bg-gray-100 cursor-pointer rounded-lg text-sm p-2.5"
          onClick={copyCode}
        >
          Copy Code <FaCopy className="ml-2" />
        </span>
        <Button
          onClick={handleSave}
          disabled={!hasChanges}
          className={`ml-2 py-2 px-4 border rounded-md flex items-center gap-x-2 ${
            hasChanges 
              ? 'bg-green-500 text-white border-green-600 hover:bg-green-600' 
              : 'bg-gray-200 text-gray-500 border-gray-300 cursor-not-allowed'
          }`}
        >
          <FaSave /> Save
        </Button>
        {hasChanges && (
          <span className="ml-2 text-orange-500 text-sm">未保存の変更があります</span>
        )}
      </div>
      <CodeMirror
        code={localCode}
        editorTheme={settings.editorTheme}
        onCodeChange={handleCodeChange}
      />
    </div>
  );
}

export default CodeTab;
