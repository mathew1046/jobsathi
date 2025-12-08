import React from 'react';
import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

const LanguageSelector = ({ selectedLanguage, setSelectedLanguage, languages, t }) => {
    const _t = t || ((k) => k);
    return (
        <div className="flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="w-full max-w-md bg-white dark:bg-saas-dark-card rounded-2xl shadow-card hover:shadow-card-hover transition-shadow overflow-hidden border border-gray-100 dark:border-gray-700"
            >
                {/* Header Strip */}
                <div className="bg-saas-blue dark:bg-blue-600 px-6 py-4">
                    <h3 className="text-white font-bold text-lg text-center">{_t("language_selection")}</h3>
                </div>

                {/* Card Content */}
                <div className="p-8">
                    <div className="relative group">
                        <select
                            value={selectedLanguage}
                            onChange={(e) => setSelectedLanguage(e.target.value)}
                            className="block w-full px-4 py-3 pr-10 text-base text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-800 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-saas-blue focus:border-transparent appearance-none transition-all cursor-pointer shadow-sm hover:border-gray-300 dark:hover:border-gray-500"
                        >
                            {languages.map(({ code, label }) => (
                                <option key={code} value={code} className="text-gray-900 dark:text-white">
                                    {label}
                                </option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500 dark:text-gray-400">
                            <ChevronDown className="w-5 h-5" />
                        </div>
                    </div>

                    <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        {_t("language_selection_help")}
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default LanguageSelector;
