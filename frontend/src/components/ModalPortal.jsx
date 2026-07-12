import React, { useEffect, useRef, useState, useCallback } from "react";
import { createPortal } from "react-dom";

const focusableSelectors = [
  "button:not([disabled])",
  "a[href]",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

const MODAL_DEBUG_FLAG = "__DATAMANTRI_MODAL_DEBUG__";
const activeModalIds = [];
const activeBodyLocks = new Set();
let originalBodyState = null;

function logModalLifecycle(message, details = {}) {
  if (typeof window === "undefined") return;
  if (!window[MODAL_DEBUG_FLAG] && window.localStorage?.getItem("datamantriModalDebug") !== "true") return;
  console.debug(`[DataMantri modal] ${message}`, details);
}

function snapshotBodyState() {
  const body = document.body;
  return {
    overflow: body.style.overflow,
    paddingRight: body.style.paddingRight,
    touchAction: body.style.touchAction,
    overscrollBehavior: body.style.overscrollBehavior,
    pointerEvents: body.style.pointerEvents,
  };
}

function restoreBodyState() {
  if (!originalBodyState) return;
  const body = document.body;
  body.style.overflow = originalBodyState.overflow;
  body.style.paddingRight = originalBodyState.paddingRight;
  body.style.touchAction = originalBodyState.touchAction;
  body.style.overscrollBehavior = originalBodyState.overscrollBehavior;
  body.style.pointerEvents = originalBodyState.pointerEvents;
  body.classList.remove("modal-open", "datamantri-modal-open");
  document.documentElement.classList.remove("modal-open", "datamantri-modal-open");
  originalBodyState = null;
}

function applyBodyLock(lockId) {
  if (typeof document === "undefined") return;
  const body = document.body;
  if (!originalBodyState) {
    originalBodyState = snapshotBodyState();
    const scrollBarWidth = window.innerWidth - document.documentElement.clientWidth;
    body.style.overflow = "hidden";
    body.style.touchAction = "none";
    body.style.overscrollBehavior = "contain";
    body.style.pointerEvents = originalBodyState.pointerEvents || "";
    if (scrollBarWidth > 0) {
      body.style.paddingRight = `${scrollBarWidth}px`;
    }
    body.classList.add("datamantri-modal-open");
    document.documentElement.classList.add("datamantri-modal-open");
    logModalLifecycle("Body lock applied", { lockId, activeLocks: activeBodyLocks.size + 1 });
  }
  activeBodyLocks.add(lockId);
}

function releaseBodyLock(lockId) {
  if (typeof document === "undefined") return;
  activeBodyLocks.delete(lockId);
  if (activeBodyLocks.size === 0) {
    restoreBodyState();
    logModalLifecycle("Body lock removed", { lockId });
  } else {
    logModalLifecycle("Body lock retained by another modal", { lockId, activeLocks: activeBodyLocks.size });
  }
}

function registerModal(modalId) {
  activeModalIds.push(modalId);
  logModalLifecycle("Modal opened", { modalId, stackDepth: activeModalIds.length });
}

function unregisterModal(modalId) {
  const index = activeModalIds.lastIndexOf(modalId);
  if (index >= 0) activeModalIds.splice(index, 1);
  logModalLifecycle("Modal closed", { modalId, stackDepth: activeModalIds.length });
}

function isTopModal(modalId) {
  return activeModalIds[activeModalIds.length - 1] === modalId;
}

function getFocusableElements(node) {
  if (!node) return [];
  return Array.from(node.querySelectorAll(focusableSelectors)).filter(
    (element) => element.offsetWidth > 0 || element.offsetHeight > 0 || element.getClientRects().length
  );
}

function ModalPortal({
  open,
  onClose,
  title,
  children,
  className = "",
  overlayClassName = "",
  panelStyle: panelStyleOverride = {},
  closeOnOverlay = true,
}) {
  const modalIdRef = useRef(`modal-${Date.now()}-${Math.random().toString(36).slice(2)}`);
  const [mounted, setMounted] = useState(open);
  const [visible, setVisible] = useState(open);
  const containerRef = useRef(null);
  const dialogRef = useRef(null);
  const lastFocusedElement = useRef(null);
  const closeTimerRef = useRef(null);
  const lockAppliedRef = useRef(false);

  useEffect(() => {
    const modalId = modalIdRef.current;
    const container = document.createElement("div");
    containerRef.current = container;
    document.body.appendChild(container);
    logModalLifecycle("Portal mounted", { modalId });
    return () => {
      if (closeTimerRef.current) window.clearTimeout(closeTimerRef.current);
      if (lockAppliedRef.current) {
        unregisterModal(modalId);
        releaseBodyLock(modalId);
        lockAppliedRef.current = false;
      }
      if (container.parentNode) {
        container.parentNode.removeChild(container);
      }
      logModalLifecycle("Portal removed", { modalId });
    };
  }, []);

  useEffect(() => {
    if (open) {
      lastFocusedElement.current = document.activeElement;
      setMounted(true);
      window.requestAnimationFrame(() => setVisible(true));
    } else if (mounted) {
      setVisible(false);
    }
  }, [open, mounted]);

  useEffect(() => {
    if (!mounted) return undefined;
    const modalId = modalIdRef.current;
    if (!lockAppliedRef.current) {
      registerModal(modalId);
      applyBodyLock(modalId);
      lockAppliedRef.current = true;
      logModalLifecycle("Backdrop mounted", { modalId });
    }
    return () => {
      if (lockAppliedRef.current) {
        unregisterModal(modalId);
        releaseBodyLock(modalId);
        lockAppliedRef.current = false;
        logModalLifecycle("Backdrop removed", { modalId });
      }
    };
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return undefined;
    const handleKeyDown = (event) => {
      if (!isTopModal(modalIdRef.current)) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
      if (event.key === "Tab") {
        const focusableElements = getFocusableElements(dialogRef.current);
        if (!focusableElements.length) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const current = document.activeElement;

        if (event.shiftKey && current === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }

        if (!event.shiftKey && current === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mounted, onClose]);

  useEffect(() => {
    if (!visible) return undefined;
    const dialog = dialogRef.current;
    if (!dialog) return undefined;
    const focusable = getFocusableElements(dialog);
    if (focusable.length) {
      focusable[0].focus();
    } else {
      dialog.focus();
    }
    return undefined;
  }, [visible]);

  useEffect(() => {
    if (!mounted || visible) return undefined;
    closeTimerRef.current = window.setTimeout(() => {
      setMounted(false);
      if (lastFocusedElement.current instanceof HTMLElement) {
        lastFocusedElement.current.focus();
      }
    }, 180);
    return () => {
      if (closeTimerRef.current) window.clearTimeout(closeTimerRef.current);
    };
  }, [mounted, visible]);

  const handleOverlayClick = useCallback(
    (event) => {
      if (closeOnOverlay && event.target === event.currentTarget) {
        onClose();
      }
    },
    [closeOnOverlay, onClose]
  );

  if (!mounted || !containerRef.current) return null;

  const overlayStyle = {
    position: "fixed",
    inset: 0,
    zIndex: 10000,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "rgba(15, 23, 42, 0.58)",
    backdropFilter: "blur(14px)",
    padding: "24px",
    boxSizing: "border-box",
    pointerEvents: visible ? "auto" : "none",
  };

  const panelStyle = {
    width: "min(1000px, calc(100vw - 48px))",
    maxWidth: "100%",
    maxHeight: "85vh",
    overflowY: "auto",
    background: "var(--bg)",
    border: "1px solid var(--border)",
    borderRadius: "24px",
    boxShadow: "0 32px 90px rgba(15, 23, 42, 0.18)",
    transform: visible ? "scale(1)" : "scale(0.98)",
    opacity: visible ? 1 : 0,
    transition: `opacity ${visible ? 220 : 180}ms ease-out, transform ${visible ? 220 : 180}ms ease-out`,
    willChange: "opacity, transform",
    outline: "none",
    position: "relative",
    minWidth: "320px",
    color: "inherit",
    ...panelStyleOverride,
  };

  return createPortal(
    <div style={overlayStyle} className={overlayClassName} onClick={handleOverlayClick}>
      <div
        ref={dialogRef}
        style={panelStyle}
        className={className}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
      >
        {children}
      </div>
    </div>,
    containerRef.current
  );
}

export default ModalPortal;
