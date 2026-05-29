"use client";
import { useState, useRef, useEffect } from "react";

// options: [{ id, label, searchText? }]  — searchText adds extra search surface (e.g. documento)
// value: selected id (string or number, compared loosely)
// onChange: (id) => void — called with "" when selection is cleared
export default function Combobox({ options, value, onChange, placeholder, inputClassName }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  const selected = options.find((o) => String(o.id) === String(value));

  useEffect(() => {
    function onClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    if (!value) setQuery("");
  }, [value]);

  const filtered = query.trim()
    ? options.filter((o) => {
        const haystack = (o.label + " " + (o.searchText || "")).toLowerCase();
        return haystack.includes(query.toLowerCase());
      })
    : options;

  function handleInputChange(e) {
    setQuery(e.target.value);
    onChange("");
    setOpen(true);
  }

  function handleFocus() {
    setQuery("");
    setOpen(true);
  }

  function handleSelect(option) {
    onChange(option.id);
    setOpen(false);
    setQuery("");
  }

  const displayValue = open ? query : (selected ? selected.label : "");

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <input
          type="text"
          value={displayValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          placeholder={placeholder}
          autoComplete="off"
          className={inputClassName}
        />
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setOpen((o) => !o)}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {open && (
        <ul className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-52 overflow-y-auto">
          {filtered.length > 0 ? (
            filtered.map((option) => (
              <li
                key={option.id}
                onMouseDown={(e) => { e.preventDefault(); handleSelect(option); }}
                className={`px-3 py-2 text-sm cursor-pointer hover:bg-gray-50 ${
                  String(option.id) === String(value)
                    ? "font-medium text-gray-900 bg-gray-50"
                    : "text-gray-700"
                }`}
              >
                {option.label}
              </li>
            ))
          ) : (
            <li className="px-3 py-2 text-sm text-gray-400">Sin resultados</li>
          )}
        </ul>
      )}
    </div>
  );
}
