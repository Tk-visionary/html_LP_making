import React, { useRef, useState, useCallback } from 'react';

export interface ImageRegion {
  id: string;
  top: number;
  left: number;
  width: number;
  height: number;
  type: 'human' | 'hero' | 'coupon' | 'illustration';
}

interface Props {
  imageSrc: string;
  regions: ImageRegion[];
  onRegionsChange: (regions: ImageRegion[]) => void;
}

const REGION_TYPES = [
  { value: 'human', label: '人物', color: '#ef4444' },
  { value: 'hero', label: 'ヒーロー', color: '#3b82f6' },
  { value: 'coupon', label: 'クーポン', color: '#22c55e' },
  { value: 'illustration', label: 'イラスト', color: '#a855f7' },
] as const;

function getColorForType(type: ImageRegion['type']): string {
  const found = REGION_TYPES.find(t => t.value === type);
  return found?.color || '#6b7280';
}

// Padding around image for easier dragging with trackpad
const CANVAS_PADDING = 50;

export function RegionSelector({ imageSrc, regions, onRegionsChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentRect, setCurrentRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [showTypePopup, setShowTypePopup] = useState<{ x: number; y: number; regionId: string } | null>(null);

  // Get mouse position relative to the image (accounting for padding)
  const getRelativePosition = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current || !imageSize) return null;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - CANVAS_PADDING;
    const y = e.clientY - rect.top - CANVAS_PADDING;
    return { x, y };
  }, [imageSize]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    
    // Don't start drawing if popup is open
    if (showTypePopup) {
      setShowTypePopup(null);
      return;
    }
    
    const pos = getRelativePosition(e);
    if (!pos) return;
    
    // Check if click is on an existing region
    const clickedRegion = regions.find(r => 
      pos.x >= r.left && pos.x <= r.left + r.width &&
      pos.y >= r.top && pos.y <= r.top + r.height
    );
    
    if (clickedRegion) {
      // Show popup for existing region
      e.stopPropagation();
      setShowTypePopup({ x: pos.x + CANVAS_PADDING, y: pos.y + CANVAS_PADDING, regionId: clickedRegion.id });
      return;
    }
    
    setIsDrawing(true);
    setStartPoint(pos);
    setCurrentRect(null);
    setShowTypePopup(null);
  }, [getRelativePosition, showTypePopup, regions]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDrawing || !startPoint) return;
    const pos = getRelativePosition(e);
    if (!pos) return;

    const x = Math.min(startPoint.x, pos.x);
    const y = Math.min(startPoint.y, pos.y);
    const w = Math.abs(pos.x - startPoint.x);
    const h = Math.abs(pos.y - startPoint.y);
    
    setCurrentRect({ x, y, w, h });
  }, [isDrawing, startPoint, getRelativePosition]);

  const handleMouseUp = useCallback(() => {
    if (!isDrawing || !currentRect || !imageSize) {
      setIsDrawing(false);
      return;
    }

    // Only create region if it's big enough (min 20x20)
    if (currentRect.w > 20 && currentRect.h > 20) {
      // Clamp region to image bounds
      const clampedRect = {
        x: Math.max(0, currentRect.x),
        y: Math.max(0, currentRect.y),
        w: Math.min(currentRect.w, imageSize.width - Math.max(0, currentRect.x)),
        h: Math.min(currentRect.h, imageSize.height - Math.max(0, currentRect.y)),
      };
      
      const newRegion: ImageRegion = {
        id: `region_${Date.now()}`,
        left: Math.round(clampedRect.x),
        top: Math.round(clampedRect.y),
        width: Math.round(clampedRect.w),
        height: Math.round(clampedRect.h),
        type: 'human', // Default type
      };

      onRegionsChange([...regions, newRegion]);
      
      // Show type popup at center of new region
      setShowTypePopup({ 
        x: clampedRect.x + clampedRect.w / 2 + CANVAS_PADDING, 
        y: clampedRect.y + clampedRect.h / 2 + CANVAS_PADDING, 
        regionId: newRegion.id 
      });
    }

    setIsDrawing(false);
    setStartPoint(null);
    setCurrentRect(null);
  }, [isDrawing, currentRect, imageSize, regions, onRegionsChange]);

  const handleRegionTypeChange = useCallback((regionId: string, type: ImageRegion['type']) => {
    const updated = regions.map(r => 
      r.id === regionId ? { ...r, type } : r
    );
    onRegionsChange(updated);
    setShowTypePopup(null);
  }, [regions, onRegionsChange]);

  const handleRegionDelete = useCallback((regionId: string) => {
    const updated = regions.filter(r => r.id !== regionId);
    onRegionsChange(updated);
    setShowTypePopup(null);
  }, [regions, onRegionsChange]);

  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.clientWidth, height: img.clientHeight });
  }, []);

  return (
    <div 
      ref={containerRef}
      className="relative cursor-crosshair select-none bg-gray-200"
      style={{
        width: imageSize ? imageSize.width + CANVAS_PADDING * 2 : 'auto',
        height: imageSize ? imageSize.height + CANVAS_PADDING * 2 : 'auto',
        padding: CANVAS_PADDING,
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        if (isDrawing) {
          setIsDrawing(false);
          setCurrentRect(null);
        }
      }}
    >
      {/* Padding indicator - dashed border around image */}
      <div 
        className="absolute border-2 border-dashed border-gray-400 pointer-events-none"
        style={{
          left: CANVAS_PADDING,
          top: CANVAS_PADDING,
          width: imageSize?.width || 0,
          height: imageSize?.height || 0,
        }}
      />
      
      <img 
        ref={imageRef}
        src={imageSrc} 
        alt="Screenshot" 
        className="max-w-full h-auto relative z-0"
        onLoad={handleImageLoad}
        draggable={false}
      />
      
      {/* Existing regions - now with higher transparency */}
      {regions.map((region) => (
        <div
          key={region.id}
          className="absolute border-3 cursor-pointer transition-all hover:opacity-60"
          style={{
            left: region.left + CANVAS_PADDING,
            top: region.top + CANVAS_PADDING,
            width: region.width,
            height: region.height,
            borderWidth: 3,
            borderColor: getColorForType(region.type),
            backgroundColor: getColorForType(region.type),
            opacity: 0.35, // Higher transparency (was 0.2)
          }}
        >
          <span 
            className="absolute -top-7 left-0 px-2 py-1 text-xs text-white rounded font-medium shadow-sm"
            style={{ 
              backgroundColor: getColorForType(region.type),
              opacity: 1, // Label stays fully visible
            }}
          >
            {REGION_TYPES.find(t => t.value === region.type)?.label}
          </span>
        </div>
      ))}

      {/* Current drawing rectangle */}
      {currentRect && (
        <div
          className="absolute border-2 border-dashed border-blue-500 pointer-events-none"
          style={{
            left: currentRect.x + CANVAS_PADDING,
            top: currentRect.y + CANVAS_PADDING,
            width: currentRect.w,
            height: currentRect.h,
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
          }}
        />
      )}

      {/* Type selection popup */}
      {showTypePopup && (
        <div
          className="absolute z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-2 min-w-[150px]"
          style={{
            left: Math.min(showTypePopup.x, (imageSize?.width || 300) + CANVAS_PADDING - 160),
            top: Math.min(showTypePopup.y, (imageSize?.height || 300) + CANVAS_PADDING - 220),
          }}
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="text-xs font-semibold text-gray-500 mb-2 px-2">タイプ選択</div>
          {REGION_TYPES.map((type) => {
            const isSelected = regions.find(r => r.id === showTypePopup.regionId)?.type === type.value;
            return (
              <button
                key={type.value}
                className={`w-full text-left px-3 py-2 text-sm rounded flex items-center gap-2 ${
                  isSelected ? 'bg-gray-100 font-medium' : 'hover:bg-gray-100'
                }`}
                onClick={() => handleRegionTypeChange(showTypePopup.regionId, type.value)}
              >
                <span 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: type.color }}
                />
                {type.label}
                {isSelected && <span className="ml-auto text-gray-400">✓</span>}
              </button>
            );
          })}
          <hr className="my-2" />
          <button
            className="w-full text-left px-3 py-2 text-sm text-red-500 rounded hover:bg-red-50 font-medium"
            onClick={() => handleRegionDelete(showTypePopup.regionId)}
          >
            🗑️ 削除
          </button>
        </div>
      )}
    </div>
  );
}
