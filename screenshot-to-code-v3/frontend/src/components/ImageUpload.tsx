import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "react-hot-toast";
import { URLS } from "../urls";
import ScreenRecorder from "./recording/ScreenRecorder";
import { ScreenRecorderState } from "../types";
import { SliceList, FileWithPreview } from "./SliceList";
import { RegionSelector, ImageRegion } from "./RegionSelector";

const baseStyle = {
  flex: 1,
  width: "80%",
  margin: "0 auto",
  minHeight: "200px",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px",
  borderWidth: 2,
  borderRadius: 2,
  borderColor: "#eeeeee",
  borderStyle: "dashed",
  backgroundColor: "#fafafa",
  color: "#bdbdbd",
  outline: "none",
  transition: "border .24s ease-in-out",
};

const focusedStyle = {
  borderColor: "#2196f3", // Blue
};

const acceptStyle = {
  borderColor: "#00e676", // Green
};

const rejectStyle = {
  borderColor: "#ff1744", // Red
};

// TODO: Move to a separate file
function fileToDataURL(file: File) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
}

interface Props {
  setReferenceImages: (
    referenceImages: string[],
    inputMode: "image" | "video",
    textPrompt?: string
  ) => void;
  onUploadStateChange?: (hasUpload: boolean) => void;
}

function ImageUpload({ setReferenceImages, onUploadStateChange }: Props) {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [uploadedInputMode, setUploadedInputMode] = useState<
    "image" | "video"
  >("image");
  const [textPrompt, setTextPrompt] = useState("");
  const [showTextPrompt, setShowTextPrompt] = useState(false);
  const textInputRef = useRef<HTMLTextAreaElement>(null);
  const [regionModeEnabled, setRegionModeEnabled] = useState(false);
  const [imageRegions, setImageRegions] = useState<ImageRegion[]>([]);

  // TODO: Switch to Zustand
  const [screenRecorderState, setScreenRecorderState] =
    useState<ScreenRecorderState>(ScreenRecorderState.INITIAL);

  const hasUploadedFile = files.length > 0;

  // Notify parent of upload state changes
  useEffect(() => {
    onUploadStateChange?.(hasUploadedFile);
  }, [hasUploadedFile, onUploadStateChange]);

  const handleGenerate = useCallback(async () => {
    if (files.length > 0) {
      // Re-read data URLs to ensure order matches the current files list
      try {
          const dataUrls = await Promise.all(files.map(file => fileToDataURL(file)));
          // Include region data in the text prompt if regions are defined
          let finalPrompt = textPrompt;
          if (regionModeEnabled && imageRegions.length > 0) {
            const regionData = JSON.stringify(imageRegions);
            finalPrompt = `__MANUAL_REGIONS__${regionData}__END_REGIONS__${textPrompt}`;
          }
          setReferenceImages(dataUrls as string[], uploadedInputMode, finalPrompt);
      } catch (error) {
          toast.error("Error processing files");
          console.error(error);
      }
    }
  }, [files, uploadedInputMode, textPrompt, imageRegions, regionModeEnabled, setReferenceImages]);

  // Global Enter key listener for generating when image is uploaded
  useEffect(() => {
    if (!hasUploadedFile) return;

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        // Don't fire if textarea is focused (it has its own handler)
        if (document.activeElement === textInputRef.current) return;
        e.preventDefault();
        handleGenerate();
      }
    };

    document.addEventListener("keydown", handleGlobalKeyDown);
    return () => document.removeEventListener("keydown", handleGlobalKeyDown);
  }, [hasUploadedFile, handleGenerate]);

  const filesRef = useRef<FileWithPreview[]>([]);
  useEffect(() => {
    filesRef.current = files;
  }, [files]);

  useEffect(() => {
    return () => {
      filesRef.current.forEach((file) => URL.revokeObjectURL(file.preview));
    };
  }, []);

  const handleClear = () => {
    files.forEach((file) => URL.revokeObjectURL(file.preview));
    setFiles([]);
    setTextPrompt("");
    setShowTextPrompt(false);
    setImageRegions([]);
    setRegionModeEnabled(false);
  };

  const removeFile = (index: number) => {
    URL.revokeObjectURL(files[index].preview);
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleGenerate();
    }
  };

  const { getRootProps, getInputProps, isFocused, isDragAccept, isDragReject } =
    useDropzone({
      maxFiles: 20, // Increased limit
      maxSize: 1024 * 1024 * 20, // 20 MB
      accept: {
        // Image formats
        "image/png": [".png"],
        "image/jpeg": [".jpeg"],
        "image/jpg": [".jpg"],
        // Video formats
        "video/quicktime": [".mov"],
        "video/mp4": [".mp4"],
        "video/webm": [".webm"],
      },
      onDrop: (acceptedFiles) => {
        // Prepare preview objects
        const newFiles = acceptedFiles.map((file: File) =>
            Object.assign(file, {
              preview: URL.createObjectURL(file),
            })
          ) as FileWithPreview[];
        
        setFiles(prev => [...prev, ...newFiles]);

        // Determine mode from the first file (assuming mixed content isn't primary use case but logic handles it)
        if (acceptedFiles.length > 0) {
             const inputMode = acceptedFiles[0].type.startsWith("video") ? "video" : "image";
             setUploadedInputMode(inputMode);
             // Focus text input
             setTimeout(() => textInputRef.current?.focus(), 100);
        }
      },
      onDropRejected: (rejectedFiles) => {
        toast.error(rejectedFiles[0].errors[0].message);
      },
    });

  const style = useMemo(
    () => ({
      ...baseStyle,
      ...(isFocused ? focusedStyle : {}),
      ...(isDragAccept ? acceptStyle : {}),
      ...(isDragReject ? rejectStyle : {}),
    }),
    [isFocused, isDragAccept, isDragReject]
  );

  // Screen recorder callback - wrap to include empty text prompt
  const handleScreenRecorderGenerate = (
    images: string[],
    inputMode: "image" | "video"
  ) => {
    setReferenceImages(images, inputMode, "");
  };

  return (
    <section className="container flex flex-col items-center gap-6">
      
        {/* Dropzone is always visible but smaller if files exist */}
        <div {...getRootProps({ style: style as any })} className="cursor-pointer hover:bg-gray-50 transition-colors bg-white">
          <input {...getInputProps()} className="file-input" />
          <p className="text-slate-600 text-center">
            {hasUploadedFile ? (
                <span>Add more slices...</span>
            ) : (
                <span>
                    Drag & drop screenshots here<br />
                    <span className="text-sm text-slate-400">(Supports multiple files for Hybrid LP)</span>
                </span>
            )}
          </p>
        </div>

      {hasUploadedFile && (
        <div className="flex flex-col items-center gap-4 w-full">
          
          {/* Region Mode Toggle */}
          <div className="flex items-center gap-4 w-full max-w-2xl justify-between bg-gray-50 p-3 rounded-lg border">
            <div>
              <span className="text-sm font-medium text-gray-700">Region Selection Mode</span>
              <p className="text-xs text-gray-500">画像上で切り抜き領域を指定</p>
            </div>
            <button
              onClick={() => setRegionModeEnabled(!regionModeEnabled)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                regionModeEnabled 
                  ? 'bg-blue-500 text-white hover:bg-blue-600' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {regionModeEnabled ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Region Selector - show when mode is enabled and there's only 1 image */}
          {regionModeEnabled && files.length === 1 && files[0].type.startsWith('image') && (
            <div className="w-full max-w-4xl bg-gray-100 p-4 rounded-lg">
              <div className="mb-2 text-sm text-gray-600">
                画像上でドラッグして領域を選択 ({imageRegions.length}個の領域)
              </div>
              <RegionSelector
                imageSrc={files[0].preview}
                regions={imageRegions}
                onRegionsChange={setImageRegions}
              />
            </div>
          )}

          {regionModeEnabled && files.length > 1 && (
            <div className="w-full max-w-2xl bg-yellow-50 border border-yellow-200 p-3 rounded-lg text-sm text-yellow-700">
              ⚠️ Region Selection Modeは1枚の画像でのみ使用できます
            </div>
          )}

          <SliceList 
            files={files} 
            setFiles={setFiles} 
            onRemove={removeFile}
          />

          <div className="flex gap-2">
            <button
               onClick={handleClear}
               className="text-sm text-red-500 hover:text-red-700 underline"
            >
                Clear All
            </button>
          </div>

          {/* Text Prompt Toggle/Input */}
          {!showTextPrompt ? (
            <button
              onClick={() => {
                setShowTextPrompt(true);
                setTimeout(() => textInputRef.current?.focus(), 50);
              }}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              (optional) add text prompt
            </button>
          ) : (
            <div className="w-full max-w-lg">
              <textarea
                ref={textInputRef}
                value={textPrompt}
                onChange={(e) => setTextPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe any specific requirements or changes..."
                className="w-full p-3 text-sm border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                rows={3}
              />
            </div>
          )}

          {/* Generate Button */}
          <div className="flex flex-col items-center gap-1 w-full max-w-md">
            <button
              onClick={handleGenerate}
              className="w-full py-3 px-6 bg-black text-white font-medium rounded-md hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 shadow-lg"
            >
              Generate Code ({files.length} slices)
            </button>
            <p className="text-xs text-gray-400">
              Press Enter to generate
            </p>
          </div>
        </div>
      )}

      {screenRecorderState === ScreenRecorderState.INITIAL && !hasUploadedFile && (
        <div className="text-center text-sm text-slate-800 mt-4">
          Upload a screen recording (.mp4, .mov) or record your screen to clone
          a whole app (experimental).{" "}
          <a
            className="underline"
            href={URLS["intro-to-video"]}
            target="_blank"
          >
            Learn more.
          </a>
        </div>
      )}
      {!hasUploadedFile && (
        <ScreenRecorder
          screenRecorderState={screenRecorderState}
          setScreenRecorderState={setScreenRecorderState}
          generateCode={handleScreenRecorderGenerate}
        />
      )}
    </section>
  );
}

export default ImageUpload;
