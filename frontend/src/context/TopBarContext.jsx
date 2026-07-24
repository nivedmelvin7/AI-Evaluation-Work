import { createContext, useContext, useEffect, useMemo, useState } from 'react';

// Split into two contexts so that pages calling `useTopBarConfig` (write-only)
// never subscribe to the display value. If they shared one context, a page
// whose `action` prop isn't referentially stable would loop forever: the
// page's effect writes the new value, the context changes, the page
// re-renders (because it also reads the context), which recreates the action
// element, which re-fires the effect. The dispatch context only ever holds
// useState setters, which React guarantees are stable — so it never changes
// after the first render and pages that only need it never re-render because
// of their own writes.
const TopBarValueContext = createContext(null);
const TopBarDispatchContext = createContext(null);

export function TopBarProvider({ children }) {
  const [title, setTitle] = useState('Engineering Report Evaluation');
  const [action, setAction] = useState(null);

  const value = useMemo(() => ({ title, action }), [title, action]);
  const dispatch = useMemo(() => ({ setTitle, setAction }), []);

  return (
    <TopBarDispatchContext.Provider value={dispatch}>
      <TopBarValueContext.Provider value={value}>
        {children}
      </TopBarValueContext.Provider>
    </TopBarDispatchContext.Provider>
  );
}

/** Display-only: title/action for TopBar to render. */
export function useTopBar() {
  const context = useContext(TopBarValueContext);
  if (!context) throw new Error('useTopBar must be used inside TopBarProvider');
  return context;
}

function useTopBarDispatch() {
  const context = useContext(TopBarDispatchContext);
  if (!context) throw new Error('useTopBarConfig must be used inside TopBarProvider');
  return context;
}

/**
 * Called by a page component to register its title and optional primary
 * action button with the shared top bar. Cleans up on unmount so the next
 * page doesn't inherit a stale action.
 */
export function useTopBarConfig({ title, action }) {
  const { setTitle, setAction } = useTopBarDispatch();

  useEffect(() => {
    if (title) setTitle(title);
  }, [title, setTitle]);

  useEffect(() => {
    setAction(action || null);
    return () => setAction(null);
  }, [action, setAction]);
}
