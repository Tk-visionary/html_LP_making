import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { FaGripLines, FaTimes } from "react-icons/fa";

interface Props {
  files: FileWithPreview[];
  setFiles: (files: FileWithPreview[]) => void;
  onRemove: (index: number) => void;
}

export type FileWithPreview = {
  preview: string;
} & File;

function VideoPreview({ file }: { file: FileWithPreview }) {
  return (
    <video
      src={file.preview}
      className="h-20 w-auto object-contain rounded border border-gray-200 bg-gray-50"
      controls
    />
  );
}

function ImagePreview({ file }: { file: FileWithPreview }) {
  return (
    <img
      src={file.preview}
      alt="Preview"
      className="h-20 w-auto object-contain rounded border border-gray-200 bg-gray-50"
    />
  );
}

function SortableItem({
  file,
  index,
  onRemove,
}: {
  file: FileWithPreview;
  index: number;
  onRemove: (index: number) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: file.name + index });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 10 : 1,
    opacity: isDragging ? 0.8 : 1,
  };

  const isVideo = file.type.startsWith("video");

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-4 bg-white p-3 rounded-lg shadow-sm border border-gray-200 mb-2"
    >
      <div
        {...attributes}
        {...listeners}
        className="cursor-move text-gray-400 hover:text-gray-600 p-2"
      >
        <FaGripLines size={20} />
      </div>

      <div className="flex-shrink-0">
        {isVideo ? <VideoPreview file={file} /> : <ImagePreview file={file} />}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {file.name}
        </p>
        <p className="text-xs text-gray-500">
          {(file.size / 1024).toFixed(1)} KB
        </p>
      </div>

       <div className="bg-gray-100 px-2 py-1 rounded text-xs font-mono text-gray-500">
          Slice #{index + 1}
       </div>

      <button
        onClick={() => onRemove(index)}
        className="text-gray-400 hover:text-red-500 p-2 rounded-full hover:bg-gray-50 transition-colors"
        title="Remove"
      >
        <FaTimes size={16} />
      </button>
    </div>
  );
}

export function SliceList({ files, setFiles, onRemove }: Props) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = files.findIndex((f, i) => (f.name + i) === active.id);
      const newIndex = files.findIndex((f, i) => (f.name + i) === over?.id);

      if (oldIndex !== -1 && newIndex !== -1) {
          setFiles(arrayMove(files, oldIndex, newIndex));
      }
    }
  }

  return (
    <div className="w-full max-w-2xl bg-gray-50 p-4 rounded-xl border border-gray-200">
        <div className="flex items-center justify-between mb-3 px-1">
            <h3 className="text-sm font-semibold text-gray-700">
                Uploaded Slices ({files.length})
            </h3>
            <span className="text-xs text-gray-500">
                Drag to reorder
            </span>
        </div>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={files.map((f, i) => f.name + i)}
          strategy={verticalListSortingStrategy}
        >
          {files.map((file, index) => (
            <SortableItem
              key={file.name + index}
              file={file}
              index={index}
              onRemove={onRemove}
            />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
}
