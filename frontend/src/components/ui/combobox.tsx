import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ComboboxOption {
  id: string;
  label: string;
  sublabel?: string;
}

export interface ComboboxProps {
  id: string;
  options: ComboboxOption[];
  value: string | null;
  onSelect: (id: string) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  placeholder: string;
  loading?: boolean;
  disabled?: boolean;
  'aria-label'?: string;
}

/**
 * Searchable, keyboard-navigable combobox. Hand-rolled per Story 1.8's
 * established pattern (no new dependency) — this is the first Combobox
 * primitive in the repo (Story 3.4). Controlled: search text and selection
 * are both owned by the parent, which is responsible for debouncing
 * `onSearchChange` calls into the actual API request.
 */
export function Combobox({
  id,
  options,
  value,
  onSelect,
  searchValue,
  onSearchChange,
  placeholder,
  loading,
  disabled,
  'aria-label': ariaLabel,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(-1);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const listboxId = `${id}-listbox`;

  const selected = options.find((option) => option.id === value) ?? null;

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, options.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === 'Enter') {
      if (open && activeIndex >= 0 && options[activeIndex]) {
        event.preventDefault();
        onSelect(options[activeIndex].id);
        setOpen(false);
      }
    } else if (event.key === 'Escape') {
      if (open) {
        // Stop the open listbox's own Escape from also bubbling to the
        // Dialog's document-level keydown handler, which would otherwise
        // close the whole modal instead of just this dropdown.
        event.stopPropagation();
      }
      setOpen(false);
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <input
        id={id}
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label={ariaLabel}
        autoComplete="off"
        disabled={disabled}
        placeholder={placeholder}
        value={selected ? selected.label : searchValue}
        onChange={(event) => {
          onSearchChange(event.target.value);
          setOpen(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        className="flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-talentpilot-500 disabled:cursor-not-allowed disabled:opacity-50"
      />
      {open && !disabled && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg"
        >
          {loading ? (
            <li className="px-3 py-2 text-sm text-gray-400">Loading…</li>
          ) : options.length === 0 ? (
            <li className="px-3 py-2 text-sm text-gray-400">No results</li>
          ) : (
            options.map((option, index) => (
              <li
                key={option.id}
                role="option"
                aria-selected={option.id === value}
                className={cn(
                  'cursor-pointer px-3 py-2 text-sm hover:bg-gray-50',
                  index === activeIndex && 'bg-talentpilot-50'
                )}
                // onMouseDown (not onClick) fires before the input's onBlur,
                // so the click actually registers instead of the listbox
                // closing first.
                onMouseDown={(event) => {
                  event.preventDefault();
                  onSelect(option.id);
                  setOpen(false);
                }}
              >
                {option.label}
                {option.sublabel && <span className="ml-1 text-gray-400">· {option.sublabel}</span>}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
