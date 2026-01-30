import React, { useEffect, useRef, useState } from "react";
import { Rnd } from "react-rnd";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { addHighlight, getAdjustedCoordinates, removeHighlight } from "./utils";
import { useAppStore } from "../../store/app-store";
import KeyboardShortcutBadge from "../core/KeyboardShortcutBadge";

interface EditPopupProps {
  event: MouseEvent | null;
  iframeRef: React.RefObject<HTMLIFrameElement>;
  scale: number;
}

const EditPopup: React.FC<EditPopupProps> = ({
  event,
  iframeRef,
  scale,
}) => {
  // App state
  const { inSelectAndEditMode, addPendingEdit } = useAppStore();

  // Create a wrapper ref to store inSelectAndEditMode so the value is not stale
  // in a event listener
  const inSelectAndEditModeRef = useRef(inSelectAndEditMode);

  // Update the ref whenever the state changes
  useEffect(() => {
    inSelectAndEditModeRef.current = inSelectAndEditMode;
  }, [inSelectAndEditMode]);

  // Popup state
  const [popupVisible, setPopupVisible] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });

  // Edit state
  const [selectedElement, setSelectedElement] = useState<
    HTMLElement | undefined
  >(undefined);
  const [updateText, setUpdateText] = useState("");

  // Textarea ref for focusing
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  function onUpdate(updateText: string) {
    if (!selectedElement) return;

    // Add to pending edits queue
    addPendingEdit(selectedElement, updateText);

    // Unselect the element (removes highlight)
    if (selectedElement) removeHighlight(selectedElement);
    setSelectedElement(undefined);

    // Hide the popup
    setPopupVisible(false);
  }

  // Remove highlight and reset state when not in select and edit mode
  useEffect(() => {
    if (!inSelectAndEditMode) {
      if (selectedElement) removeHighlight(selectedElement);
      setSelectedElement(undefined);
      setPopupVisible(false);
    }
  }, [inSelectAndEditMode, selectedElement]);

  // Handle the click event
  useEffect(() => {
    // Return if not in select and edit mode
    if (!inSelectAndEditModeRef.current || !event) {
      return;
    }

    // Prevent default to avoid issues like label clicks triggering textareas, etc.
    event.preventDefault();

    const targetElement = event.target as HTMLElement;

    // Return if no target element
    if (!targetElement) return;

    // Highlight and set the selected element
    setSelectedElement((prev) => {
      // Remove style from previous element
      if (prev) {
        removeHighlight(prev);
      }
      return addHighlight(targetElement);
    });

    // Calculate adjusted coordinates
    const adjustedCoordinates = getAdjustedCoordinates(
      event.clientX,
      event.clientY,
      iframeRef.current?.getBoundingClientRect(),
      scale
    );

    // Show the popup at the click position
    setPopupVisible(true);
    setPopupPosition({ x: adjustedCoordinates.x, y: adjustedCoordinates.y });

    // Reset the update text
    setUpdateText("");

    // Focus the textarea
    textareaRef.current?.focus();
  }, [event, iframeRef, scale]);

  // Focus the textarea when the popup is visible (we can't do this only when handling the click event
  // because the textarea is not rendered yet)
  // We need to also do it in the click event because popupVisible doesn't change values in that event
  useEffect(() => {
    if (popupVisible) {
      textareaRef.current?.focus();
    }
  }, [popupVisible]);

  if (!popupVisible) return null;

  return (
    <Rnd
      key={popupPosition.x + "-" + popupPosition.y} // Force re-mount on new click position
      default={{
        x: popupPosition.x,
        y: popupPosition.y,
        width: 320,
        height: "auto",
      }}
      minWidth={300}
      minHeight={200}
      bounds="window"
      dragHandleClassName="drag-handle"
      className="z-50"
    >
      <div className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-lg flex flex-col h-full w-full">
        {/* Drag Handle Header */}
        <div className="drag-handle bg-gray-100 dark:bg-gray-700 p-2 rounded-t cursor-move flex justify-between items-center border-b border-gray-200 dark:border-gray-600">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">Edit Element</span>
            <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-red-400"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
            </div>
        </div>
        
        <div className="p-4 flex flex-col flex-grow overflow-hidden">
            <div className="mb-2 max-h-32 overflow-y-auto text-xs font-mono bg-gray-100 dark:bg-gray-900 p-2 rounded text-gray-600 dark:text-gray-300 break-words whitespace-pre-wrap">
                {selectedElement?.outerHTML.replace(/ style="[^"]*border: 2px solid red[^"]*"/, "")}
            </div>
            
            <Textarea
                ref={textareaRef}
                value={updateText}
                onChange={(e) => setUpdateText(e.target.value)}
                placeholder="Tell the AI what to change about this element..."
                className="dark:bg-gray-700 dark:text-white flex-grow resize-none"
                onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                    e.preventDefault();
                    onUpdate(updateText);
                }
                }}
            />
            
            <div className="flex justify-end mt-2 pt-2">
                <Button
                className="dark:bg-gray-700 dark:text-white w-full"
                onClick={() => onUpdate(updateText)}
                >
                Add Change <KeyboardShortcutBadge letter="enter" />
                </Button>
            </div>
        </div>
      </div>
    </Rnd>
  );
};

export default EditPopup;
