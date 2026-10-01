'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
  X,
  Download,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  Loader2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

// Session in-memory cache for fetched PDF ArrayBuffers
const pdfCache = new Map<string, ArrayBuffer>();

export interface PreviewResume {
  id: string;
  name: string;
  file_type?: string;
  download_url?: string;
  file_url?: string;
  file_path?: string;
}

interface ResumePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  resume: PreviewResume | null;
  onDownload?: (resume: PreviewResume) => void;
}

export default function ResumePreviewModal({
  isOpen,
  onClose,
  resume,
  onDownload
}: ResumePreviewModalProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [pdfData, setPdfData] = useState<ArrayBuffer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const isDocx = Boolean(
    resume &&
      ((resume.file_type || '').toLowerCase() === 'docx' ||
        (resume.name || '').toLowerCase().endsWith('.docx'))
  );

  const loadPdf = useCallback(async (resumeId: string) => {
    if (pdfCache.has(resumeId)) {
      setPdfData(pdfCache.get(resumeId)!);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    setPdfData(null);

    try {
      const token = await apiClient.getAuthToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // 1. Create short-lived preview session
      const sessionRes = await fetch(`/api/py/resumes/${resumeId}/preview-session`, {
        method: 'POST',
        headers,
        credentials: 'same-origin'
      });

      if (!sessionRes.ok) {
        throw new Error('Failed to create preview session');
      }

      // 2. Fetch raw PDF byte stream
      const viewHeaders: Record<string, string> = {};
      if (token) {
        viewHeaders['Authorization'] = `Bearer ${token}`;
      }

      const viewRes = await fetch(`/api/py/resumes/${resumeId}/view`, {
        headers: viewHeaders,
        credentials: 'same-origin'
      });

      if (!viewRes.ok) {
        throw new Error('Failed to retrieve PDF file');
      }

      const arrayBuffer = await viewRes.arrayBuffer();
      pdfCache.set(resumeId, arrayBuffer);
      setPdfData(arrayBuffer);
    } catch (err: unknown) {
      setError('Unable to preview this resume.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen && resume && !isDocx) {
      setPageNumber(1);
      setScale(1.0);
      loadPdf(resume.id);
    } else {
      setPdfData(null);
      setNumPages(null);
      setError(null);
    }
  }, [isOpen, resume, isDocx, loadPdf]);

  // Lock background body scroll when open
  useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  // Handle keyboard Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !resume) return null;

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
    setLoading(false);
  };

  const onDocumentLoadError = () => {
    setError('Unable to preview this resume.');
    setLoading(false);
  };

  const changePage = (offset: number) => {
    setPageNumber((prevPage) => {
      const newPage = prevPage + offset;
      return Math.min(Math.max(1, newPage), numPages || 1);
    });
  };

  const zoomOut = () => setScale((prev) => Math.max(0.6, Math.round((prev - 0.15) * 100) / 100));
  const zoomIn = () => setScale((prev) => Math.min(2.2, Math.round((prev + 0.15) * 100) / 100));
  const resetZoom = () => setScale(1.0);

  const cleanFilename = resume.name.replace(/\s*\([^)]*\)\s*/g, '').trim() || 'resume';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Resume Preview Modal"
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(6px)',
        WebkitBackdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-xl, 16px)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 0, 0, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          maxWidth: '1000px',
          height: '88vh',
          maxHeight: '920px',
          overflow: 'hidden',
          position: 'relative',
          color: 'var(--text-primary)'
        }}
      >
        {/* HEADER */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 20px',
            borderBottom: '1px solid var(--border-primary)',
            backgroundColor: 'var(--bg-primary)',
            flexShrink: 0
          }}
        >
          {/* Left: Icon & Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-md, 8px)',
                backgroundColor: 'var(--accent-primary-bg, rgba(99, 102, 241, 0.15))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <FileText size={18} color="var(--accent-primary, #6366f1)" />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Resume Preview
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '380px' }}>
                {cleanFilename}
              </div>
            </div>
          </div>

          {/* Right: Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {onDownload && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onDownload(resume)}
                aria-label="Download resume"
                title="Download original file"
                style={{ fontSize: '0.8rem', padding: '6px 14px', display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <Download size={15} />
                <span className="hide-mobile">Download</span>
              </button>
            )}

            <button
              className="btn btn-ghost btn-sm btn-icon"
              onClick={onClose}
              aria-label="Close preview modal"
              style={{ borderRadius: 'var(--radius-md)', padding: 6, color: 'var(--text-secondary)' }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* DOCUMENT VIEWPORT */}
        <div
          ref={containerRef}
          style={{
            flex: 1,
            overflow: 'auto',
            backgroundColor: 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
            padding: '24px 16px',
            position: 'relative'
          }}
        >
          {isDocx ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                margin: 'auto',
                padding: '40px 24px',
                textAlign: 'center',
                maxWidth: 420,
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-lg, 12px)',
                border: '1px solid var(--border-primary)',
                boxShadow: 'var(--shadow-md)'
              }}
            >
              <div style={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: 'var(--accent-warning-bg, rgba(217, 119, 6, 0.15))', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <FileText size={28} color="var(--accent-warning, #d97706)" />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
                Preview isn't available for DOCX files.
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 24, lineHeight: 1.5 }}>
                DOCX format cannot be rendered inline in the browser. You can download the file to view it in Microsoft Word or any compatible app.
              </p>
              {onDownload && (
                <button className="btn btn-primary" onClick={() => onDownload(resume)}>
                  <Download size={16} /> Download DOCX
                </button>
              )}
            </div>
          ) : loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', margin: 'auto', padding: 40, gap: 14, color: 'var(--text-secondary)' }}>
              <Loader2 size={32} className="animate-spin" color="var(--accent-primary, #6366f1)" />
              <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>Preparing resume preview...</div>
            </div>
          ) : error ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                margin: 'auto',
                padding: '36px 24px',
                textAlign: 'center',
                maxWidth: 420,
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-lg, 12px)',
                border: '1px solid var(--border-primary)'
              }}
            >
              <div style={{ width: 48, height: 48, borderRadius: '50%', backgroundColor: 'var(--accent-danger-bg, rgba(239, 68, 68, 0.15))', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                <AlertCircle size={24} color="var(--accent-danger, #ef4444)" />
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
                Unable to preview this resume.
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
                We ran into a problem loading the PDF. Please try again or download the document directly.
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => loadPdf(resume.id)}>
                  <RefreshCw size={14} /> Try again
                </button>
                {onDownload && (
                  <button className="btn btn-primary btn-sm" onClick={() => onDownload(resume)}>
                    <Download size={14} /> Download resume
                  </button>
                )}
              </div>
            </div>
          ) : pdfData ? (
            <div
              style={{
                boxShadow: '0 10px 30px rgba(0,0,0,0.25)',
                borderRadius: '4px',
                overflow: 'hidden',
                backgroundColor: '#ffffff',
                transition: 'transform 0.15s ease-out'
              }}
            >
              <Document
                file={{ data: pdfData }}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={null}
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
              </Document>
            </div>
          ) : null}
        </div>

        {/* BOTTOM TOOLBAR (Shown for PDFs when loaded successfully) */}
        {!isDocx && !loading && !error && pdfData && numPages && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 20px',
              backgroundColor: 'var(--bg-primary)',
              borderTop: '1px solid var(--border-primary)',
              flexShrink: 0,
              gap: 12,
              flexWrap: 'wrap'
            }}
          >
            {/* Pagination Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => changePage(-1)}
                disabled={pageNumber <= 1}
                aria-label="Previous page"
                title="Previous page"
                style={{ padding: '6px' }}
              >
                <ChevronLeft size={18} />
              </button>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', minWidth: 64, textAlign: 'center' }}>
                {pageNumber} / {numPages}
              </span>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => changePage(1)}
                disabled={pageNumber >= numPages}
                aria-label="Next page"
                title="Next page"
                style={{ padding: '6px' }}
              >
                <ChevronRight size={18} />
              </button>
            </div>

            {/* Zoom Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={zoomOut}
                disabled={scale <= 0.6}
                aria-label="Zoom out"
                title="Zoom out"
                style={{ padding: '6px' }}
              >
                <ZoomOut size={16} />
              </button>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-tertiary)', width: 44, textAlign: 'center' }}>
                {Math.round(scale * 100)}%
              </span>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={zoomIn}
                disabled={scale >= 2.2}
                aria-label="Zoom in"
                title="Zoom in"
                style={{ padding: '6px' }}
              >
                <ZoomIn size={16} />
              </button>

              <button
                className="btn btn-ghost btn-sm"
                onClick={resetZoom}
                aria-label="Fit size"
                title="Reset zoom to 100%"
                style={{ fontSize: '0.75rem', padding: '4px 8px', marginLeft: 4 }}
              >
                <Maximize2 size={13} style={{ marginRight: 4 }} /> Fit
              </button>
            </div>
          </div>
        )}
      </div>

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @media (max-width: 640px) {
          .hide-mobile {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
