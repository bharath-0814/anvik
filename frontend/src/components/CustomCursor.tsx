import React, { useEffect, useState, useRef } from 'react';

/**
 * CustomCursor
 * High-contrast, tactical forensic cursor follower designed for Anvik.
 * Features a dual-tone glowing emerald reticle with white outer border
 * that ensures maximum visibility across dark, light, green, and canvas surfaces.
 */
export const CustomCursor: React.FC = () => {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [followerPos, setFollowerPos] = useState({ x: -100, y: -100 });
  const [isHovered, setIsHovered] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [hoverLabel, setHoverLabel] = useState<string | null>(null);

  const requestRef = useRef<number | null>(null);
  const targetPos = useRef({ x: -100, y: -100 });

  useEffect(() => {
    // Check if device is touch-based
    if (window.matchMedia('(pointer: coarse)').matches) {
      setIsTouchDevice(true);
      return;
    }

    const onMouseMove = (e: MouseEvent) => {
      targetPos.current = { x: e.clientX, y: e.clientY };
      setPosition({ x: e.clientX, y: e.clientY });
      if (!isVisible) setIsVisible(true);

      // Check if hovering over interactive elements
      const target = e.target as HTMLElement | null;
      if (target) {
        const interactive = target.closest(
          'button, a, [role="button"], .cursor-pointer, input, select, textarea, [data-node="true"]'
        );
        if (interactive) {
          setIsHovered(true);
          if (interactive.getAttribute('data-node') === 'true') {
            setHoverLabel('NODE');
          } else if (interactive.tagName === 'BUTTON' || interactive.getAttribute('role') === 'button') {
            setHoverLabel('ACTION');
          } else {
            setHoverLabel(null);
          }
        } else {
          setIsHovered(false);
          setHoverLabel(null);
        }
      }
    };

    const onMouseDown = () => setIsClicking(true);
    const onMouseUp = () => setIsClicking(false);
    const onMouseLeave = () => setIsVisible(false);
    const onMouseEnter = () => setIsVisible(true);

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseenter', onMouseEnter);

    // Smooth lerp animation for the outer tactical follower ring
    const animate = () => {
      setFollowerPos((prev) => {
        const dx = targetPos.current.x - prev.x;
        const dy = targetPos.current.y - prev.y;
        return {
          x: prev.x + dx * 0.28,
          y: prev.y + dy * 0.28,
        };
      });
      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mouseleave', onMouseLeave);
      document.removeEventListener('mouseenter', onMouseEnter);
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isVisible]);

  if (isTouchDevice || !isVisible) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 z-[999999] overflow-hidden select-none"
      aria-hidden="true"
    >
      {/* 1. Tactical Outer Reticle Ring (Lerped Follower) */}
      <div
        className="fixed top-0 left-0 transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(${followerPos.x}px, ${followerPos.y}px, 0) translate(-50%, -50%)`,
        }}
      >
        <div
          className={`relative rounded-full transition-all duration-200 ease-out flex items-center justify-center ${
            isHovered
              ? 'w-10 h-10 border-2 border-[#00A887] bg-emerald-500/10 shadow-[0_0_15px_rgba(0,168,135,0.45)]'
              : 'w-7 h-7 border border-[#007065]/60 bg-transparent shadow-[0_0_6px_rgba(0,112,101,0.2)]'
          } ${isClicking ? 'scale-75' : isHovered ? 'scale-110' : 'scale-100'}`}
        >
          {/* Outer High-Contrast Dark Ring for visibility on white/cream backgrounds */}
          <div
            className={`absolute inset-[-2px] rounded-full border border-black/25 pointer-events-none transition-all ${
              isHovered ? 'border-black/35' : 'border-black/15'
            }`}
          />

          {/* Tactical Crosshair Ticks when Hovering */}
          {isHovered && (
            <>
              <span className="absolute -top-1 w-1 h-1 bg-[#00A887] rounded-full shadow-[0_0_4px_#00A887]" />
              <span className="absolute -bottom-1 w-1 h-1 bg-[#00A887] rounded-full shadow-[0_0_4px_#00A887]" />
              <span className="absolute -left-1 w-1 h-1 bg-[#00A887] rounded-full shadow-[0_0_4px_#00A887]" />
              <span className="absolute -right-1 w-1 h-1 bg-[#00A887] rounded-full shadow-[0_0_4px_#00A887]" />
            </>
          )}

          {/* Micro HUD Tag when targeting an entity */}
          {hoverLabel && (
            <span className="absolute -bottom-4 px-1 py-0.2 rounded text-[8px] font-mono font-bold tracking-widest uppercase bg-slate-900/90 text-[#10B981] border border-emerald-500/40 shadow-xs whitespace-nowrap">
              {hoverLabel}
            </span>
          )}
        </div>
      </div>

      {/* 2. Precision Center Dot (Instant Mouse Follower) */}
      <div
        className="fixed top-0 left-0 will-change-transform"
        style={{
          transform: `translate3d(${position.x}px, ${position.y}px, 0) translate(-50%, -50%)`,
        }}
      >
        <div
          className={`rounded-full transition-transform duration-100 ease-out shadow-xs ${
            isHovered
              ? 'w-2 h-2 bg-[#10B981] ring-2 ring-white ring-offset-1 ring-offset-slate-900'
              : 'w-2 h-2 bg-[#007065] ring-1.5 ring-white shadow-[0_0_4px_rgba(0,0,0,0.5)]'
          } ${isClicking ? 'scale-50' : 'scale-100'}`}
        />
      </div>
    </div>
  );
};
