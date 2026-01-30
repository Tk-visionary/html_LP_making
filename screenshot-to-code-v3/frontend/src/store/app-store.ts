import { create } from "zustand";
import { AppState } from "../types";

// Store for app-wide state
interface AppStore {
  appState: AppState;
  setAppState: (state: AppState) => void;

  // UI state
  updateInstruction: string;
  setUpdateInstruction: (instruction: string) => void;

  // Update images support (multiple images)
  updateImages: string[];
  setUpdateImages: (images: string[]) => void;

  inSelectAndEditMode: boolean;
  toggleInSelectAndEditMode: () => void;
  disableInSelectAndEditMode: () => void;

  // Pending edits
  pendingEdits: { element: HTMLElement; instruction: string }[];
  addPendingEdit: (element: HTMLElement, instruction: string) => void;
  removePendingEdit: (index: number) => void;
  clearPendingEdits: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  appState: AppState.INITIAL,
  setAppState: (state: AppState) => set({ appState: state }),

  // UI state
  updateInstruction: "",
  setUpdateInstruction: (instruction: string) =>
    set({ updateInstruction: instruction }),

  // Update images support
  updateImages: [],
  setUpdateImages: (images: string[]) => set({ updateImages: images }),

  inSelectAndEditMode: false,
  toggleInSelectAndEditMode: () =>
    set((state) => ({ inSelectAndEditMode: !state.inSelectAndEditMode })),
  disableInSelectAndEditMode: () => set({ inSelectAndEditMode: false }),

  // Pending edits for selection mode batch update
  pendingEdits: [],
  addPendingEdit: (element: HTMLElement, instruction: string) =>
    set((state) => ({
      pendingEdits: [...state.pendingEdits, { element, instruction }],
    })),
  removePendingEdit: (index: number) =>
    set((state) => ({
      pendingEdits: state.pendingEdits.filter((_, i) => i !== index),
    })),
  clearPendingEdits: () => set({ pendingEdits: [] }),
}));
