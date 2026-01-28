import React, { useEffect, useState } from "react";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { FaHistory, FaTrash } from "react-icons/fa";

interface HistoryItem {
  id: string;
  date: string;
  timestamp: string;
  prompt: string;
  input_mode: string;
  url: string;
}

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSelect: (session: any) => void;
}

const HistoryList: React.FC<Props> = ({ onSelect }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:7002/history/list");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (item: HistoryItem) => {
    try {
      const res = await fetch(`http://localhost:7002${item.url}`);
      if (res.ok) {
        const data = await res.json();
        onSelect(data);
      }
    } catch (e) {
      console.error("Failed to fetch session", e);
    }
  };

  const handleDelete = async (e: React.MouseEvent, item: HistoryItem) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this history?")) {
      return;
    }
    
    try {
      const res = await fetch(`http://localhost:7002/history/${item.date}/${item.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setHistory((prev) => prev.filter((h) => h.id !== item.id));
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleEditClick = (e: React.MouseEvent, item: HistoryItem) => {
    e.stopPropagation();
    setEditingId(item.id);
    setEditTitle((item.prompt || "").replace(/\.\.\.$/, "")); // Remove ellipsis if present for initial edit value
  };

  const handleSaveTitle = async (e: React.SyntheticEvent, item: HistoryItem) => {
    e.stopPropagation();
    if (!editTitle.trim()) {
        setEditingId(null);
        return;
    }

    try {
      const res = await fetch("http://localhost:7002/history/title", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date_str: item.date,
          session_id: item.id,
          title: editTitle,
        }),
      });

      if (res.ok) {
        setHistory((prev) =>
          prev.map((h) => (h.id === item.id ? { ...h, prompt: editTitle } : h))
        );
      }
    } catch (e) {
      console.error("Failed to update title", e);
    } finally {
      setEditingId(null);
    }
  };

  const handleEditKeyDown = (e: React.KeyboardEvent, item: HistoryItem) => {
      if (e.key === "Enter") {
          handleSaveTitle(e, item);
      } else if (e.key === "Escape") {
          setEditingId(null);
      }
  };

  if (loading) {
    return <div className="text-sm text-gray-500 p-2">Loading history...</div>;
  }

  if (history.length === 0) return (
      <div className="text-sm text-gray-400 p-2">No history found.</div>
  );

  return (
    <div className="flex flex-col gap-y-4 w-full text-left">
      <div className="flex items-center gap-x-2 text-sm font-semibold text-gray-500 uppercase tracking-wider">
        <FaHistory className="w-4 h-4" />
        History
      </div>
      <ScrollArea className="h-[200px] w-full rounded-md border p-2">
        <div className="flex flex-col gap-y-2">
          {history.map((item) => (
            <div
              key={item.id}
              className="group flex flex-col gap-y-1 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-left transition-colors relative cursor-pointer"
              onClick={() => handleSelect(item)}
            >
              <div className="flex justify-between items-center w-full">
                <span className="text-xs text-gray-400">
                  {item.date} {item.timestamp.replace(/-/g, ":")}
                </span>
                <div className="flex items-center gap-x-2">
                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">
                    {item.input_mode}
                    </Badge>
                     {/* Edit Button */}
                     <button
                        onClick={(e) => handleEditClick(e, item)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-blue-500 transition-opacity"
                        title="Rename"
                    >
                        <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 576 512" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M402.6 83.2l90.2 90.2c3.8 3.8 3.8 10 0 13.8L274.4 405.6l-92.8 10.3c-12.4 1.4-22.9-9.1-21.5-21.5l10.3-92.8L388.8 83.2c3.8-3.8 10-3.8 13.8 0zm162-22.9l-48.8-48.8c-15.2-15.2-39.9-15.2-55.2 0l-35.4 35.4c-3.8 3.8-3.8 10 0 13.8l90.2 90.2c3.8 3.8 10 3.8 13.8 0l35.4-35.4c15.2-15.3 15.2-40 0-55.2zM381.8 162.5l-90.2-90.2 13.8-13.8c3.8-3.8 10-3.8 13.8 0l90.2 90.2c3.8 3.8 3.8 10 0 13.8l-13.8 13.8zM32.5 512h195.1V368H32.5C14.6 368 0 382.6 0 400.5v79C0 497.4 14.6 512 32.5 512z"></path></svg>
                    </button>
                    <button 
                        onClick={(e) => handleDelete(e, item)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-opacity"
                        title="Delete"
                    >
                        <FaTrash className="w-3 h-3" />
                    </button>
                </div>
              </div>
              {editingId === item.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => handleEditKeyDown(e, item)}
                    onClick={(e) => e.stopPropagation()}
                    onBlur={(e) => handleSaveTitle(e, item)}
                    autoFocus
                    className="text-sm w-full border rounded px-1"
                  />
              ) : (
                  <p className="text-sm line-clamp-2 text-gray-700 dark:text-gray-300 pr-4">
                    {item.prompt || "Image Generation"}
                  </p>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default HistoryList;
