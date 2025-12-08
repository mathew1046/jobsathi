import React from 'react';
import { motion } from 'framer-motion';
import { Globe, Check } from 'lucide-react';

const LanguageSelectionModal = ({ languages, onSelectLanguage }) => {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-700"
            >
                <div className="bg-saas-blue p-8 text-center">
                    <div className="mx-auto w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mb-4 backdrop-blur-md">
                        <Globe className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Welcome to JobSathi</h2>
                    <p className="text-blue-100">Please select your preferred language to continue</p>
                </div>

                <div className="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => onSelectLanguage(lang.code)}
                                className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-saas-blue dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all group text-left"
                            >
                                <span className="font-semibold text-gray-700 dark:text-gray-200 group-hover:text-saas-blue dark:group-hover:text-blue-400">
                                    {lang.label}
                                </span>
                                <div className="w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-600 group-hover:border-saas-blue dark:group-hover:border-blue-500 flex items-center justify-center">
                                    <div className="w-3 h-3 rounded-full bg-saas-blue dark:bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default LanguageSelectionModal;
