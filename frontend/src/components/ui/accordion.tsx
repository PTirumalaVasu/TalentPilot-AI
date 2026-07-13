import { useState } from "react";

interface AccordionItemProps {
  title: string;
  children: React.ReactNode;
  isOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
}

export function AccordionItem({ title, children, isOpen = false, onToggle }: AccordionItemProps) {
  const [open, setOpen] = useState(isOpen);

  const handleToggle = () => {
    const newState = !open;
    setOpen(newState);
    onToggle?.(newState);
  };

  return (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left font-medium text-gray-900 hover:bg-gray-50 transition-colors"
      >
        <span>{title}</span>
        <span className={`text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}>
          ▼
        </span>
      </button>
      {open && (
        <div className="bg-gray-50 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
}

interface AccordionProps {
  items: Array<{
    title: string;
    content: React.ReactNode;
    isOpen?: boolean;
  }>;
}

export function Accordion({ items }: AccordionProps) {
  return (
    <div className="border border-gray-200 rounded-lg bg-white overflow-hidden shadow-sm">
      {items.map((item, index) => (
        <AccordionItem
          key={index}
          title={item.title}
          isOpen={item.isOpen}
        >
          {item.content}
        </AccordionItem>
      ))}
    </div>
  );
}
