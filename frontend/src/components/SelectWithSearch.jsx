import React, { useState, useMemo, useRef, useEffect } from 'react';

const SelectWithSearch = ({ items, label, selectedItem, onSelectItem, placeholder }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    // Update query when selectedItem changes externally
    useEffect(() => {
        if (selectedItem) {
            setQuery(selectedItem.name || selectedItem);
        }
    }, [selectedItem]);

    const filteredItems = useMemo(() => {
        if (!items) return [];
        return items.filter(item => {
            const name = item.name || item;
            return name.toLowerCase().includes(query.toLowerCase());
        });
    }, [query, items]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (item) => {
        onSelectItem(item);
        setQuery(item.name || item);
        setIsOpen(false);
    };

    return (
        <div className="relative mb-4" ref={containerRef}>
            <label className="block text-sm font-bold text-gray-700 mb-1">{label}</label>
            <input
                type="text"
                className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={placeholder || "Buscar..."}
                value={query}
                onChange={(e) => {
                    setQuery(e.target.value);
                    setIsOpen(true);
                }}
                onFocus={() => setIsOpen(true)}
            />
            {isOpen && filteredItems.length > 0 && (
                <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded mt-1 max-h-60 overflow-y-auto shadow-lg">
                    {filteredItems.map((item, index) => (
                        <li
                            key={index}
                            className="p-2 hover:bg-blue-100 cursor-pointer"
                            onClick={() => handleSelect(item)}
                        >
                            {item.name || item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default SelectWithSearch;
