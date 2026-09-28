'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Move, Check, X, Loader2 } from 'lucide-react';

interface AvatarCropModalProps {
  imageSrc: string;
  onCancel: () => void;
  onSave: (croppedFile: File) => Promise<void>;
}

export default function AvatarCropModal({ imageSrc, onCancel, onSave }: AvatarCropModalProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [imgElement, setImgElement] = useState<HTMLImageElement | null>(null);
  const [saving, setSaving] = useState(false);

  // Load image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      setImgElement(img);
      setZoom(1);
      setOffset({ x: 0, y: 0 });
    };
    img.src = imageSrc;
  }, [imageSrc]);

  // Draw crop preview on canvas
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imgElement) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = 300; // Canvas dimensions
    const circleRadius = 100; // Crop circle radius
    const centerX = size / 2;
    const centerY = size / 2;

    ctx.clearRect(0, 0, size, size);

    // Calculate base scale to fill crop circle
    const minDim = Math.min(imgElement.width, imgElement.height);
    const baseScale = (circleRadius * 2) / minDim;
    const currentScale = baseScale * zoom;

    const drawWidth = imgElement.width * currentScale;
    const drawHeight = imgElement.height * currentScale;

    const drawX = centerX - drawWidth / 2 + offset.x;
    const drawY = centerY - drawHeight / 2 + offset.y;

    // Draw main image
    ctx.drawImage(imgElement, drawX, drawY, drawWidth, drawHeight);

    // Overlay background dimming
    ctx.save();
    ctx.fillStyle = 'rgba(15, 23, 42, 0.65)'; // Darkened backdrop
    ctx.beginPath();
    ctx.rect(0, 0, size, size);
    ctx.arc(centerX, centerY, circleRadius, 0, Math.PI * 2, true);
    ctx.fill('evenodd');
    ctx.restore();

    // Circle border
    ctx.strokeStyle = '#6366f1'; // var(--accent-primary)
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, circleRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Grid guide crosshair inside circle
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(centerX - circleRadius, centerY);
    ctx.lineTo(centerX + circleRadius, centerY);
    ctx.moveTo(centerX, centerY - circleRadius);
    ctx.lineTo(centerX, centerY + circleRadius);
    ctx.stroke();
  }, [imgElement, zoom, offset]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  // Pointer event handlers for dragging
  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        // Ignore if pointer capture release throws
      }
    }
  };

  // Generate cropped output file
  const handleApply = async () => {
    if (!imgElement) return;
    setSaving(true);

    try {
      const outputSize = 400; // Output resolution 400x400
      const outputCanvas = document.createElement('canvas');
      outputCanvas.width = outputSize;
      outputCanvas.height = outputSize;
      const ctx = outputCanvas.getContext('2d');

      if (ctx) {
        const circleRadius = 100;
        const minDim = Math.min(imgElement.width, imgElement.height);
        const baseScale = (circleRadius * 2) / minDim;
        const currentScale = baseScale * zoom;

        // Scale ratio from 300px viewport to 400px output canvas
        const scaleToOutput = outputSize / (circleRadius * 2);

        const drawWidth = imgElement.width * currentScale * scaleToOutput;
        const drawHeight = imgElement.height * currentScale * scaleToOutput;

        const drawX = outputSize / 2 - drawWidth / 2 + offset.x * scaleToOutput;
        const drawY = outputSize / 2 - drawHeight / 2 + offset.y * scaleToOutput;

        ctx.drawImage(imgElement, drawX, drawY, drawWidth, drawHeight);

        outputCanvas.toBlob(
          async (blob) => {
            if (!blob) {
              setSaving(false);
              return;
            }
            const file = new File([blob], 'cropped_avatar.jpeg', { type: 'image/jpeg' });
            await onSave(file);
            setSaving(false);
          },
          'image/jpeg',
          0.92
        );
      }
    } catch (err) {
      console.error('Cropping error:', err);
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
    >
      <div
        className="card animate-in"
        style={{
          width: '100%',
          maxWidth: 420,
          padding: 24,
          background: 'var(--bg-secondary)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Crop Profile Avatar</h3>
          <button
            onClick={onCancel}
            disabled={saving}
            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: 4 }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16, textAlign: 'center' }}>
          <Move size={14} style={{ display: 'inline', verticalAlign: -2, marginRight: 4 }} />
          Drag image to position & use slider to zoom
        </p>

        {/* Interactive Canvas Viewport */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginBottom: 20,
            touchAction: 'none',
            userSelect: 'none',
          }}
        >
          <canvas
            ref={canvasRef}
            width={300}
            height={300}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            style={{
              cursor: isDragging ? 'grabbing' : 'grab',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
              background: '#0f172a',
            }}
          />
        </div>

        {/* Zoom Controls Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, padding: '0 8px' }}>
          <ZoomOut size={18} color="var(--text-secondary)" />
          <input
            type="range"
            min={1}
            max={3}
            step={0.05}
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
          />
          <ZoomIn size={18} color="var(--text-secondary)" />
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={saving}>
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={handleApply} disabled={saving}>
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Check size={16} /> Save Avatar
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
