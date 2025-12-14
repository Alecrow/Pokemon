import React, { useState, useMemo, useRef, useEffect } from 'react';

const SelectWithSearch = ({ items, label, selectedItem, onSelectItem, placeholder }) => {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

    // Update query when selectedItem changes externally
    useEffect(() => {
        if (selectedItem !== null && selectedItem !== undefined) {
            const name = selectedItem.name || selectedItem;
            // Only update if different to avoid cursor jumping if we were to sync back
            if (name !== query) {
                setQuery(name);
            }
        }
    }, [selectedItem]);

    const filteredItems = useMemo(() => {
        if (!items) return [];
        return items.filter(item => {
            const name = item.name || item;
            // Normalize: remove spaces, lowercase
            const normalizedName = name.toLowerCase().replace(/[^a-z0-9]/g, '');
            const normalizedQuery = query.toLowerCase().replace(/[^a-z0-9]/g, '');
            return normalizedName.includes(normalizedQuery);
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
                    const val = e.target.value;
                    setQuery(val);
                    setIsOpen(true);
                    
                    // Allow custom values by updating parent immediately
                    onSelectItem(val);
                    
                    // Auto-select if exact match found (case-insensitive, ignoring spaces)
                    if (items) {
                        const match = items.find(item => {
                            const name = item.name || item;
                            const nName = name.toLowerCase().replace(/[^a-z0-9]/g, '');
                            const nVal = val.toLowerCase().replace(/[^a-z0-9]/g, '');
                            return nName === nVal;
                        });
                        if (match) {
                            onSelectItem(match);
                        }
                    }
                }}
                onFocus={() => setIsOpen(true)}
            />
            {isOpen && (
                <ul className="absolute z-[1000] w-full bg-white border border-gray-300 rounded mt-1 max-h-60 overflow-y-auto shadow-2xl">
                    {filteredItems.length > 0 ? (
                        filteredItems.map((item, index) => (
                            <li
                                key={index}
                                className="p-2 hover:bg-blue-100 cursor-pointer text-gray-800"
                                onClick={() => handleSelect(item)}
                            >
                                {item.name || item}
                            </li>
                        ))
                    ) : (
                        <li className="p-2 text-gray-500 italic">No se encontraron resultados</li>
                    )}
                </ul>
            )}
        </div>
    );
};

export default SelectWithSearch;
