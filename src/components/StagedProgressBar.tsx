'use client';

import { useEffect, useState, useRef } from 'react';
import { Sparkles } from 'lucide-react';

interface StagedProgressBarProps {
  isLoading: boolean;
  stages: string[];
  hasError?: boolean;
  className?: string;
  stageDurationMs?: number;
}

export default function StagedProgressBar({
  isLoading,
  stages,
  hasError = false,
  className = '',
  stageDurationMs = 1600,
}: StagedProgressBarProps) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [visible, setVisible] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    if (isLoading) {
      setVisible(true);
      setIsFinishing(false);
      setCurrentStageIndex(0);
      setProgressPercent(4);
      startTimeRef.current = Date.now();

      const stageCount = Math.max(1, stages.length);
      const stageDurationSec = stageDurationMs / 1000;
      const expectedTotalSec = stageCount * stageDurationSec;

      // 100ms ticker for continuous, fluid percentage and stage updates
      const ticker = setInterval(() => {
        const elapsedSec = (Date.now() - startTimeRef.current) / 1000;

        // Stage index advances naturally with elapsed time
        const idealStage = Math.min(Math.floor(elapsedSec / stageDurationSec), stageCount - 1);
        setCurrentStageIndex(idealStage);

        // Continuous percentage calculation
        let pct: number;
        if (elapsedSec <= expectedTotalSec) {
          // Smooth progression from 4% to 88% over expected duration
          pct = 4 + (elapsedSec / expectedTotalSec) * 84;
        } else {
          // Asymptotic creep towards 95% if backend takes longer than expected (never freezes at 90%)
          const extraSec = elapsedSec - expectedTotalSec;
          pct = 88 + 7 * (1 - Math.exp(-extraSec / 5.0));
        }

        setProgressPercent(Math.min(95, Math.round(pct)));
      }, 100);

      return () => clearInterval(ticker);
    } else {
      if (hasError) {
        // Immediately reset and hide on error
        setVisible(false);
        setIsFinishing(false);
        setProgressPercent(0);
        setCurrentStageIndex(0);
      } else if (visible) {
        // Immediate completion to 100% when real request finishes
        setIsFinishing(true);
        setCurrentStageIndex(stages.length - 1);
        setProgressPercent(100);

        const hideTimeout = setTimeout(() => {
          setVisible(false);
          setIsFinishing(false);
          setProgressPercent(0);
          setCurrentStageIndex(0);
        }, 350);

        return () => clearTimeout(hideTimeout);
      }
    }
  }, [isLoading, hasError, stages, stageDurationMs, visible]);

  if (!visible) return null;

  return (
    <div
      className={`staged-progress-container animate-in ${className}`}
      style={{
        marginTop: 14,
        marginBottom: 8,
        width: '100%',
      }}
    >
      {/* Label and Status */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 6,
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: 'var(--accent-success)',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <Sparkles size={14} className="animate-spin" style={{ color: 'var(--accent-success)' }} />
          <span>{stages[currentStageIndex] || 'Processing...'}</span>
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-tertiary)',
            fontWeight: 500,
          }}
        >
          {isFinishing ? '100% Complete' : `${progressPercent}%`}
        </span>
      </div>

      {/* Progress Track */}
      <div
        style={{
          width: '100%',
          height: '7px',
          backgroundColor: 'var(--accent-success-bg)',
          borderRadius: '9999px',
          overflow: 'hidden',
          position: 'relative',
          border: '1px solid rgba(5, 150, 105, 0.2)',
          boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)',
        }}
        aria-label="AI Progress Indicator"
        role="progressbar"
        aria-valuenow={progressPercent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        {/* Animated Green Progress Fill */}
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, #10b981 0%, #059669 100%)',
            borderRadius: '9999px',
            transition: isFinishing
              ? 'width 300ms ease-out'
              : 'width 200ms ease-out',
            boxShadow: '0 0 8px rgba(16, 185, 129, 0.4)',
          }}
        />
      </div>
    </div>
  );
}

